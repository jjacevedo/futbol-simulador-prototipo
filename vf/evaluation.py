import math
from dataclasses import dataclass
from typing import List

from vf.alternatives import ConduccionAlternative, PassAlternative
from vf.entities import Player
from vf.perception import PerceivedEntity
from vf.probabilistic_engine import (
    PRESSURE_K,
    PRESSURE_X0,
    compute_conduccion_maintain_probability,
    compute_pass_success_probability,
    score_linear,
    score_sigmoid,
)
from vf.understanding import ContextualState

# Weights — invented (AI Bible Vol XII Cap. 128 requires them to be
# explicit configuration, never implicit in code). See docs/decisions.md.
W_BENEFICIO = 0.6
W_SEGURIDAD = 0.4
W_VIABILIDAD = 1.0  # exponent on the multiplicative probability factor

BENEFIT_MIN = -20.0
BENEFIT_MAX = 20.0


@dataclass
class EvaluatedAlternative:
    alternative: PassAlternative
    score_beneficio: float
    score_seguridad: float
    score_prob_exito: float
    utility_raw: float
    utility_normalized: float = 0.0


def _evaluate_single(passer: Player, alt: PassAlternative, context: ContextualState) -> EvaluatedAlternative:
    forward_gain = alt.target_position[0] - passer.position[0]
    score_beneficio = score_linear(forward_gain, BENEFIT_MIN, BENEFIT_MAX)  # Curva Lineal

    rival_distance = context.nearest_rival_distance.get(alt.target_player_id)
    if rival_distance is None:
        pressure = 0.0
    else:
        pressure = 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)  # Curva Sigmoide
    score_seguridad = 1.0 - pressure

    score_prob_exito = compute_pass_success_probability(
        passer.attributes, alt.distance, rival_distance
    )  # perceived viability estimate — same formula, agent-side inputs

    utility_raw = (
        W_BENEFICIO * score_beneficio + W_SEGURIDAD * score_seguridad
    ) * (score_prob_exito ** W_VIABILIDAD)

    return EvaluatedAlternative(
        alternative=alt,
        score_beneficio=score_beneficio,
        score_seguridad=score_seguridad,
        score_prob_exito=score_prob_exito,
        utility_raw=utility_raw,
    )


def normalize_utilities(evaluated: List[EvaluatedAlternative]) -> List[EvaluatedAlternative]:
    if not evaluated:
        return evaluated
    utilities = [e.utility_raw for e in evaluated]
    u_min, u_max = min(utilities), max(utilities)
    span = u_max - u_min
    for e in evaluated:
        e.utility_normalized = 1.0 if span == 0.0 else (e.utility_raw - u_min) / span
    return evaluated


def evaluate_alternatives(
    passer: Player, alternatives: List[PassAlternative], context: ContextualState
) -> List[EvaluatedAlternative]:
    evaluated = [_evaluate_single(passer, alt, context) for alt in alternatives]
    return normalize_utilities(evaluated)


def _evaluate_single_conduccion(
    carrier: Player, alt: ConduccionAlternative, rivals: List[PerceivedEntity]
) -> EvaluatedAlternative:
    forward_gain = alt.target_position[0] - carrier.position[0]
    score_beneficio = score_linear(forward_gain, BENEFIT_MIN, BENEFIT_MAX)

    if rivals:
        rival_distance = min(
            math.hypot(alt.target_position[0] - r.position[0], alt.target_position[1] - r.position[1])
            for r in rivals
        )
    else:
        rival_distance = None
    pressure = 0.0 if rival_distance is None else 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)
    score_seguridad = 1.0 - pressure

    score_prob_exito = compute_conduccion_maintain_probability(carrier.attributes, rival_distance)

    utility_raw = (
        W_BENEFICIO * score_beneficio + W_SEGURIDAD * score_seguridad
    ) * (score_prob_exito ** W_VIABILIDAD)

    return EvaluatedAlternative(
        alternative=alt, score_beneficio=score_beneficio, score_seguridad=score_seguridad,
        score_prob_exito=score_prob_exito, utility_raw=utility_raw,
    )


def evaluate_conduccion_alternatives(
    carrier: Player, alternatives: List[ConduccionAlternative], perceived: List[PerceivedEntity]
) -> List[EvaluatedAlternative]:
    rivals = [e for e in perceived if e.team != carrier.team]
    evaluated = [_evaluate_single_conduccion(carrier, alt, rivals) for alt in alternatives]
    return normalize_utilities(evaluated)
