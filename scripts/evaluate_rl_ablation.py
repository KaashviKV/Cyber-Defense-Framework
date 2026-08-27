"""
Evaluate IDS, response, and pipeline variants for the experimental section.

Does not call VirusTotal/AbuseIPDB or MongoDB.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.rl.baselines import (
    ACTIONS,
    ideal_action,
    ml_cti_action,
    ml_cti_risk_action,
    ml_only_action,
    rule_based_action,
)
from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.predict_action import RLDecisionMaker

DOUBLE_DQN_PATH = PROJECT_ROOT / "ml" / "saved_models" / "double_dqn_model.pth"
LEGACY_PATH = PROJECT_ROOT / "ml" / "saved_models" / "dqn_model_v1_legacy.pth"


def evaluate_policy(name: str, choose_action, episodes: int = 200, max_steps: int = 4) -> dict:
    env = CyberDefenseEnvironment(max_steps=max_steps, multi_step=True)
    total_reward = 0.0
    false_blocks = 0
    missed_high = 0
    correct = 0
    critical_total = 0
    critical_contained = 0
    action_counts = {a: 0 for a in ACTIONS}
    samples = 0

    for _ in range(episodes):
        state = env.reset()
        done = False
        while not done:
            action_name = choose_action(state)
            action_idx = ACTIONS.index(action_name)
            action_counts[action_name] += 1

            desired = ideal_action(state)
            if action_name == desired:
                correct += 1

            risk = float(state.get("risk_score", 0) or 0)
            attack = state.get("attack", "BENIGN")
            if attack == "BENIGN" and action_name in ("BLOCK_IP", "ISOLATE_HOST"):
                false_blocks += 1
            if risk >= 80:
                critical_total += 1
                if action_name in ("BLOCK_IP", "ISOLATE_HOST"):
                    critical_contained += 1
            if risk >= 85 and action_name in ("NO_ACTION", "ALERT_ADMIN"):
                missed_high += 1

            next_state, reward, done = env.step(action_idx)
            total_reward += reward
            samples += 1
            state = next_state

    return {
        "name": name,
        "episodes": episodes,
        "steps": samples,
        "avg_reward": round(total_reward / max(1, episodes), 3),
        "correct_response_rate": round(correct / max(1, samples), 4),
        "unnecessary_block_rate": round(false_blocks / max(1, samples), 4),
        "critical_threat_response_rate": round(critical_contained / max(1, critical_total), 4),
        "false_block_rate": round(false_blocks / max(1, samples), 4),
        "missed_high_risk_rate": round(missed_high / max(1, samples), 4),
        "action_distribution": {
            k: round(v / max(1, samples), 4) for k, v in action_counts.items()
        },
        "notes": (
            "correct_response_rate uses the same reward-shaping bands as the environment; "
            "the rule-based policy encodes those bands, so it is a strong baseline rather "
            "than an independent oracle."
        ),
    }


def _dqn_chooser(maker: RLDecisionMaker):
    def choose(state: dict) -> str:
        return maker.predict(
            state["severity"],
            state["risk_score"],
            confidence=state.get("confidence", 0),
            virustotal_score=state.get("virustotal_score", 0),
            abuseipdb_score=state.get("abuseipdb_score", 0),
        )

    return choose


def main() -> None:
    results = [
        evaluate_policy("rule_based", rule_based_action),
        evaluate_policy("ml_only", ml_only_action),
        evaluate_policy("ml_cti", ml_cti_action),
        evaluate_policy("ml_cti_risk", ml_cti_risk_action),
    ]

    if LEGACY_PATH.exists():
        results.append(evaluate_policy("dqn_v1_legacy", _dqn_chooser(RLDecisionMaker(str(LEGACY_PATH)))))

    current = RLDecisionMaker()
    results.append(evaluate_policy(f"dqn_{current.model_version}", _dqn_chooser(current)))

    if DOUBLE_DQN_PATH.exists():
        results.append(
            evaluate_policy("double_dqn", _dqn_chooser(RLDecisionMaker(str(DOUBLE_DQN_PATH))))
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_model_version": current.model_version,
        "current_state_size": current.state_size,
        "experiment": "response_strategy_and_ablation",
        "results": results,
    }

    out_path = PROJECT_ROOT / "ml" / "saved_models" / "ablation_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== Response Strategy / Ablation ===")
    print(
        f"{'Variant':<22} {'Reward':>8} {'Correct':>9} {'UnnecBlk':>10} {'CritResp':>10}"
    )
    for row in results:
        print(
            f"{row['name']:<22} {row['avg_reward']:>8.2f} "
            f"{row['correct_response_rate']:>9.3f} "
            f"{row['unnecessary_block_rate']:>10.4f} "
            f"{row['critical_threat_response_rate']:>10.3f}"
        )
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
