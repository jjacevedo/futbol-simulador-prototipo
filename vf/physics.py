import math
from typing import Tuple

from vf.entities import Ball

# Invented — Data Bible Vol VIII gives no equations (decision #3:
# constant velocity, no acceleration/friction). See docs/decisions.md.
SIM_DT = 0.1  # seconds of simulated time per tick, decoupled from real time
PASS_SPEED = 12.0  # m/s


def start_pass(
    ball: Ball, passer_position: Tuple[float, float], target_position: Tuple[float, float],
    target_player_id: str,
) -> None:
    distance = math.hypot(
        target_position[0] - passer_position[0], target_position[1] - passer_position[1]
    )
    ticks = max(1, round((distance / PASS_SPEED) / SIM_DT))

    ball.position = passer_position
    ball.owner_id = None
    ball.state = "in_flight"
    ball.target_position = target_position
    ball.target_player_id = target_player_id
    ball.ticks_total = ticks
    ball.ticks_remaining = ticks


def advance_ball(ball: Ball) -> bool:
    if ball.state != "in_flight":
        return False

    ball.ticks_remaining -= 1
    if ball.ticks_remaining <= 0:
        ball.position = ball.target_position
        return True
    return False


def interpolate_position(
    start: Tuple[float, float], target: Tuple[float, float], ticks_total: int, ticks_remaining: int
) -> Tuple[float, float]:
    if ticks_total <= 0:
        return target
    progress = 1.0 - (ticks_remaining / ticks_total)
    x = start[0] + (target[0] - start[0]) * progress
    y = start[1] + (target[1] - start[1]) * progress
    return (x, y)


# Invented — Data Bible Vol VIII gives no equations for sustained movement.
# One conducción "step" = one re-evaluation opportunity (one cognitive cycle),
# matching the Simulation Bible's "contacto a contacto" granularity (Cap.
# 103.3/103.6), not raw per-tick physics. See docs/decisions.md.
PLAYER_SPEED = 5.0  # m/s
CONDUCCION_STEP_DISTANCE = 4.0  # meters covered per step
CONDUCCION_TICKS_PER_STEP = max(1, round((CONDUCCION_STEP_DISTANCE / PLAYER_SPEED) / SIM_DT))


def conduccion_step_target(
    position: Tuple[float, float], direction: Tuple[float, float],
    step_distance: float = CONDUCCION_STEP_DISTANCE,
) -> Tuple[float, float]:
    dx, dy = direction
    norm = math.hypot(dx, dy)
    if norm == 0.0:
        return position
    ux, uy = dx / norm, dy / norm
    return (position[0] + ux * step_distance, position[1] + uy * step_distance)
