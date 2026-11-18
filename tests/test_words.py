import random

import pytest

from app.words import WordService, filter_words


def test_filter_keeps_only_typeable_words_in_range():
    candidates = ["hi", "house", "don't", "x2y", "naïve", "extraordinarily", "river"]
    assert filter_words(candidates, 3, 10) == ["house", "river"]


def test_blocklist_is_respected():
    assert filter_words(["house", "river"], 3, 10, blocklist={"river"}) == ["house"]


def test_same_seed_gives_same_words():
    service = WordService([f"word{chr(97 + i)}" for i in range(20)])
    assert service.sample(random.Random(1), 5) == service.sample(random.Random(1), 5)


def test_sample_has_no_repeats_and_respects_pool_size():
    service = WordService(["alpha", "bravo", "delta"])
    result = service.sample(random.Random(), 10)
    assert sorted(result) == ["alpha", "bravo", "delta"]


def test_empty_pool_is_an_error():
    with pytest.raises(ValueError):
        WordService([])
