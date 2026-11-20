"""Many towns at once (Jason, 12/11/2026: "Many runs per setting. One run is one town's luck.").

A batch is a list of seeds and one or more settings. The first setting is the base: the
model as written, plus any dials the batch sets. Each varied dial adds one setting for each
of its values, changing that one dial from the base. Every setting is run on every seed.

Each town is an ordinary run in its own folder, made exactly as `run.py` in a world's folder
makes it, so it has the same record fingerprint as the same town run alone. What happened
to every town is then gathered into one table, `batch.sqlite`, built only from the towns'
records. The page is built from that table by batchpage.py.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import multiprocessing
import os
import pathlib
import re
import shutil
import signal
import sqlite3
import time
import traceback
from concurrent.futures.process import BrokenProcessPool

from .config import Config, load_config
from .recorder import code_fingerprint
from .runner import run_in

# (C) A batch town records every person and firm once a quarter. Every event and every weekly
# measure is still recorded, and the record fingerprint, which covers those, is the same.
LIGHT = ("snapshot_every=13",)
MOST_SEEDS = 100_000

# The files that only read records or drive runs. Everything else in the package decides what
# a town does or what its record holds, and is "the model" for the purpose of keeping a batch
# to one version of it. A fix to a page must not stop a batch being carried on.
NOT_MODEL = frozenset({"batch.py", "batchpage.py", "dashboard.py", "townview.py", "townpage.py", "__main__.py"})


class BatchError(ValueError):
    """A batch that cannot be planned or run as asked. The message is for whoever asked."""


class TownsFailed(BatchError):
    """The batch ran, but some of its towns could not be run. The others are finished."""


class Stopped(BatchError):
    """The batch was stopped from the keyboard. The towns that finished are kept."""


def model_fingerprint(folder=None) -> str:
    """A short hash of the model's own files: the package without the pages and the tools
    that read records. Two towns belong in one batch only if this is the same for both."""
    here = pathlib.Path(folder) if folder is not None else pathlib.Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(here.glob("*.py")):
        if path.name not in NOT_MODEL:
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _open(path) -> sqlite3.Connection:
    """Open a record or a table to read only. The path may hold any character."""
    return sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True)


# --- the plan ---------------------------------------------------------------------------------------
def parse_seeds(text: str) -> list[int]:
    """`1-5,9` is seeds 1 to 5 and 9. Sorted, with no repeats."""
    seeds: set[int] = set()
    for part in str(text).split(","):
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not match:
            raise BatchError(f"seeds are numbers and ranges, such as 1-30 or 1,2,5-8, not {text!r}")
        first, last = int(match.group(1)), int(match.group(2) or match.group(1))
        if last < first:
            raise BatchError(f"a range of seeds runs upwards: {part.strip()}")
        if last - first + 1 > MOST_SEEDS:
            raise BatchError(f"more than {MOST_SEEDS:,} seeds: {text!r}")
        seeds.update(range(first, last + 1))
        if len(seeds) > MOST_SEEDS:
            raise BatchError(f"more than {MOST_SEEDS:,} seeds: {text!r}")
    return sorted(seeds)


def slug(name: str) -> str:
    """A folder name made from a setting's name. Never empty and never only dots."""
    safe = re.sub(r"[^A-Za-z0-9._=-]", "_", name)
    return safe if safe.strip(".") else "_" + safe


def _settings(config, overrides: list[str]) -> dict:
    """The full settings a town would run with. A mistyped dial or value stops here."""
    try:
        return load_config(config, overrides).to_dict()
    except (KeyError, ValueError) as err:
        raise BatchError(f"bad setting: {err.args[0]}") from None
    except OSError as err:
        raise BatchError(f"the settings file {config} cannot be read: {err}") from None


def town_overrides(plan: dict, setting: dict, seed: int) -> list[str]:
    """The dials one town of the batch is run with, in the order they are applied."""
    return plan["record"] + plan["base"] + setting["overrides"] + [f"seed={seed}"]


def _resolved(plan: dict, setting: dict, config) -> dict:
    """What a setting comes to once every dial is filled in, whatever it is called and however
    its values are spelt. The seed is left out: it is the town's, not the setting's."""
    full = _settings(config, town_overrides(plan, setting, 0))
    full.pop("seed", None)
    return full


def make_plan(name: str, seeds, base=(), vary=(), config: str | None = None, full: bool = False,
              unnamed=()) -> dict:
    """What a batch will run: its seeds and its settings, checked before any town is run.

    `base` is a list of `dial=value`. Each item of `vary` is `dial=a,b,c`. A varied value
    that leaves the settings as an earlier setting has them is not a setting of its own.
    `unnamed`: parts of the base that are not named in what the base is called (a world's
    own settings file, and the world itself: the batch's folder and page already say)."""
    if not name or slug(name) != name:
        raise BatchError(f"a batch's name is its folder: letters, digits and . _ = - only, not {name!r}")
    seeds = sorted({int(seed) for seed in seeds})
    if not seeds:
        raise BatchError("a batch needs at least one seed")
    base, vary = [str(item) for item in base], [str(item) for item in vary]
    for item in base + vary:
        if item.split("=", 1)[0].strip() == "seed":
            raise BatchError(f"seeds are given as the batch's seeds, not as a dial: {item}")
    record = [] if full else list(LIGHT)
    plan = {"name": name, "seeds": seeds, "base": base, "config": config, "record": record,
            "code": code_fingerprint(), "model": model_fingerprint(), "settings": []}
    plan["world"] = _resolved(plan, {"overrides": []}, config).get("world", "wef")   # which world its towns are in

    def checked(setting: dict) -> dict:
        made = _resolved(plan, setting, config)
        if not made.get("stop_on_failure", True):
            # The page reads a town's last week as the week it failed.
            raise BatchError("a batch stops each town when it fails: stop_on_failure=false is not taken, "
                             "because a town's last week would then not be the week it failed")
        return made

    label = [part for part in ([pathlib.Path(config).name] if config else []) + base if part not in unnamed]
    first = {"name": ", ".join(label) if label else "as written", "slug": "base", "overrides": []}
    settings, seen = [first], [checked(first)]
    for item in vary:
        dial, _, values = item.partition("=")
        dial, values = dial.strip(), [value.strip() for value in values.split(",") if value.strip()]
        if not values:
            raise BatchError(f"a varied dial is written dial=value,value and {item!r} has no values")
        for value in values:
            setting = {"name": f"{dial}={value}", "slug": slug(f"{dial}={value}"), "overrides": [f"{dial}={value}"]}
            made = checked(setting)
            if made in seen:                         # what the base, or an earlier value, already is
                continue
            seen.append(made)
            settings.append(setting)
    taken: dict[str, str] = {}
    for setting in settings:
        if setting["slug"] in taken:
            raise BatchError(f"the settings {taken[setting['slug']]!r} and {setting['name']!r} would share "
                             f"the folder {setting['slug']}")
        taken[setting["slug"]] = setting["name"]
    plan["settings"] = settings
    return plan


# --- running it -------------------------------------------------------------------------------------
PLAN_FILE = "batch.json"
SETTINGS_COPY = "base-settings.json"     # the batch's own copy of the settings file it was started with


def town_dir(batch_dir, setting: dict, seed: int) -> pathlib.Path:
    """Where one town of a batch lives."""
    return pathlib.Path(batch_dir) / "towns" / setting["slug"] / f"seed-{seed:04d}"


def finished(run_dir) -> bool:
    """Does this folder hold the record of a run that reached its end?"""
    record = pathlib.Path(run_dir) / "run.sqlite"
    if not record.is_file():
        return False
    try:
        con = _open(record)
        try:
            return con.execute("SELECT 1 FROM run WHERE key = 'outcome'").fetchone() is not None
        finally:
            con.close()
    except sqlite3.DatabaseError:
        return False


def default_jobs() -> int:
    """How many towns to run at once: every processor core but two, and at least one."""
    return max(1, (os.cpu_count() or 1) - 2)


def _read(path: str) -> str:
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as err:
        raise BatchError(f"the settings file {path} cannot be read: {err}") from None


def _join(batch_dir: pathlib.Path, plan: dict) -> dict:
    """Start the batch's folder, or carry on a batch already there. A batch is carried on
    only by the same model, with the same base and the same recording; its seeds and its
    settings can grow. Settings are compared by what they come to, not by how they are
    spelt. Returns the plan as it now stands, and writes it."""
    stored = batch_dir / PLAN_FILE
    copy = batch_dir / SETTINGS_COPY
    text = None if plan["config"] is None else _read(plan["config"])
    if stored.exists():
        old = json.loads(stored.read_text(encoding="utf-8"))
        name = old["name"]
        if "model" in old:
            if old["model"] != plan["model"]:
                raise BatchError(
                    f"batch {name} was started with the model's code at {old['model']} and it is now "
                    f"{plan['model']}. Towns made by different models do not belong in one batch: give this "
                    "one another name.")
        elif old["code"] != plan["code"]:            # planned before batches carried the model's own stamp
            raise BatchError(
                f"batch {name} was planned with code {old['code']}, before batches were stamped with the model's "
                f"own code. This is code {plan['code']} and it cannot be told whether the model is the same: "
                "give this one another name.")
        if old["record"] != plan["record"]:
            raise BatchError(f"batch {name} was started with another record of each town "
                             f"({', '.join(old['record']) or 'the full weekly record'}). Give this one another name.")
        old_config = str(copy) if copy.exists() else None
        have = [_resolved(old, setting, old_config) for setting in old["settings"]]
        if have[0] != _resolved(plan, plan["settings"][0], plan["config"]):
            raise BatchError(f"batch {name} was started with another base: its dials or its settings file come "
                             "to something else. Give this one another name.")
        names = {setting["name"] for setting in old["settings"]}
        slugs = {setting["slug"] for setting in old["settings"]}
        settings = list(old["settings"])
        for setting in plan["settings"][1:]:
            if setting["name"] in names:
                continue
            made = _resolved(plan, setting, plan["config"])
            if made in have:                         # already there under another spelling
                continue
            if setting["slug"] in slugs:
                raise BatchError(f"the setting {setting['name']!r} would share a folder with one already in "
                                 f"batch {name}")
            settings.append(setting)
            have.append(made)
            names.add(setting["name"])
            slugs.add(setting["slug"])
        plan = {**old, "model": plan["model"], "seeds": sorted(set(old["seeds"]) | set(plan["seeds"])),
                "settings": settings}
    else:
        if batch_dir.exists() and any(batch_dir.iterdir()):
            raise BatchError(f"{batch_dir} is there already and is not a batch")
        batch_dir.mkdir(parents=True, exist_ok=True)
        if text is not None:
            copy.write_text(text, encoding="utf-8")
    stored.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def run_town(task: tuple) -> dict:
    """Run one town of a batch into its folder. `task` is (folder, settings file, dials,
    setting name, seed, the model stamp of the plan). A folder left by a run that was stopped
    is emptied first. A town is not run by a model other than the plan's."""
    folder, config, overrides, name, seed, model = task
    folder = pathlib.Path(folder)
    started = time.time()
    if model_fingerprint() != model:
        return {"setting": name, "seed": seed,
                "error": "the model's code has changed since this batch was planned, so the town was not run"}
    try:
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        summary = run_in(load_config(config, overrides), folder, quiet=True, pages=False)
    except Exception as err:                         # one town must not cost the batch the others
        note = folder / "error.txt"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            note.write_text(traceback.format_exc(), encoding="utf-8")
            where = f" (the whole error is in {note})"
        except OSError:
            where = ""
        return {"setting": name, "seed": seed, "error": f"{type(err).__name__}: {err}{where}"}
    return {"setting": name, "seed": seed, "outcome": summary["outcome"], "years": summary["years"],
            "failed_year": summary["failed_year"], "seconds": time.time() - started}


def _ended(row: dict) -> str:
    if "error" in row:
        return f"could not be run: {row['error']}"
    if row["outcome"] == "failed":
        return f"failed in year {row['failed_year']} ({row['seconds']:.0f} s)"
    return (f"still standing after {row['years']:g} {'year' if row['years'] == 1 else 'years'} "
            f"({row['seconds']:.0f} s)")


def _ignore_interrupt() -> None:
    """In a town's own process: leave Ctrl-C to the batch, which lets the town finish."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _outcome(future, task: tuple) -> dict:
    """What a town's process handed back, or what became of it."""
    try:
        return future.result()
    except BrokenProcessPool:
        return {"setting": task[3], "seed": task[4], "error": "its process died before it finished"}
    except Exception as err:
        return {"setting": task[3], "seed": task[4], "error": f"{type(err).__name__}: {err}"}


def run_batch(plan: dict, out_root="batches", jobs: int | None = None, quiet: bool = False) -> pathlib.Path:
    """Run every town of the plan that is not already finished, `jobs` at a time, each in
    its own folder under `out_root/<name>/towns`. Returns the batch's folder.

    Ctrl-C stops it: no new town is started, the towns already running are let finish, and
    `Stopped` is raised. A second Ctrl-C drops those too. Either way every finished town is
    kept and the same call carries on from there."""
    batch_dir = pathlib.Path(out_root) / plan["name"]
    plan = _join(batch_dir, plan)
    config = str(batch_dir / SETTINGS_COPY) if plan["config"] is not None else None
    tasks = [(str(town_dir(batch_dir, setting, seed)), config, town_overrides(plan, setting, seed),
              setting["name"], seed, plan["model"])
             for setting in plan["settings"] for seed in plan["seeds"]
             if not finished(town_dir(batch_dir, setting, seed))]
    jobs = max(1, min(jobs or default_jobs(), len(tasks) or 1))
    if not quiet:
        print(f"batch {plan['name']}: " + (f"{len(tasks)} towns to run, {jobs} at a time" if tasks
                                            else "nothing left to run"), flush=True)
    failed: list[dict] = []
    reported = 0
    stopped = False

    def note(row: dict) -> None:
        nonlocal reported
        reported += 1
        if "error" in row:
            failed.append(row)
        if not quiet:
            print(f"{reported:>5}/{len(tasks)} {row['setting']}, seed {row['seed']}: {_ended(row)}", flush=True)

    unstarted = 0
    if jobs == 1:
        try:
            for task in tasks:
                note(run_town(task))
        except KeyboardInterrupt:                    # the town in flight is left unfinished and is run again next time
            stopped = True
    else:
        # Towns are handed out one at a time as a process comes free, never queued ahead, so
        # that stopping waits only for the towns in flight.
        context = multiprocessing.get_context("spawn")       # each town starts from a clean process
        queue = iter(tasks)
        running: dict = {}
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs, mp_context=context,
                                                    initializer=_ignore_interrupt) as pool:
            def hand_out() -> bool:
                """Start towns until every process is busy. False once a process has died."""
                nonlocal unstarted
                while len(running) < jobs:
                    task = next(queue, None)
                    if task is None:
                        return True
                    try:
                        running[pool.submit(run_town, task)] = task
                    except BrokenProcessPool:
                        unstarted += 1               # this one, and those still waiting, were never started
                        return False
                return True

            def take_in() -> None:
                finished_now, _ = concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in finished_now:
                    note(_outcome(future, running.pop(future)))

            try:
                try:
                    alive = hand_out()
                    while running:
                        take_in()
                        alive = alive and hand_out()
                    unstarted += sum(1 for _ in queue)       # more than none only when a process died
                except KeyboardInterrupt:
                    stopped = True
                    if not quiet:
                        print(f"stopping: no new town will be started. Letting the {len(running)} already "
                              "running finish. Ctrl-C again drops them.", flush=True)
                    while running:
                        take_in()
            except KeyboardInterrupt:                # a second time: drop the towns in flight too
                for child in multiprocessing.active_children():
                    child.terminate()
                pool.shutdown(wait=False, cancel_futures=True)
    done = reported - len(failed)
    if stopped:
        raise Stopped(f"stopped: {done} of {len(tasks)} towns finished this time. Run the same command again "
                      "to carry on.")
    if failed:
        more = f"; {unstarted} more were not started" if unstarted else ""
        raise TownsFailed(f"{len(failed)} of {len(tasks)} towns could not be run: " + "; ".join(
            f"{row['setting']}, seed {row['seed']}: {row['error']}" for row in failed)
            + more + ". Run the same command again to try them again.")
    return batch_dir


# --- the table --------------------------------------------------------------------------------------
TABLE_FILE = "batch.sqlite"
CLASSES = ("all", "owner", "working", "out")
# What is kept for every town at the end of every year it finished: (scope, metric) in its record.
MEASURES = (
    tuple((scope, metric) for scope in CLASSES for metric in ("n", "unhappy", "cash_median"))
    + tuple(("town", metric) for metric in (
        "population", "wage", "basket", "affordability", "jobless_rate", "destitute", "firms",
        "needs_invented", "top10_shares", "top10_cash", "gini_shares", "gini_cash", "homes",
        "homes_vacant", "money", "loans_firms", "loans_people"))
    + (("all", "homeless"),)
)
# The RTR world's own, kept as well (stage 3, 20/11/2026). A WEF town records none of them, so keeps none.
# `homes_lived_in_by_owner` is worked out: the homes a person owns (`homes_owned`) less those they let.
RTR_MEASURES = tuple(("town", metric) for metric in (
    "wage_offer", "homes_lived_in_by_owner", "homes_let_private", "homes_foreclosed", "sets_owned",
    "home_loans", "makers", "small_businesses"))

TABLES = """
CREATE TABLE batch (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE settings (setting INTEGER PRIMARY KEY, name TEXT, slug TEXT, overrides TEXT, dials TEXT);
CREATE TABLE towns (
    setting INTEGER, seed INTEGER, folder TEXT, outcome TEXT, weeks INTEGER, failed_week INTEGER,
    full_week INTEGER, year_weeks INTEGER, years INTEGER, fingerprint TEXT, code TEXT, events INTEGER,
    summary TEXT, PRIMARY KEY (setting, seed));
CREATE TABLE moments (setting INTEGER, seed INTEGER, name TEXT, week INTEGER, PRIMARY KEY (setting, seed, name));
CREATE TABLE yearly (
    setting INTEGER, seed INTEGER, year INTEGER, scope TEXT, metric TEXT, value REAL,
    PRIMARY KEY (setting, seed, year, scope, metric)) WITHOUT ROWID;
"""


def read_plan(batch_dir) -> dict:
    """The plan of the batch in this folder."""
    path = pathlib.Path(batch_dir) / PLAN_FILE
    if not path.is_file():
        raise BatchError(f"{batch_dir} is not a batch: it has no {PLAN_FILE}")
    return json.loads(path.read_text(encoding="utf-8"))


def _dial(cfg, key: str):
    """The value a dial has in a full set of settings. Dials are named as `--set` names them."""
    parts = key.split(".")
    if parts[0] == "needs" and len(parts) == 3:
        return getattr(cfg.need(parts[1]), parts[2])
    if parts[0] == "founding_capital" and len(parts) == 2:
        return cfg.founding_capital[parts[1]]
    return getattr(cfg, key)


def varied_dials(plan: dict) -> list[str]:
    """The dials the plan varies, in the order they were first given."""
    dials: list[str] = []
    for setting in plan["settings"]:
        for item in setting["overrides"]:
            dial = item.split("=", 1)[0]
            if dial not in dials:
                dials.append(dial)
    return dials


def _town_rows(folder: pathlib.Path) -> tuple[tuple, list, list, dict]:
    """What the table keeps of one finished town, read from its record alone: its row, its
    moments, its yearly measures, and the settings it was run with."""
    from .townview import _marks                     # the same four moments the town view marks
    con = _open(folder / "run.sqlite")
    try:
        meta = dict(con.execute("SELECT key, value FROM run").fetchall())
        summary = json.loads(meta["summary"])
        config = json.loads(meta["config"])
        year_weeks = config["weeks_per_year"]
        moments = [(mark["kind"], mark["week"]) for mark in _marks(con)]
        wanted = set(MEASURES + RTR_MEASURES)
        yearly = [(week // year_weeks, scope, metric, value) for week, scope, metric, value in con.execute(
            "SELECT week, scope, metric, value FROM series WHERE week > 0 AND week % ? = 0 "
            "ORDER BY week, scope, metric", (year_weeks,)) if (scope, metric) in wanted]
        owned = {week // year_weeks: value for week, value in con.execute(    # RTR: a home a person owns and
            "SELECT week, value FROM series WHERE scope = 'town' AND metric = 'homes_owned' "   # does not let
            "AND week > 0 AND week % ? = 0", (year_weeks,))}
        let = {week // year_weeks: value for week, value in con.execute(
            "SELECT week, value FROM series WHERE scope = 'town' AND metric = 'homes_let_private' "
            "AND week > 0 AND week % ? = 0", (year_weeks,))}
        yearly += [(year, "town", "homes_lived_in_by_owner", value - let.get(year, 0.0))
                   for year, value in sorted(owned.items())]
    finally:
        con.close()
    row = (meta["outcome"], summary["weeks"], summary["failed_week"], summary["full_week"], year_weeks,
           config["years"], meta["fingerprint"], meta.get("code_fingerprint"), int(meta["events"]), meta["summary"])
    return row, moments, yearly, config


def collect(batch_dir) -> pathlib.Path:
    """Build `batch.sqlite` afresh from the plan and the records of the finished towns.
    A town that is missing or unfinished is left out, and the table says how many towns the
    plan asks for and how many it holds. What each setting has each varied dial at is read
    from a town's own record of its settings, not worked out again by today's code."""
    batch_dir = pathlib.Path(batch_dir)
    plan = read_plan(batch_dir)
    fresh = batch_dir / (TABLE_FILE + ".tmp")
    fresh.unlink(missing_ok=True)
    con = sqlite3.connect(fresh)
    try:
        con.executescript(TABLES)
        found = 0
        dials = varied_dials(plan)
        for number, setting in enumerate(plan["settings"]):
            values: dict = {}
            for seed in plan["seeds"]:
                folder = town_dir(batch_dir, setting, seed)
                if not finished(folder):
                    continue
                row, moments, yearly, config = _town_rows(folder)
                if not values:
                    cfg = Config.from_dict(config)
                    values = {dial: _dial(cfg, dial) for dial in dials}
                where = folder.relative_to(batch_dir).as_posix()
                con.execute("INSERT INTO towns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (number, seed, where) + row)
                con.executemany("INSERT INTO moments VALUES (?, ?, ?, ?)",
                                [(number, seed, name, week) for name, week in moments])
                con.executemany("INSERT INTO yearly VALUES (?, ?, ?, ?, ?, ?)",
                                [(number, seed) + item for item in yearly])
                found += 1
            con.execute("INSERT INTO settings VALUES (?, ?, ?, ?, ?)",
                        (number, setting["name"], setting["slug"], json.dumps(setting["overrides"]),
                         json.dumps(values)))
        con.executemany("INSERT INTO batch VALUES (?, ?)", [
            ("plan", json.dumps(plan)), ("code", plan["code"]), ("model", plan.get("model", "")),
            ("world", plan.get("world", "wef")),
            ("planned", str(len(plan["settings"]) * len(plan["seeds"]))), ("finished", str(found))])
        con.commit()
    finally:
        con.close()
    table = batch_dir / TABLE_FILE
    os.replace(fresh, table)
    return table
