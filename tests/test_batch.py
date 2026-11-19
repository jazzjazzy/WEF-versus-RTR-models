"""Many towns at once: the plan of a batch, running it, and the table it leaves."""

import json
import sqlite3

import pytest

from engine import batch
from engine.batch import BatchError, make_plan, parse_seeds, slug, town_overrides
from engine.config import load_config
from engine.recorder import code_fingerprint

SMALL = ["population_cap=30", "years=1"]


def run_table(run_dir):
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        return dict(con.execute("SELECT key, value FROM run").fetchall())
    finally:
        con.close()


# --- seeds ------------------------------------------------------------------------------------------
def test_seeds_are_ranges_and_single_numbers_sorted_with_no_repeats():
    assert parse_seeds("1-5,9") == [1, 2, 3, 4, 5, 9]
    assert parse_seeds("3,1,2,2") == [1, 2, 3]
    assert parse_seeds(" 7 ") == [7]
    assert parse_seeds("0-2, 10-11") == [0, 1, 2, 10, 11]


@pytest.mark.parametrize("text", ["", " ", "a", "1-", "-3", "5-1", "1,,2", "1.5", "1-2-3"])
def test_seeds_that_make_no_sense_are_refused(text):
    with pytest.raises(BatchError):
        parse_seeds(text)


# --- names that are safe as folders -------------------------------------------------------------------
def test_a_slug_keeps_what_is_safe_and_replaces_the_rest():
    assert slug("needs.food.initial_price=5000") == "needs.food.initial_price=5000"
    assert slug("as written") == "as_written"
    assert slug("price rule=<b>/x") == "price_rule=_b__x"
    assert slug("a\\b:c") == "a_b_c"


def test_a_slug_is_never_empty_and_never_only_dots():
    assert slug("") == "_"
    assert slug(".") == "_."
    assert slug("..") == "_.."


# --- the plan -----------------------------------------------------------------------------------------
def test_a_plan_with_nothing_varied_is_the_model_as_written():
    plan = make_plan("first", [1, 2, 3])
    assert plan["name"] == "first" and plan["seeds"] == [1, 2, 3]
    assert plan["settings"] == [{"name": "as written", "slug": "base", "overrides": []}]
    assert plan["record"] == ["snapshot_every=13"]          # the lighter record
    assert (plan["code"], plan["model"]) == (code_fingerprint(), batch.model_fingerprint())
    assert (plan["base"], plan["config"]) == ([], None)
    assert json.loads(json.dumps(plan)) == plan             # it can be written out and read back


def test_the_base_is_named_by_the_dials_it_sets():
    plan = make_plan("b", [1], base=SMALL)
    assert plan["settings"][0] == {"name": "population_cap=30, years=1", "slug": "base", "overrides": []}
    assert plan["base"] == SMALL


def test_the_base_has_a_short_folder_however_many_dials_it_sets():
    dials = ["population_cap=30", "years=1", "habit_weeks=52", "price_rule=search", "walk_range=7", "move_prob=0.04",
             "wage_step_up=0.03", "wage_step_down=0.03", "homes_per_spot=9", "map_width=12", "map_height=12",
             "transport_speed=5", "time_value_share=0.03"]
    plan = make_plan("many", [1], base=dials, vary=["habit_weeks=104"])
    assert [s["slug"] for s in plan["settings"]] == ["base", "habit_weeks=104"]
    assert len(plan["settings"][0]["name"]) > 200           # the name still says what the base is


def test_a_batch_does_not_run_towns_on_after_they_fail():
    for kwargs in ({"base": ["stop_on_failure=false"]}, {"vary": ["stop_on_failure=false"]}):
        with pytest.raises(BatchError) as stop:
            make_plan("on", [1], **kwargs)
        assert "stop_on_failure" in str(stop.value)
    make_plan("on", [1], base=["stop_on_failure=true"])      # saying what is already so is fine


def test_there_is_a_limit_to_how_many_seeds_a_batch_takes():
    assert len(parse_seeds("1-100000")) == 100_000
    with pytest.raises(BatchError):
        parse_seeds("1-100001")
    with pytest.raises(BatchError):
        parse_seeds("1-60000,70000-130000")


def test_each_varied_value_is_a_setting_of_its_own():
    plan = make_plan("v", [1, 2], base=SMALL, vary=["price_rule=ratchet,search", "habit_weeks=0,52,104"])
    assert [s["name"] for s in plan["settings"]] == [
        "population_cap=30, years=1", "price_rule=search", "habit_weeks=0", "habit_weeks=104"]
    assert [s["overrides"] for s in plan["settings"]] == [
        [], ["price_rule=search"], ["habit_weeks=0"], ["habit_weeks=104"]]
    # ratchet and 52 are what the base already is: not run twice


def test_a_varied_value_given_twice_is_one_setting():
    plan = make_plan("v", [1], vary=["habit_weeks=104,104, 104"])
    assert [s["name"] for s in plan["settings"]] == ["as written", "habit_weeks=104"]


def test_town_overrides_put_the_record_first_and_the_seed_last():
    plan = make_plan("v", [4], base=SMALL, vary=["price_rule=search"])
    assert town_overrides(plan, plan["settings"][1], 4) == [
        "snapshot_every=13", "population_cap=30", "years=1", "price_rule=search", "seed=4"]
    cfg = load_config(None, town_overrides(plan, plan["settings"][1], 4))
    assert (cfg.snapshot_every, cfg.population_cap, cfg.price_rule, cfg.seed) == (13, 30, "search", 4)


def test_full_keeps_the_weekly_record_of_every_person():
    plan = make_plan("f", [1], full=True)
    assert plan["record"] == []
    assert load_config(None, town_overrides(plan, plan["settings"][0], 1)).snapshot_every == 1


def test_a_base_that_sets_its_own_recording_wins_over_the_lighter_record():
    plan = make_plan("f", [1], base=["snapshot_every=4"])
    assert load_config(None, town_overrides(plan, plan["settings"][0], 1)).snapshot_every == 4


@pytest.mark.parametrize("kwargs, word", [
    ({"base": ["price_rool=search"]}, "price_rool"),
    ({"vary": ["price_rule=ratchet,serach"]}, "price_rule"),
    ({"vary": ["habit_weeks"]}, "habit_weeks"),
    ({"vary": ["habit_weeks="]}, "habit_weeks"),
    ({"base": ["seed=4"]}, "seed"),
    ({"vary": ["seed=1,2"]}, "seed"),
])
def test_a_mistyped_dial_or_value_stops_the_plan_and_is_named(kwargs, word):
    with pytest.raises(BatchError) as stop:
        make_plan("bad", [1], **kwargs)
    assert word in str(stop.value)


@pytest.mark.parametrize("name", ["", "two words", "a/b", "..", "x<y"])
def test_a_batch_name_must_be_a_safe_folder_name(name):
    with pytest.raises(BatchError):
        make_plan(name, [1])


def test_a_plan_needs_at_least_one_seed():
    with pytest.raises(BatchError):
        make_plan("none", [])


def test_two_settings_that_would_share_a_folder_are_refused(monkeypatch):
    monkeypatch.setattr(batch, "slug", lambda name: "same")     # no two real dials collide, so force it
    with pytest.raises(BatchError) as stop:
        make_plan("clash", [1], vary=["habit_weeks=52,104"])
    assert "folder" in str(stop.value)


def test_a_settings_file_is_part_of_the_plan(tmp_path):
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"population_cap": 30, "years": 1, "price_rule": "search"}))
    plan = make_plan("file", [1], config=str(short), vary=["price_rule=ratchet,search"])
    assert plan["config"] == str(short)
    assert [s["name"] for s in plan["settings"]] == ["short.json", "price_rule=ratchet"]   # search is the file's own
    assert load_config(plan["config"], town_overrides(plan, plan["settings"][0], 1)).price_rule == "search"


# --- running a batch ----------------------------------------------------------------------------------
def towns(batch_dir, plan):
    """Every town folder of the plan, keyed by (setting name, seed)."""
    return {(setting["name"], seed): batch.town_dir(batch_dir, setting, seed)
            for setting in plan["settings"] for seed in plan["seeds"]}


def stamps(batch_dir, plan):
    """When each town's record was last written: it changes if the town is run again."""
    return {key: (folder / "run.sqlite").stat().st_mtime_ns for key, folder in towns(batch_dir, plan).items()}


def prints(batch_dir, plan):
    return {key: run_table(folder)["fingerprint"] for key, folder in towns(batch_dir, plan).items()}


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    """Two settings on three seeds, three towns at a time. Tests only read it."""
    root = tmp_path_factory.mktemp("batches")
    plan = make_plan("made", [1, 2, 3], base=SMALL, vary=["price_rule=search"])
    return batch.run_batch(plan, out_root=root, jobs=3, quiet=True), plan, root


def fresh(tmp_path, seeds=(1, 2)):
    """A small batch of its own, for a test that changes it."""
    plan = make_plan("own", list(seeds), base=SMALL, vary=["price_rule=search"])
    return batch.run_batch(plan, out_root=tmp_path, jobs=2, quiet=True), plan


def test_a_batch_makes_one_ordinary_run_folder_for_each_town(made):
    batch_dir, plan, root = made
    assert batch_dir == root / "made"
    assert {p.name for p in (batch_dir / "towns").iterdir()} == {"base", "price_rule=search"}
    folders = towns(batch_dir, plan)
    assert len(folders) == 6
    for (name, seed), folder in folders.items():
        assert folder.name == f"seed-{seed:04d}"
        assert sorted(f.name for f in folder.iterdir()) == ["config.json", "run.sqlite", "summary.json"]   # no pages
        cfg = load_config(str(folder / "config.json"))
        assert (cfg.seed, cfg.population_cap, cfg.snapshot_every) == (seed, 30, 13)
        assert cfg.price_rule == ("search" if name == "price_rule=search" else "ratchet")
        assert run_table(folder)["outcome"] in ("survived", "failed")


def test_a_batch_town_is_the_same_town_as_the_one_run_alone(made, tmp_path):
    from engine.runner import run
    batch_dir, plan, _ = made
    alone = run(load_config(None, SMALL + ["price_rule=search", "seed=2"]), out_root=tmp_path, quiet=True)
    assert load_config(str(alone / "config.json")).snapshot_every == 1          # the full weekly record
    assert run_table(alone)["fingerprint"] == prints(batch_dir, plan)[("price_rule=search", 2)]


def test_how_many_towns_run_at_once_does_not_change_them(made, tmp_path):
    batch_dir, plan, _ = made
    single = batch.run_batch({**plan, "name": "single"}, out_root=tmp_path, jobs=1, quiet=True)
    assert prints(single, plan) == prints(batch_dir, plan)
    assert len(set(prints(single, plan).values())) == 6                         # and they are six different towns


def test_a_finished_town_is_not_run_again_and_new_seeds_are_added(tmp_path):
    batch_dir, plan = fresh(tmp_path)
    before = stamps(batch_dir, plan)
    batch.run_batch(plan, out_root=tmp_path, jobs=2, quiet=True)
    assert stamps(batch_dir, plan) == before
    more = make_plan("own", [2, 3], base=SMALL, vary=["price_rule=search"])
    batch.run_batch(more, out_root=tmp_path, jobs=2, quiet=True)
    stored = json.loads((batch_dir / "batch.json").read_text())
    assert stored["seeds"] == [1, 2, 3]
    after = stamps(batch_dir, stored)
    assert len(after) == 6 and {key: after[key] for key in before} == before


def test_a_setting_can_be_added_to_a_batch_later(tmp_path):
    batch_dir, plan = fresh(tmp_path)
    before = stamps(batch_dir, plan)
    batch.run_batch(make_plan("own", [1], base=SMALL, vary=["habit_weeks=104"]), out_root=tmp_path, jobs=2, quiet=True)
    stored = json.loads((batch_dir / "batch.json").read_text())
    assert [s["name"] for s in stored["settings"]] == ["population_cap=30, years=1", "price_rule=search", "habit_weeks=104"]
    after = stamps(batch_dir, stored)
    assert {key: after[key] for key in before} == before
    assert all(("habit_weeks=104", seed) in after for seed in stored["seeds"])    # the new setting runs on every seed


def test_a_setting_that_is_already_there_under_another_spelling_is_not_run_twice(tmp_path):
    batch_dir, plan = fresh(tmp_path)
    batch.run_batch(make_plan("own", [1, 2], base=SMALL, vary=["wage_step_up=0.03"]), out_root=tmp_path, jobs=2, quiet=True)
    before = json.loads((batch_dir / "batch.json").read_text())
    batch.run_batch(make_plan("own", [1, 2], base=SMALL, vary=["wage_step_up=0.030", "price_rule= search"]),
                    out_root=tmp_path, jobs=2, quiet=True)
    assert json.loads((batch_dir / "batch.json").read_text()) == before
    assert sorted(p.name for p in (batch_dir / "towns").iterdir()) == ["base", "price_rule=search", "wage_step_up=0.03"]


def test_a_town_left_unfinished_is_run_again_and_its_neighbours_are_left_alone(tmp_path):
    batch_dir, plan = fresh(tmp_path, seeds=(1, 2, 3))
    folder = batch.town_dir(batch_dir, plan["settings"][0], 2)
    was = run_table(folder)["fingerprint"]
    con = sqlite3.connect(folder / "run.sqlite")
    con.execute("DELETE FROM run WHERE key = 'outcome'")                         # as a stopped run leaves it
    con.commit()
    con.close()
    (folder / "leftover.txt").write_text("from the run that was stopped")
    assert not batch.finished(folder)
    others = {key: stamp for key, stamp in stamps(batch_dir, plan).items() if key != (plan["settings"][0]["name"], 2)}
    batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    assert batch.finished(folder) and not (folder / "leftover.txt").exists()
    assert run_table(folder)["fingerprint"] == was
    after = stamps(batch_dir, plan)
    assert {key: after[key] for key in others} == others                         # only that one town was touched
    assert len(others) == 5


def test_finished_is_false_for_no_folder_no_record_and_a_file_that_is_not_a_record(tmp_path):
    assert not batch.finished(tmp_path / "nowhere")
    assert not batch.finished(tmp_path)
    (tmp_path / "run.sqlite").write_text("not a record")
    assert not batch.finished(tmp_path)


@pytest.mark.parametrize("change, words", [
    (lambda plan: {**plan, "model": "0123456789abcdef"}, ["0123456789abcdef", "model"]),
    (lambda plan: make_plan("made", [1], base=SMALL + ["habit_weeks=104"]), ["base"]),
    (lambda plan: make_plan("made", [1], base=SMALL, full=True), ["record"]),
])
def test_a_batch_cannot_be_carried_on_with_another_model_or_another_base(made, change, words):
    batch_dir, plan, root = made
    stored = (batch_dir / "batch.json").read_text()
    before = stamps(batch_dir, json.loads(stored))
    with pytest.raises(BatchError) as stop:
        batch.run_batch(change(plan), out_root=root, jobs=1, quiet=True)
    for word in words:
        assert word in str(stop.value)
    if "model" in words:
        assert batch.model_fingerprint() in str(stop.value)                      # both stamps are named
    assert (batch_dir / "batch.json").read_text() == stored
    assert stamps(batch_dir, json.loads(stored)) == before                       # and nothing was run


# --- which code made the towns ------------------------------------------------------------------------
def test_the_model_stamp_covers_the_model_and_not_the_pages(tmp_path):
    import pathlib
    import shutil
    here = pathlib.Path(batch.__file__).parent
    copy = tmp_path / "engine"
    shutil.copytree(here, copy, ignore=shutil.ignore_patterns("__pycache__"))
    assert batch.model_fingerprint(copy) == batch.model_fingerprint() == batch.model_fingerprint(here)
    assert len(batch.model_fingerprint()) == 16
    for name in sorted(batch.NOT_MODEL):
        assert (here / name).is_file(), name                 # a file renamed must be renamed here too
        with open(copy / name, "a") as fh:
            fh.write("\n# a change to a page or a tool\n")
        assert batch.model_fingerprint(copy) == batch.model_fingerprint()
    assert {"dashboard.py", "townview.py", "townpage.py", "batch.py", "batchpage.py", "__main__.py"} == set(batch.NOT_MODEL)
    for name in ("labour.py", "runner.py", "recorder.py", "config.py"):
        again = tmp_path / name.replace(".py", "")
        shutil.copytree(here, again, ignore=shutil.ignore_patterns("__pycache__"))
        with open(again / name, "a") as fh:
            fh.write("\n# a change to the model\n")
        assert batch.model_fingerprint(again) != batch.model_fingerprint(), name


def test_a_batch_is_carried_on_after_a_change_to_a_page(tmp_path):
    batch_dir, plan = fresh(tmp_path)
    later = {**make_plan("own", [1, 2, 3], base=SMALL, vary=["price_rule=search"]), "code": "another page's code"}
    batch.run_batch(later, out_root=tmp_path, jobs=2, quiet=True)                # same model, other pages
    stored = json.loads((batch_dir / "batch.json").read_text())
    assert stored["seeds"] == [1, 2, 3] and stored["model"] == batch.model_fingerprint()
    assert all(batch.finished(folder) for folder in towns(batch_dir, stored).values())


def test_a_batch_planned_before_the_model_stamp_is_held_to_the_whole_code(tmp_path):
    batch_dir, plan = fresh(tmp_path)
    old = json.loads((batch_dir / "batch.json").read_text())
    del old["model"]
    (batch_dir / "batch.json").write_text(json.dumps(old))
    batch.run_batch(make_plan("own", [1, 2, 3], base=SMALL, vary=["price_rule=search"]), out_root=tmp_path, jobs=2,
                    quiet=True)                              # the same code: carried on, and stamped from now on
    assert json.loads((batch_dir / "batch.json").read_text())["model"] == batch.model_fingerprint()
    old["code"] = "0000000000000000"
    (batch_dir / "batch.json").write_text(json.dumps(old))
    with pytest.raises(BatchError) as stop:
        batch.run_batch(make_plan("own", [1, 2, 3, 4], base=SMALL, vary=["price_rule=search"]), out_root=tmp_path,
                        jobs=1, quiet=True)
    assert "0000000000000000" in str(stop.value)


def test_no_town_is_run_once_the_models_code_is_not_the_plans(tmp_path, monkeypatch):
    plan = make_plan("moved", [1, 2], base=SMALL)
    monkeypatch.setattr(batch, "model_fingerprint", lambda folder=None: "f" * 16)   # as if a model file were edited since
    with pytest.raises(batch.TownsFailed) as stop:
        batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    assert "changed" in str(stop.value) and "2 of 2" in str(stop.value)
    assert not any(batch.finished(batch.town_dir(tmp_path / "moved", plan["settings"][0], seed)) for seed in (1, 2))


# --- stopping, and what can go wrong ------------------------------------------------------------------
def test_ctrl_c_with_one_town_at_a_time_stops_and_keeps_what_finished(tmp_path, monkeypatch):
    real = batch.run_in

    def pressed(cfg, run_dir, **kwargs):
        if cfg.seed == 2:
            raise KeyboardInterrupt
        return real(cfg, run_dir, **kwargs)

    monkeypatch.setattr(batch, "run_in", pressed)
    plan = make_plan("halted", [1, 2, 3], base=SMALL)
    with pytest.raises(batch.Stopped) as stop:
        batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    assert "1 of 3" in str(stop.value) and "again" in str(stop.value)
    done = {seed: batch.finished(batch.town_dir(tmp_path / "halted", plan["settings"][0], seed)) for seed in (1, 2, 3)}
    assert done == {1: True, 2: False, 3: False}


def test_ctrl_c_at_the_keyboard_stops_a_batch_running_several_towns(tmp_path):
    import os
    import pathlib
    import signal
    import subprocess
    import sys
    root = pathlib.Path(batch.__file__).parent.parent
    command = [sys.executable, str(root / "wef" / "batch.py"), "halt", "--seeds", "1-24", "--set", "population_cap=50",
               "--set", "years=2", "--out", str(tmp_path), "--jobs", "2"]
    # Ctrl-C must mean what it means at a keyboard even when the tests themselves were started
    # somewhere that ignores it (a background job does).
    proc = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True,
                            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.default_int_handler))
    lines = []
    while sum("/24 " in line for line in lines) < 2:         # two towns have been reported
        line = proc.stdout.readline()
        assert line, "the batch ended before it could be stopped"
        lines.append(line)
    os.killpg(proc.pid, signal.SIGINT)                       # Ctrl-C at a terminal reaches the whole group
    out, err = proc.communicate(timeout=300)
    lines += out.splitlines()
    assert proc.returncode == 130, err
    assert "Traceback" not in err and "stopped" in err and "again" in err
    stop = next(i for i, line in enumerate(lines) if line.startswith("stopping:"))
    assert "Letting the 2 already running finish" in lines[stop]
    after = [line for line in lines[stop + 1:] if "/24 " in line]
    assert len(after) == 2                                   # the two in flight were let finish; no new one was started
    plan = json.loads((tmp_path / "halt" / "batch.json").read_text())
    done = sum(batch.finished(folder) for folder in towns(tmp_path / "halt", plan).values())
    assert done == sum("/24 " in line for line in lines) and 4 <= done < 24
    assert f"stopped: {done} of 24 towns finished" in err
    page = (tmp_path / "halt" / "batch.html").read_text()
    assert f"{24 - done} of 24 towns" in page and "missing or unfinished" in page
    again = subprocess.run(command + ["--quiet"], cwd=root, capture_output=True, text=True, timeout=300)
    assert again.returncode == 0, again.stderr
    assert all(batch.finished(folder) for folder in towns(tmp_path / "halt", plan).values())


def test_a_process_that_dies_is_reported_and_the_rest_can_be_carried_on(tmp_path, monkeypatch):
    import concurrent.futures
    from concurrent.futures.process import BrokenProcessPool

    class Dead:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def submit(self, fn, task):
            future = concurrent.futures.Future()
            future.set_exception(BrokenProcessPool("a child process terminated abruptly"))
            return future

    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", Dead)
    with pytest.raises(batch.TownsFailed) as stop:
        batch.run_batch(make_plan("dead", [1, 2, 3], base=SMALL), out_root=tmp_path, jobs=2, quiet=True)
    assert "died" in str(stop.value) and "again" in str(stop.value)


def test_a_town_that_cannot_be_run_leaves_the_whole_error_in_its_folder(tmp_path, monkeypatch):
    def faulty(cfg, run_dir, **kwargs):
        raise RuntimeError("the model fell over")

    monkeypatch.setattr(batch, "run_in", faulty)
    plan = make_plan("fell", [1], base=SMALL)
    with pytest.raises(batch.TownsFailed) as stop:
        batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    note = batch.town_dir(tmp_path / "fell", plan["settings"][0], 1) / "error.txt"
    assert "Traceback" in note.read_text() and "the model fell over" in note.read_text()
    assert "error.txt" in str(stop.value)


def test_a_batch_in_a_folder_with_a_hash_a_question_mark_and_a_percent_in_its_name(tmp_path):
    odd = tmp_path / "odd#dir?x%20y"
    plan = make_plan("named", [1, 2], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=odd, jobs=1, quiet=True)
    assert all(batch.finished(folder) for folder in towns(batch_dir, plan).values())
    before = stamps(batch_dir, plan)
    batch.run_batch(plan, out_root=odd, jobs=1, quiet=True)
    assert stamps(batch_dir, plan) == before                 # finished towns are seen as finished, not run again
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        assert con.execute("SELECT COUNT(*) FROM towns").fetchone()[0] == 2
    finally:
        con.close()
    from engine.batchpage import build_batch_page
    assert "2 towns" in build_batch_page(batch_dir).read_text()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["odd#dir?x%20y"]      # and nothing strayed beside it


def test_every_town_is_run_from_the_batchs_own_copy_of_the_settings_file(tmp_path, monkeypatch):
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"population_cap": 30, "years": 1}))
    seen = []
    real = batch.run_town
    monkeypatch.setattr(batch, "run_town", lambda task: seen.append(task) or real(task))
    batch_dir = batch.run_batch(make_plan("copied", [1, 2], config=str(short)), out_root=tmp_path / "b", jobs=1, quiet=True)
    assert [task[1] for task in seen] == [str(batch_dir / "base-settings.json")] * 2


def test_a_settings_file_that_moved_but_says_the_same_carries_the_batch_on(tmp_path):
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"population_cap": 30, "years": 1}))
    batch_dir = batch.run_batch(make_plan("moved", [1], config=str(short)), out_root=tmp_path / "b", jobs=1, quiet=True)
    renamed = tmp_path / "renamed.json"
    renamed.write_text(json.dumps({"years": 1, "population_cap": 30}, indent=2))     # another name, another layout
    batch.run_batch(make_plan("moved", [1, 2], config=str(renamed)), out_root=tmp_path / "b", jobs=1, quiet=True)
    stored = json.loads((batch_dir / "batch.json").read_text())
    assert stored["seeds"] == [1, 2] and len(stored["settings"]) == 1


def test_a_folder_that_is_not_a_batch_is_left_alone(tmp_path):
    (tmp_path / "mine").mkdir()
    (tmp_path / "mine" / "notes.txt").write_text("keep")
    with pytest.raises(BatchError):
        batch.run_batch(make_plan("mine", [1], base=SMALL), out_root=tmp_path, jobs=1, quiet=True)
    assert sorted(p.name for p in (tmp_path / "mine").iterdir()) == ["notes.txt"]


def test_a_batch_keeps_its_own_copy_of_the_settings_file(tmp_path):
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"population_cap": 30, "years": 1, "price_rule": "search"}))
    plan = make_plan("filed", [1], config=str(short))
    batch_dir = batch.run_batch(plan, out_root=tmp_path / "batches", jobs=1, quiet=True)
    assert json.loads((batch_dir / "base-settings.json").read_text()) == json.loads(short.read_text())
    assert load_config(str(batch.town_dir(batch_dir, plan["settings"][0], 1) / "config.json")).price_rule == "search"
    short.write_text(json.dumps({"population_cap": 30, "years": 1, "price_rule": "ratchet"}))
    with pytest.raises(BatchError) as stop:
        batch.run_batch(make_plan("filed", [1, 2], config=str(short)), out_root=tmp_path / "batches", jobs=1, quiet=True)
    assert "settings file" in str(stop.value) and "base" in str(stop.value)
    assert not batch.town_dir(batch_dir, plan["settings"][0], 2).exists()


def test_one_town_that_cannot_be_run_does_not_cost_the_others(tmp_path, monkeypatch):
    real = batch.run_in

    def faulty(cfg, run_dir, **kwargs):
        if cfg.seed == 2:
            raise RuntimeError("the model fell over")
        return real(cfg, run_dir, **kwargs)

    monkeypatch.setattr(batch, "run_in", faulty)
    plan = make_plan("partly", [1, 2, 3], base=SMALL)
    with pytest.raises(BatchError) as stop:
        batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    assert "seed 2" in str(stop.value) and "the model fell over" in str(stop.value)
    done = {seed: batch.finished(batch.town_dir(tmp_path / "partly", plan["settings"][0], seed)) for seed in (1, 2, 3)}
    assert done == {1: True, 2: False, 3: True}


def test_a_batch_says_how_each_town_ended_as_it_goes(tmp_path, capsys):
    plan = make_plan("loud", [1, 2], base=SMALL)
    batch.run_batch(plan, out_root=tmp_path, jobs=1)
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines[0].startswith("batch loud: 2 towns to run")
    assert any("seed 1" in line and ("still standing" in line or "failed in year" in line) for line in lines)
    assert any(line.lstrip().startswith("2/2") for line in lines)
    batch.run_batch(plan, out_root=tmp_path, jobs=1)
    assert "nothing left to run" in capsys.readouterr().out


def test_the_default_leaves_two_cores_free_and_is_at_least_one():
    import os
    assert batch.default_jobs() == max(1, (os.cpu_count() or 1) - 2)


# --- the table ----------------------------------------------------------------------------------------
def dump(path):
    """Every row of every table of a batch table, in a fixed order."""
    con = sqlite3.connect(path)
    try:
        names = [name for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        return {name: sorted(con.execute(f"SELECT * FROM {name}").fetchall(), key=repr) for name in names}
    finally:
        con.close()


@pytest.fixture(scope="module")
def table(mixed_batch):
    batch_dir, plan = mixed_batch
    con = sqlite3.connect(batch.collect(batch_dir))
    yield batch_dir, plan, con
    con.close()


def test_the_mixed_batch_is_mixed(table):
    """The towns these tests lean on: failures and survivors, early and late."""
    _, _, con = table
    base = con.execute("SELECT outcome, failed_week FROM towns WHERE setting = 0").fetchall()
    strict = con.execute("SELECT outcome, failed_week FROM towns WHERE setting = 1").fetchall()
    assert {outcome for outcome, _ in base} == {"failed", "survived"}
    assert all(outcome == "failed" for outcome, _ in strict)
    assert any(week < 52 for _, week in strict) and any(week > 52 for _, week in strict)


def test_collect_writes_the_table_into_the_batch_folder_and_leaves_no_working_file(table):
    batch_dir, _, _ = table
    names = {p.name for p in batch_dir.iterdir()}
    assert {"batch.json", "batch.sqlite", "towns"} <= names <= {"batch.json", "batch.sqlite", "towns", "batch.html"}


def test_the_table_holds_the_plan_and_the_settings(table):
    batch_dir, plan, con = table
    meta = dict(con.execute("SELECT key, value FROM batch").fetchall())
    assert json.loads(meta["plan"]) == json.loads((batch_dir / "batch.json").read_text()) == plan
    assert (meta["code"], meta["planned"], meta["finished"]) == (code_fingerprint(), "16", "16")
    assert con.execute("SELECT setting, name, slug, overrides FROM settings ORDER BY setting").fetchall() == [
        (i, s["name"], s["slug"], json.dumps(s["overrides"])) for i, s in enumerate(plan["settings"])]


def test_every_town_row_equals_the_towns_own_record(table):
    batch_dir, plan, con = table
    rows = con.execute("SELECT setting, seed, folder, outcome, weeks, failed_week, full_week, year_weeks, "
                       "fingerprint, code, events, summary FROM towns ORDER BY setting, seed").fetchall()
    assert [(row[0], row[1]) for row in rows] == [(i, seed) for i in (0, 1) for seed in range(1, 9)]
    for setting, seed, folder, outcome, weeks, failed, full, year_weeks, fingerprint, code, events, summary in rows:
        assert folder == f"towns/{plan['settings'][setting]['slug']}/seed-{seed:04d}"
        meta = run_table(batch_dir / folder)
        own = json.loads(meta["summary"])
        assert json.loads(summary) == own
        assert (outcome, weeks, failed, full) == (meta["outcome"], own["weeks"], own["failed_week"], own["full_week"])
        assert (fingerprint, code, events) == (meta["fingerprint"], meta["code_fingerprint"], int(meta["events"]))
        assert year_weeks == 52 and own["seed"] == seed


def test_the_moments_are_the_first_week_each_thing_happened(table):
    batch_dir, _, con = table
    seen = set()
    for setting, seed, folder in con.execute("SELECT setting, seed, folder FROM towns").fetchall():
        town = sqlite3.connect(batch_dir / folder / "run.sqlite")
        try:
            first = lambda kind: town.execute("SELECT MIN(week) FROM events WHERE kind = ?", (kind,)).fetchone()[0]  # noqa: E731
            expect = {"full": first("town_full"), "land": first("land_scarce"), "failed": first("town_failed"),
                      "transport": town.execute("SELECT MIN(founded) FROM firm_static WHERE need = 'transport'").fetchone()[0]}
        finally:
            town.close()
        got = dict(con.execute("SELECT name, week FROM moments WHERE setting = ? AND seed = ?", (setting, seed)).fetchall())
        assert got == {name: week for name, week in expect.items() if week is not None}
        seen |= set(got)
    assert {"full", "failed"} <= seen


def test_every_yearly_value_is_the_towns_weekly_measure_at_the_end_of_that_year(table):
    batch_dir, _, con = table
    checked = 0
    for setting, seed, folder, weeks in con.execute("SELECT setting, seed, folder, weeks FROM towns").fetchall():
        got = {(year, scope, metric): value for year, scope, metric, value in con.execute(
            "SELECT year, scope, metric, value FROM yearly WHERE setting = ? AND seed = ?", (setting, seed))}
        town = sqlite3.connect(batch_dir / folder / "run.sqlite")
        try:
            series = {(week, scope, metric): value for week, scope, metric, value in town.execute(
                "SELECT week, scope, metric, value FROM series WHERE week > 0 AND week % 52 = 0")}
        finally:
            town.close()
        expect = {(week // 52, scope, metric): value for (week, scope, metric), value in series.items()
                  if (scope, metric) in batch.MEASURES}
        assert got == expect
        assert {year for year, _, _ in got} == set(range(1, weeks // 52 + 1))      # only the years it finished
        if weeks >= 52:
            assert {(scope, metric) for _, scope, metric in got} == set(batch.MEASURES)   # every measure is in the record
        checked += len(got)
    assert checked > 1000
    assert con.execute("SELECT COUNT(*) FROM towns WHERE weeks < 52").fetchone()[0] >= 2  # and some have none at all


def test_the_measures_are_the_ones_the_design_names():
    assert len(batch.MEASURES) == len(set(batch.MEASURES)) == 30
    assert {scope for scope, _ in batch.MEASURES} == {"all", "owner", "working", "out", "town"}
    for wanted in (("all", "unhappy"), ("working", "cash_median"), ("out", "n"), ("town", "wage"), ("town", "basket"),
                   ("town", "homes"), ("town", "homes_vacant"), ("town", "top10_shares"), ("all", "homeless")):
        assert wanted in batch.MEASURES


def test_collecting_again_gives_the_same_table(table):
    batch_dir, _, _ = table
    before = dump(batch_dir / "batch.sqlite")
    batch.collect(batch_dir)
    assert dump(batch_dir / "batch.sqlite") == before
    assert set(before) == {"batch", "settings", "towns", "moments", "yearly"}


def test_a_town_missing_or_unfinished_is_left_out_and_counted(tmp_path):
    plan = make_plan("holes", [1, 2, 3], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    import shutil
    shutil.rmtree(batch.town_dir(batch_dir, plan["settings"][0], 1))
    con = sqlite3.connect(batch.town_dir(batch_dir, plan["settings"][0], 3) / "run.sqlite")
    con.execute("DELETE FROM run WHERE key = 'outcome'")
    con.commit()
    con.close()
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        assert con.execute("SELECT seed FROM towns").fetchall() == [(2,)]
        meta = dict(con.execute("SELECT key, value FROM batch").fetchall())
        assert (meta["planned"], meta["finished"]) == ("3", "1")
        assert {seed for (seed,) in con.execute("SELECT DISTINCT seed FROM yearly")} == {2}
    finally:
        con.close()


def test_collect_on_a_folder_that_is_not_a_batch_says_so(tmp_path):
    with pytest.raises(BatchError) as stop:
        batch.collect(tmp_path)
    assert "batch.json" in str(stop.value)


def test_the_table_says_what_each_setting_has_each_varied_dial_at(table):
    _, _, con = table
    rows = con.execute("SELECT setting, dials FROM settings ORDER BY setting").fetchall()
    assert [(number, json.loads(dials)) for number, dials in rows] == [
        (0, {"failure_unhappy_share": 0.35}), (1, {"failure_unhappy_share": 0.25})]


def test_a_dial_inside_a_need_can_be_varied_and_is_read_back(tmp_path):
    plan = make_plan("needs", [1], base=SMALL, vary=["needs.food.initial_price=9000", "founding_capital.food=30000000"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        rows = [json.loads(dials) for (dials,) in con.execute("SELECT dials FROM settings ORDER BY setting")]
    finally:
        con.close()
    assert [row["needs.food.initial_price"] for row in rows][1] == 9000
    assert [row["founding_capital.food"] for row in rows][2] == 30000000
    assert rows[0]["needs.food.initial_price"] != 9000 and rows[0]["founding_capital.food"] != 30000000


# --- the commands -------------------------------------------------------------------------------------
def test_the_batch_command_makes_the_towns_the_table_and_the_page(tmp_path, capsys):
    from conftest import wef_main as main
    code = main(["batch", "cmd", "--seeds", "1-2", "--set", "population_cap=30", "--set", "years=1",
                 "--vary", "price_rule=ratchet,search", "--out", str(tmp_path), "--jobs", "2"])
    out = capsys.readouterr().out
    batch_dir = tmp_path / "cmd"
    assert code == 0 and "4 towns to run, 2 at a time" in out
    assert out.strip().splitlines()[-1] == str(batch_dir / "batch.html")
    assert (batch_dir / "batch.sqlite").is_file() and "4 towns" in (batch_dir / "batch.html").read_text()
    stored = json.loads((batch_dir / "batch.json").read_text())
    assert [s["name"] for s in stored["settings"]] == ["population_cap=30, years=1", "price_rule=search"]
    assert all(batch.finished(batch.town_dir(batch_dir, s, seed)) for s in stored["settings"] for seed in (1, 2))
    assert main(["batch", "cmd", "--seeds", "1-2", "--set", "population_cap=30", "--set", "years=1",
                 "--vary", "price_rule=ratchet,search", "--out", str(tmp_path), "--quiet"]) == 0
    assert capsys.readouterr().out.strip() == str(batch_dir / "batch.html")     # quiet: only where the page is


@pytest.mark.parametrize("args, word", [
    (["--seeds", "1", "--set", "price_rool=search"], "price_rool"),
    (["--seeds", "one"], "seeds"),
    (["--seeds", "1", "--vary", "habit_weeks"], "habit_weeks"),
])
def test_the_batch_command_refuses_what_makes_no_sense_and_makes_nothing(tmp_path, capsys, args, word):
    from conftest import wef_main as main
    assert main(["batch", "bad"] + args + ["--out", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("wef: ") and word in err
    assert list(tmp_path.iterdir()) == []


def test_the_batch_command_says_why_a_batch_cannot_be_carried_on(tmp_path, capsys):
    from conftest import wef_main as main
    args = ["batch", "kept", "--seeds", "1", "--set", "population_cap=30", "--set", "years=1", "--out", str(tmp_path),
            "--quiet"]
    assert main(args) == 0
    assert main(args + ["--full"]) == 2
    assert "record" in capsys.readouterr().err


def test_batch_report_rebuilds_the_table_and_the_page(tmp_path, capsys):
    from conftest import wef_main as main
    batch_dir = batch.run_batch(make_plan("again", [1, 2], base=SMALL), out_root=tmp_path, jobs=1, quiet=True)
    assert not (batch_dir / "batch.sqlite").exists()
    assert main(["batch-report", str(batch_dir)]) == 0
    assert capsys.readouterr().out.strip() == str(batch_dir / "batch.html")
    assert (batch_dir / "batch.sqlite").is_file() and "2 towns" in (batch_dir / "batch.html").read_text()


def test_batch_report_on_a_folder_that_is_not_a_batch_says_so(tmp_path, capsys):
    from conftest import wef_main as main
    assert main(["batch-report", str(tmp_path)]) == 2
    assert "is not a batch" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_a_town_that_cannot_be_run_still_leaves_the_page_for_the_rest(tmp_path, capsys, monkeypatch):
    from conftest import wef_main as main
    real = batch.run_in

    def faulty(cfg, run_dir, **kwargs):
        if cfg.seed == 2:
            raise RuntimeError("the model fell over")
        return real(cfg, run_dir, **kwargs)

    monkeypatch.setattr(batch, "run_in", faulty)
    code = main(["batch", "partly", "--seeds", "1-3", "--set", "population_cap=30", "--set", "years=1",
                 "--out", str(tmp_path), "--jobs", "1", "--quiet"])
    streams = capsys.readouterr()
    assert code == 1 and "seed 2" in streams.err
    page = (tmp_path / "partly" / "batch.html").read_text()
    assert "1 of 3 towns is missing or unfinished" in page


def test_the_dial_values_in_the_table_are_the_towns_own_not_todays_defaults(tmp_path):
    plan = make_plan("kept", [1], base=SMALL, vary=["habit_weeks=104"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    record = batch.town_dir(batch_dir, plan["settings"][0], 1) / "run.sqlite"
    con = sqlite3.connect(record)                            # as if this town had been made when the default was 26
    settings = json.loads(con.execute("SELECT value FROM run WHERE key = 'config'").fetchone()[0])
    settings["habit_weeks"] = 26
    con.execute("UPDATE run SET value = ? WHERE key = 'config'", (json.dumps(settings),))
    con.commit()
    con.close()
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        rows = [json.loads(dials) for (dials,) in con.execute("SELECT dials FROM settings ORDER BY setting")]
    finally:
        con.close()
    assert rows == [{"habit_weeks": 26}, {"habit_weeks": 104}]


def test_the_table_keeps_how_long_each_town_was_given(table):
    _, _, con = table
    assert con.execute("SELECT DISTINCT years, year_weeks FROM towns").fetchall() == [(4, 52)]
    assert dict(con.execute("SELECT key, value FROM batch"))["model"] == batch.model_fingerprint()


def test_a_setting_with_no_finished_town_has_no_dial_values_to_show(tmp_path):
    import shutil
    plan = make_plan("bare", [1], base=SMALL, vary=["habit_weeks=104"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    shutil.rmtree(batch.town_dir(batch_dir, plan["settings"][1], 1))
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        rows = [json.loads(dials) for (dials,) in con.execute("SELECT dials FROM settings ORDER BY setting")]
    finally:
        con.close()
    assert rows == [{"habit_weeks": 52}, {}]
