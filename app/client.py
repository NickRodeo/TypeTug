"""One connected player."""
import asyncio
import json
import time
import uuid


class RateLimiter:
    """Token bucket: allows `rate` messages per second, with a small burst."""

    def __init__(self, rate: float, clock=time.monotonic):
        self._rate = rate
        self._tokens = rate
        self._clock = clock
        self._last = clock()

    def allow(self) -> bool:
        now = self._clock()
        self._tokens = min(self._rate, self._tokens + (now - self._last) * self._rate)
        self._last = now
        if self._tokens < 1:
            return False
        self._tokens -= 1
        return True


class Client:
    """Outgoing messages go into a queue and a separate task writes them to the socket.
    This way a slow client can never block a game loop that is broadcasting to everyone."""

    def __init__(self, name, settings):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.outbox = asyncio.Queue(maxsize=settings.outbox_size)
        self.limiter = RateLimiter(settings.max_messages_per_second)
        self.room = None
        self.queued_size = None

    def send(self, message: dict):
        self.send_raw(json.dumps(message))

    def send_raw(self, text: str):
        if self.outbox.full():
            self.outbox.get_nowait()  # slow client: drop the oldest message, keep the newest
        self.outbox.put_nowait(text)
