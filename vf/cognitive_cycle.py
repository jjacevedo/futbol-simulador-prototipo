import random
from dataclasses import dataclass
from typing import List, Optional

from vf.alternatives import (
    ConduccionAlternative,
    PassAlternative,
    generate_conduccion_alternatives,
    generate_pass_alternatives,
)
from vf.entities import MatchState, Player
from vf.evaluation import EvaluatedAlternative, evaluate_alternatives, evaluate_conduccion_alternatives, normalize_utilities
from vf.goals import Goal, generate_goals
from vf.perception import PerceivedEntity, perceive
from vf.selection import select_alternative
from vf.understanding import ContextualState, build_context

# Utility threshold below which Selection converts its best available option
# into a CONSERVAR intention instead of acting on it (Iteracion 2 Cap. 52 —
# "El umbral... es un parametro nuevo... Su valor inicial sera provisional").
# Invented, expected to be recalibrated — see docs/decisions.md.
CONSERVAR_THRESHOLD = 0.15


@dataclass
class CognitiveCycleResult:
    perceived: List[PerceivedEntity]
    context: ContextualState
    goals: List[Goal]
    pass_alternatives: List[PassAlternative]
    conduccion_alternatives: List[ConduccionAlternative]
    evaluated: List[EvaluatedAlternative]
    chosen: Optional[EvaluatedAlternative]
    intention_type: str  # "PASE" | "CONDUCCION" | "CONSERVAR" | "NINGUNA"


def run_cognitive_cycle(
    observer: Player, state: MatchState, rng: random.Random
) -> Optional[CognitiveCycleResult]:
    goals = generate_goals(observer, state)
    if not goals:
        return None  # LOD (Vol XXXII): only the ball carrier runs the full cycle

    perceived = perceive(observer, state)
    context = build_context(observer, perceived)

    pass_alts = generate_pass_alternatives(observer, perceived, goals)
    conduccion_alts = generate_conduccion_alternatives(observer, goals)

    pass_evaluated = evaluate_alternatives(observer, pass_alts, context) if pass_alts else []
    conduccion_evaluated = (
        evaluate_conduccion_alternatives(observer, conduccion_alts, perceived) if conduccion_alts else []
    )

    combined = pass_evaluated + conduccion_evaluated
    normalize_utilities(combined)  # re-normalize across BOTH types together; see Task 4 note

    if not combined:
        return CognitiveCycleResult(perceived, context, goals, pass_alts, conduccion_alts, [], None, "NINGUNA")

    best_raw = max(e.utility_raw for e in combined)
    if best_raw < CONSERVAR_THRESHOLD:
        return CognitiveCycleResult(
            perceived, context, goals, pass_alts, conduccion_alts, combined, None, "CONSERVAR"
        )

    chosen = select_alternative(rng, combined, observer.personality.creatividad)
    intention_type = "PASE" if isinstance(chosen.alternative, PassAlternative) else "CONDUCCION"
    return CognitiveCycleResult(
        perceived, context, goals, pass_alts, conduccion_alts, combined, chosen, intention_type
    )
