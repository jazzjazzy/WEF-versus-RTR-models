"""A firm's working week: serve customers, keep its units up, build, make goods,
import what it is short of, export what it profitably can.

Staff are assigned in that order when there are too few of them. Homes and
appliance sets age one week each week and cost more to keep as they age
(Jason, 12/11/2026).
"""

from __future__ import annotations

import math

from .entities import Project
from .ledger import OUTSIDE
from .places import place_unit, reserve_home


# --- decay ------------------------------------------------------------------------------
def upkeep_need(cfg, unit) -> tuple[float, float]:
    """Labour (worker-weeks) and goods (units) one unit needs this week. Both grow with age."""
    spec = unit.spec
    factor = 1.0 + spec.upkeep_growth * unit.age / cfg.weeks_per_year
    return spec.upkeep_labour * factor * unit.scale, spec.upkeep_goods * factor * unit.scale


def best_condition(cfg, unit) -> float:
    """The best condition full upkeep can hold a unit at. It falls as the unit ages."""
    years = unit.age / cfg.weeks_per_year
    return max(cfg.cond_floor_best, 1.0 - unit.spec.aging_rate * years)


def update_condition(cfg, unit, done: float) -> None:
    """One week of wear. `done` is the share of the needed upkeep that was carried out."""
    best = best_condition(cfg, unit)
    cond = min(unit.cond, best)
    cond += cfg.cond_recover * (best - cond) * done
    cond -= cfg.cond_neglect * (1.0 - done)
    unit.cond = min(best, max(0.0, cond))


# --- decisions taken at the quarterly review -----------------------------------------------
def choose_make_mode(cfg, firm) -> str:
    """Make the good in town or import it, whichever is cheaper for shareholders."""
    make = firm.make_cost() * (1.0 + cfg.overhead_allowance)
    imp = firm.spec.import_price
    if firm.make_mode == "make":
        return "import" if make > imp * (1.0 + cfg.make_hysteresis) else "make"
    return "make" if make < imp * (1.0 - cfg.make_hysteresis) else "import"


def export_target(cfg, firm, n_firms: int) -> float:
    """Units a week the firm will try to sell outside: its share of the quota, if it pays."""
    spec = firm.spec
    if spec.make_labour <= 0 or spec.export_quota <= 0:
        return 0.0
    share = spec.export_quota / max(1, n_firms)
    cost = firm.make_cost() * (1.0 + cfg.overhead_allowance) * (1.0 + cfg.export_margin)
    if cost >= spec.export_price:
        return 0.0
    if cfg.export_price_drop <= 0:
        return share
    # The outside pays less for each further unit: sell up to the unit that still covers the cost.
    return share * min(1.0, (1.0 - cost / spec.export_price) / cfg.export_price_drop)


def unit_cost(cfg, spec, wage: int) -> int:
    """What it costs to supply one customer for a week at this wage: labour with
    overhead, goods at the cheaper of making and importing, and for homes and
    appliance sets the cost of the capital tied up in the unit."""
    overhead = 1.0 + cfg.overhead_allowance
    goods_unit = spec.import_price
    if spec.make_labour > 0:
        goods_unit = min(spec.make_labour * wage * overhead, spec.import_price)
    labour = spec.service_labour
    if spec.fixed_labour > 0:
        # A crew it needs however few it serves, spread over the customers a firm reckons on.
        labour += spec.fixed_labour / max(1, cfg.transport_assumed_riders)
    goods = spec.goods_per_sub
    capital = 0.0
    if spec.kind == "asset":
        labour += spec.upkeep_labour
        goods += spec.upkeep_goods
        build = spec.build_labour * wage * overhead + spec.build_goods * goods_unit
        wear = 1.0 / spec.life_years if spec.life_years > 0 else 0.0
        capital = build * (cfg.firm_rate + wear) / cfg.weeks_per_year
    return int(round(labour * wage * overhead + goods * goods_unit + capital))


# --- building ---------------------------------------------------------------------------------
def project_cost(firm, project) -> int:
    return int(project.labour_left * firm.wage + project.goods_left * firm.goods_cost())


def plan_building(town, firm) -> None:
    """Start new units when the buffer of free ones runs low or people were turned away.
    Better homes are planned on top of that, for the well-off waiting for one (16/11/2026)."""
    firm.funding_gap = 0
    if firm.spec.kind != "asset":
        return
    _plan_standard(town, firm)
    if firm.spec.name == "housing" and town.cfg.well_off_income > 0:
        _plan_better(town, firm)


def _plan_standard(town, firm) -> None:
    """Standard units: better homes, built for the well-off, are not counted here."""
    cfg, spec = town.cfg, firm.spec
    standard = [u for u in firm.units if u.scale == 1.0]
    occupied = sum(1 for u in standard if u.occupant is not None)
    if spec.name == "housing":
        buffer = max(cfg.vacancy_buffer_min, math.ceil(cfg.vacancy_buffer_share * occupied))
    else:
        buffer = max(cfg.spare_units_min, math.ceil(cfg.spare_units_share * occupied))
    desired = occupied + buffer + int(round(firm.unmet_demand))
    in_progress = sum(1 for p in firm.projects if p.unit is None and p.scale == 1.0)
    need = min(desired - len(standard) - in_progress, cfg.max_starts_week)
    firm.unmet_demand *= cfg.unmet_decay
    if need <= 0:
        return
    cost = firm.unit_build_cost()
    committed = sum(project_cost(firm, p) for p in firm.projects)
    reserve = int(cfg.reserve_weeks * firm.last_opex)
    funds = firm.cash - reserve - committed + town.bank.firm_credit(firm)
    can = need if cost <= 0 else max(0, funds // cost)
    starts = min(need, can)
    placed = town.map is not None and spec.name == "housing"
    for _ in range(starts):
        project = Project(spec)
        if placed:                           # a new home needs room on a spot
            project.spot = reserve_home(town, firm)
            if project.spot is None:
                town.event("no_land", firm=firm, qty=need)
                break
        firm.projects.append(project)
    if starts < need:
        firm.funding_gap = (need - starts) * cost


def _plan_better(town, firm) -> None:
    """(J) 16/11/2026: better homes for the well-off still waiting for one, less the better
    homes standing free or being built anywhere in town (C: counting people, not looks, so
    none are built while better homes stand empty). The biggest landlord builds them, if it
    can pay for them."""
    cfg = town.cfg
    landlords = town.firms_for("housing")
    if firm is not max(landlords, key=lambda f: (len(f.units), -f.id)):
        return
    waiting = sum(1 for a in town.agents if a.wants_better)
    if waiting == 0:
        return
    free = sum(1 for f in landlords for u in f.units if u.scale > 1.0 and u.occupant is None)
    building = sum(1 for f in landlords for p in f.projects if p.unit is None and p.scale > 1.0)
    wanted = min(waiting - free - building, cfg.max_starts_week)
    if wanted <= 0:
        return
    cost = int(firm.unit_build_cost() * cfg.better_home)
    committed = sum(project_cost(firm, p) for p in firm.projects)
    reserve = int(cfg.reserve_weeks * firm.last_opex)
    funds = firm.cash - reserve - committed + town.bank.firm_credit(firm)
    starts = min(wanted, wanted if cost <= 0 else max(0, funds // cost))
    placed = town.map is not None and firm.spec.name == "housing"
    for _ in range(starts):
        project = Project(firm.spec, scale=cfg.better_home)
        if placed:
            project.spot = reserve_home(town, firm)
            if project.spot is None:
                town.event("no_land", firm=firm, qty=wanted, grade="better")
                break
        firm.projects.append(project)


def _finish_projects(town, firm) -> None:
    remaining = []
    for p in firm.projects:
        if p.labour_left > 1e-9:
            remaining.append(p)
        elif p.unit is None:
            unit = town.new_unit(firm)
            unit.scale = p.scale
            if p.spot is not None:           # the home goes on the spot kept for it
                p.spot.reserved -= 1
                place_unit(p.spot, unit)
            town.event("unit_built", firm=firm, qty=unit.id,
                       **({"spot": p.spot.id} if p.spot is not None else {}),
                       **({"grade": "better"} if p.scale > 1.0 else {}))
        else:
            p.unit.age = 0
            p.unit.cond = 1.0
            town.event("unit_rebuilt", firm=firm, qty=p.unit.id)
    firm.projects = remaining


# --- the working week ----------------------------------------------------------------------------
def _work(town, firm) -> float:
    """Run one firm's week. Returns the units it could export with the staff left over."""
    cfg, spec = town.cfg, firm.spec
    labour = float(len(firm.staff))
    n_subs = firm.load()                             # in standard plans: a bigger plan counts as that many
    firm.unserved = {}

    # 1. service
    variable = n_subs * spec.service_labour
    need_service = variable + spec.fixed_labour      # some firms need a crew however few they serve
    service = min(labour, need_service)
    labour -= service
    served = n_subs
    if spec.kind == "flow" and need_service > 0:
        if service < spec.fixed_labour:
            served = 0                               # without its crew nothing runs
        elif variable > 0:
            served = int(n_subs * (service - spec.fixed_labour) / variable + 1e-9)

    # 2. upkeep, at the level the firm has chosen
    up_labour_full = up_goods_full = 0.0
    for u in firm.units:
        l, g = upkeep_need(cfg, u)
        up_labour_full += l
        up_goods_full += g
    upkeep = min(labour, up_labour_full * firm.upkeep_level)
    labour -= upkeep
    done = upkeep / up_labour_full if up_labour_full > 0 else 1.0

    # 3. building
    uses = []
    for p in firm.projects:
        use = min(labour, p.labour_left, cfg.build_crew)
        labour -= use
        goods = p.goods_left if p.labour_left <= 1e-9 else p.goods_left * use / p.labour_left
        uses.append((p, use, goods))

    # 4. goods: make what it can, import the rest
    goods_need = served * spec.goods_per_sub + up_goods_full * done + sum(g for _, _, g in uses)
    made = 0.0
    if firm.make_mode == "make" and spec.make_labour > 0 and goods_need > 0:
        make_labour = min(labour, goods_need * spec.make_labour)
        labour -= make_labour
        made = make_labour / spec.make_labour
    gap = max(0.0, goods_need - made)
    cost = int(round(gap * spec.import_price))
    if cost > firm.cash:
        town.bank.lend_firm(firm, cost - firm.cash)
    if cost > firm.cash:                       # still short: buy what it can afford
        gap = firm.cash / spec.import_price if spec.import_price > 0 else 0.0
        cost = min(firm.cash, int(gap * spec.import_price))
    town.ledger.pay(firm, OUTSIDE, cost, "import")
    firm.w_goods += cost
    firm.made_units = made
    firm.import_units = gap if cost > 0 else 0.0
    have = made + firm.import_units
    share = 1.0 if goods_need <= 1e-9 else min(1.0, have / goods_need)

    # a shortage of goods cuts service, upkeep and building alike
    if share < 1.0:
        served = int(served * share + 1e-9)
        done *= share
    firm.upkeep_done = done

    # building is not a cost of the week: it turns into units. Wear on the units is.
    build_labour = sum(use for _, use, _ in uses) * share
    build_goods = sum(g for _, _, g in uses) * share
    made_part = made / have if have > 1e-9 else 0.0
    goods_unit = made_part * firm.make_cost() + (1.0 - made_part) * spec.import_price
    firm.w_capex += int(build_labour * firm.staff_pay() + build_goods * goods_unit)   # the work done, at what was paid for it
    if firm.units and spec.life_years > 0:
        firm.w_wear += int(sum(u.scale for u in firm.units) * firm.unit_build_cost()
                           / (spec.life_years * cfg.weeks_per_year))
    if served < n_subs:                              # the newest customers go without, plan by plan
        plans = 0
        for agent_id, agent in firm.subs.items():
            plans += agent.plan.get(firm.need, 1)
            if plans > served:
                firm.unserved[agent_id] = True

    # units age and wear; projects advance
    for u in firm.units:
        u.age += 1
        update_condition(cfg, u, done)
    for p, use, goods in uses:
        p.labour_left -= use * share
        p.goods_left = max(0.0, p.goods_left - goods * share)
    _finish_projects(town, firm)

    # 5. whatever staff are left can make goods: for the town's makers first (RTR), then for export
    firm.town_units = 0.0
    if firm.town_target > 0 and spec.make_labour > 0:
        firm.town_units = min(firm.town_target, labour / spec.make_labour)
        labour -= firm.town_units * spec.make_labour
    if firm.export_target > 0 and spec.make_labour > 0:
        return min(firm.export_target, labour / spec.make_labour)
    return 0.0


def operate(town) -> None:
    """Every firm's working week, then the outside buys exports up to its quota."""
    wants: dict[str, list] = {}
    for firm in town.alive_firms:
        firm.export_units = 0.0
        plan_building(town, firm)
        want = _work(town, firm)
        if want > 0:
            wants.setdefault(firm.need, []).append((firm, want))
    drop = town.cfg.export_price_drop
    for need_name, entries in wants.items():
        quota = town.needs[need_name].export_quota
        total = sum(w for _, w in entries)
        scale = min(1.0, quota / total) if total > 0 else 0.0
        share = quota / max(1, len(town.firms_for(need_name)))
        for firm, want in entries:
            units = want * scale
            price = firm.spec.export_price
            if drop > 0 and share > 0:        # the average price over the units sold
                price *= 1.0 - drop * min(1.0, units / share) / 2.0
            revenue = int(round(units * price))
            town.ledger.pay(OUTSIDE, firm, revenue, "export")
            firm.export_units = units
            firm.w_export += revenue
