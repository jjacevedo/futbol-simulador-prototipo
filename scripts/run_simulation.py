"""Runs a single possession end to end and renders before/after schematic
2D snapshots. Run: python3 scripts/run_simulation.py [seed]
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_one_possession  # noqa: E402
from vf.visualization import render_pass_trajectory, render_scenario  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    state = build_scenario(seed=seed)
    render_scenario(state, title=f"Antes (seed={seed})", out_path="frame_before.png")
    passer_position = state.ball.position

    rng = random.Random(state.seed)
    log = run_one_possession(state, rng)
    if log is None:
        print("No decision was made (no alternatives generated).")
        return

    render_scenario(state, title=f"Despues (seed={seed})", out_path="frame_after.png")
    render_pass_trajectory(
        start=passer_position,
        end=state.ball.position,
        out_path="frame_pass_trajectory.png",
        title=f"Pase (seed={seed})",
    )
    print(log)


if __name__ == "__main__":
    main()
