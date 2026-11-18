// UI logic: reacts to server messages and sends the player's actions.
import { Arena } from "./arena.js";
import { Socket } from "./socket.js";

const $ = (id) => document.getElementById(id);
const arena = new Arena($("arena"));
const state = { socket: null, me: null, players: [], words: [], index: 0, size: 1 };

// ---- Screens and messages -------------------------------------------------

function show(screen) {
  for (const id of ["home", "room", "game"]) $(id).hidden = id !== screen;
}

let toastTimer;
function toast(text) {
  $("toast").textContent = text;
  $("toast").classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $("toast").classList.remove("visible"), 3500);
}

// One handler per message type the server can send.
const handlers = {
  welcome(msg) {
    state.me = msg.id;
    $("lobby").hidden = false;
    $("name-form").hidden = true;
  },

  queued(msg) {
    $("queue-status").textContent = `Searching for players: ${msg.waiting} of ${msg.needed}`;
    $("cancel-queue").hidden = false;
    $("find-match").disabled = true;
  },

  room_state(msg) {
    show("room");
    state.size = msg.size;
    $("room-code").textContent = msg.code;
    $("room-format").textContent = `${msg.size}v${msg.size}`;
    for (const team of ["A", "B"]) {
      const list = $(`team-${team}`);
      list.replaceChildren(...msg.players.filter((p) => p.team === team).map((p) => {
        const item = document.createElement("li");
        item.textContent = p.id === msg.host ? `${p.name} (host)` : p.name;
        return item;
      }));
    }
    const unassigned = msg.players.filter((p) => !p.team).map((p) => p.name);
    $("unassigned").textContent = unassigned.length ? `Choosing a team: ${unassigned.join(", ")}` : "";
    const full = ["A", "B"].every((t) => msg.players.filter((p) => p.team === t).length === msg.size);
    $("start-room").hidden = msg.host !== state.me;
    $("start-room").disabled = !full;
  },

  countdown(msg) {
    show("game");
    arena.reset([], state.me);
    $("typing").disabled = true;
    $("timer").textContent = "";
    $("overlay-title").textContent = msg.seconds;
    $("overlay-text").textContent = "Get ready";
    $("back-to-lobby").hidden = true;
    $("overlay").hidden = false;
  },

  match_start(msg) {
    state.players = msg.players;
    state.words = msg.words;
    state.index = 0;
    arena.reset(msg.players, state.me);
    $("overlay").hidden = true;
    $("typing").disabled = false;
    $("typing").value = "";
    $("typing").focus();
    renderWord("");
  },

  tick(msg) {
    arena.update(msg);
    $("timer").textContent = Math.ceil(msg.time_left);
  },

  match_end(msg) {
    const myTeam = state.players.find((p) => p.id === state.me)?.team;
    $("typing").disabled = true;
    $("overlay-title").textContent = msg.winner === "draw" ? "Draw" : msg.winner === myTeam ? "You win" : "You lose";
    $("overlay-text").textContent = msg.winner === "draw" ? "Both teams pulled equally."
      : msg.reason === "rope" ? "The rope crossed the win line." : "Time ran out. The team ahead wins.";
    $("back-to-lobby").hidden = false;
    $("overlay").hidden = false;
  },

  error(msg) {
    toast(msg.message);
  },
};

function connect(name) {
  state.socket = new Socket(
    name,
    (msg) => handlers[msg.type]?.(msg),
    () => toast("Connection lost. Reload the page to reconnect."),
  );
}

// ---- Lobby ------------------------------------------------------------------

const selectedSize = () => Number(document.querySelector("input[name=size]:checked").value);

$("name-form").addEventListener("submit", (event) => {
  event.preventDefault();
  connect($("name").value.trim() || "Player");
});

$("find-match").addEventListener("click", () => state.socket.send("queue", { size: selectedSize() }));

$("cancel-queue").addEventListener("click", () => {
  state.socket.send("cancel_queue");
  $("queue-status").textContent = "";
  $("cancel-queue").hidden = true;
  $("find-match").disabled = false;
});

$("create-room").addEventListener("click", () => state.socket.send("create_room", { size: selectedSize() }));

$("join-form").addEventListener("submit", (event) => {
  event.preventDefault();
  state.socket.send("join_room", { code: $("join-code").value.trim().toUpperCase() });
});

// ---- Room -------------------------------------------------------------------

$("join-team-A").addEventListener("click", () => state.socket.send("choose_team", { team: "A" }));
$("join-team-B").addEventListener("click", () => state.socket.send("choose_team", { team: "B" }));
$("start-room").addEventListener("click", () => state.socket.send("start"));
$("leave-room").addEventListener("click", () => {
  state.socket.send("leave");
  backToLobby();
});

function backToLobby() {
  $("queue-status").textContent = "";
  $("cancel-queue").hidden = true;
  $("find-match").disabled = false;
  show("home");
}
$("back-to-lobby").addEventListener("click", backToLobby);

// ---- Typing -----------------------------------------------------------------

// Shows the current word letter by letter (correct / wrong) and a preview of the next ones.
function renderWord(typed) {
  const word = state.words[state.index] ?? "";
  $("word").replaceChildren(...[...word].map((letter, i) => {
    const span = document.createElement("span");
    span.textContent = letter;
    if (i < typed.length) span.className = typed[i] === letter ? "ok" : "bad";
    return span;
  }));
  $("next-words").textContent = state.words.slice(state.index + 1, state.index + 5).join("  ");
}

$("typing").addEventListener("input", (event) => {
  const typed = event.target.value;
  if (typed === state.words[state.index]) {
    state.socket.send("word", { text: typed });   // the server checks it again
    state.index += 1;
    event.target.value = "";
    renderWord("");
  } else {
    renderWord(typed);
  }
});

// Keep the cursor in the input so players never have to click it.
$("game").addEventListener("click", () => $("typing").focus());
