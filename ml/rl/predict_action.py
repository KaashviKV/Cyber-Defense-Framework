"""
RL decision maker with backward-compatible DQN loading.

- Auto-detects state size from checkpoint (v1=2, v2=5)
- Accepts optional CTI features; ignored safely for legacy models
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import torch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

from ml.rl.dqn_agent import DQN
from ml.rl.state_encoder import (
    STATE_SIZE_V1,
    STATE_SIZE_V2,
    encode_state,
    infer_state_size_from_checkpoint,
)


class RLDecisionMaker:
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.actions = [
            "NO_ACTION",
            "ALERT_ADMIN",
            "BLOCK_IP",
            "ISOLATE_HOST",
        ]

        self.model_path = model_path or os.path.join(
            PROJECT_ROOT,
            "ml",
            "saved_models",
            "dqn_model.pth",
        )

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"DQN model not found: {self.model_path}")

        state_dict = torch.load(self.model_path, map_location=self.device)
        self.state_size = infer_state_size_from_checkpoint(state_dict)
        self.model_version = "v2_cti" if self.state_size == STATE_SIZE_V2 else "v1_legacy"

        self.model = DQN(
            state_size=self.state_size,
            action_size=len(self.actions),
        ).to(self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def predict(
        self,
        severity,
        risk_score,
        confidence: float = 0.0,
        virustotal_score: float = 0.0,
        abuseipdb_score: float = 0.0,
    ) -> str:
        """
        Predict defensive action.

        Optional CTI/confidence arguments are used when a CTI-aware (v2)
        model is loaded. Legacy v1 models continue to use severity+risk only.
        """
        state_values = encode_state(
            severity=float(severity),
            risk_score=float(risk_score),
            confidence=float(confidence or 0.0),
            virustotal_score=float(virustotal_score or 0.0),
            abuseipdb_score=float(abuseipdb_score or 0.0),
            state_size=self.state_size,
        )

        state = torch.FloatTensor(state_values).unsqueeze(0).to(self.device)

        with torch.no_grad():
            q_values = self.model(state)
            action_idx = int(torch.argmax(q_values).item())

        return self.actions[action_idx]

    def predict_with_details(
        self,
        severity,
        risk_score,
        confidence: float = 0.0,
        virustotal_score: float = 0.0,
        abuseipdb_score: float = 0.0,
    ) -> dict:
        state_values = encode_state(
            severity=float(severity),
            risk_score=float(risk_score),
            confidence=float(confidence or 0.0),
            virustotal_score=float(virustotal_score or 0.0),
            abuseipdb_score=float(abuseipdb_score or 0.0),
            state_size=self.state_size,
        )
        state = torch.FloatTensor(state_values).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_tensor = self.model(state)[0]
            q_values = [float(v) for v in q_tensor.tolist()]
            action_idx = int(torch.argmax(q_tensor).item())
        return {
            "action": self.actions[action_idx],
            "q_values": q_values,
            "model_version": self.model_version,
            "state_size": self.state_size,
        }


if __name__ == "__main__":
    rl = RLDecisionMaker()
    print(f"Loaded DQN {rl.model_version} (state_size={rl.state_size})")
    print("\n===== RL Decision Maker =====")
    severity = int(input("Attack Severity (0-100): "))
    risk = float(input("Risk Score (0-100): "))
    confidence = float(input("Confidence (0-100) [0]: ") or 0)
    vt = float(input("VirusTotal score (0-100) [0]: ") or 0)
    abuse = float(input("AbuseIPDB score (0-100) [0]: ") or 0)
    action = rl.predict(
        severity,
        risk,
        confidence=confidence,
        virustotal_score=vt,
        abuseipdb_score=abuse,
    )
    print("\nRecommended Action")
    print(action)
