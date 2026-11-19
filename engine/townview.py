"""The town view: one HTML file per run that replays the recorded town.

Jason, 12/11/2026: "the town itself with people moving through it". The page is built
only from the run's SQLite record and fetches nothing, so it opens offline.

What the record holds is shown as recorded: where each person lives, works and shops
each week, their class and wellbeing, and what stands on each spot. What the record
does not hold is drawn and said to be drawn: the journeys inside a week (the model has
no days), and the strip where people with no home are shown.

The data is embedded as change lists: `[week, value, week, value, ...]`. A value holds
from its week until the next entry. -1 means none.

One thing changes nearly every week for nearly everyone, and a change list would only make
it longer: a person's cash. It is embedded as one number for each recorded week, from the
person's first.
"""

from __future__ import annotations

import html
import json
import pathlib
import sqlite3

from .config import WORLD_NAMES
from .townpage import CORE_JS, PAGE_JS, TEMPLATE

NONE = -1
KLASS = {"owner": 0, "working": 1, "out": 2}
ROLE = {None: 0, "staff": 1, "exec": 2, "ceo": 3}


def _push(track: list, week: int, value) -> None:
    """Add a week's value to a change list, if it differs from the one in force."""
    value = NONE if value is None else value
    if not track or track[-1] != value:
        track.append(week)
        track.append(value)


def encode(pairs) -> list:
    """`[(week, value), ...]` in week order as a change list."""
    track: list = []
    for week, value in pairs:
        _push(track, week, value)
    return track


def mood_step(happy, wellbeing: float, cutoff: float) -> int:
    """0 very unhappy, 1 unhappy, 2 content, 3 well. The recorded happy flag decides the
    side, so the picture can never disagree with the count; the number decides the depth."""
    if happy:
        return 3 if wellbeing >= (1.0 + cutoff) / 2.0 else 2
    return 0 if wellbeing < cutoff / 2.0 else 1


def _people(con, cutoff: float, weeks: list[int] | None = None) -> list[dict]:
    """Every person, with a change list for each thing the page draws about them.

    Their money, for the card (Jason, 13/11/2026): `w` is their weekly pay as a change list,
    and `c` is their cash, one number for each recorded week from their first, which is
    recorded week number `c0`. Both are in whole dollars."""
    weeks = _weeks(con) if weeks is None else weeks
    number = {week: i for i, week in enumerate(weeks)}
    people: dict[int, dict] = {}
    for agent, arrived in con.execute("SELECT agent, arrived FROM agent_static ORDER BY agent"):
        people[agent] = {"id": agent, "arrived": arrived,
                         "h": [], "j": [], "o": [], "k": [], "m": [], "r": [], "f": [], "e": [],
                         "w": [], "c0": len(weeks), "c": []}
    for (week, agent, home, employer, role, klass, happy, wellbeing, rides, food, fun, cash, pay) in con.execute(
            "SELECT week, agent, home_spot, employer, role, klass, happy, wellbeing, rides, food_firm, "
            "fun_firm, cash, pay FROM agent_snap ORDER BY week, agent"):
        p = people[agent]
        _push(p["h"], week, home)
        _push(p["j"], week, employer)
        _push(p["o"], week, ROLE[role])
        _push(p["k"], week, KLASS[klass])
        _push(p["m"], week, mood_step(happy, wellbeing, cutoff))
        _push(p["r"], week, 0 if rides is None else 1)
        _push(p["f"], week, food)
        _push(p["e"], week, fun)
        _push(p["w"], week, round((pay or 0) / 100))
        held = p["c"]
        if not held:
            p["c0"] = number[week]
        held.extend(held[-1:] * (number[week] - p["c0"] - len(held)))   # a week with no record of them: as it was
        held.append(round((cash or 0) / 100))
    return [people[agent] for agent in sorted(people)]


def _weeks(con) -> list[int]:
    """The recorded weeks, in order: the weeks of the agent and firm snapshots."""
    return [w for (w,) in con.execute(
        "SELECT week FROM agent_snap UNION SELECT week FROM firm_snap ORDER BY 1")]


def _firms(con, weeks: list[int]) -> list[dict]:
    """Every firm that ever existed. `end` is the first recorded week it is gone, or None."""
    firms: dict[int, dict] = {}
    for firm, name, need, founded in con.execute(
            "SELECT firm, name, need, founded FROM firm_static ORDER BY firm"):
        firms[firm] = {"id": firm, "name": name, "need": need, "founded": founded, "end": None,
                       "s": [], "n": [], "c": [], "p": []}
    last: dict[int, int] = {}
    for week, firm, spot, staff, customers, price in con.execute(
            "SELECT week, firm, spot, staff, customers, price FROM firm_snap ORDER BY week, firm"):
        f = firms[firm]
        _push(f["s"], week, spot)
        _push(f["n"], week, staff)
        _push(f["c"], week, customers)
        _push(f["p"], week, price)
        last[firm] = week
    for firm, f in firms.items():
        if firm in last:
            f["end"] = next((w for w in weeks if w > last[firm]), None)
        else:                                        # opened and closed between two records
            f["end"] = next((w for w in weeks if w >= f["founded"]), None)
    return [firms[firm] for firm in sorted(firms)]


KIND = {None: 0, "homes": 1, "premises": 2, "service": 3}


def spot_tracks(weeks, n_spots: int, places: dict, premises: dict, homes: dict) -> list[dict]:
    """What stands on each spot each recorded week, as change lists: kind, user firm, homes.

    `places` is the quarterly record, `{week: {spot: (kind, user, homes)}}`. Between records
    the weekly snapshots fill in: `premises` is `{week: {spot: firm}}` and `homes` is
    `{week: {spot: (landlord, people living there)}}`. The rule:
    a firm that has the spot that week makes it premises; a premises whose firm no longer
    has the spot is empty; a spot someone lives on is homes, with at least as many homes
    as people living there. What is worked out one week is kept the next, until a
    quarterly record says what is really there."""
    out = [{"k": [], "u": [], "n": []} for _ in range(n_spots)]
    records = sorted(places)
    nothing = (None, None, 0)
    now: dict = {}                                   # what the page takes to stand on each spot
    for week in weeks:
        while records and records[0] <= week:        # the latest quarterly record: start again from it
            now = dict(places[records.pop(0)])
        firms_here = premises.get(week, {})
        living = homes.get(week, {})
        for spot in range(n_spots):
            kind, user, count = now.get(spot, nothing)
            if spot in firms_here:
                kind, user, count = "premises", firms_here[spot], 0
            else:
                if kind == "premises":
                    kind, user, count = nothing
                if spot in living:
                    landlord, heads = living[spot]
                    count = max(count if kind == "homes" else 0, heads)
                    kind, user = "homes", landlord if landlord is not None else user
            now[spot] = (kind, user, count)
            tracks = out[spot]
            _push(tracks["k"], week, KIND[kind])
            _push(tracks["u"], week, user)
            _push(tracks["n"], week, count)
    return out


def _spots(con, weeks: list[int]) -> list[dict]:
    """Every spot: where it is, the town service on it if any, and what stands on it over time."""
    where = con.execute("SELECT spot, x, y FROM spots ORDER BY spot").fetchall()
    places: dict[int, dict] = {}
    labels: dict[int, str] = {}
    for week, spot, kind, user, count, label in con.execute(
            "SELECT week, spot, kind, user, homes, label FROM places"):
        places.setdefault(week, {})[spot] = (kind, user, count)
        if label:
            labels[spot] = label
    premises: dict[int, dict] = {}
    for week, firm, spot in con.execute("SELECT week, firm, spot FROM firm_snap WHERE spot IS NOT NULL"):
        premises.setdefault(week, {})[spot] = firm
    homes: dict[int, dict] = {}
    for week, spot, landlord, heads in con.execute(
            "SELECT week, home_spot, MIN(home_firm), COUNT(*) FROM agent_snap "
            "WHERE home_spot IS NOT NULL GROUP BY week, home_spot"):
        homes.setdefault(week, {})[spot] = (landlord, heads)
    tracks = spot_tracks(weeks, len(where), places, premises, homes)
    return [{"x": x, "y": y, "label": labels.get(spot, ""), **tracks[i]}
            for i, (spot, x, y) in enumerate(where)]


SCOPES = ("all", "owner", "working", "out")


def _series(con, weeks: list[int]) -> dict:
    """The weekly town numbers the side panel and the time line show, one value per recorded week."""
    by: dict[tuple[str, str], dict[int, float]] = {}
    for week, scope, metric, value in con.execute(
            "SELECT week, scope, metric, value FROM series WHERE metric IN "
            "('n', 'unhappy', 'homeless', 'riders', 'jobless_rate', 'destitute', 'firms', 'wage', 'basket')"):
        by.setdefault((scope, metric), {})[week] = value

    def whole(scope, metric):
        values = by.get((scope, metric), {})
        return [int(values[w]) if w in values else None for w in weeks]

    def share(scope, metric):
        values = by.get((scope, metric), {})
        return [round(values[w], 4) if w in values else None for w in weeks]

    return {
        "n": {scope: whole(scope, "n") for scope in SCOPES},
        "unhappy": {scope: share(scope, "unhappy") for scope in SCOPES},
        "homeless": whole("all", "homeless"),
        "riders": share("all", "riders"),
        "jobless": share("town", "jobless_rate"),
        "destitute": whole("town", "destitute"),
        "firms": whole("town", "firms"),
        "wage": whole("town", "wage"),
        "basket": whole("town", "basket"),
    }


def _marks(con) -> list[dict]:
    """The moments marked on the time line: only those that happened, in week order."""
    def first(kind):
        return con.execute("SELECT MIN(week) FROM events WHERE kind = ?", (kind,)).fetchone()[0]

    found = [
        (con.execute("SELECT MIN(founded) FROM firm_static WHERE need = 'transport'").fetchone()[0],
         "transport", "First transport firm"),
        (first("town_full"), "full", "Town full"),
        (first("land_scarce"), "land", "Land runs out"),
        (first("town_failed"), "failed", "Town fails"),
    ]
    return [{"week": week, "kind": kind, "label": label}
            for week, kind, label in sorted(f for f in found if f[0] is not None)]


def _line(con) -> dict:
    """The share of everyone who is unhappy, for every week the run measured. The weekly
    measures are complete in the record however often people were snapshotted."""
    rows = con.execute("SELECT week, value FROM series WHERE scope = 'all' AND metric = 'unhappy' "
                       "ORDER BY week").fetchall()
    return {"weeks": [week for week, _ in rows], "unhappy": [round(value, 4) for _, value in rows]}


def _quarter_of(week: int, quarter: int) -> int:
    """Which quarter a week falls in. The model's quarters end on weeks 13, 26, 39 and so on;
    week 0, when the founders arrive, is in the first."""
    return (max(week, 1) - 1) // quarter


def quarter_weeks(weeks: list[int], quarter: int = 13) -> list[int]:
    """The last recorded week of each quarter: where the life lines are sampled."""
    last: dict[int, int] = {}
    for week in weeks:
        last[_quarter_of(week, quarter)] = week
    return [last[q] for q in sorted(last)]


# The events told in a person's life, and which two details of each are kept as words.
LIFE_KINDS = {
    "arrival": ("who", None), "hire": ("source", None), "layoff": ("reason", None),
    "quit": ("reason", None), "employer_changed": (None, None), "promotion": (None, None),
    "demotion": (None, None), "ceo_appointed": (None, None), "firm_founded": ("need", None),
    "founding_blocked": ("need", "reason"), "takeover": (None, None), "control_change": (None, None),
    "class_change": ("new", None), "moved_home": ("reason", None), "sub_start": ("need", "reason"),
    "sub_end": ("need", "reason"), "missed_payment": ("need", None), "loan_missed": (None, None),
    "loan_called": (None, None), "loan_repaid": (None, None), "default": (None, None),
    "share_trade": ("reason", None), "share_issue": (None, None), "cash_call": (None, None),
    "offer_refused": (None, None), "too_far": ("what", None),
}
_SHARES = ("share_trade", "share_issue")            # their amount is a number of shares, not money
# Events that can come week after week. Within one quarter each is told once, with a count.
# The value says what the one line's amount is: the total, the largest or the latest.
_REPEATS = {"missed_payment": "sum", "loan_missed": "sum", "share_trade": "sum", "share_issue": "sum",
            "cash_call": "sum", "loan_repaid": "sum", "loan_called": "max", "sub_start": "last",
            "sub_end": "last", "too_far": "last"}


def _told_another_way(kind: str, data: dict) -> bool:
    """Events that only repeat what another line in the same life already says."""
    if kind == "sub_start":
        return data.get("reason") in ("arrival", "moved")       # 'Arrived' and 'Moved home' say it
    if kind == "sub_end":
        return data.get("reason") in ("moved", "switch")        # the new subscription says it
    if kind == "too_far":
        return data.get("what") not in ("job", "food")
    return False


def _lives(con, people: list[dict], weeks: list[int], quarter: int = 13) -> dict:
    """Give each person their life: quarterly lines from their first record, and what happened
    to them in order. Returns what the page needs to read them: the quarter weeks, the kinds
    of event and the table of words.

    An event is `[week, kind, firm, amount, word, word]`. One that stands for several in the
    same quarter has a seventh number, how many, and is dated by the first of them."""
    by_id = {p["id"]: p for p in people}
    qweeks = quarter_weeks(weeks, quarter)
    for p in people:
        p["life"] = {"q0": len(qweeks), "cash": [], "pay": [], "loan": [], "shares": [], "well": [],
                     "sec": [], "events": []}
    if qweeks:
        marks = ",".join("?" * len(qweeks))
        index = {week: i for i, week in enumerate(qweeks)}
        for week, agent, cash, pay, loan, shares, well, sec in con.execute(
                "SELECT week, agent, cash, pay, loan, shares_value, wellbeing, security FROM agent_snap "
                f"WHERE week IN ({marks}) ORDER BY week, agent", qweeks):
            life = by_id[agent]["life"]
            life["q0"] = min(life["q0"], index[week])
            life["cash"].append(round((cash or 0) / 100))
            life["pay"].append(round((pay or 0) / 100))
            life["loan"].append(round((loan or 0) / 100))
            life["shares"].append(round((shares or 0) / 100))
            life["well"].append(round((well or 0.0) * 100))
            life["sec"].append(round((sec or 0.0) * 100))

    kinds = list(LIFE_KINDS)
    code = {kind: i for i, kind in enumerate(kinds)}
    words: dict[str, int] = {}
    merged: dict[tuple, list] = {}                   # (person, kind, firm, words) -> [quarter, row, size so far]

    def word(text) -> int:
        if text is None:
            return NONE
        return words.setdefault(str(text), len(words))

    def tell(person: dict, week: int, kind: str, firm, size: int, first: int, second: int) -> None:
        """Add one event to a person's life, or fold it into the line that already tells it."""
        firm = NONE if firm is None else firm
        how = _REPEATS.get(kind)
        key = (person["id"], kind, firm, first, second)
        this = _quarter_of(week, quarter)
        held = merged.get(key) if how else None
        if held is not None and held[0] == this:
            row = held[1]
            held[2] = held[2] + size if how == "sum" else max(held[2], size) if how == "max" else size
            row[3] = held[2] if kind in _SHARES else round(held[2] / 100)
            if len(row) == 6:
                row.append(1)
            row[6] += 1
            return
        row = [week, code[kind], firm, size if kind in _SHARES else round(size / 100), first, second]
        if how:
            merged[key] = [this, row, size]
        if kind == "arrival":                        # told first, whatever came with it that week
            person["life"]["events"].insert(0, row)
        else:
            person["life"]["events"].append(row)

    marks = ",".join("?" * len(kinds))
    for week, kind, agent, firm, amount, qty, text in con.execute(
            f"SELECT week, kind, agent, firm, amount, qty, data FROM events "
            f"WHERE agent IS NOT NULL AND kind IN ({marks}) ORDER BY id", kinds):
        data = json.loads(text) if text else {}
        if _told_another_way(kind, data) or agent not in by_id:
            continue
        first, second = LIFE_KINDS[kind]
        size = (qty or 0) if kind in _SHARES else (amount or 0)
        if kind == "share_trade":                    # one sale, two lives; the reason is the seller's
            tell(by_id[agent], week, kind, firm, size, NONE, word("bought"))
            seller = by_id.get(data.get("seller"))
            if seller is not None:
                tell(seller, week, kind, firm, size, word(data.get("reason")), word("sold"))
            continue
        tell(by_id[agent], week, kind, firm, size,
             word(data.get(first)) if first else NONE, word(data.get(second)) if second else NONE)
    return {"qweeks": qweeks, "kinds": kinds, "words": sorted(words, key=words.get)}


def town_data(con) -> dict | None:
    """Everything the page draws, from the record alone. None when the run has no map."""
    try:
        where = con.execute("SELECT MAX(x), MAX(y) FROM spots").fetchone()
    except sqlite3.OperationalError:
        return None                                  # a record from before the map
    weeks = _weeks(con)
    if where[0] is None or not weeks:
        return None
    meta = dict(con.execute("SELECT key, value FROM run").fetchall())
    cfg = json.loads(meta.get("config") or "{}")
    cutoff = cfg.get("happy_cutoff", 0.5)
    quarter = cfg.get("quarter_weeks", 13)
    people = _people(con, cutoff, weeks)
    data = {
        "run": {
            "id": meta.get("run_id", ""), "seed": int(meta.get("seed") or 0),
            "outcome": meta.get("outcome"), "cutoff": cutoff,
            "fail": cfg.get("failure_unhappy_share", 0.9), "ride": cfg.get("transport_speed", 4.0),
            "year": cfg.get("weeks_per_year", 52), "quarter": quarter,
            "step": cfg.get("snapshot_every", 1),     # weeks between records of people and firms
            "places": cfg.get("register_every", 13),  # weeks between records of what stands on each spot
        },
        "map": {"w": where[0] + 1, "h": where[1] + 1},
        "weeks": weeks,
        "people": people,
        "firms": _firms(con, weeks),
        "spots": _spots(con, weeks),
        "series": _series(con, weeks),
        "line": _line(con),
        "marks": _marks(con),
    }
    data.update(_lives(con, people, weeks, quarter))
    return data


# --- the page -----------------------------------------------------------------------------------
def _ended(data: dict) -> str:
    """How the run ended, in a sentence."""
    run_info, last = data["run"], data["weeks"][-1]
    failed = next((m["week"] for m in data["marks"] if m["kind"] == "failed"), None)
    if run_info["outcome"] is None:
        return f"Unfinished run: the record stops at week {last}."
    if failed is not None:
        return f"Failed in year {failed / run_info['year']:.1f} (week {failed})."
    return f"Survived {last / run_info['year']:.0f} years."


def _every(weeks: int) -> str:
    """'every week', 'every 4th week'."""
    if weeks == 1:
        return "every week"
    ending = "th" if 10 <= weeks % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(weeks % 10, "th")
    return f"every {weeks}{ending} week"


def _header(data: dict) -> str:
    e = html.escape
    run_info, where = data["run"], data["map"]
    return f"""
<header>
  <h1>The __WORLD__: the town, week by week</h1>
  <div class="sub">Run {e(str(run_info['id']))}. Seed {e(str(run_info['seed']))}. {e(_ended(data))}
  The town on a {where['w']} by {where['h']} map.
  <a href="dashboard.html">The dashboard for this run</a></div>
  <div class="notice" role="note">
    <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5 15 14H1z" fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6v4M8 11.6v.6"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    <span><strong>Untuned.</strong> The build so far proves the machinery: the accounts balance and every
    week is recorded. The starting values have not been tested, so watch this as a first look, not a
    finding.</span>
  </div>
</header>
"""


def _footer(meta: dict, data: dict, events: int) -> str:
    e = html.escape
    run_info = data["run"]
    step, places, quarter = run_info["step"], run_info["places"], run_info["quarter"]
    sparse = ("" if step == 1 else
              f" The page moves {step} weeks at a time, because that is how often this run recorded people."
              " The time line under the map is weekly.")
    between = ("Between those records a firm is drawn from the week it has its spot, and homes from the "
               "week someone lives there.")
    if places == 1:
        spots = "<p>What stands on each spot is recorded every week too.</p>"
    elif places == quarter:
        spots = f"<p><strong>Recorded, once a quarter.</strong> What stands on each spot. {between}</p>"
    else:
        spots = f"<p><strong>Recorded, every {places} weeks.</strong> What stands on each spot. {between}</p>"
    return f"""
<footer>
  <h2>How to read this</h2>
  <p><strong>Recorded, {_every(step)}.</strong> Where each person lives and works, which food firm and which
  entertainment firm they pay, their class, their wellbeing, their cash and their pay, and whether they pay
  for a ride. Each firm's spot, staff, customers and price. The numbers in the panel.{sparse}</p>
  {spots}
  <p><strong>Drawn, not recorded.</strong> The journeys. The model works in whole weeks and has no days, so
  each week is drawn as one round: home, work, the food shop, the entertainment firm, home. Journeys are
  drawn slower than they would be so that they can be seen. A person who pays for a ride moves
  {e(f"{run_info['ride']:g}")} times as fast as a walker, as in the model. A round too long to fit in the
  week is hurried so that it does. Where a dot sits inside a block is also drawn: it is that person's own
  place, the same every week.</p>
  <p><strong>No home.</strong> The model gives a person with no home no place on the map. They are drawn in
  the strip under the map, and their round starts and ends there.</p>
  <p><strong>One person.</strong> The lines beside a person have one point a quarter. The number beside
  each line is its latest point, and the page says which week that point is. What happened to them is
  from the record. Something that happened several times in one quarter is told once, with how many
  times.</p>
  <p><strong>The card.</strong> Point at a person to see their card. Under their class it gives their cash
  and their pay. Cash is what they hold at the end of the week shown, after pay and bills. Pay is what
  their job pays a week. Dividends are not pay and are not on the card. Both numbers are for the week
  shown, so the cash can differ from the line beside a person, which has one point a quarter.</p>
  <p><strong>Class is by role.</strong> Owner class: founders, anyone who controls a firm, chief executives,
  executives, and people living on dividends alone. Working class: staff drawing a wage, with or without
  shares. Out of work: everyone else. <strong>Unhappy</strong> means wellbeing below {e(f"{run_info['cutoff']:g}")}.
  The town fails when {e(f"{100 * run_info['fail']:g}")}% of everyone is unhappy.</p>
  <p><strong>Keys.</strong> Space plays and pauses. The left and right arrows step back and forward.</p>
  <p class="fine">Built only from run.sqlite. {events:,} events recorded.
  Record fingerprint {e(str(meta.get('fingerprint', 'not finished'))[:16])}.
  Code fingerprint {e(str(meta.get('code_fingerprint', '')))}.</p>
</footer>
"""


def build_town_view(run_dir) -> pathlib.Path | None:
    """Write town.html in the run folder, from run.sqlite alone. Returns its path, or None
    (and writes nothing) when the run has no map."""
    run_dir = pathlib.Path(run_dir)
    record = run_dir / "run.sqlite"
    if not record.is_file():
        raise FileNotFoundError(f"no run.sqlite in {run_dir}")
    con = sqlite3.connect(record)
    try:
        data = town_data(con)
        if data is None:
            return None
        meta = dict(con.execute("SELECT key, value FROM run").fetchall())
        events = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    finally:
        con.close()
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    world = WORLD_NAMES.get(json.loads(meta.get("config", "{}")).get("world", "wef"), "WEF world")
    page = (TEMPLATE
            .replace("__TITLE__", html.escape(f"{world} town {data['run']['id'] or run_dir.name}"))
            .replace("__HEADER__", _header(data).replace("__WORLD__", world))
            .replace("__FOOTER__", _footer(meta, data, events))
            .replace("__FAIL__", f"{100 * data['run']['fail']:g}")
            .replace("__CORE__", CORE_JS)
            .replace("__PAGE__", PAGE_JS)
            .replace("__DATA__", payload))
    out = run_dir / "town.html"
    out.write_text(page, encoding="utf-8")
    return out
