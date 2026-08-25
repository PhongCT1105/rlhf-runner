#!/usr/bin/env python3
"""Run the current policy through the level and render replay.svg.

The card is fully legible with animations off (SMIL only, everything
visible at t=0): full level, a dotted trace of the run, the robot at its
final position, the crowd's open question, and the weekly learning curve.
"""

import engine

BG, EDGE, DIM, SLATE, TEXT = "#0b0d17", "#1e293b", "#334155", "#94a3b8", "#e2e8f0"
PURPLE, CYAN, GREEN, PINK = "#c084fc", "#22d3ee", "#4ade80", "#f472b6"
MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Menlo, monospace"

W, H = 920, 330
GROUND = 172
ROBOT_Y = GROUND - 9  # sprite center while grounded


def text(x, y, s, fill=TEXT, size=13, anchor="start", weight="400"):
    return (f"<text x='{x}' y='{y}' fill='{fill}' font-size='{size}' font-weight='{weight}' "
            f"text-anchor='{anchor}' font-family=\"{MONO}\">{s}</text>")


def x_px(level, x_cell):
    return 30 + x_cell * (860 / (level["length"] - 1))


def robot(x, y, opacity=1.0, animate=""):
    return (f"<g opacity='{opacity}' transform='translate({x:.1f},{y:.1f})'>" if not animate else
            f"<g>{animate}") + (
        f"<line x1='0' y1='-13' x2='0' y2='-8' stroke='{CYAN}' stroke-width='1.5'/>"
        f"<circle cx='0' cy='-14' r='2' fill='{CYAN}'/>"
        f"<rect x='-8' y='-8' width='16' height='15' rx='4' fill='{PURPLE}'/>"
        f"<circle cx='3' cy='-1' r='2.4' fill='#0b0d17'/><circle cx='3.8' cy='-1.8' r='1' fill='white'/>"
        "</g>")


def run_path(level, steps):
    """The robot's actual route: flat runs, arcs for jumps."""
    if not steps:
        return f"M {x_px(level, 0):.1f} {ROBOT_Y}"
    d = f"M {x_px(level, steps[0][1]):.1f} {ROBOT_Y}"
    for action, fr, to in steps:
        fx, tx = x_px(level, fr), x_px(level, to)
        if action == "RUN":
            d += f" L {tx:.1f} {ROBOT_Y}"
        else:
            lift = 26 if action == "JUMP" else 34
            d += f" Q {(fx + tx) / 2:.1f} {ROBOT_Y - lift} {tx:.1f} {ROBOT_Y}"
    return d


def pattern_glyphs(state):
    return " ".join({"S": "▲", "P": "▼", ".": "·"}[c] for c in state)


def tally_rows(votes):
    counts = {a: 0 for a in engine.ACTIONS}
    for a in votes.values():
        if a in counts:
            counts[a] += 1
    peak = max(max(counts.values()), 1)
    rows = []
    for i, a in enumerate(engine.ACTIONS):
        y = 262 + i * 17
        w = round(120 * counts[a] / peak, 1)
        rows += [
            text(300, y + 9, a, SLATE, 11),
            f"<rect x='386' y='{y}' width='120' height='8' rx='4' fill='{EDGE}'/>",
            f"<rect x='386' y='{y}' width='{max(w, 2 if counts[a] else 0)}' height='8' rx='4' fill='{CYAN}'/>",
            text(514, y + 9, str(counts[a]), TEXT, 11, weight="700"),
        ]
    return rows


def learning_curve(history, current_distance, level_len):
    """Distance reached per week — the real learning curve."""
    x0, y0, w, h = 610, 236, 270, 62
    pts_data = [(e["week"], e["distance"]) for e in history] + [(len(history) + 1, current_distance)]
    max_week = max(len(pts_data), 4)
    out = [text(x0, y0 - 8, "learning curve // distance per week", DIM, 10)]
    coords = []
    for wk, dist in pts_data:
        px = x0 + (wk - 1) * w / max(max_week - 1, 1)
        py = y0 + h - (dist / level_len) * h
        coords.append((px, py))
    if len(coords) > 1:
        out.append("<polyline points='" + " ".join(f"{x:.1f},{y:.1f}" for x, y in coords) +
                   f"' fill='none' stroke='{GREEN}' stroke-width='2'/>")
    for i, (px, py) in enumerate(coords):
        last = i == len(coords) - 1
        out.append(f"<circle cx='{px:.1f}' cy='{py:.1f}' r='3.5' fill='{'none' if last else GREEN}' "
                   f"stroke='{GREEN}' stroke-width='2'/>")
    out.append(text(x0 + w + 4, y0 + h + 4, "goal", DIM, 9))
    out.append(f"<line x1='{x0}' y1='{y0}' x2='{x0 + w}' y2='{y0}' stroke='{EDGE}' stroke-dasharray='3 3'/>")
    return out


def render(level, steps, died_at, death_state, state, votes):
    distance = steps[-1][1] if died_at is not None else level["length"] - 1
    week = state["week"]
    finished = died_at is None

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}' role='img' "
        f"aria-label='A tiny agent learning a platformer level from real human votes, retrained weekly'>",
        f"<rect x='1' y='1' width='{W-2}' height='{H-2}' rx='12' fill='{BG}' stroke='{EDGE}'/>",
        text(28, 34, "⚡ rlhf-runner", PURPLE, 14, weight="700"),
        text(158, 34, "· a crowd-taught agent · real weights, real votes", SLATE, 12),
        text(W - 28, 34, f"week {week} · policy v{week}", CYAN, 13, anchor="end"),
        f"<line x1='24' y1='48' x2='{W-24}' y2='48' stroke='{EDGE}'/>",
        text(28, 68, "it was born only knowing how to RUN — your vote is its training data · weights update every sunday", SLATE, 11),
    ]

    # ground with pit gaps
    parts.append(f"<line x1='{x_px(level, 0)}' y1='{GROUND}' x2='{x_px(level, level['length'] - 1)}' y2='{GROUND}' "
                 f"stroke='{SLATE}' stroke-width='2'/>")
    cell_w = 860 / (level["length"] - 1)
    for pos, kind in level["obstacles"].items():
        px = x_px(level, int(pos))
        if kind == "S":
            parts.append(f"<path d='M {px - 6:.1f} {GROUND} L {px:.1f} {GROUND - 13} L {px + 6:.1f} {GROUND} Z' "
                         f"fill='{PINK}' opacity='0.9'/>")
        else:  # pit
            parts.append(f"<rect x='{px - cell_w / 2:.1f}' y='{GROUND - 2}' width='{cell_w:.1f}' height='5' fill='{BG}'/>")
            parts.append(f"<rect x='{px - cell_w / 2:.1f}' y='{GROUND + 2}' width='{cell_w:.1f}' height='10' "
                         f"fill='{PINK}' opacity='0.25'/>")
    # finish flag
    fx = x_px(level, level["length"] - 1)
    parts += [
        f"<line x1='{fx}' y1='{GROUND}' x2='{fx}' y2='{GROUND - 26}' stroke='{GREEN}' stroke-width='2'/>",
        f"<path d='M {fx} {GROUND - 26} L {fx + 12} {GROUND - 21} L {fx} {GROUND - 16} Z' fill='{GREEN}'/>",
    ]

    # dotted trace of the actual run + robot (static at end, animated copy on the path)
    path = run_path(level, steps)
    end_x = x_px(level, died_at if died_at is not None else level["length"] - 1)
    parts.append(f"<path d='{path}' fill='none' stroke='{DIM}' stroke-width='1.5' stroke-dasharray='2 4'/>")
    if died_at is not None:
        parts += [
            text(end_x, GROUND - 26, "✖", PINK, 15, anchor="middle", weight="700"),
            text(end_x, GROUND + 16, "died here", PINK, 9, anchor="middle"),
        ]
    parts.append(robot(end_x, ROBOT_Y, opacity=0.55))
    dur = max(len(steps) * 0.38, 2.0)
    parts.append(robot(0, 0, animate=f"<animateMotion dur='{dur:.1f}s' repeatCount='indefinite' path='{path}'/>"))

    # footer: status, open question with live tallies, learning curve
    parts.append(f"<line x1='24' y1='212' x2='{W-24}' y2='212' stroke='{EDGE}'/>")
    outcome = ("🏁 finished the level!" if finished else
               f"reached {distance}m / {level['length'] - 1}m")
    parts.append(text(28, 240, outcome, TEXT, 13, weight="700"))
    if not finished:
        kind = "pit" if engine.cell(level, died_at) == "P" else "spike"
        parts.append(text(28, 258, f"cause of death: {kind}", SLATE, 11))
        parts += [
            text(28, 284, "it saw:", SLATE, 11),
            text(88, 285, pattern_glyphs(death_state), PINK, 14, weight="700"),
            text(300, 240, "what should it have done? → vote below", CYAN, 12, weight="700"),
        ]
        parts += tally_rows(votes.get("votes", {}))
    else:
        parts.append(text(28, 262, "the crowd taught it every move — new level soon", GREEN, 11))
    parts += learning_curve(state["history"], distance, level["length"] - 1)
    parts.append(text(28, H - 14, "vote = open a prefilled github issue · ci counts it in ~30s and this card updates", DIM, 10))
    parts.append(f"<rect x='{W - 36}' y='{H - 26}' width='7' height='13' fill='{CYAN}'>"
                 f"<animate attributeName='opacity' values='1;0;1' dur='1.2s' repeatCount='indefinite'/></rect>")
    parts.append("</svg>")
    return "".join(parts)


def main():
    level = engine.load("level.json")
    policy = engine.load("policy.json")
    state = engine.load("state.json")
    votes = engine.load("votes.json")

    steps, died_at, death_state = engine.rollout(level, policy)

    # keep votes only while they answer the current question
    if votes.get("question") != death_state:
        votes = {"question": death_state, "votes": {}}
        engine.save("votes.json", votes)

    with open(engine.os.path.join(engine.ROOT, "replay.svg"), "w") as f:
        f.write(render(level, steps, died_at, death_state, state, votes))
    print(f"replay.svg · week {state['week']} · "
          f"{'FINISHED' if died_at is None else f'died at {died_at} seeing {death_state}'}")


if __name__ == "__main__":
    main()
