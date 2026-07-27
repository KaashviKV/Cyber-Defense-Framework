import os
import sys
import torch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

sys.path.append(PROJECT_ROOT)

from ml.rl.dqn_agent import DQN


class RLDecisionMaker:

    def __init__(self):

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.actions = [
            "NO_ACTION",
            "ALERT_ADMIN",
            "BLOCK_IP",
            "ISOLATE_HOST"
        ]

        self.model = DQN(
            state_size=2,
            action_size=4
        ).to(self.device)

        model_path = os.path.join(
            PROJECT_ROOT,
            "ml",
            "saved_models",
            "dqn_model.pth"
        )

        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device)
        )

        self.model.eval()

    def predict(self, severity, risk_score):

        state = torch.FloatTensor([
            severity / 100,
            risk_score / 100
        ]).unsqueeze(0).to(self.device)

        with torch.no_grad():

            q_values = self.model(state)

            action = torch.argmax(q_values).item()

        return self.actions[action]


if __name__ == "__main__":

    rl = RLDecisionMaker()

    print("\n===== RL Decision Maker =====")

    severity = int(input("Attack Severity (0-100): "))

    risk = float(input("Risk Score (0-100): "))

    action = rl.predict(severity, risk)

    print("\nRecommended Action")

    print(action)