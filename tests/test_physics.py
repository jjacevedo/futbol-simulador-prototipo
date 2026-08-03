import math

from vf.entities import Ball
from vf.physics import CONDUCCION_STEP_DISTANCE, PASS_SPEED, advance_ball, conduccion_step_target, interpolate_position, start_pass


def test_start_pass_sets_in_flight_state_and_tick_count():
    ball = Ball(position=(0.0, 0.0), owner_id="p1", state="controlled")

    start_pass(ball, passer_position=(0.0, 0.0), target_position=(12.0, 0.0), target_player_id="p2")

    assert ball.state == "in_flight"
    assert ball.owner_id is None
    assert ball.target_player_id == "p2"
    assert ball.ticks_total > 0
    assert ball.ticks_remaining == ball.ticks_total


def test_longer_distance_takes_more_ticks():
    short_ball = Ball(position=(0.0, 0.0))
    long_ball = Ball(position=(0.0, 0.0))

    start_pass(short_ball, passer_position=(0.0, 0.0), target_position=(5.0, 0.0), target_player_id="p2")
    start_pass(long_ball, passer_position=(0.0, 0.0), target_position=(25.0, 0.0), target_player_id="p2")

    assert long_ball.ticks_total > short_ball.ticks_total


def test_advance_ball_arrives_after_exact_tick_count():
    ball = Ball(position=(0.0, 0.0))
    start_pass(ball, passer_position=(0.0, 0.0), target_position=(6.0, 0.0), target_player_id="p2")
    total = ball.ticks_total

    arrived_flags = [advance_ball(ball) for _ in range(total)]

    assert arrived_flags[-1] is True
    assert arrived_flags[:-1] == [False] * (total - 1)
    assert ball.position == (6.0, 0.0)


def test_interpolate_position_halfway():
    pos = interpolate_position((0.0, 0.0), (10.0, 0.0), ticks_total=4, ticks_remaining=2)
    assert pos == (5.0, 0.0)


def test_conduccion_step_moves_along_unit_direction():
    start = (0.0, 0.0)
    target = conduccion_step_target(start, direction=(1.0, 0.0))
    assert math.isclose(target[0], CONDUCCION_STEP_DISTANCE)
    assert math.isclose(target[1], 0.0, abs_tol=1e-9)


def test_conduccion_step_normalizes_non_unit_direction():
    start = (0.0, 0.0)
    target = conduccion_step_target(start, direction=(2.0, 0.0))  # not a unit vector
    assert math.isclose(target[0], CONDUCCION_STEP_DISTANCE)


def test_conduccion_step_handles_zero_direction_by_staying_put():
    start = (5.0, 5.0)
    target = conduccion_step_target(start, direction=(0.0, 0.0))
    assert target == start
