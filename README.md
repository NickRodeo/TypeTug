# TugType

**Real-time multiplayer tug of war, powered by typing speed.**

TugType is a browser-based multiplayer game where teams pull a rope by typing words faster than their opponents. Matches support 1v1 up to 5v5, with random matchmaking or custom teams. The server is built in Python on asynchronous WebSockets and designed to handle many concurrent players and rooms.

> **Status:** In development. Built as a Network Programming course project.

---

## Features

- **Flexible match formats:** 1v1, 2v2, 3v3, 4v4, and 5v5.
- **Two ways to form teams:** random matchmaking, or custom rooms where players choose their own teams.
- **Typing-driven gameplay:** every correct word pulls the rope toward your side. Longer words pull harder.
- **Animated rope and characters:** the rope and the pulling animation reflect the live state of the match.
- **Match timer:** if nobody wins by pulling the marker past the win line, the team ahead when time runs out wins.
- **Dynamic word generation:** words are sampled at runtime from a real dictionary, never hardcoded. Length and difficulty are configurable.
- **Server-authoritative:** all scoring and rope physics are computed on the server, so clients cannot cheat by sending fake progress.

## How a Match Works

1. Players join the lobby and pick a format (1v1 to 5v5).
2. They are placed into teams, either randomly or by custom team selection.
3. A short countdown starts the round, and each player receives a word to type.
4. Every correctly typed word applies force to the rope for that player's team.
5. The rope moves according to the force difference between the two teams.
6. The match ends when the rope crosses a win line or the timer expires.

## Architecture

```
Browser (HTML / CSS / JS, Canvas)
        |
        |  WebSocket (JSON messages)
        v
FastAPI + Uvicorn (asyncio, single process)
  |-- main.py     WebSocket endpoint, message validation, rate limiting
  |-- lobby.py    clients, matchmaking queues, custom rooms
  |-- room.py     one asyncio task per room: countdown, tick loop, broadcast
  |-- match.py    game rules and rope physics (pure logic, no networking)
  |-- words.py    dictionary-based random word generation
```

Key design decisions:

- **One asyncio task per room** runs the game loop, so rooms are isolated and never block each other.
- **State broadcast at a fixed tick rate** (instead of on every keystroke) keeps bandwidth predictable as player count grows. Each broadcast is serialized once and shared by all players in the room.
- **Per-client outbox queue.** Game loops only put messages in a queue; a separate task writes them to the socket. A slow client can never stall a room, and its oldest messages are dropped first.
- **Typed message protocol** validated with Pydantic, so every client message is checked before it reaches game logic.
- **Per-client rate limiting** (token bucket) caps messages per second, so one misbehaving client cannot overload a room.
- **WebSocket heartbeat** (ping/pong, handled by Uvicorn) detects dead connections and frees their resources.
- **Game rules are separate from networking.** `match.py` has no I/O, so it is easy to read, explain and test.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Uvicorn, asyncio |
| Realtime | WebSockets |
| Validation | Pydantic |
| Word source | `wordfreq` (frequency-ranked dictionary) |
| Frontend | HTML, CSS, vanilla JavaScript (ES modules), Canvas |
| Testing | pytest, asyncio bot script for load testing |

## Word Generation

Words are not stored in the source code. At startup, `WordService` loads a frequency-ranked word list for the configured language and filters it by:

- minimum and maximum length
- lowercase letters only
- an optional blocklist (`app/data/blocklist.txt`)

At the start of each match, words are sampled randomly from this pool without repeats. Every player in a match receives the same word list, so the race is fair. The server checks each submitted word against the player's expected next word.

Set `WORD_LANGUAGE=id` to play with Indonesian words.

## Project Structure

```
tugtype/
├── app/
│   ├── main.py        # FastAPI app, WebSocket endpoint, message dispatch
│   ├── config.py      # Settings (environment variables)
│   ├── schemas.py     # Client message models (Pydantic)
│   ├── client.py      # Connected player, outbox queue, rate limiter
│   ├── lobby.py       # Matchmaking queues and custom rooms
│   ├── room.py        # Room lifecycle and game loop
│   ├── match.py       # Rules and rope physics
│   ├── words.py       # Word loading, filtering, sampling
│   └── data/blocklist.txt
├── static/            # Frontend: index.html, style.css, app.js, arena.js, socket.js
├── tests/             # Unit and integration tests
├── loadtest/bots.py   # Simulated players
├── run.py             # Starts the server
└── requirements.txt
```

## Getting Started

```bash
# Clone
git clone https://github.com/<your-username>/tugtype.git
cd tugtype

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies (requirements-dev.txt adds the test tools)
pip install -r requirements-dev.txt

# Run the server
python run.py
```

Open `http://localhost:8000` in two browser tabs to play against yourself. Live server numbers (clients, rooms, queued players) are at `http://localhost:8000/stats`.

## Configuration

Settings live in `app/config.py`. Override any of them with an environment variable, for example `MATCH_DURATION=90 python run.py`.

| Variable | Description | Default |
| --- | --- | --- |
| `TICK_RATE` | State broadcasts per second | `20` |
| `MATCH_DURATION` | Match length in seconds | `60` |
| `COUNTDOWN` | Seconds before a match starts | `3` |
| `WORD_LANGUAGE` | Dictionary language (`en`, `id`, ...) | `en` |
| `WORD_MIN_LENGTH` / `WORD_MAX_LENGTH` | Word length range | `3` / `10` |
| `WORDS_PER_MATCH` | Words generated per match | `300` |
| `MARGIN_PER_PLAYER` | Characters of lead needed to win, per player on a team | `40` |
| `MAX_MESSAGES_PER_SECOND` | Rate limit per client | `30` |
| `HEARTBEAT_INTERVAL` | Seconds between WebSocket pings | `10` |
| `OUTBOX_SIZE` | Queued outgoing messages per client | `64` |

## Testing

```bash
# Unit and integration tests
pytest

# Load test: 200 simulated players (start the server first)
python loadtest/bots.py --bots 200
```

## Roadmap

- [x] WebSocket server and connection manager
- [x] Lobby, rooms, and team assignment
- [x] Game engine and rope physics
- [x] Dynamic word generation
- [x] Frontend with rope and character animation
- [x] Rate limiting and heartbeat
- [ ] Load testing results and performance tuning
- [ ] Reconnect handling
- [ ] Multi-worker scaling with Redis
- [ ] Leaderboard and match history
- [ ] Spectator mode
- [ ] Lobby chat

## License

MIT
