"""The pure JavaScript in the town view: reading change lists, routes along the streets,
and the week's round. Run under Node. Skipped when Node is not installed, because the
model itself needs nothing but Python."""

import json
import random
import shutil
import subprocess

import pytest

from engine.townview import CORE_JS
from test_townview import at, weekly

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node is not installed")

STREET = 0.16          # half a street, in blocks: must match TownCore.STREET
WALK = 0.03            # the share of the round a walker takes over one block
MOST_TRAVEL = 0.6


def js(script: str):
    """Run CORE_JS followed by `script` under Node. The script prints one JSON value."""
    out = subprocess.run([NODE, "-e", CORE_JS + "\n" + script], capture_output=True, text=True,
                         timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_the_numbers_the_tests_assume_are_the_ones_in_the_page():
    got = js("console.log(JSON.stringify([TownCore.STREET, TownCore.WALK, TownCore.MOST_TRAVEL]));")
    assert got == [STREET, WALK, MOST_TRAVEL]


# --- change lists ---------------------------------------------------------------------------------
def test_at_reads_a_change_list_as_the_python_reference_does():
    rng = random.Random(4)
    tracks = []
    for _ in range(40):
        weeks = sorted(rng.sample(range(0, 60), rng.randint(0, 12)))
        tracks.append([v for w in weeks for v in (w, rng.randint(-1, 9))])
    got = js(f"""
        var tracks = {json.dumps(tracks)};
        console.log(JSON.stringify(tracks.map(function (t) {{
          var out = []; for (var w = -1; w <= 61; w++) out.push(TownCore.at(t, w)); return out; }})));""")
    assert got == [[at(t, w) for w in range(-1, 62)] for t in tracks]


def test_at_on_an_empty_list_is_null():
    assert js("console.log(JSON.stringify([TownCore.at([], 0), TownCore.at([], 99)]));") == [None, None]


# --- a number for every recorded week ---------------------------------------------------------------
def test_weekly_reads_a_list_that_starts_at_a_persons_first_week_as_the_python_reference_does():
    rng = random.Random(7)
    cases = [[[rng.randint(0, 9_000_000) for _ in range(rng.randint(0, 15))], rng.randint(0, 20)] for _ in range(40)]
    got = js(f"""
        var cases = {json.dumps(cases)};
        console.log(JSON.stringify(cases.map(function (c) {{
          var out = []; for (var i = -1; i <= 40; i++) out.push(TownCore.weekly(c[0], c[1], i)); return out; }})));""")
    assert got == [[weekly(values, first, i) for i in range(-1, 41)] for values, first in cases]
    assert any(v is not None for row in got for v in row) and any(v is None for row in got for v in row)


def test_weekly_on_an_empty_list_is_null():
    assert js("console.log(JSON.stringify([TownCore.weekly([], 0, 0), TownCore.weekly([], 5, 2)]));") == [None, None]


# --- a person's own place -------------------------------------------------------------------------
def test_rnd_is_steady_and_spread_out():
    got = js("""
        var a = []; for (var i = 0; i < 2000; i++) a.push(TownCore.rnd(i, 1));
        console.log(JSON.stringify({a: a, again: TownCore.rnd(7, 1) === TownCore.rnd(7, 1),
                                    other: TownCore.rnd(7, 2) !== TownCore.rnd(7, 1)}));""")
    values = got["a"]
    assert all(0 <= v < 1 for v in values)
    assert 0.45 < sum(values) / len(values) < 0.55
    assert len({round(v, 3) for v in values}) > 800
    assert got["again"] and got["other"]


def test_a_place_in_a_block_is_inside_it_and_off_the_street():
    places = js("""
        var out = []; for (var id = 0; id < 400; id++) out.push(TownCore.inBlock(3, 5, id, 2));
        console.log(JSON.stringify(out));""")
    assert len({(round(p["x"], 3), round(p["y"], 3)) for p in places}) > 350
    for p in places:
        assert (p["bx"], p["by"]) == (3, 5)
        assert 3 + STREET < p["x"] < 4 - STREET
        assert 5 + STREET < p["y"] < 6 - STREET


def test_shrink_pulls_a_place_toward_the_middle_of_its_block():
    got = js("""
        var p = TownCore.inBlock(3, 5, 11, 2), q = TownCore.shrink(p, 0.5);
        console.log(JSON.stringify([p, q]));""")
    p, q = got
    assert (q["bx"], q["by"]) == (3, 5)
    assert q["x"] == pytest.approx(3.5 + (p["x"] - 3.5) * 0.5)
    assert q["y"] == pytest.approx(5.5 + (p["y"] - 5.5) * 0.5)


# --- routes ---------------------------------------------------------------------------------------
def routes(cases):
    return js(f"""
        var cases = {json.dumps(cases)};
        console.log(JSON.stringify(cases.map(function (c) {{
          var a = TownCore.inBlock(c[0], c[1], c[4], 1), b = TownCore.inBlock(c[2], c[3], c[4], 2);
          var pts = TownCore.route(a, b, c[5]);
          return {{a: a, b: b, pts: pts, len: TownCore.length(pts)}}; }})));""")


def test_a_route_runs_from_one_place_to_the_other_along_the_streets():
    rng = random.Random(8)
    cases = [(rng.randrange(13), rng.randrange(14), rng.randrange(13), rng.randrange(14), i,
              rng.choice([-1, -0.4, 0, 0.6, 1])) for i in range(300)]
    cases = [c for c in cases if (c[0], c[1]) != (c[2], c[3])]
    for case, r in zip(cases, routes(cases)):
        a, b, pts = r["a"], r["b"], r["pts"]
        assert pts[0] == [a["x"], a["y"]] and pts[-1] == [b["x"], b["y"]]
        assert len(pts) == 5
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            assert x0 == x1 or y0 == y1                      # every leg runs along the grid
        street_y, street_x = pts[1][1], pts[2][0]
        assert pts[2][1] == street_y and pts[3][0] == street_x
        assert abs(street_y - round(street_y)) <= STREET     # the long legs are in a street,
        assert abs(street_x - round(street_x)) <= STREET     # never through a block
        assert round(street_y) in (case[1], case[1] + 1)     # the street beside the block it left
        assert round(street_x) in (case[2], case[2] + 1)     # the street beside the block it enters
        straight = abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])
        assert straight - 1e-9 <= r["len"] <= straight + 3


def test_a_route_inside_one_block_is_a_straight_line():
    (r,) = routes([(4, 4, 4, 4, 9, 1)])
    assert r["pts"] == [[r["a"]["x"], r["a"]["y"]], [r["b"]["x"], r["b"]["y"]]]


def test_along_walks_a_route_from_start_to_end():
    got = js("""
        var pts = [[0, 0], [0, 2], [3, 2]];
        console.log(JSON.stringify([0, 0.2, 0.4, 0.7, 1, -1, 2].map(function (f) {
          return TownCore.along(pts, f); })));""")
    for point, expected in zip(got, [[0, 0], [0, 1], [0, 2], [1.5, 2], [3, 2], [0, 0], [3, 2]], strict=True):
        assert point == pytest.approx(expected)


# --- the week's round -----------------------------------------------------------------------------
ROUND = """
    function stop(bx, by, salt, stay) { var p = TownCore.inBlock(bx, by, 1, salt); p.stay = stay; return p; }
    var home = stop(2, 2, 1, 1), work = stop(6, 3, 2, 4), shop = stop(4, 7, 3, 1), back = stop(2, 2, 1, 1);
"""


def test_the_round_starts_and_ends_at_home_and_takes_the_stops_in_order():
    got = js(ROUND + """
        var plan = TownCore.plan([home, work, shop, back], TownCore.WALK, 0);
        var seen = [];
        for (var i = 0; i <= 1000; i++) {
          var w = TownCore.where(plan, i / 1000);
          var name = w.moving ? "road" : w.x === home.x && w.y === home.y ? "home"
                   : w.x === work.x && w.y === work.y ? "work" : w.x === shop.x && w.y === shop.y ? "shop" : "?";
          if (seen[seen.length - 1] !== name) seen.push(name);
        }
        console.log(JSON.stringify({seen: seen, t: plan.t}));""")
    assert got["seen"] == ["home", "road", "work", "road", "shop", "road", "home"]
    t = got["t"]
    assert t[0] == 0 and t[-1] == pytest.approx(1) and t == sorted(t) and len(t) == 8


def test_time_at_each_stop_follows_its_weight():
    got = js(ROUND + """
        var plan = TownCore.plan([home, work, shop, back], TownCore.WALK, 0);
        console.log(JSON.stringify(plan.t));""")
    stays = [got[1] - got[0], got[3] - got[2], got[5] - got[4], got[7] - got[6]]
    travel = (got[2] - got[1]) + (got[4] - got[3]) + (got[6] - got[5])
    assert sum(stays) + travel == pytest.approx(1)
    for stay, weight in zip(stays, (1, 4, 1, 1)):
        assert stay == pytest.approx((1 - travel) * weight / 7)


def test_a_rider_covers_each_leg_in_a_quarter_of_the_time():
    got = js(ROUND + """
        var walk = TownCore.plan([home, work, shop, back], TownCore.WALK, 0);
        var ride = TownCore.plan([home, work, shop, back], TownCore.WALK / 4, 0);
        console.log(JSON.stringify([walk.t, ride.t, walk.legs.map(TownCore.length)]));""")
    walk, ride, lengths = got
    for leg, blocks in enumerate(lengths):
        on_foot = walk[2 * leg + 2] - walk[2 * leg + 1]
        riding = ride[2 * leg + 2] - ride[2 * leg + 1]
        assert on_foot == pytest.approx(blocks * WALK)
        assert riding == pytest.approx(on_foot / 4)


def test_a_very_long_round_is_squeezed_so_there_is_still_time_at_each_stop():
    got = js("""
        function stop(bx, by, salt, stay) { var p = TownCore.inBlock(bx, by, 1, salt); p.stay = stay; return p; }
        var plan = TownCore.plan([stop(0, 0, 1, 1), stop(40, 40, 2, 4), stop(0, 0, 1, 1)], TownCore.WALK, 0);
        console.log(JSON.stringify(plan.t));""")
    travel = (got[2] - got[1]) + (got[4] - got[3])
    assert travel == pytest.approx(MOST_TRAVEL)
    assert got[1] - got[0] > 0.05 and got[3] - got[2] > 0.2 and got[-1] == pytest.approx(1)


def test_someone_with_nowhere_to_go_stays_home_all_week():
    got = js("""
        var home = TownCore.inBlock(2, 2, 1, 1); home.stay = 1;
        var plan = TownCore.plan([home, home], TownCore.WALK, 0);
        console.log(JSON.stringify([0, 0.3, 0.5, 0.99, 1].map(function (f) { return TownCore.where(plan, f); })));""")
    assert all(w["moving"] is False for w in got)
    assert len({(w["x"], w["y"]) for w in got}) == 1


def test_where_is_on_the_route_while_travelling():
    got = js(ROUND + """
        var plan = TownCore.plan([home, work, back], TownCore.WALK, 0);
        var mid = (plan.t[1] + plan.t[2]) / 2, w = TownCore.where(plan, mid), half = TownCore.along(plan.legs[0], 0.5);
        console.log(JSON.stringify([w, half]));""")
    w, half = got
    assert w["moving"] is True and [w["x"], w["y"]] == pytest.approx(half)


# --- numbers and dates in words -------------------------------------------------------------------
def test_pct_keeps_a_decimal_only_under_ten():
    got = js("console.log(JSON.stringify([0, 0.0211, 0.0996, 0.1, 0.4249, 0.986, 1].map(TownCore.pct)));")
    assert got == ["0%", "2.1%", "10%", "10%", "42%", "99%", "100%"]


def test_a_share_just_under_the_failure_line_is_not_rounded_up_to_it():
    got = js("""console.log(JSON.stringify([[0.896, 0.9], [0.8999, 0.9], [0.9, 0.9], [0.42, 0.9], [0.796, 0.8]]
        .map(function (c) { return TownCore.pctUnder(c[0], c[1]); })));""")
    assert got == ["89.6%", "89.9%", "90%", "42%", "79.6%"]


def test_when_text_follows_the_runs_own_year_and_quarter():
    got = js("""console.log(JSON.stringify([[0, 52, 13], [1, 52, 13], [13, 52, 13], [14, 52, 13], [52, 52, 13],
        [53, 52, 13], [700, 52, 13], [48, 48, 12], [49, 48, 12], [60, 48, 12]]
        .map(function (c) { return TownCore.whenText(c[0], c[1], c[2]); })));""")
    assert got == ["Year 1, quarter 1", "Year 1, quarter 1", "Year 1, quarter 1", "Year 1, quarter 2",
                   "Year 1, quarter 4", "Year 2, quarter 1", "Year 14, quarter 2",
                   "Year 1, quarter 4", "Year 2, quarter 1", "Year 2, quarter 1"]


def test_finding_a_recorded_week():
    got = js("""
        var weeks = [0, 4, 8, 12, 16];
        console.log(JSON.stringify({
          at: [-3, 0, 3, 4, 15, 16, 99].map(function (w) { return TownCore.indexAt(weeks, w); }),
          from: [-3, 0, 3, 4, 15, 16, 99].map(function (w) { return TownCore.indexFrom(weeks, w); }) }));""")
    assert got["at"] == [0, 0, 0, 1, 3, 4, 4]          # the last recorded week at or before
    assert got["from"] == [0, 0, 1, 1, 4, 4, 4]        # the first recorded week at or after


def test_the_point_a_life_number_comes_from():
    got = js("""
        var qweeks = [13, 26, 39, 52, 65];
        console.log(JSON.stringify([12, 13, 25, 26, 40, 65, 999].map(function (w) {
          return [TownCore.sampleAt(qweeks, 0, 5, w), TownCore.sampleAt(qweeks, 2, 3, w)]; })));""")
    #            week 12     13      25      26      40      65      999      (second person starts at the third point)
    assert got == [[-1, -1], [0, -1], [0, -1], [1, -1], [2, 0], [4, 2], [4, 2]]


# --- the week of one person -----------------------------------------------------------------------
WEEK = """
    var spots = []; for (var y = 0; y < 5; y++) for (var x = 0; x < 6; x++) spots.push({ x: x, y: y });
    function env(firmSpot, size) {
      return { W: 6, H: 5, ride: 4, spots: spots, firmSpot: firmSpot || {}, size: size || function () { return 1; } };
    }
    function person(over) {
      var p = { id: 7, h: [3, 2], j: [3, 11], o: [3, 1], k: [3, 1], m: [3, 2], r: [3, 0], f: [3, 12], e: [3, 13] };
      for (var k in over) p[k] = over[k];
      return p;
    }
    var open = { 11: 20, 12: 9, 13: 28 };      // firm -> spot: work at (2,3), food at (3,1), fun at (4,4)
    function blocks(q) { return q.plan.stops.map(function (s) { return [s.bx, s.by, s.stay]; }); }
"""


def test_nobody_is_drawn_before_they_arrive():
    assert js(WEEK + "console.log(JSON.stringify(TownCore.weekOf(person(), 2, env(open))));") is None


def test_the_week_takes_in_work_then_food_then_entertainment_and_home_again():
    got = js(WEEK + """
        var q = TownCore.weekOf(person(), 3, env(open));
        console.log(JSON.stringify({ b: blocks(q), day: q.day, home: q.home, job: q.job, klass: q.klass,
                                     mood: q.mood, rides: q.rides, role: q.role }));""")
    stops = got["b"]
    assert [s[:2] for s in stops] == [[2, 0], [2, 3], [3, 1], [4, 4], [2, 0]]
    assert [s[2] for s in stops[1:4]] == [4, 1, 1]
    assert stops[0][2] + stops[4][2] == pytest.approx(2) and 0.6 <= stops[0][2] <= 1.4
    assert (got["day"], got["home"], got["job"], got["klass"], got["mood"], got["rides"], got["role"]) == (
        1, 2, 11, 1, 2, False, 1)


def test_someone_whose_employer_has_no_premises_is_given_no_work_stop():
    got = js(WEEK + """
        var q = TownCore.weekOf(person(), 3, env({ 12: 9, 13: 28 }));
        console.log(JSON.stringify({ b: blocks(q), day: q.day }));""")
    assert [s[:2] for s in got["b"]] == [[2, 0], [3, 1], [4, 4], [2, 0]]
    assert got["day"] == 0                                    # so they are shown at home


def test_someone_with_no_job_and_no_shops_stays_home():
    got = js(WEEK + """
        var q = TownCore.weekOf(person({ j: [3, -1], f: [3, -1], e: [3, -1] }), 3, env(open));
        console.log(JSON.stringify({ b: blocks(q), day: q.day }));""")
    assert [s[:2] for s in got["b"]] == [[2, 0], [2, 0]] and got["day"] == 0


def test_someone_with_no_home_starts_and_ends_in_the_strip_under_the_map():
    got = js(WEEK + """
        var out = [];
        for (var id = 1; id <= 300; id++) {
          var q = TownCore.weekOf(person({ id: id, h: [3, -1] }), 3, env(open));
          out.push([q.plan.stops[0], q.plan.stops[q.plan.stops.length - 1], q.plan.stops.length, q.day]);
        }
        console.log(JSON.stringify(out));""")
    for first, last, count, day in got:
        assert first["by"] == 5 and last["by"] == 5           # the row under the last row of the map
        assert 5 + STREET < first["y"] < 6 - STREET and STREET < first["x"] < 6 - STREET
        assert (first["x"], first["y"]) == (last["x"], last["y"])
        assert first["bx"] == int(first["x"]) and count == 5 and day == 1
    assert len({round(f["x"], 2) for f, _, _, _ in got}) > 200     # spread along the strip, not bunched


def test_a_rider_makes_the_same_round_four_times_as_fast():
    got = js(WEEK + """
        var walk = TownCore.weekOf(person(), 3, env(open)), ride = TownCore.weekOf(person({ r: [3, 1] }), 3, env(open));
        console.log(JSON.stringify([walk.plan.t, ride.plan.t, ride.rides]));""")
    walk, ride, rides = got
    assert rides is True
    for leg in range(4):
        assert ride[2 * leg + 2] - ride[2 * leg + 1] == pytest.approx((walk[2 * leg + 2] - walk[2 * leg + 1]) / 4)


def test_a_stop_at_a_small_building_is_inside_the_building():
    got = js(WEEK + """
        var q = TownCore.weekOf(person(), 3, env(open, function (spot) { return spot === 20 ? 0.5 : 1; }));
        console.log(JSON.stringify(q.plan.stops[1]));""")
    assert abs(got["x"] - 2.5) <= 0.5 * (0.5 - STREET) and abs(got["y"] - 3.5) <= 0.5 * (0.5 - STREET)


def test_only_firms_that_exist_and_have_premises_that_week_can_be_visited():
    got = js("""
        var firms = [{ id: 1, end: null, s: [0, 14] }, { id: 2, end: 10, s: [0, 15] }, { id: 3, end: null, s: [5, 16] },
                     { id: 4, end: null, s: [0, -1, 6, 17] }, { id: 5, end: null, s: [] }];
        console.log(JSON.stringify([4, 9, 10].map(function (w) { return TownCore.firmSpots(firms, w); })));""")
    assert got == [{"1": 14, "2": 15}, {"1": 14, "2": 15, "3": 16, "4": 17}, {"1": 14, "3": 16, "4": 17}]


# --- pointing -------------------------------------------------------------------------------------
def test_a_person_is_picked_only_when_the_pointer_is_on_them():
    got = js("""
        var present = [{ x: 10, y: 10, id: 1 }, { x: 14, y: 10, id: 2 }, { x: 60, y: 60, id: 3 }];
        console.log(JSON.stringify([[11, 10, 5], [13.5, 10, 5], [30, 30, 5], [56, 60, 5], [55.9, 60, 4]]
          .map(function (c) { var q = TownCore.pickPerson(present, c[0], c[1], c[2]); return q ? q.id : null; })));""")
    assert got == [1, 2, None, 3, None]


def test_what_the_pointer_is_over():
    got = js("""
        console.log(JSON.stringify([[2.5, 3.5], [2.1, 3.5], [2.5, 3.05], [2.5, 2.95], [2.5, 0.05], [2.5, -0.1],
                                    [3.2, 5.5], [0.05, 5.5], [2.5, 5.05], [2.5, 6.5], [-0.5, 2.5], [6.5, 2.5], [2.05, 3.0]]
          .map(function (c) { return TownCore.blockAt(c[0], c[1], 6, 5); })));""")
    assert got == [
        {"type": "spot", "x": 2, "y": 3, "name": False},     # inside a block
        None,                                                 # in the street beside it
        {"type": "spot", "x": 2, "y": 3, "name": True},      # just above it: where its name is written
        {"type": "spot", "x": 2, "y": 3, "name": True},      # the same street, from the other side
        {"type": "spot", "x": 2, "y": 0, "name": True},      # the name of a block in the top row
        {"type": "spot", "x": 2, "y": 0, "name": True},
        {"type": "strip"},                                    # the band for people with no home
        None,                                                 # off its end
        {"type": "strip"},                                    # where the strip's own label is written
        None, None, None, None,
    ]


# --- one person's life in words -------------------------------------------------------------------
KINDS = ["arrival", "hire", "layoff", "quit", "employer_changed", "promotion", "demotion", "ceo_appointed",
         "firm_founded", "founding_blocked", "takeover", "control_change", "class_change", "moved_home",
         "sub_start", "sub_end", "missed_payment", "loan_missed", "loan_called", "loan_repaid", "default",
         "share_trade", "share_issue", "cash_call", "offer_refused", "too_far"]
WORDS = ["founder", "worker", "outside", "moved", "resident", "laid_off", "out_of_reach", "wound_up", "firm_failed",
         "unpaid", "ousted", "odd_reason", "poached", "founded", "food", "transport", "no spot to be had", "owner",
         "working", "out", "cheaper", "reach", "job", "housing", "switch", "needed", "signup", "entertainment",
         "budget", "cut_off", "evicted", "repossessed", "appliances", "unserved", "health", "redeveloped",
         "bought", "sold", "distress", "unhappy", "forced"]
LIFE = [
    (("arrival", -1, 480000, "founder"), "Arrived to start a firm, bringing $480,000"),
    (("arrival", -1, 927, "worker"), "Arrived for a job, bringing $927"),
    (("hire", 2, 1000, "outside"), "Hired by Food 2 at $1,000 a week"),
    (("hire", 2, 1000, "moved"), "Hired by Food 2 at $1,000 a week, leaving another job"),
    (("layoff", 2, 1000, "laid_off"), "Laid off by Food 2"),
    (("layoff", 2, 1000, "out_of_reach"), "Lost the job at Food 2: could not get there"),
    (("layoff", 2, 1000, "wound_up"), "Lost the job at Food 2: the firm was wound up"),
    (("layoff", 2, 1000, "firm_failed"), "Lost the job at Food 2: the firm failed"),
    (("layoff", 2, 1000, "unpaid"), "Lost the job at Food 2: it could not pay wages"),
    (("layoff", 2, 1000, "ousted"), "Removed as chief executive of Food 2"),
    (("layoff", 2, 1000, "odd_reason"), "Lost the job at Food 2 (odd reason)"),
    (("quit", 2, 1000, "moved"), "Left Food 2 for another job"),
    (("quit", 2, 1000, "poached"), "Left Food 2 to run another firm"),
    (("quit", 2, 1000, "founded"), "Left Food 2 to run their own firm"),
    (("employer_changed", 2, 900), "Their employer was taken over by Food 2, now paid $900 a week"),
    (("promotion", 2, 2500), "Promoted to executive at Food 2, $2,500 a week"),
    (("demotion", 2, 1000), "Moved back to staff at Food 2, $1,000 a week"),
    (("ceo_appointed", 2, 1500), "Made chief executive of Food 2, $1,500 a week"),
    (("firm_founded", 2, 430000, "food"), "Founded Food 2 (food) with $430,000"),
    (("founding_blocked", -1, 300000, "transport", "no spot to be had"),
     "Could not start a transport firm: no spot to be had"),
    (("takeover", 2, 10000), "Bought Food 2 for $10,000"),
    (("control_change", 2, 0), "Took control of Food 2"),
    (("class_change", -1, 0, "owner"), "Joined the owner class"),
    (("class_change", -1, 0, "working"), "Joined the working class"),
    (("class_change", -1, 0, "out"), "Now out of work"),
    (("moved_home", 1, 0, "cheaper"),
     "Moved to a home that costs less once rent, fares and time on the road are counted"),
    (("moved_home", 1, 0, "reach"), "Moved home to stay within reach of work"),
    (("moved_home", 1, 0, "job"), "Moved home for a job"),
    (("moved_home", 1, 0, "food"), "Moved home to be within reach of food"),
    (("sub_start", 1, 350, "housing", "signup"), "Rented a home from Housing 1"),
    (("sub_start", 2, 90, "food", "switch"), "Switched food to Food 2, $90 a week"),
    (("sub_start", 6, 53, "transport", "needed"), "Took transport from Transport 6 because they needed it, $53 a week"),
    (("sub_start", 4, 95, "entertainment", "signup"), "Began paying Entertainment 4 for entertainment, $95 a week"),
    (("sub_start", 4, 95, "entertainment", "signup", 3),
     "Began paying Entertainment 4 for entertainment, $95 a week (3 times this quarter)"),
    (("sub_end", 4, 0, "entertainment", "budget"), "Gave up entertainment: could not afford it"),
    (("sub_end", 4, 0, "entertainment", "budget", 2), "Gave up entertainment: could not afford it (2 times this quarter)"),
    (("sub_end", 2, 0, "food", "cut_off"), "Cut off by Food 2 after missed payments (food)"),
    (("sub_end", 1, 0, "housing", "evicted"), "Evicted by Housing 1 after missed rent"),
    (("sub_end", 3, 0, "appliances", "repossessed"), "Appliances 3 took back the appliances after missed payments"),
    (("sub_end", 6, 0, "transport", "unserved"), "Left Transport 6 (transport): it could not serve them"),
    (("sub_end", 5, 0, "health", "out_of_reach"), "Lost health: Health 5 was too far away"),
    (("sub_end", 1, 0, "housing", "redeveloped"), "Put out of their home: it was pulled down for premises"),
    (("missed_payment", 1, 480, "housing"), "Missed a payment to Housing 1 for housing ($480)"),
    (("missed_payment", 1, 1920, "housing", None, 4), "Missed 4 payments to Housing 1 for housing ($1,920 in all)"),
    (("loan_missed", -1, 50), "Missed a loan payment ($50)"),
    (("loan_missed", -1, 150, None, None, 3), "Missed 3 loan payments ($150 in all)"),
    (("loan_called", -1, 6432), "The bank called in their loan of $6,432"),
    (("loan_called", -1, 6432, None, None, 2), "The bank called in their loan 2 times, the largest $6,432"),
    (("loan_repaid", -1, 228), "Finished repaying the called loan"),
    (("loan_repaid", -1, 500, None, None, 2), "Finished repaying a called loan 2 times"),
    (("default", -1, 5924), "Defaulted: the bank wrote off $5,924"),
    (("share_trade", 2, 1, None, "bought"), "Bought 1 share in Food 2"),
    (("share_trade", 2, 60, None, "bought", 3), "Bought 60 shares in Food 2 in 3 purchases"),
    (("share_trade", 2, 47, "distress", "sold"), "Sold 47 shares in Food 2 to pay the bills"),
    (("share_trade", 2, 40, "distress", "sold", 2), "Sold 40 shares in Food 2 in 2 sales, to pay the bills"),
    (("share_trade", 2, 20, "unhappy", "sold"), "Sold 20 shares in Food 2, valuing them below the price"),
    (("share_trade", 2, 5, "forced", "sold"), "Sold 5 shares in Food 2 because the bank called in their loan"),
    (("share_issue", 2, 9822), "Bought 9,822 new shares in Food 2"),
    (("share_issue", 2, 9822, None, None, 2), "Bought 9,822 new shares in Food 2 in 2 purchases"),
    (("cash_call", 2, 15753), "Put $15,753 into Food 2 to keep it going"),
    (("cash_call", 2, 30000, None, None, 2), "Put $30,000 into Food 2 to keep it going, in 2 payments"),
    (("offer_refused", 2, 1000), "Turned down a job at Food 2 paying $1,000 a week"),
    (("too_far", -1, 0, "job"), "A job was too far to reach"),
    (("too_far", -1, 0, "food"), "Food was too far to reach"),
    (("hire", 99, 1000, "outside"), "Hired by a firm that has gone at $1,000 a week"),
]


def test_every_kind_of_life_event_has_a_sentence_in_the_test():
    from engine.townview import LIFE_KINDS
    assert KINDS == list(LIFE_KINDS)
    assert {case[0][0] for case in LIFE} == set(KINDS)


def test_each_recorded_event_is_told_in_the_right_words():
    rows = []
    for (kind, firm, amount, *rest), _ in LIFE:
        first = rest[0] if len(rest) > 0 else None
        second = rest[1] if len(rest) > 1 else None
        row = [5, KINDS.index(kind), firm, amount, WORDS.index(first) if first else -1,
               WORDS.index(second) if second else -1]
        if len(rest) > 2:
            row.append(rest[2])
        rows.append(row)
    got = js(f"""
        var names = {{ 1: "Housing 1", 2: "Food 2", 3: "Appliances 3", 4: "Entertainment 4", 5: "Health 5", 6: "Transport 6" }};
        var env = {{ kinds: {json.dumps(KINDS)}, words: {json.dumps(WORDS)},
                    firm: function (id) {{ return names[id] || "a firm that has gone"; }},
                    money: function (n) {{ return "$" + Math.round(n).toLocaleString("en-AU"); }} }};
        console.log(JSON.stringify({json.dumps(rows)}.map(function (e) {{ return TownCore.lifeText(e, env); }})));""")
    assert got == [text for _, text in LIFE]
