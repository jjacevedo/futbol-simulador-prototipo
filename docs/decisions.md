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
  fallido deja el balón suelto (`loose`) en el punto de destino. El
  Control y Recepción completo (Vol XIII) queda fuera de alcance.
