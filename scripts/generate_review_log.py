"""Generates possession-level logs for human behavioral review
(Plan Tecnico Iteracion 2, Criterios de Exito 1-5 / Validacion Conductual).
Run: python3 scripts/generate_review_log.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.degeneracy import detect_action_loop, max_conduccion_streak  # noqa: E402
from vf.simulation import build_scenario, run_possession  # noqa: E402

N_POSSESSIONS = 25
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "decisions_review_log.jsonl"


def main() -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for seed in range(N_POSSESSIONS):
            state = build_scenario(seed=seed)
            rng = random.Random(state.seed)
            steps = run_possession(state, rng)
            if not steps:
                continue

            history = [
                {"actor_id": s.get("carrier_id", s.get("passer_id")), "action_type": s["intention_type"],
                 "action_key": s.get("target_player_id") or s.get("direction")}
                for s in steps
            ]

            record = {
                "seed": seed,
                "steps": steps,
                "loop_detected": detect_action_loop(history),
                "max_conduccion_streak": max_conduccion_streak(history),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote possession log to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
