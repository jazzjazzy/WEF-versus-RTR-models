"""The WEF world and the RTR world on the same seeds, side by side (stage 3 of the RTR world,
20 November 2026). Built from two batches' tables alone: one batch of each world, one setting
each, the same seeds. The design: "then the WEF and RTR batches on the same 100 seeds, side by
side."

`python3 -m engine compare <WEF batch> <RTR batch>` writes `compare.html` beside the RTR batch,
or in the folder given with `--out`."""

import pathlib

from .batchpage import (CHARTS, RTR_CHARTS, TEMPLATE, _axis, _count, _e, _fan_card, _fmt, _seeds_words,
                        _ticks, _year_ticks, _years, _yr, report_data)

WEF, RTR = "WEF world", "RTR world"
COLOUR = {"wef": "var(--series-1)", "rtr": "var(--series-2)"}


BASKET_NOTE = (" The basket is made of asking prices, and in the RTR world they may be the prices of firms with no "
               "tenants or customers: most people own their home and their appliances, and a firm left with nobody to "
               "serve can go on raising what it asks. See how to read this.")


class CompareError(ValueError):
    """Two batches that cannot be set side by side, and why, in plain words."""


def _report(batch_dir) -> dict:
    from .batch import TABLE_FILE, _open, collect
    batch_dir = pathlib.Path(batch_dir)
    if not (batch_dir / "batch.json").is_file():
        raise CompareError(f"{batch_dir} is not a batch folder")
    table = batch_dir / TABLE_FILE
    if not table.is_file():
        collect(batch_dir)                           # its towns are there, its table not yet made
    con = _open(table)
    try:
        return report_data(con)
    finally:
        con.close()


def _world_side(setting: dict) -> dict:
    failed = setting["failed"]
    return {"name": setting["name"], "n": setting["n"], "failed": len(failed), "survived": setting["survived"],
            "half_failed": setting["half_failed"], "planned": setting["planned"],
            "first": failed[0] if failed else None, "middle": setting["end"]["failed_year"]["median"] if failed else None,
            "last": failed[-1] if failed else None}


def compare_data(wef_dir, rtr_dir) -> dict:
    """Everything the page shows. Raises CompareError unless the first batch is of the WEF world,
    the second of the RTR world, each has one setting, and both ran the same seeds."""
    wef, rtr = _report(wef_dir), _report(rtr_dir)
    if wef["batch"]["world"] != WEF:
        raise CompareError(f"the first batch must be of the WEF world; {wef_dir} is of the {wef['batch']['world']}")
    if rtr["batch"]["world"] != RTR:
        raise CompareError(f"the second batch must be of the RTR world; {rtr_dir} is of the {rtr['batch']['world']}")
    for report, where in ((wef, wef_dir), (rtr, rtr_dir)):
        if len(report["settings"]) != 1:
            raise CompareError(f"each batch must have one setting; {where} has {len(report['settings'])}")
    w, r = wef["settings"][0], rtr["settings"][0]
    seeds = [town["seed"] for town in w["towns"]]
    if seeds != [town["seed"] for town in r["towns"]]:
        raise CompareError("the two batches must have finished the same seeds: "
                           f"{_seeds_words(seeds)} against {_seeds_words([t['seed'] for t in r['towns']])}")
    towns, cases = [], {"both": 0, "only_wef": 0, "only_rtr": 0, "neither": 0}
    for a, b in zip(w["towns"], r["towns"]):
        fw, fr = a["failed_year"], b["failed_year"]
        if fw is None and fr is None:
            longer, case = "neither failed", "neither"
        elif fw is None:
            longer, case = WEF, "only_rtr"
        elif fr is None:
            longer, case = RTR, "only_wef"
        else:
            longer, case = (RTR if fr > fw else WEF if fw > fr else "the same"), "both"
        cases[case] += 1
        towns.append({"seed": a["seed"], "wef": fw, "rtr": fr, "longer": longer,
                      "wef_years": a["years"], "rtr_years": b["years"]})
    near = {side: _near_line(where, report["settings"][0]["planned"])
            for side, where, report in (("wef", wef_dir, wef), ("rtr", rtr_dir, rtr))}
    return {"names": {"wef": wef["batch"]["name"], "rtr": rtr["batch"]["name"]}, "seeds": seeds, "near_line": near,
            "wef": _world_side(w), "rtr": _world_side(r), "towns": towns, "cases": cases,
            "yearly": {"wef": w["yearly"], "rtr": r["yearly"]}, "rtr_setting": r}


def _near_line(batch_dir, year: int, share: float = 0.8) -> dict:
    """Of the towns still standing at the end of `year`, how many had `share` or more unhappy."""
    from .batch import TABLE_FILE, _open
    con = _open(pathlib.Path(batch_dir) / TABLE_FILE)
    try:
        ended = {seed: (failed, weeks) for seed, failed, weeks in con.execute(
            "SELECT seed, failed_week, year_weeks FROM towns")}
        values = [value for seed, value in con.execute(
            "SELECT seed, value FROM yearly WHERE scope = 'all' AND metric = 'unhappy' AND year = ?", (year,))
            if ended[seed][0] is None or ended[seed][0] > year * ended[seed][1]]
    finally:
        con.close()
    return {"year": year, "standing": len(values), "at_80": sum(1 for v in values if v >= share)}


# --- words ------------------------------------------------------------------------------------------
def _side_words(side: dict, world: str) -> str:
    n, failed = side["n"], side["failed"]
    if failed == 0:
        return f"In the {world}, none of the {n} towns reached the failure line in {_years(side['planned'])}."
    words = f"In the {world}, {failed} of {n} towns reached the failure line"
    if failed == 1:
        return words + f", in year {_yr(side['middle'])}."
    words += (f": the first in year {_yr(side['first'])}, the middle one of those in year {_yr(side['middle'])}, "
              f"the last in year {_yr(side['last'])}.")
    if side["half_failed"] is not None:
        words += f" Half of all {n} had failed by year {_yr(side['half_failed'])}."
    else:
        words += f" More than half had not reached it in {_years(side['planned'])}, when the towns were stopped."
    return words


def _town_words(failed, years: float) -> str:
    return f"failed in year {_yr(failed)}" if failed is not None else f"stood {_years(round(years, 2))}"


# --- the chart of one measure in both worlds --------------------------------------------------------
def _pair_svg(rows: dict, unit: str, title: str) -> str:
    """The middle town of each world as a line, with the middle half of its towns as a band."""
    width, height, left, right, top, bottom = 420.0, 200.0, 54.0, 10.0, 8.0, 22.0
    plot_w, plot_h = width - left - right, height - top - bottom
    years = sorted({row["year"] for side in rows.values() for row in side})
    first, last = years[0], years[-1]
    ticks = _ticks(max(row["q3"] for side in rows.values() for row in side), unit)
    ceiling, step = ticks[-1], ticks[1] - ticks[0]

    def x(year):
        return left + plot_w / 2 if last == first else left + plot_w * (year - first) / (last - first)

    def y(value):
        return top + plot_h * (1 - min(value, ceiling) / ceiling)

    parts = []
    for tick in ticks:
        parts.append(f'<line x1="{left:.1f}" x2="{left + plot_w:.1f}" y1="{y(tick):.1f}" y2="{y(tick):.1f}" '
                     f'stroke="var(--grid)"/>')
        parts.append(f'<text x="{left - 6:.1f}" y="{y(tick) + 4:.1f}" text-anchor="end">{_axis(unit, tick, step)}</text>')
    for year in _year_ticks(first, last):
        parts.append(f'<text x="{x(year):.1f}" y="{height - 6:.1f}" text-anchor="middle">{year}</text>')
    dashes = {"wef": "", "rtr": ' stroke-dasharray="7 4"'}         # the two lines differ in more than colour
    for side in ("wef", "rtr"):
        found = rows.get(side) or []
        if not found:
            continue
        colour = COLOUR[side]
        if len(found) > 1:
            along = [f"{x(row['year']):.1f},{y(row['q3']):.1f}" for row in found]
            back = [f"{x(row['year']):.1f},{y(row['q1']):.1f}" for row in reversed(found)]
            parts.append(f'<polygon points="{" ".join(along + back)}" fill="{colour}" opacity="0.2"/>')
            line = " ".join(f"{x(row['year']):.1f},{y(row['median']):.1f}" for row in found)
            parts.append(f'<polyline class="series" data-world="{side}" points="{line}" fill="none" '
                         f'stroke="{colour}" stroke-width="2"{dashes[side]} stroke-linejoin="round"/>')
        else:
            row = found[0]
            parts.append(f'<line data-world="{side}" x1="{x(row["year"]) - 9:.1f}" x2="{x(row["year"]) + 9:.1f}" '
                         f'y1="{y(row["median"]):.1f}" y2="{y(row["median"]):.1f}" stroke="{colour}" stroke-width="2"/>')
    gap = plot_w if last == first else plot_w / (last - first)
    by_year = {side: {row["year"]: row for row in rows.get(side) or []} for side in ("wef", "rtr")}
    for year in years:
        lines = [f"Year {year}"]
        for side, world in (("wef", WEF), ("rtr", RTR)):
            row = by_year[side].get(year)
            lines.append(f"{world}: middle town {_fmt(unit, row['median'])}, of {_count(row['n'], 'town', 'towns')} "
                         f"standing" if row else f"{world}: no town standing")
        start, end = max(left, x(year) - gap / 2), min(left + plot_w, x(year) + gap / 2)
        parts.append(f'<rect class="hit" x="{start:.1f}" y="{top:.1f}" width="{max(1.0, end - start):.1f}" '
                     f'height="{plot_h:.1f}" fill="transparent" data-tip="{_e("|".join(lines))}"/>')
    return (f'<svg viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{_e(title)}, year by year, '
            f'the two worlds">{"".join(parts)}</svg>')


def _pair_card(data: dict, measure: str, title: str, unit: str, note: str) -> str:
    rows = {side: data["yearly"][side].get(measure) for side in ("wef", "rtr")}
    if not any(rows.values()):
        return ""
    body = []
    years = sorted({row["year"] for side in rows.values() if side for row in side})
    by_year = {side: {row["year"]: row for row in rows[side] or []} for side in ("wef", "rtr")}
    for year in years:
        cells = []
        for side in ("wef", "rtr"):
            row = by_year[side].get(year)
            cells.append(f"<td>{row['n']}</td><td>{_fmt(unit, row['median'])}</td>" if row else "<td>0</td><td></td>")
        body.append(f"<tr><td>{year}</td>{''.join(cells)}</tr>")
    return f"""<figure class="card" data-measure="{_e(measure)}">
<div class="card-title">{_e(title)}</div>
<div class="card-note">{_e(note)}{_e(BASKET_NOTE if measure in ("town/basket", "town/affordability") else "")} The line is the middle town still standing; the band, the middle half.</div>
<div class="plot">{_pair_svg(rows, unit, title)}</div>
<details><summary>Table</summary><div class="tablewrap"><table>
<thead><tr><th>Year</th><th>WEF towns standing</th><th>WEF middle town</th><th>RTR towns standing</th><th>RTR middle town</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div></details>
</figure>"""


# --- the page ---------------------------------------------------------------------------------------
def _header(data: dict) -> str:
    n = len(data["seeds"])
    return f"""
<header>
  <h1>The WEF world and the RTR world, side by side</h1>
  <div class="sub">The WEF world: batch {_e(data['names']['wef'])}. The RTR world: batch {_e(data['names']['rtr'])}.
  The same {_count(n, 'seed', 'seeds')} in each: {_e(_seeds_words(data['seeds']))}. A seed is the same start in both
  worlds; the worlds' rules differ.</div>
  <div class="notice" role="note"><span><strong>Untuned.</strong> The starting values have not been tested,
  so read this page as a first look, not a finding.</span></div>
</header>
"""


def _answer(data: dict) -> str:
    n, c = len(data["seeds"]), data["cases"]
    planned = _years(max(data["wef"]["planned"], data["rtr"]["planned"]))
    hero = (f"WEF world: {data['wef']['failed']} of {n} failed. RTR world: {data['rtr']['failed']} of {n} failed. "
            f"Both in {planned}.")
    near = []
    for side, world in (("wef", WEF), ("rtr", RTR)):
        found = data["near_line"][side]
        if found["standing"]:
            near.append(f"In the {world}, at year {found['year']}, {found['at_80']} of the {found['standing']} "
                        f"towns still standing had 80% or more of their people unhappy.")
    near_words = " ".join(near)
    return f"""
<section id="answer"><h2>The answer first</h2>
<div class="hero">{_e(hero)}</div>
<p>{_e(_side_words(data['wef'], WEF))}</p>
<p>{_e(_side_words(data['rtr'], RTR))}</p>
<p>{_e(near_words)} The towns were stopped there, not finished: a town under the line at the end may be on its way to it.</p>
<p>Seed by seed: both towns failed {c['both']} times; only the WEF town failed {c['only_wef']} times; only the
RTR town failed {c['only_rtr']} times; neither failed {c['neither']} times.</p>
</section>
"""


def _towns(data: dict) -> str:
    rows = "".join(
        f'<tr data-seed="{t["seed"]}"><td>{t["seed"]}</td><td>{_e(_town_words(t["wef"], t["wef_years"]))}</td>'
        f'<td>{_e(_town_words(t["rtr"], t["rtr_years"]))}</td><td>{_e(t["longer"])}</td></tr>'
        for t in data["towns"])
    return f"""
<section id="towns"><h2>Town for town</h2>
<p>Each row is one seed: the same start, run once under each world's rules. "Lasted longer" names the world whose
town did; a town that never reached the failure line lasted longer than one that did.</p>
<div class="tablewrap"><table>
<thead><tr><th>Seed</th><th>WEF world</th><th>RTR world</th><th>Lasted longer</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</section>
"""


def _measures(data: dict) -> str:
    cards = "".join(_pair_card(data, measure, title, unit, note) for measure, title, unit, _, note in CHARTS)
    return f"""
<section id="measures"><h2>The measures side by side</h2>
<p>Each chart is one measure, year by year, in both worlds: the WEF world in the first colour with a solid
line, the RTR world in the second with a broken one.</p>
<div class="grid">{cards}</div>
</section>
"""


def _rtr_only(data: dict) -> str:
    cards = "".join(_fan_card(data["rtr_setting"], *spec) for spec in RTR_CHARTS)
    return f"""
<section id="rtr-only"><h2>What only the RTR world has</h2>
<p>Owning, letting and side hustles do not happen in the WEF world, so these are the RTR towns alone: the middle
town as a line, the middle half of the towns as a band, all of them as a paler band.</p>
<div class="grid">{cards or '<p class="empty">This batch has none of them.</p>'}</div>
</section>
"""


def _read() -> str:
    return """
<section id="read"><footer><h2>How to read this</h2>
<p><strong>Towns that fail drop out.</strong> A year's figures are over the towns still standing at the end of
that year. A town that reached the failure line drops out of every year after. So a world whose towns fail early
can look better in later years than it is: only its strongest towns are left. Read the yearly charts beside the
count of towns standing, which each chart's table gives.</p>
<p><strong>The failure line</strong> is the same in both worlds: the first week nine in ten people are unhappy
(Jason's rule). A town that never reached it is not a town that works. Look at what its people are paid, how many
have no job and how many are unhappy.</p>
<p><strong>The basket is the cheapest price on offer</strong> for each of the four needs, the same measure
in both worlds. In the RTR world most people who own their home pay no rent and own their appliances, so the
basket is not what most of them pay. A landlord firm or an appliance firm with no tenants or customers at all, and
often no homes, can go on raising the price it asks, and that asking price is the basket's. Read "Weekly basket" and
"Basket against the staff wage" in the RTR world as asking prices, not costs.</p>
<p><strong>The same seed</strong> starts the same in both worlds, then the rules part them. One seed is one town's
luck; read the counts across all of them.</p>
</footer></section>
"""


def build_compare_page(wef_dir, rtr_dir, out_dir=None) -> pathlib.Path:
    """Write `compare.html` beside the RTR batch, or in `out_dir`. Returns its path."""
    data = compare_data(wef_dir, rtr_dir)
    body = _header(data) + _answer(data) + _towns(data) + _measures(data) + _rtr_only(data) + _read()
    page = TEMPLATE.replace("__TITLE__", _e("The WEF world and the RTR world")).replace("__BODY__", body)
    out = pathlib.Path(out_dir if out_dir is not None else rtr_dir) / "compare.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
