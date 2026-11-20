"""The command line.

A town belongs to a world, and is run from that world's folder: `wef/run.py` and
`rtr/run.py` for one town, `batch.py` beside each for many. Those scripts call `world_main`
here, which takes the world's own settings and keeps its runs in its folder.

`python -m engine` alone only reads what a run left: batch-report | dashboard | town | compare | info."""

from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys

from .config import WORLD_NAMES, load_config
from .runner import info, run

SCRIPTS = {"run": "run.py", "batch": "batch.py"}


def world_main(world: str, home, command: str, argv) -> int:
    """`run` or `batch` for one world, from its folder `home`."""
    return main([command, *argv], world=world, home=home)


def _say(world, text: str) -> None:
    print(f"{world or 'engine'}: {text}", file=sys.stderr)


def _other(world: str) -> str:
    return "rtr" if world == "wef" else "wef"


def _settings(world, home, args, sets):
    """The settings file and the overrides for a town of this world: the world's own
    settings.json unless they gave a file of their own. Raises ValueError if they ask for
    the other world: the world is the folder a town is run from."""
    elsewhere = (f"this folder runs the {WORLD_NAMES[world]}; "
                 f"the {WORLD_NAMES[_other(world)]} is run with {_other(world)}/{SCRIPTS[args.command]}")
    for item in sets:
        if item.split("=", 1)[0].strip() == "world":
            raise ValueError(elsewhere)
    config = args.config
    if config is None and home is not None:
        return str(pathlib.Path(home) / "settings.json"), []     # it says which world it is
    if config is not None:
        with open(config, encoding="utf-8") as fh:
            named = json.load(fh).get("world")
        if named is not None and named != world:
            raise ValueError(elsewhere)
    return config, [f"world={world}"]


def main(argv=None, world: str | None = None, home=None) -> int:
    parser = argparse.ArgumentParser(
        prog=SCRIPTS.get((argv or sys.argv[1:] or [""])[0], "engine") if world else "engine",
        description="One town economy, run as either of two worlds: wef/ (everything is rented) "
                    "and rtr/ (people may rent or own, build and let).")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="run a town and write its record (from a world's folder: run.py)")
    p.add_argument("--seed", type=int, help="random seed (default 1)")
    p.add_argument("--years", type=int, help="how long to run (default 60)")
    p.add_argument("--config", help="a JSON settings file of your own, in place of the world's settings.json")
    p.add_argument("--set", action="append", default=[], metavar="DIAL=VALUE",
                   help="override one dial; repeatable; need dials are needs.<name>.<field>")
    p.add_argument("--out", help="folder for run folders (default: runs, in the world's folder)")
    p.add_argument("--label", default="", help="a word added to the run folder's name")
    p.add_argument("--quiet", action="store_true")

    p = sub.add_parser("batch", help="run many towns: every setting on every seed (from a world's folder: batch.py)")
    p.add_argument("name", help="the batch's name, which is its folder")
    p.add_argument("--seeds", default="1-30", help="seeds, such as 1-30 or 1,2,5-8 (default 1-30)")
    p.add_argument("--set", action="append", default=[], metavar="DIAL=VALUE",
                   help="a dial of the base, the setting every other is compared with; repeatable")
    p.add_argument("--vary", action="append", default=[], metavar="DIAL=A,B,C",
                   help="one more setting for each value, changing that one dial from the base; repeatable")
    p.add_argument("--config", help="a JSON settings file of your own for the base, in place of the world's settings.json")
    p.add_argument("--jobs", type=int, help="towns to run at once (default: every processor core but two)")
    p.add_argument("--out", help="folder for batch folders (default: batches, in the world's folder)")
    p.add_argument("--full", action="store_true",
                   help="record every person every week, as a single run does (default: once a quarter)")
    p.add_argument("--quiet", action="store_true")

    p = sub.add_parser("batch-report", help="rebuild the table and the page of a batch from its towns")
    p.add_argument("batch_dir")

    p = sub.add_parser("dashboard", help="rebuild the dashboard for a run")
    p.add_argument("run_dir")

    p = sub.add_parser("town", help="rebuild the town view for a run: the map, with people moving")
    p.add_argument("run_dir")

    p = sub.add_parser("compare", help="the WEF world and the RTR world on the same seeds, side by side")
    p.add_argument("wef_batch", help="a batch of the WEF world")
    p.add_argument("rtr_batch", help="a batch of the RTR world, on the same seeds")
    p.add_argument("--out", help="the folder for compare.html (default: the RTR batch's folder)")

    p = sub.add_parser("info", help="a few lines about a run")
    p.add_argument("run_dir")

    args = parser.parse_args(argv)
    if args.command in SCRIPTS:
        if world is None:
            script = SCRIPTS[args.command]
            _say(None, f"a town belongs to a world, and is run from that world's folder: "
                       f"wef/{script} for the WEF world, rtr/{script} for the RTR world")
            if args.command == "run":
                raise SystemExit(2)
            return 2
        if args.out is None:
            folder = "runs" if args.command == "run" else "batches"
            args.out = str(pathlib.Path(home) / folder) if home is not None else folder
    if args.command == "run":
        overrides = list(args.set)
        if args.seed is not None:
            overrides.append(f"seed={args.seed}")
        if args.years is not None:
            overrides.append(f"years={args.years}")
        try:
            config, first = _settings(world, home, args, args.set)
            cfg = load_config(config, first + overrides)
        except (KeyError, ValueError) as err:
            _say(world, f"bad setting: {err.args[0]}")
            raise SystemExit(2)
        run(cfg, out_root=args.out, quiet=args.quiet, label=args.label)
        return 0
    if args.command in ("batch", "batch-report"):
        return _batch(args, world, home)
    if args.command == "dashboard":
        from .dashboard import build_dashboard
        print(build_dashboard(pathlib.Path(args.run_dir)))
        return 0
    if args.command == "town":
        from .townview import build_town_view
        try:
            path = build_town_view(pathlib.Path(args.run_dir))
        except FileNotFoundError as err:
            _say(world, str(err))
            return 2
        except sqlite3.DatabaseError as err:
            _say(world, f"{pathlib.Path(args.run_dir) / 'run.sqlite'} is not a run record ({err})")
            return 2
        if path is None:
            _say(world, "this run has no map, so there is no town to draw")
            return 1
        print(path)
        return 0
    if args.command == "compare":
        from .comparepage import CompareError, build_compare_page
        try:
            print(build_compare_page(args.wef_batch, args.rtr_batch, out_dir=args.out))
        except (CompareError, FileNotFoundError) as err:
            _say(None, str(err))
            return 2
        return 0
    print(info(args.run_dir))
    return 0


def _batch(args, world=None, home=None) -> int:
    """Run a batch, or only rebuild what it leaves: the table, then the page. Prints where
    the page is. 2 for a batch that cannot be planned or carried on, 1 when a town could not
    be run, 130 when it was stopped from the keyboard. In the last two the table and the page
    are still built for the towns that finished."""
    from .batch import BatchError, Stopped, TownsFailed, collect, make_plan, parse_seeds, run_batch
    from .batchpage import build_batch_page
    code = 0
    try:
        if args.command == "batch":
            try:
                config, first = _settings(world, home, args, args.set + args.vary)
            except ValueError as err:
                raise BatchError(err.args[0])
            own = [pathlib.Path(config).name] if config is not None and args.config is None else []
            plan = make_plan(args.name, parse_seeds(args.seeds), base=first + args.set, vary=args.vary,
                             config=config, full=args.full, unnamed=own + first)
            batch_dir = pathlib.Path(args.out) / plan["name"]
            try:
                run_batch(plan, out_root=args.out, jobs=args.jobs, quiet=args.quiet)
            except (TownsFailed, Stopped) as err:    # the others finished: still build their page
                _say(world, str(err))
                code = 130 if isinstance(err, Stopped) else 1
        else:
            batch_dir = pathlib.Path(args.batch_dir)
        collect(batch_dir)
    except BatchError as err:
        _say(world, str(err))
        return 2
    print(build_batch_page(batch_dir))
    return code


if __name__ == "__main__":
    sys.exit(main())
