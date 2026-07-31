import random

from vf.simulation import build_scenario, run_one_possession


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


def test_run_one_possession_is_reproducible_under_same_seed():
    state_a = build_scenario(seed=3)
    state_b = build_scenario(seed=3)

    log_a = run_one_possession(state_a, random.Random(state_a.seed))
    log_b = run_one_possession(state_b, random.Random(state_b.seed))

    assert log_a["target_player_id"] == log_b["target_player_id"]
    assert log_a["success"] == log_b["success"]
