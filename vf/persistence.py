import json
from dataclasses import asdict
from typing import Any, Dict

from vf.entities import Attributes, Ball, MatchState, Personality, Player


def _tuple_positions_to_list(obj: Any) -> Any:
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _tuple_positions_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_tuple_positions_to_list(v) for v in obj]
    return obj


def save_state(state: MatchState, path: str) -> None:
    raw = asdict(state)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_tuple_positions_to_list(raw), f, indent=2)


def _player_from_dict(d: Dict[str, Any]) -> Player:
    attrs = Attributes(**d["attributes"])
    personality = Personality(**d["personality"])
    return Player(
        id=d["id"],
        team=d["team"],
        position=tuple(d["position"]),
        attributes=attrs,
        personality=personality,
        facing_rad=d["facing_rad"],
        fov_angle_deg=d["fov_angle_deg"],
        fov_distance_m=d["fov_distance_m"],
        has_ball=d["has_ball"],
    )


def _ball_from_dict(d: Dict[str, Any]) -> Ball:
    return Ball(
        position=tuple(d["position"]),
        owner_id=d["owner_id"],
        state=d["state"],
        target_position=tuple(d["target_position"]) if d["target_position"] else None,
        target_player_id=d["target_player_id"],
        ticks_total=d["ticks_total"],
        ticks_remaining=d["ticks_remaining"],
    )


def load_state(path: str) -> MatchState:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    players = [_player_from_dict(p) for p in raw["players"]]
    ball = _ball_from_dict(raw["ball"])
    return MatchState(players=players, ball=ball, tick=raw["tick"], seed=raw["seed"])
