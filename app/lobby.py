"""Tracks every connected client, the matchmaking queues and the open rooms."""
import secrets

from .client import Client
from .config import MAX_TEAM_SIZE, Settings
from .room import LobbyError, Room
from .words import WordService

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I to avoid typos


class Lobby:
    def __init__(self, settings: Settings, words: WordService):
        self.settings = settings
        self.words = words
        self.clients: dict[str, Client] = {}
        self.rooms: dict[str, Room] = {}
        self.queues: dict[int, list[Client]] = {size: [] for size in range(1, MAX_TEAM_SIZE + 1)}

    # --- connection -------------------------------------------------------

    def connect(self, client: Client):
        self.clients[client.id] = client

    def disconnect(self, client: Client):
        self.leave(client)
        self.clients.pop(client.id, None)

    def stats(self) -> dict:
        return {
            "clients": len(self.clients),
            "rooms": len(self.rooms),
            "queued": sum(len(queue) for queue in self.queues.values()),
        }

    # --- random matchmaking -----------------------------------------------

    def enqueue(self, client: Client, size: int):
        self._require_idle(client)
        queue = self.queues[size]
        queue.append(client)
        client.queued_size = size
        needed = 2 * size
        if len(queue) < needed:
            self._announce_queue(size)
            return
        players, self.queues[size] = queue[:needed], queue[needed:]
        room = self._new_room(size, "random")
        for player in players:
            player.queued_size = None
            room.add(player)
        room.assign_random_teams()
        room.start()

    def cancel_queue(self, client: Client):
        size = client.queued_size
        if size is None:
            return
        self.queues[size].remove(client)
        client.queued_size = None
        self._announce_queue(size)

    def _announce_queue(self, size: int):
        queue = self.queues[size]
        for waiting in queue:
            waiting.send({"type": "queued", "size": size, "waiting": len(queue), "needed": 2 * size})

    # --- custom rooms -----------------------------------------------------

    def create_room(self, client: Client, size: int):
        self._require_idle(client)
        room = self._new_room(size, "custom")
        room.host_id = client.id
        room.add(client)
        room.broadcast_state()

    def join_room(self, client: Client, code: str):
        self._require_idle(client)
        room = self.rooms.get(code.upper())
        if room is None or room.phase != "waiting":
            raise LobbyError("Room not found or already started")
        if len(room.members) >= 2 * room.size:
            raise LobbyError("Room is full")
        room.add(client)
        room.broadcast_state()

    def choose_team(self, client: Client, team: str):
        self._require_room(client).set_team(client, team)

    def start_room(self, client: Client):
        self._require_room(client).start_by(client)

    # --- shared -----------------------------------------------------------

    def submit_word(self, client: Client, text: str):
        if client.room:
            client.room.submit_word(client, text)

    def leave(self, client: Client):
        self.cancel_queue(client)
        if client.room:
            client.room.remove(client)

    def _new_room(self, size: int, mode: str) -> Room:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        while code in self.rooms:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        room = Room(code, size, mode, self.settings, self.words, on_close=self._close_room)
        self.rooms[code] = room
        return room

    def _close_room(self, room: Room):
        """Called when a room ends. Safe to call more than once."""
        self.rooms.pop(room.code, None)
        for member in room.members.values():
            member.room = None
        room.members.clear()

    def _require_idle(self, client: Client):
        if client.room or client.queued_size:
            raise LobbyError("Leave your current room or queue first")

    def _require_room(self, client: Client) -> Room:
        if client.room is None:
            raise LobbyError("You are not in a room")
        return client.room
