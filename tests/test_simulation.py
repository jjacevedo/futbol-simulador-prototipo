import random

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.simulation import build_scenario, run_one_possession


def _attrs(pase_corto=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50)


def test_build_scenario_has_one_ball_carrier():
    state = build_scenario(seed=1)
    carriers = [p for p in state.players if p.has_ball]
    assert len(carriers) == 1


def test_run_one_possession_returns_full_log_when_alternatives_exist():
    state = build_scenario(seed=1)
    rng = random.Random(state.seed)

    log = run_one_possession(state, rng)

    assert log is not None
    assert "passer_id" in log
    assert "target_player_id" in log
    assert "success" in log
    assert "utility_normalized" in log
    assert "alternatives_considered" in log
    assert len(log["alternatives_considered"]) >= 1
    assert "weights" in log


def test_run_one_possession_is_reproducible_under_same_seed():
    state_a = build_scenario(seed=3)
    state_b = build_scenario(seed=3)

    log_a = run_one_possession(state_a, random.Random(state_a.seed))
    log_b = run_one_possession(state_b, random.Random(state_b.seed))

    assert log_a["target_player_id"] == log_b["target_player_id"]
    assert log_a["success"] == log_b["success"]


def test_alternatives_considered_includes_distance():
    state = build_scenario(seed=1)
    rng = random.Random(state.seed)

    log = run_one_possession(state, rng)

    for alt in log["alternatives_considered"]:
        assert "distance" in alt
        assert isinstance(alt["distance"], float)
        assert alt["distance"] > 0.0


def _four_player_scenario():
    # p2 unmarked, p4 marked closely by r1 -> clear utility gap, not a near-tie.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0, has_ball=True)
    near_forward = Player(id="p2", team="A", position=(8.0, 2.0), attributes=_attrs())
    marked_forward = Player(id="p4", team="A", position=(8.0, -2.0), attributes=_attrs())
    rival = Player(id="r1", team="B", position=(8.0, -3.0), attributes=_attrs())

    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, near_forward, marked_forward, rival], ball=ball, tick=0, seed=5)


def test_near_tie_false_and_no_runner_up_key_on_clear_winner():
    state = _four_player_scenario()
    rng = random.Random(state.seed)

    log = run_one_possession(state, rng)

    assert log["near_tie"] is False
    assert "runner_up_target_id" not in log


def _near_tie_scenario():
    # Two teammates symmetric across the passer's facing axis, both unmarked
    # (no rival present) -> identical utility_raw, gap 0.0, well within
    # TIE_MARGIN — mirrors tests/test_cognitive_cycle.py::_near_tie_scenario.
    creative_personality = Personality(creatividad=0.9)
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                     personality=creative_personality, facing_rad=0.0, has_ball=True)
    left_forward = Player(id="p2", team="A", position=(8.0, 2.0), attributes=_attrs())
    right_forward = Player(id="p4", team="A", position=(8.0, -2.0), attributes=_attrs())

    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, left_forward, right_forward], ball=ball, tick=0, seed=7)


def test_near_tie_true_and_runner_up_set_on_near_tie():
    state = _near_tie_scenario()
    rng = random.Random(state.seed)

    log = run_one_possession(state, rng)

    assert log["near_tie"] is True
    assert log["runner_up_target_id"] in {"p2", "p4"}
    assert log["runner_up_target_id"] != log["target_player_id"]
