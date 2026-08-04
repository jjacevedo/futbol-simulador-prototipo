# Validación de la Iteración 2 — Conservar Balón, Recepción y Conducción

Verificación final contra los 5 Criterios de Éxito del
[Plan Técnico de Prototipo — Iteración 2](../VF/Plan_Tecnico_Iteracion_2.docx).
Suite automatizada: 75/75 tests (`python3 -m pytest -v`). Comportamiento real:
25 posesiones simuladas (`decisions_review_log.jsonl`), ~500 ciclos cognitivos.

## Hipótesis de la iteración

> "La incorporación de Conservar Balón, Recepción/Control y Conducción,
> junto al Pase ya existente, permite la aparición de un comportamiento
> futbolístico reconocible, sin introducir comportamientos degenerados."

**Veredicto: rechazada parcialmente.** Los mecanismos individuales (Conservar,
Recepción/Control, Conducción) están correctamente implementados y
verificados en aislamiento — cada uno hace exactamente lo que su
especificación exige, con tests que lo prueban. Pero al ejecutarlos juntos
en secuencias de varios ciclos, el sistema cae sistemáticamente en un
patrón degenerado: **conducción indefinida en línea casi recta, sin
oposición, hasta el tope de seguridad**. La causa no es un error de
calibración — es una limitación estructural que el propio Plan Técnico de
Iteración 2 ya anticipaba (Hallazgo 3) y decidió explícitamente no resolver
en esta iteración.

## Resultado por criterio

**Criterio 1 — Conservación motivada**: ❌ no observado en comportamiento real.
El mecanismo está bien implementado y unitariamente probado
(`tests/test_cognitive_cycle.py::test_full_cycle_conserves_when_all_alternatives_below_threshold_criterio_1`,
`tests/test_simulation.py::test_conservar_scenario_produces_conservar_intention`) —
cuando se fuerza un escenario con 8 rivales rodeando al jugador, Conservar
dispara correctamente. Pero en las 25 posesiones reales generadas por
`build_scenario`, **Conservar nunca disparó ni una sola vez** (0 de ~500
ciclos). Causa: con rival(es) casi siempre fuera del campo visual tras el
primer pase (ver más abajo), la presión percibida es 0, y ninguna
alternativa de Conducción cae nunca por debajo de `CONSERVAR_THRESHOLD=0.15`.

**Criterio 2 — Conducción con propósito**: ⚠️ parcialmente soportado.
Conducción nunca es una "acción por defecto sin cálculo" en sentido
literal — cada dirección se evalúa con la misma matemática de Utility AI
que el Pase, con puntuaciones y pesos auditables en el log. Pero en la
práctica, Conducción gana casi siempre no porque supere a una alternativa
de Pase real y disponible, sino porque **las alternativas de Pase
desaparecen** (ver Hallazgo 3 abajo) dejando a Conducción como única opción
evaluable. Intento de recalibración documentado abajo.

**Criterio 3 — Recepción realista**: ✅ soportado, con matiz.
La resolución en dos etapas (precisión del pase, luego control del
receptor) está implementada y probada
(`tests/test_match_engine.py`), y ahora que el balón suelto realmente se
dispersa (Fix 1 del review final), el turnover es mecánicamente posible —
se observó en 1 de 25 posesiones (seed 2). El mecanismo es correcto; su
**frecuencia** en escenarios reales es baja porque los fallos de control
también dependen de presión percibida, que rara vez existe dado el
Hallazgo 3.

**Criterio 4A — Sin bucles de acción repetida**: ❌ el detector implementado
no captura el patrón dominante. `detect_action_loop` compara la dirección
exacta de Conducción ciclo a ciclo; como el desempate por
`creatividad`/`TIE_MARGIN` hace que direcciones casi-empatadas (p. ej. 0° y
45°) se alternen, el detector marca `loop_detected=True` en solo 5 de 25
posesiones aunque **24 de 25 alcanzan el tope de 20 ciclos con rachas de
Conducción de 18-20 pasos consecutivos**. Esto es exactamente el tipo de
insuficiencia que el Plan anticipaba ("Los criterios 4A y 4B podrían
mostrarse insuficientes para capturar todos los tipos de degeneración
observables") — confirmado empíricamente, no hipotético.

**Criterio 4B — Sin conducción indefinida**: ❌ falla de forma sistemática,
no puntual. `MAX_CONDUCCION_STREAK=6` se supera en 24 de 25 posesiones
(rachas observadas: 18-20). Verificado a mano (seed 6): un jugador conduce
en línea casi recta desde `(11.8, 18.4)` hasta `(38.6, 21.3)` — es decir,
cruza más de la mitad del campo — sin que ningún rival relevante entre
nunca en su campo visual.

**Criterio 5 — Explicabilidad**: ✅ soportado. Cada decisión en el log
incluye `alternatives_considered` (con las 8 direcciones de Conducción y
las alternativas de Pase, si las hay), `weights`, `near_tie` y
`runner_up_utility_raw` cuando aplica. La mecánica de decisión es
completamente auditable — el problema no es que las decisiones sean
opacas, es que casi todas las decisiones disponibles para auditar son del
mismo tipo.

## Hallazgo raíz: por qué Conducción domina (y por qué no es un problema de calibración)

Rastreado directamente en el código y verificado con `build_scenario(seed=1)`:

1. Todos los jugadores tienen `facing_rad=0.0` fijo — nunca se actualiza,
   ni al recibir el balón ni al conducir.
2. Tras el primer pase exitoso, el nuevo portador del balón típicamente
   queda con sus compañeros **detrás** de él en el eje de ataque (+x). Con
   un campo visual de 100°, esos compañeros caen fuera del cono de
   percepción.
3. `generate_pass_alternatives` depende de percibir compañeros — con cero
   compañeros percibidos, devuelve `[]`. **El 91% de los ~500 ciclos
   simulados no tuvo ninguna alternativa de Pase que evaluar.**
4. Sin rival percibido tampoco (mismo problema de campo visual, ahora
   aplicado al rival), cada dirección de Conducción anota una utilidad casi
   idéntica y consistentemente alta (`seguridad=1.0`, `prob_exito` alto) —
   un punto fijo que ninguna alternativa de Pase real (porque no existen)
   puede superar.

### Intento de recalibración (obligatorio según Hallazgo 2 del Plan)

Se intentó desacoplar el rango de la curva de beneficio de Conducción
(`BENEFIT_MIN/MAX=-20/20`, calibrado para pases de 10-20m) de un rango
propio escalado a `CONDUCCION_STEP_DISTANCE=4.0m`. Resultado medido: la
dominancia de Conducción **empeoró** (CONDUCCION 471→499 decisiones, PASE
14→1, sobre las mismas 25 semillas) — un paso hacia adelante ahora anota
utilidad aún más alta (1.0 en vez de 0.6), haciendo la Conducción todavía
más atractiva. El cambio se revirtió; el código actual conserva la curva
compartida. Este resultado confirma empíricamente lo que el análisis
estructural ya sugería: **ningún ajuste de pesos o umbrales dentro de esta
iteración resuelve el problema**, porque la causa no está en la función de
utilidad — está en que las alternativas de Pase dejan de generarse.

Esto es exactamente el **Hallazgo 3** que el propio Plan Técnico de
Iteración 2 escribió por adelantado: *"Al incorporar Conducción, el jugador
comenzará a desplazarse, y con él su orientación y su campo de visión...
Esta limitación no se resolverá en esta iteración... Se registrará como
parte del sistema tal como está, y sus efectos concretos serán observados y
documentados como posible input para la iteración siguiente."* Eso es
precisamente lo que este documento hace.

## Lo que sí se corrigió en esta iteración (no calibración, bugs reales)

El review final de todo el branch encontró y corrigió, antes de este
documento, tres problemas estructurales que habrían invalidado cualquier
medición:

1. El balón suelto siempre "se recuperaba" a distancia 0 por el mismo
   jugador que acababa de perderlo — ningún fallo tenía consecuencia real.
   Corregido con deriva del balón antes de ofrecer la recuperación.
2. La Conducción no respetaba los límites de la cancha — jugadores
   terminaban a 90m en un campo de 40m. Corregido descartando direcciones
   fuera de límites y con un clamp de seguridad.
3. `run_possession` no distinguía cambio de equipo — ahora termina
   correctamente la posesión cuando el balón cambia de dueño entre equipos.

Sin estos tres arreglos, los números de este documento (0 Conservar, 1
turnover en 25 posesiones, rachas de 18-20) habrían sido aún peores y
además ocultos por un mecanismo de recuperación que hacía que ningún fallo
importara.

## Sección Obligatoria: Lecciones Aprendidas

Conforme al Cap. 8 del Plan Técnico de Iteración 2.

**Limitaciones descubiertas en la arquitectura actual:**
- El campo visual estático (`facing_rad` nunca se actualiza) es la causa
  raíz única de casi toda la degeneración observada. No es un defecto de
  implementación — es una limitación explícitamente anticipada y diferida
  por el propio Plan (Hallazgo 3).
- El Sistema de Selección puede producir Conservar correctamente en
  aislamiento, pero su umbral (`CONSERVAR_THRESHOLD`) está diseñado para
  responder a *presión percibida alta*, no a *ausencia de alternativas de
  Pase*. Son dos condiciones distintas que el diseño actual no distingue.

**Comportamientos emergentes no esperados:**
- Ningún comportamiento "extraño" por sí solo — cada decisión individual es
  localmente explicable (Criterio 5 se sostiene). Lo inesperado es la
  *ausencia total* de variedad en la secuencia completa.

**Insuficiencias en los propios criterios de éxito:**
- Criterio 4A (`detect_action_loop`) no captura rachas de Conducción que
  alternan entre direcciones casi-empatadas — confirmado, no hipotético.
  Un detector futuro debería agrupar por tipo de acción + actor
  consecutivos, no por parámetro exacto (esto ya lo hace `max_conduccion_streak`
  para Conducción específicamente, y por eso 4B sí detecta el patrón
  correctamente donde 4A no).

**Dependencias entre módulos que se hicieron visibles al implementar:**
- Percepción (Volumen VII) y Conducción (Volumen XIV) están más
  acopladas de lo que el Plan asumía: cualquier sistema de acción sostenida
  que mueva al jugador necesita, como mínimo, una orientación (`facing_rad`)
  que seguimiento del movimiento — no puede seguir siendo un campo estático
  fijado una vez en `build_scenario`.

**Parámetros cuya calibración resultó más delicada de lo previsto:**
- `CONSERVAR_THRESHOLD`: no existe un valor único que separe "conservar
  quirúrgicamente cuando hay presión real" de "conservar siempre" o
  "nunca conservar", porque el umbral no puede distinguir las dos causas
  de utilidad baja (presión real vs. ausencia de información).
- El rango de la curva de beneficio de Conducción demostró ser
  contraintuitivo: la corrección "teóricamente correcta" (escalar al
  tamaño del paso) empeoró el comportamiento observado.

## Próximo paso sugerido (Iteración 3)

Directo del propio Hallazgo 3 del Plan: antes de añadir más acciones
técnicas, esta arquitectura necesita que los jugadors actualicen su
`facing_rad` — mínimamente, hacia la dirección de desplazamiento durante
Conducción, y hacia el balón o el compañero relevante al recibir. Sin eso,
cualquier acción adicional sufrirá el mismo colapso hacia "la única opción
que el jugador puede ver".
