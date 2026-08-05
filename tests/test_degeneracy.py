import math

from vf.degeneracy import MAX_CONDUCCION_STREAK, MAX_LOOP_REPEATS, detect_action_loop, max_conduccion_streak, trailing_conduccion_streak
from vf.degeneracy import MAX_FACING_SWING_RAD, MIN_OSCILLATION_REPEATS, detect_facing_oscillation


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


def test_loop_detected_for_alternating_conduccion_directions_regardless_of_key():
    # This is the exact pattern Iteracion 2 documented as missed: same actor,
    # same action type, direction alternates every cycle via the tie-break.
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.7, 0.7)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.7, 0.7)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
    ]
    assert detect_action_loop(history, max_consecutive=4) is True


def test_conservar_repeats_regardless_of_key_still_loop():
    history = [_entry("p1", "CONSERVAR", None)] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_pase_to_different_receivers_is_not_a_loop_even_same_actor():
    # Same actor passing to different teammates each cycle is not a loop —
    # the receiver (action_key) still matters for PASE specifically.
    history = [
        _entry("p1", "PASE", "p2"),
        _entry("p1", "PASE", "p3"),
        _entry("p1", "PASE", "p2"),
        _entry("p1", "PASE", "p3"),
        _entry("p1", "PASE", "p2"),
    ]
    assert detect_action_loop(history, max_consecutive=4) is False


def test_pase_to_same_receiver_repeated_is_still_a_loop():
    history = [_entry("p1", "PASE", "p2")] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_trailing_conduccion_streak_counts_only_the_tail_run():
    history = [
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
        _entry("p2", "CONDUCCION", (0.0, 1.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert trailing_conduccion_streak(history) == 3


def test_trailing_conduccion_streak_zero_if_last_entry_is_not_conduccion():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),
        _entry("p1", "PASE", "p2"),
    ]
    assert trailing_conduccion_streak(history) == 0


def test_trailing_conduccion_streak_resets_on_actor_change():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert trailing_conduccion_streak(history) == 1


def _facing_entry(actor_id, facing_rad):
    return {"actor_id": actor_id, "facing_rad": facing_rad}


def test_no_oscillation_in_smoothly_turning_history():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", 0.3),
        _facing_entry("p1", 0.6),
        _facing_entry("p1", 0.9),
    ]
    assert detect_facing_oscillation(history) is False


def test_oscillation_detected_on_repeated_large_flips():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", math.pi),   # ~180 deg flip
        _facing_entry("p1", 0.0),        # flip back
        _facing_entry("p1", math.pi),   # flip again
    ]
    assert detect_facing_oscillation(history) is True


def test_single_large_swing_is_not_enough_to_flag():
    # one big turn (e.g. genuinely turning around after a pass) is expected
    # behavior, not oscillation — only REPEATED big swings count.
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", math.pi),
    ]
    assert detect_facing_oscillation(history) is False


def test_oscillation_ignores_different_actors():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p2", math.pi),
        _facing_entry("p1", 0.0),
        _facing_entry("p2", math.pi),
    ]
    assert detect_facing_oscillation(history) is False
