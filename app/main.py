"""Entry point: HTTP for the static site, one WebSocket endpoint for the game."""
import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .client import Client
from .config import Settings
from .lobby import Lobby
from .room import LobbyError
from .schemas import (CancelQueue, ChooseTeam, CreateRoom, JoinRoom, Leave,
                      Queue, StartMatch, SubmitWord, parse_message)
from .words import WordService, load_blocklist

ROOT = Path(__file__).resolve().parent.parent
MAX_MESSAGE_LENGTH = 512

settings = Settings.from_env()
words = WordService.from_wordfreq(
    settings.word_language,
    settings.word_min_length,
    settings.word_max_length,
    blocklist=load_blocklist(ROOT / "app" / "data" / "blocklist.txt"),
)
lobby = Lobby(settings, words)
app = FastAPI(title="TugType")


@app.get("/stats")
def stats():
    return lobby.stats()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, name: str = "Player"):
    await ws.accept()
    client = Client(name.strip()[:16] or "Player", settings)
    lobby.connect(client)
    client.send({"type": "welcome", "id": client.id, "name": client.name})
    writer = asyncio.create_task(write_loop(ws, client))
    try:
        while True:
            handle_message(client, await ws.receive_text())
    except WebSocketDisconnect:
        pass
    finally:
        writer.cancel()
        lobby.disconnect(client)


async def write_loop(ws: WebSocket, client: Client):
    """Sends queued messages to the socket, one at a time."""
    try:
        while True:
            await ws.send_text(await client.outbox.get())
    except Exception:
        pass  # connection is gone; the receive loop will clean up


def handle_message(client: Client, raw: str):
    if len(raw) > MAX_MESSAGE_LENGTH or not client.limiter.allow():
        return  # drop silently so a flood does not cause a flood of replies
    try:
        message = parse_message(raw)
    except ValidationError:
        client.send({"type": "error", "message": "Invalid message"})
        return
    try:
        dispatch(client, message)
    except LobbyError as error:
        client.send({"type": "error", "message": str(error)})


def dispatch(client: Client, message):
    match message:
        case Queue():
            lobby.enqueue(client, message.size)
        case CancelQueue():
            lobby.cancel_queue(client)
        case CreateRoom():
            lobby.create_room(client, message.size)
        case JoinRoom():
            lobby.join_room(client, message.code)
        case ChooseTeam():
            lobby.choose_team(client, message.team)
        case StartMatch():
            lobby.start_room(client)
        case Leave():
            lobby.leave(client)
        case SubmitWord():
            lobby.submit_word(client, message.text)


# Mounted last so it does not shadow the routes above.
app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
