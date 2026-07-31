import os
import tempfile

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.persistence import load_state, save_state


def _sample_state() -> MatchState:
    attrs = Attributes(pase_corto=72, vision=64, decision=58,
                        posicionamiento_ofensivo=70, posicionamiento_defensivo=45)
    p1 = Player(id="p1", team="A", position=(10.0, 12.5), attributes=attrs,
                personality=Personality(creatividad=0.8), has_ball=True)
    ball = Ball(position=(10.0, 12.5), owner_id="p1")
    return MatchState(players=[p1], ball=ball, tick=7, seed=1234)


def test_save_and_load_round_trip():
    state = _sample_state()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "state.json")
        save_state(state, path)
        loaded = load_state(path)

    assert loaded.tick == 7
    assert loaded.seed == 1234
    assert loaded.ball.owner_id == "p1"
    assert loaded.ball.position == (10.0, 12.5)
    assert len(loaded.players) == 1
    p = loaded.players[0]
    assert p.id == "p1"
    assert p.has_ball is True
    assert p.attributes.pase_corto == 72
    assert p.attributes.posicionamiento_promedio == 57.5
    assert p.personality.creatividad == 0.8
