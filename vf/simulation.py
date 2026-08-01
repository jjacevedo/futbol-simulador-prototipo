import random
from typing import Dict, Optional, Tuple

from vf.cognitive_cycle import run_cognitive_cycle
from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.evaluation import W_BENEFICIO, W_SEGURIDAD, W_VIABILIDAD
from vf.match_engine import execute_pass
from vf.selection import TIE_MARGIN


def _attrs(rng: random.Random) -> Attributes:
    return Attributes(
        pase_corto=rng.uniform(40, 90),
        vision=rng.uniform(40, 90),
        decision=rng.uniform(40, 90),
        posicionamiento_ofensivo=rng.uniform(40, 90),
        posicionamiento_defensivo=rng.uniform(40, 90),
    )


def _jitter(rng: random.Random, base: Tuple[float, float]) -> Tuple[float, float]:
    """Seeded jitter so different seeds produce meaningfully different tactical
    pictures (rival sometimes near p2, sometimes near p3, sometimes near
    neither/outside FOV), while remaining deterministic for a given seed."""
    return (base[0] + rng.uniform(-3.0, 3.0), base[1] + rng.uniform(-3.0, 3.0))


def build_scenario(seed: int) -> MatchState:
    """3 teammates + 1 rival, reduced field, ball starts with p1."""
    rng = random.Random(seed)

    passer = Player(id="p1", team="A", position=_jitter(rng, (10.0, 12.5)), attributes=_attrs(rng),
                     personality=Personality(creatividad=rng.uniform(0.0, 1.0)),
                     facing_rad=0.0, has_ball=True)
    forward = Player(id="p2", team="A", position=_jitter(rng, (20.0, 15.0)), attributes=_attrs(rng),
                      personality=Personality(creatividad=rng.uniform(0.0, 1.0)))
    winger = Player(id="p3", team="A", position=_jitter(rng, (18.0, 5.0)), attributes=_attrs(rng),
                     personality=Personality(creatividad=rng.uniform(0.0, 1.0)))
    rival = Player(id="r1", team="B", position=_jitter(rng, (19.0, 14.0)), attributes=_attrs(rng))

    ball = Ball(position=passer.position, owner_id=passer.id)
    return MatchState(players=[passer, forward, winger, rival], ball=ball, tick=0, seed=seed)


def run_one_possession(state: MatchState, rng: random.Random) -> Optional[Dict]:
    carrier = next((p for p in state.players if p.has_ball), None)
    if carrier is None:
        return None

    result = run_cognitive_cycle(carrier, state, rng)
    if result is None or result.chosen is None:
        return None

    log = execute_pass(state, carrier.id, result.chosen, rng)

    # Full decision log (Global Constraint: every decision must be
    # loggable — which alternatives, which scores, which weights, why one
    # was chosen), not just the chosen alternative's outcome.
    log["alternatives_considered"] = [
        {
            "target_player_id": e.alternative.target_player_id,
            "distance": e.alternative.distance,
            "score_beneficio": e.score_beneficio,
            "score_seguridad": e.score_seguridad,
            "score_prob_exito": e.score_prob_exito,
            "utility_raw": e.utility_raw,
            "utility_normalized": e.utility_normalized,
        }
        for e in result.evaluated
    ]
    log["weights"] = {
        "W_BENEFICIO": W_BENEFICIO,
        "W_SEGURIDAD": W_SEGURIDAD,
        "W_VIABILIDAD": W_VIABILIDAD,
        "TIE_MARGIN": TIE_MARGIN,
    }

    # near_tie: was the chosen alternative within TIE_MARGIN (raw utility) of
    # the best alternative that wasn't chosen? Lets a human reviewer see when
    # personality (creatividad), not a clear utility gap, decided the pass.
    chosen = result.chosen
    runner_up_candidates = [
        e for e in result.evaluated if e.alternative.target_player_id != chosen.alternative.target_player_id
    ]
    if runner_up_candidates:
        runner_up = max(runner_up_candidates, key=lambda e: e.utility_raw)
        log["near_tie"] = abs(chosen.utility_raw - runner_up.utility_raw) <= TIE_MARGIN
        if log["near_tie"]:
            log["runner_up_target_id"] = runner_up.alternative.target_player_id
    else:
        log["near_tie"] = False

    return log
