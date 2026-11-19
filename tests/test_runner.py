import json
import sqlite3

import pytest

from conftest import wef_main as main
from engine.config import Config, load_config
from engine.recorder import Recorder
from engine.runner import info, run, run_in


def small(*overrides):
    return load_config(None, ["population_cap=40", "years=2"] + list(overrides))


def run_table(run_dir):
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        return dict(con.execute("SELECT key, value FROM run").fetchall())
    finally:
        con.close()


def test_run_writes_a_folder_with_record_settings_and_summary(tmp_path):
    cfg = small("seed=3")
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    assert run_dir.parent == tmp_path and "seed3" in run_dir.name
    assert (run_dir / "run.sqlite").exists()
    assert Config.from_dict(json.loads((run_dir / "config.json").read_text())) == cfg
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["outcome"] in ("survived", "failed")
    assert summary["weeks"] == 104 or summary["failed_week"] is not None
    assert set(summary["unhappy"]) == {"all", "owner", "working", "out"}
    assert summary["price_rule"] == "ratchet"
    assert run_table(run_dir)["outcome"] == summary["outcome"]


def test_same_settings_and_seed_give_the_same_record(tmp_path):
    first = run(small("seed=5"), out_root=tmp_path, quiet=True, label="a")
    second = run(small("seed=5"), out_root=tmp_path, quiet=True, label="b")
    other = run(small("seed=6"), out_root=tmp_path, quiet=True, label="c")
    assert first != second
    assert run_table(first)["fingerprint"] == run_table(second)["fingerprint"]
    assert run_table(first)["fingerprint"] != run_table(other)["fingerprint"]


def test_failed_run_records_when_and_how(tmp_path):
    cfg = small("happy_cutoff=1.01", "failure_min_population=4")
    run_dir = run(cfg, out_root=tmp_path, quiet=True)
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["outcome"] == "failed" and summary["failed_week"] == 1
    assert summary["weeks"] == 1
    assert "top10_shares" in summary and "price_ratio" in summary


def test_info_reports_an_unfinished_run(tmp_path, capsys):
    run_dir = tmp_path / "stopped"
    run_dir.mkdir()
    rec = Recorder(run_dir / "run.sqlite", small(), run_id="stopped")
    rec.flush()
    text = info(run_dir)
    assert "unfinished" in text and "stopped" in text


def test_info_reports_a_finished_run(tmp_path):
    run_dir = run(small(), out_root=tmp_path, quiet=True)
    text = info(run_dir)
    assert "survived" in text or "failed" in text
    assert "seed 1" in text


def test_command_line_runs_and_rejects_a_mistyped_dial(tmp_path, capsys):
    code = main(["run", "--years", "1", "--set", "population_cap=30", "--out", str(tmp_path), "--quiet"])
    assert code == 0
    assert len([p for p in tmp_path.iterdir() if p.is_dir()]) == 1
    with pytest.raises(SystemExit) as stop:
        main(["run", "--set", "populaton_cap=30", "--out", str(tmp_path), "--quiet"])
    assert stop.value.code == 2
    assert "populaton_cap" in capsys.readouterr().err


def test_command_line_rejects_a_mistyped_value(tmp_path, capsys):
    with pytest.raises(SystemExit) as stop:
        main(["run", "--set", "price_rule=serach", "--out", str(tmp_path), "--quiet"])
    assert stop.value.code == 2
    assert "price_rule" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []                # nothing was run


def test_a_run_can_be_repeated_from_its_folder(tmp_path):
    first = run(small("seed=5"), out_root=tmp_path, quiet=True, label="a")
    again = run(load_config(str(first / "config.json")), out_root=tmp_path, quiet=True, label="b")
    assert run_table(first)["fingerprint"] == run_table(again)["fingerprint"]


# --- a run into a folder it is given (the way a batch makes its towns) --------------------------------
def test_run_in_makes_the_same_town_as_run_in_the_folder_it_is_given(tmp_path):
    alone = run(small("seed=5"), out_root=tmp_path / "alone", quiet=True)
    given = tmp_path / "given"
    given.mkdir()
    summary = run_in(small("seed=5"), given)
    assert run_table(given)["fingerprint"] == run_table(alone)["fingerprint"]
    assert summary == json.loads((given / "summary.json").read_text())
    assert summary == json.loads((alone / "summary.json").read_text())
    assert Config.from_dict(json.loads((given / "config.json").read_text())) == small("seed=5")
    assert run_table(given)["run_id"] == "given"
    assert sorted(f.name for f in given.iterdir()) == sorted(f.name for f in alone.iterdir())


def test_run_in_without_pages_leaves_only_the_record_the_settings_and_the_summary(tmp_path):
    run_in(small("seed=5"), tmp_path, pages=False)
    assert sorted(f.name for f in tmp_path.iterdir()) == ["config.json", "run.sqlite", "summary.json"]


def test_run_in_says_nothing_unless_asked(tmp_path, capsys):
    run_in(small("seed=5"), tmp_path, pages=False)
    assert capsys.readouterr().out == ""


def test_run_in_will_not_write_over_a_record(tmp_path):
    run_in(small("seed=5"), tmp_path, pages=False)
    before = (tmp_path / "run.sqlite").read_bytes()
    with pytest.raises(FileExistsError):
        run_in(small("seed=6"), tmp_path, pages=False)
    assert (tmp_path / "run.sqlite").read_bytes() == before
    assert json.loads((tmp_path / "config.json").read_text())["seed"] == 5
