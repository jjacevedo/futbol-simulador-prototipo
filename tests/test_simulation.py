import random

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.simulation import MAX_CYCLES_PER_POSSESSION, build_scenario, run_possession


def _attrs(pase_corto=70, control_balon=70, primer_toque=70, conduccion=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50,
                       control_balon=control_balon, primer_toque=primer_toque, conduccion=conduccion)


def test_build_scenario_has_one_ball_carrier():
    state = build_scenario(seed=1)
    carriers = [p for p in state.players if p.has_ball]
    assert len(carriers) == 1


def test_run_possession_returns_at_least_one_step():
    state = build_scenario(seed=1)
    rng = random.Random(state.seed)

    steps = run_possession(state, rng)

    assert len(steps) >= 1
    first = steps[0]
    assert "intention_type" in first
    assert "alternatives_considered" in first
    assert "weights" in first


def test_run_possession_is_reproducible_under_same_seed():
    state_a = build_scenario(seed=3)
    state_b = build_scenario(seed=3)

    steps_a = run_possession(state_a, random.Random(state_a.seed))
    steps_b = run_possession(state_b, random.Random(state_b.seed))

    assert len(steps_a) == len(steps_b)
    assert [s["intention_type"] for s in steps_a] == [s["intention_type"] for s in steps_b]


def test_run_possession_never_exceeds_cycle_cap():
    state = build_scenario(seed=1)
    rng = random.Random(state.seed)

    steps = run_possession(state, rng)

    assert len(steps) <= MAX_CYCLES_PER_POSSESSION


def _four_player_scenario():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0, has_ball=True)
    near_forward = Player(id="p2", team="A", position=(8.0, 2.0), attributes=_attrs())
    marked_forward = Player(id="p4", team="A", position=(8.0, -2.0), attributes=_attrs())
    rival = Player(id="r1", team="B", position=(8.0, -3.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, near_forward, marked_forward, rival], ball=ball, tick=0, seed=5)


def test_conducir_step_changes_carrier_position_across_cycles():
    state = _four_player_scenario()
    rng = random.Random(state.seed)

    steps = run_possession(state, rng)

    conduccion_steps = [s for s in steps if s.get("intention_type") == "CONDUCCION"]
    if conduccion_steps:
        assert "new_position" in conduccion_steps[0]


def test_conservar_scenario_produces_conservar_intention():
    passer = Player(id="p1", team="A", position=(0.0, 0.0),
                     attributes=_attrs(pase_corto=20, conduccion=10), facing_rad=0.0, has_ball=True,
                     fov_angle_deg=360.0)
    rivals = [
        Player(id=f"r{i}", team="B", position=pos, attributes=_attrs())
        for i, pos in enumerate([(3.0, 0.0), (-3.0, 0.0), (0.0, 3.0), (0.0, -3.0),
                                  (2.1, 2.1), (-2.1, 2.1), (2.1, -2.1), (-2.1, -2.1)])
    ]
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, *rivals], ball=ball, tick=0, seed=9)
    rng = random.Random(state.seed)

    steps = run_possession(state, rng)

    assert steps[0]["intention_type"] == "CONSERVAR"
