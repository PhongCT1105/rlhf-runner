#!/usr/bin/env python3
"""Count one vote from a GitHub issue.

Reads ISSUE_TITLE ("vote: JUMP") and ISSUE_USER from the environment.
Only the three known actions are ever accepted — arbitrary text from the
issue can never reach the card. One vote per GitHub account per question;
voting again just changes your vote.

Writes the outcome ("counted" / "rejected") to GITHUB_OUTPUT for the
workflow's reply comment.
"""

import os

import engine


def emit(result):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"result={result}\n")
    print(result)


def main():
    title = os.environ.get("ISSUE_TITLE", "")
    user = os.environ.get("ISSUE_USER", "")
    action = title.split(":", 1)[1].strip().upper() if ":" in title else ""

    votes = engine.load("votes.json")
    if action not in engine.ACTIONS or not user or not votes.get("question"):
        emit("rejected")
        return

    votes["votes"][user] = action
    engine.save("votes.json", votes)
    emit("counted")


if __name__ == "__main__":
    main()
