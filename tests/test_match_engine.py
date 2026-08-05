import math
import random

from vf.alternatives import ConduccionAlternative, PassAlternative
from vf.entities import Attributes, Ball, MatchState, Player
from vf.evaluation import EvaluatedAlternative
from vf.match_engine import execute_conduccion, execute_conservar, execute_pass, recover_loose_ball


def _attrs(pase_corto=90, control_balon=90, primer_toque=90, conduccion=90):
    return Attributes(pase_corto=pase_corto, vision=90, decision=90,
                       posicionamiento_ofensivo=90, posicionamiento_defensivo=90,
                       control_balon=control_balon, primer_toque=primer_toque, conduccion=conduccion)


def _state_with_two_players(receiver_attrs=None):
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=receiver_attrs or _attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)


def _chosen_pass_alt(target_id="p2", target_position=(6.0, 0.0)):
    alt = PassAlternative(target_player_id=target_id, target_position=target_position, distance=6.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                 score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)


def test_successful_pass_and_control_transfers_ball_ownership():
    state = _state_with_two_players()
    rng = random.Random(1)

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    receiver = next(p for p in state.players if p.id == "p2")
    assert log["pass_success"] is True
    assert log["control_success"] is True
    assert log["success"] is True
    assert state.ball.owner_id == "p2"
    assert receiver.has_ball is True


def test_failed_control_leaves_ball_loose_then_recovered():
    state = _state_with_two_players(receiver_attrs=_attrs(control_balon=10, primer_toque=10))
    rng = random.Random(1)
    call_count = {"n": 0}

    def rigged(*args, **kwargs):
        call_count["n"] += 1
        return 0.01 if call_count["n"] == 1 else 0.99  # pass succeeds, control fails
    rng.random = rigged

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is True
    assert log["control_success"] is False
    assert log["success"] is False
    assert log["recovered_by"] is not None
    assert state.ball.state == "controlled"  # recovered, not left loose forever
    # the ball must have drifted from the receiver's exact position — otherwise
    # "nearest player" trivially resolves to the receiver every time (Fix 1)
    assert state.ball.position != (6.0, 0.0)


def test_failed_pass_never_reaches_control_stage():
    state = _state_with_two_players()
    rng = random.Random(1)
    rng.random = lambda: 0.999  # forces pass failure regardless of probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is False
    assert log["control_success"] is None
    assert log["success"] is False
    # ball drifted past the target position (Fix 1), not left exactly on top of it
    assert state.ball.position != (6.0, 0.0)


def _chosen_conduccion_alt(direction=(1.0, 0.0), target_position=(4.0, 0.0)):
    alt = ConduccionAlternative(direction=direction, target_position=target_position, distance=4.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.7, score_seguridad=0.8,
                                 score_prob_exito=0.9, utility_raw=0.75, utility_normalized=1.0)


def test_execute_conduccion_moves_carrier_and_ball_together_on_success():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)  # high conduccion attr, no rivals -> should maintain control

    log = execute_conduccion(state, carrier_id="p1", chosen=_chosen_conduccion_alt(), rng=rng)

    assert log["success"] is True
    assert passer.position == (4.0, 0.0)
    assert state.ball.position == (4.0, 0.0)
    assert passer.has_ball is True


def test_execute_conduccion_updates_carrier_facing_to_direction_of_movement():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    diagonal_alt = _chosen_conduccion_alt(direction=(0.0, 1.0), target_position=(0.0, 4.0))
    log = execute_conduccion(state, carrier_id="p1", chosen=diagonal_alt, rng=rng)

    assert math.isclose(passer.facing_rad, math.pi / 2, abs_tol=1e-9)  # facing +y
    assert math.isclose(log["facing_rad"], math.pi / 2, abs_tol=1e-9)


def test_execute_conduccion_facing_updates_even_when_control_is_lost():
    # facing_rad reflects the direction the player WAS moving in this step,
    # regardless of whether they kept the ball at the end of it.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(conduccion=1),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force loss of control

    backward_alt = _chosen_conduccion_alt(direction=(-1.0, 0.0), target_position=(-4.0, 0.0))
    execute_conduccion(state, carrier_id="p1", chosen=backward_alt, rng=rng)

    assert math.isclose(passer.facing_rad, math.pi, abs_tol=1e-9)  # facing -x


def test_execute_conservar_advances_tick_without_moving():
    passer = Player(id="p1", team="A", position=(3.0, 4.0), attributes=_attrs(), has_ball=True)
    ball = Ball(position=(3.0, 4.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=10, seed=1)

    log = execute_conservar(state, carrier_id="p1")

    assert log["success"] is True
    assert passer.position == (3.0, 4.0)
    assert passer.has_ball is True
    assert state.tick > 10


def test_recover_loose_ball_assigns_nearest_player():
    p_near = Player(id="near", team="A", position=(1.0, 0.0), attributes=_attrs())
    p_far = Player(id="far", team="B", position=(10.0, 0.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id=None, state="loose")
    state = MatchState(players=[p_near, p_far], ball=ball, tick=0, seed=1)

    recovered_id = recover_loose_ball(state)

    assert recovered_id == "near"
    assert p_near.has_ball is True
    assert state.ball.owner_id == "near"
    assert state.ball.state == "controlled"


def test_loose_ball_recovery_is_genuinely_contested_after_pass_accuracy_failure():
    # "the failing player" is the receiver: under the pre-Fix-1 bug the ball
    # settled exactly on top of them (distance 0), so they always recovered
    # their own failed pass. Fix 1 drifts the ball LOOSE_BALL_DRIFT=2.0m past
    # them along the pass direction before recovery, so a different player who
    # happens to be near the drifted landing spot can now be closer.
    passer = Player(id="p1", team="A", position=(-10.0, 0.0), attributes=_attrs(), has_ball=True)
    target = Player(id="p2", team="A", position=(0.0, 0.0), attributes=_attrs())  # "the failing player"
    # pass direction is (1.0, 0.0); drifted ball lands at (2.0, 0.0)
    close_candidate = Player(id="close", team="B", position=(2.05, 0.0), attributes=_attrs())
    far_candidate = Player(id="far", team="B", position=(-30.0, 20.0), attributes=_attrs())
    ball = Ball(position=(-10.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, target, close_candidate, far_candidate], ball=ball, tick=0, seed=1)
    rng = random.Random(1)
    rng.random = lambda: 0.999  # forces pass-accuracy failure regardless of probability

    chosen = _chosen_pass_alt(target_id="p2", target_position=(0.0, 0.0))
    log = execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert log["pass_success"] is False
    assert state.ball.position != (0.0, 0.0)  # drifted, not left on top of the receiver
    assert log["recovered_by"] == "close"
    assert log["recovered_by"] != "p2"


def test_successful_control_orients_receiver_toward_passer_option_a():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 8.0), attributes=_attrs())  # NE of passer
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 8.0), distance=10.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    log = execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert log["control_success"] is True
    # receiver at (6,8), passer at (0,0) -> ball arrived from the SW ->
    # receiver should face back toward the passer, i.e. direction (-6,-8)
    expected = math.atan2(-8.0, -6.0)
    assert math.isclose(receiver.facing_rad, expected, abs_tol=1e-9)
    assert math.isclose(log["facing_rad"], expected, abs_tol=1e-9)


def test_successful_control_orients_receiver_to_attack_direction_option_b(monkeypatch):
    import vf.match_engine as match_engine_module
    monkeypatch.setattr(match_engine_module, "RECEPTION_FACING_MODE", "ATTACK")

    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 8.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 8.0), distance=10.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    log = execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert log["control_success"] is True
    assert receiver.facing_rad == 0.0  # facing +x, the attack direction, regardless of where the pass came from


def test_facing_not_set_when_pass_fails():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=_attrs(), facing_rad=1.23)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force pass failure

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 0.0), distance=6.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert math.isclose(receiver.facing_rad, 1.23, abs_tol=1e-9)  # unchanged
