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
