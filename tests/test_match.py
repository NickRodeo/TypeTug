from app.match import Match


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make_match(clock, size=1, duration=60, margin=10):
    teams = {f"a{i}": "A" for i in range(size)} | {f"b{i}": "B" for i in range(size)}
    return Match(teams, ["apple", "river", "stone"], duration, margin, clock)


def test_correct_word_moves_rope_toward_typists_team():
    match = make_match(FakeClock())
    assert match.submit("a0", "apple")
    assert match.rope == 0.5           # 5 chars / margin 10


def test_wrong_word_is_rejected():
    match = make_match(FakeClock())
    assert not match.submit("a0", "wrong")
    assert match.rope == 0


def test_words_must_be_typed_in_order():
    match = make_match(FakeClock())
    assert not match.submit("a0", "river")   # first word is "apple"


def test_team_wins_when_rope_reaches_the_line():
    match = make_match(FakeClock())
    match.submit("a0", "apple")
    match.submit("a0", "river")
    assert match.update()
    assert (match.winner, match.reason) == ("A", "rope")


def test_team_ahead_wins_when_time_runs_out():
    clock = FakeClock()
    match = make_match(clock, margin=100)
    match.submit("b0", "apple")
    clock.now = 61
    assert match.update()
    assert (match.winner, match.reason) == ("B", "time")


def test_equal_force_is_a_draw():
    clock = FakeClock()
    match = make_match(clock, margin=100)
    clock.now = 61
    match.update()
    assert match.winner == "draw"


def test_margin_scales_with_team_size():
    assert make_match(FakeClock(), size=1).margin == 10
    assert make_match(FakeClock(), size=5).margin == 50


def test_no_points_after_match_is_over():
    match = make_match(FakeClock())
    match.submit("a0", "apple")
    match.submit("a0", "river")
    match.update()
    assert not match.submit("b0", "apple")
