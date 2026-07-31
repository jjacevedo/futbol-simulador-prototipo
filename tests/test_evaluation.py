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
