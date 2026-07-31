import random
from typing import List, Optional

from vf.evaluation import EvaluatedAlternative

# Margin within which two alternatives are considered "close enough" for
# personality to influence the outcome (AI Bible Vol XIV Cap. 159,
# Determinismo Controlado). Invented value — see docs/decisions.md.
TIE_MARGIN = 0.05


def select_alternative(
    rng: random.Random, evaluated: List[EvaluatedAlternative], creatividad: float
) -> Optional[EvaluatedAlternative]:
    if not evaluated:
        return None

    ranked = sorted(evaluated, key=lambda e: e.utility_normalized, reverse=True)
    best = ranked[0]
    contenders = [e for e in ranked if best.utility_normalized - e.utility_normalized <= TIE_MARGIN]

    if len(contenders) == 1:
        return best

    weights = [1.0 if e is best else creatividad for e in contenders]
    total = sum(weights)
    if total == 0.0:
        return best

    r = rng.random() * total
    upto = 0.0
    for e, w in zip(contenders, weights):
        upto += w
        if r <= upto:
            return e
    return best
