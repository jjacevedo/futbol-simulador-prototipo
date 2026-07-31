from typing import List, Tuple

import matplotlib.pyplot as plt

from vf.entities import MatchState


def render_scenario(state: MatchState, title: str, out_path: str) -> None:
    """Schematic 2D snapshot: points for players/ball, no animation.
    Points-and-lines only, per the Plan's 'visualizacion 2D esquematica' decision."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(-2, 42)
    ax.set_ylim(-2, 27)
    ax.set_aspect("equal")
    ax.set_title(title)

    for p in state.players:
        color = "tab:blue" if p.team == "A" else "tab:red"
        marker = "o" if not p.has_ball else "*"
        size = 120 if p.has_ball else 80
        ax.scatter(*p.position, c=color, marker=marker, s=size, zorder=3)
        ax.annotate(p.id, p.position, textcoords="offset points", xytext=(4, 4), fontsize=8)

    ax.scatter(*state.ball.position, c="black", marker=".", s=40, zorder=4)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def render_pass_trajectory(
    start: Tuple[float, float], end: Tuple[float, float], out_path: str, title: str
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(-2, 42)
    ax.set_ylim(-2, 27)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.plot([start[0], end[0]], [start[1], end[1]], "k--", linewidth=1)
    ax.scatter(*start, c="tab:blue", s=100, zorder=3)
    ax.scatter(*end, c="tab:green", s=100, zorder=3)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
