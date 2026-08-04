import random

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.cognitive_cycle import CONSERVAR_THRESHOLD, run_cognitive_cycle


def _attrs(pase_corto=70, control_balon=70, primer_toque=70, conduccion=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50,
                       control_balon=control_balon, primer_toque=primer_toque, conduccion=conduccion)


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
    assert "p3" not in perceived_ids


def test_full_cycle_combines_pass_and_conduccion_alternatives():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert len(result.pass_alternatives) >= 2  # p2, p4 visible
    # p1 sits at the field origin (0.0, 0.0) in this fixture; after Fix 2's
    # field-bounds check only the 0/45/90 deg directions stay on the pitch.
    assert len(result.conduccion_alternatives) == 3
    assert len(result.evaluated) == len(result.pass_alternatives) + len(result.conduccion_alternatives)


def test_full_cycle_selection_reproducible_under_same_seed_criterio_3():
    state_a = _four_player_scenario()
    state_b = _four_player_scenario()

    result_a = run_cognitive_cycle(state_a.players[0], state_a, random.Random(state_a.seed))
    result_b = run_cognitive_cycle(state_b.players[0], state_b, random.Random(state_b.seed))

    assert result_a.intention_type == result_b.intention_type
    if result_a.chosen is not None:
        assert type(result_a.chosen.alternative) == type(result_b.chosen.alternative)


def _all_options_starved_scenario():
    # Passer surrounded by rivals in every conduccion direction and with no
    # visible teammates -> every alternative should score below
    # CONSERVAR_THRESHOLD, forcing the CONSERVAR intention (Criterio 1).
    # fov_angle_deg=360 so the passer actually perceives all 8 surrounding
    # rivals (default FOV is 100 deg; with it, rivals behind/beside the
    # passer fall outside perceive()'s output, leaving the conduccion
    # evaluator a false "blind spot" and no scenario can force CONSERVAR).
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(pase_corto=30, conduccion=20),
                     facing_rad=0.0, fov_angle_deg=360.0, has_ball=True)
    rivals = [
        Player(id=f"r{i}", team="B", position=pos, attributes=_attrs())
        for i, pos in enumerate([(3.0, 0.0), (-3.0, 0.0), (0.0, 3.0), (0.0, -3.0),
                                  (2.1, 2.1), (-2.1, 2.1), (2.1, -2.1), (-2.1, -2.1)])
    ]
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, *rivals], ball=ball, tick=0, seed=9)


def test_full_cycle_conserves_when_all_alternatives_below_threshold_criterio_1():
    state = _all_options_starved_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert max(e.utility_raw for e in result.evaluated) < CONSERVAR_THRESHOLD
    assert result.intention_type == "CONSERVAR"
    assert result.chosen is None


def test_non_ball_carrier_produces_no_cycle_result():
    state = _four_player_scenario()
    non_carrier = state.players[1]

    result = run_cognitive_cycle(non_carrier, state, random.Random(state.seed))

    assert result is None
