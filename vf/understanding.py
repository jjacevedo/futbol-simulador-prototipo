import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from vf.entities import Player
from vf.perception import PerceivedEntity


@dataclass
class ContextualState:
    nearest_rival_distance: Dict[str, Optional[float]] = field(default_factory=dict)


def build_context(observer: Player, perceived: List[PerceivedEntity]) -> ContextualState:
    teammates = [e for e in perceived if e.team == observer.team]
    rivals = [e for e in perceived if e.team != observer.team]

    nearest: Dict[str, Optional[float]] = {}
    for mate in teammates:
        if not rivals:
            nearest[mate.id] = None
            continue
        distances = [
            math.hypot(mate.position[0] - r.position[0], mate.position[1] - r.position[1])
            for r in rivals
        ]
        nearest[mate.id] = min(distances)

    return ContextualState(nearest_rival_distance=nearest)
