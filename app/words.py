"""Word generation.

Words are never hardcoded. A frequency-ranked dictionary is loaded once at
startup, filtered, and sampled randomly for every match.
"""
import random
from pathlib import Path


def filter_words(candidates, min_length, max_length, blocklist=frozenset()):
    """Keep only plain lowercase words that are easy to type."""
    return [
        word for word in candidates
        if word.isascii() and word.isalpha()
        and min_length <= len(word) <= max_length
        and word not in blocklist
    ]


def load_blocklist(path: Path) -> frozenset:
    lines = path.read_text().splitlines() if path.exists() else []
    return frozenset(line.strip().lower() for line in lines if line.strip() and not line.startswith("#"))


class WordService:
    def __init__(self, words):
        if not words:
            raise ValueError("The word pool is empty. Check the language and length settings.")
        self._pool = list(words)

    @classmethod
    def from_wordfreq(cls, language, min_length, max_length, top_n=20000, blocklist=frozenset()):
        from wordfreq import top_n_list  # imported here so tests do not need the package
        candidates = top_n_list(language, top_n)
        return cls(filter_words(candidates, min_length, max_length, blocklist))

    def sample(self, rng: random.Random, count: int):
        """Random words without repeats. Using the same rng seed gives the same words."""
        return rng.sample(self._pool, min(count, len(self._pool)))
