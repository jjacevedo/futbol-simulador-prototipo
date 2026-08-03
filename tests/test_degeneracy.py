from vf.degeneracy import MAX_CONDUCCION_STREAK, MAX_LOOP_REPEATS, detect_action_loop, max_conduccion_streak


def _entry(actor_id, action_type, action_key):
    return {"actor_id": actor_id, "action_type": action_type, "action_key": action_key}


def test_no_loop_detected_in_varied_history():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (0.0, 1.0)),
    ]
    assert detect_action_loop(history) is False


def test_loop_detected_when_same_action_repeats_past_threshold():
    history = [_entry("p1", "CONDUCCION", (1.0, 0.0))] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_loop_not_flagged_at_exactly_the_threshold():
    history = [_entry("p1", "CONDUCCION", (1.0, 0.0))] * MAX_LOOP_REPEATS
    assert detect_action_loop(history) is False


def test_different_actors_repeating_same_action_key_is_not_a_loop():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
    ]
    assert detect_action_loop(history) is False


def test_max_conduccion_streak_counts_consecutive_same_actor_conduccion():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),  # different direction, still CONDUCCION -> counts
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert max_conduccion_streak(history) == 2


def test_max_conduccion_streak_zero_when_no_conduccion():
    history = [_entry("p1", "PASE", "p2"), _entry("p2", "CONSERVAR", None)]
    assert max_conduccion_streak(history) == 0


def test_conduccion_streak_threshold_constant_is_positive():
    assert MAX_CONDUCCION_STREAK > 0
