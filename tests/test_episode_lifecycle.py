"""Exercise production method bodies without importing the interactive game.

The game imports Pygame/PyTorch and launches a window at module load. These
focused source-isolated checks run its actual reset/early-return statements;
they do not constitute a full model, rendering or training execution.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "ai.py"
MODULE = ast.parse(SOURCE.read_text(encoding="utf-8"))
AGENT = next(node for node in MODULE.body
             if isinstance(node, ast.ClassDef) and node.name == "AISaviorRL")


def method(name):
    return next(node for node in AGENT.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def function_from(node, **globals_):
    namespace = dict(globals_)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace[node.name]


def decay(agent):
    # Execute the production epsilon update after a successful optimiser step.
    train = method("train")
    update = train.body[-1]
    namespace = {"self": agent, "EPSILON_MIN": 0.1, "EPSILON_DECAY": 0.995}
    exec(compile(ast.Module(body=[update], type_ignores=[]), str(SOURCE), "exec"), namespace)


class ExplorationTests(unittest.TestCase):
    def test_decay_clamps_just_above_minimum(self):
        agent = SimpleNamespace(epsilon=0.1001)
        decay(agent)
        self.assertEqual(agent.epsilon, 0.1)

    def test_decay_retains_existing_rate_above_floor(self):
        agent = SimpleNamespace(epsilon=1.0)
        decay(agent)
        self.assertAlmostEqual(agent.epsilon, 0.995)

    def test_minimum_is_stable(self):
        agent = SimpleNamespace(epsilon=0.1)
        decay(agent)
        self.assertEqual(agent.epsilon, 0.1)

    def test_replay_warmup_does_not_decay_exploration(self):
        agent = SimpleNamespace(epsilon=0.8, replay_buffer=[])
        function_from(method("train"), BATCH_SIZE=64)(agent)
        self.assertEqual(agent.epsilon, 0.8)


class EpisodeResetTests(unittest.TestCase):
    def agent(self):
        return SimpleNamespace(
            x=10, y=20, health=0, bullets=[object()], kills=8,
            highest_kills=5, trials=3, last_pos=(10, 20), stay_timer=2.9,
            blink_timer=0.8, show_level_text=False, level_display_timer=1.9,
            q_network=object(), target_network=object(), optimizer=object(),
            replay_buffer=object(), steps=512, epsilon=0.42,
        )

    def test_reset_restarts_world_and_presentation_state(self):
        agent = self.agent()
        function_from(method("reset"), CENTER_X=600, CENTER_Y=350)(agent)
        self.assertEqual((agent.x, agent.y, agent.health), (600, 350, 100))
        self.assertEqual((agent.bullets, agent.kills), ([], 0))
        self.assertEqual((agent.last_pos, agent.stay_timer), ((600, 350), 0.0))
        self.assertEqual(agent.blink_timer, 0.0)
        self.assertTrue(agent.show_level_text)
        self.assertEqual(agent.level_display_timer, 0.0)

    def test_reset_preserves_learning_and_updates_episode_counters(self):
        agent = self.agent()
        preserved = {name: getattr(agent, name) for name in
                     ("q_network", "target_network", "optimizer", "replay_buffer")}
        function_from(method("reset"), CENTER_X=600, CENTER_Y=350)(agent)
        for name, value in preserved.items():
            self.assertIs(getattr(agent, name), value)
        self.assertEqual((agent.steps, agent.epsilon), (512, 0.42))
        self.assertEqual((agent.highest_kills, agent.trials), (8, 4))


if __name__ == "__main__":
    unittest.main()
