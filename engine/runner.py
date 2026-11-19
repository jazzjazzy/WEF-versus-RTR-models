"""One run from start to finish: a folder holding the record, the settings and a summary."""

from __future__ import annotations

import datetime
import json
import pathlib
import sqlite3
import sys
import time

from .config import WORLD_NAMES, WORLD_SAYS
from .metrics import SCOPES, weekly_series
from .recorder import Recorder
from .town import Town


def summarise(town, outcome: str) -> dict:
    """The state of the town when the run ended. For a failed run this is the week it failed."""
    cfg = town.cfg
    by = {(scope, metric): value for scope, metric, value in weekly_series(town)}
    base = [s for s in town.needs.values() if not s.invented]
    ratio = {s.name: round(by[("town", f"price_{s.name}")] / s.initial_price, 4)
             for s in base if s.initial_price}
    firms: dict[str, int] = {}
    for f in town.alive_firms:
        firms[f.need] = firms.get(f.need, 0) + 1
    per_year = cfg.weeks_per_year
    summary = {
        "outcome": outcome,
        "world": cfg.world,
        "price_rule": cfg.price_rule,
        "seed": cfg.seed,
        "weeks": town.week,
        "years": round(town.week / per_year, 2),
        "failed_week": town.failed_week,
        "failed_year": round(town.failed_week / per_year, 2) if town.failed_week else None,
        "full_week": town.cap_week,
        "full_year": round(town.cap_week / per_year, 2) if town.cap_week else None,
        "population": town.population,
        "class_counts": {s: int(by[(s, "n")]) for s in SCOPES},
        "unhappy": {s: round(by[(s, "unhappy")], 4) for s in SCOPES},
        "security": {s: round(by[(s, "security")], 4) for s in SCOPES},
        "shares_pct": {s: round(by[(s, "shares_pct")], 4) for s in SCOPES},
        "cash_total": {s: int(by[(s, "cash_total")]) for s in SCOPES},
        "gini_shares": round(by[("town", "gini_shares")], 4),
        "top10_shares": round(by[("town", "top10_shares")], 4),
        "gini_cash": round(by[("town", "gini_cash")], 4),
        "top10_cash": round(by[("town", "top10_cash")], 4),
        "wage": int(by[("town", "wage")]),
        "basket": int(by[("town", "basket")]),
        "affordability": round(by[("town", "affordability")], 4),
        "price_ratio": ratio,
        "biggest_price_rise": max(ratio, key=ratio.get) if ratio else None,
        "jobless_rate": round(by[("town", "jobless_rate")], 4),
        "destitute": int(by[("town", "destitute")]),
        "homeless": int(by[("all", "homeless")]),
        "firms_alive": firms,
        "firms_ever": len(town.firms),
        "needs_invented": int(by[("town", "needs_invented")]),
        "money": town.money_in_town(),
        "flows_in": dict(town.ledger.total_in),
        "flows_out": dict(town.ledger.total_out),
        "writeoffs": town.bank.writeoffs_total,
        "endowment": town.endowment,
        "events": town.rec.event_count,
    }
    if cfg.rtr:                                  # the Right to Repair world: who owns
        summary["homes_owned"] = int(by[("town", "homes_owned")])
        summary["sets_owned"] = int(by[("town", "sets_owned")])
        summary["home_loans"] = int(by[("town", "home_loans")])
        summary["foreclosures"] = town.foreclosures_total
        for name in ("homes_bought", "homes_let_private", "small_landlords"):    # stage 1b
            summary[name] = int(by[("town", name)])
    return summary


def _new_run_dir(out_root, name: str) -> pathlib.Path:
    root = pathlib.Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    run_dir, n = root / name, 2
    while run_dir.exists():
        run_dir = root / f"{name}-{n}"
        n += 1
    run_dir.mkdir()
    return run_dir


def run_in(cfg, run_dir, quiet: bool = True, pages: bool = True) -> dict:
    """Run the town into a folder that is already there and holds no record. Writes the
    settings, the record and the summary, builds the two pages unless told not to, and
    returns the summary. This is all of a run except naming its folder: a batch makes each
    of its towns this way."""
    run_dir = pathlib.Path(run_dir)
    if (run_dir / "run.sqlite").exists():
        raise FileExistsError(f"{run_dir} already holds a record")
    (run_dir / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2), encoding="utf-8")
    rec = Recorder(run_dir / "run.sqlite", cfg, run_id=run_dir.name)
    town = Town(cfg, rec)
    started = time.time()
    if not quiet:
        print(f"The {WORLD_NAMES[cfg.world]} ({WORLD_SAYS[cfg.world]}). "
              f"Run {run_dir.name}: seed {cfg.seed}, up to {cfg.years} years, price rule {cfg.price_rule}")
        print(" year  people  unhappy  jobless   wage  basket  firms")
    for _ in range(cfg.weeks):
        town.step()
        if not quiet and town.week % cfg.weeks_per_year == 0:
            by = {(s, m): v for s, m, v in weekly_series(town) if s == "town"}
            print(f"{town.week // cfg.weeks_per_year:5d} {town.population:7d} "
                  f"{100 * by[('town', 'unhappy_share')]:7.1f}% {100 * by[('town', 'jobless_rate')]:7.1f}% "
                  f"{by[('town', 'wage')] / 100:6.0f} {by[('town', 'basket')] / 100:7.0f} "
                  f"{int(by[('town', 'firms')]):6d}", flush=True)
        if town.failed_week is not None and cfg.stop_on_failure:
            break
    outcome = "failed" if town.failed_week is not None else "survived"
    summary = summarise(town, outcome)
    rec.finish(outcome, summary)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if pages:
        _build_pages(run_dir)
    if not quiet:
        when = (f"FAILED in year {summary['failed_year']}" if outcome == "failed"
                else f"survived {summary['years']} years")
        print(f"{when}; {summary['events']} events; {time.time() - started:.0f}s; {run_dir}")
    return summary


def _build_pages(run_dir: pathlib.Path) -> None:
    """The town view and the dashboard for a finished run."""
    try:
        from . import townview
    except ImportError:
        townview = None
    if townview is not None:                     # before the dashboard, which links to it
        try:
            townview.build_town_view(run_dir)
        except Exception as err:                 # a fault in one view must not cost the run the other
            print(f"the town view could not be built ({type(err).__name__}: {err})",
                  file=sys.stderr)
    try:
        from .dashboard import build_dashboard
    except ImportError:
        build_dashboard = None
    if build_dashboard is not None:
        build_dashboard(run_dir)


def run(cfg, out_root="runs", quiet: bool = False, label: str = "") -> pathlib.Path:
    """Run the town and write its folder. Returns the folder."""
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{stamp}-seed{cfg.seed}" + (f"-{label}" if label else "")
    run_dir = _new_run_dir(out_root, name)
    run_in(cfg, run_dir, quiet=quiet)
    return run_dir


def info(run_dir) -> str:
    """A few lines about a run, finished or not."""
    run_dir = pathlib.Path(run_dir)
    con = sqlite3.connect(run_dir / "run.sqlite")
    try:
        meta = dict(con.execute("SELECT key, value FROM run").fetchall())
        last = con.execute("SELECT MAX(week) FROM series").fetchone()[0] or 0
    finally:
        con.close()
    lines = [f"run {meta.get('run_id') or run_dir.name}",
             f"seed {meta.get('seed')}, code {meta.get('code_fingerprint')}, started {meta.get('started')}"]
    if "outcome" not in meta:
        lines.append(f"unfinished: the record stops at week {last}")
        return "\n".join(lines)
    s = json.loads(meta["summary"])
    if s["outcome"] == "failed":
        lines.append(f"failed in week {s['failed_week']} (year {s['failed_year']}): "
                     f"{100 * s['unhappy']['all']:.0f}% unhappy")
    else:
        lines.append(f"survived {s['years']} years: {100 * s['unhappy']['all']:.0f}% unhappy at the end")
    lines.append(f"people {s['population']}: owners {s['class_counts']['owner']}, "
                 f"working {s['class_counts']['working']}, out of work {s['class_counts']['out']}")
    lines.append(f"top tenth hold {100 * s['top10_shares']:.0f}% of shares; "
                 f"basket is {100 * s['affordability']:.0f}% of the staff wage")
    lines.append(f"record fingerprint {meta.get('fingerprint', '')[:16]}, {meta.get('events')} events")
    return "\n".join(lines)
