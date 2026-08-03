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
SKILL_DIVISOR = 400.0  # 4 attributes, each 0..100, normalized to 0..1
DISTANCE_WEIGHT = 0.5
PRESSURE_WEIGHT = 0.5


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
    ) / SKILL_DIVISOR

    distance_score = score_linear(distance_m, 0.0, MAX_PASS_DISTANCE)

    if rival_distance_to_receiver is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance_to_receiver, PRESSURE_X0, PRESSURE_K)

    net_advantage = skill - DISTANCE_WEIGHT * distance_score - PRESSURE_WEIGHT * pressure_score
    return score_sigmoid(net_advantage, PROB_X0, PROB_K)


def resolve_pass(rng: random.Random, probability: float) -> bool:
    return rng.random() < probability


# Control/Recepcion and Conduccion formulas — same sigmoid-on-(skill-vs-pressure)
# pattern as compute_pass_success_probability, reusing PRESSURE_X0/PRESSURE_K/
# PROB_X0 (same physical meaning: rival distance to the player handling the
# ball). Invented — Data/Simulation Bibles give no formula for Control de
# Balon, Primer Toque, or Conduccion beyond their bare names. See
# docs/decisions.md.
CONTROL_SKILL_DIVISOR = 200.0  # control_balon + primer_toque, each 0..100 -> 0..1
CONTROL_PROB_K = 6.0

CONDUCCION_SKILL_DIVISOR = 100.0  # conduccion attribute, 0..100 -> 0..1
CONDUCCION_PROB_K = 6.0


def compute_control_success_probability(
    receiver_attrs: Attributes, rival_distance_to_receiver: Optional[float]
) -> float:
    skill = (receiver_attrs.control_balon + receiver_attrs.primer_toque) / CONTROL_SKILL_DIVISOR
    if rival_distance_to_receiver is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance_to_receiver, PRESSURE_X0, PRESSURE_K)
    net_advantage = skill - pressure_score
    return score_sigmoid(net_advantage, PROB_X0, CONTROL_PROB_K)


def compute_conduccion_maintain_probability(
    carrier_attrs: Attributes, rival_distance: Optional[float]
) -> float:
    skill = carrier_attrs.conduccion / CONDUCCION_SKILL_DIVISOR
    if rival_distance is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)
    net_advantage = skill - pressure_score
    return score_sigmoid(net_advantage, PROB_X0, CONDUCCION_PROB_K)
