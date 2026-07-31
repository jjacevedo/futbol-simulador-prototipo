import math

from vf.entities import Attributes, Player
from vf.perception import PerceivedEntity
from vf.understanding import build_context


def _observer():
    attrs = Attributes(pase_corto=50, vision=50, decision=50,
                        posicionamiento_ofensivo=50, posicionamiento_defensivo=50)
    return Player(id="p1", team="A", position=(0.0, 0.0), attributes=attrs)


def test_nearest_rival_distance_computed_per_teammate():
    perceived = [
        PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0),
        PerceivedEntity(id="r1", team="B", position=(11.0, 0.0), distance=11.0),
        PerceivedEntity(id="r2", team="B", position=(12.0, 0.0), distance=12.0),
    ]

    context = build_context(_observer(), perceived)

    assert math.isclose(context.nearest_rival_distance["p2"], 1.0)


def test_teammate_with_no_perceived_rival_gets_none():
    perceived = [PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0)]

    context = build_context(_observer(), perceived)

    assert context.nearest_rival_distance["p2"] is None
