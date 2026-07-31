from vf.entities import Attributes, Personality, Player, Ball, MatchState


def test_posicionamiento_promedio():
    attrs = Attributes(
        pase_corto=70, vision=60, decision=65,
        posicionamiento_ofensivo=80, posicionamiento_defensivo=40,
    )
    assert attrs.posicionamiento_promedio == 60.0


def test_player_defaults():
    p = Player(id="p1", team="A", position=(0.0, 0.0), attributes=Attributes(
        pase_corto=50, vision=50, decision=50,
        posicionamiento_ofensivo=50, posicionamiento_defensivo=50,
    ))
    assert p.has_ball is False
    assert p.personality.creatividad == 0.5
    assert p.fov_angle_deg == 100.0
    assert p.fov_distance_m == 25.0


def test_match_state_holds_players_and_ball():
    ball = Ball(position=(20.0, 12.5))
    state = MatchState(players=[], ball=ball, tick=0, seed=42)
    assert state.tick == 0
    assert state.seed == 42
    assert state.ball.state == "controlled"
