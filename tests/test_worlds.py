"""Two worlds, one engine. Each world has a folder of its own with its settings, and is run
from there: nobody chooses a world by setting a dial."""

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORLDS = {"wef": "WEF world", "rtr": "RTR world"}
RTR_ONLY = {"free_hours", "job_hours", "mortgage_ltv", "mortgage_weeks", "mortgage_income_share",
            "foreclosed_price_drop", "empty_sale_weeks", "newcomers_buy", "owners_pay_any_price", "makers_weigh_jobs", "home_loan_presses", "makers_buy_in_town", "town_goods_premium",
            "line_is_who_would_take", "unhappy_makers_apply", "staff_keep_pay", "loss_sheds_staff", "longest_serving_first",
            "owners_judge_by_what_they_pay", "going_without_at_lowest_price", "going_without_appliances_at_owning", "arrivals_own_appliances", "reservation_covers_basket", "floor_counts_kept_business", "jobless_leaves_out_own_work", "maker_margin",
            "hustle_min_hours", "hustle_rate", "hustle_rate_struggling", "maker_hour_floor", "hustle_quit_share",
            "hustle_full_share", "hustle_loan_weeks", "hustle_loan_term_weeks", "idea_rate", "idea_hours",
            "tools_entertainment", "tools_invented", "tools_food", "tools_repair", "tools_set_building",
            "tools_home_building"}
SMALL = ["--years", "1", "--set", "population_cap=30"]
OLD_NAME = "wef" + "world"                       # written this way so this file does not hold it either


def _home(tmp_path, world):
    """A copy of a world's folder, so a test's runs do not land among the real ones."""
    home = tmp_path / world
    home.mkdir()
    shutil.copy(ROOT / world / "settings.json", home)
    return home


def _summary(run_dir):
    return json.loads((run_dir / "summary.json").read_text())


# --- the layout ------------------------------------------------------------------------------------------
def test_each_world_has_a_folder_with_its_page_its_settings_and_its_scripts():
    for world in WORLDS:
        for name in ("README.md", "settings.json", "run.py", "batch.py"):
            assert (ROOT / world / name).is_file(), f"{world}/{name}"
    assert (ROOT / "engine" / "town.py").is_file() and (ROOT / "engine" / "rtr_owning.py").is_file()
    assert not (ROOT / OLD_NAME).exists() and not (ROOT / "configs").exists()
    assert not (ROOT / "engine" / "owning.py").exists()


def test_the_old_name_is_gone_from_the_code_the_commands_and_the_worlds_pages():
    files = [ROOT / "README.md", ROOT / "pyproject.toml"]
    for pattern in ("engine/*.py", "tests/*.py", "wef/*.py", "wef/*.md", "wef/*.json", "wef/experiments/**/*.py",
                    "rtr/*.py", "rtr/*.md", "rtr/*.json"):
        files += sorted(ROOT.glob(pattern))
    assert len(files) > 60
    for path in files:
        assert OLD_NAME not in path.read_text(encoding="utf-8").lower(), path.relative_to(ROOT)


# --- the settings ----------------------------------------------------------------------------------------
def test_each_worlds_settings_are_the_engines_own_for_that_world():
    from engine.config import load_config
    assert load_config(str(ROOT / "wef" / "settings.json")).to_dict() == load_config(None).to_dict()
    assert (load_config(str(ROOT / "rtr" / "settings.json")).to_dict()
            == load_config(None, ["world=rtr"]).to_dict())


def test_the_rent_only_world_has_no_settings_about_owning():
    wef = json.loads((ROOT / "wef" / "settings.json").read_text())
    rtr = json.loads((ROOT / "rtr" / "settings.json").read_text())
    assert wef["world"] == "wef" and rtr["world"] == "rtr"
    assert not (RTR_ONLY & set(wef)) and set(rtr) - set(wef) == RTR_ONLY     # every other dial is in both


# --- running a world -------------------------------------------------------------------------------------
@pytest.mark.parametrize("world", sorted(WORLDS))
def test_a_town_run_from_a_worlds_folder_is_a_town_of_that_world_and_says_so(world, tmp_path):
    done = subprocess.run([sys.executable, str(ROOT / world / "run.py"), *SMALL, "--out", str(tmp_path)],
                          capture_output=True, text=True, cwd=tmp_path)     # from anywhere: it finds its own folder
    assert done.returncode == 0, done.stderr
    assert WORLDS[world] in done.stdout.splitlines()[0]
    [run_dir] = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert _summary(run_dir)["world"] == world
    for page in ("dashboard.html", "town.html"):
        text = (run_dir / page).read_text(encoding="utf-8")
        assert WORLDS[world] in text
        assert all(other not in text for w, other in WORLDS.items() if w != world), page


def test_a_worlds_runs_and_batches_land_in_its_own_folder(tmp_path):
    from engine.__main__ import world_main
    home = _home(tmp_path, "rtr")
    assert world_main("rtr", home, "run", SMALL + ["--quiet"]) == 0
    [run_dir] = list((home / "runs").iterdir())
    assert _summary(run_dir)["world"] == "rtr"
    assert world_main("rtr", home, "batch", ["two", "--seeds", "1-2", "--set", "population_cap=30",
                                             "--set", "years=1", "--jobs", "1", "--quiet"]) == 0
    batch_dir = home / "batches" / "two"
    assert (batch_dir / "batch.json").is_file()
    assert "RTR world" in (batch_dir / "batch.html").read_text(encoding="utf-8")
    assert "WEF world" not in (batch_dir / "batch.html").read_text(encoding="utf-8")


def test_a_worlds_folder_runs_only_that_world(tmp_path, capsys):
    from engine.__main__ import world_main
    for more in (["--set", "world=rtr"], ["--config", str(ROOT / "rtr" / "settings.json")]):
        with pytest.raises(SystemExit) as stop:
            world_main("wef", ROOT / "wef", "run", SMALL + ["--quiet", "--out", str(tmp_path)] + more)
        assert stop.value.code == 2
        assert "rtr/run.py" in capsys.readouterr().err                      # it says where the other world is run
    assert world_main("rtr", ROOT / "rtr", "batch", ["x", "--vary", "world=wef,rtr", "--out", str(tmp_path)]) == 2
    assert "wef/batch.py" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []                                    # and nothing was run


def test_settings_of_ones_own_are_run_in_the_folders_world(tmp_path):
    from engine.__main__ import world_main
    mine = tmp_path / "mine.json"
    mine.write_text('{"population_cap": 30, "years": 1}')
    out = tmp_path / "out"
    assert world_main("rtr", ROOT / "rtr", "run", ["--config", str(mine), "--out", str(out), "--quiet"]) == 0
    [run_dir] = list(out.iterdir())
    assert _summary(run_dir)["world"] == "rtr" and _summary(run_dir)["population"] <= 30


def test_the_engine_alone_does_not_run_a_town_without_a_world(tmp_path, capsys):
    from engine.__main__ import main
    with pytest.raises(SystemExit) as stop:
        main(["run", *SMALL, "--out", str(tmp_path)])
    err = capsys.readouterr().err
    assert stop.value.code == 2 and "wef/run.py" in err and "rtr/run.py" in err
    assert main(["batch", "b", "--seeds", "1", "--out", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "wef/batch.py" in err and "rtr/batch.py" in err and list(tmp_path.iterdir()) == []
