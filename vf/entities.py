from dataclasses import dataclass, field
from typing import Optional, Tuple

FIELD_LENGTH = 40.0
FIELD_WIDTH = 25.0


@dataclass
class Attributes:
    pase_corto: float
    vision: float
    decision: float
    posicionamiento_ofensivo: float
    posicionamiento_defensivo: float

    @property
    def posicionamiento_promedio(self) -> float:
        return (self.posicionamiento_ofensivo + self.posicionamiento_defensivo) / 2.0


@dataclass
class Personality:
    creatividad: float = 0.5  # 0..1, stand-in for AI Bible Vol XVII (fuera de alcance)


@dataclass
class Player:
    id: str
    team: str
    position: Tuple[float, float]
    attributes: Attributes
    personality: Personality = field(default_factory=Personality)
    facing_rad: float = 0.0
    fov_angle_deg: float = 100.0
    fov_distance_m: float = 25.0
    has_ball: bool = False


@dataclass
class Ball:
    position: Tuple[float, float]
    owner_id: Optional[str] = None
    state: str = "controlled"  # controlled | in_flight | loose
    target_position: Optional[Tuple[float, float]] = None
    target_player_id: Optional[str] = None
    ticks_total: int = 0
    ticks_remaining: int = 0


@dataclass
class MatchState:
    players: list
    ball: Ball
    tick: int = 0
    seed: int = 0
