"""Execute the actual transition block against deterministic fake worlds."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "ai.py"
LEVELS = [25, 50, 75, 100, 300]


def run_transition(health, level, zombies):
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    loop = next(node for node in module.body if isinstance(node, ast.While))
    start = next(i for i, node in enumerate(loop.body)
                 if isinstance(node, ast.Assign)
                 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id == "dead")
    stop = next(i for i, node in enumerate(loop.body)
                if isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "screen")
    records, events = [], []

    class Agent:
        x, y = 600, 350

        def get_state(self, world):
            return (self.health, self.level, len(world), self.x, self.y)

        def train(self):
            events.append("train")

        def reset(self):
            events.append("reset")
            self.health = 100

        def advance_level(self):
            events.append("advance")
            self.level += 1
            self.x, self.y = 600, 350

    def start_level(new_level):
        events.append(("spawn", new_level))
        return [SimpleNamespace(x=0, y=0) for _ in range(LEVELS[new_level - 1])]

    agent = Agent()
    agent.health, agent.level = health, level
    agent.replay_buffer = SimpleNamespace(add=records.append)
    namespace = dict(ai_savior=agent, zombies=zombies, st="before", act=3,
                     CENTER_X=600, CENTER_Y=350, CENTER_RADIUS=200,
                     LEVELS=LEVELS, math=__import__("math"), start_level=start_level)
    exec(compile(ast.Module(body=loop.body[start:stop], type_ignores=[]),
                 str(SOURCE), "exec"), namespace)
    return records, agent, namespace["zombies"], events


class TerminalTransitionTests(unittest.TestCase):
    def test_terminal_record_precedes_death_reset(self):
        records, agent, world, events = run_transition(0, 1, [])
        self.assertEqual(len(records), 1)
        _, _, reward, next_state, done = records[0]
        self.assertEqual(next_state[:3], (0, 1, 0))
        self.assertTrue(done)
        self.assertLess(reward, -90)
        self.assertEqual((agent.health, agent.level, len(world)), (100, 1, 25))
        self.assertEqual(events, ["train", "reset", ("spawn", 1)])

    def test_final_wave_is_terminal_without_a_death_penalty(self):
        records, agent, world, events = run_transition(80, 5, [])
        _, _, reward, next_state, done = records[0]
        self.assertTrue(done)
        self.assertEqual(next_state[:3], (80, 5, 0))
        self.assertAlmostEqual(reward, -0.5)
        self.assertEqual((agent.health, agent.level, len(world)), (100, 1, 25))
        self.assertEqual(events, ["train", "reset", ("spawn", 1)])

    def test_intermediate_wave_continues_with_actual_successor_state(self):
        records, agent, world, events = run_transition(60, 2, [])
        _, _, reward, next_state, done = records[0]
        self.assertFalse(done)
        self.assertAlmostEqual(reward, -0.5)
        self.assertEqual(next_state[:3], (60, 3, 75))
        self.assertEqual((agent.health, agent.level, len(world)), (60, 3, 75))
        self.assertEqual(events, ["advance", ("spawn", 3), "train"])

    def test_active_wave_does_not_reset_or_advance(self):
        zombie = SimpleNamespace(x=600, y=350)
        records, agent, world, events = run_transition(50, 2, [zombie])
        self.assertFalse(records[0][-1])
        self.assertEqual(records[0][3][:3], (50, 2, 1))
        self.assertIs(world[0], zombie)
        self.assertEqual(events, ["train"])


if __name__ == "__main__":
    unittest.main()

