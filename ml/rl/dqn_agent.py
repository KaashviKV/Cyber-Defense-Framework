import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


# ==========================
# Deep Q Network
# ==========================

class DQN(nn.Module):

    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()

        self.network = nn.Sequential(

            nn.Linear(state_size, 128),
            nn.ReLU(),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, action_size)

        )

    def forward(self, x):
        return self.network(x)


# ==========================
# DQN Agent
# ==========================

class DQNAgent:

    def __init__(self, state_size, action_size):

        self.state_size = state_size
        self.action_size = action_size

        # Hyperparameters
        self.gamma = 0.95
        self.learning_rate = 0.001

        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

        self.batch_size = 64

        # Replay Memory
        self.memory = deque(maxlen=5000)

        # Device
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Networks
        self.model = DQN(state_size, action_size).to(self.device)
        self.target_model = DQN(state_size, action_size).to(self.device)

        self.update_target_network()

        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate
        )

        self.loss_function = nn.MSELoss()

    # ==========================
    # Copy Weights
    # ==========================

    def update_target_network(self):
        self.target_model.load_state_dict(
            self.model.state_dict()
        )

    # ==========================
    # Store Experience
    # ==========================

    def remember(
            self,
            state,
            action,
            reward,
            next_state,
            done):

        self.memory.append(
            (
                state,
                action,
                reward,
                next_state,
                done
            )
        )

    # ==========================
    # Action Selection
    # ==========================

    def act(self, state):

        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)

        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            q_values = self.model(state)

        return torch.argmax(q_values).item()

    # ==========================
    # Experience Replay (batched)
    # ==========================

    def replay(self):

        if len(self.memory) < self.batch_size:
            return

        mini_batch = random.sample(self.memory, self.batch_size)

        states = torch.FloatTensor([item[0] for item in mini_batch]).to(self.device)
        actions = torch.LongTensor([item[1] for item in mini_batch]).to(self.device)
        rewards = torch.FloatTensor([item[2] for item in mini_batch]).to(self.device)
        next_states = torch.FloatTensor([item[3] for item in mini_batch]).to(self.device)
        dones = torch.FloatTensor([float(item[4]) for item in mini_batch]).to(self.device)

        q_values = self.model(states)
        q_selected = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0]
            targets = rewards + self.gamma * next_q * (1.0 - dones)

        loss = self.loss_function(q_selected, targets)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    # ==========================
    # Save Model
    # ==========================

    def save(self, path):

        torch.save(
            self.model.state_dict(),
            path
        )

    # ==========================
    # Load Model
    # ==========================

    def load(self, path):

        self.model.load_state_dict(
            torch.load(path)
        )

        self.model.eval()