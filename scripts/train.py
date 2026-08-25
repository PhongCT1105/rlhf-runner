#!/usr/bin/env python3
"""The weekly training step — this is where the crowd's votes become weights.

Every Sunday CI runs this once:
  1. take the open question (the state the agent died in)
  2. the majority-voted action becomes the supervised label for that state
  3. write the updated Q-table back to policy.json  ← real weight update
  4. archive the week, roll the counter, re-render the replay

No votes -> no update; the agent stays stuck and the question stays open.
"""

from collections import Counter

import engine
import rollout


def main():
    level = engine.load("level.json")
    policy = engine.load("policy.json")
    state = engine.load("state.json")
    votes = engine.load("votes.json")

    steps, died_at, death_state = engine.rollout(level, policy)
    distance = steps[-1][1] if died_at is not None else level["length"] - 1
    taught = None

    ballots = Counter(votes.get("votes", {}).values())
    if votes.get("question") and ballots and votes["question"] == death_state:
        taught = ballots.most_common(1)[0][0]
        q = {**engine.DEFAULT_Q, **policy.get(death_state, {})}
        q[taught] = max(q.values()) + 1.0  # crowd label becomes the argmax
        policy[death_state] = q
        engine.save("policy.json", policy)

    state["history"].append({
        "week": state["week"],
        "distance": distance,
        "outcome": "finished" if died_at is None else f"died at {distance}m seeing {death_state}",
        "taught": taught,
        "votes": sum(ballots.values()),
    })
    state["week"] += 1
    engine.save("state.json", state)
    engine.save("votes.json", {"question": None, "votes": {}})  # rollout.py sets the new question

    rollout.main()
    print(f"week trained · taught={taught} · votes={sum(ballots.values())}")


if __name__ == "__main__":
    main()
