"""The stage 4 diagnostic script, wef/experiments/wage_trace.py. It runs the model itself, so
with nothing changed it must give the model's own record; a change asked for "at full"
must leave every week up to the filling untouched; and what it reports must be what the
record holds."""

import importlib.util
import json
import pathlib
import sqlite3

import pytest

from engine.config import load_config
from engine.runner import run

ROOT = pathlib.Path(__file__).resolve().parents[1]
SMALL = ["population_cap=60", "years=3", "seed=4", "stop_on_failure=false"]


@pytest.fixture(scope="module")
def wt():
    spec = importlib.util.spec_from_file_location("wage_trace", ROOT / "wef" / "experiments" / "wage_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(run_dir, sql, *args):
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def meta(run_dir):
    return dict(rows(run_dir, "select key, value from run"))


def full_week(run_dir):
    return rows(run_dir, "select min(week) from events where kind='town_full'")[0][0]


def series(run_dir, upto=None):
    if upto is None:
        return rows(run_dir, "select week, scope, metric, value from series order by week, scope, metric")
    return rows(run_dir, "select week, scope, metric, value from series where week<=? "
                         "order by week, scope, metric", upto)


@pytest.fixture(scope="module")
def plain(wt, tmp_path_factory):
    return wt.run_town("plain", SMALL, [], tmp_path_factory.mktemp("wage_trace"))


@pytest.fixture(scope="module")
def changed(wt, tmp_path_factory):
    return wt.run_town("changed", SMALL, ["invest_prob=0"], tmp_path_factory.mktemp("wage_trace"))


def test_with_nothing_changed_it_gives_the_models_own_record(plain, tmp_path):
    theirs = run(load_config(None, SMALL), out_root=tmp_path, quiet=True)
    assert meta(plain)["fingerprint"] == meta(theirs)["fingerprint"]
    assert meta(plain)["outcome"] == meta(theirs)["outcome"]


def test_the_run_folder_holds_the_record_the_settings_and_what_was_changed(plain, changed):
    assert plain.name == "plain"
    for name in ("run.sqlite", "config.json", "summary.json", "experiment.json"):
        assert (plain / name).is_file(), name
    assert json.loads((plain / "experiment.json").read_text()) == {"from_start": SMALL, "at_full": []}
    assert json.loads((changed / "experiment.json").read_text()) == {
        "from_start": SMALL, "at_full": [["invest_prob", 0]]}


def test_a_change_at_full_leaves_every_week_up_to_the_filling_untouched(plain, changed):
    full = full_week(plain)
    assert full is not None and full == full_week(changed)
    assert series(plain, upto=full) == series(changed, upto=full)
    events = "select week, kind, agent, firm, amount, qty, data from events where week<=? order by id"
    assert rows(plain, events, full) == rows(changed, events, full)


def test_a_change_at_full_does_change_what_comes_after(plain, changed):
    assert series(plain) != series(changed)
    assert meta(plain)["fingerprint"] != meta(changed)["fingerprint"]


def test_the_settings_kept_are_the_ones_the_town_started_with(changed):
    # the record says what the town started as; experiment.json says what changed and when
    assert json.loads((changed / "config.json").read_text())["invest_prob"] > 0


def test_an_unknown_dial_at_full_is_refused_before_anything_runs(wt, tmp_path):
    with pytest.raises(KeyError):
        wt.run_town("bad", SMALL, ["no_such_dial=1"], tmp_path)
    assert not (tmp_path / "bad").exists()


def test_a_label_already_used_is_not_overwritten(wt, plain):
    with pytest.raises(FileExistsError):
        wt.run_town("plain", SMALL, [], plain.parent)


def test_the_evidence_is_what_the_record_holds(wt, plain):
    e = wt.evidence(plain)
    full = full_week(plain)
    last = rows(plain, "select max(week) from series")[0][0]
    wage = dict(rows(plain, "select week, value from series where scope='town' and metric='wage'"))
    vac = dict(rows(plain, "select week, value from series where scope='town' and metric='vacancies'"))
    out = dict(rows(plain, "select week, value from series where scope='town' and metric='jobless_rate'"))
    weeks = range(full, last + 1)
    assert e["full_week"] == full and e["last_week"] == last and e["weeks_after_full"] == len(weeks)
    assert e["wage_at_full"] == wage[full] and e["wage_at_end"] == wage[last]
    assert e["weeks_with_unfilled_jobs"] == sum(1 for w in weeks if vac[w] > 0)
    assert e["weeks_with_a_queue"] == sum(1 for w in weeks if out[w] > 0.05)
    changes = rows(plain, "select data from events where kind='wage_change' and week>=?", full)
    reasons = [json.loads(d)["reason"] for d, in changes]
    assert e["wage_rises"] == reasons.count("unfilled") and e["wage_cuts"] == reasons.count("queue")
    housing = {f for f, in rows(plain, "select firm from firm_static where need='housing'")}
    built = rows(plain, "select firm from events where kind='unit_built' and week>=?", full)
    assert e["homes_built_after_full"] == sum(1 for f, in built if f in housing)
    homes = dict(rows(plain, "select week, value from series where scope='town' and metric='homes'"))
    empty = dict(rows(plain, "select week, value from series where scope='town' and metric='homes_vacant'"))
    assert e["homes_at_full"] == homes[full] and e["most_homes"] == max(homes[w] for w in weeks)
    assert e["most_empty_homes"] == max(empty[w] for w in weeks)


def test_the_two_wage_rules_account_for_each_firms_changes(wt, plain):
    # what the rises and cuts moved the average by, weighted by each firm's share of the staff
    e = wt.evidence(plain)
    moved = e["wage_at_end"] - e["wage_at_full"]
    assert e["rises_moved_the_average"] >= 0 >= e["cuts_moved_the_average"]
    assert e["moves_between_firms"] == pytest.approx(
        moved - e["rises_moved_the_average"] - e["cuts_moved_the_average"])


def test_a_town_that_never_filled_has_no_evidence(wt, tmp_path):
    run_dir = wt.run_town("not-full", ["years=1", "seed=4"], [], tmp_path)
    with pytest.raises(ValueError, match="never filled"):
        wt.evidence(run_dir)


def test_the_report_names_the_run_and_gives_its_numbers(wt, plain):
    text = wt.report("small town", plain)
    e = wt.evidence(plain)
    assert text.startswith("small town")
    assert f"{e['homes_built_after_full']} built after it filled" in text
    assert f"${e['wage_at_end'] / 100:,.0f}" in text


def test_the_command_line_runs_a_town_and_reports_on_it(wt, tmp_path, capsys):
    assert wt.main(["run", "cli", "--out", str(tmp_path), *SMALL, "--at-full", "invest_prob=0"]) == 0
    out = capsys.readouterr().out
    assert "cli" in out and (tmp_path / "cli" / "run.sqlite").is_file()
    assert json.loads((tmp_path / "cli" / "experiment.json").read_text())["at_full"] == [["invest_prob", 0]]
    assert wt.main(["report", str(tmp_path / "cli")]) == 0
    assert "built after it filled" in capsys.readouterr().out


def test_a_bad_setting_on_the_command_line_is_a_plain_message(wt, tmp_path, capsys):
    assert wt.main(["run", "bad", "--out", str(tmp_path), "no_such_dial=1"]) == 2
    assert "no_such_dial" in capsys.readouterr().err
    assert not (tmp_path / "bad").exists()


def test_it_is_not_part_of_the_model(wt):
    # the code fingerprint covers engine/*.py only, so this script cannot change it
    assert not (ROOT / "engine" / "wage_trace.py").exists()
    assert pathlib.Path(wt.__file__).parent.name == "experiments"
