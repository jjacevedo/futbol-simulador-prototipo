# Iteración 3 — Actualización Perceptiva (facing_rad) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether updating `Player.facing_rad` during Conducción (toward the direction of movement) and at pass reception (Opción A: toward the incoming ball, first) — with the Iteración-2 action space and weights otherwise completely unchanged — produces the three effects the hypothesis predicts: Conservar fires under real perceived pressure, Pase reappears as an option after Conducción, and Criterios 4A/4B hold without depending on the known detector bug. Source: `VF/Plan_Tecnico_Iteracion_3.docx`.

**Architecture:** One isolated variable. No new files for the mechanism itself — `facing_rad` assignment is added at the two points where a player's orientation should change (`execute_conduccion`, `execute_pass`'s control-success branch), both in `vf/match_engine.py`. The 4A loop detector is corrected first, as prep work, since it's the measurement instrument for Criterios 1 and 3, not part of the hypothesis. Measurement reuses `build_scenario`'s exact 25 seeds unchanged (Riesgo heredado #4) for direct comparison against Iteración 2's `docs/validacion_iteracion_2.md` numbers, plus a small set of hand-built adversarial scenarios specifically for Criterio 1 (real pressure), since the 25 stock seeds are not guaranteed to ever produce perceived pressure on the ball carrier.

**Tech Stack:** Same as Iteraciones 1-2 — Python 3.11+, `pytest`, `matplotlib`, stdlib only otherwise. No new dependencies.

## Global Constraints

- **Single-variable isolation, non-negotiable** (inherited Hallazgo 2): no change to `W_BENEFICIO`, `W_SEGURIDAD`, `W_VIABILIDAD`, `BENEFIT_MIN`/`BENEFIT_MAX`, `CONSERVAR_THRESHOLD`, any curve/sigmoid constant, or the Conservar mechanism itself. If a task's own code touches any of `vf/evaluation.py`'s weight constants or `vf/cognitive_cycle.py`'s `CONSERVAR_THRESHOLD`, that is a plan violation — stop and ask, don't silently "improve" it.
- **`build_scenario` in `vf/simulation.py` must not change** (Riesgo heredado #4: "Cualquier cambio incidental al build_scenario invalidaría la comparación"). Its 25 seeds are the direct comparison baseline against Iteración 2's already-published numbers (471 Conducción / 14 Pase / 0 Conservar over 485 cycles). Do not touch this function in this plan.
- No new technical actions (Disparo, Regate, Presión, Cobertura). No rival-as-a-system modeling, no collective layers, no cross-match learning, no personality changes beyond creatividad's existing tie-break role, no ECS/DI framework, no optimization work.
- Every invented constant (thresholds, angle limits) must be named module-level and referenced from `docs/decisions.md`, same discipline as prior iterations.
- The 4A/4B detector correction (Task 0) is **prep work, not the hypothesis** — do not report its own correctness as evidence for or against the Iteración 3 hypothesis in the final write-up; it only makes the subsequent measurement trustworthy.
- Opción A (facing toward the incoming ball at reception) is implemented and measured *first*. Opción B is a conditional task (Task 6) — only executed if Task 5's measurement shows Criterios 1 and/or 2 failing. Do not implement Opción B speculatively ahead of that checkpoint.
- Small, descriptive commits per task, same TDD discipline as prior iterations.

---

## Task 0: Corrected 4A Loop Detector (Trabajo Preparatorio)

Not part of the hypothesis — a measurement precondition (Hallazgo 3 heredado). The current `detect_action_loop` compares the exact `action_key` (direction for Conducción) between consecutive cycles, so a player alternating between two near-tied directions (resolved by the `creatividad` tie-break) is never flagged, even across an 18-20-cycle Conducción streak. The fix: for Conducción and Conservar, a "repeat" only requires the same actor and the same action *type* — the specific direction/parameter no longer matters. For Pase, the specific parameter (the receiving teammate) still matters, per the source doc's own wording ("Pase repetido al mismo receptor").

**Files:**
- Modify: `vf/degeneracy.py`
- Test: `tests/test_degeneracy.py`

**Interfaces:**
- Modifies: `detect_action_loop(history, max_consecutive=MAX_LOOP_REPEATS) -> bool` — same signature, corrected equality rule.
- Unchanged: `max_conduccion_streak`, `MAX_LOOP_REPEATS`, `MAX_CONDUCCION_STREAK` (already correct per Iteración 2's own postmortem — `max_conduccion_streak` already ignores the direction parameter; only `detect_action_loop` had the bug).
- Produces (new): `trailing_conduccion_streak(history) -> int` — like `max_conduccion_streak` but only the run ending at the very last entry (needed by Task 5/Criterio 3 to determine whether a possession hit the cycle cap *because of* an unbroken tail of Conducción, not merely containing one somewhere in the middle).

- [ ] **Step 1: Write failing test**

Add to `tests/test_degeneracy.py` (the existing `_entry` helper and prior tests stay untouched):
```python
from vf.degeneracy import trailing_conduccion_streak


def test_loop_detected_for_alternating_conduccion_directions_regardless_of_key():
    # This is the exact pattern Iteracion 2 documented as missed: same actor,
    # same action type, direction alternates every cycle via the tie-break.
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.7, 0.7)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.7, 0.7)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
    ]
    assert detect_action_loop(history, max_consecutive=4) is True


def test_conservar_repeats_regardless_of_key_still_loop():
    history = [_entry("p1", "CONSERVAR", None)] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_pase_to_different_receivers_is_not_a_loop_even_same_actor():
    # Same actor passing to different teammates each cycle is not a loop —
    # the receiver (action_key) still matters for PASE specifically.
    history = [
        _entry("p1", "PASE", "p2"),
        _entry("p1", "PASE", "p3"),
        _entry("p1", "PASE", "p2"),
        _entry("p1", "PASE", "p3"),
        _entry("p1", "PASE", "p2"),
    ]
    assert detect_action_loop(history, max_consecutive=4) is False


def test_pase_to_same_receiver_repeated_is_still_a_loop():
    history = [_entry("p1", "PASE", "p2")] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_trailing_conduccion_streak_counts_only_the_tail_run():
    history = [
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
        _entry("p2", "CONDUCCION", (0.0, 1.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert trailing_conduccion_streak(history) == 3


def test_trailing_conduccion_streak_zero_if_last_entry_is_not_conduccion():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),
        _entry("p1", "PASE", "p2"),
    ]
    assert trailing_conduccion_streak(history) == 0


def test_trailing_conduccion_streak_resets_on_actor_change():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert trailing_conduccion_streak(history) == 1
```

Existing tests in the file (`test_no_loop_detected_in_varied_history`, `test_loop_detected_when_same_action_repeats_past_threshold`, `test_loop_not_flagged_at_exactly_the_threshold`, `test_different_actors_repeating_same_action_key_is_not_a_loop`, and the two `max_conduccion_streak` tests) must still pass unmodified — they already only use `CONDUCCION`/mixed-type histories whose behavior doesn't change under the new rule (the old and new rule agree whenever the type isn't `PASE`, or the actor/type already differs).

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_degeneracy.py -v`
Expected: FAIL — `test_loop_detected_for_alternating_conduccion_directions_regardless_of_key` fails (old code requires exact `action_key` match), and `ImportError` on `trailing_conduccion_streak`.

- [ ] **Step 3: Modify `vf/degeneracy.py`**

```python
def _is_repeat(prev: Dict[str, Any], curr: Dict[str, Any]) -> bool:
    if prev["actor_id"] != curr["actor_id"] or prev["action_type"] != curr["action_type"]:
        return False
    if curr["action_type"] == "PASE":
        # For Pase specifically, the receiver still matters — passing to a
        # different teammate each cycle is not a repeat. See Plan Iteracion
        # 3 Cap. 5: "Pase repetido al mismo receptor."
        return prev["action_key"] == curr["action_key"]
    # CONDUCCION, CONSERVAR: actor+type match is enough — the specific
    # direction/parameter no longer matters (Hallazgo 3 heredado, corrected
    # here as precondition for measuring the Iteracion 3 hypothesis).
    return True


def detect_action_loop(history: List[Dict[str, Any]], max_consecutive: int = MAX_LOOP_REPEATS) -> bool:
    if len(history) < max_consecutive + 1:
        return False

    streak = 1
    for i in range(1, len(history)):
        if _is_repeat(history[i - 1], history[i]):
            streak += 1
            if streak > max_consecutive:
                return True
        else:
            streak = 1
    return False


def trailing_conduccion_streak(history: List[Dict[str, Any]]) -> int:
    streak = 0
    for entry in reversed(history):
        if entry["action_type"] != "CONDUCCION":
            break
        if streak == 0:
            streak = 1
            actor = entry["actor_id"]
        elif entry["actor_id"] == actor:
            streak += 1
        else:
            break
    return streak
```

Place `_is_repeat` above `detect_action_loop`, replacing the old inline `same = (...)` block. Add `trailing_conduccion_streak` after `max_conduccion_streak` (leave `max_conduccion_streak` itself untouched — it's already correct).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_degeneracy.py -v`
Expected: PASS (14 tests — 7 existing + 7 new)

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `python3 -m pytest -v`
Expected: all tests PASS (75 existing). No other module calls `detect_action_loop` directly except `scripts/generate_review_log.py`, which is unaffected by this signature-preserving change.

- [ ] **Step 6: Commit**

```bash
git add vf/degeneracy.py tests/test_degeneracy.py
git commit -m "fix: 4A loop detector groups by action type, not exact parameter (Trabajo Preparatorio It3)"
```

---

## Task 1: facing_rad Update During Conducción

The hypothesis's core, unambiguous mechanism (Plan Cap. 4: "El jugador mira hacia donde se mueve... Esta especificación no admite ambigüedad").

**Files:**
- Modify: `vf/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Modifies: `execute_conduccion` — sets `carrier.facing_rad` after moving, adds `"facing_rad"` to the returned log dict.

- [ ] **Step 1: Write failing test**

Add to `tests/test_match_engine.py`:
```python
import math


def test_execute_conduccion_updates_carrier_facing_to_direction_of_movement():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    diagonal_alt = _chosen_conduccion_alt(direction=(0.0, 1.0), target_position=(0.0, 4.0))
    log = execute_conduccion(state, carrier_id="p1", chosen=diagonal_alt, rng=rng)

    assert math.isclose(passer.facing_rad, math.pi / 2, abs_tol=1e-9)  # facing +y
    assert math.isclose(log["facing_rad"], math.pi / 2, abs_tol=1e-9)


def test_execute_conduccion_facing_updates_even_when_control_is_lost():
    # facing_rad reflects the direction the player WAS moving in this step,
    # regardless of whether they kept the ball at the end of it.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(conduccion=1),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force loss of control

    backward_alt = _chosen_conduccion_alt(direction=(-1.0, 0.0), target_position=(-4.0, 0.0))
    execute_conduccion(state, carrier_id="p1", chosen=backward_alt, rng=rng)

    assert math.isclose(passer.facing_rad, math.pi, abs_tol=1e-9)  # facing -x
```

`_chosen_conduccion_alt` and `_attrs` already exist in `tests/test_match_engine.py` from Iteración 2 — reuse them, don't redefine.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: FAIL — `AssertionError` (facing_rad still 0.0), `KeyError: 'facing_rad'`.

- [ ] **Step 3: Modify `vf/match_engine.py::execute_conduccion`**

After the line `carrier.position = new_position` (before or after `state.ball.position = new_position` — order doesn't matter, group with the other carrier-state updates), add:
```python
    carrier.facing_rad = math.atan2(alt.direction[1], alt.direction[0])
```
And add `"facing_rad": carrier.facing_rad,` to the `log` dict (alongside `"direction"`, `"new_position"`, etc.).

`math` is already imported at the top of `vf/match_engine.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add vf/match_engine.py tests/test_match_engine.py
git commit -m "feat: update carrier facing_rad to direction of movement during Conduccion"
```

---

## Task 2: Integration Test — Perception Reflects New Orientation Next Cycle

Verifies the mechanism actually has a downstream effect, not just that a field got mutated (Plan Cap. 7, validation bullet 3: "La Percepción del ciclo siguiente a una Conducción debe reflejar la nueva orientación").

**Files:**
- Test only: `tests/test_cognitive_cycle.py` (no production code changes in this task)

**Interfaces:**
- Consumes: `vf.match_engine.execute_conduccion`, `vf.perception.perceive`, `vf.cognitive_cycle.run_cognitive_cycle` (all already implemented).

- [ ] **Step 1: Write failing test**

Add to `tests/test_cognitive_cycle.py`:
```python
from vf.match_engine import execute_conduccion


def test_perception_next_cycle_reflects_facing_after_conduccion():
    # A teammate sits behind the passer's initial +x-facing orientation
    # (invisible at first), and ahead of where the passer will be facing
    # after conducting toward -x (turning around).
    passer = Player(id="p1", team="A", position=(10.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)  # facing +x
    teammate_behind = Player(id="p2", team="A", position=(-5.0, 0.0), attributes=_attrs())
    ball = Ball(position=(10.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, teammate_behind], ball=ball, tick=0, seed=1)

    result_before = run_cognitive_cycle(passer, state, random.Random(1))
    assert "p2" not in {e.id for e in result_before.perceived}  # behind, outside 100 deg FOV

    backward_alt = None
    for alt in result_before.conduccion_alternatives:
        if math.isclose(alt.direction[0], -1.0, abs_tol=1e-6) and math.isclose(alt.direction[1], 0.0, abs_tol=1e-6):
            backward_alt = alt
            break
    assert backward_alt is not None
    from vf.evaluation import EvaluatedAlternative
    chosen = EvaluatedAlternative(alternative=backward_alt, score_beneficio=1.0, score_seguridad=1.0,
                                   score_prob_exito=1.0, utility_raw=1.0, utility_normalized=1.0)
    execute_conduccion(state, carrier_id="p1", chosen=chosen, rng=random.Random(1))

    result_after = run_cognitive_cycle(passer, state, random.Random(2))
    assert "p2" in {e.id for e in result_after.perceived}  # now facing -x, teammate ahead
```

`_attrs` already exists in `tests/test_cognitive_cycle.py`; add `import math` at the top if not already present (check first).

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cognitive_cycle.py -v`
Expected: FAIL before Task 1 exists — but Task 1 is already merged by this point in the plan, so this should actually PASS immediately if Task 1 was implemented correctly. If it fails here, that means Task 1's `facing_rad` update isn't taking effect — do not weaken this test to make it pass; investigate and fix `execute_conduccion` instead, since this is the integration proof the whole hypothesis rests on.

- [ ] **Step 3: (No production code step — this task is verification-only)**

If Step 2 already passes, skip straight to Step 4. This task exists to make the integration explicit and regression-proof, not to add new behavior.

- [ ] **Step 4: Run full suite**

Run: `python3 -m pytest -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cognitive_cycle.py
git commit -m "test: perception reflects facing_rad change after Conduccion (integration proof)"
```

---

## Task 3: facing_rad Update at Pass Reception (Opción A)

Plan Cap. 4, Opción A: receiver orients toward the incoming ball / the passer. Implemented first per the plan's own decision process (simplest, most physically direct).

**Files:**
- Modify: `vf/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Modifies: `execute_pass` — on `control_success`, sets `target.facing_rad` toward `passer.position`, adds `"facing_rad"` to the returned log dict on that branch.

- [ ] **Step 1: Write failing test**

Add to `tests/test_match_engine.py`:
```python
def test_successful_control_orients_receiver_toward_passer_option_a():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 8.0), attributes=_attrs())  # NE of passer
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 8.0), distance=10.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    log = execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert log["control_success"] is True
    # receiver at (6,8), passer at (0,0) -> ball arrived from the SW ->
    # receiver should face back toward the passer, i.e. direction (-6,-8)
    expected = math.atan2(-8.0, -6.0)
    assert math.isclose(receiver.facing_rad, expected, abs_tol=1e-9)
    assert math.isclose(log["facing_rad"], expected, abs_tol=1e-9)


def test_facing_not_set_when_pass_fails():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=_attrs(), facing_rad=1.23)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force pass failure

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 0.0), distance=6.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert math.isclose(receiver.facing_rad, 1.23, abs_tol=1e-9)  # unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: FAIL — `receiver.facing_rad` still 0.0/default, `KeyError: 'facing_rad'` on the success path.

- [ ] **Step 3: Modify `vf/match_engine.py::execute_pass`**

In the `if control_success:` branch (after `target.has_ball = True`), add:
```python
        target.facing_rad = math.atan2(
            passer.position[1] - target.position[1], passer.position[0] - target.position[0]
        )
        log["facing_rad"] = target.facing_rad
```
Do NOT set `facing_rad` in the `else:` branch (control failure) or in the stage-1 (`pass_success is False`) early-return branch — the receiver only reorients once they've genuinely gained control of the ball.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add vf/match_engine.py tests/test_match_engine.py
git commit -m "feat: orient receiver toward passer on successful control (Opcion A)"
```

---

## Task 4: Criterio 5 Support — Trailing-Streak-Aware Cap Detection, Facing Oscillation, Stuck-Player Visibility

Three small, independent pieces needed before Task 5 can measure Criterios 3 and 5.

**Files:**
- Modify: `vf/degeneracy.py`
- Modify: `vf/simulation.py`
- Test: `tests/test_degeneracy.py`, `tests/test_simulation.py`

**Interfaces:**
- Produces: `MAX_FACING_SWING_RAD`, `MIN_OSCILLATION_REPEATS`, `detect_facing_oscillation(facing_history) -> bool` in `vf/degeneracy.py`.
- Modifies: `run_possession` — appends a minimal step log (`intention_type="NINGUNA"`) before breaking on the "no alternatives at all" case, so a stuck player is visible in the record instead of silently truncating it.

- [ ] **Step 1: Write failing test**

Add to `tests/test_degeneracy.py`:
```python
import math

from vf.degeneracy import MAX_FACING_SWING_RAD, MIN_OSCILLATION_REPEATS, detect_facing_oscillation


def _facing_entry(actor_id, facing_rad):
    return {"actor_id": actor_id, "facing_rad": facing_rad}


def test_no_oscillation_in_smoothly_turning_history():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", 0.3),
        _facing_entry("p1", 0.6),
        _facing_entry("p1", 0.9),
    ]
    assert detect_facing_oscillation(history) is False


def test_oscillation_detected_on_repeated_large_flips():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", math.pi),   # ~180 deg flip
        _facing_entry("p1", 0.0),        # flip back
        _facing_entry("p1", math.pi),   # flip again
    ]
    assert detect_facing_oscillation(history) is True


def test_single_large_swing_is_not_enough_to_flag():
    # one big turn (e.g. genuinely turning around after a pass) is expected
    # behavior, not oscillation — only REPEATED big swings count.
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p1", math.pi),
    ]
    assert detect_facing_oscillation(history) is False


def test_oscillation_ignores_different_actors():
    history = [
        _facing_entry("p1", 0.0),
        _facing_entry("p2", math.pi),
        _facing_entry("p1", 0.0),
        _facing_entry("p2", math.pi),
    ]
    assert detect_facing_oscillation(history) is False
```

Add to `tests/test_simulation.py`:
```python
def test_ningun_alternative_scenario_still_logs_a_step():
    # Player has the ball but is cornered: no visible teammates, no in-bounds
    # conduccion directions -> intention_type NINGUNA. Must still appear in
    # the returned steps, not silently truncate the possession.
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                     facing_rad=0.0, has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    steps = run_possession(state, rng)

    assert len(steps) == 1
    assert steps[0]["intention_type"] == "NINGUNA"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_degeneracy.py tests/test_simulation.py -v`
Expected: FAIL — `ImportError: cannot import name 'detect_facing_oscillation'`; `test_ningun_alternative_scenario_still_logs_a_step` fails with `len(steps) == 0`.

- [ ] **Step 3a: Add to `vf/degeneracy.py`**

```python
# Criterio 5 (Iteracion 3): flag repeated large facing_rad swings between a
# player's own consecutive cycles as "oscilacion perceptiva sin motivo
# aparente." A single large turn is legitimate (e.g. turning to face a new
# Conduccion direction, or receiving a pass from behind); only a REPEATED
# flip-flop pattern counts. Invented thresholds — see docs/decisions.md.
MAX_FACING_SWING_RAD = 2.5  # ~143 degrees
MIN_OSCILLATION_REPEATS = 2


def _angular_diff(a: float, b: float) -> float:
    diff = abs(a - b) % (2 * math.pi)
    return min(diff, 2 * math.pi - diff)


def detect_facing_oscillation(
    facing_history: List[Dict[str, Any]], max_swing: float = MAX_FACING_SWING_RAD,
    min_repeats: int = MIN_OSCILLATION_REPEATS,
) -> bool:
    large_swings = 0
    for i in range(1, len(facing_history)):
        prev, curr = facing_history[i - 1], facing_history[i]
        if prev["actor_id"] != curr["actor_id"]:
            large_swings = 0
            continue
        if _angular_diff(prev["facing_rad"], curr["facing_rad"]) > max_swing:
            large_swings += 1
            if large_swings >= min_repeats:
                return True
        else:
            large_swings = 0
    return False
```

Add `import math` at the top of `vf/degeneracy.py` (not currently imported — check first).

- [ ] **Step 3b: Modify `vf/simulation.py::run_possession`**

Replace the `else:  # "NINGUNA"` branch:
```python
        else:  # "NINGUNA"
            steps.append({
                "intention_type": "NINGUNA",
                "carrier_id": carrier.id,
                "alternatives_considered": [],
                "weights": {
                    "W_BENEFICIO": W_BENEFICIO,
                    "W_SEGURIDAD": W_SEGURIDAD,
                    "W_VIABILIDAD": W_VIABILIDAD,
                    "TIE_MARGIN": TIE_MARGIN,
                },
                "near_tie": False,
                "success": False,
            })
            break
```
This replaces the bare `break` — every other branch (`CONSERVAR`/`PASE`/`CONDUCCION`) continues through the shared `step_log["intention_type"] = ...` / `steps.append(step_log)` tail below the if/elif chain as before, so restructure carefully: since NINGUNA now builds and appends its own complete dict and then breaks immediately, do this check as an early branch that returns to the top of the loop's exit, NOT falling through to the shared tail-processing code that expects `result.chosen`/`result.evaluated` to exist (they don't, meaningfully, for NINGUNA). Simplest correct structure: keep the existing `if/elif/elif` for CONSERVAR/PASE/CONDUCCION building `step_log` and falling through to the shared tail as today, and turn the final `else` into its own self-contained block (append + break) that skips the shared tail entirely, as written above.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_degeneracy.py tests/test_simulation.py -v`
Expected: PASS

- [ ] **Step 5: Run full suite**

Run: `python3 -m pytest -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add vf/degeneracy.py vf/simulation.py tests/test_degeneracy.py tests/test_simulation.py
git commit -m "feat: facing-oscillation detector (Criterio 5) and visible NINGUNA steps (stuck-player check)"
```

---

## Task 5: Measurement — Run Comparison Against Iteración 2 Baseline

Not a pure code task — mirrors the measurement discipline of Iteración 2's Task 10, but this time the primary deliverable is a **comparison**, not a fresh baseline. Executed by the controller directly (or a single agent dispatch), not further subdivided.

- [ ] **Step 1: Run the full automated suite**

```bash
python3 -m pytest -v
```
Confirm all tests (75 + new ones from Tasks 0-4) pass. This is the evidence for Criterio 4 (explicabilidad — unchanged log shape, still fully inspectable) and the unit/integration parts of Criterios 1/2/3/5.

- [ ] **Step 2: Regenerate the review log using the SAME 25 seeds as Iteración 2**

```bash
python3 scripts/generate_review_log.py
```
`build_scenario` is untouched (Global Constraint), so seeds 0-24 produce the same initial positions/attributes as Iteración 2 — only the facing_rad mechanism differs. Confirm this explicitly: diff the `steps[0]`'s starting conditions (passer/teammate/rival positions) for a couple of seeds against the numbers already published in `docs/validacion_iteracion_2.md` if they're recorded there, or just confirm `build_scenario`'s source is byte-identical to Iteración 2's committed version via `git diff <iteracion-2-final-commit> -- vf/simulation.py` (should show no changes to `build_scenario` specifically, only to `run_possession`'s NINGUNA branch from Task 4).

- [ ] **Step 3: Compute the primary comparison numbers**

```bash
python3 -c "
import json, collections
recs = [json.loads(l) for l in open('decisions_review_log.jsonl')]
intents = collections.Counter()
for r in recs:
    for s in r['steps']:
        intents[s['intention_type']] += 1
print('Iteracion 3 (Opcion A) intent counts:', intents)
print('Iteracion 2 baseline (for reference): CONDUCCION=471, PASE=14, CONSERVAR=0 (485 cycles)')
"
```
Report this comparison plainly in the final write-up regardless of outcome.

- [ ] **Step 4: Criterio 2 — Pase share among cycles with perceived teammates**

This needs the denominator restricted to cycles where at least one teammate was perceived (not all cycles) — the existing log's `alternatives_considered` list already lets you infer this: a cycle had a perceivable teammate if `pass_alternatives` was non-empty, i.e. if any entry in `alternatives_considered` has `"type": "PASE"`, OR more directly, re-derive it from `run_cognitive_cycle`'s own `pass_alternatives` field by instrumenting a small one-off script (don't add this as permanent log output — it's a one-time measurement). Suggested approach: write a small throwaway script (not committed, or committed under `scripts/` only if you judge it reusable for Iteración 4) that calls `build_scenario`+`run_possession`-equivalent logic per cycle directly, capturing `len(result.pass_alternatives) > 0` as the "teammate perceived" condition, and `result.intention_type == "PASE"` as the numerator. Report: `(PASE count) / (cycles with pass_alternatives non-empty)`, compare against the 25% threshold from Criterio 2.

- [ ] **Step 5: Criterio 1 — dedicated pressure scenarios**

The 25 stock seeds are not guaranteed to ever put a rival within the ball carrier's perceptual cone (Iteración 2's own data showed rivals were essentially never perceived). Build 3-5 small hand-constructed scenarios (mirroring the pattern already used in `tests/test_cognitive_cycle.py::_all_options_starved_scenario` from Iteración 2) where a rival is placed directly in front of the ball carrier, close enough to register real pressure, and run `run_possession` on each. Report whether Conservar fires in at least one, and under what `score_seguridad`/pressure values (pull from `alternatives_considered` in that possession's log). This can be a short ad-hoc script — write it to `scripts/measure_criterio_1_it3.py` if you want it reproducible, or run it inline and paste the output into the report; either is acceptable, but the numbers must come from actually running the real `run_possession` pipeline, not a unit test in isolation (the plan explicitly requires this "fuera de tests unitarios").

- [ ] **Step 6: Criterio 3 — cap-hit-by-Conduccion-tail check**

```bash
python3 -c "
import json
from vf.degeneracy import trailing_conduccion_streak, MAX_CONDUCCION_STREAK
from vf.simulation import MAX_CYCLES_PER_POSSESSION

recs = [json.loads(l) for l in open('decisions_review_log.jsonl')]
violations = []
for r in recs:
    history = [{'actor_id': s.get('carrier_id', s.get('passer_id')), 'action_type': s['intention_type'],
                'action_key': s.get('target_player_id') or s.get('direction')} for s in r['steps']]
    if len(r['steps']) == MAX_CYCLES_PER_POSSESSION and trailing_conduccion_streak(history) >= MAX_CONDUCCION_STREAK:
        violations.append(r['seed'])
print('Criterio 3 violations (possessions capped by trailing Conduccion streak):', violations)
"
```
Report the raw list — do not adjust `MAX_CONDUCCION_STREAK` or `MAX_CYCLES_PER_POSSESSION` to make this number look better (Global Constraint: weights/thresholds frozen).

- [ ] **Step 7: Criterio 5 — oscillation and stuck-player check**

```bash
python3 -c "
import json
from vf.degeneracy import detect_facing_oscillation

recs = [json.loads(l) for l in open('decisions_review_log.jsonl')]
oscillating = []
stuck = []
for r in recs:
    facing_history = [{'actor_id': s.get('carrier_id', s.get('passer_id')), 'facing_rad': s.get('facing_rad')}
                       for s in r['steps'] if s.get('facing_rad') is not None]
    if detect_facing_oscillation(facing_history):
        oscillating.append(r['seed'])
    if any(s['intention_type'] == 'NINGUNA' for s in r['steps']):
        stuck.append(r['seed'])
print('Oscillating:', oscillating)
print('Stuck (NINGUNA occurred):', stuck)
"
```

- [ ] **Step 8: Render a handful of snapshots**

```bash
python3 scripts/run_simulation.py 1
python3 scripts/run_simulation.py 6
```
(Seeds 1 and 6 were the two most illustrative in Iteración 2's own write-up — reuse them for a visual before/after comparison.) Send the resulting PNGs and per-cycle console output to the user.

- [ ] **Step 9: Decide whether Task 6 (Opción B) is needed**

Per the plan's own decision rule: if Criterios 1 and/or 2 are failing (Conservar still never fires under real pressure, or Pase share among teammate-visible cycles is well below 25%), proceed to Task 6. If both hold, skip Task 6 entirely and move to Task 7, noting in the write-up "solo se implementó A, ver Lecciones Aprendidas para por qué no hizo falta B" per the plan's Cap. 9 requirement.

---

## Task 6: Opción B — facing_rad Toward Attack Direction at Reception (Conditional)

**Only execute this task if Task 5 Step 9 determined it's needed.** If Opción A already satisfies Criterios 1 and 2, skip this task entirely and proceed to Task 7 — do not implement this speculatively.

Plan Cap. 4, Opción B, simplified sub-variant: "mirar hacia adelante en el campo" (facing_rad = 0.0, the constant attack axis already used throughout the codebase for `score_beneficio`'s forward-gain calculation), rather than "hacia el compañero avanzado más cercano que percibía en el ciclo previo" — the latter would require threading the passer's own prior-cycle perception into the receiver's state, which the current architecture has no mechanism for (Player doesn't retain another player's perception history) and would be new state, not a pure orientation change. The plain "face the attack direction" sub-variant is the one actually implementable without adding cross-player memory, and the plan itself offers it as an equivalent ("o hacia..."). Document this operational choice explicitly in Lecciones Aprendidas.

**Files:**
- Modify: `vf/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Modifies: `execute_pass`'s control-success branch — replace the Opción A assignment with Opción B, OR (preferred, to preserve both measurements for the comparison Lecciones Aprendidas requires) make it a module-level toggle:
```python
RECEPTION_FACING_MODE = "ATTACK"  # "BALL" (Opcion A) | "ATTACK" (Opcion B) — see docs/decisions.md
```
and branch on it inside `execute_pass`. This lets you re-run Task 5's exact measurement script with the mode flipped and diff the two result sets directly, which is what Lecciones Aprendidas needs to document ("El resultado de la comparación entre Opción A y Opción B").

- [ ] **Step 1: Write failing test**

Add to `tests/test_match_engine.py`:
```python
def test_successful_control_orients_receiver_to_attack_direction_option_b(monkeypatch):
    import vf.match_engine as match_engine_module
    monkeypatch.setattr(match_engine_module, "RECEPTION_FACING_MODE", "ATTACK")

    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 8.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)
    rng = random.Random(1)

    alt = PassAlternative(target_player_id="p2", target_position=(6.0, 8.0), distance=10.0)
    chosen = EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                   score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)

    log = execute_pass(state, passer_id="p1", chosen=chosen, rng=rng)

    assert log["control_success"] is True
    assert receiver.facing_rad == 0.0  # facing +x, the attack direction, regardless of where the pass came from
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: FAIL — `AttributeError: module 'vf.match_engine' has no attribute 'RECEPTION_FACING_MODE'`.

- [ ] **Step 3: Modify `vf/match_engine.py`**

Add the module-level constant near the other invented constants at the top:
```python
# Iteracion 3 Cap. 4: Opcion A (face the incoming ball/passer) is the default,
# implemented and measured first per the plan's own decision process. Opcion
# B (face the attack direction) is implemented as a toggle, not a
# replacement, so both can be measured and compared in Lecciones Aprendidas.
RECEPTION_FACING_MODE = "BALL"  # "BALL" (Opcion A) | "ATTACK" (Opcion B)
```
Replace the Task 3 assignment in `execute_pass`'s `if control_success:` branch with:
```python
        if RECEPTION_FACING_MODE == "ATTACK":
            target.facing_rad = 0.0
        else:
            target.facing_rad = math.atan2(
                passer.position[1] - target.position[1], passer.position[0] - target.position[0]
            )
        log["facing_rad"] = target.facing_rad
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: PASS. Also re-run the ORIGINAL Opción-A test from Task 3 to confirm it still passes with the default mode unchanged (`RECEPTION_FACING_MODE = "BALL"` is the module default, so existing tests that don't monkeypatch it are unaffected).

- [ ] **Step 5: Re-run Task 5's full measurement with `RECEPTION_FACING_MODE = "ATTACK"`**

Temporarily set the module constant to `"ATTACH"` — no wait, `"ATTACK"` — at the top of the file (or monkeypatch it in a throwaway script), regenerate the review log, and re-run every measurement script from Task 5 (Steps 3-7). Save both result sets (Opción A's from Task 5, Opción B's from this step) for the comparison Lecciones Aprendidas requires. Revert `RECEPTION_FACING_MODE` back to whichever value performed better against Criterios 1/2 (or to `"BALL"` if the comparison is inconclusive — Opción A is the plan's specified default absent a clear reason to switch) before committing.

- [ ] **Step 6: Commit**

```bash
git add vf/match_engine.py tests/test_match_engine.py
git commit -m "feat: Opcion B reception facing toggle (attack direction) + measured comparison vs Opcion A"
```

---

## Task 7: Final Verification, Comparison Write-Up, Lecciones Aprendidas

Mirrors Iteración 2's closing structure. Produces `docs/validacion_iteracion_3.md`.

- [ ] **Step 1: Assemble the criterion-by-criterion verdict**

Using Task 5's (and, if applicable, Task 6's) measurements, write the verdict for each of the 5 criteria: met / not met / met with margin / met at the edge, with the actual numbers, not just pass/fail.

- [ ] **Step 2: Write the direct comparison against Iteración 2**

Table or prose: `CONDUCCION`/`PASE`/`CONSERVAR` counts, side by side with Iteración 2's 471/14/0 baseline. This comparison is the plan's explicit primary evidence (Cap. 7, validation bullet 5: "La aceptación de la hipótesis se decide sobre esta comparación").

- [ ] **Step 3: Human behavioral review**

Per the plan (Cap. 7, last bullet): present the user a readable sample from the review log, with special attention to (a) any cycle where Conservar fired, and (b) cycles immediately following a long Conducción streak, checking whether Pase alternatives visibly reappear. Do not self-certify — ask for the user's read, same discipline as Iteraciones 1 and 2.

- [ ] **Step 4: Write the mandatory Lecciones Aprendidas section**

Per Plan Cap. 9, must explicitly cover:
- Opción A vs Opción B comparison result (or, if B wasn't needed, why not).
- The effective `MAX_CONDUCCION_STREAK`/cap-related threshold used for Criterio 3 and the evidence behind it (state plainly if it was left unchanged at 6, and why that's defensible or not given the new data).
- Criterio 2's exact observed value against the 25% threshold — comfortable margin, borderline, or failed.
- Any new degeneracy type Criterio 5 caught that wasn't anticipated in the Riesgos chapter.
- The full action-distribution comparison against Iteración 2 (Step 2 above), stated explicitly.

- [ ] **Step 5: Overall verdict**

State plainly: hypothesis accepted / rejected / partially rejected, per criterion, following the same rigor as `docs/validacion_iteracion_2.md` — this is not a task to soften a negative result, and not a task to manufacture false confidence in a positive one.

- [ ] **Step 6: Commit and push**

```bash
git add docs/validacion_iteracion_3.md
git commit -m "docs: Iteracion 3 validation — facing_rad update measured against Iteracion 2 baseline"
git push origin main
```

---

## Self-Review Notes

- **Spec coverage:** Task 0 covers the Trabajo Preparatorio. Tasks 1-2 cover the Conducción-facing mechanism and its integration proof. Task 3 (and conditionally Task 6) cover reception facing. Task 4 covers Criterio 5's two sub-checks plus the NINGUNA-visibility fix Criterio 5 needs. Task 5 covers Criterios 1, 2, 3 measurement plus Criterio 4's suite-level check. Task 7 closes with the mandatory comparison and Lecciones Aprendidas.
- **Global Constraint enforcement built into the plan itself:** every task's file list is scoped to `vf/match_engine.py`, `vf/degeneracy.py`, `vf/simulation.py` (only the `NINGUNA` branch, not `build_scenario`), and tests — `vf/evaluation.py` and `vf/cognitive_cycle.py`'s `CONSERVAR_THRESHOLD` never appear in any task's file list, by design.
- **Type/interface consistency:** `execute_conduccion` and `execute_pass` both now populate a `"facing_rad"` key in their returned dict only when a player's orientation actually changed (unconditionally for Conducción since it always executes; conditionally for Pase, only on `control_success`) — Task 5's measurement scripts account for this with `.get('facing_rad')` / `is not None` filtering rather than assuming the key is always present.
- **Known simplification carried through, not hidden:** Opción B's "hacia el compañero avanzado más cercano" sub-variant is deliberately not implemented (would require new cross-player memory state); the plain attack-direction sub-variant is used instead and this substitution is documented in Task 6 and must appear in Lecciones Aprendidas, not silently substituted without comment.
