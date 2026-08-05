# Validación de la Iteración 3 — Actualización Perceptiva (facing_rad)

Verificación final contra los 5 Criterios de Éxito del
[Plan Técnico de Prototipo — Iteración 3](../VF/Plan_Tecnico_Iteracion_3.docx).
Suite automatizada: 93/93 tests. Comportamiento real: mismas 25 posesiones/
semillas de `build_scenario` que Iteración 2 (sin tocar), más escenarios de
presión dedicados construidos específicamente para medir Conservar.

## Hipótesis de la iteración

> "La actualización de facing_rad durante Conducción y en el momento de
> recepción de un pase, sin añadir acciones nuevas al espacio ya existente,
> produce comportamiento con variedad de acciones observable: Conservar
> dispara en presencia de presión real, Pase reaparece como opción tras la
> conducción, y los criterios 4A y 4B se cumplen sin depender de bugs de
> detección."

**Veredicto: rechazada.** El mecanismo está correctamente implementado
(unitariamente probado, con prueba de integración explícita de que la
percepción del ciclo siguiente refleja la nueva orientación) y produce
efectos reales — pero no los tres que la hipótesis exige simultáneamente, y
en el camino confirma un hallazgo estructural más profundo que la
actualización de `facing_rad` por sí sola no puede resolver.

## Resultado por criterio

**Criterio 1 — Conservar dispara en presencia de presión real**: ⚠️ el
mecanismo es correcto pero casi nunca se activa en condiciones realistas.
Con un escenario de 8 rivales rodeando completamente al portador y campo
visual ampliado a 360° (para que la presión esté *percibida*, no solo
presente), Conservar dispara correctamente (`utility_raw=0.0145 < 0.15`).
Pero con el campo visual real de 100° — incluso en el mismo escenario de
rodeo total — Conservar **nunca dispara**, porque el jugador siempre
encuentra una dirección de Conducción que en ese instante no tiene ningún
rival percibido (aunque en la realidad haya uno justo detrás, fuera de su
cono actual) y esa dirección anota utilidad alta. Sobre las 25 posesiones
estándar más los escenarios dedicados, Conservar disparó 0 veces bajo
condiciones perceptivas realistas.

**Criterio 2 — Pase representa ≥25% de las acciones cuando hay compañeros
percibidos**: ❌ falla con margen amplio. Medido: **12.8%** (14 de 109
ciclos) con Opción A, **14.9%** (14 de 94) con Opción B — ambas muy por
debajo del umbral. La actualización de `facing_rad` sí aumentó la
*visibilidad* de compañeros (de 9.7% de ciclos en Iteración 2 a ~19-22%
aquí), pero incluso cuando un compañero es visible, Conducción sigue
ganando la mayoría de las veces porque su curva de utilidad (pesos
congelados, tal como exige el Hallazgo 2 heredado) sigue anotando alto sin
presión visible.

**Criterio 3 — Ninguna posesión llega al tope por Conducción indefinida**:
❌ falla de forma sistemática. Con el detector corregido (Trabajo
Preparatorio), **25 de 25 posesiones** siguen terminando por una racha de
Conducción consecutiva que llega al tope de 20 ciclos — igual o peor que
las 24 de 25 de Iteración 2 (medidas con el detector viejo, que
subestimaba el problema).

**Criterio 4 — Explicabilidad preservada**: ✅ sostenido. El formato del
log no cambió de forma que oculte información — `alternatives_considered`,
`weights`, `near_tie` siguen presentes en cada ciclo, y ahora además
`facing_rad` es visible donde cambia. Ninguna decisión se volvió opaca.

**Criterio 5 — Sin nuevos comportamientos degenerados**: ❌ falla — y de
la forma que el propio plan anticipó como riesgo. El detector de
oscilación perceptiva (nuevo en esta iteración) encontró **10 de 25
posesiones** con giros de `facing_rad` de gran amplitud repetidos sin
motivo aparente — el jugador alterna entre direcciones de Conducción
casi-empatadas (resueltas por el desempate de `creatividad`), y como cada
alternancia ahora también gira la orientación, el resultado es un jugador
que literalmente da vueltas mirando para todos lados mientras conduce.
Esto es exactamente el riesgo #2 que el documento de Iteración 3 escribió
por adelantado. El sub-criterio de "jugador bloqueado sin poder actuar"
(`NINGUNA`) nunca ocurrió — 0/25 — pero se confirmó que es geométricamente
inalcanzable en un campo de 40×25m con pasos de conducción de 4m (hasta
las 4 esquinas exactas dejan 3 de 8 direcciones válidas), así que ese
resultado no es evidencia de robustez, es un artefacto del tamaño de
campo/paso.

## Comparación directa Opción A vs Opción B

Implementadas y medidas ambas, con toggle (`RECEPTION_FACING_MODE`), tal
como pide el Cap. 9 del plan:

| Métrica | Opción A (balón) | Opción B (ataque) |
|---|---|---|
| CONDUCCION / PASE / CONSERVAR | 486 / 14 / 0 | 486 / 14 / 0 |
| Ciclos con compañero visible | 109 | 94 |
| Pase entre esos ciclos | 12.8% | 14.9% |
| Posesiones que topan por racha (Criterio 3) | 25/25 | 25/25 |
| Posesiones con oscilación (Criterio 5) | 10/25 (semillas 1,3,4,8,11,16,17,20,21,23) | Idénticas |

La diferencia entre A y B es marginal y no cambia ningún veredicto. Se
mantiene A (`RECEPTION_FACING_MODE="BALL"`) como configuración por
defecto — es la opción físicamente más simple y ninguna evidencia
justifica el costo adicional de B. La oscilación (Criterio 5) es
*idéntica* entre A y B porque la causa es el mecanismo de Conducción
(Tarea 1), no el de recepción (Tareas 3/6) — la recepción solo ocurre en
14 de 500 ciclos, demasiado poco para mover el resultado agregado.

## Hallazgo raíz: por qué la actualización de facing_rad no basta

La Iteración 2 encontró que el campo visual estático colapsaba el espacio
de decisión. La Iteración 3 confirma que *actualizar* el campo visual no
es suficiente por una razón más sutil, verificada directamente:

**Las 8 alternativas de Conducción se evalúan usando la percepción
ACTUAL del jugador (antes de girar), no la percepción que tendría si
efectivamente girara hacia esa dirección.** Esto significa que una
dirección hacia donde hay un rival, pero que ese rival cae fuera del cono
visual actual, se evalúa como "segura" (presión = 0) porque el rival
simplemente no aparece en la lista de percibidos usada para puntuar esa
alternativa. Verificado con un escenario de 8 rivales rodeando
completamente al jugador: con FOV realista de 100°, siempre hay una
dirección "hacia donde no estoy mirando ahora" que anota utilidad alta,
sin importar cuántos rivales haya en las direcciones que sí se perciben.
Solo con FOV de 360° (viendo todo simultáneamente) el sistema correctamente
reconoce que está rodeado y dispara Conservar.

Esto explica en cascada los tres fallos:
- **Criterio 1** falla porque siempre hay una dirección "invisible" que
  parece segura.
- **Criterio 2** falla porque, aun viendo más compañeros que antes, la
  Conducción hacia una dirección sin rival percibido sigue anotando más
  alto que el Pase (pesos congelados, tal como exige el diseño
  experimental).
- **Criterio 5** falla porque, al no haber una dirección claramente mejor
  cuando el entorno percibido cambia poco de un ciclo a otro, el
  desempate por creatividad alterna libremente entre direcciones
  casi-empatadas — y ahora cada alternancia gira físicamente al jugador.

## Sección Obligatoria: Lecciones Aprendidas

Conforme al Cap. 9 del Plan Técnico de Iteración 3.

**Opción A vs Opción B**: ambas implementadas y medidas (tabla arriba). La
diferencia es marginal (12.8% vs 14.9% en Criterio 2, idénticas en
Criterios 3 y 5). Se conserva A como configuración por defecto por
simplicidad física, sin evidencia que respalde el costo de mantener B.

**Umbral de racha de Conducción (Criterio 3)**: se mantuvo
`MAX_CONDUCCION_STREAK=6` sin recalibrar (pesos y umbrales congelados por
restricción de diseño heredada del Hallazgo 2). La evidencia muestra que
el umbral no es el problema — con cualquier valor razonable, 25/25
posesiones llegan al tope de ciclos por una razón previa a cualquier
umbral de "cuántos ciclos son demasiados": el jugador nunca deja de
conducir porque nunca encuentra una razón (percibida) para parar.

**Resultado del Criterio 2**: no se cumplió ni de cerca — 12.8-14.9%
contra un umbral de 25%. No fue un "fallo al filo": la brecha es de casi
la mitad del valor requerido.

**Degeneración no anticipada en el capítulo de Riesgos**: ninguna más
allá de la oscilación perceptiva, que el propio documento ya anticipó
como riesgo #2 y que el Criterio 5 fue diseñado específicamente para
capturar — funcionó como se esperaba.

**Distribución de acciones comparada con Iteración 2** (471 Conducción /
14 Pase / 0 Conservar sobre 485 ciclos): Iteración 3 produjo 486 / 14 / 0
sobre 500 ciclos — **prácticamente sin cambio**. La actualización de
`facing_rad` aumentó la visibilidad de compañeros (de ~9.7% a ~20% de los
ciclos) pero esa mejora perceptiva no se tradujo en un cambio de
comportamiento observable, porque el mecanismo de evaluación de
Conducción (evaluar todas las direcciones con la percepción actual, sin
simular el giro) sigue encontrando una salida "segura" con la misma
frecuencia que antes.

## Próximo paso sugerido (Iteración 4)

El hallazgo central de esta iteración es más específico que "la
percepción es estática" (eso ya se resolvió parcialmente) — es que
**la evaluación de alternativas de Conducción no considera el cambio de
percepción que cada alternativa produciría**. Dos rutas posibles, a
decidir con datos, no por elegancia:

1. Evaluar cada dirección de Conducción con la percepción que *tendría*
   el jugador si girara hacia ella (requiere recalcular percepción por
   cada una de las 8 alternativas, no solo una vez por ciclo — coste
   computacional mayor pero conceptualmente directo).
2. Ampliar el campo visual efectivo para la evaluación de Conducción
   específicamente (no para la Percepción general), reconociendo que un
   jugador real integra información periférica y memoria reciente al
   decidir hacia dónde girar, no solo lo que ve en ese instante exacto —
   esto tocaría el Sistema de Memoria (Volumen VIII de la AI Bible),
   explícitamente fuera de alcance hasta ahora.

Cualquiera de las dos rompe la regla de "una sola variable" que esta
iteración y la anterior mantuvieron deliberadamente — por eso se propone
como Iteración 4 y no como parche de esta.
