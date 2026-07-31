from dataclasses import dataclass
from typing import List

from vf.entities import MatchState, Player


@dataclass
class Goal:
    type: str
    priority: float


def generate_goals(observer: Player, state: MatchState) -> List[Goal]:
    if observer.has_ball:
        return [Goal(type="PASAR_BALON", priority=1.0)]
    return []
