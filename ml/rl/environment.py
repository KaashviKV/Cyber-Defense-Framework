import random


class CyberDefenseEnvironment:
    """
    Reinforcement Learning Environment
    ----------------------------------
    State:
        (Attack Severity, Risk Score)

    Actions:
        0 -> No Action
        1 -> Alert Admin
        2 -> Block IP
        3 -> Isolate Host

    Reward:
        Correct defensive action = Positive reward
        Wrong action = Negative reward
    """

    def __init__(self):

        self.actions = [
            "NO_ACTION",
            "ALERT_ADMIN",
            "BLOCK_IP",
            "ISOLATE_HOST"
        ]

        self.attack_types = {
            "BENIGN": 0,
            "Bot": 55,
            "PortScan": 60,
            "FTP-Patator": 65,
            "SSH-Patator": 70,
            "Web Attack": 75,
            "DoS": 82,
            "DDoS": 95,
            "Heartbleed": 100,
            "Infiltration": 98
        }

        self.state = None

    # ------------------------------------
    # Reset Environment
    # ------------------------------------

    def reset(self):

        attack = random.choice(list(self.attack_types.keys()))

        severity = self.attack_types[attack]

        risk_score = random.randint(
            max(0, severity - 10),
            min(100, severity + 10)
        )

        self.state = {
            "attack": attack,
            "severity": severity,
            "risk_score": risk_score
        }

        return self.state

    # ------------------------------------
    # Step Function
    # ------------------------------------

    def step(self, action):

        attack = self.state["attack"]
        risk = self.state["risk_score"]

        reward = self.calculate_reward(
            attack,
            risk,
            action
        )

        done = True

        next_state = self.reset()

        return next_state, reward, done

    # ------------------------------------
    # Reward Function
    # ------------------------------------

    def calculate_reward(self, attack, risk, action):

        if risk >= 90:

            if action == 3:
                return 20

            elif action == 2:
                return 15

            else:
                return -10

        elif risk >= 70:

            if action == 2:
                return 15

            elif action == 1:
                return 8

            else:
                return -5

        elif risk >= 40:

            if action == 1:
                return 10

            elif action == 0:
                return 3

            else:
                return -2

        else:

            if action == 0:
                return 10

            else:
                return -5

    # ------------------------------------
    # Action Name
    # ------------------------------------

    def get_action_name(self, action):

        return self.actions[action]


# ----------------------------------------
# Testing
# ----------------------------------------

if __name__ == "__main__":

    env = CyberDefenseEnvironment()

    state = env.reset()

    print("\nCurrent State")
    print(state)

    action = random.randint(0, 3)

    print("\nChosen Action")
    print(env.get_action_name(action))

    next_state, reward, done = env.step(action)

    print("\nReward:", reward)

    print("\nNext State")
    print(next_state)