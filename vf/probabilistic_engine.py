import math
import random
from typing import Optional

from vf.entities import Attributes

# Calibration constants — invented (Data Bible Vol VII gives no formula).
# See docs/decisions.md. Expected to need iteration per the Plan's own
# "Riesgos Conocidos" section.
MAX_PASS_DISTANCE = 30.0
PRESSURE_X0 = 3.0
PRESSURE_K = 1.5
PROB_X0 = 0.0
PROB_K = 6.0


def score_linear(x: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def score_sigmoid(x: float, x0: float, k: float) -> float:
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def compute_pass_success_probability(
    passer_attrs: Attributes, distance_m: float, rival_distance_to_receiver: Optional[float]
) -> float:
    skill = (
        passer_attrs.pase_corto
        + passer_attrs.vision
        + passer_attrs.decision
        + passer_attrs.posicionamiento_promedio
    ) / 400.0  # each attribute 0..100, four attributes -> 0..1

    distance_score = score_linear(distance_m, 0.0, MAX_PASS_DISTANCE)

    if rival_distance_to_receiver is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance_to_receiver, PRESSURE_X0, PRESSURE_K)

    net_advantage = skill - 0.5 * distance_score - 0.5 * pressure_score
    return score_sigmoid(net_advantage, PROB_X0, PROB_K)


def resolve_pass(rng: random.Random, probability: float) -> bool:
    return rng.random() < probability
