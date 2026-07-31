from vf.entities import Ball
from vf.physics import PASS_SPEED, advance_ball, interpolate_position, start_pass


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
