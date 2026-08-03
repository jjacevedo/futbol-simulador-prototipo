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
    real_random = rng.random

    def rigged(*args, **kwargs):
        call_count["n"] += 1
        return 0.01 if call_count["n"] == 1 else 0.99  # pass succeeds, control fails
    rng.random = rigged

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is True
    assert log["control_success"] is False
    assert log["success"] is False
    assert log["recovered_by"] is not None  # nearest player (the receiver itself, at the ball's position) recovers
    assert state.ball.state == "controlled"  # recovered, not left loose forever


def test_failed_pass_never_reaches_control_stage():
    state = _state_with_two_players()
    rng = random.Random(1)
    rng.random = lambda: 0.999  # forces pass failure regardless of probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is False
    assert log["control_success"] is None
    assert log["success"] is False


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
