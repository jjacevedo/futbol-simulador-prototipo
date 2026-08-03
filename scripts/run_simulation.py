"""Runs a single possession end to end (possibly several cycles: Conducir,
Pase, Conservar chained together) and renders before/after schematic 2D
snapshots. Run: python3 scripts/run_simulation.py [seed]
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_possession  # noqa: E402
from vf.visualization import render_scenario  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    state = build_scenario(seed=seed)
    render_scenario(state, title=f"Antes (seed={seed})", out_path="frame_before.png")

    rng = random.Random(state.seed)
    steps = run_possession(state, rng)
    if not steps:
        print("No decision was made (no alternatives generated).")
        return

    render_scenario(state, title=f"Despues (seed={seed}, {len(steps)} ciclos)", out_path="frame_after.png")
    for i, step in enumerate(steps):
        print(f"ciclo {i}: {step['intention_type']} -> success={step.get('success')}")


if __name__ == "__main__":
    main()
