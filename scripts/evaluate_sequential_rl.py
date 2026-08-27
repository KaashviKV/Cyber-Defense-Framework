"""Compare default vs cost-sensitive sequential environment using the production DQN."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.predict_action import RLDecisionMaker
from scripts.evaluate_rl_ablation import _dqn_chooser


def main() -> None:
    maker = RLDecisionMaker()
    choose = _dqn_chooser(maker)

    def eval_env(name: str, **kwargs):
        # evaluate_policy constructs its own env; run a small local loop instead
        env = CyberDefenseEnvironment(max_steps=4, multi_step=True, **kwargs)
        total = 0.0
        steps = 0
        for _ in range(80):
            state = env.reset()
            done = False
            while not done:
                action = choose(state)
                idx = env.actions.index(action)
                state, reward, done = env.step(idx)
                total += reward
                steps += 1
        return {
            "name": name,
            "episodes": 80,
            "steps": steps,
            "avg_reward": round(total / 80, 3),
        }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Cost-sensitive sequential rewards are not comparable to the original shaping "
            "table. Production DQN weights are unchanged."
        ),
        "results": [
            eval_env("legacy_shaping"),
            eval_env("sequential_effects", sequential_effects=True),
            eval_env("cost_sensitive_sequential", sequential_effects=True, cost_sensitive=True),
        ],
    }
    out = PROJECT_ROOT / "ml" / "saved_models" / "sequential_rl_results.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
