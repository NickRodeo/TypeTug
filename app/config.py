"""Application settings.

Every value can be overridden with an environment variable
of the same name in upper case, e.g. MATCH_DURATION=90.
"""
import os
from dataclasses import dataclass, fields

MAX_TEAM_SIZE = 5  # biggest supported format is 5v5


@dataclass(frozen=True)
class Settings:
    tick_rate: int = 20                  # state broadcasts per second
    match_duration: float = 60.0         # seconds
    countdown: int = 3                   # seconds before a match starts
    word_language: str = "en"            # any language supported by wordfreq, e.g. "id"
    word_min_length: int = 3
    word_max_length: int = 10
    words_per_match: int = 300
    margin_per_player: int = 40          # characters of lead needed to win, per player on a team
    max_messages_per_second: int = 30    # per-client rate limit
    heartbeat_interval: float = 10.0     # seconds between WebSocket pings
    outbox_size: int = 64                # max queued outgoing messages per client

    @classmethod
    def from_env(cls) -> "Settings":
        values = {}
        for field in fields(cls):
            raw = os.getenv(field.name.upper())
            if raw is not None:
                values[field.name] = field.type(raw)
        return cls(**values)
