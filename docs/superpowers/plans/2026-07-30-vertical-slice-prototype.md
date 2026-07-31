# Prototipo Vertical-Slice (Pase + Ciclo Cognitivo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest executable vertical slice of the football simulator — 2-4 AI-controlled players, one ball, one technical action (the Pass) — that exercises the full cognitive cycle (Knowledge → Perception → Memory → Understanding → Goals → Alternatives → Evaluation (real Utility AI) → Selection) end to end, per `docs/../Plan_Prototipo_Tecnico` (source: `VF/Plan_Prototipo_Tecnico.docx`).

**Architecture:** Plain Python, no ECS/DI framework (explicitly deferred by the plan). One module per cognitive/simulation system, each independently unit-tested, wired together by `cognitive_cycle.py` (decision) and `match_engine.py` (physical execution). Simulated time is decoupled from wall-clock time (`SIM_DT` per tick, accelerated mode) — matches AI Bible Vol XXIX's Tiempo Real vs Tiempo Simulado distinction. Determinism via a single seeded `random.Random` threaded through every stochastic call (AI Bible Vol III, Determinismo Controlado).

**Tech Stack:** Python 3.11+, `pytest`, `matplotlib` (2D schematic visualization only, no game engine), stdlib `dataclasses`/`math`/`random`/`json`.

## Global Constraints

- Scope is frozen to `Plan_Prototipo_Tecnico`: 2-4 players, single Pass action, no offside/fouls/referee, no rendering beyond schematic 2D, no ECS/messaging framework, no multi-match statistical optimization.
- Every numeric formula/constant invented here (the Data Bible volumes in scope give no equations) must live in one clearly named module-level constant block and be referenced from `docs/decisions.md` — never buried inline.
- Four structural decisions already confirmed with the user (do not re-litigate):
  1. `Posicionamiento` attribute = average of `posicionamiento_ofensivo` and `posicionamiento_defensivo`.
  2. Pass success probability = sigmoid(skill − dificultad), reusing the AI Bible's own curve vocabulary.
  3. Physics = constant velocity, no acceleration/friction, for both ball flight and player movement.
  4. Personality = single scalar `creatividad` (0..1) trait, used only to break near-ties in Selección (Determinismo Controlado).
- Attribute scale: 0-100 (not specified by the Data Bible; documented assumption in `docs/decisions.md`).
- Field: reduced pitch, `FIELD_LENGTH=40.0m` × `FIELD_WIDTH=25.0m`, attack direction `+x`.
- Every module must expose plain functions/dataclasses — no hidden global state, so each is unit-testable in isolation per the user's explicit "aislado, y solo entonces se integra" instruction.
- Every pass decision must be fully loggable (which alternatives, which scores, which weights, why one was chosen) — AI Bible Vol III Observability requirement, and required for Criterio de Éxito 5 (human behavioral review).
- Small, descriptive commits per task. No single giant commit.

---

## Task 0: Project Scaffolding + Git Init

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `vf/__init__.py`
- Create: `tests/__init__.py`
- Create: `README.md`
- Create: `docs/decisions.md`

**Interfaces:**
- Produces: importable `vf` package, `pytest` runnable from repo root.

- [ ] **Step 1: Init git repo**

```bash
git init
```

- [ ] **Step 2: Create package skeleton**

`vf/__init__.py`:
```python
"""Vertical-slice football simulation prototype."""
```

`tests/__init__.py`: empty file.

- [ ] **Step 3: Create `requirements.txt`**

```
pytest>=8.0
matplotlib>=3.8
```

- [ ] **Step 4: Create `pyproject.toml`**

```toml
[project]
name = "vf-prototype"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
.venv/
*.jsonl
*.png
*.gif
```

- [ ] **Step 6: Create `docs/decisions.md`**

```markdown
# Decisiones de Implementación No Especificadas en las Biblias

Registro de todo valor/formula inventado porque el documento fuente no lo
especifica. Cada entrada: qué se decidió, por qué, dónde vive en el código.

## Estructurales (confirmadas con el usuario antes de escribir código)

1. **Posicionamiento**: Data Bible Vol VI solo define Posicionamiento
   Ofensivo y Defensivo por separado. Se usa el promedio de ambos.
   (`vf/entities.py::Attributes.posicionamiento_promedio`)
2. **Fórmula de éxito de pase**: Data Bible Vol VII no da fórmula. Se usa
   una sigmoide sobre (habilidad − dificultad), reutilizando el lenguaje
   matemático de curvas de la AI Bible Vol XII.
   (`vf/probabilistic_engine.py::compute_pass_success_probability`)
3. **Física 2D**: Data Bible Vol VIII no da ecuaciones. Velocidad
   constante, sin fricción ni aceleración, para balón y jugadores.
   (`vf/physics.py`)
4. **Personalidad**: AI Bible Vol XVII (Sistema de Personalidad) está
   fuera de alcance. Stand-in mínimo: un rasgo escalar `creatividad`
   (0..1) por jugador, usado solo para desempatar en Selección.
   (`vf/entities.py::Personality`, `vf/selection.py`)

## De implementación (decididas sin bloquear al usuario, por ser
calibración esperada según "Riesgos Conocidos" del Plan de Prototipo)

- Escala de atributos: 0-100 (no especificada por la Data Bible).
- Campo reducido: 40m × 25m, ataque en dirección +x.
- `SIM_DT = 0.1s`: duración de tiempo simulado por tick, desacoplada del
  tiempo real de ejecución (modo acelerado, AI Bible Vol XXIX).
- Constantes de las curvas de respuesta (`PRESSURE_X0`, `PRESSURE_K`,
  `PROB_K`, `MAX_PASS_DISTANCE`, pesos de Evaluación) — ver
  `vf/probabilistic_engine.py` y `vf/evaluation.py`. El propio Plan de
  Prototipo anticipa que estos valores necesitarán iteración
  ("Riesgos Conocidos", punto 1).
- Percepción: sin modelado de oclusión (solo distancia + campo visual
  angular). Data Bible Vol VII lista oclusión como factor, pero el
  Criterio de Éxito 1 del Plan solo exige distancia/ángulo correctos.
- "Pase al espacio" (Simulation Bible Vol XII, Cap. 88.3) no se
  implementa — todo pase apunta a la posición actual del receptor
  ("pase al jugador"). Se difiere al siguiente prototipo.
- Intercepción/desvío (Simulation Bible Cap. 91) no se modela: un pase
  fallido deja el balón suelto (`loose`) en el punto de destino. El
  Control y Recepción completo (Vol XIII) queda fuera de alcance.
```

- [ ] **Step 7: Create minimal `README.md`**

```markdown
# VF — Prototipo Vertical-Slice

Prototipo ejecutable del ciclo cognitivo completo (Percepción → Comprensión
→ Objetivos → Alternativas → Evaluación → Selección) aplicado a una única
acción técnica: el Pase. Alcance y exclusiones: ver
`docs/superpowers/plans/2026-07-30-vertical-slice-prototype.md`.

## Setup

\`\`\`bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
\`\`\`
```

- [ ] **Step 8: Verify pytest runs (no tests yet, should report 0 collected)**

Run: `python3 -m pytest`
Expected: `no tests ran` or `collected 0 items`, exit code 0 or 5 (no error).

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml requirements.txt .gitignore vf/__init__.py tests/__init__.py README.md docs/decisions.md docs/superpowers/
git commit -m "chore: scaffold project, record open design decisions"
```

---

## Task 1: Entities & Core Data Model

**Files:**
- Create: `vf/entities.py`
- Test: `tests/test_entities.py`

**Interfaces:**
- Produces: `Attributes`, `Personality`, `Player`, `Ball`, `MatchState`, `FIELD_LENGTH`, `FIELD_WIDTH` — used by every later module.

- [ ] **Step 1: Write failing test**

`tests/test_entities.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_entities.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.entities'`

- [ ] **Step 3: Write implementation**

`vf/entities.py`:
```python
from dataclasses import dataclass, field
from typing import Optional, Tuple

FIELD_LENGTH = 40.0
FIELD_WIDTH = 25.0


@dataclass
class Attributes:
    pase_corto: float
    vision: float
    decision: float
    posicionamiento_ofensivo: float
    posicionamiento_defensivo: float

    @property
    def posicionamiento_promedio(self) -> float:
        return (self.posicionamiento_ofensivo + self.posicionamiento_defensivo) / 2.0


@dataclass
class Personality:
    creatividad: float = 0.5  # 0..1, stand-in for AI Bible Vol XVII (fuera de alcance)


@dataclass
class Player:
    id: str
    team: str
    position: Tuple[float, float]
    attributes: Attributes
    personality: Personality = field(default_factory=Personality)
    facing_rad: float = 0.0
    fov_angle_deg: float = 100.0
    fov_distance_m: float = 25.0
    has_ball: bool = False


@dataclass
class Ball:
    position: Tuple[float, float]
    owner_id: Optional[str] = None
    state: str = "controlled"  # controlled | in_flight | loose
    target_position: Optional[Tuple[float, float]] = None
    target_player_id: Optional[str] = None
    ticks_total: int = 0
    ticks_remaining: int = 0


@dataclass
class MatchState:
    players: list
    ball: Ball
    tick: int = 0
    seed: int = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_entities.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/entities.py tests/test_entities.py
git commit -m "feat: core entities (Player, Ball, MatchState, Attributes)"
```

---

## Task 2: Persistencia (Save/Load)

**Files:**
- Create: `vf/persistence.py`
- Test: `tests/test_persistence.py`

**Interfaces:**
- Consumes: `vf.entities.{Attributes, Personality, Player, Ball, MatchState}`
- Produces: `save_state(state: MatchState, path: str) -> None`, `load_state(path: str) -> MatchState`

- [ ] **Step 1: Write failing test**

`tests/test_persistence.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_persistence.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.persistence'`

- [ ] **Step 3: Write implementation**

`vf/persistence.py`:
```python
import json
from dataclasses import asdict
from typing import Any, Dict

from vf.entities import Attributes, Ball, MatchState, Personality, Player


def _tuple_positions_to_list(obj: Any) -> Any:
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _tuple_positions_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_tuple_positions_to_list(v) for v in obj]
    return obj


def save_state(state: MatchState, path: str) -> None:
    raw = asdict(state)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_tuple_positions_to_list(raw), f, indent=2)


def _player_from_dict(d: Dict[str, Any]) -> Player:
    attrs = Attributes(**d["attributes"])
    personality = Personality(**d["personality"])
    return Player(
        id=d["id"],
        team=d["team"],
        position=tuple(d["position"]),
        attributes=attrs,
        personality=personality,
        facing_rad=d["facing_rad"],
        fov_angle_deg=d["fov_angle_deg"],
        fov_distance_m=d["fov_distance_m"],
        has_ball=d["has_ball"],
    )


def _ball_from_dict(d: Dict[str, Any]) -> Ball:
    return Ball(
        position=tuple(d["position"]),
        owner_id=d["owner_id"],
        state=d["state"],
        target_position=tuple(d["target_position"]) if d["target_position"] else None,
        target_player_id=d["target_player_id"],
        ticks_total=d["ticks_total"],
        ticks_remaining=d["ticks_remaining"],
    )


def load_state(path: str) -> MatchState:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    players = [_player_from_dict(p) for p in raw["players"]]
    ball = _ball_from_dict(raw["ball"])
    return MatchState(players=players, ball=ball, tick=raw["tick"], seed=raw["seed"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_persistence.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add vf/persistence.py tests/test_persistence.py
git commit -m "feat: minimal JSON persistence (save/load MatchState round trip)"
```

---

## Task 3: Percepción (Field of View)

Implements AI Bible Vol VII. Directly targets **Criterio de Éxito 1**.

**Files:**
- Create: `vf/perception.py`
- Test: `tests/test_perception.py`

**Interfaces:**
- Consumes: `vf.entities.{Player, MatchState}`
- Produces: `PerceivedEntity(id, team, position, distance)`, `perceive(observer: Player, state: MatchState) -> list[PerceivedEntity]`

- [ ] **Step 1: Write failing test**

`tests/test_perception.py`:
```python
import math

from vf.entities import Attributes, Ball, MatchState, Player
from vf.perception import perceive


def _attrs():
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def _make_state(observer: Player, others: list) -> MatchState:
    return MatchState(players=[observer, *others], ball=Ball(position=(0.0, 0.0)))


def test_teammate_ahead_within_range_is_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0)  # facing +x
    teammate = Player(id="p2", team="A", position=(10.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert len(result) == 1
    assert result[0].id == "p2"
    assert math.isclose(result[0].distance, 10.0)


def test_teammate_behind_observer_is_not_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0)  # facing +x, FOV 100 deg => +-50 deg
    teammate = Player(id="p2", team="A", position=(-10.0, 0.0), attributes=_attrs())  # directly behind
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert result == []


def test_teammate_beyond_fov_distance_is_not_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(),
                       facing_rad=0.0, fov_distance_m=25.0)
    teammate = Player(id="p2", team="A", position=(30.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [teammate])

    result = perceive(observer, state)

    assert result == []


def test_rival_within_fov_is_also_perceived():
    observer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), facing_rad=0.0)
    rival = Player(id="r1", team="B", position=(5.0, 0.0), attributes=_attrs())
    state = _make_state(observer, [rival])

    result = perceive(observer, state)

    assert len(result) == 1
    assert result[0].team == "B"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_perception.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.perception'`

- [ ] **Step 3: Write implementation**

`vf/perception.py`:
```python
import math
from dataclasses import dataclass
from typing import List, Tuple

from vf.entities import MatchState, Player


@dataclass
class PerceivedEntity:
    id: str
    team: str
    position: Tuple[float, float]
    distance: float


def _angle_to(observer_pos: Tuple[float, float], target_pos: Tuple[float, float]) -> float:
    dx = target_pos[0] - observer_pos[0]
    dy = target_pos[1] - observer_pos[1]
    return math.atan2(dy, dx)


def _angular_difference(a: float, b: float) -> float:
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return diff


def is_visible(observer: Player, target_position: Tuple[float, float]) -> bool:
    dx = target_position[0] - observer.position[0]
    dy = target_position[1] - observer.position[1]
    distance = math.hypot(dx, dy)
    if distance > observer.fov_distance_m:
        return False
    if distance == 0.0:
        return True
    angle_to_target = _angle_to(observer.position, target_position)
    diff = abs(_angular_difference(angle_to_target, observer.facing_rad))
    half_fov = math.radians(observer.fov_angle_deg) / 2.0
    return diff <= half_fov


def perceive(observer: Player, state: MatchState) -> List[PerceivedEntity]:
    perceived = []
    for other in state.players:
        if other.id == observer.id:
            continue
        if is_visible(observer, other.position):
            dx = other.position[0] - observer.position[0]
            dy = other.position[1] - observer.position[1]
            distance = math.hypot(dx, dy)
            perceived.append(PerceivedEntity(id=other.id, team=other.team,
                                              position=other.position, distance=distance))
    return perceived
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_perception.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/perception.py tests/test_perception.py
git commit -m "feat: perception system (FOV angle + distance) — Criterio de Exito 1"
```

---

## Task 4: Comprensión del Contexto

Implements AI Bible Vol IX, restricted to what Evaluación needs: pressure on each perceived teammate from the nearest perceived rival.

**Files:**
- Create: `vf/understanding.py`
- Test: `tests/test_understanding.py`

**Interfaces:**
- Consumes: `vf.perception.PerceivedEntity`, `vf.entities.Player`
- Produces: `ContextualState(nearest_rival_distance: dict[str, float | None])`, `build_context(observer: Player, perceived: list[PerceivedEntity]) -> ContextualState`

- [ ] **Step 1: Write failing test**

`tests/test_understanding.py`:
```python
import math

from vf.entities import Attributes, Player
from vf.perception import PerceivedEntity
from vf.understanding import build_context


def _observer():
    attrs = Attributes(pase_corto=50, vision=50, decision=50,
                        posicionamiento_ofensivo=50, posicionamiento_defensivo=50)
    return Player(id="p1", team="A", position=(0.0, 0.0), attributes=attrs)


def test_nearest_rival_distance_computed_per_teammate():
    perceived = [
        PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0),
        PerceivedEntity(id="r1", team="B", position=(11.0, 0.0), distance=11.0),
        PerceivedEntity(id="r2", team="B", position=(12.0, 0.0), distance=12.0),
    ]

    context = build_context(_observer(), perceived)

    assert math.isclose(context.nearest_rival_distance["p2"], 1.0)


def test_teammate_with_no_perceived_rival_gets_none():
    perceived = [PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0)]

    context = build_context(_observer(), perceived)

    assert context.nearest_rival_distance["p2"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_understanding.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.understanding'`

- [ ] **Step 3: Write implementation**

`vf/understanding.py`:
```python
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from vf.entities import Player
from vf.perception import PerceivedEntity


@dataclass
class ContextualState:
    nearest_rival_distance: Dict[str, Optional[float]] = field(default_factory=dict)


def build_context(observer: Player, perceived: List[PerceivedEntity]) -> ContextualState:
    teammates = [e for e in perceived if e.team == observer.team]
    rivals = [e for e in perceived if e.team != observer.team]

    nearest: Dict[str, Optional[float]] = {}
    for mate in teammates:
        if not rivals:
            nearest[mate.id] = None
            continue
        distances = [
            math.hypot(mate.position[0] - r.position[0], mate.position[1] - r.position[1])
            for r in rivals
        ]
        nearest[mate.id] = min(distances)

    return ContextualState(nearest_rival_distance=nearest)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_understanding.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/understanding.py tests/test_understanding.py
git commit -m "feat: understanding system (rival pressure on perceived teammates)"
```

---

## Task 5: Objetivos

Implements AI Bible Vol X, minimal: ball carrier generates a single `PASAR_BALON` goal.

**Files:**
- Create: `vf/goals.py`
- Test: `tests/test_goals.py`

**Interfaces:**
- Consumes: `vf.entities.{Player, MatchState}`
- Produces: `Goal(type: str, priority: float)`, `generate_goals(observer: Player, state: MatchState) -> list[Goal]`

- [ ] **Step 1: Write failing test**

`tests/test_goals.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_goals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.goals'`

- [ ] **Step 3: Write implementation**

`vf/goals.py`:
```python
from dataclasses import dataclass
from typing import List

from vf.entities import MatchState, Player


@dataclass
class Goal:
    type: str
    priority: float


def generate_goals(observer: Player, state: MatchState) -> List[Goal]:
    if observer.has_ball:
        return [Goal(type="PASAR_BALON", priority=1.0)]
    return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_goals.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/goals.py tests/test_goals.py
git commit -m "feat: goals system (minimal PASAR_BALON operational goal)"
```

---

## Task 6: Generación de Alternativas

Implements AI Bible Vol XI, restricted to Pass alternatives.

**Files:**
- Create: `vf/alternatives.py`
- Test: `tests/test_alternatives.py`

**Interfaces:**
- Consumes: `vf.entities.Player`, `vf.perception.PerceivedEntity`, `vf.goals.Goal`
- Produces: `PassAlternative(target_player_id, target_position, distance)`, `generate_pass_alternatives(observer, perceived, goals) -> list[PassAlternative]`

- [ ] **Step 1: Write failing test**

`tests/test_alternatives.py`:
```python
import math

from vf.alternatives import generate_pass_alternatives
from vf.entities import Attributes, Player
from vf.goals import Goal
from vf.perception import PerceivedEntity


def _attrs():
    return Attributes(pase_corto=50, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def _observer():
    return Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs())


def test_generates_one_alternative_per_visible_teammate():
    perceived = [
        PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0),
        PerceivedEntity(id="p3", team="A", position=(0.0, 8.0), distance=8.0),
        PerceivedEntity(id="r1", team="B", position=(5.0, 0.0), distance=5.0),
    ]
    goals = [Goal(type="PASAR_BALON", priority=1.0)]

    alts = generate_pass_alternatives(_observer(), perceived, goals)

    assert {a.target_player_id for a in alts} == {"p2", "p3"}
    p2_alt = next(a for a in alts if a.target_player_id == "p2")
    assert math.isclose(p2_alt.distance, 10.0)


def test_no_alternatives_without_pasar_balon_goal():
    perceived = [PerceivedEntity(id="p2", team="A", position=(10.0, 0.0), distance=10.0)]

    alts = generate_pass_alternatives(_observer(), perceived, goals=[])

    assert alts == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_alternatives.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.alternatives'`

- [ ] **Step 3: Write implementation**

`vf/alternatives.py`:
```python
import math
from dataclasses import dataclass
from typing import List, Tuple

from vf.entities import Player
from vf.goals import Goal
from vf.perception import PerceivedEntity


@dataclass
class PassAlternative:
    target_player_id: str
    target_position: Tuple[float, float]
    distance: float


def generate_pass_alternatives(
    observer: Player, perceived: List[PerceivedEntity], goals: List[Goal]
) -> List[PassAlternative]:
    if not any(g.type == "PASAR_BALON" for g in goals):
        return []

    alternatives = []
    for entity in perceived:
        if entity.team != observer.team:
            continue
        distance = math.hypot(
            entity.position[0] - observer.position[0],
            entity.position[1] - observer.position[1],
        )
        alternatives.append(
            PassAlternative(target_player_id=entity.id, target_position=entity.position,
                             distance=distance)
        )
    return alternatives
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_alternatives.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/alternatives.py tests/test_alternatives.py
git commit -m "feat: alternative generation (pass-to-teammate candidates)"
```

---

## Task 7: Motor Probabilístico

Implements Data Bible Vol VII (formula invented and confirmed with user — decision #2). Directly targets **Criterio de Éxito 4**.

**Files:**
- Create: `vf/probabilistic_engine.py`
- Test: `tests/test_probabilistic_engine.py`

**Interfaces:**
- Consumes: `vf.entities.Attributes`
- Produces: `score_linear`, `score_sigmoid`, `compute_pass_success_probability(passer_attrs, distance_m, rival_distance_to_receiver) -> float`, `resolve_pass(rng, probability) -> bool`

- [ ] **Step 1: Write failing test**

`tests/test_probabilistic_engine.py`:
```python
import random

from vf.entities import Attributes
from vf.probabilistic_engine import compute_pass_success_probability, resolve_pass


def _attrs(pase_corto):
    return Attributes(pase_corto=pase_corto, vision=50, decision=50,
                       posicionamiento_ofensivo=50, posicionamiento_defensivo=50)


def test_higher_pase_corto_yields_higher_probability():
    weak = compute_pass_success_probability(_attrs(30), distance_m=10.0, rival_distance_to_receiver=None)
    strong = compute_pass_success_probability(_attrs(90), distance_m=10.0, rival_distance_to_receiver=None)
    assert strong > weak


def test_longer_distance_lowers_probability():
    near = compute_pass_success_probability(_attrs(70), distance_m=5.0, rival_distance_to_receiver=None)
    far = compute_pass_success_probability(_attrs(70), distance_m=25.0, rival_distance_to_receiver=None)
    assert near > far


def test_nearby_rival_lowers_probability():
    unmarked = compute_pass_success_probability(_attrs(70), distance_m=10.0, rival_distance_to_receiver=15.0)
    marked = compute_pass_success_probability(_attrs(70), distance_m=10.0, rival_distance_to_receiver=1.0)
    assert unmarked > marked


def test_resolve_pass_respects_probability_statistically():
    rng = random.Random(42)
    successes = sum(1 for _ in range(2000) if resolve_pass(rng, 0.7))
    rate = successes / 2000
    assert 0.65 <= rate <= 0.75


def test_better_pase_corto_fails_less_on_average_criterio_4():
    weak_attrs = _attrs(30)
    strong_attrs = _attrs(90)
    n = 1000

    weak_prob = compute_pass_success_probability(weak_attrs, distance_m=12.0, rival_distance_to_receiver=6.0)
    strong_prob = compute_pass_success_probability(strong_attrs, distance_m=12.0, rival_distance_to_receiver=6.0)

    rng_weak = random.Random(7)
    rng_strong = random.Random(7)
    weak_successes = sum(1 for _ in range(n) if resolve_pass(rng_weak, weak_prob))
    strong_successes = sum(1 for _ in range(n) if resolve_pass(rng_strong, strong_prob))

    assert strong_successes > weak_successes
    # neither is guaranteed: both must show some failures over n trials
    assert weak_successes < n
    assert strong_successes < n
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_probabilistic_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.probabilistic_engine'`

- [ ] **Step 3: Write implementation**

`vf/probabilistic_engine.py`:
```python
import math
import random
from typing import Optional

from vf.entities import Attributes

# Calibration constants — invented (Data Bible Vol VII gives no formula).
# See docs/decisions.md. Expected to need iteration per the Plan's own
# "Riesgos Conocidos" section.
MAX_PASS_DISTANCE = 30.0
PRESSURE_X0 = 3.0
PRESSURE_K = 1.5
PROB_X0 = 0.0
PROB_K = 6.0


def score_linear(x: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def score_sigmoid(x: float, x0: float, k: float) -> float:
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def compute_pass_success_probability(
    passer_attrs: Attributes, distance_m: float, rival_distance_to_receiver: Optional[float]
) -> float:
    skill = (
        passer_attrs.pase_corto
        + passer_attrs.vision
        + passer_attrs.decision
        + passer_attrs.posicionamiento_promedio
    ) / 400.0  # each attribute 0..100, four attributes -> 0..1

    distance_score = score_linear(distance_m, 0.0, MAX_PASS_DISTANCE)

    if rival_distance_to_receiver is None:
        pressure_score = 0.0
    else:
        pressure_score = 1.0 - score_sigmoid(rival_distance_to_receiver, PRESSURE_X0, PRESSURE_K)

    net_advantage = skill - 0.5 * distance_score - 0.5 * pressure_score
    return score_sigmoid(net_advantage, PROB_X0, PROB_K)


def resolve_pass(rng: random.Random, probability: float) -> bool:
    return rng.random() < probability
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_probabilistic_engine.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/probabilistic_engine.py tests/test_probabilistic_engine.py
git commit -m "feat: probabilistic engine (pass success formula) — Criterio de Exito 4"
```

---

## Task 8: Evaluación (Utility AI)

Implements AI Bible Vol XII literally: response curves + additive-weighted + multiplicative combination + normalization. Directly targets **Criterio de Éxito 2**.

**Files:**
- Create: `vf/evaluation.py`
- Test: `tests/test_evaluation.py`

**Interfaces:**
- Consumes: `vf.entities.Player`, `vf.alternatives.PassAlternative`, `vf.understanding.ContextualState`, `vf.probabilistic_engine.{score_linear, score_sigmoid, compute_pass_success_probability, PRESSURE_X0, PRESSURE_K}`
- Produces: `EvaluatedAlternative(alternative, score_beneficio, score_seguridad, score_prob_exito, utility_raw, utility_normalized)`, `evaluate_alternatives(passer, alternatives, context) -> list[EvaluatedAlternative]`

- [ ] **Step 1: Write failing test**

`tests/test_evaluation.py`:
```python
from vf.alternatives import PassAlternative
from vf.entities import Attributes, Player
from vf.evaluation import evaluate_alternatives
from vf.understanding import ContextualState


def _passer():
    attrs = Attributes(pase_corto=70, vision=65, decision=60,
                        posicionamiento_ofensivo=60, posicionamiento_defensivo=50)
    return Player(id="p1", team="A", position=(0.0, 0.0), attributes=attrs)


def test_three_alternatives_get_distinct_explicable_utilities():
    alts = [
        PassAlternative(target_player_id="near_forward", target_position=(8.0, 0.0), distance=8.0),
        PassAlternative(target_player_id="far_forward", target_position=(18.0, 0.0), distance=18.0),
        PassAlternative(target_player_id="backward", target_position=(-5.0, 0.0), distance=5.0),
    ]
    context = ContextualState(nearest_rival_distance={
        "near_forward": None, "far_forward": None, "backward": None,
    })

    evaluated = evaluate_alternatives(_passer(), alts, context)

    utilities = {e.alternative.target_player_id: e.utility_raw for e in evaluated}
    assert len(set(round(u, 6) for u in utilities.values())) == 3  # all distinct
    # forward progress should beat an equal-distance backward pass
    assert utilities["near_forward"] > utilities["backward"]


def test_nearby_rival_on_receiver_lowers_utility_criterio_2():
    alt = PassAlternative(target_player_id="p2", target_position=(10.0, 0.0), distance=10.0)

    context_no_rival = ContextualState(nearest_rival_distance={"p2": None})
    context_with_rival = ContextualState(nearest_rival_distance={"p2": 1.0})

    eval_no_rival = evaluate_alternatives(_passer(), [alt], context_no_rival)[0]
    eval_with_rival = evaluate_alternatives(_passer(), [alt], context_with_rival)[0]

    assert eval_with_rival.utility_raw < eval_no_rival.utility_raw


def test_utility_normalized_spans_zero_to_one_across_set():
    alts = [
        PassAlternative(target_player_id="best", target_position=(15.0, 0.0), distance=15.0),
        PassAlternative(target_player_id="worst", target_position=(-10.0, 0.0), distance=10.0),
    ]
    context = ContextualState(nearest_rival_distance={"best": None, "worst": 1.0})

    evaluated = evaluate_alternatives(_passer(), alts, context)
    normalized = {e.alternative.target_player_id: e.utility_normalized for e in evaluated}

    assert normalized["best"] == 1.0
    assert normalized["worst"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_evaluation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.evaluation'`

- [ ] **Step 3: Write implementation**

`vf/evaluation.py`:
```python
from dataclasses import dataclass
from typing import List

from vf.alternatives import PassAlternative
from vf.entities import Player
from vf.probabilistic_engine import (
    PRESSURE_K,
    PRESSURE_X0,
    compute_pass_success_probability,
    score_linear,
    score_sigmoid,
)
from vf.understanding import ContextualState

# Weights — invented (AI Bible Vol XII Cap. 128 requires them to be
# explicit configuration, never implicit in code). See docs/decisions.md.
W_BENEFICIO = 0.6
W_SEGURIDAD = 0.4
W_VIABILIDAD = 1.0  # exponent on the multiplicative probability factor

BENEFIT_MIN = -20.0
BENEFIT_MAX = 20.0


@dataclass
class EvaluatedAlternative:
    alternative: PassAlternative
    score_beneficio: float
    score_seguridad: float
    score_prob_exito: float
    utility_raw: float
    utility_normalized: float = 0.0


def _evaluate_single(passer: Player, alt: PassAlternative, context: ContextualState) -> EvaluatedAlternative:
    forward_gain = alt.target_position[0] - passer.position[0]
    score_beneficio = score_linear(forward_gain, BENEFIT_MIN, BENEFIT_MAX)  # Curva Lineal

    rival_distance = context.nearest_rival_distance.get(alt.target_player_id)
    if rival_distance is None:
        pressure = 0.0
    else:
        pressure = 1.0 - score_sigmoid(rival_distance, PRESSURE_X0, PRESSURE_K)  # Curva Sigmoide
    score_seguridad = 1.0 - pressure

    score_prob_exito = compute_pass_success_probability(
        passer.attributes, alt.distance, rival_distance
    )  # perceived viability estimate — same formula, agent-side inputs

    utility_raw = (
        W_BENEFICIO * score_beneficio + W_SEGURIDAD * score_seguridad
    ) * (score_prob_exito ** W_VIABILIDAD)

    return EvaluatedAlternative(
        alternative=alt,
        score_beneficio=score_beneficio,
        score_seguridad=score_seguridad,
        score_prob_exito=score_prob_exito,
        utility_raw=utility_raw,
    )


def evaluate_alternatives(
    passer: Player, alternatives: List[PassAlternative], context: ContextualState
) -> List[EvaluatedAlternative]:
    evaluated = [_evaluate_single(passer, alt, context) for alt in alternatives]
    if not evaluated:
        return evaluated

    utilities = [e.utility_raw for e in evaluated]
    u_min, u_max = min(utilities), max(utilities)
    span = u_max - u_min
    for e in evaluated:
        e.utility_normalized = 1.0 if span == 0.0 else (e.utility_raw - u_min) / span

    return evaluated
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_evaluation.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/evaluation.py tests/test_evaluation.py
git commit -m "feat: evaluation system, Utility AI with additive+multiplicative combination — Criterio de Exito 2"
```

---

## Task 9: Selección

Implements AI Bible Vol XIV: argmax with margin-based, personality-weighted, seeded tie-break. Directly targets **Criterio de Éxito 3**.

**Files:**
- Create: `vf/selection.py`
- Test: `tests/test_selection.py`

**Interfaces:**
- Consumes: `vf.evaluation.EvaluatedAlternative`
- Produces: `select_alternative(rng: random.Random, evaluated: list[EvaluatedAlternative], creatividad: float) -> EvaluatedAlternative | None`

- [ ] **Step 1: Write failing test**

`tests/test_selection.py`:
```python
import random

from vf.alternatives import PassAlternative
from vf.evaluation import EvaluatedAlternative
from vf.selection import select_alternative


def _evaluated(target_id, utility_normalized):
    alt = PassAlternative(target_player_id=target_id, target_position=(0.0, 0.0), distance=1.0)
    return EvaluatedAlternative(
        alternative=alt, score_beneficio=0.0, score_seguridad=0.0, score_prob_exito=0.0,
        utility_raw=utility_normalized, utility_normalized=utility_normalized,
    )


def test_picks_clear_best_when_no_other_is_close():
    evaluated = [_evaluated("best", 0.9), _evaluated("worst", 0.2)]

    chosen = select_alternative(random.Random(1), evaluated, creatividad=0.9)

    assert chosen.alternative.target_player_id == "best"


def test_same_seed_produces_same_choice_criterio_3():
    evaluated = [_evaluated("a", 0.80), _evaluated("b", 0.78), _evaluated("c", 0.30)]

    chosen_1 = select_alternative(random.Random(99), evaluated, creatividad=0.9)
    chosen_2 = select_alternative(random.Random(99), evaluated, creatividad=0.9)

    assert chosen_1.alternative.target_player_id == chosen_2.alternative.target_player_id


def test_zero_creativity_always_takes_the_best_even_with_close_tie():
    evaluated = [_evaluated("a", 0.80), _evaluated("b", 0.79)]

    for seed in range(20):
        chosen = select_alternative(random.Random(seed), evaluated, creatividad=0.0)
        assert chosen.alternative.target_player_id == "a"


def test_empty_alternatives_returns_none():
    assert select_alternative(random.Random(1), [], creatividad=0.5) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_selection.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.selection'`

- [ ] **Step 3: Write implementation**

`vf/selection.py`:
```python
import random
from typing import List, Optional

from vf.evaluation import EvaluatedAlternative

# Margin within which two alternatives are considered "close enough" for
# personality to influence the outcome (AI Bible Vol XIV Cap. 159,
# Determinismo Controlado). Invented value — see docs/decisions.md.
TIE_MARGIN = 0.05


def select_alternative(
    rng: random.Random, evaluated: List[EvaluatedAlternative], creatividad: float
) -> Optional[EvaluatedAlternative]:
    if not evaluated:
        return None

    ranked = sorted(evaluated, key=lambda e: e.utility_normalized, reverse=True)
    best = ranked[0]
    contenders = [e for e in ranked if best.utility_normalized - e.utility_normalized <= TIE_MARGIN]

    if len(contenders) == 1:
        return best

    weights = [1.0 if e is best else creatividad for e in contenders]
    total = sum(weights)
    if total == 0.0:
        return best

    r = rng.random() * total
    upto = 0.0
    for e, w in zip(contenders, weights):
        upto += w
        if r <= upto:
            return e
    return best
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_selection.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/selection.py tests/test_selection.py
git commit -m "feat: selection system, seeded margin tie-break — Criterio de Exito 3"
```

---

## Task 10: Física 2D

Implements Data Bible Vol VIII (constant-velocity model — decision #3).

**Files:**
- Create: `vf/physics.py`
- Test: `tests/test_physics.py`

**Interfaces:**
- Consumes: `vf.entities.{Ball, Player}`
- Produces: `SIM_DT`, `PASS_SPEED`, `start_pass(ball, passer, target_position, target_player_id) -> None`, `advance_ball(ball) -> bool`, `interpolate_position(start, target, ticks_total, ticks_remaining) -> tuple`

- [ ] **Step 1: Write failing test**

`tests/test_physics.py`:
```python
from vf.entities import Ball
from vf.physics import PASS_SPEED, advance_ball, interpolate_position, start_pass


def test_start_pass_sets_in_flight_state_and_tick_count():
    ball = Ball(position=(0.0, 0.0), owner_id="p1", state="controlled")

    start_pass(ball, passer_position=(0.0, 0.0), target_position=(12.0, 0.0), target_player_id="p2")

    assert ball.state == "in_flight"
    assert ball.owner_id is None
    assert ball.target_player_id == "p2"
    assert ball.ticks_total > 0
    assert ball.ticks_remaining == ball.ticks_total


def test_longer_distance_takes_more_ticks():
    short_ball = Ball(position=(0.0, 0.0))
    long_ball = Ball(position=(0.0, 0.0))

    start_pass(short_ball, passer_position=(0.0, 0.0), target_position=(5.0, 0.0), target_player_id="p2")
    start_pass(long_ball, passer_position=(0.0, 0.0), target_position=(25.0, 0.0), target_player_id="p2")

    assert long_ball.ticks_total > short_ball.ticks_total


def test_advance_ball_arrives_after_exact_tick_count():
    ball = Ball(position=(0.0, 0.0))
    start_pass(ball, passer_position=(0.0, 0.0), target_position=(6.0, 0.0), target_player_id="p2")
    total = ball.ticks_total

    arrived_flags = [advance_ball(ball) for _ in range(total)]

    assert arrived_flags[-1] is True
    assert arrived_flags[:-1] == [False] * (total - 1)
    assert ball.position == (6.0, 0.0)


def test_interpolate_position_halfway():
    pos = interpolate_position((0.0, 0.0), (10.0, 0.0), ticks_total=4, ticks_remaining=2)
    assert pos == (5.0, 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_physics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.physics'`

- [ ] **Step 3: Write implementation**

`vf/physics.py`:
```python
import math
from typing import Tuple

from vf.entities import Ball

# Invented — Data Bible Vol VIII gives no equations (decision #3:
# constant velocity, no acceleration/friction). See docs/decisions.md.
SIM_DT = 0.1  # seconds of simulated time per tick, decoupled from real time
PASS_SPEED = 12.0  # m/s


def start_pass(
    ball: Ball, passer_position: Tuple[float, float], target_position: Tuple[float, float],
    target_player_id: str,
) -> None:
    distance = math.hypot(
        target_position[0] - passer_position[0], target_position[1] - passer_position[1]
    )
    ticks = max(1, round((distance / PASS_SPEED) / SIM_DT))

    ball.position = passer_position
    ball.owner_id = None
    ball.state = "in_flight"
    ball.target_position = target_position
    ball.target_player_id = target_player_id
    ball.ticks_total = ticks
    ball.ticks_remaining = ticks


def advance_ball(ball: Ball) -> bool:
    if ball.state != "in_flight":
        return False

    ball.ticks_remaining -= 1
    if ball.ticks_remaining <= 0:
        ball.position = ball.target_position
        return True
    return False


def interpolate_position(
    start: Tuple[float, float], target: Tuple[float, float], ticks_total: int, ticks_remaining: int
) -> Tuple[float, float]:
    if ticks_total <= 0:
        return target
    progress = 1.0 - (ticks_remaining / ticks_total)
    x = start[0] + (target[0] - start[0]) * progress
    y = start[1] + (target[1] - start[1]) * progress
    return (x, y)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_physics.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add vf/physics.py tests/test_physics.py
git commit -m "feat: 2D physics, constant-velocity ball flight"
```

---

## Task 11: Match Engine

Implements Data Bible Vol XII generic cycle, specialized to executing one selected pass end to end (flight + real probabilistic resolution).

**Files:**
- Create: `vf/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Consumes: `vf.entities.MatchState`, `vf.evaluation.EvaluatedAlternative`, `vf.physics.{start_pass, advance_ball}`, `vf.probabilistic_engine.{compute_pass_success_probability, resolve_pass}`
- Produces: `execute_pass(state: MatchState, passer_id: str, chosen: EvaluatedAlternative, rng: random.Random) -> dict`

- [ ] **Step 1: Write failing test**

`tests/test_match_engine.py`:
```python
import random

from vf.alternatives import PassAlternative
from vf.entities import Attributes, Ball, MatchState, Player
from vf.evaluation import EvaluatedAlternative
from vf.match_engine import execute_pass


def _attrs(pase_corto=90):
    return Attributes(pase_corto=pase_corto, vision=90, decision=90,
                       posicionamiento_ofensivo=90, posicionamiento_defensivo=90)


def _state_with_two_players():
    passer = Player(id="p1", team="A", position=(0.0, 0.0), attributes=_attrs(), has_ball=True)
    receiver = Player(id="p2", team="A", position=(6.0, 0.0), attributes=_attrs())
    ball = Ball(position=(0.0, 0.0), owner_id="p1")
    return MatchState(players=[passer, receiver], ball=ball, tick=0, seed=1)


def _chosen_alt(target_id="p2", target_position=(6.0, 0.0)):
    alt = PassAlternative(target_player_id=target_id, target_position=target_position, distance=6.0)
    return EvaluatedAlternative(alternative=alt, score_beneficio=0.8, score_seguridad=0.9,
                                 score_prob_exito=0.9, utility_raw=0.85, utility_normalized=1.0)


def test_successful_pass_transfers_ball_ownership():
    state = _state_with_two_players()
    rng = random.Random(1)  # seed that yields a success against a very high probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    receiver = next(p for p in state.players if p.id == "p2")
    passer = next(p for p in state.players if p.id == "p1")
    assert log["success"] is True
    assert state.ball.state == "controlled"
    assert state.ball.owner_id == "p2"
    assert receiver.has_ball is True
    assert passer.has_ball is False


def test_failed_pass_leaves_ball_loose():
    state = _state_with_two_players()
    rng = random.Random(1)
    rng.random = lambda: 0.999  # force failure regardless of probability

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    assert log["success"] is False
    assert state.ball.state == "loose"
    assert state.ball.owner_id is None
    passer = next(p for p in state.players if p.id == "p1")
    assert passer.has_ball is False


def test_log_contains_decision_factors_for_observability():
    state = _state_with_two_players()
    rng = random.Random(1)

    log = execute_pass(state, passer_id="p1", chosen=_chosen_alt(), rng=rng)

    assert "passer_id" in log
    assert "target_player_id" in log
    assert "distance_m" in log
    assert "real_probability" in log
    assert "success" in log
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.match_engine'`

- [ ] **Step 3: Write implementation**

`vf/match_engine.py`:
```python
import math
import random
from typing import Dict

from vf.entities import MatchState
from vf.evaluation import EvaluatedAlternative
from vf.physics import advance_ball, start_pass
from vf.probabilistic_engine import compute_pass_success_probability, resolve_pass


def _nearest_real_rival_distance(state: MatchState, team: str, position) -> float | None:
    rivals = [p for p in state.players if p.team != team]
    if not rivals:
        return None
    return min(math.hypot(position[0] - r.position[0], position[1] - r.position[1]) for r in rivals)


def execute_pass(
    state: MatchState, passer_id: str, chosen: EvaluatedAlternative, rng: random.Random
) -> Dict:
    passer = next(p for p in state.players if p.id == passer_id)
    target = next(p for p in state.players if p.id == chosen.alternative.target_player_id)

    # 1. validation (Match Engine Cap. 101, step 3)
    if not passer.has_ball:
        raise ValueError(f"{passer_id} does not have the ball, cannot pass")
    if target.id == passer.id:
        raise ValueError("cannot pass to self")

    # 2-3. execution: ball flight (Fisica) until arrival
    start_pass(state.ball, passer.position, chosen.alternative.target_position, target.id)
    ticks_elapsed = 0
    while not advance_ball(state.ball):
        ticks_elapsed += 1
    ticks_elapsed += 1
    state.tick += ticks_elapsed

    # 4. resolution: real (ground-truth) probability, not the perceived estimate
    real_rival_distance = _nearest_real_rival_distance(state, target.team, target.position)
    real_probability = compute_pass_success_probability(
        passer.attributes, chosen.alternative.distance, real_rival_distance
    )
    success = resolve_pass(rng, real_probability)

    passer.has_ball = False
    if success:
        state.ball.state = "controlled"
        state.ball.owner_id = target.id
        target.has_ball = True
    else:
        state.ball.state = "loose"
        state.ball.owner_id = None

    return {
        "passer_id": passer.id,
        "target_player_id": target.id,
        "distance_m": chosen.alternative.distance,
        "score_beneficio": chosen.score_beneficio,
        "score_seguridad": chosen.score_seguridad,
        "score_prob_exito_percibida": chosen.score_prob_exito,
        "utility_normalized": chosen.utility_normalized,
        "real_probability": real_probability,
        "success": success,
        "ticks_elapsed": ticks_elapsed,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_match_engine.py -v`
Expected: PASS (3 tests)

Note: `test_successful_pass_transfers_ball_ownership` relies on seed 1 producing a `rng.random()` draw below the (high, ~0.9+) real probability given the strong attributes in `_attrs()`. If it flakes, replace `rng = random.Random(1)` with an explicit stub (`rng.random = lambda: 0.01`) exactly as done in the failure test — do this during Step 4 if the natural seed does not cooperate, and note the change here.

- [ ] **Step 5: Commit**

```bash
git add vf/match_engine.py tests/test_match_engine.py
git commit -m "feat: match engine, executes selected pass (flight + real resolution)"
```

---

## Task 12: Ciclo Cognitivo + Integration Test

Wires Tasks 3-9 into one call per the AI Bible Vol III unidirectional flow. This is the "Verificación de ciclo completo" the Plan's validation section requires, and it exercises **Criterios de Éxito 1, 2, 3 together**.

**Files:**
- Create: `vf/cognitive_cycle.py`
- Test: `tests/test_cognitive_cycle.py`

**Interfaces:**
- Consumes: every module from Tasks 3-9.
- Produces: `CognitiveCycleResult(perceived, context, goals, alternatives, evaluated, chosen)`, `run_cognitive_cycle(observer: Player, state: MatchState, rng: random.Random) -> CognitiveCycleResult | None`

- [ ] **Step 1: Write failing test**

`tests/test_cognitive_cycle.py`:
```python
import random

from vf.entities import Attributes, Ball, MatchState, Player
from vf.cognitive_cycle import run_cognitive_cycle


def _attrs(pase_corto=70):
    return Attributes(pase_corto=pase_corto, vision=65, decision=60,
                       posicionamiento_ofensivo=60, posicionamiento_defensivo=50)


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
    assert "p3" not in perceived_ids  # behind observer, outside 100 deg FOV


def test_full_cycle_produces_at_least_three_distinct_utilities_criterio_2():
    state = _four_player_scenario()
    passer = state.players[0]

    result = run_cognitive_cycle(passer, state, random.Random(state.seed))

    assert len(result.evaluated) >= 2  # p2 and p4 visible (p3 excluded by FOV)
    utility_by_target = {e.alternative.target_player_id: e.utility_raw for e in result.evaluated}
    # p4 is marked closely by a rival, p2 is unmarked -> lower utility for p4
    assert utility_by_target["p4"] < utility_by_target["p2"]


def test_full_cycle_selection_reproducible_under_same_seed_criterio_3():
    state_a = _four_player_scenario()
    state_b = _four_player_scenario()

    result_a = run_cognitive_cycle(state_a.players[0], state_a, random.Random(state_a.seed))
    result_b = run_cognitive_cycle(state_b.players[0], state_b, random.Random(state_b.seed))

    assert result_a.chosen.alternative.target_player_id == result_b.chosen.alternative.target_player_id


def test_non_ball_carrier_produces_no_cycle_result():
    state = _four_player_scenario()
    non_carrier = state.players[1]

    result = run_cognitive_cycle(non_carrier, state, random.Random(state.seed))

    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cognitive_cycle.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.cognitive_cycle'`

- [ ] **Step 3: Write implementation**

`vf/cognitive_cycle.py`:
```python
import random
from dataclasses import dataclass
from typing import List, Optional

from vf.alternatives import PassAlternative, generate_pass_alternatives
from vf.entities import MatchState, Player
from vf.evaluation import EvaluatedAlternative, evaluate_alternatives
from vf.goals import Goal, generate_goals
from vf.perception import PerceivedEntity, perceive
from vf.selection import select_alternative
from vf.understanding import ContextualState, build_context


@dataclass
class CognitiveCycleResult:
    perceived: List[PerceivedEntity]
    context: ContextualState
    goals: List[Goal]
    alternatives: List[PassAlternative]
    evaluated: List[EvaluatedAlternative]
    chosen: Optional[EvaluatedAlternative]


def run_cognitive_cycle(
    observer: Player, state: MatchState, rng: random.Random
) -> Optional[CognitiveCycleResult]:
    # Unidirectional flow (AI Bible Vol III Cap. 23):
    # Estado -> Percepcion -> Comprension -> Objetivos -> Alternativas -> Evaluacion -> Seleccion
    goals = generate_goals(observer, state)
    if not goals:
        return None  # LOD (Vol XXXII): only the ball carrier runs the full cycle in this prototype

    perceived = perceive(observer, state)
    context = build_context(observer, perceived)
    alternatives = generate_pass_alternatives(observer, perceived, goals)
    if not alternatives:
        return CognitiveCycleResult(perceived, context, goals, alternatives, [], None)

    evaluated = evaluate_alternatives(observer, alternatives, context)
    chosen = select_alternative(rng, evaluated, observer.personality.creatividad)

    return CognitiveCycleResult(perceived, context, goals, alternatives, evaluated, chosen)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cognitive_cycle.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Run the full suite to confirm no regressions**

Run: `python3 -m pytest -v`
Expected: all tests across every module PASS.

- [ ] **Step 6: Commit**

```bash
git add vf/cognitive_cycle.py tests/test_cognitive_cycle.py
git commit -m "feat: wire full cognitive cycle (Percepcion..Seleccion) — Criterios 1, 2, 3 integration"
```

---

## Task 13: Simulación End-to-End, Decision Log, Visualización 2D

Final integration: runs the cognitive cycle + match engine together over a scripted scenario, produces the ≥20-decision log required for **Criterio de Éxito 5** (human behavioral review), and a schematic 2D replay for visual sanity-checking (per the Plan's "Representación visual" decision).

**Files:**
- Create: `vf/simulation.py`
- Create: `vf/visualization.py`
- Create: `scripts/run_simulation.py`
- Create: `scripts/generate_review_log.py`
- Test: `tests/test_simulation.py`

**Interfaces:**
- Consumes: `vf.cognitive_cycle.run_cognitive_cycle`, `vf.match_engine.execute_pass`, `vf.entities.MatchState`
- Produces: `run_one_possession(state, rng) -> dict | None` (a full perceive→decide→execute round for the current ball carrier), `build_scenario(seed) -> MatchState`

- [ ] **Step 1: Write failing test**

`tests/test_simulation.py`:
```python
import random

from vf.simulation import build_scenario, run_one_possession


def test_build_scenario_has_one_ball_carrier():
    state = build_scenario(seed=1)
    carriers = [p for p in state.players if p.has_ball]
    assert len(carriers) == 1


def test_run_one_possession_returns_full_log_when_alternatives_exist():
    state = build_scenario(seed=1)
    rng = random.Random(state.seed)

    log = run_one_possession(state, rng)

    assert log is not None
    assert "passer_id" in log
    assert "target_player_id" in log
    assert "success" in log
    assert "utility_normalized" in log


def test_run_one_possession_is_reproducible_under_same_seed():
    state_a = build_scenario(seed=3)
    state_b = build_scenario(seed=3)

    log_a = run_one_possession(state_a, random.Random(state_a.seed))
    log_b = run_one_possession(state_b, random.Random(state_b.seed))

    assert log_a["target_player_id"] == log_b["target_player_id"]
    assert log_a["success"] == log_b["success"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_simulation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vf.simulation'`

- [ ] **Step 3: Write `vf/simulation.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_simulation.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write `vf/visualization.py` (no unit test — visual output, per the Plan's own Criterio de Éxito 5 needing human review, not automation)**

```python
from typing import List, Tuple

import matplotlib.pyplot as plt

from vf.entities import MatchState


def render_scenario(state: MatchState, title: str, out_path: str) -> None:
    """Schematic 2D snapshot: points for players/ball, no animation.
    Points-and-lines only, per the Plan's 'visualizacion 2D esquematica' decision."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(-2, 42)
    ax.set_ylim(-2, 27)
    ax.set_aspect("equal")
    ax.set_title(title)

    for p in state.players:
        color = "tab:blue" if p.team == "A" else "tab:red"
        marker = "o" if not p.has_ball else "*"
        size = 120 if p.has_ball else 80
        ax.scatter(*p.position, c=color, marker=marker, s=size, zorder=3)
        ax.annotate(p.id, p.position, textcoords="offset points", xytext=(4, 4), fontsize=8)

    ax.scatter(*state.ball.position, c="black", marker=".", s=40, zorder=4)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def render_pass_trajectory(
    start: Tuple[float, float], end: Tuple[float, float], out_path: str, title: str
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(-2, 42)
    ax.set_ylim(-2, 27)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.plot([start[0], end[0]], [start[1], end[1]], "k--", linewidth=1)
    ax.scatter(*start, c="tab:blue", s=100, zorder=3)
    ax.scatter(*end, c="tab:green", s=100, zorder=3)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
```

- [ ] **Step 6: Write `scripts/generate_review_log.py`** — produces the ≥20-decision log for Criterio de Éxito 5.

```python
"""Generates >=20 pass decisions for human behavioral review
(Plan de Prototipo Tecnico, Criterio de Exito 5 / Validacion Conductual,
AI Bible Vol XXXI Cap. 401). Run: python3 scripts/generate_review_log.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_one_possession  # noqa: E402

N_DECISIONS = 25
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "decisions_review_log.jsonl"


def main() -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for seed in range(N_DECISIONS):
            state = build_scenario(seed=seed)
            rng = random.Random(state.seed)
            log = run_one_possession(state, rng)
            if log is None:
                continue
            log["seed"] = seed
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    print(f"Wrote decision log to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Write `scripts/run_simulation.py`** — CLI to run one possession and render before/after snapshots.

```python
"""Runs a single possession end to end and renders before/after schematic
2D snapshots. Run: python3 scripts/run_simulation.py [seed]
"""
import copy
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vf.simulation import build_scenario, run_one_possession  # noqa: E402
from vf.visualization import render_scenario  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    state = build_scenario(seed=seed)
    render_scenario(state, title=f"Antes (seed={seed})", out_path="frame_before.png")

    rng = random.Random(state.seed)
    log = run_one_possession(state, rng)
    if log is None:
        print("No decision was made (no alternatives generated).")
        return

    render_scenario(state, title=f"Despues (seed={seed})", out_path="frame_after.png")
    print(log)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run full suite**

Run: `python3 -m pytest -v`
Expected: every test across all modules PASS.

- [ ] **Step 9: Commit**

```bash
git add vf/simulation.py vf/visualization.py scripts/ tests/test_simulation.py
git commit -m "feat: end-to-end simulation runner, 2D schematic visualization, review-log generator"
```

---

## Task 14: Verificación Final Contra los 5 Criterios de Éxito

Not a code task — a verification pass. Produces the evidence the user explicitly asked for ("no me digas funciona, muéstrame cómo lo comprobaste").

- [ ] **Step 1: Run the entire automated suite and capture output**

```bash
python3 -m pytest -v
```
Save the full pass/fail output — this is the evidence for Criterios 1-4 (each has a dedicated test named `..._criterio_N` in `tests/test_cognitive_cycle.py`, `tests/test_evaluation.py`, `tests/test_selection.py`, `tests/test_probabilistic_engine.py`).

- [ ] **Step 2: Generate the behavioral review log**

```bash
python3 scripts/generate_review_log.py
```
Produces `decisions_review_log.jsonl` with ≥20 entries (Criterio 5 needs "al menos veinte decisiones de pase registradas").

- [ ] **Step 3: Present the log to the user for human review**

Criterio 5 explicitly requires human judgment ("ningún test automatizado sustituye ese juicio", AI Bible Vol XXXI Cap. 401). Do not self-certify this criterion — show the user a readable summary (per-decision: passer attributes, alternatives considered, scores, chosen target, success/fail) and ask them to judge credibility.

- [ ] **Step 4: Render a handful of schematic snapshots for visual sanity check**

```bash
python3 scripts/run_simulation.py 1
python3 scripts/run_simulation.py 7
```
Send the resulting PNGs to the user.

- [ ] **Step 5: Write the final summary** covering: what was built, which decisions were made that weren't explicit in the plan (cross-reference `docs/decisions.md`), and any design gaps found translating the Bibles into code (cross-reference the three research reports already gathered — e.g. Data Bible's total absence of formulas/equations/persistence format, the implicit Vol XI dependency of Simulation Bible's Pase chapter, the Vol XVII personality gap).

---

## Self-Review Notes

- **Spec coverage:** all "Qué SÍ entra" items from the Plan are covered — Task 1 (2-4 players + ball), Tasks 3-9 (full cognitive cycle), Task 8 (real Utility AI, ≥2 curve families, additive+multiplicative), Task 2 (persistence). All five Criterios de Éxito have dedicated named tests (Tasks 7, 8, 9, 12) plus a final manual step (Task 14) for Criterio 5, which cannot be automated by design.
- **Explicitly out of scope, confirmed absent from every task:** Inteligencia Colectiva/Blackboard/Influence Maps, long-term learning, full football rules, real rendering, ECS/DI framework, multi-thousand-simulation scaling.
- **Type consistency check:** `EvaluatedAlternative` (Task 8) is consumed identically by `select_alternative` (Task 9), `execute_pass` (Task 11), and `run_cognitive_cycle`/`run_one_possession` (Tasks 12-13) — field names (`utility_normalized`, `score_beneficio`, `score_seguridad`, `score_prob_exito`, `alternative`) match everywhere they're used.
- **Known simplification carried through every task, not hidden:** interception/deflection outcomes (Simulation Bible Cap. 91) collapse to a binary success/loose-ball result; "pase al espacio" (Cap. 88.3) is not modeled — both are logged in `docs/decisions.md` and were flagged as deferred to the next prototype in the Plan itself (Control y Recepción / Vol XIII is explicitly the "next" system).
