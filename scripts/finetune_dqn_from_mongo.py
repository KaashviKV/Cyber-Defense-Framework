"""
Fine-tune DQN from MongoDB analysis history (offline experience replay).

Safe by design:
- Read-only Mongo access
- Writes a NEW checkpoint: dqn_model_finetuned.pth
- Does NOT overwrite production dqn_model.pth unless --promote is passed
- Skips gracefully if MongoDB is unavailable or history is empty
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.rl.dqn_agent import DQNAgent
from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.state_encoder import STATE_SIZE_V2, encode_state


ACTIONS = ["NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"]


def load_history(limit: int = 500) -> list[dict]:
    try:
        from backend.database.mongo import analysis_collection, get_mongo_status

        if get_mongo_status() != "connected":
            return []
        return list(analysis_collection.find().sort("timestamp", -1).limit(limit))
    except Exception as exc:
        print(f"Mongo unavailable ({exc}); skipping fine-tune.")
        return []


def transition_from_doc(doc: dict) -> tuple | None:
    try:
        pred = doc.get("prediction") or {}
        risk = doc.get("risk") or {}
        decision = doc.get("decision") or {}
        action_name = decision.get("action")
        if action_name not in ACTIONS:
            return None

        severity = float(pred.get("severity", 0) or 0)
        confidence = float(pred.get("confidence", 0) or 0)
        risk_score = float(risk.get("risk_score", 0) or 0)
        vt = float(risk.get("virustotal_score", 0) or 0)
        abuse = float(risk.get("abuseipdb_score", 0) or 0)

        state = encode_state(
            severity,
            risk_score,
            confidence=confidence,
            virustotal_score=vt,
            abuseipdb_score=abuse,
            state_size=STATE_SIZE_V2,
        )
        action = ACTIONS.index(action_name)

        # Reconstruct a pseudo-state for reward evaluation
        env = CyberDefenseEnvironment(multi_step=False)
        pseudo = {
            "attack": pred.get("attack", "BENIGN"),
            "severity": severity,
            "confidence": confidence,
            "risk_score": risk_score,
            "virustotal_score": vt,
            "abuseipdb_score": abuse,
        }
        reward = env.calculate_reward(pseudo, action)
        # One-step transition; next_state ~= state (terminal)
        return (state, action, reward, state, True)
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()

    docs = load_history(limit=args.limit)
    transitions = [t for t in (transition_from_doc(d) for d in docs) if t]
    print(f"Loaded {len(docs)} docs, usable transitions={len(transitions)}")

    save_dir = PROJECT_ROOT / "ml" / "saved_models"
    prod = save_dir / "dqn_model.pth"
    out = save_dir / "dqn_model_finetuned.pth"
    metrics_out = save_dir / "dqn_finetune_metrics.json"

    if len(transitions) < 32:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "skipped",
            "reason": "insufficient_transitions",
            "docs": len(docs),
            "transitions": len(transitions),
        }
        with open(metrics_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print("Not enough history to fine-tune (need >= 32). Metrics written.")
        return

    agent = DQNAgent(STATE_SIZE_V2, 4)
    if prod.exists():
        # Only load if compatible with v2
        import torch
        from ml.rl.state_encoder import infer_state_size_from_checkpoint

        state_dict = torch.load(prod, map_location="cpu")
        if infer_state_size_from_checkpoint(state_dict) == STATE_SIZE_V2:
            agent.model.load_state_dict(state_dict)
            agent.update_target_network()
            print("Loaded production v2 weights as fine-tune starting point")
        else:
            print("Production model is not v2; training fine-tune from scratch on history")

    for t in transitions:
        agent.remember(*t)

    # Reduce exploration during fine-tune
    agent.epsilon = 0.05

    for epoch in range(args.epochs):
        agent.replay()
        if epoch % 5 == 0:
            print(f"fine-tune epoch={epoch} epsilon={agent.epsilon:.3f}", flush=True)

    agent.save(str(out))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "docs": len(docs),
        "transitions": len(transitions),
        "epochs": args.epochs,
        "output": str(out),
        "promoted": False,
    }

    if args.promote:
        shutil.copy2(prod, save_dir / "dqn_model_pre_finetune_backup.pth")
        shutil.copy2(out, prod)
        payload["promoted"] = True

    with open(metrics_out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Fine-tuned model saved: {out}")
    print(f"Metrics: {metrics_out}")
    if not args.promote:
        print("Production model unchanged (pass --promote to replace)")


if __name__ == "__main__":
    main()
