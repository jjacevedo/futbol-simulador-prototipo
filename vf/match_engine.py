import math
import random
from typing import Dict

from vf.entities import MatchState
from vf.evaluation import EvaluatedAlternative
from vf.physics import advance_ball, start_pass
from vf.probabilistic_engine import compute_pass_success_probability, resolve_pass


def _nearest_real_rival_distance(state: MatchState, team: str, position) -> float | None:
    rivals = [p for p in state.players if p.team != team]
    if not rivals:
        return None
    return min(math.hypot(position[0] - r.position[0], position[1] - r.position[1]) for r in rivals)


def execute_pass(
    state: MatchState, passer_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    passer = next(p for p in state.players if p.id == passer_id)
    target = next(p for p in state.players if p.id == chosen.alternative.target_player_id)

    # 1. validation (Match Engine Cap. 101, step 3)
    if not passer.has_ball:
        raise ValueError(f"{passer_id} does not have the ball, cannot pass")
    if target.id == passer.id:
        raise ValueError("cannot pass to self")

    # 2-3. execution: ball flight (Fisica) until arrival
    start_pass(state.ball, passer.position, chosen.alternative.target_position, target.id)
    ticks_elapsed = 0
    while not advance_ball(state.ball):
        ticks_elapsed += 1
    ticks_elapsed += 1
    state.tick += ticks_elapsed

    # 4. resolution: real (ground-truth) probability, not the perceived estimate
    real_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    real_probability = compute_pass_success_probability(
        passer.attributes, chosen.alternative.distance, real_rival_distance
    )
    success = resolve_pass(rng, real_probability)

    passer.has_ball = False
    if success:
        state.ball.state = "controlled"
        state.ball.owner_id = target.id
        target.has_ball = True
    else:
        state.ball.state = "loose"
        state.ball.owner_id = None

    return {
        "passer_id": passer.id,
        "target_player_id": target.id,
        "distance_m": chosen.alternative.distance,
        "score_beneficio": chosen.score_beneficio,
        "score_seguridad": chosen.score_seguridad,
        "score_prob_exito_percibida": chosen.score_prob_exito,
        "utility_normalized": chosen.utility_normalized,
        "real_probability": real_probability,
        "success": success,
        "ticks_elapsed": ticks_elapsed,
    }
