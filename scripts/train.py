#!/usr/bin/env python3
"""The weekly training step — a full batch rebuild from the entire dataset.

Every Sunday CI runs this once:
  1. aggregate the complete ledger (dataset.jsonl): per state, each
     teacher's latest label counts once
  2. the aggregated counts BECOME the policy weights — policy.json is
     rebuilt from all data in one step, so it is always reproducible
     from the dataset alone
  3. archive the week, roll the counter, re-render the replay

votes.json (this week's live tally) is cleared, but nothing is lost:
the ledger keeps every vote ever cast.
"""

import engine
import rollout


def main():
    level = engine.load("level.json")
    old_policy = engine.load("policy.json")
    state = engine.load("state.json")
    dataset = engine.load_dataset()

    # record what this week's run looked like before the update
    steps, died_at, death_state = engine.rollout(level, old_policy)
    distance = steps[-1][1] if died_at is not None else level["length"] - 1

    # batch rebuild: the crowd's aggregated labels are the weights
    agg = engine.aggregate(dataset)
    policy = {s: {**engine.DEFAULT_Q, **counts} for s, counts in agg.items()}
    engine.save("policy.json", policy)

    week_votes = [r for r in dataset if r["week"] == state["week"]]
    taught = None
    if death_state and death_state in agg and any(agg[death_state].values()):
        taught = max(engine.ACTIONS, key=lambda a: agg[death_state].get(a, 0.0))

    state["history"].append({
        "week": state["week"],
        "distance": distance,
        "outcome": "finished" if died_at is None else f"died at {distance}m seeing {death_state}",
        "taught": taught,
        "votes": len(week_votes),
    })
    state["week"] += 1
    engine.save("state.json", state)
    engine.save("votes.json", {"question": None, "votes": {}})  # rollout.py sets the new question

    rollout.main()
    print(f"week trained · policy rebuilt from {len(dataset)} ledger events · taught={taught}")


if __name__ == "__main__":
    main()
