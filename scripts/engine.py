"""The world and the agent.

A deterministic side-scroller on a 1-D track. The agent sees the next
three cells (its "state") and picks one of three actions:

    RUN        move +1 — dies if the next cell is a hazard
    JUMP       move +2, airborne over cell +1 — dies if it lands on a hazard
    LONG JUMP  move +3, airborne over cells +1 and +2 — dies on a bad landing

The policy is a plain Q-table: state pattern -> action scores. Untrained,
it only knows how to RUN. Humans teach it the rest, one death at a time.
"""

import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
ACTIONS = ["RUN", "JUMP", "LONG JUMP"]
DEFAULT_Q = {"RUN": 0.1, "JUMP": 0.0, "LONG JUMP": 0.0}  # baby model: run at everything


def load(name):
    with open(os.path.join(ROOT, name)) as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(ROOT, name), "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def cell(level, x):
    return level["obstacles"].get(str(x), ".") if 0 <= x < level["length"] else "."


def window(level, x):
    """What the agent sees: the three cells ahead of it."""
    return "".join(cell(level, x + i) for i in (1, 2, 3))


def choose(policy, state):
    q = {**DEFAULT_Q, **policy.get(state, {})}
    return max(ACTIONS, key=lambda a: q[a])


def rollout(level, policy):
    """Run the greedy policy until death or the finish line.

    Returns (trajectory, died_at, death_state) where trajectory is a list of
    (action, from_x, to_x) steps. died_at / death_state are None on a win.
    """
    x, steps = 0, []
    stride = {"RUN": 1, "JUMP": 2, "LONG JUMP": 3}
    while x < level["length"] - 1 and len(steps) < 200:
        state = window(level, x)
        action = choose(policy, state)
        target = x + stride[action]
        steps.append((action, x, target))
        if cell(level, target) != ".":  # ran into it or landed on it
            return steps, target, state
        x = target
    return steps, None, None
