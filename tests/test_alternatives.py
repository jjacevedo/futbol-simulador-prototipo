import math

from vf.alternatives import ConduccionAlternative, generate_conduccion_alternatives, generate_pass_alternatives
from vf.entities import FIELD_LENGTH, FIELD_WIDTH, Attributes, Player
from vf.goals import Goal
from vf.perception import PerceivedEntity
from vf.physics import CONDUCCION_STEP_DISTANCE


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


def test_excludes_observer_from_alternatives():
    observer = _observer()
    perceived = [
        PerceivedEntity(id="p1", team="A", position=(0.0, 0.0), distance=0.0),  # observer
        PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0),
    ]
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_pass_alternatives(observer, perceived, goals)

    assert {a.target_player_id for a in alts} == {"p2"}
    assert not any(a.target_player_id == "p1" for a in alts)


def test_generates_eight_conduccion_directions_when_goal_present():
    # Centered on the pitch (not near an edge) so none of the 8 directions
    # are excluded by the Fix 2 field-bounds check — see the dedicated
    # near-corner test below for the excluded-direction behavior.
    observer = Player(id="p1", team="A", position=(20.0, 12.5), attributes=_attrs())
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_conduccion_alternatives(observer, goals)

    assert len(alts) == 8
    for alt in alts:
        assert math.isclose(alt.distance, CONDUCCION_STEP_DISTANCE)
        # direction is a unit vector
        assert math.isclose(math.hypot(*alt.direction), 1.0, abs_tol=1e-6)


def test_forward_direction_targets_positive_x_from_observer():
    observer = _observer()  # at (0.0, 0.0)
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_conduccion_alternatives(observer, goals)
    forward = next(a for a in alts if math.isclose(a.direction[0], 1.0, abs_tol=1e-6)
                   and math.isclose(a.direction[1], 0.0, abs_tol=1e-6))

    assert math.isclose(forward.target_position[0], CONDUCCION_STEP_DISTANCE)
    assert math.isclose(forward.target_position[1], 0.0, abs_tol=1e-6)


def test_no_conduccion_alternatives_without_pasar_balon_goal():
    observer = _observer()

    alts = generate_conduccion_alternatives(observer, goals=[])

    assert alts == []


def test_conduccion_alternatives_near_corner_exclude_out_of_bounds_directions():
    observer = Player(id="p1", team="A", position=(1.0, 1.0), attributes=_attrs())
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_conduccion_alternatives(observer, goals)

    assert len(alts) < 8  # some of the 8 directions would exit the pitch from this corner
    for alt in alts:
        x, y = alt.target_position
        assert 0.0 <= x <= FIELD_LENGTH
        assert 0.0 <= y <= FIELD_WIDTH
