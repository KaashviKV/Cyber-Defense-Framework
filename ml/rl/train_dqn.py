import os
import sys

# Add project root to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

sys.path.append(PROJECT_ROOT)

from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.dqn_agent import DQNAgent


# ============================
# State Encoder
# ============================

def encode_state(state):

    severity = state["severity"] / 100
    risk = state["risk_score"] / 100

    return [severity, risk]


# ============================
# Training
# ============================

env = CyberDefenseEnvironment()

state_size = 2
action_size = 4

agent = DQNAgent(state_size, action_size)

EPISODES = 500

print("\n==========================")
print("Training DQN Agent")
print("==========================")

for episode in range(EPISODES):

    state = env.reset()

    state = encode_state(state)

    done = False

    total_reward = 0

    while not done:

        action = agent.act(state)

        next_state, reward, done = env.step(action)

        next_state = encode_state(next_state)

        agent.remember(
            state,
            action,
            reward,
            next_state,
            done
        )

        state = next_state

        total_reward += reward

        agent.replay()

    if episode % 20 == 0:

        print(
            f"Episode {episode:3d} | "
            f"Reward = {total_reward:3d} | "
            f"Epsilon = {agent.epsilon:.3f}"
        )

    if episode % 25 == 0:
        agent.update_target_network()


print("\nTraining Finished!")

SAVE_DIR = os.path.join(PROJECT_ROOT, "ml", "saved_models")
os.makedirs(SAVE_DIR, exist_ok=True)

MODEL_PATH = os.path.join(SAVE_DIR, "dqn_model.pth")

agent.save(MODEL_PATH)

print("\nModel Saved Successfully!")
print(MODEL_PATH)