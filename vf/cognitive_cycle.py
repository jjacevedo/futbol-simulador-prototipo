import random
from dataclasses import dataclass
from typing import List, Optional

from vf.alternatives import PassAlternative, generate_pass_alternatives
from vf.entities import MatchState, Player
from vf.evaluation import EvaluatedAlternative, evaluate_alternatives
from vf.goals import Goal, generate_goals
from vf.perception import PerceivedEntity, perceive
from vf.selection import select_alternative
from vf.understanding import ContextualState, build_context


@dataclass
class CognitiveCycleResult:
    perceived: List[PerceivedEntity]
    context: ContextualState
    goals: List[Goal]
    alternatives: List[PassAlternative]
    evaluated: List[EvaluatedAlternative]
    chosen: Optional[EvaluatedAlternative]


def run_cognitive_cycle(
    observer: Player, state: MatchState, rng: random.Random
) -> Optional[CognitiveCycleResult]:
    # Unidirectional flow (AI Bible Vol III Cap. 23):
    # Estado -> Percepcion -> Comprension -> Objetivos -> Alternativas -> Evaluacion -> Seleccion
    goals = generate_goals(observer, state)
    if not goals:
        return None  # LOD (Vol XXXII): only the ball carrier runs the full cycle in this prototype

    perceived = perceive(observer, state)
    context = build_context(observer, perceived)
    alternatives = generate_pass_alternatives(observer, perceived, goals)
    if not alternatives:
        return CognitiveCycleResult(perceived, context, goals, alternatives, [], None)

    evaluated = evaluate_alternatives(observer, alternatives, context)
    chosen = select_alternative(rng, evaluated, observer.personality.creatividad)

    return CognitiveCycleResult(perceived, context, goals, alternatives, evaluated, chosen)
