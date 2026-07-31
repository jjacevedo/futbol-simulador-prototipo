import math

from vf.alternatives import generate_pass_alternatives
from vf.entities import Attributes, Player
from vf.goals import Goal
from vf.perception import PerceivedEntity


def _attrs():
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def _observer():
    return Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs())


def test_generates_one_alternative_per_visible_teammate():
    perceived = [
        PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0),
        PerceivedEntity(id="p3", team="A", position=(0.0, 8.0), distance=8.0),
        PerceivedEntity(id="r1", team="B", position=(5.0, 0.0), distance=5.0),
    ]
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_pass_alternatives(_observer(), perceived, goals)

    assert {a.target_player_id for a in alts} == {"p2", "p3"}
    p2_alt = next(a for a in alts if a.target_player_id == "p2")
    assert math.isclose(p2_alt.distance, 10.0)


def test_no_alternatives_without_pasar_balon_goal():
    perceived = [PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0)]

    alts = generate_pass_alternatives(_observer(), perceived, goals=[])

    assert alts == []
