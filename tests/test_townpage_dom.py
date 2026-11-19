"""The whole town view page, loaded and driven under Node with a small stand-in for the
browser. It proves that the page's own script runs, that what it writes and draws equals
the record, and that the controls do what the page says. Skipped when Node is not
installed, because the model itself needs nothing but Python."""

import json
import re
import shutil
import sqlite3
import subprocess

import pytest

from engine.config import load_config
from engine.runner import run

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node is not installed")

EDGE = 0.2             # blank margin round the map, in blocks: must match the page

# A stand-in for the browser: just enough of a page for the town view's script to run.
# Elements remember their children, text, attributes and listeners. The canvas remembers
# what was drawn in the last frame. Nothing here knows anything about the town view.
HARNESS = r"""
"use strict";
const fs = require("fs"), vm = require("vm");
const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function element(tag) {
  const el = {
    tagName: String(tag).toUpperCase(), children: [], attrs: {}, style: {}, listeners: {}, className: "",
    own: "", parent: null, value: "", max: "", scrollTop: 0, clientWidth: 0, clientHeight: 0,
    offsetWidth: 120, offsetHeight: 40, offsetTop: 0,
    appendChild(c) { c.parent = el; c.offsetTop = 24 * el.children.length; el.children.push(c); return c; },
    removeChild(c) { el.children = el.children.filter(function (x) { return x !== c; }); return c; },
    setAttribute(k, v) { el.attrs[k] = String(v); },
    getAttribute(k) { return k in el.attrs ? el.attrs[k] : null; },
    addEventListener(type, fn) { (el.listeners[type] = el.listeners[type] || []).push(fn); },
    fire(type, evt) {
      evt = evt || {};
      if (!evt.target) evt.target = el;
      evt.preventDefault = function () { evt.prevented = true; };
      (el.listeners[type] || []).forEach(function (fn) { fn.call(el, evt); });
      return evt;
    },
    getBoundingClientRect() { return { left: 0, top: 0, width: el.clientWidth || 800, height: el.clientHeight || 600 }; },
    getComputedTextLength() { return el.textContent.length * 6.5; },
    setPointerCapture() {},
    getContext() { return ctx; },
    get textContent() { return el.own + el.children.map(function (c) { return c.textContent; }).join(""); },
    set textContent(v) { el.own = v == null ? "" : String(v); el.children = []; }
  };
  return el;
}

// The canvas: remembers what the last frame filled, stroked and wrote.
const frame = { fills: [], strokes: [], texts: [] };
let path = [];
const ctx = {
  fillStyle: "", strokeStyle: "", lineWidth: 1, font: "", globalAlpha: 1,
  clearRect() { frame.fills = []; frame.strokes = []; frame.texts = []; },
  beginPath() { path = []; },
  arc(x, y, r) { path.push({ shape: "arc", x: x, y: y, r: r }); },
  rect(x, y, w, h) { path.push({ shape: "rect", x: x + w / 2, y: y + h / 2, r: w / 2 }); },
  closePath() {                      // three corners joined up: a triangle, kept as one shape at its middle
    const c = path.slice(-3);
    if (c.length === 3 && c.every(function (p) { return p.shape === "line"; })) {
      path.splice(-3, 3, { shape: "tri", x: (c[0].x + c[1].x + c[2].x) / 3, y: (c[0].y + c[1].y + c[2].y) / 3,
                           r: (c[1].x - c[2].x) / 2 });
    }
  },
  roundRect(x, y, w, h) { path.push({ shape: "box", x: x, y: y, w: w, h: h }); },
  moveTo(x, y) { path.push({ shape: "line", x: x, y: y }); },
  lineTo(x, y) { path.push({ shape: "line", x: x, y: y }); },
  fill() { path.forEach(function (p) { frame.fills.push(Object.assign({ fill: ctx.fillStyle }, p)); }); },
  stroke() { path.forEach(function (p) { frame.strokes.push(Object.assign({ stroke: ctx.strokeStyle, width: ctx.lineWidth }, p)); }); },
  fillText(text, x, y) { frame.texts.push({ text: String(text), x: x, y: y }); },
  strokeText() {}, setTransform() {}, setLineDash() {},
  measureText(text) { return { width: String(text).length * 6 }; }
};

const ids = {};
spec.ids.forEach(function (pair) { ids[pair[0]] = element(pair[1]); ids[pair[0]].attrs.id = pair[0]; });
const modes = spec.modes.map(function (m) { const b = element("button"); b.attrs["data-mode"] = m; return b; });
ids.data.own = spec.data;
ids.mapwrap.clientWidth = spec.width || 922;
ids.line.clientWidth = spec.width || 922;
const keys = [], resizes = [], frames = [];
let clock = 1000;
const document = {
  body: element("body"),
  getElementById(id) { if (!ids[id]) throw new Error("the page has no element with id " + id); return ids[id]; },
  createElement: element,
  createElementNS(ns, tag) { return element(tag); },
  querySelectorAll(sel) { if (sel === "[data-mode]") return modes; throw new Error("unexpected selector " + sel); },
  addEventListener(type, fn) { if (type === "keydown") keys.push(fn); }
};
const window = {
  innerHeight: spec.height || 900, innerWidth: spec.width || 1300, devicePixelRatio: 1,
  addEventListener(type, fn) { if (type === "resize") resizes.push(fn); },
  matchMedia() { return { addEventListener() {} }; }
};
const sandbox = {
  document: document, window: window, console: console,
  getComputedStyle() { return { getPropertyValue(name) { return name; } }; },   // a colour is its own name
  performance: { now() { return clock; } },
  requestAnimationFrame(fn) { frames.push(fn); return frames.length; }
};
vm.createContext(sandbox);
vm.runInContext(spec.core, sandbox, { filename: "core.js" });
vm.runInContext(spec.page, sandbox, { filename: "page.js" });

function all(root, test, out) {
  out = out || [];
  root.children.forEach(function (c) { if (test(c)) out.push(c); all(c, test, out); });
  return out;
}
const DATA = JSON.parse(spec.data), W = DATA.map.w, H = DATA.map.h;
const T = {
  DATA: DATA, core: sandbox.TownCore, frame: frame, ids: ids, modes: modes,
  text(id) { return ids[id].textContent; },
  lines(id) { return ids[id].children.map(function (c) { return c.textContent; }); },   // one entry for each line
  click(id) { return ids[id].fire("click"); },
  go(i) { ids.seek.value = String(i); ids.seek.fire("input"); },
  week() { return +/Week (\d+)/.exec(ids.whensub.textContent)[1]; },
  speed(i) { ids.speeds.children[i].fire("click"); },
  mode(m) { modes.filter(function (b) { return b.attrs["data-mode"] === m; })[0].fire("click"); },
  key(key, tag) {
    const evt = { key: key, target: { tagName: tag || "BODY" }, preventDefault() { evt.prevented = true; } };
    keys.forEach(function (fn) { fn(evt); });
    return evt;
  },
  // run the animation for `seconds` of page time, 60 frames a second; returns how many frames ran
  play(seconds) {
    let n = 0;
    while (frames.length && n < Math.round(seconds * 60)) { clock += 1000 / 60; frames.shift()(clock); n++; }
    return n;
  },
  resize(width, height) {
    ids.mapwrap.clientWidth = width; ids.line.clientWidth = width; window.innerWidth = width;
    if (height) window.innerHeight = height;
    resizes.forEach(function (fn) { fn(); });
  },
  S() { return parseFloat(ids.town.style.width) / (W + 2 * spec.edge); },         // pixels to a block
  // the people drawn in the last frame, in the order drawn: where (in blocks), what colour, what shape
  people() { return frame.fills.filter(function (f) { return f.shape === "arc" || f.shape === "rect" || f.shape === "tri"; }); },
  dots() {
    const S = T.S();
    return T.people().map(function (f) {
      return { x: f.x / S - spec.edge, y: f.y / S - spec.edge, fill: f.fill, shape: f.shape };
    });
  },
  outlines() {                       // the outline drawn round each person, in the order drawn
    return frame.strokes.filter(function (s) { return s.shape === "arc" || s.shape === "rect" || s.shape === "tri"; });
  },
  point(bx, by, where) {             // a pointer event over a block: its middle, or its name in the street above
    const S = T.S();
    return { clientX: (bx + 0.5 + spec.edge) * S, clientY: (by + (where === "name" ? 0 : 0.5) + spec.edge) * S };
  },
  byClass(root, cls) { return all(root, function (c) { return (" " + c.className + " ").indexOf(" " + cls + " ") >= 0; }); },
  byTag(root, tag) { return all(root, function (c) { return c.tagName === tag.toUpperCase(); }); },
  money(n) { return (n < 0 ? "-$" : "$") + Math.abs(Math.round(n)).toLocaleString("en-AU"); }
};
const out = (function () { return eval(spec.scenario); })();
console.log(JSON.stringify(out === undefined ? null : out));
"""


def parts(html):
    """What the stand-in needs from a built page: its scripts, its ids and its mode buttons."""
    data = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1)
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert len(scripts) == 2
    body = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    ids = re.findall(r'<(\w+)[^>]*?\bid="([^"]+)"', body)
    return {"data": data.replace("<\\/", "</"), "core": scripts[0], "page": scripts[1],
            "ids": [[name, tag] for tag, name in ids] + [["data", "script"]],
            "modes": re.findall(r'data-mode="(\w+)"', body), "edge": EDGE}


class Page:
    def __init__(self, run_dir, tmp):
        self.run_dir, self.tmp = run_dir, tmp
        self.spec = parts((run_dir / "town.html").read_text(encoding="utf-8"))
        self.data = json.loads(self.spec["data"])
        (tmp / "harness.js").write_text(HARNESS, encoding="utf-8")

    def js(self, scenario, **options):
        """Load the page afresh and run `scenario` (JavaScript, with `T` in reach). Its last
        expression comes back as JSON."""
        (self.tmp / "spec.json").write_text(json.dumps({**self.spec, **options, "scenario": scenario}),
                                            encoding="utf-8")
        out = subprocess.run([NODE, str(self.tmp / "harness.js"), str(self.tmp / "spec.json")],
                             capture_output=True, text=True, timeout=180)
        assert out.returncode == 0, out.stderr[-3000:]
        return json.loads(out.stdout)

    def rows(self, sql, *args):
        con = sqlite3.connect(self.run_dir / "run.sqlite")
        try:
            return con.execute(sql, args).fetchall()
        finally:
            con.close()


def half_up(x) -> int:
    """Round as the page does (Math.round): a half goes up. Python's round sends it to the even."""
    import math
    return math.floor(x + 0.5)


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    cfg = load_config(None, ["population_cap=80", "years=4", "seed=9", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path_factory.mktemp("runs"), quiet=True)
    return Page(run_dir, tmp_path_factory.mktemp("node"))


@pytest.fixture(scope="module")
def sparse(tmp_path_factory):
    cfg = load_config(None, ["population_cap=60", "years=3", "seed=4", "snapshot_every=4", "stop_on_failure=false"])
    run_dir = run(cfg, out_root=tmp_path_factory.mktemp("sparse"), quiet=True)
    return Page(run_dir, tmp_path_factory.mktemp("node"))


# --- it loads ---------------------------------------------------------------------------------------
def test_the_page_script_runs_and_shows_the_first_week(page):
    got = page.js("""({ when: T.text("when"), sub: T.text("whensub"), people: T.text("n-all"), play: T.text("play"),
                        dots: T.dots().length, note: T.text("speednote"), back: T.text("back"), fwd: T.text("fwd"),
                        speeds: T.ids.speeds.children.map(function (b) { return b.textContent; }) })""")
    assert got == {"when": "Year 1, quarter 1", "sub": "Week 0 of 208", "people": "4", "play": "Play", "dots": 4,
                   "note": "A week takes two seconds. People make their round: home, work, shops, home.",
                   "back": "Back a week", "fwd": "Forward a week", "speeds": ["Walk", "Slow", "Fast", "Fastest"]}


def test_every_id_the_script_asks_for_is_in_the_page(page):
    asked = {name for name in re.findall(r'\$\("([\w-]+)"', page.spec["page"]) if not name.endswith("-")}
    asked |= {f"{stem}-{scope}" for stem in ("n", "u", "bar") for scope in ("all", "owner", "working", "out")}
    assert asked <= {name for name, _ in page.spec["ids"]}
    assert len(asked) >= 28


# --- the panel equals the record ----------------------------------------------------------------------
def test_the_panel_shows_the_record_at_every_week(page):
    got = page.js("""
        var out = [], names = ["n-all", "n-owner", "n-working", "n-out", "u-all", "u-owner", "u-working", "u-out",
                               "f-homeless", "f-riders", "f-jobless", "f-wage", "f-basket", "f-firms", "f-destitute"];
        for (var i = 0; i < T.DATA.weeks.length; i++) {
          T.go(i);
          out.push([T.week(), T.dots().length].concat(names.map(T.text)).concat(
            ["all", "owner", "working", "out"].map(function (s) { return T.ids["bar-" + s].style.width; })));
        }
        var fmt = { pct: [0, 0.0211, 0.2463, 0.5, 1].map(T.core.pct), money: [100000, 88612].map(function (c) { return T.money(c / 100); }) };
        ({ rows: out, fmt: fmt })""")
    assert got["fmt"] == {"pct": ["0%", "2.1%", "25%", "50%", "100%"], "money": ["$1,000", "$886"]}
    series = {(week, scope, metric): value for week, scope, metric, value in page.rows(
        "SELECT week, scope, metric, value FROM series WHERE metric IN "
        "('n','unhappy','homeless','riders','jobless_rate','wage','basket','firms','destitute')")}
    assert len(got["rows"]) == 209
    shares = set()                                      # (the record's share to four places, the text, the bar, everyone?)
    for row in got["rows"]:
        week, dots = row[0], row[1]
        n = [int(series[(week, s, "n")]) for s in ("all", "owner", "working", "out")]
        assert dots == n[0], week                       # one dot for every person in town
        assert [int(v.replace(",", "")) for v in row[2:6]] == n, week
        for k, scope in enumerate(("all", "owner", "working", "out")):
            text, bar = row[6 + k], row[17 + k]
            if n[k] == 0:
                assert text == "nobody" and bar == "0%", (week, scope)
            else:
                shares.add((round(series[(week, scope, "unhappy")], 4), text, bar, scope == "all"))
        assert int(row[10].replace(",", "")) == int(series[(week, "all", "homeless")]), week
        shares.add((round(series[(week, "all", "riders")], 4), row[11], None, False))
        shares.add((round(series[(week, "town", "jobless_rate")], 4), row[12], None, False))
        assert row[13] == f"${half_up(series[(week, 'town', 'wage')] / 100):,} a week", week   # as the page rounds
        assert row[14] == f"${half_up(series[(week, 'town', 'basket')] / 100):,} a week", week
        assert int(row[15]) == int(series[(week, "town", "firms")]), week
        assert int(row[16]) == int(series[(week, "town", "destitute")]), week
    # every share on the page is the record's number, written the page's way
    values = sorted({value for value, _, _, _ in shares})
    written = page.js(f"{json.dumps(values)}.map(function (v) {{ return [T.core.pct(v), T.core.pctUnder(v, 0.9)]; }})")
    as_text = dict(zip(values, written))
    assert len(values) > 20
    for value, text, bar, everyone in shares:
        assert text == as_text[value][1 if everyone else 0], value
        if bar is not None:
            assert float(bar.rstrip("%")) == pytest.approx(100 * value)


def test_each_row_of_the_panel_is_its_own_group(page):
    """Not everyone's share four times over: a week where the groups differ."""
    week, = page.rows("SELECT MIN(a.week) FROM series a JOIN series b ON a.week = b.week "
                      "WHERE a.scope = 'owner' AND b.scope = 'working' AND a.metric = 'n' AND b.metric = 'n' "
                      "AND a.value > 0 AND b.value > 0 AND a.value != b.value")[0]
    got = page.js(f"T.go({week}); [T.text('n-owner'), T.text('n-working'), T.text('n-all')]")
    counts = dict(page.rows("SELECT scope, value FROM series WHERE week = ? AND metric = 'n'", week))
    assert [int(v) for v in got] == [int(counts["owner"]), int(counts["working"]), int(counts["all"])]
    assert got[0] != got[1]


# --- the map equals the record ------------------------------------------------------------------------
def expected_blocks(page, week):
    """Where the record puts each person for the day: at work if their employer has premises
    that week, otherwise at home, otherwise in the strip under the map."""
    width, height = page.data["map"]["w"], page.data["map"]["h"]
    firm_spot = dict(page.rows("SELECT firm, spot FROM firm_snap WHERE week = ? AND spot IS NOT NULL", week))
    out = []
    for agent, home, employer in page.rows(
            "SELECT agent, home_spot, employer FROM agent_snap WHERE week = ? ORDER BY agent", week):
        spot = firm_spot.get(employer, home) if employer is not None else home
        out.append([spot % width, spot // width] if spot is not None else [None, height])
    return out


def test_at_the_fast_speeds_everyone_is_drawn_where_the_record_puts_them(page):
    weeks = list(range(0, 209, 13)) + [208]
    got = page.js(f"""
        T.speed(2);
        {json.dumps(weeks)}.map(function (w) {{
          T.go(w);
          return T.dots().map(function (d) {{ return [Math.floor(d.x), Math.floor(d.y)]; }}); }})""")
    for week, blocks in zip(weeks, got):
        expect = expected_blocks(page, week)
        assert len(blocks) == len(expect)
        for drawn, wanted in zip(blocks, expect):
            if wanted[0] is None:
                assert drawn[1] == wanted[1]               # the strip: any column
            else:
                assert drawn == wanted, week
    assert sum(1 for b in got[-1] if b[1] < page.data["map"]["h"]) > 40     # most on the map, not in the strip


def test_at_the_slow_speeds_the_week_starts_at_home_and_people_go_out(page):
    got = page.js("""
        function where() { return T.dots().map(function (d) { return [Math.floor(d.x), Math.floor(d.y)]; }); }
        T.speed(1); T.go(100); T.click("play");
        T.play(1.02);                                       // half a week at this speed: just into week 101
        var early = where(), week = T.week();
        T.play(1);                                          // half way through week 101
        ({ early: early, middle: where(), week: week, still: T.week() })""")
    homes = [[spot % 13, spot // 13] if spot is not None else [None, 13] for (spot,) in page.rows(
        "SELECT home_spot FROM agent_snap WHERE week = 101 ORDER BY agent")]
    assert (got["week"], got["still"]) == (101, 101)
    assert len(got["early"]) == len(homes)
    for drawn, home in zip(got["early"], homes):            # the round has hardly begun: everyone is at home
        assert drawn == home or (home[0] is None and drawn[1] == 13)
    moved = sum(1 for drawn, early in zip(got["middle"], got["early"]) if drawn != early)
    assert moved > len(homes) / 2                           # half way through most are out


def test_a_rider_has_a_dark_outline_only_while_travelling(page):
    riding = json.loads(page.spec["data"])
    for p in riding["people"]:
        p["r"] = [p["r"][0], 1]                              # this small town has no transport firm: say all ride
    got = page.js("""
        function squares() { return T.outlines().filter(function (s) { return s.stroke === "--text-primary"; }).length; }
        T.speed(2); T.go(100);
        var still = squares(), people = T.dots().length;     // the fast speeds: everyone is at a stop
        T.speed(1); T.click("play");
        var most = 0;
        for (var i = 0; i < 40; i++) { T.play(0.05); most = Math.max(most, squares()); }
        ({ still: still, people: people, most: most })""", data=json.dumps(riding))
    assert got["still"] == 0 and got["people"] > 40
    assert 0 < got["most"] < got["people"]                   # some are on the road, never everyone at once


def test_dots_wear_the_colour_of_their_wellbeing_step_or_their_class(page):
    week = 150
    got = page.js(f"""
        T.speed(2); T.go({week});
        var mood = T.dots().map(function (d) {{ return d.fill; }});
        T.mode("klass");
        var klass = T.dots().map(function (d) {{ return d.fill; }});
        T.mode("mood");
        ({{ mood: mood, klass: klass, again: T.dots().map(function (d) {{ return d.fill; }}),
           legend: T.text("legend"), pressed: T.modes.map(function (b) {{ return b.attrs["aria-pressed"]; }}) }})""")
    rows = page.rows("SELECT klass, happy, wellbeing FROM agent_snap WHERE week = ? ORDER BY agent", week)
    step = lambda happy, well: (3 if well >= 0.75 else 2) if happy else (0 if well < 0.25 else 1)   # noqa: E731
    assert got["mood"] == [f"--mood-{step(happy, well)}" for _, happy, well in rows]
    assert got["klass"] == [f"--series-{ {'owner': 1, 'working': 2, 'out': 3}[klass] }" for klass, _, _ in rows]
    assert got["again"] == got["mood"]
    assert got["pressed"] == ["true", "false"]
    assert got["legend"].startswith("WellContentUnhappyVery unhappy")


# --- time ---------------------------------------------------------------------------------------------
def test_playing_moves_at_the_speed_it_says_and_stops_at_the_end(page):
    got = page.js("""
        T.speed(2); T.click("play");
        var ran = T.play(1), after = T.week(), label = T.text("play");
        T.speed(3); T.play(60);
        ({ ran: ran, after: after, label: label, end: T.week(), endLabel: T.text("play"), slider: T.ids.seek.value })""")
    assert got["ran"] == 60 and got["label"] == "Pause"
    assert got["after"] == 6                                # six weeks a second
    assert (got["end"], got["endLabel"], str(got["slider"])) == (208, "Play", "208")


def test_play_on_the_last_week_starts_again_from_the_first(page):
    got = page.js("""T.speed(2); T.go(208); T.click("play"); T.play(0.5); [T.week(), T.text("play")]""")
    assert got[0] in (2, 3) and got[1] == "Pause"


def test_stepping_and_the_keys(page):
    got = page.js("""
        T.go(50); T.click("fwd"); var a = T.week(); T.click("back"); T.click("back"); var b = T.week();
        var right = T.key("ArrowRight", "BUTTON"), c = T.week();         // a speed button still has the focus
        T.key("ArrowLeft"); var d = T.week();
        var space = T.key(" ", "BUTTON"), playing = T.text("play");
        T.key(" "); var paused = T.text("play");
        T.key("ArrowRight", "INPUT"); var typing = T.week();             // typing a person's number
        T.go(0); T.click("back"); var first = T.week(); T.go(208); T.click("fwd");
        ({ a: a, b: b, c: c, d: d, prevented: !!space.prevented, playing: playing, paused: paused, typing: typing,
           first: first, last: T.week() })""")
    assert got == {"a": 51, "b": 49, "c": 50, "d": 49, "prevented": True, "playing": "Pause", "paused": "Play",
                   "typing": 49, "first": 0, "last": 208}


def test_the_time_line_is_the_weekly_share_unhappy(page):
    got = page.js("""
        var svg = T.byTag(T.ids.line, "svg")[0], paths = T.byTag(svg, "path");
        ({ points: (paths[0].attrs.d.match(/[ML]/g) || []).length,
           labels: T.byTag(svg, "text").map(function (t) { return t.textContent; }) })""")
    weekly = page.rows("SELECT COUNT(*) FROM series WHERE scope = 'all' AND metric = 'unhappy'")[0][0]
    assert got["points"] == weekly == 209
    assert "90%: the town fails" in got["labels"] and "0%" in got["labels"] and "Year 2" in got["labels"]


# --- pointing -----------------------------------------------------------------------------------------
def test_pointing_at_a_firms_name_shows_the_firm_and_keeps_up_with_the_week(page):
    firm, name, spot = page.rows("SELECT f.firm, s.name, f.spot FROM firm_snap f JOIN firm_static s ON s.firm = f.firm "
                                 "JOIN firm_snap g ON g.firm = f.firm AND g.week = 160 "
                                 "WHERE f.week = 100 AND (g.staff != f.staff OR g.customers != f.customers) "
                                 "ORDER BY f.staff DESC LIMIT 1")[0]           # a firm that changed between the two weeks
    got = page.js(f"""
        T.speed(2); T.go(100);
        var at = T.point({spot % 13}, {spot // 13}, "name");
        T.ids.town.fire("pointermove", at);
        var first = T.text("tip"), shown = T.ids.tip.style.display;
        T.go(160);                                           // the pointer has not moved
        var later = T.text("tip");
        T.ids.town.fire("click", at);
        var picked = T.text("detail");
        T.ids.town.fire("pointerleave");
        ({{ first: first, later: later, shown: shown, hidden: T.ids.tip.style.display, picked: picked }})""")
    staff = dict(page.rows("SELECT week, staff FROM firm_snap WHERE firm = ? AND week IN (100, 160)", firm))
    customers = dict(page.rows("SELECT week, customers FROM firm_snap WHERE firm = ? AND week IN (100, 160)", firm))
    assert staff[100] != staff[160] or customers[100] != customers[160]
    assert got["first"].startswith(name) and f"{staff[100]} staff, {customers[100]:,} customers" in got["first"]
    assert got["later"].startswith(name) and f"{staff[160]} staff, {customers[160]:,} customers" in got["later"]
    assert (got["shown"], got["hidden"]) == ("block", "none")
    assert got["picked"].startswith(name)                    # a click on the name picks the firm


def test_inside_a_crowded_firm_the_gaps_between_people_still_show_the_firm(page):
    firm, name, spot = page.rows("SELECT f.firm, s.name, f.spot FROM firm_snap f JOIN firm_static s ON s.firm = f.firm "
                                 "WHERE f.week = 150 ORDER BY f.staff DESC LIMIT 1")[0]
    got = page.js(f"""
        T.speed(2); T.go(150);
        var S = T.S(), people = T.people(), r = people[0].r;
        function nearest(x, y) {{
          var best = 1e9;
          people.forEach(function (p) {{ best = Math.min(best, Math.hypot(p.x - x, p.y - y)); }});
          return best;
        }}
        var found = null, x0 = ({spot % 13} + 0.2) * S, y0 = ({spot // 13} + 0.2) * S;
        for (var x = x0 + 0.2 * S; x < x0 + 0.8 * S && !found; x += 0.5) {{
          for (var y = y0 + 0.2 * S; y < y0 + 0.8 * S && !found; y += 0.5) {{
            var d = nearest(x, y);
            if (d > r + 3.5 && d < 7.5) found = {{ clientX: x, clientY: y, gap: d, r: r }};   // close to a dot, not on it
          }}
        }}
        if (found) {{ T.ids.town.fire("pointermove", found); found.tip = T.text("tip"); }}
        found""")
    assert got is not None, "no gap between the dots to point at: pick another week for this test"
    assert got["tip"].startswith(name)                       # the firm, not the nearest person


def test_pointing_at_a_dot_shows_the_person_and_at_the_strip_the_people_with_no_home(page):
    got = page.js("""
        T.speed(2); T.go(120);
        var S = T.S(), d = T.people()[10];
        T.ids.town.fire("pointermove", { clientX: d.x, clientY: d.y });
        var person = T.text("tip");
        T.ids.town.fire("pointermove", { clientX: 3.4 * S, clientY: (T.DATA.map.h + 0.5 + 0.2) * S });
        ({ person: person, strip: T.text("tip") })""")
    assert re.match(r"Person \d+(Owner class|Working class|Out of work)", got["person"])
    assert "Click to follow" in got["person"]
    assert got["strip"].startswith("No home")


# --- the card of a person: their money that week ---------------------------------------------------------
KLASS_WORDS = {"owner": "Owner class", "working": "Working class", "out": "Out of work"}
EVERY_DOT = """T.people().map(function (d) {
          T.ids.town.fire("pointermove", { clientX: d.x, clientY: d.y });
          return T.lines("tip"); })"""


def cash_line(cents):
    return f"Cash ${round(cents / 100):,}"


def pay_line(cents):
    return f"Pay ${round(cents / 100):,} a week" if round(cents / 100) > 0 else "No pay"


def test_the_card_of_a_person_has_their_cash_and_pay_under_their_class(page):
    week = page.rows("SELECT week FROM agent_snap WHERE pay = 0 AND week > 60 GROUP BY week "
                     "ORDER BY COUNT(*) DESC, week LIMIT 1")[0][0]       # the week with the most people unpaid
    got = page.js(f"T.speed(2); T.go({week}); {EVERY_DOT}")
    record = page.rows("SELECT agent, klass, cash, pay FROM agent_snap WHERE week = ? ORDER BY agent", week)
    assert len(got) == len(record) > 40
    for lines, (agent, klass, cash, pay) in zip(got, record):   # pointing at the middle of a dot finds that person
        assert lines[:4] == [f"Person {agent}", KLASS_WORDS[klass], cash_line(cash), pay_line(pay)]
        assert lines[-1] == "Click to follow" and len(lines) >= 6
    written = [lines[3] for lines in got]
    assert "No pay" in written and len(set(written)) > 2      # someone unpaid, and more than one rate of pay
    assert len({lines[2] for lines in got}) > len(got) / 2    # each their own cash, not one number for all


def test_someone_with_no_pay_is_said_to_have_no_pay(page):
    unpaid = json.loads(page.spec["data"])
    for p in unpaid["people"]:
        p["w"] = [p["w"][0], 0]                              # say nobody is ever paid
    got = page.js(f"T.speed(2); T.go(120); {EVERY_DOT}", data=json.dumps(unpaid))
    assert len(got) > 40
    assert all(lines[3] == "No pay" and lines[2].startswith("Cash $") for lines in got)


def test_the_card_keeps_up_with_the_week(page):
    weeks = [100, 101, 102, 103, 130]
    got = page.js(f"""
        T.speed(2); T.go(100);
        var d = T.people()[10];
        T.ids.town.fire("pointermove", {{ clientX: d.x, clientY: d.y }});
        {json.dumps(weeks)}.map(function (w) {{ T.go(w); return T.lines("tip"); }})   // the pointer has not moved""")
    cards = [(week, lines) for week, lines in zip(weeks, got) if lines and lines[0].startswith("Person ")]
    assert cards[0][0] == 100 and len(cards) >= 3            # someone is still under the pointer in later weeks
    for week, lines in cards:
        agent = int(lines[0].split()[1])
        klass, cash, pay = page.rows("SELECT klass, cash, pay FROM agent_snap WHERE week = ? AND agent = ?", week, agent)[0]
        assert lines[1:4] == [KLASS_WORDS[klass], cash_line(cash), pay_line(pay)], week
    assert len({lines[2] for _, lines in cards}) > 1          # the cash on the card moves with the week


def test_the_line_about_now_beside_a_person_is_left_as_it_was(page):
    """Their money this week is on the card. Beside a person it would sit next to the number
    of the latest quarter and look like a second answer to the same question."""
    got = page.js("""T.go(150); T.ids.who.value = "3"; T.click("go"); T.byClass(T.ids.detail, "now")[0].textContent""")
    assert got.startswith("Now: ")
    assert "Cash" not in got and "Pay $" not in got and "No pay" not in got


def test_the_hint_says_what_pointing_at_a_person_shows(page):
    assert "Point at a person to see their cash and pay that week." in page.js("""T.text("detail")""")


def test_a_small_screen_keeps_the_label_of_the_strip(page):
    got = page.js("""
        T.go(150);
        var wide = T.frame.texts.map(function (t) { return t.text; });
        T.resize(330, 700);
        ({ wide: wide, narrow: T.frame.texts.map(function (t) { return t.text; }), S: T.S() })""")
    assert got["S"] < 30
    assert any(text.startswith("No home") for text in got["wide"]) and "Bank" in got["wide"]
    assert [text for text in got["narrow"] if not text.startswith("No home")] == []    # firm names are left to the hover text
    assert any(text.startswith("No home") for text in got["narrow"])


# --- one person -----------------------------------------------------------------------------------------
def test_following_a_person_shows_their_life(page):
    person = max(page.data["people"], key=lambda p: len(p["life"]["events"]))
    life, pid = person["life"], person["id"]
    got = page.js(f"""
        T.go(150); T.ids.who.value = "{pid}"; T.click("go");
        var d = T.ids.detail, sparks = T.byClass(d, "spark"), rows = T.byTag(T.byClass(d, "life")[0], "li");
        ({{ title: T.byClass(d, "who")[0].children[0].textContent,
           lines: sparks.map(function (s) {{ return [s.children[0].textContent, s.children[2].textContent]; }}),
           asat: T.byClass(d, "asat")[0].textContent,
           now: T.byClass(d, "now")[0].textContent,
           rows: rows.map(function (li) {{ return [li.className, li.children[0].children[0].textContent,
                                                   li.children[0].children[1].textContent]; }}) }})""")
    assert got["title"] == f"Person {pid}"
    point = max(k for k in range(len(life["cash"])) if page.data["qweeks"][life["q0"] + k] <= 150)
    at_week = page.data["qweeks"][life["q0"] + point]
    assert at_week == 143                                     # the last quarter end before week 150
    money = lambda dollars: f"${dollars:,}"                   # noqa: E731
    assert got["lines"] == [
        ["Cash", money(life["cash"][point])], ["Weekly pay", money(life["pay"][point])],
        ["Debt", money(life["loan"][point])], ["Shares", money(life["shares"][point])],
        ["Wellbeing", f"{life['well'][point] / 100:.2f}"], ["Security", f"{life['sec'][point] / 100:.2f}"]]
    assert got["asat"] == "The number beside each line is its latest point, at week 143."
    klass, home = page.rows("SELECT klass, home_spot FROM agent_snap WHERE week = 150 AND agent = ?", pid)[0]
    assert got["now"].startswith("Now: " + {"owner": "Owner class", "working": "Working class", "out": "Out of work"}[klass])
    assert len(got["rows"]) == len(life["events"])
    assert [row[1] for row in got["rows"]] == [f"Year {max(1, -(-e[0] // 52))}, week {e[0]}" for e in life["events"]]
    past = [e for e in life["events"] if e[0] <= 150]
    assert [row[0] for row in got["rows"]] == [""] * (len(past) - 1) + ["latest"] + ["later"] * (len(life["events"]) - len(past))
    assert got["rows"][0][2].startswith("Arrived ")


def test_the_numbers_beside_the_life_lines_say_which_week_they_are_from(page):
    person = page.data["people"][0]
    got = page.js(f"""
        T.ids.who.value = "{person['id']}"; T.click("go");
        [5, 13, 20, 26, 208].map(function (w) {{
          T.go(w);
          return [T.byClass(T.ids.detail, "asat")[0].textContent, T.byClass(T.ids.detail, "spark")[0].children[2].textContent]; }})""")
    cash = person["life"]["cash"]
    assert got == [
        ["No point yet. The first is at week 13.", ""],
        ["The number beside each line is its latest point, at week 13.", f"${cash[0]:,}"],
        ["The number beside each line is its latest point, at week 13.", f"${cash[0]:,}"],
        ["The number beside each line is its latest point, at week 26.", f"${cash[1]:,}"],
        ["The number beside each line is its latest point, at week 208.", f"${cash[-1]:,}"],
    ]


def test_clicking_a_line_of_a_life_goes_to_its_week(page):
    person = max(page.data["people"], key=lambda p: len(p["life"]["events"]))
    k = len(person["life"]["events"]) // 2
    got = page.js(f"""
        T.ids.who.value = "{person['id']}"; T.click("go");
        var rows = T.byTag(T.byClass(T.ids.detail, "life")[0], "li");
        rows[{k}].children[0].fire("click");
        [T.week(), rows[{k}].className]""")
    assert got[0] == person["life"]["events"][k][0]
    assert got[1] in ("", "latest")                          # it has happened by the week shown


def test_a_wrong_number_clears_the_person_being_followed(page):
    got = page.js("""
        T.go(100); T.ids.who.value = "3"; T.click("go");
        var before = T.text("detail"), ringed = T.frame.strokes.filter(function (s) { return s.shape === "arc" && s.width === 2; }).length;
        T.ids.who.value = "99999"; T.click("go");
        var message = T.text("detail"), rings = T.frame.strokes.filter(function (s) { return s.shape === "arc" && s.width === 2; }).length;
        T.go(101);
        ({ before: before.slice(0, 8), ringed: ringed, message: message, rings: rings, later: T.text("detail") })""")
    assert got["before"] == "Person 3" and got["ringed"] == 1
    assert got["message"] == "There is no person 99999. People are numbered from 1 to 80."
    assert got["rings"] == 0 and got["later"] == got["message"]


def test_someone_at_random_and_clear(page):
    got = page.js("""
        T.go(100); T.click("any");
        var picked = T.byClass(T.ids.detail, "who")[0].children[0].textContent;
        T.byTag(T.byClass(T.ids.detail, "who")[0], "button")[0].fire("click");
        [picked, T.text("detail"), T.ids.who.value]""")
    assert re.fullmatch(r"Person \d+", got[0]) and str(got[2]) == got[0].split()[1]
    assert got[1].startswith("Click a person")


# --- a run that recorded people every fourth week ----------------------------------------------------------
def test_a_sparse_run_says_how_far_each_step_goes(sparse):
    got = sparse.js("""
        var first = { back: T.text("back"), fwd: T.text("fwd"), note: T.text("speednote") };
        T.go(3); T.click("fwd");
        ({ first: first, week: T.week(), sub: T.text("whensub") })""")
    assert got["first"]["back"] == "Back 4 weeks" and got["first"]["fwd"] == "Forward 4 weeks"
    assert "recorded week" in got["first"]["note"] and "every 4th week" in got["first"]["note"]
    assert got["week"] == 16 and got["sub"] == "Week 16 of 156"


def test_in_a_sparse_run_a_life_line_goes_to_the_first_recorded_week_after_it_happened(sparse):
    pid, k, week = next((p["id"], k, e[0]) for p in sparse.data["people"]
                        for k, e in enumerate(p["life"]["events"]) if e[0] % 4 and k > 0)
    got = sparse.js(f"""
        T.ids.who.value = "{pid}"; T.click("go");
        var rows = T.byTag(T.byClass(T.ids.detail, "life")[0], "li");
        rows[{k}].children[0].fire("click");
        [T.week(), rows[{k}].className]""")
    assert got[0] == week + (4 - week % 4)                   # not the week before it happened
    assert got[1] in ("latest", "")                          # so it is not shown as still to come


def test_in_a_sparse_run_the_card_has_the_money_of_the_recorded_week_shown(sparse):
    got = sparse.js(f"T.speed(2); T.go(10); [[T.week()]].concat({EVERY_DOT})")
    assert got[0] == [40]                                    # the eleventh recorded week
    record = sparse.rows("SELECT agent, klass, cash, pay FROM agent_snap WHERE week = 40 ORDER BY agent")
    assert len(got) - 1 == len(record) > 10
    for lines, (agent, klass, cash, pay) in zip(got[1:], record):
        assert lines[:4] == [f"Person {agent}", KLASS_WORDS[klass], cash_line(cash), pay_line(pay)]


def test_in_a_sparse_run_the_time_line_is_still_weekly(sparse):
    points = sparse.js("""(T.byTag(T.byTag(T.ids.line, "svg")[0], "path")[0].attrs.d.match(/[ML]/g) || []).length""")
    assert points == 157 and len(sparse.data["weeks"]) == 40


# --- class is the dot's shape (Jason, 16/11/2026, decision 14) -----------------------------------------------
def test_each_person_is_drawn_in_the_shape_of_their_class_whatever_the_colour(page):
    week = 150
    got = page.js(f"""
        T.speed(2); T.go({week});
        var mood = T.dots().map(function (d) {{ return d.shape; }});
        T.mode("klass");
        ({{ mood: mood, klass: T.dots().map(function (d) {{ return d.shape; }}), legend: T.text("legend") }})""")
    rows = page.rows("SELECT klass FROM agent_snap WHERE week = ? ORDER BY agent", week)
    shapes = [{"owner": "rect", "working": "arc", "out": "tri"}[klass] for (klass,) in rows]
    assert got["mood"] == shapes and got["klass"] == shapes
    assert {"rect", "arc"} <= set(shapes)                     # more than one class in the town that week
    assert "Owner class" in got["legend"] and "Out of work" in got["legend"]


def test_the_key_shows_the_shapes_in_both_colourings(page):
    got = page.js("""
        T.speed(2); T.go(100);
        function shapes() { return T.byClass(T.ids.legend, "key-shape").map(function (s) { return s.className; }); }
        var mood = shapes();
        T.mode("klass");
        ({ mood: mood, klass: shapes(), text: T.text("legend") })""")
    for found in (got["mood"], got["klass"]):
        assert [c.split()[-1] for c in found] == ["owner", "working", "out"]
    assert "A dark outline is someone riding" in got["text"]
