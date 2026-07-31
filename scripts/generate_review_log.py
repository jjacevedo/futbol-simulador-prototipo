"""Generates >=20 pass decisions for human behavioral review
(Plan de Prototipo Tecnico, Criterio de Exito 5 / Validacion Conductual,
AI Bible Vol XXXI Cap. 401). Run: python3 scripts/generate_review_log.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_one_possession  # noqa: E402

N_DECISIONS = 25
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "decisions_review_log.jsonl"


def main() -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for seed in range(N_DECISIONS):
            state = build_scenario(seed=seed)
            rng = random.Random(state.seed)
            log = run_one_possession(state, rng)
            if log is None:
                continue
            log["seed"] = seed
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    print(f"Wrote decision log to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
