import math
from dataclasses import dataclass
from typing import List, Tuple

from vf.entities import Player
from vf.goals import Goal
from vf.perception import PerceivedEntity


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
