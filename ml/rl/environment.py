"""
Cyber defense RL environment.

Supports:
- CTI-aware state (severity, confidence, risk, VT, AbuseIPDB)
- Multi-step attack escalation episodes
- Reward shaping with false-positive penalties
"""

from __future__ import annotations

import random
from typing import Any


class CyberDefenseEnvironment:
    """
    State features (normalized externally):
        severity, confidence, risk_score, virustotal_score, abuseipdb_score

    Actions:
        0 -> NO_ACTION
        1 -> ALERT_ADMIN
        2 -> BLOCK_IP
        3 -> ISOLATE_HOST
    """

    def __init__(
        self,
        max_steps: int = 5,
        multi_step: bool = True,
        cost_sensitive: bool = False,
        sequential_effects: bool = False,
    ):
        self.actions = [
            "NO_ACTION",
            "ALERT_ADMIN",
            "BLOCK_IP",
            "ISOLATE_HOST",
        ]
        self.max_steps = max(1, int(max_steps))
        self.multi_step = bool(multi_step)
        self.cost_sensitive = bool(cost_sensitive)
        self.sequential_effects = bool(sequential_effects)
        self.state: dict[str, Any] | None = None
        self.steps_taken = 0
        self._escalation_path: list[str] = []
        self._containment = 0.0

        self.attack_profiles = {
            "BENIGN": {
                "severity": 0,
                "confidence": (70, 99),
                "vt": (0, 5),
                "abuse": (0, 10),
            },
            "PortScan": {
                "severity": 60,
                "confidence": (55, 95),
                "vt": (5, 35),
                "abuse": (20, 60),
            },
            "Bot": {
                "severity": 55,
                "confidence": (50, 90),
                "vt": (10, 45),
                "abuse": (25, 70),
            },
            "FTP-Patator": {
                "severity": 65,
                "confidence": (60, 95),
                "vt": (15, 50),
                "abuse": (30, 75),
            },
            "SSH-Patator": {
                "severity": 70,
                "confidence": (60, 95),
                "vt": (20, 55),
                "abuse": (35, 80),
            },
            "Web Attack": {
                "severity": 75,
                "confidence": (55, 92),
                "vt": (25, 70),
                "abuse": (40, 85),
            },
            "DoS": {
                "severity": 82,
                "confidence": (65, 98),
                "vt": (20, 60),
                "abuse": (45, 90),
            },
            "DDoS": {
                "severity": 95,
                "confidence": (70, 99),
                "vt": (30, 80),
                "abuse": (60, 100),
            },
            "Infiltration": {
                "severity": 98,
                "confidence": (65, 97),
                "vt": (40, 90),
                "abuse": (55, 100),
            },
            "Heartbleed": {
                "severity": 100,
                "confidence": (75, 99),
                "vt": (50, 95),
                "abuse": (60, 100),
            },
        }

        self.escalation_chains = [
            ["BENIGN"],
            ["PortScan", "SSH-Patator"],
            ["PortScan", "Bot", "DDoS"],
            ["Web Attack", "Infiltration"],
            ["DoS", "DDoS"],
            ["Bot", "Infiltration"],
            ["FTP-Patator", "SSH-Patator", "Infiltration"],
            ["Heartbleed"],
            ["DDoS"],
            ["Infiltration"],
        ]

    def reset(self) -> dict[str, Any]:
        if self.multi_step:
            chain = random.choice(self.escalation_chains)
            # Truncate/pad chain to max_steps length by repeating last stage
            self._escalation_path = list(chain[: self.max_steps])
            while len(self._escalation_path) < self.max_steps:
                self._escalation_path.append(self._escalation_path[-1])
        else:
            attack = random.choice(list(self.attack_profiles.keys()))
            self._escalation_path = [attack]

        self.steps_taken = 0
        self._containment = 0.0
        self.state = self._build_state(self._escalation_path[0])
        return dict(self.state)

    def step(self, action: int) -> tuple[dict[str, Any], float, bool]:
        if self.state is None:
            self.reset()

        assert self.state is not None
        reward = self.calculate_reward(self.state, action)
        if self.sequential_effects:
            if action >= 2:
                self._containment = min(1.0, self._containment + (0.45 if action == 2 else 0.7))
            elif action == 0:
                self._containment = max(0.0, self._containment - 0.08)

        self.steps_taken += 1

        done = (not self.multi_step) or (self.steps_taken >= len(self._escalation_path))
        if done:
            # Start a fresh episode for the next reset-like transition
            next_state = self.reset()
            return next_state, float(reward), True

        next_attack = self._escalation_path[self.steps_taken]
        self.state = self._build_state(next_attack, previous=self.state)
        return dict(self.state), float(reward), False

    def _build_state(
        self,
        attack: str,
        previous: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = self.attack_profiles[attack]
        severity = float(profile["severity"])
        confidence = float(random.randint(*profile["confidence"]))
        vt = float(random.randint(*profile["vt"]))
        abuse = float(random.randint(*profile["abuse"]))

        # Risk approximates the production weighted fusion, with noise
        risk = (
            0.40 * severity
            + 0.20 * confidence
            + 0.20 * vt
            + 0.20 * abuse
            + random.uniform(-4, 4)
        )
        risk = max(0.0, min(100.0, risk))
        if self.sequential_effects and self._containment > 0:
            risk *= 1.0 - 0.55 * self._containment
            vt *= 1.0 - 0.35 * self._containment
            abuse *= 1.0 - 0.35 * self._containment

        # Mild escalation continuity: keep scores from drifting too low mid-episode
        if previous and previous.get("attack") != "BENIGN" and attack != "BENIGN":
            risk = max(risk, float(previous.get("risk_score", 0)) - 5)
            vt = max(vt, float(previous.get("virustotal_score", 0)) * 0.8)
            abuse = max(abuse, float(previous.get("abuseipdb_score", 0)) * 0.8)

        return {
            "attack": attack,
            "severity": severity,
            "confidence": confidence,
            "risk_score": round(risk, 2),
            "virustotal_score": round(vt, 2),
            "abuseipdb_score": round(abuse, 2),
        }

    def calculate_reward(self, state: dict[str, Any], action: int) -> float:
        if self.cost_sensitive:
            return self._cost_sensitive_reward(state, action)

        attack = state.get("attack", "BENIGN")
        risk = float(state.get("risk_score", 0) or 0)
        vt = float(state.get("virustotal_score", 0) or 0)
        abuse = float(state.get("abuseipdb_score", 0) or 0)
        cti_heat = max(vt, abuse)

        # Ideal action by policy bands (used for shaping, not hard constraint)
        if attack == "BENIGN" and risk < 25 and cti_heat < 20:
            ideal = 0
        elif risk >= 90 or (risk >= 80 and cti_heat >= 70):
            ideal = 3
        elif risk >= 70 or cti_heat >= 60:
            ideal = 2
        elif risk >= 40:
            ideal = 1
        else:
            ideal = 0

        reward = 0.0

        if action == ideal:
            reward += 12.0
        elif abs(action - ideal) == 1:
            reward += 4.0
        else:
            reward -= 6.0

        # Extra false-positive penalty: blocking/isolating benign/low-risk
        if attack == "BENIGN" or risk < 25:
            if action == 2:
                reward -= 8.0
            elif action == 3:
                reward -= 12.0
            elif action == 0:
                reward += 3.0

        # Extra false-negative penalty: weak response under hot CTI
        if cti_heat >= 75 and action in (0, 1):
            reward -= 10.0
        if risk >= 90 and action in (0, 1):
            reward -= 10.0

        # Mild bonus for escalating with CTI agreement
        if cti_heat >= 60 and action >= 2:
            reward += 3.0

        return float(reward)

    def _cost_sensitive_reward(self, state: dict[str, Any], action: int) -> float:
        attack = state.get("attack", "BENIGN")
        risk = float(state.get("risk_score", 0) or 0)
        malicious = attack != "BENIGN" or risk >= 70
        critical = risk >= 85 or attack in {"DDoS", "Infiltration", "Heartbleed"}
        reward = 0.0
        if action == 0:
            reward += 10.0 if not malicious else (-120.0 if critical else -40.0)
        elif action == 1:
            reward += 15.0 if malicious else -5.0
        elif action == 2:
            if not malicious:
                reward -= 100.0
            elif critical:
                reward += 60.0
            else:
                reward += 40.0
        else:
            if not malicious:
                reward -= 130.0
            elif critical:
                reward += 70.0
            else:
                reward += 20.0
        return float(reward)

    def get_action_name(self, action: int) -> str:
        return self.actions[action]


if __name__ == "__main__":
    env = CyberDefenseEnvironment(multi_step=True, max_steps=4)
    state = env.reset()
    print("Initial:", state)
    for i in range(4):
        action = random.randint(0, 3)
        next_state, reward, done = env.step(action)
        print(f"step={i} action={env.get_action_name(action)} reward={reward} done={done}")
        print(" next:", next_state)
        if done:
            break
