"""Bounded real-dependency smoke, not a learning-performance experiment."""
import os
from pathlib import Path
import random
import runpy

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np
import pygame
import torch

random.seed(7)
np.random.seed(7)
torch.manual_seed(7)
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

original_get = pygame.event.get
event_reads = 0


def quit_after_one_frame(*args, **kwargs):
    global event_reads
    event_reads += 1
    if event_reads > 1:
        raise AssertionError("Game did not stop after the injected QUIT event")
    return original_get(*args, **kwargs) + [pygame.event.Event(pygame.QUIT)]


pygame.event.get = quit_after_one_frame
try:
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "ai.py"))
finally:
    pygame.event.get = original_get
    pygame.quit()

assert event_reads == 1
assert namespace["running"] is False
agent = namespace["ai_savior"]
device = namespace["device"]
state = agent.get_state(namespace["zombies"])
assert state.shape == (5,)
assert np.isfinite(state).all()

with torch.no_grad():
    values = agent.q_network(torch.from_numpy(state).unsqueeze(0).to(device))
assert tuple(values.shape) == (1, 5)
assert bool(torch.isfinite(values).all())
agent.epsilon = 0.0
assert agent.select_action(state) in range(5)

# Synthetic in-memory fixtures exercise tensor shape/optimisation contracts only.
# They are not observed game trajectories, a training dataset or policy evidence.
agent.replay_buffer.buffer.clear()
for i in range(64):
    next_state = state.copy()
    terminal = i % 7 == 0
    next_state[-1] = 0.0 if terminal else 0.9
    agent.replay_buffer.add((state.copy(), i % 5, -0.5, next_state, terminal))
before = [parameter.detach().clone() for parameter in agent.q_network.parameters()]
agent.epsilon = 0.1001
agent.train()
after = list(agent.q_network.parameters())
assert agent.steps == 1
assert agent.epsilon == namespace["EPSILON_MIN"]
assert any(not torch.equal(left, right) for left, right in zip(before, after))
assert all(bool(torch.isfinite(parameter).all()) for parameter in after)
assert all(torch.equal(left, right) for left, right in
           zip(agent.q_network.parameters(), agent.target_network.parameters()))
print("PASS: bounded Pygame startup/exit; real Q forward pass and finite optimiser update")

