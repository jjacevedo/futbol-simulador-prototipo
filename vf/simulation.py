import random
from typing import Dict, List, Tuple

from vf.cognitive_cycle import run_cognitive_cycle
from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.evaluation import W_BENEFICIO, W_SEGURIDAD, W_VIABILIDAD
from vf.match_engine import execute_conduccion, execute_conservar, execute_pass
from vf.selection import TIE_MARGIN
from vf.alternatives import PassAlternative

MAX_CYCLES_PER_POSSESSION = 20  # safety cap, invented — see docs/decisions.md


def _attrs(rng: random.Random) -> Attributes:
    return Attributes(
        pase_corto=rng.uniform(40, 90),
        vision=rng.uniform(40, 90),
        decision=rng.uniform(40, 90),
        posicionamiento_ofensivo=rng.uniform(40, 90),
        posicionamiento_defensivo=rng.uniform(40, 90),
        control_balon=rng.uniform(40, 90),
        primer_toque=rng.uniform(40, 90),
        conduccion=rng.uniform(40, 90),
    )


def _jitter(rng: random.Random, base: Tuple[float, float]) -> Tuple[float, float]:
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


def _describe_alternative(e) -> Dict:
    base = {
        "score_beneficio": e.score_beneficio,
        "score_seguridad": e.score_seguridad,
        "score_prob_exito": e.score_prob_exito,
        "utility_raw": e.utility_raw,
        "utility_normalized": e.utility_normalized,
    }
    if isinstance(e.alternative, PassAlternative):
        base["type"] = "PASE"
        base["target_player_id"] = e.alternative.target_player_id
        base["distance"] = e.alternative.distance
    else:
        base["type"] = "CONDUCCION"
        base["direction"] = e.alternative.direction
        base["distance"] = e.alternative.distance
    return base


def run_possession(state: MatchState, rng: random.Random) -> List[Dict]:
    steps: List[Dict] = []

    initial_carrier = next((p for p in state.players if p.has_ball), None)
    possession_team = initial_carrier.team if initial_carrier is not None else None

    for _ in range(MAX_CYCLES_PER_POSSESSION):
        carrier = next((p for p in state.players if p.has_ball), None)
        if carrier is None:
            break
        if carrier.team != possession_team:
            # Ball changed hands to a rival team — this possession record
            # belongs to one team only; the opponent's ensuing possession is
            # a separate run_possession call, out of scope here.
            break

        result = run_cognitive_cycle(carrier, state, rng)
        if result is None:
            break

        if result.intention_type == "CONSERVAR":
            step_log = execute_conservar(state, carrier.id)
        elif result.intention_type == "PASE":
            step_log = execute_pass(state, carrier.id, result.chosen, rng)
        elif result.intention_type == "CONDUCCION":
            step_log = execute_conduccion(state, carrier.id, result.chosen, rng)
        else:  # "NINGUNA"
            break

        step_log["intention_type"] = result.intention_type
        step_log["alternatives_considered"] = [_describe_alternative(e) for e in result.evaluated]
        step_log["weights"] = {
            "W_BENEFICIO": W_BENEFICIO,
            "W_SEGURIDAD": W_SEGURIDAD,
            "W_VIABILIDAD": W_VIABILIDAD,
            "TIE_MARGIN": TIE_MARGIN,
        }

        if result.chosen is not None:
            others = [e for e in result.evaluated if e is not result.chosen]
            if others:
                runner_up = max(others, key=lambda e: e.utility_raw)
                step_log["near_tie"] = abs(result.chosen.utility_raw - runner_up.utility_raw) <= TIE_MARGIN
                if step_log["near_tie"]:
                    step_log["runner_up_utility_raw"] = runner_up.utility_raw
            else:
                step_log["near_tie"] = False
        else:
            step_log["near_tie"] = False

        steps.append(step_log)

    return steps
