import random
from typing import Dict, Optional

from vf.cognitive_cycle import run_cognitive_cycle
from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.match_engine import execute_pass


def _attrs(rng: random.Random) -> Attributes:
    return Attributes(
        pase_corto=rng.uniform(40, 90),
        vision=rng.uniform(40, 90),
        decision=rng.uniform(40, 90),
        posicionamiento_ofensivo=rng.uniform(40, 90),
        posicionamiento_defensivo=rng.uniform(40, 90),
    )


def build_scenario(seed: int) -> MatchState:
    """3 teammates + 1 rival, reduced field, ball starts with p1."""
    rng = random.Random(seed)

    passer = Player(id="p1", team="A", position=(10.0, 12.5), attributes=_attrs(rng),
                     personality=Personality(creatividad=rng.uniform(0.0, 1.0)),
                     facing_rad=0.0, has_ball=True)
    forward = Player(id="p2", team="A", position=(20.0, 15.0), attributes=_attrs(rng),
                      personality=Personality(creatividad=rng.uniform(0.0, 1.0)))
    winger = Player(id="p3", team="A", position=(18.0, 5.0), attributes=_attrs(rng),
                     personality=Personality(creatividad=rng.uniform(0.0, 1.0)))
    rival = Player(id="r1", team="B", position=(19.0, 14.0), attributes=_attrs(rng))

    ball = Ball(position=passer.position, owner_id=passer.id)
    return MatchState(players=[passer, forward, winger, rival], ball=ball, tick=0, seed=seed)


def run_one_possession(state: MatchState, rng: random.Random) -> Optional[Dict]:
    carrier = next((p for p in state.players if p.has_ball), None)
    if carrier is None:
        return None

    result = run_cognitive_cycle(carrier, state, rng)
    if result is None or result.chosen is None:
        return None

    return execute_pass(state, carrier.id, result.chosen, rng)
