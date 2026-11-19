"""Places in the record, the measures of distance, and the map on the dashboard."""

import json
import re
import sqlite3

import pytest

from engine.config import load_config
from engine.dashboard import build_dashboard
from engine.metrics import weekly_series
from engine.recorder import Recorder
from engine.runner import run
from engine.town import Town
from conftest import small_town


def query(path, sql, *args):
    con = sqlite3.connect(path)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    cfg = load_config(None, ["population_cap=80", "stop_on_failure=false"])
    path = tmp_path_factory.mktemp("rec") / "run.sqlite"
    rec = Recorder(path, cfg, run_id="map-test")
    town = Town(cfg, rec)
    town.run(40)
    rec.finish("survived", {})
    return town, path


def test_spots_are_recorded_once(recorded):
    town, path = recorded
    rows = query(path, "SELECT spot, x, y FROM spots ORDER BY spot")
    assert len(rows) == 169
    assert rows[0] == (0, 0, 0) and rows[168] == (168, 12, 12)


def test_places_are_recorded_each_quarter(recorded):
    town, path = recorded
    weeks = {r[0] for r in query(path, "SELECT DISTINCT week FROM places")}
    assert weeks == {0, 13, 26, 39}
    centre = town.map.centre.id
    assert query(path, "SELECT kind, label FROM places WHERE week = 0 AND spot = ?", centre) == [("service", "bank")]
    homes, let = query(path, "SELECT SUM(homes), SUM(let) FROM places WHERE week = 39 AND kind = 'homes'")[0]
    built_after = query(path, "SELECT COUNT(*) FROM events WHERE week = 40 AND kind = 'unit_built' "
                              "AND json_extract(data, '$.spot') IS NOT NULL")[0][0]
    assert homes + built_after == sum(len(s.units) for s in town.map.homes())   # the record is of week 39
    assert 0 < let <= homes
    premises = query(path, "SELECT COUNT(*) FROM places WHERE week = 39 AND kind = 'premises'")[0][0]
    assert premises == len(town.alive_firms)


def test_agent_snapshot_has_home_work_and_hours(recorded):
    town, path = recorded
    worker = next(a for a in town.agents if a.role == "staff" and "housing" in a.unit)
    row = query(path, "SELECT home_spot, work_spot, travel_hours, rides FROM agent_snap "
                      "WHERE week = 40 AND agent = ?", worker.id)[0]
    assert row[0] == worker.unit["housing"].spot.id
    assert row[1] == worker.employer.spot.id
    assert row[2] == pytest.approx(worker.travel_hours) and row[2] > 0
    assert row[3] is None                                     # no transport firm yet


def test_firm_and_unit_rows_say_where_they_are(recorded):
    town, path = recorded
    housing = town.firms_for("housing")[0]
    assert query(path, "SELECT spot FROM firm_snap WHERE week = 40 AND firm = ?", housing.id)[0][0] == housing.spot.id
    spots = {r[0] for r in query(path, "SELECT DISTINCT spot FROM units WHERE week = 39 AND need = 'housing'")}
    assert spots == {s.id for s in housing.lots if s.units}
    assert query(path, "SELECT COUNT(*) FROM units WHERE week = 39 AND need = 'appliances' AND spot IS NOT NULL")[0][0] == 0


def test_series_has_distance_measures_for_each_class():
    town = small_town()
    town.run(30)
    by = {(s, m): v for s, m, v in weekly_series(town)}
    for scope in ("all", "owner", "working", "out"):
        for metric in ("travel_hours", "blocks_to_work", "riders"):
            assert (scope, metric) in by, (scope, metric)
    assert by[("working", "travel_hours")] > 0 and by[("all", "riders")] == 0.0
    for metric in ("spots_empty", "spots_homes", "spots_premises", "land_scarce", "land_price",
                   "turned_away", "turned_away_job", "turned_away_food", "turned_away_other",
                   "rent_middle", "rent_edge", "ground_rent"):
        assert ("town", metric) in by, metric
    used = by[("town", "spots_homes")] + by[("town", "spots_premises")] + 2      # and the bank and the broker
    assert by[("town", "spots_empty")] == 169 - used


def test_transport_is_not_counted_among_the_invented_needs():
    from test_places import far_job_scene
    town, landlord, home, firm, bus = far_job_scene()
    by = {(s, m): v for s, m, v in weekly_series(town)}
    assert by[("town", "transport_firms")] == 1
    assert by[("town", "needs_invented")] == 0 and by[("town", "firms_invented")] == 0


def test_a_count_made_once_a_quarter_is_charted_as_that_quarters_count():
    from engine.dashboard import _Shaper
    # the count for a quarter is recorded in its last week; the twelve weeks before still show the old one
    weekly = {w: (5.0 if w <= 12 else 30.0 if w <= 25 else 80.0) for w in range(1, 27)}
    shape = _Shaper({}, 26)
    assert shape.quarters(weekly, how="last") == [30.0, 80.0]
    assert shape.quarters(weekly)[0] < 30.0                   # an average would blend the old count in


def far_and_near_workers():
    from test_places import employ, far_job_scene, premises, subscribe, tenant
    town, landlord, home, firm, bus = far_job_scene()         # seven crew on the bus, none with a home
    near = premises(town, "appliances", 3, 0)
    rider = tenant(town, home)
    employ(rider, firm)                                       # twenty-four blocks from work, on the bus
    subscribe(town, rider, bus)
    walker = tenant(town, home)
    employ(walker, near)                                      # three blocks from work, on foot
    return town, rider, walker, bus


def test_distance_measures_report_what_is_there():
    town, rider, walker, bus = far_and_near_workers()
    town.reach_blocked_last = 7
    by = {(s, m): v for s, m, v in weekly_series(town)}
    assert by[("all", "riders")] == pytest.approx(1 / 9)      # one rider among nine people
    assert by[("all", "blocks_to_work")] == pytest.approx(13.5)   # twenty-four and three, for the two with homes
    assert by[("town", "turned_away")] == 7
    assert by[("town", "rent_edge")] == 33_000 and by[("town", "rent_middle")] == 0   # the only homes are far out


def test_snapshot_says_which_transport_firm_each_agent_rides_with(tmp_path):
    town, rider, walker, bus = far_and_near_workers()
    rec = Recorder(tmp_path / "run.sqlite", town.cfg, run_id="rides")
    rec.snapshot(town)
    rec.finish("survived", {})
    db = sqlite3.connect(tmp_path / "run.sqlite")
    rows = dict(db.execute("SELECT agent, rides FROM agent_snap"))
    assert rows[rider.id] == bus.id and rows[walker.id] is None


def test_town_without_a_map_has_no_place_measures():
    town = small_town("map_width=0")
    town.run(10)
    by = {(s, m): v for s, m, v in weekly_series(town)}
    assert ("town", "spots_empty") not in by and ("all", "travel_hours") not in by


def embedded(html):
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(match.group(1).replace("<\\/", "</"))


def test_dashboard_has_the_map_and_the_distance_charts(tmp_path):
    run_dir = run(load_config(None, ["population_cap=60", "years=2"]), out_root=tmp_path, quiet=True)
    html = (run_dir / "dashboard.html").read_text(encoding="utf-8")
    data = embedded(html)
    town_map = next(c for c in data["charts"] if c["type"] == "map")
    assert town_map["cols"] == 13 and town_map["rows"] == 13 and len(town_map["cells"]) == 169
    kinds = {c["kind"] for c in town_map["cells"]}
    assert {"homes", "premises", "service", "empty"} <= kinds
    bank = next(c for c in town_map["cells"] if c["label"] == "Bank")
    assert (bank["x"], bank["y"]) == (6, 6)
    titles = {c["title"] for c in data["charts"]}
    for wanted in ("The town at the end", "How the map filled", "The price of land", "Hours on the road",
                   "Share holding transport", "People turned away by distance", "Rent by place"):
        assert wanted in titles, wanted
    hours = next(c for c in data["charts"] if c["title"] == "Hours on the road")
    assert [s["name"] for s in hours["series"]] == ["Everyone", "Owner class", "Working class", "Out of work"]
    turned = next(c for c in data["charts"] if c["title"] == "People turned away by distance")
    assert [s["name"] for s in turned["series"]] == ["From a job", "From food", "From other shops"]
    assert "The map" in html
    assert "The town on a 13 by 13 map." in html and "without the map" not in html


def test_dashboard_without_a_map_still_builds(tmp_path):
    cfg = load_config(None, ["population_cap=60", "years=2", "map_width=0"])
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    html = (run_dir / "dashboard.html").read_text(encoding="utf-8")
    data = embedded(html)
    assert "The economy without the map." in html
    assert all(c["type"] != "map" for c in data["charts"])
    assert "Hours on the road" not in {c["title"] for c in data["charts"]}
