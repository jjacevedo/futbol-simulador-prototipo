# Iteración 2 — Conservar Balón, Recepción y Conducción Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the vertical-slice prototype from a single action (Pase) to four ways of using the ball — Pase, Conservar Balón (an intention, not a new technical action), Recepción/Control (separately resolved from pass accuracy), and Conducción (a sustained, multi-cycle action re-decided every cycle) — per `docs/../Plan_Tecnico_Iteracion_2` (source: `VF/Plan_Tecnico_Iteracion_2.docx`), testing the hypothesis that this is enough for recognizably footballing behavior to emerge without degenerate patterns.

**Architecture:** Every cognitive cycle now generates and evaluates a *combined* alternative set — Pass alternatives (existing) plus Conducción alternatives (new, one per candidate direction) — through the same Utility AI pipeline, normalized together. If the best raw utility across that combined set falls below a threshold, the cycle short-circuits to a `"CONSERVAR"` intention instead of calling Selección. Conducción itself requires no new persistent state on `Player`: because the plan's own source material (Simulation Bible Cap. 103.6, 108.6) describes conducción as continuously re-evaluated "contact by contact," a possession simply runs the *entire* cognitive cycle again for the same ball carrier after each conducción step — if Selección picks Conducción again, the dribble continues; if it picks Pase or falls below the Conservar threshold, the dribble ends. A new `vf/simulation.py::run_possession` loop drives this multi-cycle sequence until the ball changes hands definitively or a cycle cap is hit.

**Tech Stack:** Same as Iteración 1 — Python 3.11+, `pytest`, `matplotlib`, stdlib only otherwise. No new dependencies.

## Global Constraints

- Scope frozen to `Plan_Tecnico_Iteracion_2`: Pase (recalibration only), Conservar Balón (Selección-level intention), Recepción/Control (separately resolved), Conducción (sustained, re-decided per cycle). Everything the plan excludes stays excluded: second team, goal/portería, referee/fouls, collective/tactical layers, rival modeling as a system, learning between matches, personality influencing anything beyond the existing tie-break role, ECS/DI framework, multi-thousand-simulation optimization.
- Three structural decisions already confirmed with the user (do not re-litigate):
  1. **Dirección de Conducción**: multiple candidate directions (8, compass-style relative to the attack axis) generated as separate alternatives and scored through the same Utility AI pipeline as Pase — not a single simple heuristic vector.
  2. **Balón suelto**: after any failed control/reception or lost conducción, the nearest player on the pitch (either team) recovers the ball on the spot — this is new in this iteration; Iteración 1 explicitly punted on it.
  3. **Atributos de Control/Recepción**: `control_balon` + `primer_toque` averaged, combined with rival pressure at the reception point via the same sigmoid already used by the probabilistic engine.
- Every new invented constant (thresholds, step distances, speeds) must be a named module-level constant, referenced from `docs/decisions.md` — same discipline as Iteración 1. The plan's own Hallazgo 2 explicitly anticipates weight recalibration; Criterios 4A/4B and the Conservar threshold are explicitly left unfixed by the source doc ("no se fija a priori") — pick a reasonable initial value, document it, and revisit during Task 10's calibration pass. This is expected iteration, not a blocking ambiguity.
- New `Attributes` fields (`control_balon`, `primer_toque`, `conduccion`) get a `default=50.0` — Iteración 1 left ~15 test files constructing `Attributes(...)` without these fields; defaults avoid mass, mechanical edits to unrelated tests while still letting new tests exercise them explicitly.
- Extending `evaluate_alternatives`'s existing internal normalization to a cross-type (Pass + Conducción) combined set causes a harmless double-normalization when both are evaluated separately then re-normalized together in `cognitive_cycle.py` — this is intentional (keeps `evaluate_alternatives`'s existing standalone contract and its Iteración-1 tests unchanged) and must be called out in a comment, not "fixed."
- `CognitiveCycleResult`'s shape changes in this iteration (splits `alternatives` into `pass_alternatives`/`conduccion_alternatives`, adds `intention_type`) — this is an intentional, plan-scoped breaking change to existing Iteración-1 tests in `tests/test_cognitive_cycle.py` and `tests/test_simulation.py`; update them, don't preserve the old shape.
- Small, descriptive commits per task, same TDD discipline (test first, watch it fail, implement, watch it pass, commit) as Iteración 1.

---

## Task 0: Extend `Attributes` with Control/Conducción Fields

**Files:**
- Modify: `vf/entities.py`
- Test: `tests/test_entities.py`

**Interfaces:**
- Produces: `Attributes.control_balon: float = 50.0`, `Attributes.primer_toque: float = 50.0`, `Attributes.conduccion: float = 50.0`, `Attributes.control_promedio` (property).

- [ ] **Step 1: Write failing test**

Add to `tests/test_entities.py`:
```python
def test_control_promedio():
    attrs = Attributes(
        pase_corto=70, vision=60, decision=65,
        posicionamiento_ofensivo=80, posicionamiento_defensivo=40,
        control_balon=90, primer_toque=70,
    )
    assert attrs.control_promedio == 80.0


def test_new_technical_attributes_default_to_fifty():
    attrs = Attributes(
        pase_corto=70, vision=60, decision=65,
        posicionamiento_ofensivo=80, posicionamiento_defensivo=40,
    )
    assert attrs.control_balon == 50.0
    assert attrs.primer_toque == 50.0
    assert attrs.conduccion == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_entities.py -v`
Expected: FAIL — `TypeError: Attributes.__init__() got an unexpected keyword argument 'control_balon'`

- [ ] **Step 3: Modify `vf/entities.py`**

In the `Attributes` dataclass, add three fields with defaults after the existing five (which have no defaults, so these must come last per dataclass field-ordering rules), and a new property:
```python
@dataclass
class Attributes:
    pase_corto: float
    vision: float
    decision: float
    posicionamiento_ofensivo: float
    posicionamiento_defensivo: float
    control_balon: float = 50.0
    primer_toque: float = 50.0
    conduccion: float = 50.0

    @property
    def posicionamiento_promedio(self) -> float:
        return (self.posicionamiento_ofensivo + self.posicionamiento_defensivo) / 2.0

    @property
    def control_promedio(self) -> float:
        return (self.control_balon + self.primer_toque) / 2.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_entities.py -v`
Expected: PASS (5 tests — 3 existing + 2 new)

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `python3 -m pytest -v`
Expected: all existing tests still PASS (the new fields have defaults, so no existing `Attributes(...)` call site breaks).

- [ ] **Step 6: Commit**

```bash
git add vf/entities.py tests/test_entities.py
git commit -m "feat: add control_balon, primer_toque, conduccion attributes"
```

---

## Task 1: Probabilistic Engine — Control and Conducción Formulas

**Files:**
- Modify: `vf/probabilistic_engine.py`
- Test: `tests/test_probabilistic_engine.py`

**Interfaces:**
- Consumes: `vf.entities.Attributes`, existing `score_sigmoid`, `PRESSURE_X0`, `PRESSURE_K`, `PROB_X0`.
- Produces: `compute_control_success_probability(receiver_attrs, rival_distance_to_receiver) -> float`, `compute_conduccion_maintain_probability(carrier_attrs, rival_distance) -> float`. Reuses the existing `resolve_pass(rng, probability)` generically for both (it's already just a threshold draw — do not rename it, that would ripple into every existing caller).

- [ ] **Step 1: Write failing test**

Add to `tests/test_probabilistic_engine.py`:
```python
from vf.probabilistic_engine import (
    compute_conduccion_maintain_probability,
    compute_control_success_probability,
)


def _receiver_attrs(control_balon=70, primer_toque=70):
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50,
                       control_balon=control_balon, primer_toque=primer_toque)


def test_higher_control_attributes_yield_higher_control_probability():
    weak = compute_control_success_probability(_receiver_attrs(30, 30), rival_distance_to_receiver=None)
    strong = compute_control_success_probability(_receiver_attrs(90, 90), rival_distance_to_receiver=None)
    assert strong > weak


def test_nearby_rival_lowers_control_probability():
    unmarked = compute_control_success_probability(_receiver_attrs(), rival_distance_to_receiver=15.0)
    marked = compute_control_success_probability(_receiver_attrs(), rival_distance_to_receiver=1.0)
    assert unmarked > marked


def _carrier_attrs(conduccion=70):
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50,
                       conduccion=conduccion)


def test_higher_conduccion_attribute_yields_higher_maintain_probability():
    weak = compute_conduccion_maintain_probability(_carrier_attrs(30), rival_distance=None)
    strong = compute_conduccion_maintain_probability(_carrier_attrs(90), rival_distance=None)
    assert strong > weak


def test_nearby_rival_lowers_conduccion_maintain_probability():
    open_space = compute_conduccion_maintain_probability(_carrier_attrs(), rival_distance=15.0)
    pressured = compute_conduccion_maintain_probability(_carrier_attrs(), rival_distance=1.0)
    assert open_space > pressured
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_probabilistic_engine.py -v`
Expected: FAIL — `ImportError: cannot import name 'compute_control_success_probability'`

- [ ] **Step 3: Add to `vf/probabilistic_engine.py`**

```python
# Control/Recepcion and Conduccion formulas — same sigmoid-on-(skill-vs-pressure)
# pattern as compute_pass_success_probability, reusing PRESSURE_X0/PRESSURE_K/
# PROB_X0 (same physical meaning: rival distance to the player handling the
# ball). Invented — Data/Simulation Bibles give no formula for Control de
# Balon, Primer Toque, or Conduccion beyond their bare names. See
# docs/decisions.md.
CONTROL_SKILL_DIVISOR = 200.0  # control_balon + primer_toque, each 0..100 -> 0..1
CONTROL_PROB_K = 6.0

CONDUCCION_SKILL_DIVISOR = 100.0  # conduccion attribute, 0..100 -> 0..1
CONDUCCION_PROB_K = 6.0


def compute_control_success_probability(
    receiver_attrs: Attributes, rival_distance_to_receiver: Optional[float]
) -> float:
    skill = (receiver_attrs.control_balon + receiver_attrs.primer_toque) / CONTROL_SKILL_DIVISOR
    if rival_distance_to_receiver is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance_to_receiver, PRESSURE_X0, PRESSURE_K)
    net_advantage = skill - pressure_score
    return score_sigmoid(net_advantage, PROB_X0, CONTROL_PROB_K)


def compute_conduccion_maintain_probability(
    carrier_attrs: Attributes, rival_distance: Optional[float]
) -> float:
    skill = carrier_attrs.conduccion / CONDUCCION_SKILL_DIVISOR
    if rival_distance is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)
    net_advantage = skill - pressure_score
    return score_sigmoid(net_advantage, PROB_X0, CONDUCCION_PROB_K)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_probabilistic_engine.py -v`
Expected: PASS (9 tests — 5 existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add vf/probabilistic_engine.py tests/test_probabilistic_engine.py
git commit -m "feat: control/reception and conduccion-maintain probability formulas"
```

---

## Task 2: Physics — Player Movement Step for Conducción

**Files:**
- Modify: `vf/physics.py`
- Test: `tests/test_physics.py`

**Interfaces:**
- Produces: `PLAYER_SPEED`, `CONDUCCION_STEP_DISTANCE`, `CONDUCCION_TICKS_PER_STEP`, `conduccion_step_target(position, direction, step_distance=CONDUCCION_STEP_DISTANCE) -> Tuple[float, float]`.

- [ ] **Step 1: Write failing test**

Add to `tests/test_physics.py`:
```python
import math

from vf.physics import CONDUCCION_STEP_DISTANCE, conduccion_step_target


def test_conduccion_step_moves_along_unit_direction():
    start = (0.0, 0.0)
    target = conduccion_step_target(start, direction=(1.0, 0.0))
    assert math.isclose(target[0], CONDUCCION_STEP_DISTANCE)
    assert math.isclose(target[1], 0.0, abs_tol=1e-9)


def test_conduccion_step_normalizes_non_unit_direction():
    start = (0.0, 0.0)
    target = conduccion_step_target(start, direction=(2.0, 0.0))  # not a unit vector
    assert math.isclose(target[0], CONDUCCION_STEP_DISTANCE)


def test_conduccion_step_handles_zero_direction_by_staying_put():
    start = (5.0, 5.0)
    target = conduccion_step_target(start, direction=(0.0, 0.0))
    assert target == start
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_physics.py -v`
Expected: FAIL — `ImportError: cannot import name 'conduccion_step_target'`

- [ ] **Step 3: Add to `vf/physics.py`**

```python
# Invented — Data Bible Vol VIII gives no equations for sustained movement.
# One conducción "step" = one re-evaluation opportunity (one cognitive cycle),
# matching the Simulation Bible's "contacto a contacto" granularity (Cap.
# 103.3/103.6), not raw per-tick physics. See docs/decisions.md.
PLAYER_SPEED = 5.0  # m/s
CONDUCCION_STEP_DISTANCE = 4.0  # meters covered per step
CONDUCCION_TICKS_PER_STEP = max(1, round((CONDUCCION_STEP_DISTANCE / PLAYER_SPEED) / SIM_DT))


def conduccion_step_target(
    position: Tuple[float, float], direction: Tuple[float, float],
    step_distance: float = CONDUCCION_STEP_DISTANCE,
) -> Tuple[float, float]:
    dx, dy = direction
    norm = math.hypot(dx, dy)
    if norm == 0.0:
        return position
    ux, uy = dx / norm, dy / norm
    return (position[0] + ux * step_distance, position[1] + uy * step_distance)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_physics.py -v`
Expected: PASS (7 tests — 4 existing + 3 new)

- [ ] **Step 5: Commit**

```bash
git add vf/physics.py tests/test_physics.py
git commit -m "feat: conduccion step physics (constant-velocity player movement)"
```

---

## Task 3: Alternatives — Conducción Direction Candidates

**Files:**
- Modify: `vf/alternatives.py`
- Test: `tests/test_alternatives.py`

**Interfaces:**
- Consumes: `vf.entities.Player`, `vf.goals.Goal`, `vf.physics.conduccion_step_target`, `vf.physics.CONDUCCION_STEP_DISTANCE`.
- Produces: `ConduccionAlternative(direction, target_position, distance)`, `generate_conduccion_alternatives(observer, goals) -> List[ConduccionAlternative]`, `CONDUCCION_DIRECTIONS_DEG`.

- [ ] **Step 1: Write failing test**

Add to `tests/test_alternatives.py`:
```python
import math

from vf.alternatives import ConduccionAlternative, generate_conduccion_alternatives
from vf.goals import Goal
from vf.physics import CONDUCCION_STEP_DISTANCE


def test_generates_eight_conduccion_directions_when_goal_present():
    observer = _observer()
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_conduccion_alternatives(observer, goals)

    assert len(alts) == 8
    for alt in alts:
        assert math.isclose(alt.distance, CONDUCCION_STEP_DISTANCE)
        # direction is a unit vector
        assert math.isclose(math.hypot(*alt.direction), 1.0, abs_tol=1e-6)


def test_forward_direction_targets_positive_x_from_observer():
    observer = _observer()  # at (0.0, 0.0)
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_conduccion_alternatives(observer, goals)
    forward = next(a for a in alts if math.isclose(a.direction[0], 1.0, abs_tol=1e-6)
                   and math.isclose(a.direction[1], 0.0, abs_tol=1e-6))

    assert math.isclose(forward.target_position[0], CONDUCCION_STEP_DISTANCE)
    assert math.isclose(forward.target_position[1], 0.0, abs_tol=1e-6)


def test_no_conduccion_alternatives_without_pasar_balon_goal():
    observer = _observer()

    alts = generate_conduccion_alternatives(observer, goals=[])

    assert alts == []
```

`_observer()` already exists in `tests/test_alternatives.py` from Iteración 1 (a `Player` at `(0.0, 0.0)`) — reuse it, don't redefine it.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_alternatives.py -v`
Expected: FAIL — `ImportError: cannot import name 'ConduccionAlternative'`

- [ ] **Step 3: Add to `vf/alternatives.py`**

```python
from vf.physics import CONDUCCION_STEP_DISTANCE, conduccion_step_target

# 8 compass directions relative to the attack axis (+x = 0deg). Invented —
# neither Bible gives a mechanism for choosing conducción direction; user
# confirmed evaluating multiple candidates through Utility AI over a single
# heuristic vector. See docs/decisions.md.
CONDUCCION_DIRECTIONS_DEG = [0, 45, -45, 90, -90, 135, -135, 180]


@dataclass
class ConduccionAlternative:
    direction: Tuple[float, float]
    target_position: Tuple[float, float]
    distance: float


def generate_conduccion_alternatives(observer: Player, goals: List[Goal]) -> List[ConduccionAlternative]:
    if not any(g.type == "PASAR_BALON" for g in goals):
        return []

    alternatives = []
    for deg in CONDUCCION_DIRECTIONS_DEG:
        rad = math.radians(deg)
        direction = (math.cos(rad), math.sin(rad))
        target = conduccion_step_target(observer.position, direction)
        alternatives.append(
            ConduccionAlternative(direction=direction, target_position=target, distance=CONDUCCION_STEP_DISTANCE)
        )
    return alternatives
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_alternatives.py -v`
Expected: PASS (6 tests — 3 existing + 3 new)

- [ ] **Step 5: Commit**

```bash
git add vf/alternatives.py tests/test_alternatives.py
git commit -m "feat: conduccion direction alternatives (8 candidates)"
```

---

## Task 4: Evaluation — Score Conducción Alternatives

**Files:**
- Modify: `vf/evaluation.py`
- Test: `tests/test_evaluation.py`

**Interfaces:**
- Consumes: `vf.alternatives.ConduccionAlternative`, `vf.perception.PerceivedEntity`, `vf.probabilistic_engine.compute_conduccion_maintain_probability`.
- Produces: `normalize_utilities(evaluated) -> List[EvaluatedAlternative]` (extracted from `evaluate_alternatives`'s existing body), `evaluate_conduccion_alternatives(carrier, alternatives, perceived) -> List[EvaluatedAlternative]`.

- [ ] **Step 1: Write failing test**

Add to `tests/test_evaluation.py`:
```python
from vf.alternatives import ConduccionAlternative
from vf.evaluation import evaluate_conduccion_alternatives, normalize_utilities
from vf.perception import PerceivedEntity


def test_conduccion_toward_open_space_beats_toward_marking_rival():
    carrier = _passer()  # at (0.0, 0.0), from existing test helper
    forward_open = ConduccionAlternative(direction=(1.0, 0.0), target_position=(4.0, 0.0), distance=4.0)
    forward_marked = ConduccionAlternative(direction=(1.0, 0.0), target_position=(4.0, 0.0), distance=4.0)
    perceived_with_rival_far = [PerceivedEntity(id="r1", team="B", position=(4.0, 15.0), distance=15.0)]
    perceived_with_rival_near = [PerceivedEntity(id="r1", team="B", position=(4.5, 0.5), distance=4.5)]

    open_eval = evaluate_conduccion_alternatives(carrier, [forward_open], perceived_with_rival_far)[0]
    marked_eval = evaluate_conduccion_alternatives(carrier, [forward_marked], perceived_with_rival_near)[0]

    assert open_eval.utility_raw > marked_eval.utility_raw


def test_normalize_utilities_handles_empty_list():
    assert normalize_utilities([]) == []


def test_normalize_utilities_combines_pass_and_conduccion_types():
    carrier = _passer()
    conduccion_alt = ConduccionAlternative(direction=(1.0, 0.0), target_position=(4.0, 0.0), distance=4.0)
    conduccion_evaluated = evaluate_conduccion_alternatives(carrier, [conduccion_alt], perceived=[])

    normalized = normalize_utilities(conduccion_evaluated)

    assert normalized[0].utility_normalized == 1.0  # only entry -> normalizes to 1.0
```

`_passer()` already exists in `tests/test_evaluation.py` from Iteración 1 — reuse it.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_evaluation.py -v`
Expected: FAIL — `ImportError: cannot import name 'evaluate_conduccion_alternatives'`

- [ ] **Step 3: Modify `vf/evaluation.py`**

Extract the existing normalization loop out of `evaluate_alternatives` into its own function, keep `evaluate_alternatives`'s external behavior identical, then add the conducción evaluator:

```python
from vf.alternatives import ConduccionAlternative, PassAlternative
from vf.perception import PerceivedEntity
from vf.probabilistic_engine import compute_conduccion_maintain_probability


def normalize_utilities(evaluated: List[EvaluatedAlternative]) -> List[EvaluatedAlternative]:
    if not evaluated:
        return evaluated
    utilities = [e.utility_raw for e in evaluated]
    u_min, u_max = min(utilities), max(utilities)
    span = u_max - u_min
    for e in evaluated:
        e.utility_normalized = 1.0 if span == 0.0 else (e.utility_raw - u_min) / span
    return evaluated


def evaluate_alternatives(
    passer: Player, alternatives: List[PassAlternative], context: ContextualState
) -> List[EvaluatedAlternative]:
    evaluated = [_evaluate_single(passer, alt, context) for alt in alternatives]
    return normalize_utilities(evaluated)


def _evaluate_single_conduccion(
    carrier: Player, alt: ConduccionAlternative, rivals: List[PerceivedEntity]
) -> EvaluatedAlternative:
    forward_gain = alt.target_position[0] - carrier.position[0]
    score_beneficio = score_linear(forward_gain, BENEFIT_MIN, BENEFIT_MAX)

    if rivals:
        rival_distance = min(
            math.hypot(alt.target_position[0] - r.position[0], alt.target_position[1] - r.position[1])
            for r in rivals
        )
    else:
        rival_distance = None
    pressure = 0.0 if rival_distance is None else 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)
    score_seguridad = 1.0 - pressure

    score_prob_exito = compute_conduccion_maintain_probability(carrier.attributes, rival_distance)

    utility_raw = (
        W_BENEFICIO * score_beneficio + W_SEGURIDAD * score_seguridad
    ) * (score_prob_exito ** W_VIABILIDAD)

    return EvaluatedAlternative(
        alternative=alt, score_beneficio=score_beneficio, score_seguridad=score_seguridad,
        score_prob_exito=score_prob_exito, utility_raw=utility_raw,
    )


def evaluate_conduccion_alternatives(
    carrier: Player, alternatives: List[ConduccionAlternative], perceived: List[PerceivedEntity]
) -> List[EvaluatedAlternative]:
    rivals = [e for e in perceived if e.team != carrier.team]
    evaluated = [_evaluate_single_conduccion(carrier, alt, rivals) for alt in alternatives]
    return normalize_utilities(evaluated)
```

Add `import math` at the top of `vf/evaluation.py` if not already present.

Note (do not "fix"): `evaluate_conduccion_alternatives` and `evaluate_alternatives` each normalize their own list independently. When `vf/cognitive_cycle.py` (Task 5) concatenates a Pass-evaluated list and a Conducción-evaluated list and calls `normalize_utilities` again on the combined list, the two per-type normalizations done here get harmlessly overwritten by the final combined one — `utility_raw` (the only value that matters for the final normalization) is untouched by either intermediate call. This keeps both functions independently testable and keeps Iteración 1's `evaluate_alternatives` contract/tests unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_evaluation.py -v`
Expected: PASS (6 tests — 3 existing + 3 new)

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `python3 -m pytest -v`
Expected: all tests PASS (the `evaluate_alternatives` extraction must not change its observable behavior).

- [ ] **Step 6: Commit**

```bash
git add vf/evaluation.py tests/test_evaluation.py
git commit -m "feat: evaluate conduccion alternatives, extract shared normalization"
```

---

## Task 5: Cognitive Cycle — Combine Alternatives, Conservar Threshold

**Files:**
- Modify: `vf/cognitive_cycle.py`
- Test: `tests/test_cognitive_cycle.py`

**Interfaces:**
- Consumes: everything from Tasks 3-4 plus existing Percepción/Comprensión/Objetivos/Selección.
- Produces: updated `CognitiveCycleResult(perceived, context, goals, pass_alternatives, conduccion_alternatives, evaluated, chosen, intention_type)`, `CONSERVAR_THRESHOLD`.

**This task changes `CognitiveCycleResult`'s shape** (Iteración 1 had a single `alternatives` field; this splits it into `pass_alternatives` + `conduccion_alternatives` and adds `intention_type`). Update every existing test in `tests/test_cognitive_cycle.py` that constructs or reads a `CognitiveCycleResult` — this is an intentional, plan-scoped breaking change, not a regression to avoid.

- [ ] **Step 1: Write failing test**

Rewrite `tests/test_cognitive_cycle.py`'s existing tests to match the new result shape, and add new ones. Full replacement content:

```python
import random

from vf.entities import Attributes, Ball, MatchState, Personality, Player
from vf.cognitive_cycle import CONSERVAR_THRESHOLD, run_cognitive_cycle


def _attrs(pase_corto=70, control_balon=70, primer_toque=70, conduccion=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50,
                       control_balon=control_balon, primer_toque=primer_toque, conduccion=conduccion)


def _four_player_scenario():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0, has_ball=True)
    near_forward = Player(id="p2", team="A", position=(8.0, 2.0), attributes=_attrs())
    far_sideways = Player(id="p3", team="A", position=(-15.0, 0.0), attributes=_attrs())  # behind, outside FOV
    marked_forward = Player(id="p4", team="A", position=(8.0, -2.0), attributes=_attrs())
    rival = Player(id="r1", team="B", position=(8.0, -3.0), attributes=_attrs())  # marks p4 closely

    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, near_forward, far_sideways, marked_forward, rival],
                       ball=ball, tick=0, seed=5)


def test_full_cycle_perceives_teammates_within_fov_only_criterio_1():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    perceived_ids = {e.id for e in result.perceived}
    assert "p2" in perceived_ids
    assert "p4" in perceived_ids
    assert "p3" not in perceived_ids


def test_full_cycle_combines_pass_and_conduccion_alternatives():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert len(result.pass_alternatives) >= 2  # p2, p4 visible
    assert len(result.conduccion_alternatives) == 8
    assert len(result.evaluated) == len(result.pass_alternatives) + len(result.conduccion_alternatives)


def test_full_cycle_selection_reproducible_under_same_seed_criterio_3():
    state_a = _four_player_scenario()
    state_b = _four_player_scenario()

    result_a = run_cognitive_cycle(state_a.players[0], state_a, random.Random(state_a.seed))
    result_b = run_cognitive_cycle(state_b.players[0], state_b, random.Random(state_b.seed))

    assert result_a.intention_type == result_b.intention_type
    if result_a.chosen is not None:
        assert type(result_a.chosen.alternative) == type(result_b.chosen.alternative)


def _all_options_starved_scenario():
    # Passer surrounded by rivals in every conduccion direction and with no
    # visible teammates -> every alternative should score below
    # CONSERVAR_THRESHOLD, forcing the CONSERVAR intention (Criterio 1).
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(pase_corto=30, conduccion=20),
                     facing_rad=0.0, has_ball=True)
    rivals = [
        Player(id=f"r{i}", team="B", position=pos, attributes=_attrs())
        for i, pos in enumerate([(3.0, 0.0), (-3.0, 0.0), (0.0, 3.0), (0.0, -3.0),
                                  (2.1, 2.1), (-2.1, 2.1), (2.1, -2.1), (-2.1, -2.1)])
    ]
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, *rivals], ball=ball, tick=0, seed=9)


def test_full_cycle_conserves_when_all_alternatives_below_threshold_criterio_1():
    state = _all_options_starved_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert max(e.utility_raw for e in result.evaluated) < CONSERVAR_THRESHOLD
    assert result.intention_type == "CONSERVAR"
    assert result.chosen is None


def test_non_ball_carrier_produces_no_cycle_result():
    state = _four_player_scenario()
    non_carrier = state.players[1]

    result = run_cognitive_cycle(non_carrier, state, random.Random(state.seed))

    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cognitive_cycle.py -v`
Expected: FAIL (old `CognitiveCycleResult` shape doesn't have `pass_alternatives`/`conduccion_alternatives`/`intention_type`, and `CONSERVAR_THRESHOLD` doesn't exist yet).

- [ ] **Step 3: Rewrite `vf/cognitive_cycle.py`**

```python
import random
from dataclasses import dataclass
from typing import List, Optional

from vf.alternatives import (
    ConduccionAlternative,
    PassAlternative,
    generate_conduccion_alternatives,
    generate_pass_alternatives,
)
from vf.entities import MatchState, Player
from vf.evaluation import EvaluatedAlternative, evaluate_alternatives, evaluate_conduccion_alternatives, normalize_utilities
from vf.goals import Goal, generate_goals
from vf.perception import PerceivedEntity, perceive
from vf.selection import select_alternative
from vf.understanding import ContextualState, build_context

# Utility threshold below which Selection converts its best available option
# into a CONSERVAR intention instead of acting on it (Iteracion 2 Cap. 52 —
# "El umbral... es un parametro nuevo... Su valor inicial sera provisional").
# Invented, expected to be recalibrated — see docs/decisions.md.
CONSERVAR_THRESHOLD = 0.15


@dataclass
class CognitiveCycleResult:
    perceived: List[PerceivedEntity]
    context: ContextualState
    goals: List[Goal]
    pass_alternatives: List[PassAlternative]
    conduccion_alternatives: List[ConduccionAlternative]
    evaluated: List[EvaluatedAlternative]
    chosen: Optional[EvaluatedAlternative]
    intention_type: str  # "PASE" | "CONDUCCION" | "CONSERVAR" | "NINGUNA"


def run_cognitive_cycle(
    observer: Player, state: MatchState, rng: random.Random
) -> Optional[CognitiveCycleResult]:
    goals = generate_goals(observer, state)
    if not goals:
        return None  # LOD (Vol XXXII): only the ball carrier runs the full cycle

    perceived = perceive(observer, state)
    context = build_context(observer, perceived)

    pass_alts = generate_pass_alternatives(observer, perceived, goals)
    conduccion_alts = generate_conduccion_alternatives(observer, goals)

    pass_evaluated = evaluate_alternatives(observer, pass_alts, context) if pass_alts else []
    conduccion_evaluated = (
        evaluate_conduccion_alternatives(observer, conduccion_alts, perceived) if conduccion_alts else []
    )

    combined = pass_evaluated + conduccion_evaluated
    normalize_utilities(combined)  # re-normalize across BOTH types together; see Task 4 note

    if not combined:
        return CognitiveCycleResult(perceived, context, goals, pass_alts, conduccion_alts, [], None, "NINGUNA")

    best_raw = max(e.utility_raw for e in combined)
    if best_raw < CONSERVAR_THRESHOLD:
        return CognitiveCycleResult(
            perceived, context, goals, pass_alts, conduccion_alts, combined, None, "CONSERVAR"
        )

    chosen = select_alternative(rng, combined, observer.personality.creatividad)
    intention_type = "PASE" if isinstance(chosen.alternative, PassAlternative) else "CONDUCCION"
    return CognitiveCycleResult(
        perceived, context, goals, pass_alts, conduccion_alts, combined, chosen, intention_type
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cognitive_cycle.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Fix `tests/test_simulation.py`'s use of the old `CognitiveCycleResult` shape**

`tests/test_simulation.py` doesn't construct `CognitiveCycleResult` directly (it only calls `run_one_possession`, which is being replaced in Task 8) — leave it as-is for now; Task 8 rewrites `vf/simulation.py` and its tests together. Confirm this by running the full suite next and reading any failure carefully before touching anything.

- [ ] **Step 6: Run full suite, expect specific pre-existing failures only in `test_simulation.py`**

Run: `python3 -m pytest -v`
Expected: `tests/test_simulation.py` tests FAIL or ERROR (they call `run_one_possession`, which still exists unchanged from Iteración 1 and should still work standalone since it doesn't touch `CognitiveCycleResult`'s new fields directly — if they pass, that's fine too; if they fail, note exactly why in your report, but do NOT modify `vf/simulation.py` in this task, that's Task 8's job). Every other test file must PASS.

- [ ] **Step 7: Commit**

```bash
git add vf/cognitive_cycle.py tests/test_cognitive_cycle.py
git commit -m "feat: combine pass+conduccion alternatives, add CONSERVAR intention"
```

---

## Task 6: Match Engine — Two-Stage Pass/Control, Conducción, Conservar, Loose-Ball Recovery

**Files:**
- Modify: `vf/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Consumes: `vf.probabilistic_engine.{compute_control_success_probability, compute_conduccion_maintain_probability, resolve_pass}`, `vf.physics.CONDUCCION_TICKS_PER_STEP`, `vf.evaluation.EvaluatedAlternative`, `vf.alternatives.ConduccionAlternative`.
- Produces: modified `execute_pass` (now two-stage: `pass_success` + `control_success`, overall `success = pass_success and control_success`), `execute_conduccion(state, carrier_id, chosen, rng) -> Dict`, `execute_conservar(state, carrier_id) -> Dict`, `recover_loose_ball(state) -> Optional[str]`, `CONSERVAR_TICKS`.

- [ ] **Step 1: Write failing test**

Rewrite `tests/test_match_engine.py` in full (the two-stage change alters `execute_pass`'s return shape and success semantics):

```python
import random

from vf.alternatives import ConduccionAlternative, PassAlternative
from vf.entities import Attributes, Ball, MatchState, Player
from vf.evaluation import EvaluatedAlternative
from vf.match_engine import execute_conduccion, execute_conservar, execute_pass, recover_loose_ball


def _attrs(pase_corto=90, control_balon=90, primer_toque=90, conduccion=90):
    return Attributes(pase_corto=pase_corto, vision=90, decision=90,
                       posicionamiento_ofensivo=90, posicionamiento_defensivo=90,
                       control_balon=control_balon, primer_toque=primer_toque, conduccion=conduccion)


def _state_with_two_players(receiver_attrs=None):
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=receiver_attrs or _attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)


def _chosen_pass_alt(target_id="p2", target_position=(6.0, 0.0)):
    alt = PassAlternative(target_player_id=target_id, target_position=target_position, distance=6.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                 score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)


def test_successful_pass_and_control_transfers_ball_ownership():
    state = _state_with_two_players()
    rng = random.Random(1)

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    receiver = next(p for p in state.players if p.id == "p2")
    assert log["pass_success"] is True
    assert log["control_success"] is True
    assert log["success"] is True
    assert state.ball.owner_id == "p2"
    assert receiver.has_ball is True


def test_failed_control_leaves_ball_loose_then_recovered():
    state = _state_with_two_players(receiver_attrs=_attrs(control_balon=10, primer_toque=10))
    rng = random.Random(1)
    call_count = {"n": 0}
    real_random = rng.random

    def rigged(*args, **kwargs):
        call_count["n"] += 1
        return 0.01 if call_count["n"] == 1 else 0.99  # pass succeeds, control fails
    rng.random = rigged

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is True
    assert log["control_success"] is False
    assert log["success"] is False
    assert log["recovered_by"] is not None  # nearest player (the receiver itself, at the ball's position) recovers
    assert state.ball.state == "controlled"  # recovered, not left loose forever


def test_failed_pass_never_reaches_control_stage():
    state = _state_with_two_players()
    rng = random.Random(1)
    rng.random = lambda: 0.999  # forces pass failure regardless of probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_pass_alt(), rng=rng)

    assert log["pass_success"] is False
    assert log["control_success"] is None
    assert log["success"] is False


def _chosen_conduccion_alt(direction=(1.0, 0.0), target_position=(4.0, 0.0)):
    alt = ConduccionAlternative(direction=direction, target_position=target_position, distance=4.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.7, score_seguridad=0.8,
                                 score_prob_exito=0.9, utility_raw=0.75, utility_normalized=1.0)


def test_execute_conduccion_moves_carrier_and_ball_together_on_success():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=0, seed=1)
    rng = random.Random(1)  # high conduccion attr, no rivals -> should maintain control

    log = execute_conduccion(state, carrier_id="p1", chosen=_chosen_conduccion_alt(), rng=rng)

    assert log["success"] is True
    assert passer.position == (4.0, 0.0)
    assert state.ball.position == (4.0, 0.0)
    assert passer.has_ball is True


def test_execute_conservar_advances_tick_without_moving():
    passer = Player(id="p1", team="A", position=(3.0, 4.0), attributes=_attrs(), has_ball=True)
    ball = Ball(position=(3.0, 4.0), owner_id="p1")
    state = MatchState(players=[passer], ball=ball, tick=10, seed=1)

    log = execute_conservar(state, carrier_id="p1")

    assert log["success"] is True
    assert passer.position == (3.0, 4.0)
    assert passer.has_ball is True
    assert state.tick > 10


def test_recover_loose_ball_assigns_nearest_player():
    p_near = Player(id="near", team="A", position=(1.0, 0.0), attributes=_attrs())
    p_far = Player(id="far", team="B", position=(10.0, 0.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id=None, state="loose")
    state = MatchState(players=[p_near, p_far], ball=ball, tick=0, seed=1)

    recovered_id = recover_loose_ball(state)

    assert recovered_id == "near"
    assert p_near.has_ball is True
    assert state.ball.owner_id == "near"
    assert state.ball.state == "controlled"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: FAIL — `ImportError: cannot import name 'execute_conduccion'`

- [ ] **Step 3: Rewrite `vf/match_engine.py`**

```python
import math
import random
from typing import Dict, Optional

from vf.entities import MatchState
from vf.evaluation import EvaluatedAlternative
from vf.physics import CONDUCCION_TICKS_PER_STEP, advance_ball, start_pass
from vf.probabilistic_engine import (
    compute_conduccion_maintain_probability,
    compute_control_success_probability,
    compute_pass_success_probability,
    resolve_pass,
)

CONSERVAR_TICKS = 1  # minimal simulated-time advance for a CONSERVAR cycle. Invented.


def _nearest_real_rival_distance(state: MatchState, team: str, position) -> Optional[float]:
    rivals = [p for p in state.players if p.team != team]
    if not rivals:
        return None
    return min(math.hypot(position[0] - r.position[0], position[1] - r.position[1]) for r in rivals)


def recover_loose_ball(state: MatchState) -> Optional[str]:
    if not state.players:
        return None
    nearest = min(
        state.players,
        key=lambda p: math.hypot(p.position[0] - state.ball.position[0], p.position[1] - state.ball.position[1]),
    )
    nearest.has_ball = True
    state.ball.owner_id = nearest.id
    state.ball.state = "controlled"
    return nearest.id


def execute_pass(
    state: MatchState, passer_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    passer = next(p for p in state.players if p.id == passer_id)
    target = next(p for p in state.players if p.id == chosen.alternative.target_player_id)

    if not passer.has_ball:
        raise ValueError(f"{passer_id} does not have the ball, cannot pass")
    if target.id == passer.id:
        raise ValueError("cannot pass to self")

    start_pass(state.ball, passer.position, chosen.alternative.target_position, target.id)
    ticks_elapsed = 0
    while not advance_ball(state.ball):
        ticks_elapsed += 1
    ticks_elapsed += 1
    state.tick += ticks_elapsed

    passer.has_ball = False

    # Stage 1: pass accuracy (passer-side)
    real_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    real_probability = compute_pass_success_probability(
        passer.attributes, chosen.alternative.distance, real_rival_distance
    )
    pass_success = resolve_pass(rng, real_probability)

    log = {
        "passer_id": passer.id,
        "target_player_id": target.id,
        "distance_m": chosen.alternative.distance,
        "score_beneficio": chosen.score_beneficio,
        "score_seguridad": chosen.score_seguridad,
        "score_prob_exito_percibida": chosen.score_prob_exito,
        "utility_normalized": chosen.utility_normalized,
        "real_probability": real_probability,
        "pass_success": pass_success,
        "ticks_elapsed": ticks_elapsed,
    }

    if not pass_success:
        state.ball.state = "loose"
        state.ball.owner_id = None
        log["control_success"] = None
        log["control_probability"] = None
        log["success"] = False
        log["recovered_by"] = recover_loose_ball(state)
        return log

    # Stage 2: receiver's control/reception (receiver-side, Criterio 3 of Iteracion 2)
    control_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    control_probability = compute_control_success_probability(target.attributes, control_rival_distance)
    control_success = resolve_pass(rng, control_probability)

    log["control_probability"] = control_probability
    log["control_success"] = control_success
    log["success"] = control_success

    if control_success:
        state.ball.state = "controlled"
        state.ball.owner_id = target.id
        target.has_ball = True
        log["recovered_by"] = None
    else:
        state.ball.state = "loose"
        state.ball.owner_id = None
        log["recovered_by"] = recover_loose_ball(state)

    return log


def execute_conduccion(
    state: MatchState, carrier_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    carrier = next(p for p in state.players if p.id == carrier_id)
    if not carrier.has_ball:
        raise ValueError(f"{carrier_id} does not have the ball, cannot conducir")

    alt = chosen.alternative
    new_position = alt.target_position

    rival_distance = _nearest_real_rival_distance(state, carrier.team, new_position)
    maintain_probability = compute_conduccion_maintain_probability(carrier.attributes, rival_distance)
    maintained = resolve_pass(rng, maintain_probability)

    carrier.position = new_position
    state.ball.position = new_position
    state.tick += CONDUCCION_TICKS_PER_STEP

    log = {
        "carrier_id": carrier.id,
        "direction": alt.direction,
        "new_position": new_position,
        "maintain_probability": maintain_probability,
        "success": maintained,
        "ticks_elapsed": CONDUCCION_TICKS_PER_STEP,
    }

    if maintained:
        log["recovered_by"] = None
    else:
        carrier.has_ball = False
        state.ball.state = "loose"
        state.ball.owner_id = None
        log["recovered_by"] = recover_loose_ball(state)

    return log


def execute_conservar(state: MatchState, carrier_id: str) -> Dict:
    carrier = next(p for p in state.players if p.id == carrier_id)
    if not carrier.has_ball:
        raise ValueError(f"{carrier_id} does not have the ball, cannot conservar")

    state.tick += CONSERVAR_TICKS

    return {
        "carrier_id": carrier.id,
        "success": True,
        "ticks_elapsed": CONSERVAR_TICKS,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: PASS (7 tests)

Note on `test_failed_control_leaves_ball_loose_then_recovered`: the rigged `rng.random` forces stage 1 to succeed and stage 2 to fail regardless of the real computed probabilities — this keeps the test decoupled from exact probability values (which depend on constants you're not meant to hand-tune here). If the natural probabilities from `_attrs(control_balon=10, primer_toque=10)` already make this rigging unnecessary, that's fine too — keep the rig either way for determinism, matching the pattern already used in `test_match_engine.py` from Iteración 1.

- [ ] **Step 5: Commit**

```bash
git add vf/match_engine.py tests/test_match_engine.py
git commit -m "feat: two-stage pass/control resolution, execute_conduccion, execute_conservar, loose-ball recovery"
```

---

## Task 7: Degeneracy Checks — Loop Detection (4A) and Conducción Streak (4B)

**Files:**
- Create: `vf/degeneracy.py`
- Test: `tests/test_degeneracy.py`

**Interfaces:**
- Produces: `MAX_LOOP_REPEATS`, `MAX_CONDUCCION_STREAK`, `detect_action_loop(history, max_consecutive=MAX_LOOP_REPEATS) -> bool`, `max_conduccion_streak(history) -> int`. `history` is `List[Dict]`, each dict shaped `{"actor_id": str, "action_type": str, "action_key": Any}`.

- [ ] **Step 1: Write failing test**

`tests/test_degeneracy.py`:
```python
from vf.degeneracy import MAX_CONDUCCION_STREAK, MAX_LOOP_REPEATS, detect_action_loop, max_conduccion_streak


def _entry(actor_id, action_type, action_key):
    return {"actor_id": actor_id, "action_type": action_type, "action_key": action_key}


def test_no_loop_detected_in_varied_history():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (0.0, 1.0)),
    ]
    assert detect_action_loop(history) is False


def test_loop_detected_when_same_action_repeats_past_threshold():
    history = [_entry("p1", "CONDUCCION", (1.0, 0.0))] * (MAX_LOOP_REPEATS + 1)
    assert detect_action_loop(history) is True


def test_loop_not_flagged_at_exactly_the_threshold():
    history = [_entry("p1", "CONDUCCION", (1.0, 0.0))] * MAX_LOOP_REPEATS
    assert detect_action_loop(history) is False


def test_different_actors_repeating_same_action_key_is_not_a_loop():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
    ]
    assert detect_action_loop(history) is False


def test_max_conduccion_streak_counts_consecutive_same_actor_conduccion():
    history = [
        _entry("p1", "CONDUCCION", (1.0, 0.0)),
        _entry("p1", "CONDUCCION", (0.0, 1.0)),  # different direction, still CONDUCCION -> counts
        _entry("p1", "PASE", "p2"),
        _entry("p2", "CONDUCCION", (1.0, 0.0)),
    ]
    assert max_conduccion_streak(history) == 2


def test_max_conduccion_streak_zero_when_no_conduccion():
    history = [_entry("p1", "PASE", "p2"), _entry("p2", "CONSERVAR", None)]
    assert max_conduccion_streak(history) == 0


def test_conduccion_streak_threshold_constant_is_positive():
    assert MAX_CONDUCCION_STREAK > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_degeneracy.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vf.degeneracy'`

- [ ] **Step 3: Write `vf/degeneracy.py`**

```python
from typing import Any, Dict, List

# Criterio 4A: no possession should have the same actor repeat the exact same
# action+target/direction more than this many times in a row.
# Criterio 4B: no player should conducir for more than this many consecutive
# steps without their intention changing.
# Both invented — the Iteracion 2 plan deliberately leaves these unfixed
# ("no se fija a priori... para evitar convertir un valor provisional en una
# decision arquitectonica antes de disponer de datos"). See docs/decisions.md.
MAX_LOOP_REPEATS = 4
MAX_CONDUCCION_STREAK = 6


def detect_action_loop(history: List[Dict[str, Any]], max_consecutive: int = MAX_LOOP_REPEATS) -> bool:
    if len(history) < max_consecutive + 1:
        return False

    streak = 1
    for i in range(1, len(history)):
        prev, curr = history[i - 1], history[i]
        same = (
            prev["actor_id"] == curr["actor_id"]
            and prev["action_type"] == curr["action_type"]
            and prev["action_key"] == curr["action_key"]
        )
        if same:
            streak += 1
            if streak > max_consecutive:
                return True
        else:
            streak = 1
    return False


def max_conduccion_streak(history: List[Dict[str, Any]]) -> int:
    longest = 0
    streak = 0
    prev_actor = None
    for entry in history:
        if entry["action_type"] == "CONDUCCION" and entry["actor_id"] == prev_actor:
            streak += 1
        elif entry["action_type"] == "CONDUCCION":
            streak = 1
        else:
            streak = 0
        longest = max(longest, streak)
        prev_actor = entry["actor_id"] if entry["action_type"] == "CONDUCCION" else None
    return longest
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_degeneracy.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/degeneracy.py tests/test_degeneracy.py
git commit -m "feat: degeneracy checks — action-loop detection (4A), conduccion streak (4B)"
```

---

## Task 8: Simulation — Multi-Cycle Possession Loop

**Files:**
- Modify: `vf/simulation.py`
- Test: `tests/test_simulation.py`

**Interfaces:**
- Consumes: everything from Tasks 5-7.
- Produces: `MAX_CYCLES_PER_POSSESSION`, `run_possession(state, rng) -> List[Dict]` (replaces `run_one_possession`), updated `build_scenario` (`_attrs` now varies the three new attributes too).

**This task removes `run_one_possession`** — its single-cycle behavior is now the first iteration of `run_possession`'s loop. Update every caller (`scripts/generate_review_log.py`, `scripts/run_simulation.py` are handled in Task 9 — don't touch them here, just don't break their imports more than necessary; note any import breakage in your report for Task 9 to pick up).

- [ ] **Step 1: Write failing test**

Replace `tests/test_simulation.py` in full:

```python
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
                     attributes=_attrs(pase_corto=20, conduccion=10), facing_rad=0.0, has_ball=True)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_simulation.py -v`
Expected: FAIL — `ImportError: cannot import name 'run_possession'`

- [ ] **Step 3: Rewrite `vf/simulation.py`**

```python
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

    for _ in range(MAX_CYCLES_PER_POSSESSION):
        carrier = next((p for p in state.players if p.has_ball), None)
        if carrier is None:
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
```

Note: `others = [e for e in result.evaluated if e is not result.chosen]` uses object identity (`is not`), not `target_player_id` comparison as Iteración 1's `near_tie` logic did — this is necessary here because Conducción alternatives don't have a `target_player_id` field to compare on, and identity comparison works uniformly for both Pass and Conducción entries.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_simulation.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run full suite**

Run: `python3 -m pytest -v`
Expected: every test file PASSES except possibly `scripts/`-adjacent breakage isn't test-covered directly — confirm no `tests/*.py` failures. If `scripts/generate_review_log.py` or `scripts/run_simulation.py` still reference `run_one_possession`, that's expected and fixed in Task 9 — don't fix it here.

- [ ] **Step 6: Commit**

```bash
git add vf/simulation.py tests/test_simulation.py
git commit -m "feat: multi-cycle possession loop (run_possession) — Pase/Conducir/Conservar chaining"
```

---

## Task 9: Update Scripts for Multi-Cycle Logging

**Files:**
- Modify: `scripts/generate_review_log.py`
- Modify: `scripts/run_simulation.py`

**Interfaces:**
- Consumes: `vf.simulation.{build_scenario, run_possession}`, `vf.degeneracy.{detect_action_loop, max_conduccion_streak}`.

- [ ] **Step 1: Rewrite `scripts/generate_review_log.py`**

```python
"""Generates possession-level logs for human behavioral review
(Plan Tecnico Iteracion 2, Criterios de Exito 1-5 / Validacion Conductual).
Run: python3 scripts/generate_review_log.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.degeneracy import detect_action_loop, max_conduccion_streak  # noqa: E402
from vf.simulation import build_scenario, run_possession  # noqa: E402

N_POSSESSIONS = 25
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "decisions_review_log.jsonl"


def main() -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for seed in range(N_POSSESSIONS):
            state = build_scenario(seed=seed)
            rng = random.Random(state.seed)
            steps = run_possession(state, rng)
            if not steps:
                continue

            history = [
                {"actor_id": s.get("carrier_id", s.get("passer_id")), "action_type": s["intention_type"],
                 "action_key": s.get("target_player_id") or s.get("direction")}
                for s in steps
            ]

            record = {
                "seed": seed,
                "steps": steps,
                "loop_detected": detect_action_loop(history),
                "max_conduccion_streak": max_conduccion_streak(history),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote possession log to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rewrite `scripts/run_simulation.py`**

```python
"""Runs a single possession end to end (possibly several cycles: Conducir,
Pase, Conservar chained together) and renders before/after schematic 2D
snapshots. Run: python3 scripts/run_simulation.py [seed]
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_possession  # noqa: E402
from vf.visualization import render_scenario  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    state = build_scenario(seed=seed)
    render_scenario(state, title=f"Antes (seed={seed})", out_path="frame_before.png")

    rng = random.Random(state.seed)
    steps = run_possession(state, rng)
    if not steps:
        print("No decision was made (no alternatives generated).")
        return

    render_scenario(state, title=f"Despues (seed={seed}, {len(steps)} ciclos)", out_path="frame_after.png")
    for i, step in enumerate(steps):
        print(f"ciclo {i}: {step['intention_type']} -> success={step.get('success')}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Manually verify both scripts run**

Run:
```bash
python3 scripts/generate_review_log.py
python3 scripts/run_simulation.py 1
```
Expected: `decisions_review_log.jsonl` written with 25 lines, each containing a `steps` list; `run_simulation.py` prints one line per cycle and writes `frame_before.png`/`frame_after.png` without error. (`vf/visualization.py`'s `render_pass_trajectory` is unused by this rewrite — that's fine, it was already flagged as unused in Iteración 1's final review; leave it as-is, don't touch it in this task.)

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_review_log.py scripts/run_simulation.py
git commit -m "feat: update scripts for multi-cycle possession logging"
```

---

## Task 10: Recalibration Pass and Final Verification Against the 5 New Criterios

Not a pure code task — mirrors Iteración 1's Task 14. Produces the evidence needed to accept or reject the Iteración 2 hypothesis, and performs the empirical weight recalibration the plan's own Hallazgo 2 anticipates.

- [ ] **Step 1: Run the full automated suite**

```bash
python3 -m pytest -v
```
Save the full output. This is evidence for the unit/integration parts of Criterios 1-5 (each has a dedicated test: Criterio 1 in `test_cognitive_cycle.py::..._criterio_1`, Criterio 3's two-stage split in `test_match_engine.py`, Criterios 4A/4B in `test_degeneracy.py`, Criterio 5's explicability in every `alternatives_considered`/`weights` field already present in the log format).

- [ ] **Step 2: Verify the specific integration transitions the plan names**

The plan's validation section explicitly requires checking: Conducir → Pasar, Pasar → Recibir, Recibir → Conducir, Conducir → Conservar. Write one small standalone script (or extend `tests/test_simulation.py` with 1-2 more integration tests if a clean scenario is easy to construct) that runs `run_possession` on a scenario engineered to plausibly hit at least 3 of these 4 transitions in one sequence, and print/assert the `intention_type` sequence. Report which transitions were and weren't observed across the 25-possession review log generated in Step 3 below — if some never occur naturally, say so; that's a legitimate finding, not a failure to hide.

- [ ] **Step 3: Generate the review log**

```bash
python3 scripts/generate_review_log.py
```

- [ ] **Step 4: Recalibration pass (Hallazgo 2)**

Inspect the review log for the pathology that motivated this iteration: does the system still force a Pase to a heavily-marked teammate (low `score_seguridad`) when Conservar or Conducción would have been more sensible? If yes, that's expected on first run — adjust `CONSERVAR_THRESHOLD` (`vf/cognitive_cycle.py`) and/or `W_BENEFICIO`/`W_SEGURIDAD`/`W_VIABILIDAD` (`vf/evaluation.py`) by small increments, regenerate the log, and repeat until the six originally-flagged-style cases (marked-teammate passes) either disappear or become visibly rarer. Document every constant you change and why in `docs/decisions.md`, and note the before/after comparison in your final report — this is the recalibration Hallazgo 2 explicitly asked for, not optional polish.

- [ ] **Step 5: Check for loop degeneracy across the full log**

```bash
python3 -c "
import json
with open('decisions_review_log.jsonl') as f:
    records = [json.loads(l) for l in f]
loops = [r['seed'] for r in records if r['loop_detected']]
streaks = [r['max_conduccion_streak'] for r in records]
print('possessions with a detected loop:', loops)
print('max conduccion streak seen:', max(streaks) if streaks else 0)
print('MAX_CONDUCCION_STREAK threshold:', __import__('vf.degeneracy', fromlist=['MAX_CONDUCCION_STREAK']).MAX_CONDUCCION_STREAK)
"
```
If any possession trips `loop_detected`, inspect it by hand (its `steps` list is right there in the JSONL) and report whether it's a genuine degenerate pattern (Criterio 4A fails) or a false positive in the detector's definition (document either conclusion).

- [ ] **Step 6: Render a handful of snapshots**

```bash
python3 scripts/run_simulation.py 1
python3 scripts/run_simulation.py 7
python3 scripts/run_simulation.py 15
```
Send the resulting PNGs and each run's per-cycle console output to the user.

- [ ] **Step 7: Present the log for human behavioral review (Criterio 5) and Criterios 1/2/3 sign-off**

As in Iteración 1, do not self-certify Criterio 5. Present the user a readable summary of enough possessions to judge credibility (the plan says "revisar suficientes casos como para tener confianza, no tantos como para volver la revisión imposible" — use judgment, likely 10-15 of the 25 is enough, prioritizing possessions with multiple cycles/interesting transitions over single-cycle ones), and ask for their verdict — specifically inviting comment on whether Conservar/Conducción now appear where a real player would have chosen them (the exact gap Iteración 1's review flagged).

- [ ] **Step 8: Write the final summary**

Cover: what was built, every decision made that wasn't explicit in `Plan_Tecnico_Iteracion_2` (cross-reference `docs/decisions.md`), the recalibration results from Step 4, the transition-coverage findings from Step 2, the loop-degeneracy findings from Step 5, and — per the plan's own mandatory "Sección Obligatoria: Lecciones Aprendidas" (Cap. 8) — an explicit closing list of: limitations discovered, unexpected emergent behavior, insufficiencies in the success criteria themselves, newly-visible module dependencies, and any parameter that was harder to calibrate than expected. This section is not optional per the source document.

---

## Self-Review Notes

- **Spec coverage:** Pase (Task 6 recalibration hooks), Conservar Balón (Task 5's threshold short-circuit), Recepción/Control (Task 6's two-stage `execute_pass`), Conducción (Tasks 2-3-4-6-8) are all covered. All 5 Criterios de Éxito have a locatable automated test or, for Criterio 5, a mandatory manual step (Task 10). The plan's mandatory closing "Lecciones Aprendidas" section is captured in Task 10 Step 8, not left implicit.
- **Explicitly out of scope, confirmed absent from every task:** second team/portería/gol/árbitro, collective/tactical layers, rival-as-a-system modeling, cross-match learning, personality influencing anything beyond the pre-existing Selección tie-break, ECS/DI framework, large-scale optimization.
- **Type/interface consistency check:** `EvaluatedAlternative.alternative` now holds either a `PassAlternative` or a `ConduccionAlternative` — every consumer that needs to distinguish them (`vf/cognitive_cycle.py`'s `intention_type` assignment, `vf/simulation.py::_describe_alternative`) uses `isinstance(..., PassAlternative)`, consistently, nowhere relying on duck-typing a field that only one of the two types has.
- **Known simplification carried through, not hidden:** conducción direction choice is discretized to 8 fixed compass headings per step (not a continuous search); one conducción "step" = one full cognitive-cycle re-evaluation, not raw per-tick physics; `CONSERVAR_THRESHOLD`, `MAX_LOOP_REPEATS`, `MAX_CONDUCCION_STREAK`, `MAX_CYCLES_PER_POSSESSION`, `PLAYER_SPEED`, `CONDUCCION_STEP_DISTANCE` are all invented constants explicitly flagged for the Task 10 recalibration pass and for `docs/decisions.md`. A goalkeeper, off-the-ball teammate movement, and fatigue/condición física (all called out by the Simulation Bible as factors but explicitly listed as "pendientes" not yet formalized even in the Bible itself) remain out of scope.
