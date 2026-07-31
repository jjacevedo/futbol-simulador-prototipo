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
