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
