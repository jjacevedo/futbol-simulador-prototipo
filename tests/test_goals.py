from vf.entities import Attributes, Ball, MatchState, Player
from vf.goals import generate_goals


def _attrs():
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def test_ball_carrier_gets_pasar_balon_goal():
    carrier = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    state = MatchState(players=[carrier], ball=Ball(position=(0.0, 0.0), owner_id="p1"))

    goals = generate_goals(carrier, state)

    assert len(goals) == 1
    assert goals[0].type == "PASAR_BALON"
    assert goals[0].priority == 1.0


def test_non_carrier_gets_no_goals():
    non_carrier = Player(id="p2", team="A", position=(5.0, 0.0), attributes=_attrs(), has_ball=False)
    state = MatchState(players=[non_carrier], ball=Ball(position=(0.0, 0.0)))

    goals = generate_goals(non_carrier, state)

    assert goals == []
