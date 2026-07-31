import math
from dataclasses import dataclass
from typing import List, Tuple

from vf.entities import MatchState, Player


@dataclass
class PerceivedEntity:
    id: str
    team: str
    position: Tuple[float, float]
    distance: float


def _angle_to(observer_pos: Tuple[float, float], target_pos: Tuple[float, float]) -> float:
    dx = target_pos[0] - observer_pos[0]
    dy = target_pos[1] - observer_pos[1]
    return math.atan2(dy, dx)


def _angular_difference(a: float, b: float) -> float:
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return diff


def is_visible(observer: Player, target_position: Tuple[float, float]) -> bool:
    # Deliberate simplification: no occlusion modeling. Data Bible Vol VII
    # lists occlusion as a perception factor, but this prototype's Criterio
    # de Exito 1 only requires distance + angle correctness; occlusion is
    # deferred to a future prototype.
    dx = target_position[0] - observer.position[0]
    dy = target_position[1] - observer.position[1]
    distance = math.hypot(dx, dy)
    if distance > observer.fov_distance_m:
        return False
    if distance == 0.0:
        return True
    angle_to_target = _angle_to(observer.position, target_position)
    diff = abs(_angular_difference(angle_to_target, observer.facing_rad))
    half_fov = math.radians(observer.fov_angle_deg) / 2.0
    return diff <= half_fov


def perceive(observer: Player, state: MatchState) -> List[PerceivedEntity]:
    perceived = []
    for other in state.players:
        if other.id == observer.id:
            continue
        if is_visible(observer, other.position):
            dx = other.position[0] - observer.position[0]
            dy = other.position[1] - observer.position[1]
            distance = math.hypot(dx, dy)
            perceived.append(PerceivedEntity(id=other.id, team=other.team,
                                              position=other.position, distance=distance))
    return perceived
