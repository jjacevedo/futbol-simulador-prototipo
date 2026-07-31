import random

from vf.alternatives import PassAlternative
from vf.entities import Attributes, Ball, MatchState, Player
from vf.evaluation import EvaluatedAlternative
from vf.match_engine import execute_pass


def _attrs(pase_corto=90):
    return Attributes(pase_corto=pase_corto, vision=90, decision=90,
                       posicionamiento_ofensivo=90, posicionamiento_defensivo=90)


def _state_with_two_players():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)


def _chosen_alt(target_id="p2", target_position=(6.0, 0.0)):
    alt = PassAlternative(target_player_id=target_id, target_position=target_position, distance=6.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                 score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)


def test_successful_pass_transfers_ball_ownership():
    state = _state_with_two_players()
    rng = random.Random(1)  # seed that yields a success against a very high probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    receiver = next(p for p in state.players if p.id == "p2")
    passer = next(p for p in state.players if p.id == "p1")
    assert log["success"] is True
    assert state.ball.state == "controlled"
    assert state.ball.owner_id == "p2"
    assert receiver.has_ball is True
    assert passer.has_ball is False


def test_failed_pass_leaves_ball_loose():
    state = _state_with_two_players()
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force failure regardless of probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    assert log["success"] is False
    assert state.ball.state == "loose"
    assert state.ball.owner_id is None
    passer = next(p for p in state.players if p.id == "p1")
    assert passer.has_ball is False


def test_log_contains_decision_factors_for_observability():
    state = _state_with_two_players()
    rng = random.Random(1)

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    assert "passer_id" in log
    assert "target_player_id" in log
    assert "distance_m" in log
    assert "real_probability" in log
    assert "success" in log
