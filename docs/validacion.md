# Validación del Prototipo Vertical-Slice

Verificación final contra los 5 Criterios de Éxito del
[Plan de Prototipo Técnico](superpowers/plans/2026-07-30-vertical-slice-prototype.md).
Suite automatizada: 45/45 tests (`python3 -m pytest -v`). Log conductual:
`decisions_review_log.jsonl`, 25 decisiones, revisadas por el usuario.

## Resultado por criterio

1. **Percepción por campo visual** — validado por tests (`tests/test_perception.py`, `tests/test_cognitive_cycle.py`).
2. **Utilidades distintas y coherentes con contexto** — validado por tests + inspección del log (`score_seguridad` baja cuando hay rival cerca del receptor, visible en `alternatives_considered`).
3. **Selección determinista con variabilidad por personalidad** — validado por tests (`tests/test_selection.py`, `tests/test_cognitive_cycle.py`, marca `near_tie`/`runner_up_target_id` en el log).
4. **Motor Probabilístico coherente con atributos** — validado por tests (`tests/test_probabilistic_engine.py::...criterio_4`).
5. **Credibilidad — revisión humana** — 25/25 decisiones consideradas creíbles por el usuario, dentro del alcance del prototipo.

## Hallazgo de la revisión conductual (Criterio 5)

En los casos 10, 13, 15, 18, 21 y 22 del log, el jugador pasa a un
compañero con `score_seguridad` bajo (0.09–0.30 aprox.) — un rival
encima o muy cerca del receptor. Un futbolista real en esa situación
probablemente conservaría el balón, buscaría mejor apoyo, o retrocedería.

El prototipo no puede hacer eso: **la única acción implementada es el
Pase**. No hay "conducir", "proteger el balón" ni "esperar". La decisión
tomada es la única disponible — sigue siendo creíble dado el alcance,
pero confirma que "solo pasar" es insuficiente para producir
comportamiento genuinamente futbolístico.

Esto no es un defecto del prototipo: es exactamente el tipo de
descubrimiento que el Plan de Prototipo Técnico anticipaba en su
sección "Qué Sigue Después de Este Prototipo" — ampliar del Pase al
bloque completo de acciones técnicas (Control, Conducción, Regate,
Disparo, Defensa) es el paso siguiente natural, no un cambio de rumbo.

## Próximo paso sugerido

Añadir, en orden de menor a mayor esfuerzo:

1. Una decisión de "conservar balón" cuando ninguna alternativa de pase
   supera cierto umbral de utilidad (extiende Generación de Alternativas
   + Evaluación, sin nueva acción técnica).
2. Control/Recepción (Simulation Bible Vol XIII) para resolver qué pasa
   cuando el pase llega — hoy el prototipo colapsa eso a
   éxito/balón-suelto.
3. Conducción como segunda acción técnica real.

Cada expansión debería producir su propio documento corto de alcance
(qué entra, qué queda fuera, qué es éxito), tal como pide el Plan.

## Veredicto

**El prototipo vertical-slice está validado.** Cumple los 5 criterios
de éxito definidos en el Plan de Prototipo Técnico.
