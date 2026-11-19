import json
import sqlite3

import pytest

from engine.config import load_config
from engine.recorder import NullRecorder, Recorder, code_fingerprint
from engine.town import Town


def recorded_run(tmp_path, weeks, *overrides):
    cfg = load_config(None, ["population_cap=60", "stop_on_failure=false"] + list(overrides))
    path = tmp_path / "run.sqlite"
    rec = Recorder(path, cfg, run_id="test-run")
    town = Town(cfg, rec)
    town.run(weeks)
    return cfg, town, rec, path


def query(path, sql, *args):
    con = sqlite3.connect(path)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def test_run_record_holds_seed_settings_and_fingerprint(tmp_path):
    cfg, town, rec, path = recorded_run(tmp_path, 30, "seed=7")
    rec.finish("survived", {"weeks": 30})
    run = dict(query(path, "SELECT key, value FROM run"))
    assert run["seed"] == "7" and run["run_id"] == "test-run"
    assert json.loads(run["config"]) == cfg.to_dict()
    assert run["code_fingerprint"] == code_fingerprint()
    assert run["outcome"] == "survived" and json.loads(run["summary"]) == {"weeks": 30}
    assert len(run["fingerprint"]) == 64
    assert json.loads(run["endowment"])["housing"]["units"] == 60


def test_series_has_four_coverages_and_town(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 30)
    rec.finish("survived", {})
    scopes = {r[0] for r in query(path, "SELECT DISTINCT scope FROM series")}
    assert scopes == {"all", "owner", "working", "out", "town"}
    weeks = query(path, "SELECT COUNT(DISTINCT week) FROM series")[0][0]
    assert weeks == 31                            # week 0 (the founders arrive) and thirty weeks


def test_agent_events_carry_security_and_horizon(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 30)
    rec.finish("survived", {})
    rows = query(path, "SELECT data FROM events WHERE kind = 'hire' LIMIT 20")
    assert rows
    for (data,) in rows:
        d = json.loads(data)
        assert 0.0 <= d["sec"] <= 1.0 and d["h"] > 0


def test_events_are_numbered_in_the_order_they_happened(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 30)
    rec.finish("survived", {})
    rows = query(path, "SELECT id, week FROM events ORDER BY id")
    assert [r[0] for r in rows] == list(range(1, len(rows) + 1))
    assert [r[1] for r in rows] == sorted(r[1] for r in rows)


def test_snapshot_rows_match_population_each_week(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 40)
    rec.finish("survived", {})
    per_week = dict(query(path, "SELECT week, COUNT(*) FROM agent_snap GROUP BY week"))
    pop = dict(query(path, "SELECT week, value FROM series WHERE scope='town' AND metric='population'"))
    assert set(per_week) == set(range(0, 41))
    assert all(per_week[w] == pop[w] for w in per_week)
    statics = query(path, "SELECT COUNT(*) FROM agent_static")[0][0]
    assert statics == town.population


def test_each_agent_snapshot_names_their_home_and_its_condition(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 20)
    rec.finish("survived", {})
    a = town.agents[0]
    row = query(path, "SELECT home_firm, home_unit, home_cond, klass, cash FROM agent_snap "
                      "WHERE week = 20 AND agent = ?", a.id)[0]
    assert row[0] == a.subs["housing"].id and row[1] == a.unit["housing"].id
    assert row[2] == pytest.approx(a.unit["housing"].cond)
    assert row[3] == a.klass and row[4] == a.cash


def test_share_register_and_units_are_kept_each_quarter(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 26)
    rec.finish("survived", {})
    assert {r[0] for r in query(path, "SELECT DISTINCT week FROM holdings")} == {0, 13, 26}
    assert {r[0] for r in query(path, "SELECT DISTINCT week FROM units")} == {0, 13, 26}
    held = query(path, "SELECT SUM(shares) FROM holdings WHERE week = 26 AND firm = 1")[0][0]
    assert held == town.firm(1).shares_out


def test_every_share_order_is_kept_with_what_was_filled(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 3 * 52)
    rec.finish("survived", {})
    rows = query(path, "SELECT side, qty, filled FROM orders")
    assert rows
    assert all(0 <= filled <= qty for _, qty, filled in rows)
    assert {side for side, _, _ in rows} <= {"bid", "ask", "issue"}


def test_unfinished_run_is_readable(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 30)
    rec.flush()                                   # the run stops here; finish() is never called
    run = dict(query(path, "SELECT key, value FROM run"))
    assert "outcome" not in run and run["seed"] == "1"
    assert query(path, "SELECT MAX(week) FROM series")[0][0] == 30


def test_recorded_run_matches_unrecorded_run(tmp_path):
    cfg, town, rec, path = recorded_run(tmp_path, 3 * 52, "seed=4")
    plain = Town(load_config(None, ["population_cap=60", "stop_on_failure=false", "seed=4"]),
                 NullRecorder(keep_events=False))
    plain.run(3 * 52)
    assert rec.fingerprint() == plain.rec.fingerprint()
    assert [a.cash for a in town.agents] == [a.cash for a in plain.agents]


def test_firm_snapshot_carries_the_weeks_profit(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 60)
    rec.finish("survived", {})
    rows = query(path, "SELECT profit, revenue, export, wages, goods, capex, interest, wear FROM firm_snap")
    assert rows
    for profit, revenue, export, wages, goods, capex, interest, wear in rows:
        assert profit == revenue + export - (wages + goods - capex) - interest - wear
    assert any(r[0] != 0 for r in rows)


def test_income_columns_separate_wages_from_dividends(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 2 * 52)
    rec.finish("survived", {})
    rows = query(path, "SELECT income, wage_income, dividends FROM agent_snap")
    assert all(income == wages + divs and wages >= 0 and divs >= 0 for income, wages, divs in rows)
    assert any(divs > 0 for _, _, divs in rows)           # dividends were paid in this run
    paid = query(path, "SELECT SUM(amount) FROM events WHERE kind = 'dividend'")[0][0]
    assert sum(divs for _, _, divs in rows) == paid


def test_week_zero_is_recorded_with_the_founders_capital(tmp_path):
    _, town, rec, path = recorded_run(tmp_path, 30)
    rec.finish("survived", {})
    weeks = [r[0] for r in query(path, "SELECT DISTINCT week FROM series ORDER BY week")]
    assert weeks == list(range(0, 31))
    arrivals = query(path, "SELECT SUM(value) FROM series WHERE scope='town' AND metric='in_arrival'")[0][0]
    assert arrivals == town.ledger.total_in["arrival"]
    flows = query(path, "SELECT SUM(value) FROM series WHERE scope='town' AND metric='net_flow'")[0][0]
    assert flows == town.money_in_town()                  # every cent in town came through the five flows
    assert query(path, "SELECT COUNT(*) FROM agent_snap WHERE week = 0")[0][0] == 4
