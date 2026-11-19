"""The record of a run: one SQLite file. Everything a later view needs is read from
here, never from the live model (Jason, 12/11/2026: record first).

NullRecorder keeps the same running fingerprint without writing a file, so tests
can prove that recording a run does not change it.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sqlite3

SCHEMA_VERSION = 3          # 2: places (spots, what stands on them, where agents live and work)
                            # 3: units carry their scale and, for what a person owns, their owner (16/11/2026)


def _dumps(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def code_fingerprint() -> str:
    """A short hash of the model's source files, so a run records exactly which code made it."""
    digest = hashlib.sha256()
    here = pathlib.Path(__file__).parent
    for path in sorted(here.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


class _Fingerprint:
    """Every event and every weekly measure, hashed in order."""

    def __init__(self) -> None:
        self._hash = hashlib.sha256()
        self.event_count = 0

    def _mix_event(self, week, kind, agent_id, firm_id, amount, qty, data_json: str) -> None:
        self.event_count += 1
        self._hash.update(f"{week}|{kind}|{agent_id}|{firm_id}|{amount}|{qty}|{data_json}\n".encode())

    def _mix_series(self, week, rows) -> None:
        self._hash.update(f"{week}|{rows!r}\n".encode())

    def fingerprint(self) -> str:
        return self._hash.hexdigest()


class NullRecorder(_Fingerprint):
    """Keeps events in a list (optionally) and writes nothing to disk."""

    def __init__(self, keep_events: bool = True) -> None:
        super().__init__()
        self.keep_events = keep_events
        self.events: list[dict] = []

    def event(self, week, kind, agent_id, firm_id, amount, qty, data) -> None:
        self._mix_event(week, kind, agent_id, firm_id, amount, qty, _dumps(data))
        if self.keep_events:
            self.events.append({"week": week, "kind": kind, "agent": agent_id, "firm": firm_id,
                                "amount": amount, "qty": qty, "data": data})

    def series(self, week, rows) -> None:
        self._mix_series(week, rows)

    def agent_static(self, agent) -> None:
        pass

    def firm_static(self, firm) -> None:
        pass

    def need(self, week, spec) -> None:
        pass

    def meta(self, key, value) -> None:
        pass

    def snapshot(self, town) -> None:
        pass

    def orders(self, week, rows) -> None:
        pass

    def flush(self) -> None:
        pass

    def finish(self, outcome, summary) -> None:
        pass


TABLES = """
CREATE TABLE run (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE needs (name TEXT PRIMARY KEY, week INTEGER, kind TEXT, invented INTEGER, spec TEXT);
CREATE TABLE events (
    id INTEGER PRIMARY KEY, week INTEGER, kind TEXT, agent INTEGER, firm INTEGER,
    amount INTEGER, qty INTEGER, data TEXT);
CREATE TABLE agent_static (
    agent INTEGER PRIMARY KEY, arrived INTEGER, origin TEXT, start_cash INTEGER,
    loss_aversion REAL, horizon REAL, growth_expect REAL, skill REAL, risk REAL, taste REAL,
    prefers_equity INTEGER);
CREATE TABLE firm_static (
    firm INTEGER PRIMARY KEY, name TEXT, need TEXT, kind TEXT, invented INTEGER,
    founded INTEGER, founder INTEGER, share_pay REAL, prefers_equity INTEGER);
CREATE TABLE agent_snap (
    week INTEGER, agent INTEGER, cash INTEGER, employer INTEGER, role TEXT, klass TEXT,
    pay INTEGER, loan INTEGER, loan_called INTEGER, shares_value INTEGER, holdings INTEGER,
    security REAL, horizon REAL, wellbeing REAL, happy INTEGER, destitute INTEGER,
    provision REAL, condition REAL, income INTEGER, wage_income INTEGER, dividends INTEGER,
    spend INTEGER, weeks_out INTEGER,
    food_firm INTEGER, home_firm INTEGER, home_unit INTEGER, home_cond REAL,
    appl_firm INTEGER, appl_unit INTEGER, appl_cond REAL, fun_firm INTEGER, other_subs TEXT,
    home_spot INTEGER, work_spot INTEGER, travel_hours REAL, rides INTEGER,
    PRIMARY KEY (week, agent)) WITHOUT ROWID;
CREATE TABLE firm_snap (
    week INTEGER, firm INTEGER, price INTEGER, wage INTEGER, customers INTEGER, unserved INTEGER,
    staff INTEGER, execs INTEGER, ceo INTEGER, vacancies INTEGER, cash INTEGER, loan INTEGER,
    revenue INTEGER, export INTEGER, wages INTEGER, goods INTEGER, interest INTEGER,
    capex INTEGER, wear INTEGER, profit INTEGER, retained INTEGER, dividend INTEGER,
    shares_out INTEGER, share_price INTEGER, target_growth REAL, shortfall INTEGER,
    upkeep_level REAL, upkeep_done REAL, units INTEGER, vacant INTEGER, avg_cond REAL,
    projects INTEGER, make_mode TEXT, made REAL, imported REAL, exported REAL,
    spot INTEGER, lots INTEGER, land_value INTEGER,
    PRIMARY KEY (week, firm)) WITHOUT ROWID;
CREATE TABLE holdings (week INTEGER, firm INTEGER, agent INTEGER, shares INTEGER);
CREATE TABLE units (
    week INTEGER, unit INTEGER, firm INTEGER, need TEXT, age INTEGER, cond REAL, occupant INTEGER,
    spot INTEGER, scale REAL, owner INTEGER);
CREATE TABLE spots (spot INTEGER PRIMARY KEY, x INTEGER, y INTEGER);
CREATE TABLE places (
    week INTEGER, spot INTEGER, kind TEXT, label TEXT, owner INTEGER, user INTEGER,
    homes INTEGER, let INTEGER, building INTEGER, rent_factor REAL, access REAL, popularity REAL,
    ground_rent INTEGER);
CREATE TABLE orders (
    week INTEGER, firm INTEGER, agent INTEGER, side TEXT, limit_price INTEGER, qty INTEGER,
    filled INTEGER, price INTEGER, reason TEXT);
CREATE TABLE series (
    week INTEGER, scope TEXT, metric TEXT, value REAL,
    PRIMARY KEY (week, scope, metric)) WITHOUT ROWID;
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS events_week ON events (week);
CREATE INDEX IF NOT EXISTS events_kind ON events (kind, week);
CREATE INDEX IF NOT EXISTS events_agent ON events (agent, week);
CREATE INDEX IF NOT EXISTS events_firm ON events (firm, week);
CREATE INDEX IF NOT EXISTS agent_snap_agent ON agent_snap (agent, week);
CREATE INDEX IF NOT EXISTS series_metric ON series (metric, scope, week);
CREATE INDEX IF NOT EXISTS holdings_week ON holdings (week, firm);
CREATE INDEX IF NOT EXISTS units_week ON units (week, firm);
CREATE INDEX IF NOT EXISTS orders_week ON orders (week, firm);
CREATE INDEX IF NOT EXISTS places_week ON places (week, spot);
"""

BASE_SLOTS = ("food", "housing", "appliances", "entertainment")


class Recorder(_Fingerprint):
    """Writes a run to SQLite. Rows are buffered and committed every so often, so a run
    that is stopped part way still leaves a readable file."""

    def __init__(self, path, cfg, run_id: str = "") -> None:
        super().__init__()
        self.path = pathlib.Path(path)
        self.cfg = cfg
        self.con = sqlite3.connect(self.path)
        self.con.execute("PRAGMA journal_mode = WAL")
        self.con.execute("PRAGMA synchronous = OFF")
        self.con.executescript(TABLES)
        self._buf: dict[str, list] = {name: [] for name in (
            "events", "agent_static", "firm_static", "needs", "agent_snap", "firm_snap",
            "holdings", "units", "orders", "series", "spots", "places")}
        self._spots_written = False
        self._pending = 0
        self.meta("run_id", run_id)
        self.meta("schema_version", SCHEMA_VERSION)
        self.meta("seed", cfg.seed)
        self.meta("config", _dumps(cfg.to_dict()))
        self.meta("code_fingerprint", code_fingerprint())
        self.meta("started", datetime.datetime.now().isoformat(timespec="seconds"))
        self.con.commit()

    # --- small writes -------------------------------------------------------------------
    def meta(self, key, value) -> None:
        self.con.execute("INSERT OR REPLACE INTO run (key, value) VALUES (?, ?)", (key, str(value)))

    def need(self, week, spec) -> None:
        self._buf["needs"].append((spec.name, week, spec.kind, int(spec.invented),
                                   _dumps({k: getattr(spec, k) for k in spec.__dataclass_fields__})))

    def agent_static(self, a) -> None:
        self._buf["agent_static"].append((a.id, a.arrived, a.origin, a.start_cash, a.loss_aversion,
                                          a.horizon, a.growth_expect, a.skill, a.risk, a.taste,
                                          int(a.prefers_equity)))

    def firm_static(self, f) -> None:
        self._buf["firm_static"].append((f.id, f.name, f.need, f.spec.kind, int(f.spec.invented),
                                         f.founded, f.founder_id, f.share_pay, int(f.prefers_equity)))

    def event(self, week, kind, agent_id, firm_id, amount, qty, data) -> None:
        text = _dumps(data)
        self._mix_event(week, kind, agent_id, firm_id, amount, qty, text)
        self._buf["events"].append((week, kind, agent_id, firm_id, amount, qty, text))
        self._pending += 1
        if self._pending >= 100_000:
            self.flush()

    def series(self, week, rows) -> None:
        self._mix_series(week, rows)
        self._buf["series"].extend((week, scope, metric, value) for scope, metric, value in rows)

    def orders(self, week, rows) -> None:
        self._buf["orders"].extend((week,) + tuple(r) for r in rows)

    # --- the weekly snapshot ------------------------------------------------------------------
    def snapshot(self, town) -> None:
        cfg, week = self.cfg, town.week
        if week % cfg.snapshot_every == 0:
            share_price = {f.id: f.share_price for f in town.firms if f.alive}
            rows = self._buf["agent_snap"]
            for a in town.agents:
                subs, unit = a.subs, a.unit
                home, appl = unit.get("housing"), unit.get("appliances")
                others = ",".join(f"{name}:{firm.id}" for name, firm in subs.items()
                                  if name not in BASE_SLOTS)
                rows.append((
                    week, a.id, a.cash, a.employer.id if a.employer is not None else None,
                    a.role, a.klass, a.wage, a.loan, int(a.loan_called),
                    sum(n * share_price.get(fid, 0) for fid, n in a.shares.items()), len(a.shares),
                    a.security, a.h_eff(cfg), a.wellbeing, int(a.happy), int(a.destitute),
                    a.provision, a.condition, a.income_week + a.div_week, a.income_week, a.div_week,
                    a.spend_week, a.weeks_out,
                    subs["food"].id if "food" in subs else None,
                    subs["housing"].id if "housing" in subs else None,
                    home.id if home is not None else None,
                    home.cond if home is not None else None,
                    subs["appliances"].id if "appliances" in subs else None,
                    appl.id if appl is not None else None,
                    appl.cond if appl is not None else None,
                    subs["entertainment"].id if "entertainment" in subs else None,
                    others or None,
                    home.spot.id if home is not None and home.spot is not None else None,
                    a.employer.spot.id if a.employer is not None and a.employer.spot is not None else None,
                    a.travel_hours,
                    subs["transport"].id if "transport" in subs else None))
            rows = self._buf["firm_snap"]
            for f in town.firms:
                if not f.alive:
                    continue
                vacant = sum(1 for u in f.units if u.occupant is None)
                rows.append((
                    week, f.id, f.price, f.wage, len(f.subs), len(f.unserved), len(f.staff),
                    len(f.execs), f.ceo.id if f.ceo is not None else None, f.vacancies, f.cash,
                    f.loan, f.w_revenue, f.w_export, f.w_wages, f.w_goods, f.w_interest, f.w_capex,
                    f.w_wear,
                    f.w_revenue + f.w_export - (f.w_wages + f.w_goods - f.w_capex) - f.w_interest - f.w_wear,
                    f.retained, f.last_dividend, f.shares_out, f.share_price,
                    f.target_growth, int(f.shortfall), f.upkeep_level, f.upkeep_done, len(f.units),
                    vacant, sum(u.cond for u in f.units) / len(f.units) if f.units else None,
                    len(f.projects), f.make_mode, f.made_units, f.import_units, f.export_units,
                    f.spot.id if f.spot is not None else None, len(f.lots), f.land_value))
        if week % cfg.register_every == 0:
            rows = self._buf["holdings"]
            units = self._buf["units"]
            for f in town.firms:
                if not f.alive:
                    continue
                rows.extend((week, f.id, agent_id, n) for agent_id, n in f.holders.items())
                units.extend((week, u.id, f.id, f.need, u.age, u.cond,
                              u.occupant.id if u.occupant is not None else None,
                              u.spot.id if u.spot is not None else None, u.scale, None) for u in f.units)
            units.extend((week, u.id, None, u.spec.name, u.age, u.cond,          # RTR: what people own
                          u.occupant.id if u.occupant is not None else None,
                          u.spot.id if u.spot is not None else None, u.scale,
                          u.owner.id if u.owner is not None else None) for u in town.own_units)
            if town.map is not None:              # what stands on every spot
                if not self._spots_written:
                    self._buf["spots"].extend((s.id, s.x, s.y) for s in town.map.spots)
                    self._spots_written = True
                self._buf["places"].extend(
                    (week, s.id, s.kind, s.label, s.owner.id if s.owner is not None else None,
                     s.user.id if s.user is not None else None, len(s.units) + len(s.private_units),
                     s.occupied + sum(1 for u in s.private_units if u.occupant is not None), s.reserved,
                     s.rent_factor, s.access, s.popularity, s.ground_rent)
                    if s.kind != "plots" else
                    (week, s.id, "homes", "owned", None, None, len(s.private_units),      # RTR: a block of plots is
                     sum(1 for u in s.private_units if u.occupant is not None),          # drawn as a block of homes
                     s.plots_reserved, s.rent_factor, s.access, s.popularity, 0)
                    for s in town.map.spots)
        if week % 13 == 0:
            self.flush()

    # --- writing out --------------------------------------------------------------------------
    def flush(self) -> None:
        con, buf = self.con, self._buf
        inserts = {
            "needs": "INSERT OR REPLACE INTO needs VALUES (?,?,?,?,?)",
            "events": "INSERT INTO events (week, kind, agent, firm, amount, qty, data) VALUES (?,?,?,?,?,?,?)",
            "agent_static": "INSERT OR REPLACE INTO agent_static VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            "firm_static": "INSERT OR REPLACE INTO firm_static VALUES (?,?,?,?,?,?,?,?,?)",
            "agent_snap": "INSERT INTO agent_snap VALUES (" + ",".join("?" * 36) + ")",
            "firm_snap": "INSERT INTO firm_snap VALUES (" + ",".join("?" * 39) + ")",
            "holdings": "INSERT INTO holdings VALUES (?,?,?,?)",
            "units": "INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?,?)",
            "spots": "INSERT OR REPLACE INTO spots VALUES (?,?,?)",
            "places": "INSERT INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            "orders": "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)",
            "series": "INSERT OR REPLACE INTO series VALUES (?,?,?,?)",
        }
        for name, sql in inserts.items():
            if buf[name]:
                con.executemany(sql, buf[name])
                buf[name] = []
        con.commit()
        self._pending = 0

    def finish(self, outcome, summary) -> None:
        self.flush()
        self.meta("outcome", outcome)
        self.meta("summary", _dumps(summary))
        self.meta("fingerprint", self.fingerprint())
        self.meta("events", self.event_count)
        self.meta("finished", datetime.datetime.now().isoformat(timespec="seconds"))
        self.con.executescript(INDEXES)
        self.con.commit()
        self.con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.con.close()
