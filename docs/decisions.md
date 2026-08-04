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
- Campo reducido: 40m × 25m (`FIELD_LENGTH`, `FIELD_WIDTH`), ataque en
  dirección +x. (`vf/entities.py`)
- `SIM_DT = 0.1s`: duración de tiempo simulado por tick, desacoplada del
  tiempo real de ejecución (modo acelerado, AI Bible Vol XXIX).
  (`vf/physics.py`)
- `PASS_SPEED = 12.0 m/s`: velocidad constante asumida para el balón en
  vuelo (ver decisión estructural #3, física 2D sin aceleración/fricción).
  (`vf/physics.py`)
- Constantes de las curvas de respuesta del Motor Probabilístico
  (`vf/probabilistic_engine.py`) — el propio Plan de Prototipo anticipa
  que estos valores necesitarán iteración ("Riesgos Conocidos", punto 1):
  - `MAX_PASS_DISTANCE = 30.0`: distancia más allá de la cual un pase se
    considera máximamente difícil (curva lineal de distancia).
  - `PRESSURE_X0 = 3.0`, `PRESSURE_K = 1.5`: punto medio y pendiente de
    la sigmoide de presión (distancia del rival más cercano al receptor).
  - `PROB_X0 = 0.0`, `PROB_K = 6.0`: punto medio y pendiente de la
    sigmoide final que convierte "ventaja neta" (habilidad − dificultad)
    en probabilidad de éxito.
  - `SKILL_DIVISOR = 400.0`: normaliza la suma de 4 atributos (0-100 cada
    uno) a una escala 0..1.
  - `DISTANCE_WEIGHT = 0.5`, `PRESSURE_WEIGHT = 0.5`: pesos de distancia
    y presión al restar dificultad de la habilidad normalizada.
- Pesos y rango de Evaluación (Utility AI) — ver `vf/evaluation.py`:
  - `W_BENEFICIO = 0.6`, `W_SEGURIDAD = 0.4`: pesos aditivos de beneficio
    (avance) y seguridad (falta de presión) en `utility_raw`.
  - `W_VIABILIDAD = 1.0`: exponente multiplicativo de la probabilidad de
    éxito percibida sobre `utility_raw`.
  - `BENEFIT_MIN = -20.0`, `BENEFIT_MAX = 20.0`: rango de avance hacia
    adelante (metros) usado por la curva lineal de `score_beneficio`.
- `TIE_MARGIN = 0.05`: margen de utilidad (sobre `utility_raw`) dentro
  del cual dos alternativas se consideran "casi empatadas" y la
  personalidad (`creatividad`) puede desempatar en Selección (ver
  decisión estructural #4). Valor inventado (AI Bible Vol XIV Cap. 159,
  Determinismo Controlado). (`vf/selection.py`)
- FOV por defecto de cada jugador: `fov_angle_deg = 100.0`,
  `fov_distance_m = 25.0` (no especificado por la Data Bible; valores de
  calibración razonables para un campo de 40m × 25m). (`vf/entities.py::Player`)
- Percepción: sin modelado de oclusión (solo distancia + campo visual
  angular). Data Bible Vol VII lista oclusión como factor, pero el
  Criterio de Éxito 1 del Plan solo exige distancia/ángulo correctos.
- "Pase al espacio" (Simulation Bible Vol XII, Cap. 88.3) no se
  implementa — todo pase apunta a la posición actual del receptor
  ("pase al jugador"). Se difiere al siguiente prototipo.
- Intercepción/desvío (Simulation Bible Cap. 91) no se modela: un pase
  fallido deja el balón suelto (`loose`) en el punto de destino.
  (Nota: Control y Recepción fueron fuera de alcance en Iteración 1 pero
  Iteración 2 los trae en alcance — ver fórmulas de Control/Conducción abajo.)
- **Fórmulas de Control/Recepción y Conducción** (Iteración 2): Data Bible
  Vol XIII no especifica fórmulas para Control de Balón, Primer Toque, o
  Conducción más allá de los nombres. Se usan sigmoide sobre (habilidad −
  presión), reutilizando el patrón de `compute_pass_success_probability`.
  (`vf/probabilistic_engine.py`):
  - `CONTROL_SKILL_DIVISOR = 200.0`: normaliza la suma de dos atributos
    (control_balon + primer_toque, cada 0..100) a una escala 0..1.
  - `CONTROL_PROB_K = 6.0`: pendiente de la sigmoide final que convierte
    "ventaja neta" (habilidad − presión) en probabilidad de control exitoso.
  - `CONDUCCION_SKILL_DIVISOR = 100.0`: normaliza el atributo conduccion
    (0..100) a una escala 0..1.
  - `CONDUCCION_PROB_K = 6.0`: pendiente de la sigmoide final que convierte
    "ventaja neta" (habilidad − presión) en probabilidad de mantener la
    conducción.

## Iteración 2

Constantes y decisiones de Iteración 2 (Conservar Balón, Recepción/Control,
Conducción) que quedaron fuera del registro anterior. Las fórmulas de
Control/Recepción y Conducción del Motor Probabilístico ya están
documentadas arriba, en la sección "De implementación" de Iteración 1.

### Estructurales (confirmadas con el usuario antes de escribir código)

5. **Discretización de la Conducción en 8 direcciones evaluadas vía Utility
   AI**: ninguna Biblia da un mecanismo para elegir la dirección de
   conducción. El usuario confirmó evaluar múltiples direcciones candidatas
   (8, en los ejes cardinales e intercardinales relativos al eje de ataque,
   +x = 0°) a través de Utility AI, en vez de aplicar un único vector
   heurístico. (`vf/alternatives.py::CONDUCCION_DIRECTIONS_DEG`,
   `generate_conduccion_alternatives`)
6. **Recuperación de balón suelto por el jugador más cercano**: ninguna
   Biblia especifica un algoritmo de recuperación de balón suelto. El
   usuario confirmó la regla simple "recupera el jugador más cercano a la
   posición del balón". (`vf/match_engine.py::recover_loose_ball`)
   Nota (fix de la revisión final de Iteración 2): se añadió
   `LOOSE_BALL_DRIFT` (ver más abajo) para desplazar el balón una distancia
   fija desde el punto de pérdida antes de invocar esta función, de modo
   que la recuperación sea genuinamente disputada en vez de resolver
   trivialmente siempre al mismo jugador que acaba de perder el balón. Esto
   no revierte la decisión del usuario — la regla de "jugador más cercano"
   es la misma; lo que cambia es el punto desde el que se mide la cercanía.
7. **Promedio de atributos de control**: Data Bible Vol XIII no da fórmula
   para combinar Control de Balón y Primer Toque. El usuario confirmó
   promediar ambos atributos, reutilizando el mismo patrón que la decisión
   estructural #1 (`posicionamiento_promedio`).
   (`vf/entities.py::Attributes.control_promedio`)

### De implementación (decididas sin bloquear al usuario, calibración
esperada)

- `PLAYER_SPEED = 5.0 m/s`: velocidad constante asumida para jugadores en
  conducción (ver decisión estructural #3, física 2D sin
  aceleración/fricción). (`vf/physics.py`)
- `CONDUCCION_STEP_DISTANCE = 4.0 m`: distancia cubierta por un "paso" de
  conducción. Un paso equivale a una oportunidad de reevaluación (un ciclo
  cognitivo), siguiendo la granularidad "contacto a contacto" de la
  Simulation Bible (Cap. 103.3/103.6), no física por-tick cruda.
  (`vf/physics.py`)
- `CONDUCCION_TICKS_PER_STEP`: derivado de `CONDUCCION_STEP_DISTANCE /
  PLAYER_SPEED / SIM_DT`, redondeado a al menos 1 tick (con los valores por
  defecto, 8 ticks). (`vf/physics.py`)
- `CONDUCCION_DIRECTIONS_DEG = [0, 45, -45, 90, -90, 135, -135, 180]`: los 8
  ángulos candidatos relativos al eje de ataque usados para generar
  alternativas de conducción (ver decisión estructural #5).
  (`vf/alternatives.py`)
- `CONSERVAR_THRESHOLD = 0.15`: umbral de utilidad (`utility_raw`) por
  debajo del cual Selección convierte la mejor alternativa disponible en
  intención CONSERVAR en vez de actuar sobre ella (Iteración 2 Cap. 52 —
  "el umbral... es un parámetro nuevo... su valor inicial será
  provisional"). Valor inventado, se anticipa recalibración.
  (`vf/cognitive_cycle.py`)
- `CONSERVAR_TICKS = 1`: avance mínimo de tiempo simulado para un ciclo
  CONSERVAR (no hay movimiento físico que temporizar). Invented.
  (`vf/match_engine.py`)
- `MAX_LOOP_REPEATS = 4`: número máximo de repeticiones consecutivas de la
  misma acción + objetivo/dirección por el mismo actor antes de
  considerarse un bucle degenerado (Criterio 4A). Deliberadamente no fijado
  a priori por el plan de Iteración 2 ("no se fija a priori... para evitar
  convertir un valor provisional en una decisión arquitectónica antes de
  disponer de datos"). (`vf/degeneracy.py`)
- `MAX_CONDUCCION_STREAK = 6`: número máximo de pasos de conducción
  consecutivos del mismo jugador sin cambiar de intención antes de
  considerarse degenerado (Criterio 4B). Mismo criterio de no fijación a
  priori que `MAX_LOOP_REPEATS`. (`vf/degeneracy.py`)
- `MAX_CYCLES_PER_POSSESSION = 20`: tope de seguridad sobre el número de
  ciclos cognitivos encadenados dentro de una misma posesión
  (`run_possession`), para garantizar terminación aunque ningún otro
  mecanismo (cambio de posesión, CONSERVAR, NINGUNA) detenga el bucle.
  Invented. (`vf/simulation.py`)
- `LOOSE_BALL_DRIFT = 2.0 m` (añadida en el fix de la revisión final de
  Iteración 2, recuperación disputada de balón suelto): distancia que se
  desplaza el balón desde el punto de pérdida antes de llamar a
  `recover_loose_ball`. Sin este desplazamiento el balón queda exactamente
  en la posición del jugador que acaba de tocarlo (distancia 0), por lo que
  "jugador más cercano" resuelve trivialmente siempre al mismo jugador que
  falló la acción — un fallo de control quedaba idéntico en estado a un
  éxito salvo por un booleano en el log, vaciando de efecto real al
  Criterio 3. Ver decisión estructural #6. (`vf/match_engine.py`)
