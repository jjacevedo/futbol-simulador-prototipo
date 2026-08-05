import math
import random
from typing import Dict, Optional

from vf.entities import MatchState, clamp_to_field
from vf.evaluation import EvaluatedAlternative
from vf.physics import CONDUCCION_TICKS_PER_STEP, advance_ball, conduccion_step_target, start_pass
from vf.probabilistic_engine import (
    compute_conduccion_maintain_probability,
    compute_control_success_probability,
    compute_pass_success_probability,
    resolve_pass,
)

CONSERVAR_TICKS = 1  # minimal simulated-time advance for a CONSERVAR cycle. Invented.

# Invented — without this the ball settles at distance 0 from whichever
# player just touched it, making recover_loose_ball's "nearest player" trivially
# resolve to that same player every time. See docs/decisions.md.
LOOSE_BALL_DRIFT = 2.0  # meters


def _nearest_real_rival_distance(state: MatchState, team: str, position) -> Optional[float]:
    rivals = [p for p in state.players if p.team != team]
    if not rivals:
        return None
    return min(math.hypot(position[0] - r.position[0], position[1] - r.position[1]) for r in rivals)


def recover_loose_ball(state: MatchState) -> Optional[str]:
    if not state.players:
        return None
    nearest = min(
        state.players,
        key=lambda p: math.hypot(p.position[0] - state.ball.position[0], p.position[1] - state.ball.position[1]),
    )
    nearest.has_ball = True
    state.ball.owner_id = nearest.id
    state.ball.state = "controlled"
    return nearest.id


def execute_pass(
    state: MatchState, passer_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    passer = next(p for p in state.players if p.id == passer_id)
    target = next(p for p in state.players if p.id == chosen.alternative.target_player_id)

    if not passer.has_ball:
        raise ValueError(f"{passer_id} does not have the ball, cannot pass")
    if target.id == passer.id:
        raise ValueError("cannot pass to self")

    start_pass(state.ball, passer.position, chosen.alternative.target_position, target.id)
    ticks_elapsed = 0
    while not advance_ball(state.ball):
        ticks_elapsed += 1
    ticks_elapsed += 1
    state.tick += ticks_elapsed

    passer.has_ball = False

    # Stage 1: pass accuracy (passer-side)
    real_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    real_probability = compute_pass_success_probability(
        passer.attributes, chosen.alternative.distance, real_rival_distance
    )
    pass_success = resolve_pass(rng, real_probability)

    log = {
        "passer_id": passer.id,
        "target_player_id": target.id,
        "distance_m": chosen.alternative.distance,
        "score_beneficio": chosen.score_beneficio,
        "score_seguridad": chosen.score_seguridad,
        "score_prob_exito_percibida": chosen.score_prob_exito,
        "utility_normalized": chosen.utility_normalized,
        "real_probability": real_probability,
        "pass_success": pass_success,
        "ticks_elapsed": ticks_elapsed,
    }

    if not pass_success:
        state.ball.state = "loose"
        pass_direction = (target.position[0] - passer.position[0], target.position[1] - passer.position[1])
        state.ball.position = clamp_to_field(
            conduccion_step_target(state.ball.position, pass_direction, LOOSE_BALL_DRIFT)
        )
        state.ball.owner_id = None
        log["control_success"] = None
        log["control_probability"] = None
        log["success"] = False
        log["recovered_by"] = recover_loose_ball(state)
        return log

    # Stage 2: receiver's control/reception (receiver-side, Criterio 3 of Iteracion 2)
    control_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    control_probability = compute_control_success_probability(target.attributes, control_rival_distance)
    control_success = resolve_pass(rng, control_probability)

    log["control_probability"] = control_probability
    log["control_success"] = control_success
    log["success"] = control_success

    if control_success:
        state.ball.state = "controlled"
        state.ball.owner_id = target.id
        target.has_ball = True
        log["recovered_by"] = None
    else:
        state.ball.state = "loose"
        angle = rng.uniform(0, 2 * math.pi)
        drift_direction = (math.cos(angle), math.sin(angle))
        state.ball.position = clamp_to_field(
            conduccion_step_target(state.ball.position, drift_direction, LOOSE_BALL_DRIFT)
        )
        state.ball.owner_id = None
        log["recovered_by"] = recover_loose_ball(state)

    return log


def execute_conduccion(
    state: MatchState, carrier_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    carrier = next(p for p in state.players if p.id == carrier_id)
    if not carrier.has_ball:
        raise ValueError(f"{carrier_id} does not have the ball, cannot conducir")

    alt = chosen.alternative
    new_position = alt.target_position

    rival_distance = _nearest_real_rival_distance(state, carrier.team, new_position)
    maintain_probability = compute_conduccion_maintain_probability(carrier.attributes, rival_distance)
    maintained = resolve_pass(rng, maintain_probability)

    carrier.position = new_position
    carrier.facing_rad = math.atan2(alt.direction[1], alt.direction[0])
    state.ball.position = new_position
    state.tick += CONDUCCION_TICKS_PER_STEP

    log = {
        "carrier_id": carrier.id,
        "direction": alt.direction,
        "new_position": new_position,
        "facing_rad": carrier.facing_rad,
        "maintain_probability": maintain_probability,
        "success": maintained,
        "ticks_elapsed": CONDUCCION_TICKS_PER_STEP,
    }

    if maintained:
        log["recovered_by"] = None
    else:
        carrier.has_ball = False
        state.ball.state = "loose"
        state.ball.position = clamp_to_field(
            conduccion_step_target(state.ball.position, alt.direction, LOOSE_BALL_DRIFT)
        )
        state.ball.owner_id = None
        log["recovered_by"] = recover_loose_ball(state)

    return log


def execute_conservar(state: MatchState, carrier_id: str) -> Dict:
    carrier = next(p for p in state.players if p.id == carrier_id)
    if not carrier.has_ball:
        raise ValueError(f"{carrier_id} does not have the ball, cannot conservar")

    state.tick += CONSERVAR_TICKS

    return {
        "carrier_id": carrier.id,
        "success": True,
        "ticks_elapsed": CONSERVAR_TICKS,
    }
