import random

from vf.alternatives import PassAlternative
from vf.evaluation import EvaluatedAlternative
from vf.selection import select_alternative


def _evaluated(target_id, utility_normalized):
    alt = PassAlternative(target_player_id=target_id, target_position=(0.0, 0.0), distance=1.0)
    return EvaluatedAlternative(
        alternative=alt, score_beneficio=0.0, score_seguridad=0.0, score_prob_exito=0.0,
        utility_raw=utility_normalized, utility_normalized=utility_normalized,
    )


def test_picks_clear_best_when_no_other_is_close():
    evaluated = [_evaluated("best", 0.9), _evaluated("worst", 0.2)]

    chosen = select_alternative(random.Random(1), evaluated, creatividad=0.9)

    assert chosen.alternative.target_player_id == "best"


def test_same_seed_produces_same_choice_criterio_3():
    evaluated = [_evaluated("a", 0.80), _evaluated("b", 0.78), _evaluated("c", 0.30)]

    chosen_1 = select_alternative(random.Random(99), evaluated, creatividad=0.9)
    chosen_2 = select_alternative(random.Random(99), evaluated, creatividad=0.9)

    assert chosen_1.alternative.target_player_id == chosen_2.alternative.target_player_id


def test_zero_creativity_always_takes_the_best_even_with_close_tie():
    evaluated = [_evaluated("a", 0.80), _evaluated("b", 0.79)]

    for seed in range(20):
        chosen = select_alternative(random.Random(seed), evaluated, creatividad=0.0)
        assert chosen.alternative.target_player_id == "a"


def test_empty_alternatives_returns_none():
    assert select_alternative(random.Random(1), [], creatividad=0.5) is None
