import math
import random

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.cognitive_cycle import CONSERVAR_THRESHOLD, run_cognitive_cycle
from vf.match_engine import execute_conduccion


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


def test_perception_next_cycle_reflects_facing_after_conduccion():
    # A teammate sits behind the passer's initial +x-facing orientation
    # (invisible at first), and ahead of where the passer will be facing
    # after conducting toward -x (turning around).
    passer = Player(id="p1", team="A", position=(10.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)  # facing +x
    teammate_behind = Player(id="p2", team="A", position=(-5.0, 0.0), attributes=_attrs())
    ball = Ball(position=(10.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, teammate_behind], ball=ball, tick=0, seed=1)

    result_before = run_cognitive_cycle(passer, state, random.Random(1))
    assert "p2" not in {e.id for e in result_before.perceived}  # behind, outside 100 deg FOV

    backward_alt = None
    for alt in result_before.conduccion_alternatives:
        if math.isclose(alt.direction[0], -1.0, abs_tol=1e-6) and math.isclose(alt.direction[1], 0.0, abs_tol=1e-6):
            backward_alt = alt
            break
    assert backward_alt is not None
    from vf.evaluation import EvaluatedAlternative
    chosen = EvaluatedAlternative(alternative=backward_alt, score_beneficio=1.0, score_seguridad=1.0,
                                   score_prob_exito=1.0, utility_raw=1.0, utility_normalized=1.0)
    execute_conduccion(state, carrier_id="p1", chosen=chosen, rng=random.Random(1))

    result_after = run_cognitive_cycle(passer, state, random.Random(2))
    assert "p2" in {e.id for e in result_after.perceived}  # now facing -x, teammate ahead
