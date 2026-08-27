"""
Train DQN for ICDF defensive action selection.

Trains a CTI-aware (state_size=5) policy by default and saves:
  ml/saved_models/dqn_model.pth

A backup of any existing model is written to:
  ml/saved_models/dqn_model_v1_legacy.pth  (only if previous was v1)
  ml/saved_models/dqn_model_backup.pth     (always, when previous exists)
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

from ml.rl.dqn_agent import DQNAgent
from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.state_encoder import STATE_SIZE_V2, encode_from_mapping, infer_state_size_from_checkpoint

import torch


def main(
    episodes: int = 400,
    max_steps: int = 4,
    multi_step: bool = True,
) -> None:
    env = CyberDefenseEnvironment(max_steps=max_steps, multi_step=multi_step)
    state_size = STATE_SIZE_V2
    action_size = 4
    agent = DQNAgent(state_size, action_size)

    save_dir = os.path.join(PROJECT_ROOT, "ml", "saved_models")
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "dqn_model.pth")
    metrics_path = os.path.join(save_dir, "dqn_training_metrics.json")

    # Backup existing model before overwrite
    if os.path.exists(model_path):
        backup_path = os.path.join(save_dir, "dqn_model_backup.pth")
        shutil.copy2(model_path, backup_path)
        try:
            old = torch.load(model_path, map_location="cpu")
            if infer_state_size_from_checkpoint(old) == 2:
                legacy_path = os.path.join(save_dir, "dqn_model_v1_legacy.pth")
                shutil.copy2(model_path, legacy_path)
                print(f"Legacy v1 model preserved at: {legacy_path}")
        except Exception as exc:
            print(f"Warning: could not inspect old model ({exc})")
        print(f"Backup saved at: {backup_path}")

    print("\n==========================")
    print("Training CTI-Aware DQN")
    print(f"state_size={state_size} actions={action_size} episodes={episodes}")
    print(f"multi_step={multi_step} max_steps={max_steps}")
    print("==========================")

    reward_history: list[float] = []

    for episode in range(episodes):
        state = encode_from_mapping(env.reset(), state_size=state_size)
        done = False
        total_reward = 0.0

        while not done:
            action = agent.act(state)
            next_raw, reward, done = env.step(action)
            next_state = encode_from_mapping(next_raw, state_size=state_size)

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            # Replay once per step is enough with batched updates
            agent.replay()

        reward_history.append(total_reward)

        if episode % 25 == 0:
            avg = sum(reward_history[-25:]) / max(1, len(reward_history[-25:]))
            print(
                f"Episode {episode:4d} | "
                f"Reward = {total_reward:7.1f} | "
                f"Avg25 = {avg:7.1f} | "
                f"Epsilon = {agent.epsilon:.3f}",
                flush=True,
            )

        if episode % 25 == 0:
            agent.update_target_network()

    agent.save(model_path)

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "DQN",
        "model_version": "v2_cti",
        "state_size": state_size,
        "action_size": action_size,
        "episodes": episodes,
        "multi_step": multi_step,
        "max_steps": max_steps,
        "final_epsilon": agent.epsilon,
        "reward_history": reward_history,
        "avg_reward_last_50": (
            sum(reward_history[-50:]) / max(1, len(reward_history[-50:]))
        ),
        "model_path": model_path,
    }
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print("\nTraining Finished!")
    print(f"Model saved: {model_path}")
    print(f"Metrics saved: {metrics_path}")
    print(f"Avg reward (last 50): {metrics['avg_reward_last_50']:.2f}")


if __name__ == "__main__":
    main()
