import math
from dataclasses import dataclass
from typing import List, Tuple

from vf.entities import FIELD_LENGTH, FIELD_WIDTH, Player
from vf.goals import Goal
from vf.perception import PerceivedEntity
from vf.physics import CONDUCCION_STEP_DISTANCE, conduccion_step_target


@dataclass
class PassAlternative:
    target_player_id: str
    target_position: Tuple[float, float]
    distance: float


def generate_pass_alternatives(
    observer: Player, perceived: List[PerceivedEntity], goals: List[Goal]
) -> List[PassAlternative]:
    if not any(g.type == "PASAR_BALON" for g in goals):
        return []

    alternatives = []
    for entity in perceived:
        if entity.id == observer.id:
            continue
        if entity.team != observer.team:
            continue
        distance = math.hypot(
            entity.position[0] - observer.position[0],
            entity.position[1] - observer.position[1],
        )
        alternatives.append(
            PassAlternative(target_player_id=entity.id, target_position=entity.position,
                             distance=distance)
        )
    return alternatives


# 8 compass directions relative to the attack axis (+x = 0deg). Invented —
# neither Bible gives a mechanism for choosing conducción direction; user
# confirmed evaluating multiple candidates through Utility AI over a single
# heuristic vector. See docs/decisions.md.
CONDUCCION_DIRECTIONS_DEG = [0, 45, -45, 90, -90, 135, -135, 180]


@dataclass
class ConduccionAlternative:
    direction: Tuple[float, float]
    target_position: Tuple[float, float]
    distance: float


def generate_conduccion_alternatives(observer: Player, goals: List[Goal]) -> List[ConduccionAlternative]:
    if not any(g.type == "PASAR_BALON" for g in goals):
        return []

    alternatives = []
    for deg in CONDUCCION_DIRECTIONS_DEG:
        rad = math.radians(deg)
        direction = (math.cos(rad), math.sin(rad))
        target = conduccion_step_target(observer.position, direction)
        if target[0] < 0 or target[0] > FIELD_LENGTH or target[1] < 0 or target[1] > FIELD_WIDTH:
            continue  # would exit the pitch — not a viable conduccion candidate
        alternatives.append(
            ConduccionAlternative(direction=direction, target_position=target, distance=CONDUCCION_STEP_DISTANCE)
        )
    return alternatives
