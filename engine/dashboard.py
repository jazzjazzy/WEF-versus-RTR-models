"""The dashboard: one HTML file per run, built only from the run's SQLite record.

Every per-person measure is drawn for everyone, the owner class, the working class
and the out of work (Jason, 12/11/2026). The page fetches nothing, so it opens offline.
"""

from __future__ import annotations

import html
import json
import pathlib
import sqlite3

from .config import WORLD_NAMES

QUARTER = 13
YEAR = 52

# (scope in the record, name on the page, colour: 'ink' for the total, else a palette slot)
CLASSES = [("all", "Everyone", "ink"), ("owner", "Owner class", 1),
           ("working", "Working class", 2), ("out", "Out of work", 3)]
BASE_NEEDS = [("food", "Food"), ("housing", "Housing"), ("appliances", "Appliances"),
              ("entertainment", "Entertainment")]
# What a break in a class line means, said in words on the chart.
EMPTY_LABEL = {"owner": "no owner class", "working": "no working class", "out": "nobody out of work"}


def _mark_empty(series: dict, scope: str) -> dict:
    """A break in a class line always means the class had nobody in it that quarter.
    Mark those quarters so the page can show the reason and not just a gap."""
    empty = [v is None for v in series["values"]]
    if any(empty) and scope in EMPTY_LABEL:
        series["empty"] = empty
        series["empty_label"] = EMPTY_LABEL[scope]
    return series


def _load(run_dir: pathlib.Path):
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        meta = dict(con.execute("SELECT key, value FROM run").fetchall())
        series: dict[tuple[str, str], dict[int, float]] = {}
        last = 0
        for week, scope, metric, value in con.execute(
                "SELECT week, scope, metric, value FROM series ORDER BY week"):
            series.setdefault((scope, metric), {})[week] = value
            last = max(last, week)
        marks = {}
        for kind in ("town_full", "town_failed"):
            marks[kind] = con.execute("SELECT MIN(week) FROM events WHERE kind = ?",
                                      (kind,)).fetchone()[0]
        events = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        places = None
        try:                                   # runs made before stage 2, or with no map, have no places
            week = con.execute("SELECT MAX(week) FROM places").fetchone()[0]
            if week is not None:
                places = {
                    "week": week,
                    "names": dict(con.execute("SELECT firm, name FROM firm_static").fetchall()),
                    "rows": con.execute(
                        "SELECT s.x, s.y, p.kind, p.label, p.owner, p.user, p.homes, p.let, "
                        "p.rent_factor, p.ground_rent FROM places p JOIN spots s ON s.spot = p.spot "
                        "WHERE p.week = ? ORDER BY p.spot", (week,)).fetchall(),
                }
        except sqlite3.OperationalError:
            places = None
    finally:
        con.close()
    return meta, series, last, marks, events, places


class _Shaper:
    """Turns weekly values into the quarterly lines and yearly columns the page draws."""

    def __init__(self, series, last: int) -> None:
        self.series = series
        self.last = last
        self.quarter_x = [round(min(s + QUARTER - 1, last) / YEAR, 4)
                          for s in range(1, last + 1, QUARTER)]
        self.year_x = list(range(1, -(-last // YEAR) + 1))

    def weekly(self, scope: str, metric: str) -> dict[int, float]:
        return self.series.get((scope, metric), {})

    def ratio(self, top: dict, bottom: dict) -> dict[int, float]:
        return {w: (top[w] / bottom[w] if bottom.get(w) else 0.0) for w in top}

    def quarters(self, values: dict, scale: float = 1.0, weights: dict | None = None,
                 how: str = "mean") -> list:
        """Quarterly averages. With `weights` (a group's head count each week) the average is
        over the people, and a quarter in which the group was empty is a gap, not a zero.
        With how='last', the value in each quarter's final week: for a count that is made
        once a quarter and recorded then."""
        out = []
        for start in range(1, self.last + 1, QUARTER):
            weeks = range(start, min(start + QUARTER, self.last + 1))
            if how == "last":
                block = [values[w] for w in weeks if w in values]
                out.append(round(scale * block[-1], 4) if block else None)
            elif weights is None:
                block = [values[w] for w in weeks if w in values]
                out.append(round(scale * sum(block) / len(block), 4) if block else None)
            else:
                people = sum(weights.get(w, 0) for w in weeks)
                if people <= 0:
                    out.append(None)
                else:
                    out.append(round(scale * sum(values.get(w, 0) * weights.get(w, 0) for w in weeks)
                                     / people, 4))
        if out and self.last in values:                 # the line ends on the final week itself
            if weights is None or weights.get(self.last, 0) > 0:
                out[-1] = round(scale * values[self.last], 4)
            else:
                out[-1] = None
        return out

    def years(self, values: dict, scale: float = 1.0, how: str = "sum") -> list:
        out = []
        for start in range(1, self.last + 1, YEAR):
            first = 0 if start == 1 else start          # week 0, when the founders arrive, is in year 1
            block = [values[w] for w in range(first, min(start + YEAR, self.last + 1))
                     if w in values]
            if not block:
                out.append(0)
            elif how == "sum":
                out.append(round(scale * sum(block), 2))
            elif how == "last":
                out.append(round(scale * block[-1], 2))
            else:
                out.append(round(scale * sum(block) / len(block), 2))
        return out

    def end(self, scope: str, metric: str, default: float = 0.0) -> float:
        return self.weekly(scope, metric).get(self.last, default)


def _map_chart(places: dict) -> dict:
    """The picture of the town: what stands on every spot at the last recorded quarter."""
    names = places["names"]
    cells = []
    for x, y, kind, label, owner, user, homes, let, factor, ground in places["rows"]:
        if kind == "service":
            text = (label or "service").capitalize()
        elif kind in ("homes", "premises"):
            text = names.get(user, f"Firm {user}")
        else:
            text = ""
        cells.append({
            "x": x, "y": y, "kind": kind or "empty", "label": text, "homes": homes, "let": let,
            "factor": round(factor, 2), "ground": round(ground / 100) if ground else 0,
            "owner": names.get(owner, "") if owner is not None and owner != user else "",
        })
    return {
        "title": "The town at the end",
        "note": f"What stands on every spot in week {places['week']}, the last quarter recorded. "
                "Point at a spot to see whose it is.",
        "type": "map", "unit": "count", "x": [0], "series": [], "section": "map",
        "cols": max(c["x"] for c in cells) + 1, "rows": max(c["y"] for c in cells) + 1, "cells": cells,
    }


def _charts(shape: _Shaper, cfg: dict, places: dict | None = None) -> list[dict]:
    charts: list[dict] = []
    cutoff = cfg.get("happy_cutoff", 0.5)
    fail_at = 100 * cfg.get("failure_unhappy_share", 0.9)

    def lines(title, note, unit, series, **extra):
        charts.append({"title": title, "note": note, "type": "line", "unit": unit,
                       "x": shape.quarter_x, "series": series, **extra})

    def stack(title, note, unit, series, **extra):
        charts.append({"title": title, "note": note, "type": "stack", "unit": unit,
                       "x": shape.year_x, "series": series, **extra})

    def by_class(title, note, unit, metric, scale=1.0, section="classes", **extra):
        # averaged over the people in the group; head count itself is a plain average
        series = [_mark_empty({"name": name, "color": color,
                               "values": shape.quarters(shape.weekly(scope, metric), scale,
                                                        None if metric == "n" else shape.weekly(scope, "n"))},
                              scope)
                  for scope, name, color in CLASSES]
        lines(title, note, unit, series, by_class=True, section=section, **extra)

    # --- the two classes ----------------------------------------------------------------
    by_class("Share unhappy",
             "The share of each group below the happiness cut-off. The run fails the first week "
             "the line for everyone reaches the marked level.",
             "pct", "unhappy", 100.0, ymax=100,
             refs=[{"y": fail_at, "label": f"{fail_at:.0f}%: the run fails"}])
    by_class("Security",
             "How safe agents feel about the weeks ahead, from 0 to 1. It falls fast and recovers slowly.",
             "ratio", "security", ymax=1)
    by_class("Wellbeing",
             "Half security, plus needs met and the condition of what they rent. "
             "An agent is happy at or above the marked level.",
             "ratio", "wellbeing", ymax=1, refs=[{"y": cutoff, "label": f"happy at {cutoff:g} or more"}])
    by_class("Needs met",
             "The share of what they need that was supplied that week, weighted by how essential it is.",
             "ratio", "provision", ymax=1)
    by_class("Condition of home and appliances",
             "From 1 (new) to 0. An agent with no home or no appliance set scores 0 for it.",
             "ratio", "condition", ymax=1)
    by_class("Weekly income", "Pay plus a year of dividends spread over the year, per person.",
             "money", "income", 0.01)
    by_class("Cash held", "The middle person's cash in each group.", "money", "cash_median", 0.01)
    debt = [_mark_empty({"name": name, "color": color,
                         "values": shape.quarters(shape.ratio(shape.weekly(scope, "debt"),
                                                              shape.weekly(scope, "n")),
                                                  0.01, shape.weekly(scope, "n"))}, scope)
            for scope, name, color in CLASSES]
    lines("Debt to the bank", "Personal loans outstanding, per person in each group.", "money", debt,
          by_class=True, section="classes")
    by_class("Planning horizon",
             "How many weeks ahead agents are effectively planning. Insecurity shortens it.",
             "count", "horizon")
    by_class("Head count", "People in each group. Class is by role, recalculated every week.",
             "count", "n")
    lines("Share of all shares held",
          "How the market value of all shares splits between the classes.", "pct",
          [{"name": name, "color": color, "values": shape.quarters(shape.weekly(scope, "shares_pct"), 100.0)}
           for scope, name, color in CLASSES[1:]], ymax=100, section="classes")

    # --- the town -------------------------------------------------------------------------
    town = lambda metric: shape.weekly("town", metric)   # noqa: E731
    lines("Prices against wages",
          "Both start at 100. The basket is the four base needs at the cheapest price on offer.",
          "index",
          [{"name": "Cost of the basket", "color": 1, "values": shape.quarters(town("price_index"), 100.0)},
           {"name": "Staff wage", "color": 2, "values": shape.quarters(town("wage_index"), 100.0)}],
          zero=False, refs=[{"y": 100, "label": "where both started"}], section="town")
    lines("Basket against the staff wage",
          "The cost of the four base needs as a share of the average staff wage.", "pct",
          [{"name": "Basket as a share of the wage", "color": 1,
            "values": shape.quarters(town("affordability"), 100.0)}],
          refs=[{"y": 100, "label": "the whole wage"}], section="town")
    initial = {n["name"]: n["initial_price"] for n in cfg.get("needs", [])}
    lines("Prices of the four needs",
          "The cheapest price on offer for each need, with its starting price as 100.", "index",
          [{"name": label, "color": i + 1,
            "values": shape.quarters(town(f"price_{name}"), 100.0 / initial[name] if initial.get(name) else 0.0)}
           for i, (name, label) in enumerate(BASE_NEEDS)],
          zero=False, section="town")
    stack("Firms by need", "Firms alive at the end of each year.", "count",
          [{"name": label, "color": i + 1, "values": shape.years(town(f"firms_{name}"), how="last")}
           for i, (name, label) in enumerate(BASE_NEEDS)]
          + [{"name": "Invented needs", "color": 5, "values": shape.years(town("firms_invented"), how="last")}],
          section="town")
    people = town("population")
    lines("Out of work, destitute, homeless", "Each as a share of everyone in town.", "pct",
          [{"name": "Out of work", "color": 1,
            "values": shape.quarters(shape.ratio(shape.weekly("out", "n"), people), 100.0)},
           {"name": "Destitute", "color": 2,
            "values": shape.quarters(shape.ratio(town("destitute"), people), 100.0)},
           {"name": "Homeless", "color": 3,
            "values": shape.quarters(shape.ratio(shape.weekly("all", "homeless"), people), 100.0)}],
          section="town")
    lines("Ownership concentration",
          "How much the top tenth of residents hold, and how unequal share ownership is "
          "(0 is equal, 100 is one person holding everything).", "pct",
          [{"name": "Top tenth's share of all shares", "color": 1,
            "values": shape.quarters(town("top10_shares"), 100.0)},
           {"name": "Top tenth's share of all cash", "color": 2,
            "values": shape.quarters(town("top10_cash"), 100.0)},
           {"name": "Inequality of share ownership", "color": 3,
            "values": shape.quarters(town("gini_shares"), 100.0)}],
          ymax=100, section="town")
    lines("Money in town", "All cash held in town, and who holds it.", "money",
          [{"name": "All money", "color": "ink", "values": shape.quarters(town("money"), 0.01)},
           {"name": "Held by people", "color": 1, "values": shape.quarters(town("money_people"), 0.01)},
           {"name": "Held by firms", "color": 2, "values": shape.quarters(town("money_firms"), 0.01)}],
          section="town")
    stack("Money crossing the town boundary",
          "The only five ways money enters or leaves, added up for each year. "
          "Money in is above the line, money out below.", "money",
          [{"name": "Arrivals' capital", "color": 1, "values": shape.years(town("in_arrival"), 0.01)},
           {"name": "Bank loans", "color": 2, "values": shape.years(town("in_loan"), 0.01)},
           {"name": "Exports", "color": 3, "values": shape.years(town("in_export"), 0.01)},
           {"name": "Loan repayments", "color": 4, "values": shape.years(town("out_repay"), -0.01)},
           {"name": "Interest", "color": 5, "values": shape.years(town("out_interest"), -0.01)},
           {"name": "Imports", "color": 6, "values": shape.years(town("out_import"), -0.01)}],
          section="town")
    lines("Bank lending", "Loans outstanding.", "money",
          [{"name": "Owed by firms", "color": 1, "values": shape.quarters(town("loans_firms"), 0.01)},
           {"name": "Owed by people", "color": 2, "values": shape.quarters(town("loans_people"), 0.01)}],
          section="town")
    stack("Moves between classes",
          "People who moved up a class each year (out of work to working to owner), "
          "and people who moved down, drawn below the line.", "count",
          [{"name": "Moved up", "color": 1, "values": shape.years(town("moved_up"))},
           {"name": "Moved down", "color": 2, "values": shape.years(town("moved_down"), -1.0)}],
          section="town")
    lines("Jobs", "Staff and executives employed, and vacancies firms could not fill.", "count",
          [{"name": "Staff", "color": 1, "values": shape.quarters(town("staff"))},
           {"name": "Executives", "color": 2, "values": shape.quarters(town("execs"))},
           {"name": "Vacancies", "color": 3, "values": shape.quarters(town("vacancies"))}],
          section="town")
    lines("Homes", "Homes standing, and how many are empty.", "count",
          [{"name": "Homes", "color": 1, "values": shape.quarters(town("homes"))},
           {"name": "Empty", "color": 2, "values": shape.quarters(town("homes_vacant"))}],
          section="town")
    lines("Upkeep and condition",
          "How much of the needed upkeep firms choose to do, and the condition of what people live with.",
          "ratio",
          [{"name": "Upkeep firms choose to do", "color": 1, "values": shape.quarters(town("upkeep_level"))},
           {"name": "Condition of lived-in homes", "color": 2, "values": shape.quarters(town("home_cond"))},
           {"name": "Condition of appliance sets in use", "color": 3,
            "values": shape.quarters(town("appl_cond"))}],
          ymax=1, section="town")
    # --- owning, letting and side hustles (only the RTR world records them) -----------------
    has = lambda metric: ("town", metric) in shape.series   # noqa: E731  an older record may lack one
    if has("homes_owned"):
        owned, let = town("homes_owned"), town("homes_let_private")
        lines("Who holds the homes",
              "Homes standing, and of them: lived in by the person who owns them, let by a person "
              "who owns them (a small landlord), and taken back by the bank and not yet sold. The "
              "rest are held by landlord firms.", "count",
              [{"name": "Homes standing", "color": "ink", "values": shape.quarters(town("homes"))},
               {"name": "Lived in by their owner", "color": 1,
                "values": shape.quarters({w: v - let.get(w, 0.0) for w, v in owned.items()})},
               {"name": "Let by a small landlord", "color": 2, "values": shape.quarters(let)},
               {"name": "Taken back by the bank", "color": 3, "values": shape.quarters(town("homes_foreclosed"))}],
              section="owning")
    if has("wage_offer"):
        lines("What staff are paid and what a newcomer is offered",
              "The average weekly pay of staff, and the rate a firm offers someone it takes on now. "
              "Staff keep the pay they were taken on at, so the two can part.", "money",
              [{"name": "Staff paid, on average", "color": 1, "values": shape.quarters(town("wage"), 0.01)},
               {"name": "The rate for someone taken on now", "color": 2,
                "values": shape.quarters(town("wage_offer"), 0.01)}],
              section="owning")
    if has("makers"):
        lines("Side hustles",
              "People selling their own work or making things on the side, the customers they serve, "
              "and how many have grown into small businesses with staff.", "count",
              [{"name": "People with a side hustle", "color": 1, "values": shape.quarters(town("makers"))},
               {"name": "Their customers", "color": 2, "values": shape.quarters(town("maker_customers"))},
               {"name": "Grown into small businesses", "color": 3,
                "values": shape.quarters(town("small_businesses"))}],
              section="owning")
    if has("sets_owned"):
        lines("Owning",
              "Appliance sets people own rather than rent, and people letting out a home they own.", "count",
              [{"name": "Appliance sets owned", "color": 1, "values": shape.quarters(town("sets_owned"))},
               {"name": "Small landlords", "color": 2, "values": shape.quarters(town("small_landlords"))}],
              section="owning")
    if has("home_loans"):
        lines("Loans against homes", "What people owe the bank on the homes they have bought or built.", "money",
              [{"name": "Owed on homes", "color": 1, "values": shape.quarters(town("home_loans"), 0.01)}],
              section="owning")
    # --- the map (only for a town that has one) --------------------------------------------
    if ("town", "spots_empty") in shape.series:
        if places is not None:
            charts.append(_map_chart(places))
        stack("How the map filled",
              "Spots holding homes, spots holding a firm's premises, and spots still empty at the end "
              "of each year. Land is free until none is empty.", "count",
              [{"name": "Homes", "color": 1, "values": shape.years(town("spots_homes"), how="last")},
               {"name": "Premises", "color": 2, "values": shape.years(town("spots_premises"), how="last")},
               {"name": "Empty", "color": 3, "values": shape.years(town("spots_empty"), how="last")}],
              section="map")
        lines("The price of land",
              "What a spot last changed hands for. Nothing until the map is full, because until then "
              "land is free.", "money",
              [{"name": "Price of a spot", "color": 1, "values": shape.quarters(town("land_price"), 0.01)}],
              section="map")
        by_class("Hours on the road",
                 "Hours a week each person spends getting to work and to the shops.",
                 "hours", "travel_hours", section="map")
        by_class("Share holding transport",
                 "Nobody has transport until someone founds a transport firm.",
                 "pct", "riders", 100.0, section="map", ymax=100)
        lines("People turned away by distance",
              "People who, in each quarter, could not take a job or get to a shop because it "
              "was too far. One person can be in more than one line.", "count",
              [{"name": "From a job", "color": 1,
                "values": shape.quarters(town("turned_away_job"), how="last")},
               {"name": "From food", "color": 2,
                "values": shape.quarters(town("turned_away_food"), how="last")},
               {"name": "From other shops", "color": 3,
                "values": shape.quarters(town("turned_away_other"), how="last")}],
              section="map")
        gaps = lambda values: [None if not v else v for v in values]   # noqa: E731  no homes there: no point
        lines("Rent by place",
              "The average rent of a home within three blocks of the middle, and of one beyond a "
              "walk from the middle.", "money",
              [{"name": "Near the middle", "color": 1, "values": gaps(shape.quarters(town("rent_middle"), 0.01))},
               {"name": "Beyond a walk from the middle", "color": 2,
                "values": gaps(shape.quarters(town("rent_edge"), 0.01))}],
              section="map")
    for i, chart in enumerate(charts):
        chart["id"] = f"c{i}"
    return charts


def _money(cents: float) -> str:
    dollars = cents / 100.0
    if abs(dollars) >= 1e6:
        return f"${dollars / 1e6:.1f}M"
    if abs(dollars) >= 1e4:
        return f"${dollars / 1e3:.0f}K"
    return f"${dollars:,.0f}"


def _header(meta: dict, shape: _Shaper, cfg: dict, marks: dict, events: int, town_view: bool = False) -> str:
    e = html.escape
    finished = "outcome" in meta
    last = shape.last
    years = last / YEAR
    seed = meta.get("seed", "?")
    rule = cfg.get("price_rule", "ratchet")
    rule_text = ("prices only ever rise (the rule as given)" if rule == "ratchet"
                 else "a firm backs off a price rise that lost it money")
    unhappy = {scope: shape.end(scope, "unhappy") for scope, _, _ in CLASSES}
    counts = {scope: int(shape.end(scope, "n")) for scope, _, _ in CLASSES}
    failed = marks.get("town_failed")
    full = marks.get("town_full")

    if not finished:
        hero = "Unfinished run"
        hero_sub = f"The record stops at week {last} (year {years:.1f}). The run did not reach its end."
    elif failed:
        hero = f"Failed in year {failed / YEAR:.1f}"
        hero_sub = (f"Week {failed} was the first week that "
                    f"{100 * cfg.get('failure_unhappy_share', 0.9):.0f}% of all agents were unhappy.")
    else:
        hero = f"Survived {years:.0f} years"
        hero_sub = f"{100 * unhappy['all']:.0f}% of agents were unhappy in the last week."

    def tile(label, value, detail=""):
        return (f'<div class="tile"><div class="tile-label">{e(label)}</div>'
                f'<div class="tile-value">{e(value)}</div>'
                f'<div class="tile-detail">{e(detail)}</div></div>')

    tiles = [
        tile("People in town", f"{counts['all']:,}",
             f"{counts['owner']:,} owner class, {counts['working']:,} working class, "
             f"{counts['out']:,} out of work"),
        tile("Unhappy at the end", f"{100 * unhappy['all']:.0f}%",
             f"owner class {100 * unhappy['owner']:.0f}%, working class {100 * unhappy['working']:.0f}%, "
             f"out of work {100 * unhappy['out']:.0f}%"),
        tile("Shares held by the top tenth", f"{100 * shape.end('town', 'top10_shares'):.0f}%",
             f"owner class holds {100 * shape.end('owner', 'shares_pct'):.0f}% of all shares, "
             f"working class {100 * shape.end('working', 'shares_pct'):.0f}%"),
        tile("Basket against the staff wage", f"{100 * shape.end('town', 'affordability'):.0f}%",
             f"basket {_money(shape.end('town', 'basket'))} a week, "
             f"staff wage {_money(shape.end('town', 'wage'))}"),
        tile("Town full", f"year {full / YEAR:.1f}" if full else "not reached",
             f"{cfg.get('population_cap', 1000):,} people is the cap; arrivals stop there"
             if cfg.get("population_cap", 1000) > 0
             else "No cap: full when the land has run out and a newcomer finds no home"),
        tile("Money in town", _money(shape.end("town", "money")),
             f"people hold {_money(shape.end('town', 'money_people'))}, "
             f"firms {_money(shape.end('town', 'money_firms'))}"),
    ]
    if ("town", "homes_owned") in shape.series:              # the RTR world: owning and side hustles
        owned, let = shape.end("town", "homes_owned"), shape.end("town", "homes_let_private")
        tiles.append(tile("Homes lived in by their owner", f"{int(owned - let):,}",
                          f"of {int(shape.end('town', 'homes')):,} homes standing; "
                          f"{int(let):,} more let by a small landlord"))
    if ("town", "makers") in shape.series:
        tiles.append(tile("People with a side hustle", f"{int(shape.end('town', 'makers')):,}",
                          f"{int(shape.end('town', 'small_businesses')):,} grown into small businesses"))
    width, height = cfg.get("map_width", 0), cfg.get("map_height", 0)
    world = f"The town on a {width} by {height} map." if width else "The economy without the map."
    watch = ' <a href="town.html">Watch this town, week by week</a>' if town_view else ""
    return f"""
<header>
  <h1>The __WORLD__: one run of the town</h1>
  <div class="sub">Run {e(str(meta.get('run_id', '')))}. Seed {e(str(seed))}. Price rule: {e(rule_text)}.
  {e(world)}{watch}</div>
  <div class="hero">{e(hero)}</div>
  <div class="herosub">{e(hero_sub)}</div>
  <div class="notice" role="note">
    <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5 15 14H1z" fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6v4M8 11.6v.6"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    <span><strong>Untuned.</strong> The build so far proves the machinery: the accounts balance and every
    week is recorded. The starting values have not been tested, so read these charts as a first look, not a
    finding.</span>
  </div>
  <div class="tiles">{''.join(tiles)}</div>
</header>
<footer id="foot">
  <h2>How to read this</h2>
  <p><strong>Class is by role.</strong> Owner class: founders, anyone who controls a firm, CEOs, executives,
  and people living on dividends alone. Working class: staff drawing a wage, with or without shares.
  Out of work: everyone else. It is recalculated every week.</p>
  <p><strong>Unhappy</strong> means wellbeing below {e(f"{cfg.get('happy_cutoff', 0.5):g}")}. Wellbeing is half
  security, plus needs met and the condition of the home and appliances they rent.</p>
  <p><strong>Lines</strong> are quarterly averages, ending on the final week itself. A class line
  is averaged over the people in that class. Where a class had nobody in it, its line breaks and a
  strip under the chart marks those quarters. Nothing is missing from the record there.
  <strong>Columns</strong> are one per year.
  Every chart has a table of its numbers behind the Table button.</p>
  <p class="fine">Built only from run.sqlite. {events:,} events recorded.
  Record fingerprint {e(str(meta.get('fingerprint', 'not finished'))[:16])}.
  Code fingerprint {e(str(meta.get('code_fingerprint', '')))}.</p>
</footer>
"""


def build_dashboard(run_dir) -> pathlib.Path:
    """Write dashboard.html in the run folder, from run.sqlite alone. Returns its path."""
    run_dir = pathlib.Path(run_dir)
    meta, series, last, marks, events, places = _load(run_dir)
    cfg = json.loads(meta.get("config", "{}"))
    world = WORLD_NAMES.get(cfg.get("world", "wef"), "WEF world")       # a record from before there were two is WEF
    shape = _Shaper(series, last)
    data = {
        "charts": _charts(shape, cfg, places),
        "marks": {"full": round(marks["town_full"] / YEAR, 4) if marks.get("town_full") else None,
                  "failed": round(marks["town_failed"] / YEAR, 4) if marks.get("town_failed") else None,
                  "end": round(last / YEAR, 4)},
    }
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    page = (TEMPLATE
            .replace("__TITLE__", html.escape(f"{world} run {meta.get('run_id', run_dir.name)}"))
            .replace("__HEADER__", _header(meta, shape, cfg, marks, events,
                                           town_view=(run_dir / "town.html").exists())
                     .replace("__WORLD__", world))
            .replace("__DATA__", payload))
    if any(c.get("section") == "owning" for c in data["charts"]):   # only the RTR world has this section
        for before, after in OWNING_SECTION:
            assert page.count(before) == 1, before
            page = page.replace(before, after)
    out = run_dir / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    return out


# The RTR world's section, put into the page only for a run that has it, so that a WEF run's page is
# the page it was before stage 3 of the RTR world (20 November 2026), byte for byte.
OWNING_SECTION = (
    ('<section id="mapsec">',
     '<section id="ownsec"><h2>Owning, letting and side hustles</h2><div class="grid" id="owning"></div></section>\n'
     '<section id="mapsec">'),
    ('var host = chart.section === "classes" ? "classes" : chart.section === "map" ? "map" : "town";',
     'var host = chart.section === "classes" ? "classes" : chart.section === "map" ? "map" : '
     'chart.section === "owning" ? "owning" : "town";'),
)

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
.viz-root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --wash: rgba(11,11,11,0.05); --ink-series: #52514e; --warning: #fab219;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --series-4: #eda100; --series-5: #e87ba4; --series-6: #008300;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --wash: rgba(255,255,255,0.06); --ink-series: #c3c2b7; --warning: #fab219;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --series-4: #c98500; --series-5: #d55181; --series-6: #008300;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --wash: rgba(255,255,255,0.06); --ink-series: #c3c2b7; --warning: #fab219;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  --series-4: #c98500; --series-5: #d55181; --series-6: #008300;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1320px; margin: 0 auto; padding: 24px 16px 56px; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 17px; font-weight: 600; margin: 32px 0 12px; }
a { color: inherit; }
.sub, .herosub { color: var(--text-secondary); font-size: 14px; }
.hero { font-size: 52px; font-weight: 600; line-height: 1.1; margin: 22px 0 6px; letter-spacing: -0.01em; }
.herosub { font-size: 15px; }
.notice { display: flex; gap: 10px; align-items: flex-start; margin: 18px 0; padding: 10px 14px;
  background: var(--surface-1); border: 1px solid var(--border); border-left: 4px solid var(--warning);
  border-radius: 8px; font-size: 14px; color: var(--text-secondary); }
.notice strong { color: var(--text-primary); }
.icon { width: 16px; height: 16px; flex: none; margin-top: 2px; color: var(--text-primary); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.tile-label { font-size: 13px; color: var(--text-secondary); }
.tile-value { font-size: 28px; font-weight: 600; line-height: 1.2; margin: 2px 0; }
.tile-detail { font-size: 12.5px; color: var(--text-secondary); }
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 28px 0 0; }
.filters span { font-size: 13px; color: var(--text-secondary); margin-right: 4px; }
button { font: inherit; font-size: 13px; color: var(--text-primary); background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; cursor: pointer; }
button:hover { background: var(--wash); }
button[aria-pressed="true"] { background: var(--text-primary); color: var(--surface-1); border-color: var(--text-primary); }
button:focus-visible, svg:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr)); gap: 14px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px 10px; margin: 0; min-width: 0; }
.card-head { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
.card-title { font-size: 15px; font-weight: 600; }
.card-note { font-size: 13px; color: var(--text-secondary); margin: 2px 0 8px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 12.5px; color: var(--text-secondary);
  margin: 0 0 4px; padding: 0; list-style: none; }
.legend li { display: flex; align-items: center; gap: 6px; }
.key-line { width: 16px; height: 0; border-top: 2px solid; border-radius: 2px; }
.key-box { width: 10px; height: 10px; border-radius: 2px; }
.key-strip { width: 16px; height: 4px; background: var(--muted); opacity: 0.6; }
.key-empty { width: 10px; height: 10px; border: 1px solid var(--axis); border-radius: 2px; }
.card.wide { grid-column: 1 / -1; }
.card.wide .plot svg { margin: 4px auto 0; }
.legend li.note { flex-basis: 100%; color: var(--muted); }
.plot svg { display: block; width: 100%; height: auto; overflow: visible; }
.plot text { font: 11.5px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted);
  font-variant-numeric: tabular-nums; }
.plot text.label { fill: var(--text-secondary); font-size: 12px; }
.plot text.label, .plot text.onplot { paint-order: stroke; stroke: var(--surface-1); stroke-width: 4px;
  stroke-linejoin: round; }
.empty { color: var(--muted); font-size: 13px; padding: 40px 0; text-align: center; }
.tablewrap { max-height: 320px; overflow: auto; margin-top: 4px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: right; padding: 4px 10px; border-bottom: 1px solid var(--grid);
  font-variant-numeric: tabular-nums; white-space: nowrap; }
th { position: sticky; top: 0; background: var(--surface-1); color: var(--text-secondary); font-weight: 600; }
th:first-child, td:first-child { text-align: left; }
#tip { position: fixed; z-index: 10; pointer-events: none; display: none; min-width: 150px; max-width: 320px;
  background: var(--surface-1); color: var(--text-primary); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 12.5px; box-shadow: 0 6px 24px rgba(0,0,0,0.14); }
#tip .when { color: var(--muted); margin-bottom: 4px; }
#tip .row { display: grid; grid-template-columns: 16px auto 1fr; gap: 6px; align-items: center; }
#tip .row b { font-weight: 600; font-variant-numeric: tabular-nums; }
#tip .row span.name { color: var(--text-secondary); }
footer p { font-size: 14px; color: var(--text-secondary); max-width: 80ch; margin: 6px 0; }
footer strong { color: var(--text-primary); }
footer .fine { font-size: 12.5px; color: var(--muted); }
@media (forced-colors: active), print {
  .plot path.series:nth-of-type(2) { stroke-dasharray: 6 3; }
  .plot path.series:nth-of-type(3) { stroke-dasharray: 2 3; }
  .plot path.series:nth-of-type(4) { stroke-dasharray: 8 3 2 3; }
}
</style>
</head>
<body class="viz-root">
<main>
__HEADER__
<div class="filters" role="group" aria-label="Years shown" id="filters"><span>Years shown</span></div>
<section><h2>The two classes</h2><div class="grid" id="classes"></div></section>
<section><h2>The town</h2><div class="grid" id="town"></div></section>
<section id="mapsec"><h2>The map</h2><div class="grid" id="map"></div></section>
</main>
<div id="tip" role="status" aria-live="polite"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("data").textContent);
  var NS = "http://www.w3.org/2000/svg";
  var tip = document.getElementById("tip");
  var marks = DATA.marks;
  var range = "all";

  function svg(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function el(name, cls, parent, text) {
    var e = document.createElement(name);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function colour(c) { return c === "ink" ? "var(--ink-series)" : "var(--series-" + c + ")"; }

  function fmt(unit, v) {
    if (v == null || isNaN(v)) return "no data";
    var a = Math.abs(v), sign = v < 0 ? "-" : "";
    if (unit === "pct") return (a >= 10 || a === 0 ? v.toFixed(0) : v.toFixed(1)) + "%";
    if (unit === "ratio") return v.toFixed(2);
    if (unit === "index") return v.toFixed(0);
    if (unit === "hours") return v.toFixed(1) + " h";
    if (unit === "money") {
      if (a >= 1e9) return sign + "$" + (a / 1e9).toFixed(2) + "B";
      if (a >= 1e6) return sign + "$" + (a / 1e6).toFixed(a >= 1e7 ? 1 : 2) + "M";
      if (a >= 1e4) return sign + "$" + (a / 1e3).toFixed(a >= 1e5 ? 0 : 1) + "K";
      return sign + "$" + Math.round(a).toLocaleString("en-AU");
    }
    return (a >= 100 || a === Math.round(a) ? Math.round(v) : +v.toFixed(1)).toLocaleString("en-AU");
  }
  // One style for a whole axis, chosen from its largest value.
  function axisFmt(unit, top) {
    if (unit !== "money") return function (v) { return fmt(unit, v); };
    var a = Math.abs(top);
    return function (v) {
      var s = v < 0 ? "-" : "", x = Math.abs(v);
      if (a >= 1e9) return s + "$" + (x / 1e9).toFixed(1) + "B";
      if (a >= 1e6) return s + "$" + (x / 1e6).toFixed(a >= 2e7 ? 0 : 1) + "M";
      if (a >= 1e4) return s + "$" + (x / 1e3).toFixed(0) + "K";
      return s + "$" + Math.round(x).toLocaleString("en-AU");
    };
  }
  function ticks(lo, hi, n) {
    if (!(hi > lo)) hi = lo + 1;
    var raw = (hi - lo) / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), norm = raw / mag;
    var step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
    var out = [], v = Math.floor(lo / step + 1e-9) * step;
    for (; v < hi + step - 1e-9 * step; v += step) out.push(+v.toFixed(10));
    if (out[out.length - 1] < hi - 1e-9) out.push(+(out[out.length - 1] + step).toFixed(10));
    return out;
  }
  function span() {
    var end = marks.end, full = marks.full;
    if (range === "growth" && full) return [0, full];
    if (range === "after" && full) return [full, end];
    if (range === "last10") return [Math.max(0, end - 10), end];
    return [0, end];
  }
  function when(x) {
    var q = ((Math.round(x * 4) - 1) % 4 + 4) % 4 + 1;
    return "Year " + Math.max(1, Math.ceil(x - 1e-9)) + ", quarter " + q;
  }

  function showTip(evt, title, rows, unit, lineKeys) {
    tip.textContent = "";
    el("div", "when", tip, title);
    rows.forEach(function (r) {
      var row = el("div", "row", tip);
      var key = el("span", lineKeys ? "key-line" : "key-box", row);
      if (lineKeys) key.style.borderTopColor = colour(r.color); else key.style.background = colour(r.color);
      el("b", null, row, r.text != null ? r.text : fmt(unit, r.value));
      el("span", "name", row, r.name);
    });
    placeTip(evt);
  }
  function placeTip(evt) {
    tip.style.display = "block";
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var x = evt.clientX + 14, y = evt.clientY + 14;
    if (x + w > window.innerWidth - 8) x = evt.clientX - w - 14;
    if (y + h > window.innerHeight - 8) y = evt.clientY - h - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  function showNote(evt, title, lines) {
    tip.textContent = "";
    el("div", "when", tip, title);
    lines.forEach(function (t) { el("div", null, tip, t); });
    placeTip(evt);
  }
  function hideTip() { tip.style.display = "none"; }

  // The picture of the town: one square a spot.
  function describe(c) {
    var lines;
    if (c.kind === "homes") {
      lines = [c.label, c.homes ? c.homes + " homes, " + c.let + " let" : "A bare lot: no homes on it yet"];
      if (c.homes) lines.push("Rent here is " + Math.round(c.factor * 100) + "% of the firm's price");
    } else if (c.kind === "premises") {
      lines = [c.label, "Premises: workplace and shop front"];
    } else if (c.kind === "service") {
      lines = [c.label];
    } else {
      lines = ["Empty"];
    }
    if (c.owner) lines.push("Land leased from " + c.owner + (c.ground ? " for $" + c.ground + " a week" : ""));
    return lines;
  }
  function renderMap(chart, body) {
    var W = Math.min(Math.max(260, body.clientWidth), 560), cell = Math.floor(W / chart.cols);
    var wide = cell * chart.cols, high = cell * chart.rows;
    var root = svg("svg", { viewBox: "0 0 " + wide + " " + high, role: "img",
      "aria-label": chart.title + ". " + chart.note + " The Table button lists every spot." }, body);
    root.style.maxWidth = wide + "px";
    chart.cells.forEach(function (c) {
      var a = { x: c.x * cell + 1, y: c.y * cell + 1, width: cell - 2, height: cell - 2, rx: 3 };
      if (c.kind === "homes") {
        a.fill = "var(--series-1)";
        a.opacity = c.homes ? (0.3 + 0.7 * c.let / c.homes).toFixed(2) : "0.12";
      } else if (c.kind === "premises") {
        a.fill = "var(--series-2)";
      } else if (c.kind === "service") {
        a.fill = "var(--ink-series)";
      } else {
        a.fill = "transparent";
        a.stroke = "var(--grid)";
      }
      var r = svg("rect", a, root);
      r.addEventListener("pointermove", function (evt) { showNote(evt, "Spot " + c.x + ", " + c.y, describe(c)); });
      r.addEventListener("pointerleave", hideTip);
    });
  }
  function renderMapTable(chart, body) {
    var wrap = el("div", "tablewrap", body), table = el("table", null, wrap);
    var head = el("tr", null, el("thead", null, table));
    ["Spot", "What", "Whose", "Homes", "Let", "Rent"].forEach(function (h) { el("th", null, head, h); });
    var tbody = el("tbody", null, table);
    chart.cells.forEach(function (c) {
      if (c.kind === "empty") return;
      var tr = el("tr", null, tbody);
      el("td", null, tr, c.x + ", " + c.y);
      el("td", null, tr, c.kind === "homes" ? "Homes" : c.kind === "premises" ? "Premises" : "Town service");
      el("td", null, tr, c.label);
      el("td", null, tr, c.kind === "homes" ? String(c.homes) : "");
      el("td", null, tr, c.kind === "homes" ? String(c.let) : "");
      el("td", null, tr, c.kind === "homes" && c.homes ? Math.round(c.factor * 100) + "%" : "");
    });
  }

  function frame(chart, body, lo, hi, unit, xLabels, X, m, W, H) {
    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", tabindex: "0",
      "aria-label": chart.title + ". " + chart.note + " Use the arrow keys to read values, or the Table button." }, body);
    var tk = ticks(lo, hi, 4), f = axisFmt(unit, Math.max(Math.abs(tk[0]), Math.abs(tk[tk.length - 1])));
    var Y = function (v) { return m.t + (1 - (v - tk[0]) / (tk[tk.length - 1] - tk[0])) * (H - m.t - m.b); };
    tk.forEach(function (v) {
      var y = Y(v);
      svg("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: v === 0 ? "var(--axis)" : "var(--grid)",
        "stroke-width": 1 }, root);
      svg("text", { x: m.l - 6, y: y + 4, "text-anchor": "end" }, root).textContent = f(v);
    });
    svg("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)", "stroke-width": 1 }, root);
    xLabels.forEach(function (t) {
      svg("text", { x: X(t.x), y: H - m.b + 16 + (m.strip || 0), "text-anchor": "middle" }, root).textContent = t.label;
    });
    svg("text", { x: W - m.r, y: H - 2, "text-anchor": "end" }, root).textContent = "years";
    return { root: root, Y: Y, top: tk[tk.length - 1], bottom: tk[0] };
  }
  function eventMarks(root, X, m, H, x0, x1, W) {
    [["full", "town full"], ["failed", "failed"]].forEach(function (p) {
      var x = marks[p[0]];
      if (x == null || x < x0 - 1e-9 || x > x1 + 1e-9) return;
      var flip = X(x) > W - m.r - 64;      // near the right edge the label goes to the left of its line
      svg("line", { x1: X(x), x2: X(x), y1: m.t - 4, y2: H - m.b, stroke: "var(--muted)", "stroke-width": 1 }, root);
      svg("text", { x: X(x) + (flip ? -4 : 4), y: m.t + 2, "text-anchor": flip ? "end" : "start",
        "class": "onplot" }, root).textContent = p[1];
    });
  }
  function yearTicks(x0, x1) {
    var out = [];
    ticks(x0, x1, 6).forEach(function (v) {
      if (v >= x0 - 1e-9 && v <= x1 + 1e-9 && v === Math.round(v)) out.push({ x: v, label: String(v) });
    });
    return out;
  }

  function renderLine(chart, body) {
    var r = span(), idx = [];
    chart.x.forEach(function (x, i) { if (x >= r[0] - 1e-9 && x <= r[1] + 1e-9) idx.push(i); });
    if (!idx.length) { el("div", "empty", body, "No data in these years."); return; }
    var xs = idx.map(function (i) { return chart.x[i]; });
    var series = chart.series.map(function (s) {
      return { name: s.name, color: s.color, v: idx.map(function (i) { return s.values[i]; }),
        empty: s.empty ? idx.map(function (i) { return s.empty[i]; }) : null, emptyLabel: s.empty_label };
    });
    var lo = Infinity, hi = -Infinity;
    series.forEach(function (s) { s.v.forEach(function (v) { if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }); });
    (chart.refs || []).forEach(function (ref) { lo = Math.min(lo, ref.y); hi = Math.max(hi, ref.y); });
    if (lo === Infinity) { el("div", "empty", body, "No data in these years."); return; }
    if (chart.zero !== false) lo = Math.min(lo, 0);
    if (chart.ymax != null) hi = Math.max(hi, chart.ymax);
    if (chart.zero === false) { var pad = (hi - lo) * 0.08 || 1; lo -= pad; hi += pad; }
    var stripRows = series.filter(function (s) {
      return s.empty && s.empty.some(function (e) { return e; });
    }).length;
    var strip = stripRows ? 3 + 6 * stripRows : 0;            // room under the axis for the strips
    var W = Math.max(300, body.clientWidth), H = 244 + strip;
    var m = { t: 20, r: 16, b: 30 + strip, l: 50, strip: strip };
    // Direct labels at the line ends, only when they fit without touching each other.
    var tkTmp = ticks(lo, hi, 4), top = tkTmp[tkTmp.length - 1], bottom = tkTmp[0];
    var endY = series.map(function (s) {
      var v = s.v[s.v.length - 1];
      return v == null ? null : m.t + (1 - (v - bottom) / (top - bottom)) * (H - m.t - m.b);
    });
    var labels = series.length > 1 && series.length <= 4 && W >= 420 && endY.every(function (y) { return y != null; });
    if (labels) {
      var sorted = endY.slice().sort(function (a, b) { return a - b; });
      for (var i = 1; i < sorted.length; i++) if (sorted[i] - sorted[i - 1] < 15) labels = false;
    }
    if (labels) m.r = 12 + 7 * Math.max.apply(null, series.map(function (s) { return s.name.length; }));
    var pw = W - m.l - m.r;
    var X = function (x) { return m.l + (xs.length > 1 ? (x - xs[0]) / (xs[xs.length - 1] - xs[0]) : 0.5) * pw; };
    var fr = frame(chart, body, lo, hi, chart.unit, yearTicks(xs[0], xs[xs.length - 1]), X, m, W, H);
    var root = fr.root, Y = fr.Y;
    eventMarks(root, X, m, H, xs[0], xs[xs.length - 1], W);
    (chart.refs || []).forEach(function (ref) {
      svg("line", { x1: m.l, x2: W - m.r, y1: Y(ref.y), y2: Y(ref.y), stroke: "var(--text-secondary)",
        "stroke-width": 1, "stroke-dasharray": "4 3" }, root);
      svg("text", { x: m.l + 4, y: Y(ref.y) - 5, "text-anchor": "start", "class": "label" }, root).textContent = ref.label;
    });
    // Quarters when a class had nobody in it: a strip under the axis in that class's colour.
    // The line itself breaks there. The legend says what the strip means.
    var stripRow = 0;
    series.forEach(function (s) {
      if (!s.empty || !s.empty.some(function (e) { return e; })) return;
      var y = H - m.b + 5 + stripRow * 6, i = 0;
      stripRow++;
      while (i < xs.length) {
        if (!s.empty[i]) { i++; continue; }
        var j = i;
        while (j + 1 < xs.length && s.empty[j + 1]) j++;
        var x0 = i > 0 ? X(xs[i - 1]) : m.l, x1 = X(xs[j]);      // a point sits at the end of its quarter
        if (x1 - x0 >= 1)
          svg("line", { x1: x0, x2: x1, y1: y, y2: y, stroke: colour(s.color), "stroke-width": 4,
            opacity: 0.6 }, root);
        i = j + 1;
      }
    });
    series.forEach(function (s) {
      var d = "", pen = false;
      s.v.forEach(function (v, i) {
        if (v == null) { pen = false; return; }
        d += (pen ? "L" : "M") + X(xs[i]).toFixed(1) + " " + Y(v).toFixed(1);
        if (!pen && (i + 1 >= s.v.length || s.v[i + 1] == null)) d += "h0.01";   // a lone quarter still shows, as a dot
        pen = true;
      });
      svg("path", { d: d, fill: "none", stroke: colour(s.color), "stroke-width": 2, "stroke-linejoin": "round",
        "stroke-linecap": "round", "class": "series" }, root);
    });
    series.forEach(function (s, k) {
      var v = s.v[s.v.length - 1];
      if (v == null) return;
      svg("circle", { cx: X(xs[xs.length - 1]), cy: Y(v), r: 4, fill: colour(s.color),
        stroke: "var(--surface-1)", "stroke-width": 2 }, root);
      if (labels) svg("text", { x: X(xs[xs.length - 1]) + 9, y: endY[k] + 4, "text-anchor": "start",
        "class": "label" }, root).textContent = s.name;
    });
    // hover and keyboard: a crosshair that snaps to the nearest quarter, one readout for every series
    var cross = svg("line", { y1: m.t, y2: H - m.b, stroke: "var(--muted)", "stroke-width": 1, visibility: "hidden" }, root);
    var dots = series.map(function (s) {
      return svg("circle", { r: 4, fill: colour(s.color), stroke: "var(--surface-1)", "stroke-width": 2,
        visibility: "hidden" }, root);
    });
    var at = xs.length - 1;
    function point(i, evt) {
      at = i;
      var x = X(xs[i]);
      cross.setAttribute("x1", x); cross.setAttribute("x2", x); cross.setAttribute("visibility", "visible");
      var rows = [];
      series.forEach(function (s, k) {
        var v = s.v[i];
        if (v == null) {
          dots[k].setAttribute("visibility", "hidden");
          if (s.empty && s.empty[i]) rows.push({ name: s.name, color: s.color, text: "nobody" });
          return;
        }
        dots[k].setAttribute("cx", x); dots[k].setAttribute("cy", Y(v)); dots[k].setAttribute("visibility", "visible");
        rows.push({ name: s.name, color: s.color, value: v });
      });
      showTip(evt, when(xs[i]), rows, chart.unit, true);
    }
    function clear() {
      cross.setAttribute("visibility", "hidden");
      dots.forEach(function (d) { d.setAttribute("visibility", "hidden"); });
      hideTip();
    }
    var hit = svg("rect", { x: m.l, y: m.t, width: Math.max(1, pw), height: H - m.t - m.b, fill: "transparent" }, root);
    hit.addEventListener("pointermove", function (evt) {
      var box = root.getBoundingClientRect();
      var px = (evt.clientX - box.left) * (W / box.width), best = 0, gap = Infinity;
      xs.forEach(function (x, i) { var g = Math.abs(X(x) - px); if (g < gap) { gap = g; best = i; } });
      point(best, evt);
    });
    hit.addEventListener("pointerleave", clear);
    root.addEventListener("keydown", function (evt) {
      if (evt.key !== "ArrowLeft" && evt.key !== "ArrowRight" && evt.key !== "Escape") return;
      evt.preventDefault();
      if (evt.key === "Escape") { clear(); return; }
      var i = Math.min(xs.length - 1, Math.max(0, at + (evt.key === "ArrowRight" ? 1 : -1)));
      var box = root.getBoundingClientRect();
      point(i, { clientX: box.left + X(xs[i]) * (box.width / W), clientY: box.top + m.t });
    });
    root.addEventListener("blur", clear);
  }

  function renderStack(chart, body) {
    var r = span(), idx = [];
    chart.x.forEach(function (y, i) { if (y > r[0] + 1e-9 && y - 1 < r[1] - 1e-9) idx.push(i); });
    if (!idx.length) { el("div", "empty", body, "No data in these years."); return; }
    var years = idx.map(function (i) { return chart.x[i]; });
    var series = chart.series.map(function (s) {
      return { name: s.name, color: s.color, v: idx.map(function (i) { return s.values[i] || 0; }) };
    });
    var hi = 0, lo = 0;
    years.forEach(function (_, i) {
      var up = 0, down = 0;
      series.forEach(function (s) { if (s.v[i] > 0) up += s.v[i]; else down += s.v[i]; });
      hi = Math.max(hi, up); lo = Math.min(lo, down);
    });
    if (hi === 0 && lo === 0) hi = 1;
    var W = Math.max(300, body.clientWidth), H = 244, m = { t: 20, r: 16, b: 30, l: 50 };
    var pw = W - m.l - m.r, band = pw / years.length, bar = Math.max(1, Math.min(24, band - 2));
    var X = function (y) { return m.l + (years.indexOf(y) + 0.5) * band; };
    var every = Math.max(1, Math.ceil(years.length / 8)), xl = [];
    years.forEach(function (y, i) { if (i % every === 0 || years.length <= 8) xl.push({ x: y, label: String(y) }); });
    var fr = frame(chart, body, lo, hi, chart.unit, xl, X, m, W, H), root = fr.root, Y = fr.Y;
    var wash = svg("rect", { y: m.t, width: band, height: H - m.t - m.b, fill: "var(--wash)", visibility: "hidden" }, root);
    years.forEach(function (y, i) {
      var up = 0, down = 0, cx = X(y), rad = Math.min(4, bar / 2);
      var lastUp = -1, lastDown = -1;
      series.forEach(function (s, k) { if (s.v[i] > 0) lastUp = k; else if (s.v[i] < 0) lastDown = k; });
      series.forEach(function (s, k) {
        var v = s.v[i];
        if (!v) return;
        var a = v > 0 ? up : down, b = a + v;
        if (v > 0) up = b; else down = b;
        var y0 = Y(a), y1 = Y(b), topY = Math.min(y0, y1), h = Math.abs(y1 - y0);
        if (h > 3) { h -= 2; if (v > 0) topY += 2; }     // a 2px gap in the surface colour between segments
        if (h < 0.5) return;
        var x0 = cx - bar / 2, x1 = cx + bar / 2, d;
        var rr = Math.min(rad, h);
        if (v > 0 && k === lastUp) {
          d = "M" + x0 + " " + (topY + h) + "V" + (topY + rr) + "Q" + x0 + " " + topY + " " + (x0 + rr) + " " + topY +
              "H" + (x1 - rr) + "Q" + x1 + " " + topY + " " + x1 + " " + (topY + rr) + "V" + (topY + h) + "Z";
        } else if (v < 0 && k === lastDown) {
          d = "M" + x0 + " " + topY + "V" + (topY + h - rr) + "Q" + x0 + " " + (topY + h) + " " + (x0 + rr) + " " + (topY + h) +
              "H" + (x1 - rr) + "Q" + x1 + " " + (topY + h) + " " + x1 + " " + (topY + h - rr) + "V" + topY + "Z";
        } else {
          d = "M" + x0 + " " + topY + "H" + x1 + "V" + (topY + h) + "H" + x0 + "Z";
        }
        svg("path", { d: d, fill: colour(s.color) }, root);
      });
    });
    var at = years.length - 1;
    function point(i, evt) {
      at = i;
      wash.setAttribute("x", m.l + i * band); wash.setAttribute("visibility", "visible");
      var rows = series.map(function (s) { return { name: s.name, color: s.color, value: s.v[i] }; });
      showTip(evt, "Year " + years[i], rows, chart.unit, false);
    }
    function clear() { wash.setAttribute("visibility", "hidden"); hideTip(); }
    var hit = svg("rect", { x: m.l, y: m.t, width: Math.max(1, pw), height: H - m.t - m.b, fill: "transparent" }, root);
    hit.addEventListener("pointermove", function (evt) {
      var box = root.getBoundingClientRect(), px = (evt.clientX - box.left) * (W / box.width);
      point(Math.min(years.length - 1, Math.max(0, Math.floor((px - m.l) / band))), evt);
    });
    hit.addEventListener("pointerleave", clear);
    root.addEventListener("keydown", function (evt) {
      if (evt.key !== "ArrowLeft" && evt.key !== "ArrowRight" && evt.key !== "Escape") return;
      evt.preventDefault();
      if (evt.key === "Escape") { clear(); return; }
      var i = Math.min(years.length - 1, Math.max(0, at + (evt.key === "ArrowRight" ? 1 : -1)));
      var box = root.getBoundingClientRect();
      point(i, { clientX: box.left + X(years[i]) * (box.width / W), clientY: box.top + m.t });
    });
    root.addEventListener("blur", clear);
  }

  function renderTable(chart, body) {
    var r = span(), wrap = el("div", "tablewrap", body), table = el("table", null, wrap);
    var head = el("tr", null, el("thead", null, table));
    el("th", null, head, "Year");
    chart.series.forEach(function (s) { el("th", null, head, s.name); });
    var tbody = el("tbody", null, table), rows = {};
    chart.x.forEach(function (x, i) {
      if (chart.type === "stack") { if (x > r[0] + 1e-9 && x - 1 < r[1] - 1e-9) rows[x] = i; }
      else if (x >= r[0] - 1e-9 && x <= r[1] + 1e-9) rows[Math.max(1, Math.ceil(x - 1e-9))] = i;   // the last quarter of each year
    });
    Object.keys(rows).map(Number).sort(function (a, b) { return a - b; }).forEach(function (year) {
      var tr = el("tr", null, tbody);
      el("td", null, tr, String(year));
      chart.series.forEach(function (s) {
        var i = rows[year];
        el("td", null, tr, s.empty && s.empty[i] ? "nobody" : fmt(chart.unit, s.values[i]));
      });
    });
  }

  function draw(chart) {
    var body = chart.body;
    body.textContent = "";
    hideTip();
    if (chart.type === "map") { if (chart.table) renderMapTable(chart, body); else renderMap(chart, body); }
    else if (chart.table) renderTable(chart, body);
    else if (chart.type === "stack") renderStack(chart, body);
    else renderLine(chart, body);
  }
  function drawAll() { DATA.charts.forEach(draw); }

  DATA.charts.forEach(function (chart) {
    var host = chart.section === "classes" ? "classes" : chart.section === "map" ? "map" : "town";
    var card = el("figure", "card" + (chart.type === "map" ? " wide" : ""), document.getElementById(host));
    var head = el("div", "card-head", card), left = el("div", null, head);
    el("div", "card-title", left, chart.title);
    var toggle = el("button", null, head, "Table");
    toggle.type = "button";
    toggle.setAttribute("aria-pressed", "false");
    toggle.setAttribute("aria-label", "Show " + chart.title + " as a table");
    el("div", "card-note", card, chart.note);
    if (chart.type === "map") {
      var keys = el("ul", "legend", card);
      [["key-box", "var(--series-1)", "Homes: darker where more are let"],
       ["key-box", "var(--series-2)", "A firm's premises"],
       ["key-box", "var(--ink-series)", "The bank and the broker"],
       ["key-empty", null, "Empty"]].forEach(function (k) {
        var item = el("li", null, keys), mark = el("span", k[0], item);
        if (k[1]) mark.style.background = k[1];
        el("span", null, item, k[2]);
      });
    }
    if (chart.series.length > 1) {
      var legend = el("ul", "legend", card);
      chart.series.forEach(function (s) {
        var li = el("li", null, legend), key = el("span", chart.type === "stack" ? "key-box" : "key-line", li);
        if (chart.type === "stack") key.style.background = colour(s.color); else key.style.borderTopColor = colour(s.color);
        el("span", null, li, s.name);
      });
      var gaps = chart.series.filter(function (s) { return s.empty; });
      if (gaps.length) {
        var note = el("li", "note", legend), strip = el("span", "key-strip", note);
        if (gaps.length === 1) {
          strip.style.background = colour(gaps[0].color);
          el("span", null, note, "Strip under the chart: " + gaps[0].empty_label + " that quarter, so no line");
        } else {
          el("span", null, note, "A strip under the chart: nobody in that group that quarter, so no line");
        }
      }
    }
    chart.body = el("div", "plot", card);
    chart.table = false;
    toggle.addEventListener("click", function () {
      chart.table = !chart.table;
      toggle.setAttribute("aria-pressed", String(chart.table));
      toggle.textContent = chart.table ? "Chart" : "Table";
      draw(chart);
    });
  });

  var choices = [["all", "All years"]];
  if (marks.full != null) { choices.push(["growth", "Until the town filled"]); choices.push(["after", "After the town filled"]); }
  if (marks.end > 10) choices.push(["last10", "Last 10 years"]);
  var buttons = [];
  choices.forEach(function (c) {
    var b = el("button", null, document.getElementById("filters"), c[1]);
    b.type = "button";
    b.setAttribute("aria-pressed", String(c[0] === range));
    b.addEventListener("click", function () {
      range = c[0];
      buttons.forEach(function (o) { o.b.setAttribute("aria-pressed", String(o.k === range)); });
      drawAll();
    });
    buttons.push({ b: b, k: c[0] });
  });

  if (!document.getElementById("map").children.length) document.getElementById("mapsec").remove();
  var foot = document.getElementById("foot");
  document.querySelector("main").appendChild(foot);
  drawAll();
  var timer = null;
  window.addEventListener("resize", function () { clearTimeout(timer); timer = setTimeout(drawAll, 150); });
})();
</script>
</body>
</html>
"""
