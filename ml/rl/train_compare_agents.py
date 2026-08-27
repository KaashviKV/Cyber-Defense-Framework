"""
Train and compare DQN vs Double DQN on the same CTI-aware environment.
Saves comparison metrics; does not overwrite production dqn_model.pth
unless --promote-best is passed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

from ml.rl.double_dqn_agent import DoubleDQNAgent
from ml.rl.dqn_agent import DQNAgent
from ml.rl.environment import CyberDefenseEnvironment
from ml.rl.state_encoder import STATE_SIZE_V2, encode_from_mapping


def train_agent(agent, env, episodes: int, label: str) -> dict:
    rewards = []
    print(f"\n--- Training {label} ({episodes} episodes) ---", flush=True)
    for episode in range(episodes):
        state = encode_from_mapping(env.reset(), state_size=STATE_SIZE_V2)
        done = False
        total = 0.0
        while not done:
            action = agent.act(state)
            nxt, reward, done = env.step(action)
            next_state = encode_from_mapping(nxt, state_size=STATE_SIZE_V2)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total += reward
            agent.replay()
        rewards.append(total)
        if episode % 25 == 0:
            agent.update_target_network()
            avg = sum(rewards[-25:]) / max(1, len(rewards[-25:]))
            print(f"{label} ep={episode:4d} reward={total:7.1f} avg25={avg:7.1f} eps={agent.epsilon:.3f}", flush=True)
    return {
        "algorithm": label,
        "episodes": episodes,
        "avg_reward_last_50": sum(rewards[-50:]) / max(1, len(rewards[-50:])),
        "reward_history": rewards,
        "final_epsilon": agent.epsilon,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--promote-best", action="store_true", help="Overwrite dqn_model.pth with best agent")
    args = parser.parse_args()

    save_dir = os.path.join(PROJECT_ROOT, "ml", "saved_models")
    os.makedirs(save_dir, exist_ok=True)

    env = CyberDefenseEnvironment(max_steps=4, multi_step=True)
    dqn = DQNAgent(STATE_SIZE_V2, 4)
    ddqn = DoubleDQNAgent(STATE_SIZE_V2, 4)

    dqn_metrics = train_agent(dqn, env, args.episodes, "DQN")
    ddqn_metrics = train_agent(ddqn, CyberDefenseEnvironment(max_steps=4, multi_step=True), args.episodes, "DoubleDQN")

    dqn_path = os.path.join(save_dir, "dqn_model_compare.pth")
    ddqn_path = os.path.join(save_dir, "double_dqn_model.pth")
    dqn.save(dqn_path)
    ddqn.save(ddqn_path)

    best = "DoubleDQN" if ddqn_metrics["avg_reward_last_50"] >= dqn_metrics["avg_reward_last_50"] else "DQN"
    best_path = ddqn_path if best == "DoubleDQN" else dqn_path

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dqn": dqn_metrics,
        "double_dqn": ddqn_metrics,
        "best": best,
        "paths": {"dqn": dqn_path, "double_dqn": ddqn_path},
        "promoted": False,
    }

    if args.promote_best:
        prod = os.path.join(save_dir, "dqn_model.pth")
        shutil.copy2(prod, os.path.join(save_dir, "dqn_model_pre_promote_backup.pth"))
        shutil.copy2(best_path, prod)
        payload["promoted"] = True
        payload["promoted_path"] = prod

    out = os.path.join(save_dir, "dqn_vs_double_dqn.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== DQN vs Double DQN ===")
    print(f"DQN avg_last_50:        {dqn_metrics['avg_reward_last_50']:.2f}")
    print(f"DoubleDQN avg_last_50:  {ddqn_metrics['avg_reward_last_50']:.2f}")
    print(f"Best: {best}")
    print(f"Saved: {out}")
    if args.promote_best:
        print("Promoted best weights to dqn_model.pth")
    else:
        print("Production dqn_model.pth left unchanged (pass --promote-best to replace)")


if __name__ == "__main__":
    main()
