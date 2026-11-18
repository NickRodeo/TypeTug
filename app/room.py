"""A room holds the players of one match and runs its game loop."""
import asyncio
import json
import random

from .client import Client
from .config import Settings
from .match import Match
from .words import WordService


class LobbyError(Exception):
    """A problem caused by the player's request. The message is sent back to them."""


class Room:
    def __init__(self, code, size, mode, settings: Settings, words: WordService, on_close):
        self.code = code
        self.size = size                  # players per team
        self.mode = mode                  # "random" or "custom"
        self.settings = settings
        self.words = words
        self.on_close = on_close
        self.phase = "waiting"            # waiting -> countdown -> playing -> finished
        self.members: dict[str, Client] = {}
        self.teams: dict[str, str | None] = {}
        self.host_id = None
        self.match = None
        self._task = None

    # --- membership -------------------------------------------------------

    def add(self, client: Client):
        self.members[client.id] = client
        self.teams[client.id] = None
        client.room = self

    def remove(self, client: Client):
        self.members.pop(client.id, None)
        client.room = None
        if self.phase == "waiting":
            self.teams.pop(client.id, None)  # once a match started, the player's score stays
            if self.host_id == client.id:
                self.host_id = next(iter(self.members), None)
            self.broadcast_state()
        if not self.members:
            if self._task:
                self._task.cancel()
            self.on_close(self)

    def set_team(self, client: Client, team: str):
        if self.phase != "waiting":
            raise LobbyError("The match has already started")
        taken = sum(1 for cid, t in self.teams.items() if t == team and cid != client.id)
        if taken >= self.size:
            raise LobbyError("That team is full")
        self.teams[client.id] = team
        self.broadcast_state()

    def assign_random_teams(self):
        ids = list(self.members)
        random.shuffle(ids)
        for position, client_id in enumerate(ids):
            self.teams[client_id] = "A" if position < self.size else "B"

    def is_ready(self) -> bool:
        assigned = list(self.teams.values())
        return assigned.count("A") == self.size and assigned.count("B") == self.size

    # --- lifecycle --------------------------------------------------------

    def start_by(self, client: Client):
        if client.id != self.host_id:
            raise LobbyError("Only the host can start the match")
        if self.phase != "waiting" or not self.is_ready():
            raise LobbyError(f"Both teams need exactly {self.size} players")
        self.start()

    def start(self):
        self.phase = "countdown"
        self._task = asyncio.create_task(self._run())

    def submit_word(self, client: Client, text: str):
        if self.phase == "playing":
            self.match.submit(client.id, text)

    async def _run(self):
        try:
            for seconds in range(self.settings.countdown, 0, -1):
                self.broadcast({"type": "countdown", "seconds": seconds})
                await asyncio.sleep(1)
            self._begin_match()
            while not self.match.update():
                self.broadcast(self.match.snapshot())
                await asyncio.sleep(1 / self.settings.tick_rate)
            self.broadcast(self.match.snapshot())
            self.phase = "finished"
            self.broadcast(self.match.result())
        finally:
            self.on_close(self)

    def _begin_match(self):
        words = self.words.sample(random.Random(), self.settings.words_per_match)
        teams = {cid: team for cid, team in self.teams.items() if team}
        self.match = Match(teams, words, self.settings.match_duration, self.settings.margin_per_player)
        self.phase = "playing"
        self.broadcast({
            "type": "match_start",
            "words": words,
            "duration": self.settings.match_duration,
            "players": self.player_list(),
        })

    # --- messaging --------------------------------------------------------

    def player_list(self):
        return [
            {"id": cid, "name": self.members[cid].name, "team": team}
            for cid, team in self.teams.items() if cid in self.members
        ]

    def broadcast(self, message: dict):
        text = json.dumps(message)  # serialize once, send to everyone
        for client in self.members.values():
            client.send_raw(text)

    def broadcast_state(self):
        self.broadcast({
            "type": "room_state",
            "code": self.code,
            "mode": self.mode,
            "size": self.size,
            "host": self.host_id,
            "players": self.player_list(),
        })
