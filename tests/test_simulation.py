import random

import vf.simulation as simulation_module
from vf.cognitive_cycle import CognitiveCycleResult
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
        # the passer's original position in _four_player_scenario is (0.0, 0.0);
        # movement must have actually happened, not just be present in the log
        assert conduccion_steps[0]["new_position"] != (0.0, 0.0)


def test_run_possession_stops_when_ball_changes_teams(monkeypatch):
    # Engineer a turnover after exactly one step (bypassing the real cognitive
    # cycle / execute_pass, per Fix 3's test guidance) and assert run_possession
    # terminates instead of silently absorbing the rival team's next cycle.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    rival = Player(id="r1", team="B", position=(20.0, 20.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, rival], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    call_count = {"n": 0}

    def fake_cognitive_cycle(observer, state, rng):
        call_count["n"] += 1
        return CognitiveCycleResult(
            perceived=[], context=None, goals=[], pass_alternatives=[],
            conduccion_alternatives=[], evaluated=[], chosen=None, intention_type="PASE",
        )

    def fake_execute_pass(state, carrier_id, chosen, rng):
        carrier = next(p for p in state.players if p.id == carrier_id)
        carrier.has_ball = False
        rival_player = next(p for p in state.players if p.team != carrier.team)
        rival_player.has_ball = True
        state.ball.owner_id = rival_player.id
        state.ball.state = "controlled"
        return {"passer_id": carrier_id, "success": False, "recovered_by": rival_player.id}

    monkeypatch.setattr(simulation_module, "run_cognitive_cycle", fake_cognitive_cycle)
    monkeypatch.setattr(simulation_module, "execute_pass", fake_execute_pass)

    steps = run_possession(state, rng)

    assert len(steps) == 1  # loop must break on the turnover, not run the rival's cycle
    assert call_count["n"] == 1  # cognitive cycle never ran for the rival
    assert rival.has_ball is True
    assert passer.has_ball is False


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


def test_ningun_alternative_scenario_still_logs_a_step(monkeypatch):
    # Player has the ball but has no alternatives at all (cognitive cycle
    # returns intention_type NINGUNA). NOTE: this cannot be constructed via a
    # real board position in the current 40x25 field — even the four exact
    # corners still leave 3 of the 8 conduccion directions in-bounds (verified
    # empirically), so a lone carrier always resolves to CONDUCCION/CONSERVAR,
    # never NINGUNA. The cognitive cycle is bypassed here, same technique as
    # test_run_possession_stops_when_ball_changes_teams above, so this test
    # targets run_possession's NINGUNA handling directly instead of relying on
    # an unreachable game-state precondition.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    def fake_cognitive_cycle(observer, state, rng):
        return CognitiveCycleResult(
            perceived=[], context=None, goals=[], pass_alternatives=[],
            conduccion_alternatives=[], evaluated=[], chosen=None, intention_type="NINGUNA",
        )

    monkeypatch.setattr(simulation_module, "run_cognitive_cycle", fake_cognitive_cycle)

    steps = run_possession(state, rng)

    assert len(steps) == 1
    assert steps[0]["intention_type"] == "NINGUNA"
