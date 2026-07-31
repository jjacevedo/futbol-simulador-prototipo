import math

from vf.entities import Attributes, Ball, MatchState, Player
from vf.perception import perceive


def _attrs():
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def _make_state(observer: Player, others: list) -> MatchState:
    return MatchState(players=[observer, *others], ball=Ball(position=(0.0, 0.0)))


def test_teammate_ahead_within_range_is_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0)  # facing +x
    teammate = Player(id="p2", team="A", position=(10.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert len(result) == 1
    assert result[0].id == "p2"
    assert math.isclose(result[0].distance, 10.0)


def test_teammate_behind_observer_is_not_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0)  # facing +x, FOV 100 deg => +-50 deg
    teammate = Player(id="p2", team="A", position=(-10.0, 0.0), attributes=_attrs())  # directly behind
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert result == []


def test_teammate_beyond_fov_distance_is_not_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0, fov_distance_m=25.0)
    teammate = Player(id="p2", team="A", position=(30.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert result == []


def test_rival_within_fov_is_also_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0)
    rival = Player(id="r1", team="B", position=(5.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [rival])

    result = perceive(observer, state)

    assert len(result) == 1
    assert result[0].team == "B"
