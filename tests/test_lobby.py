import asyncio
import json

import pytest

from app.client import Client, RateLimiter
from app.config import Settings
from app.lobby import Lobby
from app.room import LobbyError
from app.words import WordService

FAST = Settings(countdown=0, match_duration=0.3, tick_rate=50)
WORDS = WordService([f"word{chr(97 + i)}{chr(97 + j)}" for i in range(10) for j in range(10)])


def drain(client):
    """All messages a client has received so far, as dicts."""
    messages = []
    while not client.outbox.empty():
        messages.append(json.loads(client.outbox.get_nowait()))
    return messages


def run(coro):
    return asyncio.run(coro)


def test_random_matchmaking_runs_a_full_match():
    async def scenario():
        lobby = Lobby(FAST, WORDS)
        a, b = Client("Ann", FAST), Client("Bob", FAST)
        for client in (a, b):
            lobby.connect(client)
            lobby.enqueue(client, 1)
        await asyncio.sleep(0.6)
        types = [m["type"] for m in drain(a)]
        assert "match_start" in types and "tick" in types and types[-1] == "match_end"
        assert lobby.stats() == {"clients": 2, "rooms": 0, "queued": 0}
    run(scenario())


def test_queue_waits_until_enough_players():
    async def scenario():
        lobby = Lobby(FAST, WORDS)
        clients = [Client(f"p{i}", FAST) for i in range(3)]
        for client in clients:
            lobby.connect(client)
            lobby.enqueue(client, 2)           # 2v2 needs 4 players
        assert lobby.stats()["queued"] == 3
        assert drain(clients[2])[-1]["waiting"] == 3
    run(scenario())


def test_custom_room_flow():
    async def scenario():
        lobby = Lobby(FAST, WORDS)
        host, guest = Client("Host", FAST), Client("Guest", FAST)
        lobby.connect(host)
        lobby.connect(guest)
        lobby.create_room(host, 1)
        code = drain(host)[-1]["code"]
        lobby.join_room(guest, code)
        lobby.choose_team(host, "A")
        with pytest.raises(LobbyError):
            lobby.start_room(host)             # guest has no team yet
        lobby.choose_team(guest, "B")
        with pytest.raises(LobbyError):
            lobby.start_room(guest)            # only the host may start
        lobby.start_room(host)
        await asyncio.sleep(0.6)
        assert drain(guest)[-1]["type"] == "match_end"
    run(scenario())


def test_team_cannot_exceed_its_size():
    async def scenario():
        lobby = Lobby(FAST, WORDS)
        host, guest = Client("Host", FAST), Client("Guest", FAST)
        for client in (host, guest):
            lobby.connect(client)
        lobby.create_room(host, 1)
        lobby.join_room(guest, drain(host)[-1]["code"])
        lobby.choose_team(host, "A")
        with pytest.raises(LobbyError):
            lobby.choose_team(guest, "A")
    run(scenario())


def test_disconnect_cleans_up_room_and_queue():
    async def scenario():
        lobby = Lobby(FAST, WORDS)
        host = Client("Host", FAST)
        lobby.connect(host)
        lobby.create_room(host, 1)
        lobby.disconnect(host)
        assert lobby.stats() == {"clients": 0, "rooms": 0, "queued": 0}
    run(scenario())


def test_slow_client_keeps_newest_messages():
    client = Client("Slow", Settings(outbox_size=2))
    for n in range(5):
        client.send({"n": n})
    assert [m["n"] for m in drain(client)] == [3, 4]


def test_rate_limiter_blocks_floods():
    now = [0.0]
    limiter = RateLimiter(rate=5, clock=lambda: now[0])
    allowed = sum(limiter.allow() for _ in range(20))
    assert allowed == 5
    now[0] = 1.0
    assert limiter.allow()
