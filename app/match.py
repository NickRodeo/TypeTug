"""Game rules for one match. Pure logic: no networking, no asyncio.

Rope position runs from -1 to +1.
  +1 -> Team A pulled the rope to their side and wins
  -1 -> Team B pulled the rope to their side and wins
Each correct word adds force equal to its length to the typist's team.
"""
import time

TEAMS = ("A", "B")


class Match:
    def __init__(self, teams, words, duration, margin_per_player, clock=time.monotonic):
        self.teams = teams                       # {player_id: "A" | "B"}
        self.words = words                       # same list for every player, so it is fair
        self.duration = duration
        self._clock = clock
        self._started_at = clock()
        team_sizes = [list(teams.values()).count(team) for team in TEAMS]
        self.margin = margin_per_player * max(max(team_sizes), 1)
        self._words_done = dict.fromkeys(teams, 0)
        self._force = {"A": 0, "B": 0}
        self.winner = None                       # "A", "B" or "draw" once finished
        self.reason = None                       # "rope" or "time"

    @property
    def rope(self) -> float:
        lead = (self._force["A"] - self._force["B"]) / self.margin
        return max(-1.0, min(1.0, lead))

    @property
    def time_left(self) -> float:
        return max(0.0, self.duration - (self._clock() - self._started_at))

    def submit(self, player_id, typed) -> bool:
        """Count a typed word if it is the player's next word. Returns True if accepted."""
        if self.winner is not None or player_id not in self.teams:
            return False
        index = self._words_done[player_id]
        if index >= len(self.words) or typed != self.words[index]:
            return False
        self._words_done[player_id] += 1
        self._force[self.teams[player_id]] += len(typed)
        return True

    def update(self) -> bool:
        """Check the end conditions. Returns True once the match is over."""
        if self.winner is None:
            if abs(self.rope) >= 1:
                self._finish("A" if self.rope > 0 else "B", "rope")
            elif self.time_left <= 0:
                lead = self._force["A"] - self._force["B"]
                self._finish("A" if lead > 0 else "B" if lead < 0 else "draw", "time")
        return self.winner is not None

    def _finish(self, winner, reason):
        self.winner, self.reason = winner, reason

    def snapshot(self) -> dict:
        return {
            "type": "tick",
            "rope": round(self.rope, 3),
            "time_left": round(self.time_left, 1),
            "words_done": self._words_done,
        }

    def result(self) -> dict:
        return {"type": "match_end", "winner": self.winner, "reason": self.reason}
