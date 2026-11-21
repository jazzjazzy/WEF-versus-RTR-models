"""The page for a batch: one HTML file that shows how many towns did what.

It is built only from `batch.sqlite`, the table batch.py gathers from the towns' records,
and fetches nothing, so it opens offline. `report_data` works the numbers out; the rest of
this file draws them.

The middle of a set of towns is the median. The middle half runs from the first quartile to
the third, by straight-line interpolation between towns. A figure for a year is over the
towns still standing at the end of that year, and says how many that is.
"""

from __future__ import annotations

import html
import json
import math
import pathlib

from .config import WORLD_NAMES

CLASSES = ("all", "owner", "working", "out")
LEVEL = 0.001          # two prices within a tenth of a percent of each other have risen level


# --- the middle, the middle half and the range ------------------------------------------------------
def quantile(values, q: float) -> float:
    """The value a share `q` of the way through the sorted values, in a straight line between
    the two it falls between."""
    ordered = sorted(values)
    at = q * (len(ordered) - 1)
    low = math.floor(at)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (at - low)


def spread(values) -> dict | None:
    """How many, the range, the middle and the middle half. None when there is nothing."""
    values = list(values)
    if not values:
        return None
    return {"n": len(values), "min": min(values), "q1": quantile(values, 0.25),
            "median": quantile(values, 0.5), "q3": quantile(values, 0.75), "max": max(values)}


def half_failed(failed: list[float], n: int) -> float | None:
    """The year by which half of all `n` towns had failed. None when fewer than half did.
    Unlike the middle of the towns that failed, this counts the towns still standing."""
    need = math.ceil(n / 2)
    return sorted(failed)[need - 1] if n and len(failed) >= need else None


def risen_most(ratios: dict) -> str:
    """Which need's price stands highest against its starting price. Needs within a tenth of
    a percent of the highest have risen level with it, and are named together."""
    if not ratios:
        return "none"
    top = max(ratios.values())
    names = sorted(name for name, ratio in ratios.items() if top - ratio <= LEVEL)
    return names[0] if len(names) == 1 else "level: " + ", ".join(names)


# --- the numbers of a batch -------------------------------------------------------------------------
def _standing(failed: list[float], n: int, horizon: float) -> list[list]:
    """The share of towns still standing, as steps: [year, share from then on]."""
    if n == 0:
        return []
    steps = [[0, 1.0]]
    for year in sorted(set(failed)):
        steps.append([year, sum(1 for f in failed if f > year) / n + (n - len(failed)) / n])
    if steps[-1][0] < horizon:
        steps.append([horizon, steps[-1][1]])
    return steps


def _yearly(con, setting: int) -> dict:
    """For each measure, the spread across the towns still standing at the end of each year.

    A week is recorded before the failure rule is read, so a town that fails in the last week
    of a year has a record for that year: it is left out, because it is not still standing.
    A class with nobody in it has no number that year, so that town is left out of that
    class's figure."""
    from .batch import MEASURES, RTR_MEASURES
    ended = {seed: (failed, year_weeks) for seed, failed, year_weeks in con.execute(
        "SELECT seed, failed_week, year_weeks FROM towns WHERE setting = ?", (setting,))}
    values: dict[tuple, dict[int, float]] = {}
    for seed, year, scope, metric, value in con.execute(
            "SELECT seed, year, scope, metric, value FROM yearly WHERE setting = ?", (setting,)):
        failed, year_weeks = ended[seed]
        if failed is not None and failed <= year * year_weeks:
            continue                                 # it had failed by the end of that year
        values.setdefault((scope, metric, year), {})[seed] = value
    out: dict[str, list] = {}
    for scope, metric in MEASURES + RTR_MEASURES:
        rows = []
        for year in sorted(y for s, m, y in values if (s, m) == (scope, metric)):
            towns = values[(scope, metric, year)]
            if scope != "town" and metric != "n":
                sizes = values.get((scope, "n", year), {})
                towns = {seed: value for seed, value in towns.items() if sizes.get(seed, 0) > 0}
            found = spread(towns.values())
            if found:
                rows.append({"year": year, **found})
        if rows:
            out[f"{scope}/{metric}"] = rows
    return out


def _order(value):
    """Numbers in order of size, then words in order of spelling."""
    return (0, value, "") if isinstance(value, (int, float)) else (1, 0, str(value))


def report_data(con) -> dict:
    """Everything the page shows, from the batch table alone."""
    meta = dict(con.execute("SELECT key, value FROM batch").fetchall())
    plan = json.loads(meta["plan"])
    settings = []
    for number, name, overrides, dials in con.execute(
            "SELECT setting, name, overrides, dials FROM settings ORDER BY setting").fetchall():
        towns, summaries, planned = [], [], 0
        for seed, folder, outcome, weeks, failed, full, year_weeks, years, fingerprint, summary in con.execute(
                "SELECT seed, folder, outcome, weeks, failed_week, full_week, year_weeks, years, fingerprint, summary "
                "FROM towns WHERE setting = ? ORDER BY seed", (number,)):
            towns.append({"seed": seed, "folder": folder, "outcome": outcome, "weeks": weeks,
                          "years": weeks / year_weeks, "failed_week": failed,
                          "failed_year": failed / year_weeks if failed is not None else None,
                          "full_year": full / year_weeks if full is not None else None,
                          "fingerprint": fingerprint})
            summaries.append(json.loads(summary))
            planned = max(planned, years)
        failed_years = sorted(town["failed_year"] for town in towns if town["failed_year"] is not None)
        needs: dict = {}
        for summary in summaries:
            which = risen_most(summary["price_ratio"])
            needs[which] = needs.get(which, 0) + 1
        settings.append({
            "setting": number, "name": name, "overrides": json.loads(overrides), "dials": json.loads(dials),
            "towns": towns, "n": len(towns), "failed": failed_years,
            "survived": sum(1 for town in towns if town["outcome"] == "survived"),
            "planned": planned,                      # how many years the towns were given
            "half_failed": half_failed(failed_years, len(towns)),
            "standing": _standing(failed_years, len(towns), max((town["years"] for town in towns), default=0)),
            "yearly": _yearly(con, number),
            "end": {
                "failed_year": spread(failed_years),
                "top10_shares": spread(s["top10_shares"] for s in summaries),
                "gini_shares": spread(s["gini_shares"] for s in summaries),
                "unhappy": {scope: spread(s["unhappy"][scope] for s in summaries if s["class_counts"][scope] > 0)
                            for scope in CLASSES},
            },
            "needs": needs,
        })
    dials: list[str] = []
    for s in settings:
        dials += [dial for dial in s["dials"] if dial not in dials]
    varied = []
    for dial in dials:
        rows = [{"setting": s["setting"], "value": s["dials"][dial], "base": s["setting"] == 0}
                for s in settings if dial in s["dials"]
                and (s["setting"] == 0 or any(item.split("=", 1)[0] == dial for item in s["overrides"]))]
        varied.append({"dial": dial, "rows": sorted(rows, key=lambda row: _order(row["value"]))})
    return {
        "batch": {"name": plan["name"], "code": meta["code"], "planned": int(meta["planned"]),
                  "finished": int(meta["finished"]), "seeds": plan["seeds"], "record": plan["record"],
                  "world": WORLD_NAMES.get(meta.get("world", "wef"), "WEF world")},   # a table from before there were two is WEF
        "settings": settings,
        "varied": varied,
    }


# --- words and numbers ------------------------------------------------------------------------------
def _e(text) -> str:
    return html.escape(str(text), quote=True)


def _fmt(unit: str, value: float) -> str:
    """A number as the page writes it: a share as a percentage to one place, money in whole
    dollars (the record is in cents), a count to one place when it is not whole."""
    if unit == "pct":
        return f"{100 * value:.1f}%"
    if unit == "money":
        return f"${value / 100:,.0f}"
    if unit == "count":
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"
    return f"{value:.2f}"


def _yr(years: float) -> str:
    """A point in time in years, to two places: most towns fail on a quarter, at .25 or .75."""
    return f"{years:.2f}"


def _count(n: int, one: str, many: str) -> str:
    return f"{n:,} {one if n == 1 else many}"


def _years(years: float) -> str:
    return f"{years:g} {'year' if years == 1 else 'years'}"


def _shown(unit: str, value: float) -> float:
    """A value in the units the side of a chart is marked in: per cent, dollars, or itself."""
    return value * 100 if unit == "pct" else value / 100 if unit == "money" else value


def _ticks(top: float, unit: str, most: int = 4) -> list[float]:
    """Round numbers from zero up to at least `top`, in the record's own units. Counts and
    dollars are marked in whole ones, so no two marks read the same."""
    least = {"money": 100.0, "count": 1.0}.get(unit, 0.0)
    if top <= 0:
        return [0, least or 1]
    rough = max(top / most, least)
    size = 10 ** math.floor(math.log10(rough))
    step = next(mult * size for mult in (1, 2, 2.5, 5, 10) if mult * size >= rough - 1e-12)
    if least and step % least:
        step = math.ceil(step / least) * least
    count = math.ceil(top / step - 1e-9)
    return [round(step * i, 10) for i in range(count + 1)]


def _axis(unit: str, value: float, step: float) -> str:
    """A mark on the side of a chart, with as many places as the step between marks needs."""
    amount, gap = _shown(unit, value), abs(_shown(unit, step))
    sign, tail = ("$" if unit == "money" else ""), ("%" if unit == "pct" else "")
    if gap >= 1_000_000:
        return f"{sign}{amount / 1_000_000:g}m{tail}"
    places = 0 if gap >= 1 or float(gap).is_integer() else min(3, max(1, math.ceil(-math.log10(gap) - 1e-9)))
    if gap < 1 and round(gap, places) != gap:
        places = min(3, places + 1)
    return f"{sign}{amount:,.{places}f}{tail}"


def _year_ticks(first: float, last: float) -> list[int]:
    """At most nine round years from `first` to `last`."""
    span = max(1, last - first)
    step = next(mult * 10 ** power for power in range(0, 12) for mult in (1, 2, 5) if span / (mult * 10 ** power) <= 8)
    start = math.ceil(first / step) * step
    return list(range(int(start), int(math.floor(last)) + 1, step))


def _colour(c) -> str:
    return "var(--ink-series)" if c == "ink" else f"var(--series-{c})"


# --- how the towns ended: one dot a town ------------------------------------------------------------
DOT = 4.0          # the radius of a town's dot
GAP = 9.5          # the least distance between two dots in a row


def _lanes(xs: list[float]) -> list[int]:
    """Dots that would overlap are moved up and down the row: 0, -1, 1, -2, 2 and so on.
    `xs` is in order from left to right."""
    last: dict[int, float] = {}
    out = []
    for x in xs:
        lane, n = 0, 0
        while lane in last and x - last[lane] < GAP:
            n += 1
            lane = -((n + 1) // 2) if n % 2 else n // 2
        last[lane] = x
        out.append(lane)
    return out


def _after(setting: dict) -> float:
    """How long the towns still standing had stood when their runs ended."""
    return max((town["years"] for town in setting["towns"] if town["outcome"] == "survived"), default=0)


def _half_words(setting: dict) -> str:
    """When half of all the towns had failed, in words; nothing when every town failed."""
    if not setting["survived"] or not setting["failed"]:
        return ""
    if setting["half_failed"] is None:
        return "more than half never failed"
    return f"half had failed by year {_yr(setting['half_failed'])}"


def _ended_words(setting: dict) -> str:
    """'4 of 8 failed, 4 still standing after 4 years; half had failed by year 3.75'."""
    n, failed, standing = setting["n"], len(setting["failed"]), setting["survived"]
    if n == 0:
        return "no town finished"
    if failed == 0:
        first = "The one town did not fail" if n == 1 else f"None of the {n} towns failed"
        return f"{first}; still standing after {_years(_after(setting))}"
    words = f"{failed} of {n} failed"
    if standing:
        words += f", {standing} still standing after {_years(_after(setting))}; {_half_words(setting)}"
    return words


def _dot_span(rows: list[tuple[str, dict]], horizon: float) -> tuple[int, int]:
    """The years the line of dots covers. From nought when towns fail early in the time they
    were given. When every failure comes late, as when all fail between years 13 and 21 of 60,
    the line is drawn round the failures, so the dots keep their shape; the chart of the share
    still standing shows the whole of the time given."""
    failed = [year for _, setting in rows for year in setting["failed"]]
    last = max(1, math.ceil(horizon))
    if not failed:
        return 0, last
    low, high = min(failed), max(failed)
    start = 0 if low < 0.4 * high else max(0, math.floor(low) - 1)
    return start, min(max(math.ceil(high) + 1, start + 1), last)


def _strip_svg(rows: list[tuple[str, dict]], horizon: float) -> str:
    """The year each town failed: a row for each setting, a dot for each town, the middle of
    the towns that failed marked with a tick and their middle half with a bar."""
    width, left, right = 640.0, 12.0, 12.0
    plot = width - left - right
    start, end = _dot_span(rows, horizon)

    def x(year: float) -> float:
        return left + plot * (year - start) / (end - start)

    parts, y = [], 6.0
    for label, setting in rows:
        towns = sorted((town for town in setting["towns"] if town["failed_year"] is not None),
                       key=lambda town: (town["failed_year"], town["seed"]))
        lanes = _lanes([x(town["failed_year"]) for town in towns])
        reach = max((abs(lane) for lane in lanes), default=0)
        half = reach * GAP + DOT + 5
        parts.append(f'<text class="label" x="{left:.1f}" y="{y + 12:.1f}">{_e(label)}</text>')
        parts.append(f'<text x="{left:.1f}" y="{y + 27:.1f}">{_e(_ended_words(setting))}</text>')
        middle = y + 37 + half
        row = [f'<g class="row" data-setting="{setting["setting"]}">',
               f'<line x1="{left:.1f}" x2="{width - right:.1f}" y1="{middle:.1f}" y2="{middle:.1f}" stroke="var(--grid)"/>']
        found = setting["end"]["failed_year"]
        if found:
            whose = (f'of the {found["n"]} that failed, the middle one' if setting["survived"] else "the middle town")
            row.append(f'<rect class="half" x="{x(found["q1"]):.1f}" y="{middle - half:.1f}" '
                       f'width="{max(1.0, x(found["q3"]) - x(found["q1"])):.1f}" height="{2 * half:.1f}" rx="3" '
                       f'fill="var(--wash)" data-tip="{_e(label)}|{whose} failed in year {_yr(found["median"])}|'
                       f'middle half {_yr(found["q1"])} to {_yr(found["q3"])}|'
                       f'first {_yr(found["min"])}, last {_yr(found["max"])}|'
                       f'{_count(found["n"], "town", "towns")} failed"/>')
            row.append(f'<line x1="{x(found["median"]):.1f}" x2="{x(found["median"]):.1f}" y1="{middle - half:.1f}" '
                       f'y2="{middle + half:.1f}" stroke="var(--text-primary)" stroke-width="2"/>')
        for town, lane in zip(towns, lanes):
            row.append(f'<circle cx="{x(town["failed_year"]):.1f}" cy="{middle + lane * GAP:.1f}" r="{DOT:g}" '
                       f'fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="1.5" '
                       f'data-tip="Seed {town["seed"]}|failed in year {_yr(town["failed_year"])} (week {town["failed_week"]})"/>')
        row.append("</g>")
        parts.append("".join(row))
        y = middle + half + 14
    for year in _year_ticks(start, end):
        parts.append(f'<line x1="{x(year):.1f}" x2="{x(year):.1f}" y1="{y:.1f}" y2="{y + 4:.1f}" stroke="var(--axis)"/>')
        parts.append(f'<text x="{x(year):.1f}" y="{y + 17:.1f}" text-anchor="middle">{year}</text>')
    parts.append(f'<line x1="{left:.1f}" x2="{width - right:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--axis)"/>')
    parts.append(f'<text x="{width - right:.1f}" y="{y + 32:.1f}" text-anchor="end">year the town failed</text>')
    height = y + 38
    return (f'<svg viewBox="0 0 {width:g} {height:.0f}" role="img" aria-label="The year each town failed, '
            f'one dot for each town">{"".join(parts)}</svg>')


# --- the share of towns still standing --------------------------------------------------------------
DASH = ("", "7 4", "2 3", "9 3 2 3")     # the lines of one chart differ in more than colour


def _line_style(index: int) -> tuple[str, str]:
    return _colour("ink" if index == 0 else index), DASH[index % len(DASH)]


def _standing_svg(rows: list[tuple[str, dict]], horizon: float) -> str:
    """The share of towns still standing, year by year, as steps. At most four settings."""
    width, height, left, right, top, bottom = 640.0, 230.0, 40.0, 16.0, 10.0, 26.0
    plot_w, plot_h = width - left - right, height - top - bottom
    horizon = max(1.0, math.ceil(horizon))

    def x(year: float) -> float:
        return left + plot_w * year / horizon

    def y(share: float) -> float:
        return top + plot_h * (1 - share)

    parts = []
    for share in (0, 0.25, 0.5, 0.75, 1):
        parts.append(f'<line x1="{left:.1f}" x2="{left + plot_w:.1f}" y1="{y(share):.1f}" y2="{y(share):.1f}" '
                     f'stroke="var(--grid)"/>')
        parts.append(f'<text x="{left - 6:.1f}" y="{y(share) + 4:.1f}" text-anchor="end">{100 * share:.0f}%</text>')
    for year in _year_ticks(0, horizon):
        parts.append(f'<text x="{x(year):.1f}" y="{height - 8:.1f}" text-anchor="middle">{year}</text>')
    for index, (_, setting) in enumerate(rows):
        steps = setting["standing"]
        if not steps:
            continue
        colour, dash = _line_style(index)
        path = [f"M{x(0):.1f},{y(1.0):.1f}"]
        for year, share in steps[1:]:
            path.append(f"H{x(year):.1f}V{y(share):.1f}")
        path.append(f"H{x(max(steps[-1][0], setting['planned'])):.1f}")       # level to the end of the years given
        dashed = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<path class="series" d="{"".join(path)}" fill="none" stroke="{colour}" stroke-width="2" '
                     f'stroke-linejoin="round"{dashed}/>')
        for year, share in steps[1:]:
            parts.append(f'<rect class="hit" x="{x(year) - 7:.1f}" y="{y(share) - 7:.1f}" width="14" height="14" '
                         f'fill="transparent" data-tip="Year {_yr(year)}|{_e(setting["name"])}|'
                         f'{round(share * setting["n"])} of {setting["n"]} towns still standing"/>')
    return (f'<svg viewBox="0 0 {width:g} {height:g}" role="img" aria-label="The share of towns still standing, '
            f'year by year">{"".join(parts)}</svg>')


def _legend(rows: list[tuple[str, dict]]) -> str:
    """The key to the lines of one chart, each with the share still standing at the end."""
    items = []
    for index, (label, setting) in enumerate(rows):
        colour, dash = _line_style(index)
        dashed = f' stroke-dasharray="{dash}"' if dash else ""
        end = f"{100 * setting['standing'][-1][1]:.0f}% still standing at the end" if setting["standing"] else "no town finished"
        items.append(f'<li><svg class="key" viewBox="0 0 26 6" width="26" height="6" aria-hidden="true">'
                     f'<line x1="0" y1="3" x2="26" y2="3" stroke="{colour}" stroke-width="2"{dashed}/></svg>'
                     f'{_e(label)}: {end}</li>')
    return f'<ul class="legend">{"".join(items)}</ul>'


# --- the towns year by year: the middle town, the middle half, the range ----------------------------
# (measure, title, unit, colour, what it is). Every measure of the table but all/n, which is
# the same number as the people in town.
CHARTS = (
    ("all/unhappy", "Unhappy: everyone", "pct", "ink", "The share of everyone in town who is unhappy."),
    ("owner/unhappy", "Unhappy: owner class", "pct", 1, "The share of the owner class who are unhappy."),
    ("working/unhappy", "Unhappy: working class", "pct", 2, "The share of the working class who are unhappy."),
    ("out/unhappy", "Unhappy: out of work", "pct", 3, "The share of the out of work who are unhappy."),
    ("town/wage", "Staff wage", "money", "ink", "The average weekly wage of staff."),
    ("town/basket", "Weekly basket", "money", "ink", "What the four base needs cost a week."),
    ("town/affordability", "Basket against the staff wage", "pct", "ink", "The basket as a share of the staff wage."),
    ("town/jobless_rate", "Jobless rate", "pct", "ink", "The share of people without a job."),
    ("town/population", "People in town", "count", "ink", "How many people live in town."),
    ("owner/n", "Owner class", "count", 1, "How many people are in the owner class."),
    ("working/n", "Working class", "count", 2, "How many people are in the working class."),
    ("out/n", "Out of work", "count", 3, "How many people are out of work."),
    ("all/cash_median", "Cash: the middle person", "money", "ink", "The cash of the middle person in town."),
    ("owner/cash_median", "Cash: the middle of the owner class", "money", 1, "The cash of the middle person in the owner class."),
    ("working/cash_median", "Cash: the middle of the working class", "money", 2, "The cash of the middle person in the working class."),
    ("out/cash_median", "Cash: the middle of the out of work", "money", 3, "The cash of the middle person out of work."),
    ("town/top10_shares", "Shares held by the top tenth", "pct", "ink", "The share of all shares held by the tenth of people who hold most."),
    ("town/gini_shares", "Gini of shares", "plain", "ink", "How unevenly shares are held: 0 is evenly, 1 is all with one person."),
    ("town/top10_cash", "Cash held by the top tenth", "pct", "ink", "The share of all cash held by the tenth of people who hold most."),
    ("town/gini_cash", "Gini of cash", "plain", "ink", "How unevenly cash is held: 0 is evenly, 1 is all with one person."),
    ("town/homes", "Homes standing", "count", "ink", "How many homes stand in town."),
    ("town/homes_vacant", "Homes empty", "count", "ink", "How many homes have nobody living in them."),
    ("all/homeless", "People with no home", "count", "ink", "How many people have no home."),
    ("town/destitute", "Destitute", "count", "ink", "How many people cannot pay for food or a home."),
    ("town/firms", "Firms", "count", "ink", "How many firms are trading."),
    ("town/needs_invented", "Needs invented", "count", "ink", "How many needs beyond the first four have been invented."),
    ("town/money", "Money in town", "money", "ink", "All the cash held by people and firms."),
    ("town/loans_firms", "Loans to firms", "money", "ink", "What firms owe the bank."),
    ("town/loans_people", "Loans to people", "money", "ink", "What people owe the bank."),
)
# The RTR world's own (stage 3, 20/11/2026): a batch of the WEF world keeps none, so draws none.
RTR_CHARTS = (
    ("town/wage_offer", "The rate for someone taken on now", "money", "ink",
     "What a firm offers someone it takes on now. Staff keep the pay they were taken on at."),
    ("town/homes_lived_in_by_owner", "Homes lived in by their owner", "count", "ink",
     "Homes owned by the person who lives in them."),
    ("town/homes_let_private", "Homes let by a small landlord", "count", "ink",
     "Homes a person owns and lets to someone else."),
    ("town/homes_foreclosed", "Homes taken back by the bank", "count", "ink",
     "Homes the bank has taken back and not yet sold."),
    ("town/basket_asking", "Asking basket", "money", "ink",
     "The cheapest price on offer for each of the four needs, as firms ask it. In the RTR world a firm with no "
     "tenants or customers can go on raising what it asks; the weekly basket is what people pay."),
    ("town/sets_owned", "Appliance sets owned", "count", "ink", "Appliance sets people own rather than rent."),
    ("town/home_loans", "Loans against homes", "money", "ink", "What people owe the bank on homes they bought or built."),
    ("town/makers", "People with a side hustle", "count", "ink",
     "People selling their own work or making things on the side."),
    ("town/small_businesses", "Small businesses", "count", "ink", "Side hustles grown into businesses with staff."),
)


def _fan_svg(rows: list[dict], unit: str, colour: str, title: str) -> str:
    """One measure across the towns, year by year: the middle town as a line, the middle
    half as a band, the whole range as a paler band. Pointing at a year gives its numbers."""
    width, height, left, right, top, bottom = 420.0, 200.0, 54.0, 10.0, 8.0, 22.0
    plot_w, plot_h = width - left - right, height - top - bottom
    first, last = rows[0]["year"], rows[-1]["year"]
    ticks = _ticks(max(row["max"] for row in rows), unit)
    ceiling, step = ticks[-1], ticks[1] - ticks[0]

    def x(year: float) -> float:
        return left + plot_w / 2 if last == first else left + plot_w * (year - first) / (last - first)

    def y(value: float) -> float:
        return top + plot_h * (1 - value / ceiling)

    parts = []
    for tick in ticks:
        parts.append(f'<line x1="{left:.1f}" x2="{left + plot_w:.1f}" y1="{y(tick):.1f}" y2="{y(tick):.1f}" '
                     f'stroke="var(--grid)"/>')
        parts.append(f'<text x="{left - 6:.1f}" y="{y(tick) + 4:.1f}" text-anchor="end">{_axis(unit, tick, step)}</text>')
    for year in _year_ticks(first, last):
        parts.append(f'<text x="{x(year):.1f}" y="{height - 6:.1f}" text-anchor="middle">{year}</text>')
    if len(rows) == 1:
        row, at = rows[0], x(first)
        parts.append(f'<line x1="{at:.1f}" x2="{at:.1f}" y1="{y(row["max"]):.1f}" y2="{y(row["min"]):.1f}" '
                     f'stroke="{colour}" stroke-width="2" opacity="0.3"/>')
        parts.append(f'<line x1="{at:.1f}" x2="{at:.1f}" y1="{y(row["q3"]):.1f}" y2="{y(row["q1"]):.1f}" '
                     f'stroke="{colour}" stroke-width="10" opacity="0.4"/>')
        parts.append(f'<line x1="{at - 9:.1f}" x2="{at + 9:.1f}" y1="{y(row["median"]):.1f}" y2="{y(row["median"]):.1f}" '
                     f'stroke="{colour}" stroke-width="2"/>')
    else:
        def band(low: str, high: str) -> str:
            along = [f"{x(row['year']):.1f},{y(row[high]):.1f}" for row in rows]
            back = [f"{x(row['year']):.1f},{y(row[low]):.1f}" for row in reversed(rows)]
            return " ".join(along + back)
        parts.append(f'<polygon points="{band("min", "max")}" fill="{colour}" opacity="0.14"/>')
        parts.append(f'<polygon points="{band("q1", "q3")}" fill="{colour}" opacity="0.3"/>')
        line = " ".join(f"{x(row['year']):.1f},{y(row['median']):.1f}" for row in rows)
        parts.append(f'<polyline class="series" points="{line}" fill="none" stroke="{colour}" stroke-width="2" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
    gap = plot_w if last == first else plot_w / (last - first)
    for row in rows:
        tip = (f'Year {row["year"]}|middle town {_fmt(unit, row["median"])}|'
               f'middle half {_fmt(unit, row["q1"])} to {_fmt(unit, row["q3"])}|'
               f'all towns {_fmt(unit, row["min"])} to {_fmt(unit, row["max"])}|{_count(row["n"], "town", "towns")}')
        start = max(left, x(row["year"]) - gap / 2)
        end = min(left + plot_w, x(row["year"]) + gap / 2)
        parts.append(f'<rect class="hit" x="{start:.1f}" y="{top:.1f}" width="{max(1.0, end - start):.1f}" '
                     f'height="{plot_h:.1f}" fill="transparent" data-tip="{_e(tip)}"/>')
    return (f'<svg viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{_e(title)}, year by year across the towns">'
            f'{"".join(parts)}</svg>')


def _fan_card(setting: dict, measure: str, title: str, unit: str, colour, note: str) -> str:
    rows = setting["yearly"].get(measure)
    if not rows:
        return ""
    rests = f'{_count(rows[0]["n"], "town", "towns")} in year {rows[0]["year"]}'
    if len(rows) > 1:
        rests += f' and {rows[-1]["n"]} in year {rows[-1]["year"]}'
    body = "".join(
        f'<tr><td>{row["year"]}</td><td>{row["n"]}</td><td>{_fmt(unit, row["min"])}</td><td>{_fmt(unit, row["q1"])}</td>'
        f'<td>{_fmt(unit, row["median"])}</td><td>{_fmt(unit, row["q3"])}</td><td>{_fmt(unit, row["max"])}</td></tr>'
        for row in rows)
    return f"""<figure class="card" data-setting="{setting['setting']}" data-measure="{_e(measure)}">
<div class="card-title">{_e(title)}</div>
<div class="card-note">{_e(note)} Rests on {rests}.</div>
<div class="plot">{_fan_svg(rows, unit, _colour(colour), title)}</div>
<details><summary>Table</summary><div class="tablewrap"><table>
<thead><tr><th>Year</th><th>Towns</th><th>Lowest</th><th>First quarter</th><th>Middle</th><th>Third quarter</th><th>Highest</th></tr></thead>
<tbody>{body}</tbody></table></div></details>
</figure>"""


def _fans(setting: dict) -> str:
    cards = "".join(_fan_card(setting, *spec) for spec in CHARTS + RTR_CHARTS)
    return f'<div class="grid">{cards}</div>' if cards else '<p class="empty">No town under this setting was still standing at the end of a year.</p>'


# --- the page ---------------------------------------------------------------------------------------
def _groups(data: dict) -> list[list[dict]]:
    """Settings to draw on one chart: never more than four. All of them when they are few;
    otherwise the base with each varied dial's values, in threes."""
    settings = data["settings"]
    if len(settings) <= 4:
        return [settings]
    by_number = {s["setting"]: s for s in settings}
    groups, drawn = [], {0}
    for dial in data["varied"]:
        others = [by_number[row["setting"]] for row in dial["rows"] if not row["base"]]
        for i in range(0, len(others), 3):
            groups.append([settings[0]] + others[i:i + 3])
            drawn |= {s["setting"] for s in others[i:i + 3]}
    left_over = [s for s in settings if s["setting"] not in drawn]           # a setting with no finished town yet
    for i in range(0, len(left_over), 3):
        groups.append([settings[0]] + left_over[i:i + 3])
    return groups


def _horizon(data: dict) -> float:
    """How far the line of years runs: as long as any town was given, or ran."""
    return max([s["planned"] for s in data["settings"]]
               + [town["years"] for s in data["settings"] for town in s["towns"]] + [1.0])


def _hero(data: dict) -> tuple[str, str]:
    if not data["settings"] or data["batch"]["finished"] == 0:
        return "No town of this batch has finished", "Run the batch again to make its towns."
    base = data["settings"][0]
    if base["n"] == 0:
        return "No town under the base has finished", "The other settings are below. Run the batch again to make the base's towns."
    n, failed, found = base["n"], len(base["failed"]), base["end"]["failed_year"]
    after = _years(_after(base))
    standing = f" {_count(base['survived'], 'was', 'were')} still standing after {after}." if base["survived"] else ""
    if failed == 0:
        return ("The one town did not fail" if n == 1 else f"None of the {n} towns failed", f"Still standing after {after}.")
    if n == 1:
        return f"The one town failed in year {_yr(found['median'])}", ""
    hero = f"{failed} of {n} towns failed"
    if failed == 1:
        return hero, f"It failed in year {_yr(found['median'])}.{standing}"
    if failed == n:
        return hero, (f"The middle one failed in year {_yr(found['median'])}, the first in year {_yr(found['min'])} "
                      f"and the last in year {_yr(found['max'])}.")
    half = (f" Half of all {n} towns had failed by year {_yr(base['half_failed'])}." if base["half_failed"] is not None
            else " More than half never failed.")
    return hero, (f"Of the {failed} that failed, the middle one failed in year {_yr(found['median'])}, the first in "
                  f"year {_yr(found['min'])} and the last in year {_yr(found['max'])}.{half}{standing}")


def _seeds_words(seeds: list[int]) -> str:
    if seeds and seeds == list(range(seeds[0], seeds[-1] + 1)) and len(seeds) > 1:
        return f"{len(seeds):,} seeds ({seeds[0]} to {seeds[-1]})"
    return _count(len(seeds), "seed", "seeds") + (f" ({', '.join(map(str, seeds))})" if len(seeds) <= 12 else "")


def _header(data: dict) -> str:
    info = data["batch"]
    hero, sub = _hero(data)
    base = data["settings"][0]["name"] if data["settings"] else ""
    missing = info["planned"] - info["finished"]
    gap = ""
    if missing:
        gap = (f'<div class="notice" role="note"><span><strong>{missing} of {info["planned"]} towns '
               f'{"is" if missing == 1 else "are"} missing or unfinished.</strong> '
               f'Run the batch again to finish {"it" if missing == 1 else "them"}. '
               f'Everything below is over the towns that finished. While a batch is still running that is not a '
               f'fair sample: the towns that fail soonest finish first.</span></div>')
    return f"""
<header>
  <h1>The {_e(info['world'])}: many towns</h1>
  <div class="sub">Batch {_e(info['name'])}. {_count(info['finished'], 'town', 'towns')}:
  {_count(len(data['settings']), 'setting', 'settings')} on {_e(_seeds_words(info['seeds']))}.
  Code fingerprint {_e(info['code'])}.</div>
  <div class="hero">{_e(hero)}</div>
  <div class="herosub">{_e(sub)} {_e("Under the base: " + base + "." if len(data['settings']) > 1 else "")}</div>
  <div class="notice" role="note">
    <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5 15 14H1z" fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6v4M8 11.6v.6"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    <span><strong>Untuned.</strong> The build so far proves the machinery: the accounts balance and every
    week is recorded. The starting values have not been tested, so read this page as a first look,
    not a finding.</span>
  </div>
  {gap}
</header>
"""


def _ended(data: dict) -> str:
    settings = data["settings"]
    horizon = _horizon(data)
    charts = "".join(
        f'<figure class="card wide"><div class="card-title">The share of towns still standing</div>'
        f'<div class="card-note">It steps down each time a town fails. Point at a step for the count.</div>'
        f'{_legend([(s["name"], s) for s in group])}'
        f'<div class="plot">{_standing_svg([(s["name"], s) for s in group], horizon)}</div></figure>'
        for group in _groups(data))
    return f"""
<section id="ended"><h2>How the towns ended</h2>
<div class="grid">
<figure class="card wide"><div class="card-title">The year each town failed</div>
<div class="card-note">One dot for each town that failed. The tick is the middle of the towns that failed and
the shaded bar their middle half. A town still standing at the end has no dot and is counted in the words above
its row. The line of years covers the years in which towns failed; the chart under this one shows the whole of
the {_years(horizon)} the towns were given.</div>
<div class="plot">{_strip_svg([(s["name"], s) for s in settings], horizon)}</div></figure>
{charts}
</div></section>
"""


def _years_section(data: dict) -> str:
    settings = data["settings"]
    if not settings:
        return '<section id="years"><h2>The towns year by year</h2></section>'
    folded = "".join(f'<details class="fold"><summary>{_e(s["name"])}</summary>{_fans(s)}</details>'
                     for s in settings[1:])
    return f"""
<section id="years"><h2>The towns year by year</h2>
<p class="lead">Each chart is one measure at the end of each year. The line is the middle town, the darker band
the middle half of towns, the paler band every town. A year's figure is over the towns still standing at the
end of that year, so late years rest on fewer towns: each chart says how many. A town that fails in the last
week of a year is not in that year's figure.
{_e("These are for the base, " + settings[0]["name"] + ". The other settings are folded below.") if len(settings) > 1 else ""}</p>
{_fans(settings[0])}
{folded}
</section>
"""


def _mid(found: dict | None, unit: str, half: bool = True) -> str:
    """'16.50 (15.50 to 17.25)': the middle, then the middle half."""
    if not found:
        return "none"

    def one(value: float) -> str:
        return _yr(value) if unit == "years" else _fmt(unit, value)

    words = one(found["median"])
    return words + (f' ({one(found["q1"])} to {one(found["q3"])})' if half and found["n"] > 1 else "")


def _half_cell(setting: dict) -> str:
    if setting["n"] == 0:
        return "none"
    return _yr(setting["half_failed"]) if setting["half_failed"] is not None else "more than half never failed"


def _end_section(data: dict) -> str:
    """Each setting's towns in their last week. With a few settings the measures run down
    the page and the settings across, which fits a narrow window; with many, the other way."""
    def needs(s: dict) -> str:
        return ", ".join(f"{need} {count}" for need, count in
                         sorted(s["needs"].items(), key=lambda item: (-item[1], str(item[0])))) or "none"

    measures = [
        ("Towns", lambda s: str(s["n"])),
        ("Failed", lambda s: str(len(s["failed"]))),
        ("Still standing", lambda s: str(s["survived"])),
        ("Year of failure, of the towns that failed", lambda s: _mid(s["end"]["failed_year"], "years")),
        ("Half of all the towns had failed by year", _half_cell),
        ("Shares held by the top tenth", lambda s: _mid(s["end"]["top10_shares"], "pct")),
        ("Gini of shares", lambda s: _mid(s["end"]["gini_shares"], "plain", half=False)),
        ("Unhappy: everyone", lambda s: _mid(s["end"]["unhappy"]["all"], "pct", half=False)),
        ("Unhappy: owner class", lambda s: _mid(s["end"]["unhappy"]["owner"], "pct", half=False)),
        ("Unhappy: working class", lambda s: _mid(s["end"]["unhappy"]["working"], "pct", half=False)),
        ("Unhappy: out of work", lambda s: _mid(s["end"]["unhappy"]["out"], "pct", half=False)),
        ("Need whose price had risen most, and in how many towns", needs),
    ]
    settings = data["settings"]
    if len(settings) <= 3:
        head = "<th>In the last week</th>" + "".join(f"<th>{_e(s['name'])}</th>" for s in settings)
        body = "".join(f"<tr><td>{_e(label)}</td>" + "".join(f"<td>{_e(value(s))}</td>" for s in settings) + "</tr>"
                       for label, value in measures)
    else:
        head = "<th>Setting</th>" + "".join(f"<th>{_e(label)}</th>" for label, _ in measures)
        body = "".join(f"<tr><td>{_e(s['name'])}</td>" + "".join(f"<td>{_e(value(s))}</td>" for _, value in measures)
                       + "</tr>" for s in settings)
    return f"""
<section id="end"><h2>When the towns ended</h2>
<p class="lead">Each town's last week: the week it failed, or the last week of its run if it was still standing.
A figure is the middle town, with the middle half of towns in brackets. The year of failure is over the towns
that failed only; the line under it counts the towns still standing too.</p>
<div class="card"><div class="tablewrap tall"><table class="wrap">
<thead><tr>{head}</tr></thead>
<tbody>{body}</tbody></table></div></div>
</section>
"""


def _dials_section(data: dict) -> str:
    if not data["varied"]:
        return ""
    by_number = {s["setting"]: s for s in data["settings"]}
    horizon = _horizon(data)
    blocks = []
    for dial in data["varied"]:
        lines, strip = [], []
        for row in dial["rows"]:
            s = by_number[row["setting"]]
            found = s["end"]["failed_year"]
            value = f'{row["value"]}' + (" (the base)" if row["base"] else "")
            lines.append(
                f'<tr><td>{_e(value)}</td><td>{s["n"]}</td><td>{len(s["failed"])}</td><td>{s["survived"]}</td>'
                f'<td>{_mid(found, "years")}</td>'
                f'<td>{(_yr(found["min"]) + " to " + _yr(found["max"])) if found else "none"}</td>'
                f'<td>{_e(_half_cell(s))}</td></tr>')
            strip.append((f'{dial["dial"]} = {value}', s))
        blocks.append(f"""<figure class="card wide"><div class="card-title">{_e(dial["dial"])}</div>
<div class="card-note">The base, and the same seeds with this one dial changed.</div>
<div class="plot">{_strip_svg(strip, horizon)}</div>
<div class="tablewrap"><table class="wrap"><thead><tr><th>{_e(dial["dial"])}</th><th>Towns</th><th>Failed</th><th>Still standing</th>
<th>Year of failure, of the towns that failed: middle (middle half)</th><th>First to last</th>
<th>Half of all the towns had failed by year</th></tr></thead>
<tbody>{"".join(lines)}</tbody></table></div></figure>""")
    return f"""
<section id="dials"><h2>What each dial did</h2>
<p class="lead">One dial is changed at a time from the base. The same seed under two settings is not the same
town: a changed dial changes what happens next. So compare the groups of towns, not one seed with itself.
Where some towns never failed, read "half of all the towns had failed by" and not the middle of those that
failed: a setting under which only a few towns failed, and those early, would otherwise look the worst.</p>
<div class="grid">{"".join(blocks)}</div>
</section>
"""


def _towns_section(data: dict) -> str:
    rows = []
    for s in data["settings"]:
        for town in s["towns"]:
            ended = (f'failed in year {_yr(town["failed_year"])}' if town["failed_year"] is not None
                     else f'still standing after {_years(town["years"])}')
            full = _yr(town["full_year"]) if town["full_year"] is not None else "never"
            rows.append(f'<tr><td>{_e(s["name"])}</td><td>{town["seed"]}</td><td>{ended}</td><td>{full}</td>'
                        f'<td><code>{_e(town["fingerprint"][:16])}</code></td><td><code>{_e(town["folder"])}</code></td></tr>')
    return f"""
<section id="towns"><h2>Every town</h2>
<details{" open" if len(rows) <= 40 else ""}><summary>{_count(len(rows), "town", "towns")}</summary>
<div class="card"><div class="tablewrap tall"><table class="folders">
<thead><tr><th>Setting</th><th>Seed</th><th>How it ended</th><th>Town full in year</th><th>Record fingerprint</th>
<th>Folder, inside the batch</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div></div></details>
</section>
"""


def _read_section(data: dict) -> str:
    record = ("Every person and firm is recorded once a quarter in a batch town" if data["batch"]["record"]
              else "Every person and firm is recorded every week in these towns")
    return f"""
<section id="read"><footer><h2>How to read this</h2>
<p><strong>One town is one run.</strong> Every town here was made by the same rules from a different seed, so
the differences between towns under one setting are luck, and the spread shows how much luck there is.</p>
<p><strong>Failed</strong> means what it means everywhere in this model: the first week that the set share of
all people (90% as written) are unhappy. A town stops there.</p>
<p><strong>The middle</strong> is the median town. <strong>The middle half</strong> runs from the first
quartile to the third, in a straight line between towns. With few towns these are rough.</p>
<p><strong>Still standing.</strong> A figure for a year covers only the towns that had not failed by the end of
it. A town that fails in the last week of a year is not in that year's figure. Where few are left the figure
rests on few towns, and each chart says how many.</p>
<p><strong>The year of failure</strong> is given two ways. The middle of the towns that failed says nothing of
the towns that never did. "Half of all the towns had failed by" counts them, and is the one to compare
settings by.</p>
<p><strong>A class with nobody in it</strong> has no figure that year, so it rests on fewer towns still.</p>
<p><strong>The need whose price had risen most</strong> is, of the four base needs, the one whose price was
highest against its starting price in the town's last week. Needs within a tenth of a percent of the highest
are counted as level with it.</p>
<p><strong>To see one town in full.</strong> {record}; every event and every weekly measure is kept. Its
dashboard and town view can be built from its folder:
<code>python -m engine dashboard FOLDER</code> and <code>python -m engine town FOLDER</code>.
To make the same town again with every person recorded every week, from its world's folder:
<code>python run.py --config FOLDER/config.json --set snapshot_every=1</code>.
It has the same record fingerprint.</p>
<p class="fine">Built only from batch.sqlite. Code fingerprint {_e(data["batch"]["code"])}.</p>
</footer></section>
"""


def build_batch_page(batch_dir) -> pathlib.Path:
    """Write `batch.html` in the batch's folder from its `batch.sqlite` alone."""
    from .batch import _open
    batch_dir = pathlib.Path(batch_dir)
    table = batch_dir / "batch.sqlite"
    if not table.is_file():
        raise FileNotFoundError(f"no batch.sqlite in {batch_dir}")
    con = _open(table)
    try:
        data = report_data(con)
    finally:
        con.close()
    body = (_header(data) + _ended(data) + _years_section(data) + _end_section(data) + _dials_section(data)
            + _towns_section(data) + _read_section(data))
    page = (TEMPLATE.replace("__TITLE__", _e(f"{data['batch']['world']} batch {data['batch']['name']}"))
            .replace("__BODY__", body))
    out = batch_dir / "batch.html"
    out.write_text(page, encoding="utf-8")
    return out


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
  --wash: rgba(11,11,11,0.07); --ink-series: #52514e; --warning: #fab219;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --wash: rgba(255,255,255,0.09); --ink-series: #c3c2b7; --warning: #fab219;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --wash: rgba(255,255,255,0.09); --ink-series: #c3c2b7; --warning: #fab219;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1320px; margin: 0 auto; padding: 24px 16px 56px; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 17px; font-weight: 600; margin: 32px 0 12px; }
.sub, .herosub, .lead { color: var(--text-secondary); font-size: 14px; }
.lead { max-width: 85ch; margin: 0 0 12px; }
.hero { font-size: 44px; font-weight: 600; line-height: 1.1; margin: 22px 0 6px; letter-spacing: -0.01em; }
.herosub { font-size: 15px; }
.notice { display: flex; gap: 10px; align-items: flex-start; margin: 18px 0; padding: 10px 14px;
  background: var(--surface-1); border: 1px solid var(--border); border-left: 4px solid var(--warning);
  border-radius: 8px; font-size: 14px; color: var(--text-secondary); }
.notice strong { color: var(--text-primary); }
.icon { width: 16px; height: 16px; flex: none; margin-top: 2px; color: var(--text-primary); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 14px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px 10px; margin: 0; min-width: 0; }
.card.wide { grid-column: 1 / -1; }
.card-title { font-size: 15px; font-weight: 600; }
.card-note { font-size: 13px; color: var(--text-secondary); margin: 2px 0 8px; }
.legend { display: flex; flex-direction: column; gap: 3px; font-size: 12.5px; color: var(--text-secondary);
  margin: 0 0 6px; padding: 0; list-style: none; }
.legend li { display: flex; align-items: center; gap: 8px; }
.legend .key { flex: none; }
.plot svg { display: block; width: 100%; height: auto; overflow: visible; }
.card.wide .plot svg { max-width: 760px; }
.plot text { font: 11.5px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted);
  font-variant-numeric: tabular-nums; }
.plot text.label { fill: var(--text-secondary); font-size: 12px; }
.plot .hit:hover { fill: var(--wash); }
.plot circle:hover { stroke: var(--text-primary); }
.empty { color: var(--muted); font-size: 13px; padding: 24px 0; }
details > summary { cursor: pointer; font-size: 13px; color: var(--text-secondary); padding: 4px 0; }
details.fold { margin-top: 14px; }
details.fold > summary { font-size: 15px; font-weight: 600; color: var(--text-primary); padding: 8px 0; }
.tablewrap { max-height: 300px; overflow: auto; margin-top: 4px; }
.tablewrap.tall { max-height: 560px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: right; padding: 4px 10px; border-bottom: 1px solid var(--grid);
  font-variant-numeric: tabular-nums; white-space: nowrap; }
th { position: sticky; top: 0; background: var(--surface-1); color: var(--text-secondary); font-weight: 600;
  white-space: normal; vertical-align: bottom; }
th:first-child, td:first-child { text-align: left; }
table.wrap td { white-space: normal; }
table.folders td:last-child { text-align: left; }
code { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
#tip { position: fixed; z-index: 10; pointer-events: none; display: none; min-width: 140px; max-width: 320px;
  background: var(--surface-1); color: var(--text-primary); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 12.5px; box-shadow: 0 6px 24px rgba(0,0,0,0.14); }
#tip .when { font-weight: 600; margin-bottom: 3px; }
footer p { font-size: 14px; color: var(--text-secondary); max-width: 85ch; margin: 6px 0; }
footer strong { color: var(--text-primary); }
footer .fine { font-size: 12.5px; color: var(--muted); }
</style>
</head>
<body class="viz-root">
<main>
__BODY__
</main>
<div id="tip" role="status" aria-live="polite"></div>
<script>
(function () {
  "use strict";
  var tip = document.getElementById("tip");
  function hide() { tip.style.display = "none"; }
  function show(evt) {
    var mark = evt.target && evt.target.closest ? evt.target.closest("[data-tip]") : null;
    if (!mark) { hide(); return; }
    tip.textContent = "";
    mark.getAttribute("data-tip").split("|").forEach(function (line, i) {
      var row = document.createElement("div");
      if (i === 0) row.className = "when";
      row.textContent = line;
      tip.appendChild(row);
    });
    tip.style.display = "block";
    var w = tip.offsetWidth, h = tip.offsetHeight, x = evt.clientX + 14, y = evt.clientY + 14;
    if (x + w > window.innerWidth - 8) x = evt.clientX - w - 14;
    if (y + h > window.innerHeight - 8) y = evt.clientY - h - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  document.addEventListener("pointermove", show);
  document.addEventListener("pointerdown", show);
  document.addEventListener("scroll", hide, true);
  document.documentElement.addEventListener("pointerleave", hide);
})();
</script>
</body>
</html>
"""
