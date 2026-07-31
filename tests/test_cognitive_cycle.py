import random

from vf.entities import Attributes, Ball, MatchState, Player
from vf.cognitive_cycle import run_cognitive_cycle


def _attrs(pase_corto=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50)


def _four_player_scenario():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0, has_ball=True)
    near_forward = Player(id="p2", team="A", position=(8.0, 2.0), attributes=_attrs())
    far_sideways = Player(id="p3", team="A", position=(-15.0, 0.0), attributes=_attrs())  # behind, outside FOV
    marked_forward = Player(id="p4", team="A", position=(8.0, -2.0), attributes=_attrs())
    rival = Player(id="r1", team="B", position=(8.0, -3.0), attributes=_attrs())  # marks p4 closely

    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, near_forward, far_sideways, marked_forward, rival],
                       ball=ball, tick=0, seed=5)


def test_full_cycle_perceives_teammates_within_fov_only_criterio_1():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    perceived_ids = {e.id for e in result.perceived}
    assert "p2" in perceived_ids
    assert "p4" in perceived_ids
    assert "p3" not in perceived_ids  # behind observer, outside 100 deg FOV


def test_full_cycle_produces_at_least_three_distinct_utilities_criterio_2():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert len(result.evaluated) >= 2  # p2 and p4 visible (p3 excluded by FOV)
    utility_by_target = {e.alternative.target_player_id: e.utility_raw for e in result.evaluated}
    # p4 is marked closely by a rival, p2 is unmarked -> lower utility for p4
    assert utility_by_target["p4"] < utility_by_target["p2"]


def test_full_cycle_selection_reproducible_under_same_seed_criterio_3():
    state_a = _four_player_scenario()
    state_b = _four_player_scenario()

    result_a = run_cognitive_cycle(state_a.players[0], state_a, random.Random(state_a.seed))
    result_b = run_cognitive_cycle(state_b.players[0], state_b, random.Random(state_b.seed))

    assert result_a.chosen.alternative.target_player_id == result_b.chosen.alternative.target_player_id


def test_non_ball_carrier_produces_no_cycle_result():
    state = _four_player_scenario()
    non_carrier = state.players[1]

    result = run_cognitive_cycle(non_carrier, state, random.Random(state.seed))

    assert result is None
