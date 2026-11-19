"""The town view: the data it embeds, checked against the record it was built from."""

import json
import re
import shutil
import sqlite3

import pytest

from engine import townview
from engine.config import load_config
from engine.recorder import TABLES, Recorder
from engine.runner import run
from engine.town import Town
from engine.townview import CORE_JS, KIND, KLASS, ROLE, build_town_view, encode, mood_step, spot_tracks


def at(track, week):
    """The value in force in `week`: the last entry at or before it. None before the first."""
    value = None
    for i in range(0, len(track), 2):
        if track[i] > week:
            break
        value = track[i + 1]
    return value


def weekly(values, first, i):
    """The value for recorded week number `i` in a list that has one value for each recorded
    week from number `first`. None before the first, or past the end."""
    k = i - first
    return values[k] if 0 <= k < len(values) else None


def none(value):
    return -1 if value is None else value


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    cfg = load_config(None, ["population_cap=80", "years=4", "seed=9", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path_factory.mktemp("runs"), quiet=True)
    con = sqlite3.connect(run_dir / "run.sqlite")
    yield run_dir, con
    con.close()


# --- change lists ---------------------------------------------------------------------------------
def test_encode_keeps_only_the_changes():
    assert encode([(0, 5), (1, 5), (2, 7), (3, 7), (4, 5)]) == [0, 5, 2, 7, 4, 5]


def test_encode_writes_none_as_minus_one():
    assert encode([(3, None), (4, 2), (5, None)]) == [3, -1, 4, 2, 5, -1]


def test_encode_of_nothing_is_empty():
    assert encode([]) == []


def test_mood_step_has_two_steps_on_each_side_of_the_cutoff():
    assert mood_step(0, 0.10, 0.5) == 0
    assert mood_step(0, 0.25, 0.5) == 1          # the halfway point belongs to the step nearer the cutoff
    assert mood_step(0, 0.49, 0.5) == 1
    assert mood_step(1, 0.50, 0.5) == 2
    assert mood_step(1, 0.74, 0.5) == 2
    assert mood_step(1, 0.75, 0.5) == 3
    assert mood_step(1, 1.00, 0.5) == 3


def test_mood_step_takes_its_side_from_the_recorded_flag():
    assert mood_step(0, 0.9, 0.5) == 1           # recorded unhappy: never drawn on the happy side
    assert mood_step(1, 0.1, 0.5) == 2


def test_mood_step_follows_the_runs_own_cutoff():
    assert mood_step(0, 0.35, 0.8) == 0          # under half of 0.8
    assert mood_step(0, 0.45, 0.8) == 1
    assert mood_step(1, 0.85, 0.8) == 2          # under halfway from 0.8 to 1
    assert mood_step(1, 0.95, 0.8) == 3


# --- the people -----------------------------------------------------------------------------------
def test_every_person_is_there_with_the_week_they_came(recorded):
    _, con = recorded
    people = townview._people(con, 0.5)
    static = con.execute("SELECT agent, arrived FROM agent_static ORDER BY agent").fetchall()
    assert [(p["id"], p["arrived"]) for p in people] == static
    assert len(people) == 80
    assert set(people[0]) == {"id", "arrived", "h", "j", "o", "k", "m", "r", "f", "e",
                              "w", "c0", "c"}                # nothing the page does not use


def test_the_colour_step_is_worked_out_from_the_recorded_wellbeing(recorded):
    _, con = recorded
    people = {p["id"]: p for p in townview._people(con, 0.5)}
    seen = set()
    for week, agent, happy, wellbeing in con.execute("SELECT week, agent, happy, wellbeing FROM agent_snap"):
        step = at(people[agent]["m"], week)
        assert step == mood_step(happy, wellbeing, 0.5)
        seen.add(step)
    assert len(seen) >= 2                                   # the run has more than one step in it


def test_people_tracks_read_back_as_the_record(recorded):
    _, con = recorded
    people = {p["id"]: p for p in townview._people(con, 0.5)}
    rows = con.execute("SELECT week, agent, home_spot, employer, role, klass, happy, rides, food_firm, "
                       "fun_firm FROM agent_snap").fetchall()
    assert len(rows) > 5000
    for week, agent, home, employer, role, klass, happy, rides, food, fun in rows:
        p = people[agent]
        assert at(p["h"], week) == none(home)
        assert at(p["j"], week) == none(employer)
        assert at(p["o"], week) == ROLE[role]
        assert at(p["k"], week) == KLASS[klass]
        assert (at(p["m"], week) >= 2) == bool(happy)
        assert at(p["r"], week) == (0 if rides is None else 1)
        assert at(p["f"], week) == none(food)
        assert at(p["e"], week) == none(fun)


def test_a_person_is_not_on_the_page_before_they_arrive(recorded):
    _, con = recorded
    late = [p for p in townview._people(con, 0.5) if p["arrived"] > 0]
    assert late
    for p in late:
        first = p["h"][0]
        assert first >= p["arrived"]
        for key in "hjokmrfew":
            assert p[key][0] == first
            assert at(p[key], first - 1) is None


def test_tracks_hold_only_changes(recorded):
    _, con = recorded
    for p in townview._people(con, 0.5):
        for key in "hjokmrfew":
            track = p[key]
            weeks, values = track[0::2], track[1::2]
            assert weeks == sorted(set(weeks))
            assert all(a != b for a, b in zip(values, values[1:]))


# --- their money, every week ------------------------------------------------------------------------
def test_cash_and_pay_read_back_as_the_record_every_week(recorded):
    _, con = recorded
    number = {week: i for i, week in enumerate(townview._weeks(con))}
    people = {p["id"]: p for p in townview._people(con, 0.5)}
    rows = con.execute("SELECT week, agent, cash, pay FROM agent_snap").fetchall()
    assert len(rows) > 5000
    pays = set()
    for week, agent, cash, pay in rows:
        p = people[agent]
        assert weekly(p["c"], p["c0"], number[week]) == round(cash / 100)
        assert at(p["w"], week) == round(pay / 100)
        pays.add(pay)
    assert 0 in pays and len(pays) > 3                      # someone unpaid, and more than one rate of pay


def test_cash_has_one_number_for_each_recorded_week_from_the_persons_first(recorded):
    _, con = recorded
    weeks = townview._weeks(con)
    for p in townview._people(con, 0.5):
        assert weeks[p["c0"]] == p["h"][0]                  # the week of their first record
        assert len(p["c"]) == len(weeks) - p["c0"]
        assert weekly(p["c"], p["c0"], p["c0"] - 1) is None
        assert all(type(v) is int for v in p["c"])


def test_money_is_in_whole_dollars_from_the_week_of_the_first_record():
    con = blank()
    con.execute("INSERT INTO agent_static (agent, arrived) VALUES (1, 0), (2, 3)")
    for week in range(6):
        person_row(con, week, 1, cash=100 * week, pay=100_000)
    for week, cash, pay in ((3, 12_345, 104_000), (4, 12_399, 104_000), (5, 151, 0)):
        person_row(con, week, 2, cash=cash, pay=pay)
    first, second = townview._people(con, 0.5)
    assert (first["c0"], first["c"], first["w"]) == (0, [0, 1, 2, 3, 4, 5], [0, 1000])
    assert (second["c0"], second["c"], second["w"]) == (3, [123, 124, 2], [3, 1040, 5, 0])


def test_a_week_with_no_record_of_someone_keeps_their_cash_as_it_was():
    """It cannot happen in a run, where everyone in town is recorded together. If it ever
    did, the list must not slip a week: every later number would be the wrong week's."""
    con = blank()
    con.execute("INSERT INTO agent_static (agent, arrived) VALUES (1, 0), (2, 0)")
    for week in range(4):
        person_row(con, week, 1, cash=1000 * week)
    for week in (0, 1, 3):
        person_row(con, week, 2, cash=5000 + 100 * week)
    _, second = townview._people(con, 0.5)
    assert (second["c0"], second["c"]) == (0, [50, 51, 51, 53])


def test_someone_never_recorded_has_no_money_on_the_page():
    con = blank()
    con.execute("INSERT INTO agent_static (agent, arrived) VALUES (1, 0), (2, 2)")
    for week in range(3):
        person_row(con, week, 1)
    _, never = townview._people(con, 0.5)
    assert (never["c0"], never["c"], never["w"]) == (3, [], [])
    assert weekly(never["c"], never["c0"], 2) is None


# --- the firms ------------------------------------------------------------------------------------
def blank():
    """An empty record with the real tables, for rows made by hand."""
    con = sqlite3.connect(":memory:")
    con.executescript(TABLES)
    return con


def firm_row(con, week, firm, spot=None, staff=0, customers=0, price=0):
    con.execute("INSERT INTO firm_snap (week, firm, spot, staff, customers, price) VALUES (?,?,?,?,?,?)",
                (week, firm, spot, staff, customers, price))


def person_row(con, week, agent, home=None, home_firm=None, employer=None, role=None, klass="out",
               happy=1, wellbeing=0.8, rides=None, food=None, fun=None, **money):
    con.execute("INSERT INTO agent_snap (week, agent, home_spot, home_firm, employer, role, klass, happy, "
                "wellbeing, security, rides, food_firm, fun_firm, cash, pay, loan, shares_value) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (week, agent, home, home_firm, employer, role, klass, happy, wellbeing,
                 money.get("security", 0.5), rides, food, fun, money.get("cash", 0), money.get("pay", 0),
                 money.get("loan", 0), money.get("shares", 0)))


def test_recorded_weeks_are_the_snapshot_weeks(recorded):
    _, con = recorded
    assert townview._weeks(con) == list(range(0, 4 * 52 + 1))


def test_firm_tracks_read_back_as_the_record(recorded):
    _, con = recorded
    firms = townview._firms(con, townview._weeks(con))
    static = con.execute("SELECT firm, name, need, founded FROM firm_static ORDER BY firm").fetchall()
    assert [(f["id"], f["name"], f["need"], f["founded"]) for f in firms] == static
    by_id = {f["id"]: f for f in firms}
    rows = con.execute("SELECT week, firm, spot, staff, customers, price FROM firm_snap").fetchall()
    assert len(rows) > 500
    for week, firm, spot, staff, customers, price in rows:
        f = by_id[firm]
        assert at(f["s"], week) == none(spot)
        assert at(f["n"], week) == staff
        assert at(f["c"], week) == customers
        assert at(f["p"], week) == price


def test_a_firm_ends_at_the_first_recorded_week_it_is_gone():
    con = blank()
    con.execute("INSERT INTO firm_static (firm, name, need, founded) VALUES (7, 'Food 7', 'food', 3)")
    con.execute("INSERT INTO firm_static (firm, name, need, founded) VALUES (8, 'Fun 8', 'entertainment', 4)")
    for week in (3, 4, 5):
        firm_row(con, week, 7, spot=11, staff=2)
    for week in (4, 5, 6, 7, 8):
        firm_row(con, week, 8, spot=12, staff=1)
    seven, eight = townview._firms(con, list(range(9)))
    assert seven["end"] == 6                       # its last snapshot was week 5
    assert eight["end"] is None                    # still there in the last recorded week
    assert at(seven["s"], 2) is None and at(seven["s"], 5) == 11


def test_a_firm_that_was_never_snapshotted_has_already_ended():
    con = blank()
    con.execute("INSERT INTO firm_static (firm, name, need, founded) VALUES (7, 'Food 7', 'food', 3)")
    (seven,) = townview._firms(con, [0, 4, 8])     # founded and closed between two snapshot weeks
    assert seven["s"] == [] and seven["end"] == 4


# --- what stands on each spot ---------------------------------------------------------------------
def test_spot_tracks_equal_the_quarterly_record(recorded):
    _, con = recorded
    spots = townview._spots(con, townview._weeks(con))
    assert [(s["x"], s["y"]) for s in spots] == con.execute("SELECT x, y FROM spots ORDER BY spot").fetchall()
    rows = con.execute("SELECT week, spot, kind, user, homes, label FROM places").fetchall()
    assert len(rows) == 169 * 17
    seen = set()
    for week, spot, kind, user, homes, label in rows:
        s = spots[spot]
        assert at(s["k"], week) == KIND[kind], (week, spot)
        assert at(s["u"], week) == none(user), (week, spot)
        assert at(s["n"], week) == homes, (week, spot)
        assert s["label"] == (label or "")
        seen.add(kind)
    assert seen == {None, "homes", "premises", "service"}


def tracks(places=None, premises=None, homes=None, weeks=range(14), n_spots=5):
    return spot_tracks(list(weeks), n_spots, places or {}, premises or {}, homes or {})


def state(spot, week):
    return at(spot["k"], week), at(spot["u"], week), at(spot["n"], week)


def test_a_firm_shows_from_the_week_it_has_its_spot():
    spots = tracks(places={0: {}}, premises={w: {3: 9} for w in range(5, 14)})
    assert state(spots[3], 4) == (KIND[None], -1, 0)
    assert state(spots[3], 5) == (KIND["premises"], 9, 0)


def test_a_premises_whose_firm_is_gone_is_empty_until_the_next_record():
    spots = tracks(places={0: {3: ("premises", 9, 0)}, 13: {3: ("homes", 1, 4)}},
                   premises={w: {3: 9} for w in range(0, 5)})
    assert state(spots[3], 4) == (KIND["premises"], 9, 0)
    assert state(spots[3], 5) == (KIND[None], -1, 0)
    assert state(spots[3], 12) == (KIND[None], -1, 0)
    assert state(spots[3], 13) == (KIND["homes"], 1, 4)


def test_a_spot_someone_lives_on_is_homes_before_the_record_says_so():
    spots = tracks(places={0: {}}, homes={w: {2: (1, 3)} for w in range(7, 14)})
    assert state(spots[2], 6) == (KIND[None], -1, 0)
    assert state(spots[2], 7) == (KIND["homes"], 1, 3)


def test_homes_pulled_down_for_premises_show_as_premises_that_week():
    spots = tracks(places={0: {2: ("homes", 1, 8)}},
                   homes={w: {2: (1, 6)} for w in range(0, 6)},
                   premises={w: {2: 12} for w in range(6, 14)})
    assert state(spots[2], 5) == (KIND["homes"], 1, 8)
    assert state(spots[2], 6) == (KIND["premises"], 12, 0)


def test_homes_pulled_down_stay_down_when_the_new_firm_closes_in_the_same_quarter():
    spots = tracks(places={0: {2: ("homes", 1, 8)}},
                   homes={w: {2: (1, 6)} for w in range(0, 6)},
                   premises={w: {2: 12} for w in range(6, 9)})
    assert state(spots[2], 8) == (KIND["premises"], 12, 0)
    assert state(spots[2], 9) == (KIND[None], -1, 0)          # not the eight homes of the last record
    assert state(spots[2], 12) == (KIND[None], -1, 0)


def test_homes_seen_between_records_stay_when_the_tenants_leave():
    spots = tracks(places={0: {}}, homes={w: {2: (1, 3)} for w in range(7, 10)})
    assert state(spots[2], 9) == (KIND["homes"], 1, 3)
    assert state(spots[2], 10) == (KIND["homes"], 1, 3)       # empty homes are still homes


def test_a_block_has_at_least_as_many_homes_as_people_living_there():
    spots = tracks(places={0: {2: ("homes", 1, 2)}}, homes={w: {2: (1, 5)} for w in range(3, 14)})
    assert state(spots[2], 2) == (KIND["homes"], 1, 2)
    assert state(spots[2], 3) == (KIND["homes"], 1, 5)


def test_homes_follow_the_landlord_the_tenants_pay():
    spots = tracks(places={0: {2: ("homes", 1, 8)}}, homes={w: {2: (14, 6)} for w in range(4, 14)})
    assert state(spots[2], 3) == (KIND["homes"], 1, 8)
    assert state(spots[2], 4) == (KIND["homes"], 14, 8)


def test_a_quarterly_record_between_two_snapshot_weeks_is_still_used():
    spots = tracks(places={0: {}, 13: {3: ("homes", 1, 4)}}, weeks=[0, 4, 8, 12, 16, 20])
    assert state(spots[3], 12) == (KIND[None], -1, 0)
    assert state(spots[3], 16) == (KIND["homes"], 1, 4)


def test_a_town_service_stays_put():
    spots = tracks(places={0: {4: ("service", None, 0)}})
    assert all(state(spots[4], w) == (KIND["service"], -1, 0) for w in range(14))


# --- the town's numbers ---------------------------------------------------------------------------
def test_series_equal_the_record(recorded):
    _, con = recorded
    weeks = townview._weeks(con)
    series = townview._series(con, weeks)

    def record(scope, metric):
        by = dict(con.execute("SELECT week, value FROM series WHERE scope = ? AND metric = ?",
                              (scope, metric)).fetchall())
        assert len(by) >= len(weeks) - 1
        return [by.get(w) for w in weeks]

    def whole(values):
        return [None if v is None else int(v) for v in values]

    def share(values):
        return [None if v is None else round(v, 4) for v in values]

    for scope in ("all", "owner", "working", "out"):
        assert series["n"][scope] == whole(record(scope, "n"))
        assert series["unhappy"][scope] == share(record(scope, "unhappy"))
    assert series["homeless"] == whole(record("all", "homeless"))
    assert series["riders"] == share(record("all", "riders"))
    assert series["jobless"] == share(record("town", "jobless_rate"))
    assert series["destitute"] == whole(record("town", "destitute"))
    assert series["firms"] == whole(record("town", "firms"))
    assert series["wage"] == whole(record("town", "wage"))
    assert series["basket"] == whole(record("town", "basket"))
    assert max(series["n"]["all"]) == 80


def event(con, week, kind, agent=None, firm=None, amount=None, qty=None, **data):
    con.execute("INSERT INTO events (week, kind, agent, firm, amount, qty, data) VALUES (?,?,?,?,?,?,?)",
                (week, kind, agent, firm, amount, qty, json.dumps(data)))


def test_marks_are_the_first_week_of_each_moment():
    con = blank()
    con.execute("INSERT INTO firm_static (firm, name, need, founded) VALUES (6, 'Transport 6', 'transport', 25)")
    con.execute("INSERT INTO firm_static (firm, name, need, founded) VALUES (5, 'Transport 5', 'transport', 20)")
    event(con, 30, "town_full")
    event(con, 35, "town_full")
    event(con, 40, "land_scarce")
    event(con, 90, "town_failed")
    event(con, 95, "town_failed")
    assert townview._marks(con) == [
        {"week": 20, "kind": "transport", "label": "First transport firm"},
        {"week": 30, "kind": "full", "label": "Town full"},
        {"week": 40, "kind": "land", "label": "Land runs out"},
        {"week": 90, "kind": "failed", "label": "Town fails"},
    ]


def test_marks_leave_out_what_did_not_happen():
    con = blank()
    event(con, 30, "town_full")
    assert [m["kind"] for m in townview._marks(con)] == ["full"]


# --- one person's life ----------------------------------------------------------------------------
def two_people():
    con = blank()
    for agent in (1, 2):
        con.execute("INSERT INTO agent_static (agent, arrived, origin, start_cash) VALUES (?, 0, 'worker', 0)",
                    (agent,))
        for week in range(0, 14):
            person_row(con, week, agent)
    return con


def lives(con):
    people = townview._people(con, 0.5)
    extra = townview._lives(con, people, townview._weeks(con), 13)
    return people, extra["kinds"], extra["words"]


def told(person, kinds, words):
    """A person's life events with the codes turned back into words. The last number is how
    many times it happened in the quarter (1 when the row does not say)."""
    out = []
    for row in person["life"]["events"]:
        week, code, firm, amount, a, b = row[:6]
        out.append((week, kinds[code], firm, amount, words[a] if a >= 0 else None,
                    words[b] if b >= 0 else None, row[6] if len(row) > 6 else 1))
    return out


def test_quarter_weeks_are_the_last_recorded_week_of_each_quarter():
    assert townview.quarter_weeks(list(range(0, 30))) == [13, 26, 29]       # the model's quarters end at 13, 26
    assert townview.quarter_weeks([0, 4, 8, 12, 16, 20, 24, 28]) == [12, 24, 28]
    assert townview.quarter_weeks(list(range(0, 30)), 12) == [12, 24, 29]   # the run's own quarter
    assert townview.quarter_weeks([]) == []


def test_life_events_are_the_persons_own_in_order(recorded):
    _, con = recorded
    people, kinds, words = lives(con)
    for p in people:
        events = told(p, kinds, words)
        assert [e[0] for e in events] == sorted(e[0] for e in events)
        assert events[0][:2] == (p["arrived"], "arrival")
        for kind in ("hire", "layoff", "moved_home", "class_change"):
            mine = con.execute("SELECT week, firm FROM events WHERE kind = ? AND agent = ? ORDER BY id",
                               (kind, p["id"])).fetchall()
            assert [(e[0], e[2]) for e in events if e[1] == kind] == [(w, none(f)) for w, f in mine]
            assert all(e[6] == 1 for e in events if e[1] == kind)             # these are never merged
    assert sum(len(p["life"]["events"]) for p in people) > 300


def test_life_events_carry_their_details():
    con = two_people()
    event(con, 2, "hire", agent=1, firm=3, amount=100000, source="resident")
    event(con, 4, "class_change", agent=1, old="out", new="working", trigger="hired")
    event(con, 6, "layoff", agent=1, firm=3, amount=100000, reason="wound_up", role="staff")
    event(con, 7, "moved_home", agent=1, firm=9, old=4, new=8, reason="cheaper")
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [
        (2, "hire", 3, 1000, "resident", None, 1),
        (4, "class_change", -1, 0, "working", None, 1),
        (6, "layoff", 3, 1000, "wound_up", None, 1),
        (7, "moved_home", 9, 0, "cheaper", None, 1),
    ]
    assert told(people[1], kinds, words) == []
    assert "hired" not in words and "staff" not in words     # details the page never shows are not sent


def test_a_share_sale_is_in_both_lives():
    con = two_people()
    event(con, 5, "share_trade", agent=1, firm=3, amount=1000, qty=47, seller=2, reason="distress")
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [(5, "share_trade", 3, 47, None, "bought", 1)]   # the reason is the seller's
    assert told(people[1], kinds, words) == [(5, "share_trade", 3, 47, "distress", "sold", 1)]


def test_what_repeats_within_a_quarter_is_told_once_with_a_count():
    con = two_people()
    event(con, 5, "missed_payment", agent=1, firm=3, amount=9785, need="housing", missed=1)
    event(con, 6, "missed_payment", agent=1, firm=4, amount=9500, need="entertainment", missed=1)
    event(con, 6, "missed_payment", agent=1, firm=3, amount=9785, need="housing", missed=2)
    event(con, 7, "missed_payment", agent=1, firm=3, amount=9785, need="housing", missed=3)
    event(con, 7, "loan_missed", agent=1, amount=5000, missed=1)
    event(con, 8, "loan_missed", agent=1, amount=5000, missed=2)
    event(con, 13, "missed_payment", agent=1, firm=3, amount=9785, need="housing", missed=1)
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [
        (5, "missed_payment", 3, 391, "housing", None, 4),       # weeks 5, 6, 7 and 13: one quarter, $391.40
        (6, "missed_payment", 4, 95, "entertainment", None, 1),
        (7, "loan_missed", -1, 100, None, None, 2),
    ]


def test_a_new_quarter_starts_a_new_line():
    con = two_people()
    event(con, 13, "missed_payment", agent=1, firm=3, amount=10000, need="housing", missed=1)
    con.execute("INSERT INTO agent_snap (week, agent, klass, happy, wellbeing, security) VALUES (14, 1, 'out', 1, 0.8, 0.5)")
    event(con, 14, "missed_payment", agent=1, firm=3, amount=10000, need="housing", missed=2)
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [(13, "missed_payment", 3, 100, "housing", None, 1),
                                             (14, "missed_payment", 3, 100, "housing", None, 1)]


def test_shares_bought_many_times_in_a_quarter_are_one_line():
    con = two_people()
    for week, qty, seller_reason in ((2, 10, "distress"), (3, 20, "unhappy"), (4, 30, "distress")):
        event(con, week, "share_trade", agent=1, firm=3, amount=1000, qty=qty, seller=2, reason=seller_reason)
    event(con, 4, "share_issue", agent=1, firm=3, amount=1000, qty=9822)
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [(2, "share_trade", 3, 60, None, "bought", 3),
                                             (4, "share_issue", 3, 9822, None, None, 1)]   # shares, not the price
    assert told(people[1], kinds, words) == [(2, "share_trade", 3, 40, "distress", "sold", 2),
                                             (3, "share_trade", 3, 20, "unhappy", "sold", 1)]


def test_a_founder_is_told_as_a_founder():
    con = two_people()
    event(con, 0, "ceo_appointed", agent=1, firm=4, amount=150000)
    event(con, 0, "firm_founded", agent=1, firm=4, amount=43000000, need="entertainment", price=9500)
    event(con, 0, "arrival", agent=1, amount=48000000, who="founder")
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [
        (0, "arrival", -1, 480000, "founder", None, 1),
        (0, "ceo_appointed", 4, 1500, None, None, 1),
        (0, "firm_founded", 4, 430000, "entertainment", None, 1),
    ]


def test_an_eviction_is_kept():
    con = two_people()
    event(con, 9, "sub_end", agent=1, firm=1, need="housing", reason="evicted", unit=31)
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [(9, "sub_end", 1, 0, "housing", "evicted", 1)]


ONE_OF_EACH = {
    "arrival": dict(amount=100000, who="worker"), "hire": dict(firm=3, amount=100000, source="outside"),
    "layoff": dict(firm=3, amount=100000, reason="laid_off", role="staff"),
    "quit": dict(firm=3, amount=100000, reason="moved", role="staff"),
    "employer_changed": dict(firm=7, amount=90000, old=3), "promotion": dict(firm=3, amount=250000),
    "demotion": dict(firm=3, amount=100000), "ceo_appointed": dict(firm=3, amount=150000),
    "firm_founded": dict(firm=9, amount=43000000, need="food"),
    "founding_blocked": dict(amount=30000000, need="transport", reason="no spot to be had"),
    "takeover": dict(firm=9, amount=1000000, buyer="resident"), "control_change": dict(firm=9),
    "class_change": dict(old="out", new="owner", trigger="founded"),
    "moved_home": dict(firm=1, old=4, new=8, reason="cheaper"),
    "sub_start": dict(firm=4, amount=9500, need="entertainment", reason="signup"),
    "sub_end": dict(firm=4, need="entertainment", reason="budget"),
    "missed_payment": dict(firm=4, amount=9500, need="entertainment", missed=1),
    "loan_missed": dict(amount=5000, missed=1), "loan_called": dict(amount=643172),
    "loan_repaid": dict(amount=22834), "default": dict(amount=592380),
    "share_trade": dict(firm=3, amount=1000, qty=47, seller=2, reason="distress"),
    "share_issue": dict(firm=3, amount=1000, qty=9822), "cash_call": dict(firm=9, amount=1575252),
    "offer_refused": dict(firm=3, amount=100000, reservation=114460), "too_far": dict(what="food"),
}


def test_one_of_each_covers_every_kind_the_page_tells():
    assert set(ONE_OF_EACH) == set(townview.LIFE_KINDS)


@pytest.mark.parametrize("kind", sorted(ONE_OF_EACH))
def test_every_kind_of_life_event_reaches_the_persons_life(kind):
    con = two_people()
    event(con, 5, kind, agent=1, **ONE_OF_EACH[kind])
    people, kinds, words = lives(con)
    assert [(e[0], e[1]) for e in told(people[0], kinds, words)] == [(5, kind)]


def test_subscription_changes_already_told_another_way_are_left_out():
    con = two_people()
    event(con, 0, "sub_start", agent=1, firm=2, amount=9500, need="food", reason="arrival")
    event(con, 3, "sub_end", agent=1, firm=1, need="housing", reason="moved")
    event(con, 3, "sub_start", agent=1, firm=1, amount=30000, need="housing", reason="moved")
    event(con, 4, "sub_end", agent=1, firm=2, need="food", reason="switch")
    event(con, 4, "sub_start", agent=1, firm=8, amount=9000, need="food", reason="switch")
    event(con, 5, "sub_end", agent=1, firm=4, need="entertainment", reason="budget")
    event(con, 6, "sub_start", agent=1, firm=4, amount=9500, need="entertainment", reason="signup")
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [
        (4, "sub_start", 8, 90, "food", "switch", 1),
        (5, "sub_end", 4, 0, "entertainment", "budget", 1),
        (6, "sub_start", 4, 95, "entertainment", "signup", 1),
    ]


def test_too_far_is_kept_only_for_a_job_or_food():
    con = two_people()
    event(con, 5, "too_far", agent=1, what="clothing")
    event(con, 6, "too_far", agent=1, what="food")
    event(con, 7, "too_far", agent=1, what="job")
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == [(6, "too_far", -1, 0, "food", None, 1),
                                             (7, "too_far", -1, 0, "job", None, 1)]


def test_events_that_repeat_every_week_are_left_out():
    con = two_people()
    event(con, 5, "credit_refused", agent=1, amount=5665, need="appliances")
    event(con, 5, "share_grant", agent=1, firm=1, amount=1000, qty=60)
    event(con, 5, "dividend", firm=2, amount=3600720, qty=54)
    people, kinds, words = lives(con)
    assert told(people[0], kinds, words) == []


def test_life_lines_are_quarterly_from_the_first_record_of_the_person(recorded):
    _, con = recorded
    weeks = townview._weeks(con)
    people = townview._people(con, 0.5)
    extra = townview._lives(con, people, weeks, 13)
    qweeks = extra["qweeks"]
    assert qweeks == townview.quarter_weeks(weeks, 13)
    assert qweeks[:3] == [13, 26, 39] and qweeks[-1] == weeks[-1]
    for p in people:
        life = p["life"]
        mine = qweeks[life["q0"]:]
        assert mine and (life["q0"] == 0 or qweeks[life["q0"] - 1] < p["h"][0] <= mine[0])
        marks = ",".join("?" * len(mine))
        rows = {r[0]: r[1:] for r in con.execute(
            "SELECT week, cash, pay, loan, shares_value, wellbeing, security FROM agent_snap "
            f"WHERE agent = ? AND week IN ({marks})", [p["id"]] + mine)}
        for name in ("cash", "pay", "loan", "shares", "well", "sec"):
            assert len(life[name]) == len(mine)
        for i, week in enumerate(mine):
            cash, pay, loan, shares, well, sec = rows[week]
            assert life["cash"][i] == round(cash / 100)
            assert life["pay"][i] == round(pay / 100)
            assert life["loan"][i] == round(loan / 100)
            assert life["shares"][i] == round(shares / 100)
            assert life["well"][i] == round(well * 100)
            assert life["sec"][i] == round(sec * 100)


def ended(outcome, last, marks=()):
    return townview._ended({"run": {"outcome": outcome, "year": 52}, "weeks": [0, last], "marks": list(marks)})


def test_how_the_run_ended_is_said_in_words():
    failed = [{"week": 57, "kind": "transport", "label": ""}, {"week": 832, "kind": "failed", "label": ""}]
    assert ended("failed", 832, failed) == "Failed in year 16.0 (week 832)."
    assert ended("survived", 3120) == "Survived 60 years."
    assert ended(None, 30) == "Unfinished run: the record stops at week 30."


# --- everything together --------------------------------------------------------------------------
def test_town_data_has_everything_the_page_draws(recorded):
    _, con = recorded
    data = townview.town_data(con)
    assert data["map"] == {"w": 13, "h": 13}
    assert data["weeks"] == townview._weeks(con)
    assert len(data["people"]) == 80 and len(data["spots"]) == 169 and len(data["firms"]) >= 4
    run_info = data["run"]
    assert (run_info["seed"], run_info["outcome"]) == (9, "survived")
    assert (run_info["cutoff"], run_info["fail"], run_info["ride"], run_info["year"]) == (0.5, 0.9, 4.0, 52)
    assert (run_info["quarter"], run_info["step"], run_info["places"]) == (13, 1, 13)
    assert set(run_info) == {"id", "seed", "outcome", "cutoff", "fail", "ride", "year", "quarter", "step", "places"}
    assert set(data) >= {"series", "marks", "qweeks", "kinds", "words", "line"}
    weekly = dict(con.execute("SELECT week, value FROM series WHERE scope = 'all' AND metric = 'unhappy'").fetchall())
    assert data["line"]["weeks"] == sorted(weekly)
    assert data["line"]["unhappy"] == [round(weekly[w], 4) for w in sorted(weekly)]
    assert all("life" in p for p in data["people"])
    json.dumps(data)                                        # everything in it can be written out


def test_a_run_without_a_map_has_no_town_data(tmp_path):
    cfg = load_config(None, ["population_cap=30", "years=1", "map_width=0"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        assert townview.town_data(con) is None
    finally:
        con.close()


def test_a_record_from_before_the_map_has_no_town_data():
    con = blank()
    con.execute("DROP TABLE spots")
    con.execute("DROP TABLE places")
    assert townview.town_data(con) is None


# --- the page -------------------------------------------------------------------------------------
def embedded(html):
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(match.group(1).replace("<\\/", "</"))


def page(run_dir):
    return (run_dir / "town.html").read_text(encoding="utf-8")


def test_the_runner_writes_the_town_view_beside_the_dashboard(recorded):
    run_dir, _ = recorded
    assert (run_dir / "town.html").exists() and (run_dir / "dashboard.html").exists()


def test_the_town_view_builds_from_the_record_alone(recorded, tmp_path):
    run_dir, _ = recorded
    shutil.copy(run_dir / "run.sqlite", tmp_path / "run.sqlite")          # nothing else is there
    path = build_town_view(tmp_path)
    assert path == tmp_path / "town.html"
    html = page(tmp_path)
    for label in ("Everyone", "Owner class", "Working class", "Out of work"):
        assert label in html
    assert "Seed 9" in html
    assert "untuned" in html.lower()
    for forbidden in ("<script src", "<link", "@import", "url(", "fetch(", "XMLHttpRequest", "import("):
        assert forbidden not in html                       # nothing is fetched: it opens offline
    assert sorted(f.name for f in tmp_path.iterdir()) == ["run.sqlite", "town.html"]


def test_the_page_carries_exactly_the_data_worked_out_from_the_record(recorded):
    run_dir, con = recorded
    assert embedded(page(run_dir)) == json.loads(json.dumps(townview.town_data(con)))


def test_the_page_runs_the_javascript_that_the_tests_run(recorded):
    run_dir, _ = recorded
    assert CORE_JS in page(run_dir)


def test_the_page_says_what_is_drawn_and_not_recorded(recorded):
    run_dir, _ = recorded
    html = page(run_dir)
    assert "Drawn, not recorded" in html
    assert "no days" in html                               # why the journeys are a picture
    assert "No home" in html
    assert 'href="dashboard.html"' in html
    for choice in ('data-mode="mood"', 'data-mode="klass"', ">Wellbeing<", ">Class<"):
        assert choice in html


def test_the_page_says_how_the_run_ended(recorded):
    run_dir, _ = recorded
    assert "Survived 4 years" in page(run_dir)


def test_the_page_says_what_the_card_of_a_person_shows(recorded):
    run_dir, _ = recorded
    html = " ".join(page(run_dir).split())
    assert "their class, their wellbeing, their cash and their pay" in html     # among what is recorded every week
    assert "<strong>The card.</strong>" in html
    assert "at the end of the week shown, after pay and bills" in html          # which cash it is
    assert "Dividends are not pay" in html


def no_map_run(tmp_path):
    cfg = load_config(None, ["population_cap=30", "years=1", "map_width=0"])
    return run(cfg, out_root=tmp_path, quiet=True)


def test_a_run_without_a_map_gets_no_town_view(tmp_path):
    run_dir = no_map_run(tmp_path)
    assert not (run_dir / "town.html").exists()
    assert build_town_view(run_dir) is None
    assert not (run_dir / "town.html").exists()


def test_a_folder_with_no_record_is_an_error_and_nothing_is_made(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_town_view(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_an_unfinished_run_still_builds(tmp_path):
    cfg = load_config(None, ["population_cap=40", "years=2"])
    rec = Recorder(tmp_path / "run.sqlite", cfg, run_id="stopped")
    town = Town(cfg, rec)
    town.run(30)
    rec.flush()                                             # stopped here: never finished
    path = build_town_view(tmp_path)
    html = path.read_text(encoding="utf-8")
    data = embedded(html)
    assert data["run"]["outcome"] is None and data["weeks"] == list(range(0, 31))
    assert "Unfinished run" in html and "week 30" in html
    rec.finish("survived", {})


def test_with_sparse_snapshots_only_the_recorded_weeks_are_on_the_page(tmp_path):
    cfg = load_config(None, ["population_cap=40", "years=1", "snapshot_every=4", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    data = embedded(page(run_dir))
    recorded_weeks = list(range(0, 53, 4))
    assert data["weeks"] == recorded_weeks
    for p in data["people"]:
        for key in "hjokmrfew":
            assert set(p[key][0::2]) <= set(recorded_weeks)
        assert len(p["c"]) == len(recorded_weeks) - p["c0"]  # one number of cash for each recorded week
    for name in ("homeless", "wage"):
        assert len(data["series"][name]) == len(recorded_weeks)
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:                                                    # week 13's record of the spots is used from week 16
        rows = con.execute("SELECT spot, kind, user, homes FROM places WHERE week = 13").fetchall()
        money = con.execute("SELECT week, agent, cash, pay FROM agent_snap").fetchall()
    finally:
        con.close()
    people = {p["id"]: p for p in data["people"]}
    number = {week: i for i, week in enumerate(recorded_weeks)}
    assert len(money) > 100
    for week, agent, cash, pay in money:                    # and it is the cash of that week, not of week number i
        p = people[agent]
        assert weekly(p["c"], p["c0"], number[week]) == round(cash / 100)
        assert at(p["w"], week) == round(pay / 100)
    assert rows
    for spot, kind, user, homes in rows:
        if kind == "service":
            assert at(data["spots"][spot]["k"], 16) == KIND["service"]


def test_the_town_command_rebuilds_the_page(recorded, capsys):
    from engine.__main__ import main
    run_dir, _ = recorded
    before = page(run_dir)
    (run_dir / "town.html").unlink()
    assert main(["town", str(run_dir)]) == 0
    assert capsys.readouterr().out.strip() == str(run_dir / "town.html")
    assert embedded(page(run_dir)) == embedded(before)


def test_the_town_command_says_so_when_there_is_no_map(tmp_path, capsys):
    from engine.__main__ import main
    run_dir = no_map_run(tmp_path)
    assert main(["town", str(run_dir)]) == 1
    assert "no map" in capsys.readouterr().err
    assert not (run_dir / "town.html").exists()


def test_the_town_command_says_so_when_there_is_no_run(tmp_path, capsys):
    from engine.__main__ import main
    assert main(["town", str(tmp_path / "nowhere")]) == 2
    assert "run.sqlite" in capsys.readouterr().err
    assert not (tmp_path / "nowhere").exists()


def test_the_dashboard_links_to_the_town_view_only_when_there_is_one(recorded, tmp_path):
    run_dir, _ = recorded
    assert 'href="town.html"' in (run_dir / "dashboard.html").read_text(encoding="utf-8")
    bare = no_map_run(tmp_path)
    assert "town.html" not in (bare / "dashboard.html").read_text(encoding="utf-8")


# --- runs that are not made the usual way --------------------------------------------------------
@pytest.fixture(scope="module")
def own_dials(tmp_path_factory):
    """A run whose year, quarter, cutoff, ride speed and failure share are not the defaults."""
    cfg = load_config(None, ["population_cap=40", "years=2", "seed=5", "happy_cutoff=0.6", "transport_speed=3",
                             "failure_unhappy_share=0.8", "weeks_per_year=48", "quarter_weeks=12",
                             "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path_factory.mktemp("dials"), quiet=True)
    return run_dir, embedded(page(run_dir))


def test_the_page_uses_the_runs_own_dials(own_dials):
    run_dir, data = own_dials
    run_info = data["run"]
    assert (run_info["cutoff"], run_info["fail"], run_info["ride"]) == (0.6, 0.8, 3.0)
    assert (run_info["year"], run_info["quarter"]) == (48, 12)
    assert data["qweeks"][:3] == [12, 24, 36]
    assert 'style="left:80%"' in page(run_dir)                 # the failure mark on the bar for everyone
    assert "wellbeing below 0.6" in page(run_dir).replace("\n  ", " ")
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        people = {p["id"]: p for p in data["people"]}
        rows = con.execute("SELECT week, agent, happy, wellbeing FROM agent_snap").fetchall()
    finally:
        con.close()
    for week, agent, happy, wellbeing in rows:
        assert at(people[agent]["m"], week) == mood_step(happy, wellbeing, 0.6)


def test_the_time_line_is_weekly_even_when_people_were_recorded_less_often(tmp_path):
    cfg = load_config(None, ["population_cap=40", "years=1", "snapshot_every=4", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    data = embedded(page(run_dir))
    assert data["weeks"] == list(range(0, 53, 4))
    assert data["line"]["weeks"] == list(range(0, 53))         # the weekly measures are complete in the record
    assert (data["run"]["step"], data["run"]["places"]) == (4, 13)
    html = page(run_dir)
    assert "every 4th week" in html and "Recorded, every week" not in html


def test_the_page_says_how_often_things_were_recorded(recorded, tmp_path):
    run_dir, _ = recorded
    html = page(run_dir)
    assert "Recorded, every week" in html and "Recorded, once a quarter" in html
    cfg = load_config(None, ["population_cap=30", "years=1", "register_every=1"])
    weekly = page(run(cfg, out_root=tmp_path, quiet=True))
    assert "Recorded, once a quarter" not in weekly
    assert "What stands on each spot is recorded every week too" in weekly


def test_with_sparse_snapshots_the_spots_follow_the_latest_quarterly_record(tmp_path):
    cfg = load_config(None, ["population_cap=40", "years=1", "snapshot_every=4", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    data = embedded(page(run_dir))
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        rows = con.execute("SELECT spot, kind, homes FROM places WHERE week = 13").fetchall()
        firm_spots = {s for (s,) in con.execute("SELECT spot FROM firm_snap WHERE week = 16 AND spot IS NOT NULL")}
        lived = {s for (s,) in con.execute("SELECT home_spot FROM agent_snap WHERE week = 16 AND home_spot IS NOT NULL")}
    finally:
        con.close()
    checked = 0
    for spot, kind, homes in rows:
        if spot in firm_spots or spot in lived:
            continue                                            # the weekly records speak for these
        expect = KIND[None] if kind == "premises" else KIND[kind]
        assert at(data["spots"][spot]["k"], 16) == expect
        checked += 1
    assert checked > 100


def test_a_file_that_is_not_a_record_is_said_plainly(tmp_path, capsys):
    from engine.__main__ import main
    (tmp_path / "run.sqlite").write_text("this is not a database", encoding="utf-8")
    assert main(["town", str(tmp_path)]) == 2
    assert "not a run record" in capsys.readouterr().err
    assert not (tmp_path / "town.html").exists()


def test_a_fault_in_the_town_view_does_not_cost_the_run_its_dashboard(tmp_path, capsys, monkeypatch):
    def broken(run_dir):
        raise KeyError("a role the page has not been told about")
    monkeypatch.setattr(townview, "build_town_view", broken)
    cfg = load_config(None, ["population_cap=30", "years=1"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    assert (run_dir / "dashboard.html").exists() and (run_dir / "summary.json").exists()
    assert not (run_dir / "town.html").exists()
    assert "town view could not be built" in capsys.readouterr().err


# --- the page's fixed text ------------------------------------------------------------------------
def test_each_row_of_the_panel_is_labelled_for_the_group_it_shows():
    from engine.townpage import TEMPLATE
    rows = re.findall(r'<tr><td>([^<]+)</td><td id="n-(\w+)"></td>.*?id="bar-(\w+)".*?id="u-(\w+)"', TEMPLATE, re.S)
    assert rows == [("Everyone", "all", "all", "all"), ("Owner class", "owner", "owner", "owner"),
                    ("Working class", "working", "working", "working"), ("Out of work", "out", "out", "out")]
    facts = re.findall(r'<dt>([^<]+)</dt><dd id="f-(\w+)"></dd>', TEMPLATE)
    assert facts == [("People with no home", "homeless"), ("Destitute", "destitute"), ("Paying for a ride", "riders"),
                     ("Jobless rate", "jobless"), ("Staff wage", "wage"), ("Weekly basket", "basket"),
                     ("Firms", "firms")]


def test_a_class_is_the_same_colour_on_the_town_view_and_the_dashboard():
    from engine import dashboard, townpage

    def colours(text):
        return re.findall(r"--series-1: (#\w+); --series-2: (#\w+); --series-3: (#\w+);", text)

    assert colours(townpage.TEMPLATE) == colours(dashboard.TEMPLATE)
    assert len(colours(townpage.TEMPLATE)) == 3                # light, dark by the system, dark by choice
