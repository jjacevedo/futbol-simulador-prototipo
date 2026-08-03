from vf.alternatives import ConduccionAlternative, PassAlternative
from vf.entities import Attributes, Player
from vf.evaluation import evaluate_alternatives, evaluate_conduccion_alternatives, normalize_utilities
from vf.perception import PerceivedEntity
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
