"""Stage 4 diagnostics: run a town with dials changed in the week it fills, and print the
evidence the wage trace of 13 November 2026 rests on (docs/stage4-wage-trace-2026-11-13.md).

    python wef/experiments/wage_trace.py run LABEL [--out DIR] [DIAL=VALUE ...] [--at-full DIAL=VALUE ...]
    python wef/experiments/wage_trace.py report RUN_DIR [RUN_DIR ...]

`run` steps the model exactly as `wef/run.py` does. Dials before `--at-full`
apply from the start. Dials after it are set at the end of the week the town reaches its
cap, so every week up to then is the same as an unchanged run. The folder gets the record,
the settings the town started with, a summary, and experiment.json saying what was changed
and when. It gets no dashboard or town view: build those with `python -m engine dashboard`
and `python -m engine town` if wanted.

`report` reads a run's record and changes nothing.

This file is not part of the model. Nothing in engine/ imports it and a run's code
fingerprint does not cover it.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.config import _set, load_config, validate   # noqa: E402
from engine.recorder import Recorder                     # noqa: E402
from engine.runner import summarise                      # noqa: E402
from engine.town import Town                             # noqa: E402

BASE_NEEDS = ("food", "housing", "appliances", "entertainment", "transport")


def _parse(item: str):
    if "=" not in item:
        raise ValueError(f"a change must be dial=value: {item}")
    key, raw = item.split("=", 1)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    return key.strip(), value


def run_town(label: str, overrides, at_full, out_root) -> pathlib.Path:
    """Run one town into out_root/label and return the folder. `overrides` apply from the
    start, `at_full` from the end of the week the town fills."""
    overrides = list(overrides)
    changes = [_parse(item) for item in at_full]
    cfg = load_config(None, overrides)
    trial = load_config(None, overrides)             # refuse a bad late change before anything runs
    for key, value in changes:
        _set(trial, key, value)
    validate(trial)
    run_dir = pathlib.Path(out_root) / label
    if run_dir.exists():
        raise FileExistsError(f"{run_dir} is already there; pick another label")
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2), encoding="utf-8")
    (run_dir / "experiment.json").write_text(
        json.dumps({"from_start": overrides, "at_full": [list(c) for c in changes]}), encoding="utf-8")
    rec = Recorder(run_dir / "run.sqlite", cfg, run_id=run_dir.name)
    town = Town(cfg, rec)
    changed = False
    for _ in range(cfg.weeks):
        town.step()
        if changes and not changed and town.cap_week is not None:
            for key, value in changes:
                _set(cfg, key, value)
            validate(cfg)
            changed = True
        if town.failed_week is not None and cfg.stop_on_failure:
            break
    outcome = "failed" if town.failed_week is not None else "survived"
    summary = summarise(town, outcome)
    rec.finish(outcome, summary)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return run_dir


def evidence(run_dir) -> dict:
    """The numbers the wage trace reads, from the week the town filled to the end."""
    path = pathlib.Path(run_dir) / "run.sqlite"
    if not path.is_file():
        raise FileNotFoundError(f"no run record at {path}")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        full = con.execute("select min(week) from events where kind='town_full'").fetchone()[0]
        if full is None:
            raise ValueError(f"the town in {run_dir} never filled, so there is nothing after filling to read")
        last = con.execute("select max(week) from series").fetchone()[0]
        meta = dict(con.execute("select key, value from run"))
        cfg = json.loads(meta["config"]) if meta.get("config") else {}
        queue_above = cfg.get("wage_cut_unemployment", 0.05)

        def town(metric):
            return dict(con.execute(
                "select week, value from series where scope='town' and metric=?", (metric,)))

        wage, out, vac, staff = town("wage"), town("jobless_rate"), town("vacancies"), town("staff")
        homes, empty = town("homes"), town("homes_vacant")
        weeks = range(full, last + 1)
        staff_of = {(w, f): s for w, f, s in con.execute("select week, firm, staff from firm_snap")}
        count = {"unfilled": 0, "queue": 0}
        moved = {"unfilled": 0.0, "queue": 0.0}
        for w, f, new, data in con.execute(
                "select week, firm, amount, data from events where kind='wage_change' and week>=? "
                "order by id", (full,)):
            d = json.loads(data)
            reason = d["reason"]
            # the firm's share of all staff the week before, times the change in its wage
            share = ((staff_of.get((w - 1, f)) or staff_of.get((w, f)) or 0)
                     / (staff.get(w - 1) or staff.get(w) or 1))
            count[reason] = count.get(reason, 0) + 1
            moved[reason] = moved.get(reason, 0.0) + share * (new - d["old"])
        need_of = dict(con.execute("select firm, need from firm_static"))
        built = sum(1 for f, in con.execute(
            "select firm from events where kind='unit_built' and week>=?", (full,))
            if need_of.get(f) == "housing")
        people: dict[str, float] = {}
        for f, s, e in con.execute("select firm, staff, execs from firm_snap where week>=?", (full,)):
            kind = need_of[f] if need_of[f] in BASE_NEEDS else "invented"
            people[kind] = people.get(kind, 0.0) + ((s or 0) + (e or 0) + 1) / len(weeks)
    finally:
        con.close()
    change = wage[last] - wage[full]
    return {
        "full_week": full,
        "last_week": last,
        "weeks_per_year": cfg.get("weeks_per_year", 52),
        "weeks_after_full": len(weeks),
        "wage_at_full": wage[full],
        "wage_at_end": wage[last],
        "lowest_wage": min(wage[w] for w in weeks),
        "highest_wage": max(wage[w] for w in weeks),
        "weeks_with_unfilled_jobs": sum(1 for w in weeks if vac[w] > 0),
        "weeks_with_a_queue": sum(1 for w in weeks if out[w] > queue_above),
        "queue_above": queue_above,
        "average_out_of_work": sum(out[w] for w in weeks) / len(weeks),
        "wage_rises": count["unfilled"],
        "wage_cuts": count["queue"],
        "rises_moved_the_average": moved["unfilled"],
        "cuts_moved_the_average": moved["queue"],
        "moves_between_firms": change - moved["unfilled"] - moved["queue"],
        "homes_at_full": homes[full],
        "most_homes": max(homes[w] for w in weeks),
        "homes_built_after_full": built,
        "most_empty_homes": max(empty[w] for w in weeks),
        "people_at_work": people,
    }


def report(label: str, run_dir) -> str:
    e = evidence(run_dir)
    year = e["weeks_per_year"]
    n = e["weeks_after_full"]

    def dollars(cents: float) -> str:
        return f"${cents / 100:,.0f}"

    def signed(cents: float) -> str:
        return f"{'+' if cents >= 0 else '-'}${abs(cents) / 100:,.0f}"

    at_work = ", ".join(f"{kind} {e['people_at_work'][kind]:.0f}"
                        for kind in BASE_NEEDS + ("invented",) if kind in e["people_at_work"])
    lines = [
        f"{label}: full in year {e['full_week'] / year:.1f}, ended in year {e['last_week'] / year:.1f}",
        f"  staff wage {dollars(e['wage_at_full'])} when it filled, {dollars(e['wage_at_end'])} at the end "
        f"({(e['wage_at_end'] / e['wage_at_full'] - 1) * 100:+.1f}%); lowest {dollars(e['lowest_wage'])}, "
        f"highest {dollars(e['highest_wage'])}",
        f"  weeks with unfilled jobs {e['weeks_with_unfilled_jobs'] / n * 100:.0f}%; weeks with more than "
        f"{e['queue_above'] * 100:.0f}% out of work {e['weeks_with_a_queue'] / n * 100:.0f}%; "
        f"out of work on average {e['average_out_of_work'] * 100:.1f}%",
        f"  wage rises {e['wage_rises']} (moved the average {signed(e['rises_moved_the_average'])}); "
        f"wage cuts {e['wage_cuts']} (moved it {signed(e['cuts_moved_the_average'])}); "
        f"people moving between firms, firms opening and closing {signed(e['moves_between_firms'])}",
        f"  homes: {e['homes_at_full']:.0f} when it filled, {e['most_homes']:.0f} at most, "
        f"{e['homes_built_after_full']} built after it filled, {e['most_empty_homes']:.0f} empty at most",
        f"  people at work on average after it filled: {at_work}, "
        f"all {sum(e['people_at_work'].values()):.0f}",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    command, rest = args[0], args[1:]
    if command == "report":
        if not rest:
            print("wage_trace: report needs at least one run folder", file=sys.stderr)
            return 2
        for item in rest:
            try:
                print(report(pathlib.Path(item).name, item))
            except (FileNotFoundError, ValueError) as err:
                print(f"wage_trace: {err}", file=sys.stderr)
                return 2
        return 0
    if command == "run":
        if not rest:
            print("wage_trace: run needs a label", file=sys.stderr)
            return 2
        label, rest = rest[0], rest[1:]
        out_root = "runs"
        at_full: list[str] = []
        if "--at-full" in rest:
            i = rest.index("--at-full")
            rest, at_full = rest[:i], rest[i + 1:]
        if "--out" in rest:
            i = rest.index("--out")
            if i + 1 >= len(rest):
                print("wage_trace: --out needs a folder", file=sys.stderr)
                return 2
            out_root = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        try:
            run_dir = run_town(label, rest, at_full, out_root)
        except KeyError as err:
            print(f"wage_trace: bad setting: {err.args[0]}", file=sys.stderr)
            return 2
        except (ValueError, FileExistsError) as err:
            print(f"wage_trace: {err}", file=sys.stderr)
            return 2
        print(f"written to {run_dir}")
        try:
            print(report(label, run_dir))
        except ValueError as err:                    # a town that never filled still ran
            print(f"wage_trace: {err}")
        return 0
    print(f"wage_trace: unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
