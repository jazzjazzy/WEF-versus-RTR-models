import json
import re
import sqlite3

import pytest

from engine.config import load_config
from engine.dashboard import build_dashboard
from engine.runner import run

FOUR = ["Everyone", "Owner class", "Working class", "Out of work"]


def small(*overrides):
    return load_config(None, ["population_cap=40", "years=3"] + list(overrides))


def embedded(html):
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(match.group(1).replace("<\\/", "</"))


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    run_dir = run(small("seed=9"), out_root=tmp_path_factory.mktemp("runs"), quiet=True)
    return run_dir, (run_dir / "dashboard.html").read_text(encoding="utf-8")


def test_dashboard_builds_from_record_alone(built):
    run_dir, _ = built
    for name in ("dashboard.html", "summary.json", "config.json"):
        (run_dir / name).unlink()                          # only run.sqlite is left
    path = build_dashboard(run_dir)
    html = path.read_text(encoding="utf-8")
    for label in FOUR:
        assert label in html
    assert "Seed 9" in html
    assert "untuned" in html.lower()
    for forbidden in ("<script src", "<link", "@import", "url("):
        assert forbidden not in html                       # nothing is fetched: it opens offline


def test_every_class_chart_has_all_four_coverages(built):
    _, html = built
    charts = embedded(html)["charts"]
    by_class = [c for c in charts if c.get("by_class")]
    assert len(by_class) >= 8
    for chart in by_class:
        assert [s["name"] for s in chart["series"]] == FOUR, chart["title"]
    titles = {c["title"] for c in charts}
    for wanted in ("Share unhappy", "Security", "Wellbeing", "Weekly income", "Share of all shares held"):
        assert wanted in titles


def test_dashboard_numbers_match_the_record(built):
    run_dir, html = built
    chart = next(c for c in embedded(html)["charts"] if c["title"] == "Share unhappy")
    everyone = next(s for s in chart["series"] if s["name"] == "Everyone")
    con = sqlite3.connect(run_dir / "run.sqlite")
    rows = con.execute("SELECT week, value FROM series WHERE scope='all' AND metric='unhappy' "
                       "AND week >= 1 ORDER BY week").fetchall()
    people = dict(con.execute("SELECT week, value FROM series WHERE scope='all' AND metric='n'"))
    con.close()
    first_quarter = [(v, people[w]) for w, v in rows if w <= 13]       # a share of everyone: weighted by head count
    assert everyone["values"][0] == pytest.approx(
        100 * sum(v * n for v, n in first_quarter) / sum(n for _, n in first_quarter), abs=0.01)
    assert len(everyone["values"]) == -(-len(rows) // 13)
    assert chart["x"][-1] == pytest.approx(rows[-1][0] / 52, abs=0.001)


def test_five_flows_and_town_charts_are_present(built):
    _, html = built
    data = embedded(html)
    flows = next(c for c in data["charts"] if c["title"] == "Money crossing the town boundary")
    assert [s["name"] for s in flows["series"]] == [
        "Arrivals' capital", "Bank loans", "Exports", "Loan repayments", "Interest", "Imports"]
    assert flows["type"] == "stack"
    assert all(v <= 0 for s in flows["series"][3:] for v in s["values"])     # money out is drawn below zero
    assert all(v >= 0 for s in flows["series"][:3] for v in s["values"])
    titles = {c["title"] for c in data["charts"]}
    for wanted in ("Prices against wages", "Ownership concentration", "Money in town", "Bank lending",
                   "Moves between classes", "Firms by need"):
        assert wanted in titles


def test_dashboard_handles_a_short_failed_run(tmp_path):
    cfg = small("happy_cutoff=1.01", "failure_min_population=4")
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    html = (run_dir / "dashboard.html").read_text(encoding="utf-8")
    assert "Failed in year" in html
    data = embedded(html)
    assert data["marks"]["failed"] is not None
    assert all(len(c["x"]) >= 1 for c in data["charts"])


def test_dashboard_for_an_unfinished_run(tmp_path):
    from engine.recorder import Recorder
    from engine.town import Town
    cfg = small()
    run_dir = tmp_path / "stopped"
    run_dir.mkdir()
    rec = Recorder(run_dir / "run.sqlite", cfg, run_id="stopped")
    Town(cfg, rec).run(30)
    rec.flush()
    html = build_dashboard(run_dir).read_text(encoding="utf-8")
    assert "Unfinished run" in html


def test_an_empty_class_is_a_gap_not_a_zero(built):
    run_dir, _ = built
    html = build_dashboard(run_dir).read_text(encoding="utf-8")
    data = embedded(html)
    con = sqlite3.connect(run_dir / "run.sqlite")
    def weekly(metric):
        return dict(con.execute("SELECT week, value FROM series WHERE scope='out' AND metric=? "
                                "AND week >= 1", (metric,)).fetchall())
    heads, unhappy = weekly("n"), weekly("unhappy")
    con.close()
    last = max(heads)
    chart = next(c for c in data["charts"] if c["title"] == "Share unhappy")
    drawn = next(s for s in chart["series"] if s["name"] == "Out of work")["values"]
    checked_gap = checked_weighted = False
    for q, start in enumerate(range(1, last + 1, 13)):
        weeks = [w for w in range(start, min(start + 13, last + 1))]
        people = sum(heads[w] for w in weeks)
        if q == len(drawn) - 1:
            continue                                   # the last point is the final week itself
        if people == 0:
            assert drawn[q] is None                    # nobody out of work that quarter: no point drawn
            checked_gap = True
        else:
            expected = 100 * sum(unhappy[w] * heads[w] for w in weeks) / people
            assert drawn[q] == pytest.approx(expected, abs=0.01)   # weighted by how many were in the group
            if len({heads[w] for w in weeks}) > 1:
                checked_weighted = True
    assert checked_gap and checked_weighted


def test_flows_chart_adds_up_to_the_money_in_town(built):
    run_dir, _ = built
    data = embedded(build_dashboard(run_dir).read_text(encoding="utf-8"))
    flows = next(c for c in data["charts"] if c["title"] == "Money crossing the town boundary")
    total = sum(sum(s["values"]) for s in flows["series"])           # money out is already negative
    con = sqlite3.connect(run_dir / "run.sqlite")
    money = con.execute("SELECT value FROM series WHERE scope='town' AND metric='money' "
                        "ORDER BY week DESC LIMIT 1").fetchone()[0]
    con.close()
    assert total == pytest.approx(money / 100, abs=1.0)              # founders' week-0 capital included


def test_empty_spans_are_marked_on_class_charts(built):
    run_dir, _ = built
    html = build_dashboard(run_dir).read_text(encoding="utf-8")
    data = embedded(html)
    chart = next(c for c in data["charts"] if c["title"] == "Share unhappy")
    out = next(s for s in chart["series"] if s["name"] == "Out of work")
    assert out["empty_label"] == "nobody out of work"
    assert out["empty"] == [v is None for v in out["values"]]     # a break is always an empty group
    assert any(out["empty"]) and not all(out["empty"])
    everyone = next(s for s in chart["series"] if s["name"] == "Everyone")
    assert "empty" not in everyone                                # the town is never empty
    assert "nobody in that group" in html                         # the note that explains the strip
    for c in data["charts"]:
        if not c.get("by_class"):
            assert all("empty" not in s for s in c["series"])     # only class lines can be empty


def test_the_town_full_tile_says_what_full_means_with_and_without_a_cap(tmp_path):
    from engine.runner import run
    for cap, words in ((40, "40 people is the cap; arrivals stop there"),
                       (0, "No cap: full when the land has run out and a newcomer finds no home")):
        run_dir = run(load_config(None, [f"population_cap={cap}", "years=1", "map_width=6", "map_height=6"]),
                      out_root=tmp_path / str(cap), quiet=True)
        assert words in (run_dir / "dashboard.html").read_text()
