"""Company rules: the quarterly review, prices for the shareholders, dividends,
shares for wages, raising money, new firms and new needs, failure and takeover."""

from __future__ import annotations

import math

from . import rtr_owning
from .config import NeedSpec
from .entities import Project
from .firmops import appoint_ceo, set_price, set_wage, sync_pay
from .labour import in_the_line, separate
from .ledger import OUTSIDE
from .places import dist, give_up_spots, hand_back_leased_blocks, home_spot, reach, reserve_home, take_spot
from .production import best_condition, choose_make_mode, export_target, project_cost, unit_cost
from .subscriptions import home_available, note_turned_away, settle_arrival, unsubscribe, wants

# Transport is left out on purpose: it arrives with the map in stage 2.
NEW_NEED_NAMES = [
    "health", "education", "communications", "clothing", "fitness", "childcare", "travel",
    "security", "gardening", "cleaning", "beauty", "news", "gaming", "pets", "insurance",
    "advice", "music", "sport",
]


# --- profit and the shareholders' target ------------------------------------------------------
def target_growth(town, firm) -> float:
    """What the shareholders expect, each weighted by how much they hold (Jason, 12/11/2026)."""
    return firm.weighted(town, lambda a: a.growth_expect)


def quarter_profit(firm) -> int:
    """Revenue and exports, less wages, imported goods and interest, less wear on its units.
    Money spent building units is taken back out: it became units, not a cost."""
    running = firm.q_wages + firm.q_goods - firm.q_capex
    return firm.q_revenue + firm.q_export - running - firm.q_interest - firm.q_wear


def margin(firm):
    """Profit as a share of revenue over the last year, or None without a record."""
    revenue = sum(firm.rev_hist[-4:])
    if len(firm.profit_hist) < 2 or revenue <= 0:
        return None
    return sum(firm.profit_hist[-4:]) / revenue


def line_share(town, wage: int) -> float:
    """The line for work, as a share of the town: everyone with no job (Jason, 12/11/2026:
    "cutting when there is a queue"). RTR (Jason, 19/11/2026): only those who would take a
    job at this wage; someone who would turn it down "wouldn't even apply"."""
    cfg = town.cfg
    if cfg.rtr and cfg.line_is_who_would_take and town.agents:
        return in_the_line(town, wage) / len(town.agents)
    return town.jobless_share()


def review_firm(town, firm) -> None:
    """The quarterly review. Profit against the shareholders' target decides what moves."""
    cfg = town.cfg
    profit = quarter_profit(firm)
    had_revenue = sum(firm.rev_hist) + firm.q_revenue + firm.q_export > 0
    firm.profit_hist.append(profit)
    firm.rev_hist.append(firm.q_revenue + firm.q_export)
    firm.retained += profit
    eps = profit / firm.shares_out if firm.shares_out > 0 else 0.0
    firm.eps_hist.append(eps)
    firm.target_growth = growth = target_growth(town, firm)
    n = len(firm.eps_hist)
    if n >= 5:
        target = max(firm.eps_hist[-5], 0.0) * (1.0 + growth)       # the same quarter a year ago
    elif n >= 2:
        target = max(firm.eps_hist[-2], 0.0) * (1.0 + growth / 4.0)  # a young firm: last quarter
    else:
        target = 0.0
    firm.shortfall = shortfall = profit <= 0 or eps < target

    # A firm that has never had a customer has nothing to reprice or squeeze yet.
    if had_revenue:
        if shortfall:
            direction = 1                       # the rule as given: the price rises
            if cfg.price_rule == "search" and firm.last_dir != 0:
                direction = firm.last_dir
                if firm.profit_before_move is not None and profit < firm.profit_before_move:
                    direction = -firm.last_dir  # the last move lost money: go the other way
            firm.last_dir = direction
            firm.profit_before_move = profit
            set_price(town, firm, int(round(firm.price * (1.0 + direction * cfg.price_step))),
                      "shortfall")
        else:
            firm.last_dir = 0
            firm.profit_before_move = None

        if firm.spec.kind == "asset":
            if shortfall:
                horizon = firm.weighted(town, lambda a: a.h_eff(cfg))
                impatience = min(2.0, max(0.25, cfg.skimp_horizon_ref / max(horizon, 1.0)))
                level = max(cfg.upkeep_floor, firm.upkeep_level - cfg.skimp_step * impatience)
            else:
                level = min(1.0, firm.upkeep_level + cfg.restore_step)
            if level != firm.upkeep_level:
                town.event("upkeep_change", firm=firm, old=round(firm.upkeep_level, 3),
                           new=round(level, 3))
                firm.upkeep_level = level

        if shortfall and firm.vacancies == 0:
            lower = int(firm.wage * (1.0 - cfg.wage_step_down))
            if line_share(town, lower) > cfg.wage_cut_unemployment:
                set_wage(town, firm, lower, "queue")

    if firm.spec.kind == "asset" and not shortfall:
        _plan_rebuilds(town, firm)

    mode = choose_make_mode(cfg, firm)
    if mode != firm.make_mode:
        town.event("make_mode", firm=firm, old=firm.make_mode, new=mode)
        firm.make_mode = mode
    firm.export_target = export_target(cfg, firm, len(town.firms_for(firm.need)))


def _plan_rebuilds(town, firm) -> None:
    """Rebuild units worn past the point where upkeep can hold them, if it can be paid for."""
    cfg = town.cfg
    queued = {id(p.unit) for p in firm.projects if p.unit is not None}
    cost = firm.unit_build_cost()
    funds = (firm.cash - int(cfg.reserve_weeks * firm.last_opex)
             - sum(project_cost(firm, p) for p in firm.projects) + town.bank.firm_credit(firm))
    started = 0
    for unit in firm.units:
        if started >= cfg.max_starts_week or funds < cost:
            break
        if id(unit) in queued or best_condition(cfg, unit) >= cfg.replace_below:
            continue
        firm.projects.append(Project(firm.spec, unit))
        funds -= cost
        started += 1


# --- dividends, shares for wages, raising money ---------------------------------------------------
def pay_dividends(town, firm) -> int:
    """Pay out profit not yet distributed, from cash above the reserve. Never borrowed money."""
    cfg = town.cfg
    firm.dps_hist.append(0)
    firm.last_dividend = 0
    if firm.shares_out <= 0 or firm.retained <= 0:
        return 0
    committed = sum(project_cost(firm, p) for p in firm.projects)
    excess = firm.cash - int(cfg.reserve_weeks * firm.last_opex) - committed
    if excess <= 0:
        return 0
    payout = 1.0
    if firm.projects or firm.funding_gap > 0:      # still building: keep part back
        horizon = firm.weighted(town, lambda a: a.h_eff(cfg))
        payout = min(1.0, max(cfg.payout_min, cfg.payout_horizon_ref / max(horizon, 1.0)))
    total = min(int(excess * payout), firm.retained)
    per_share = total // firm.shares_out
    if per_share <= 0:
        return 0
    paid = 0
    for agent_id, shares in list(firm.holders.items()):
        agent = town.agent(agent_id)
        amount = per_share * shares
        town.ledger.pay(firm, agent, amount, "dividend")
        agent.div_this_quarter += amount
        agent.div_week += amount
        paid += amount
    firm.retained -= paid
    firm.last_dividend = paid
    firm.dps_hist[-1] = per_share
    town.event("dividend", firm=firm, amount=paid, qty=per_share)
    return paid


def grant_shares(town, firm) -> None:
    """Turn wages held back during the quarter into new shares for the staff who earned them."""
    if not firm.accrual:
        return
    price = max(1, firm.share_price or town.cfg.share_par)
    for agent_id, held in list(firm.accrual.items()):
        shares = held // price
        if shares > 0:
            agent = town.agent(agent_id)
            town.issue_shares(firm, agent, shares)
            town.event("share_grant", agent=agent, firm=firm, amount=price, qty=shares)
        rest = held - shares * price
        if rest > 0:
            firm.accrual[agent_id] = rest
        else:
            del firm.accrual[agent_id]


def raise_money(town, firm) -> None:
    """Offer new shares when there is building the firm cannot fund, or when its founder
    would sooner sell shares than borrow."""
    cfg = town.cfg
    if town.broker.pending_issue(firm) > 0 or firm.shares_out <= 0:
        return
    need = firm.funding_gap
    if need <= 0 and firm.prefers_equity:
        need = sum(project_cost(firm, p) for p in firm.projects if p.unit is None)
    if need <= 0:
        return
    price = max(1, int((firm.share_price or cfg.share_par) * (1.0 - cfg.issue_discount)))
    shares = min(need // price, firm.shares_out // 4)        # no more than a quarter again at a time
    if shares > 0:
        town.broker.issue(firm, price, shares)
        town.event("issue_offered", firm=firm, amount=price, qty=shares)


def cash_call(town, firm, need: int) -> bool:
    """Ask the largest shareholder for rescue cash, in return for new shares at the last price."""
    cfg = town.cfg
    if not firm.holders or need <= 0:
        return False
    top = town.agent(max(firm.holders, key=lambda i: (firm.holders[i], -i)))
    if top.cash < need:
        return False
    young = town.week - firm.founded < 2 * cfg.weeks_per_year
    if not young and sum(firm.profit_hist[-4:]) < 0:
        return False                              # no more good money after bad
    amount = max(need, min(need * 4, top.cash // 2))
    town.ledger.pay(top, firm, amount, "cash_call")
    town.issue_shares(firm, top, max(1, amount // max(1, firm.share_price)))
    town.event("cash_call", agent=top, firm=firm, amount=amount)
    return True


# --- who runs the firm --------------------------------------------------------------------------
def pick_manager(town, exclude=None):
    """The most skilled resident free to run a firm: the jobless first, then staff."""
    best = None
    for a in town.agents:
        if a is exclude or a.role in ("ceo", "exec"):
            continue
        key = (a.role is None, a.skill, -a.id)
        if best is None or key > best[0]:
            best = (key, a)
    return best[1] if best else None


def install_ceo(town, firm, owner) -> None:
    """The owner runs the firm if free to; otherwise they appoint a manager."""
    chief = owner
    if owner.role in ("ceo", "exec"):
        chief = pick_manager(town, exclude=owner)
        if chief is None:
            return
    if chief.role == "staff":
        separate(town, chief, "founded" if chief is owner else "poached")
    appoint_ceo(town, firm, chief)


def check_control(town, firm) -> None:
    """Whoever holds half the shares controls the firm, and takes the top job if free."""
    controller_id = firm.controller()
    if controller_id is None or (firm.ceo is not None and firm.ceo.id == controller_id):
        return
    controller = town.agent(controller_id)
    if controller.role in ("ceo", "exec"):
        return
    if firm.ceo is not None:
        separate(town, firm.ceo, "ousted")
    if controller.role == "staff":
        separate(town, controller, "founded")
    appoint_ceo(town, firm, controller)
    town.event("control_change", agent=controller, firm=firm)


# --- new firms and new needs --------------------------------------------------------------------
def found_firm(town, founder, capital: int, spec, in_kind_units: int = 0, price: int | None = None,
               name: str | None = None, near=None):
    """A founder puts in capital and receives shares at $10. Starting units, if any,
    are paid for in shares too. Where there is a map the firm takes a spot for its premises,
    near `near` if given; if no spot can be had the firm is not founded and None is returned."""
    cfg = town.cfg
    firm = town.add_firm(spec.name, founder, name)
    firm.wage = town.typical_wage()
    capital = min(int(capital), founder.cash)
    town.ledger.pay(founder, firm, capital, "founding")
    if town.map is not None:
        # Every firm needs premises: a spot, fitted out with goods bought from outside.
        if take_spot(town, firm, "premises", near=near) is None:
            town.ledger.pay(firm, founder, firm.cash, "founding")      # no spot: the money goes back
            town.firms.pop()
            del town._firms[firm.id]
            town.event("founding_blocked", agent=founder, amount=capital, need=spec.name,
                       reason="no spot to be had")
            return None
        fit_out = min(cfg.premises_cost, firm.cash)
        town.ledger.pay(firm, OUTSIDE, fit_out, "import")
    for _ in range(in_kind_units):
        town.new_unit(firm)
    in_kind = in_kind_units * firm.unit_build_cost()
    town.issue_shares(firm, founder, max(1, (capital + in_kind) // cfg.share_par))
    firm.share_price = cfg.share_par
    if price is not None:
        firm.price = int(price)
    firm.share_pay = cfg.share_pay_fraction if town.rng.random() < cfg.share_pay_firm_share else 0.0
    firm.prefers_equity = founder.prefers_equity
    firm.make_mode = choose_make_mode(cfg, firm)
    firm.export_target = export_target(cfg, firm, len(town.firms_for(spec.name)))
    install_ceo(town, firm, founder)
    founder.last_trigger = "founded"
    town.event("firm_founded", agent=founder, firm=firm, amount=capital, need=spec.name,
               units=in_kind_units, in_kind=in_kind, price=firm.price)
    town.rec.firm_static(firm)
    return firm


def invent_need(town) -> NeedSpec:
    """A new need: a service used in town, discretionary, suiting only some tastes (Jason: no limit)."""
    cfg, rng = town.cfg, town.rng
    count = sum(1 for s in town.needs.values() if s.invented)
    name = NEW_NEED_NAMES[count] if count < len(NEW_NEED_NAMES) else f"need-{count + 1}"
    labour = rng.uniform(cfg.invented_labour_low, cfg.invented_labour_high)
    spec = NeedSpec(
        name=name, kind="flow", weight=cfg.invented_weight, essential=False, priority=5 + count,
        service_labour=labour, goods_per_sub=0.0, make_labour=0.0,
        import_price=0, export_price=0, export_quota=0.0, initial_price=0,
        appeal=rng.uniform(cfg.invented_appeal_low, cfg.invented_appeal_high),
        invented=True, salt=rng.random(), trips_per_week=1.0,
    )
    spec.initial_price = int(round(unit_cost(cfg, spec, town.typical_wage())
                                   * (1.0 + cfg.new_need_markup)))
    town.needs[name] = spec
    town.rec.need(town.week, spec)
    town.event("need_invented", amount=spec.initial_price, need=name, appeal=round(spec.appeal, 3),
               labour=round(labour, 4))
    return spec


def unserved_gap(town):
    """(J) 16/11/2026: the shop need with the most residents who would buy it and cannot
    reach any seller of it, if at least `unserved_entry_min`. Shop needs are the ones a
    customer travels to, not homes and not the ride. Returns (spec, how many, the home spot
    with the most of them within a walk), or None. A need nobody sells is left to the old rule."""
    cfg = town.cfg
    if town.map is None or not cfg.shops_near_unserved:
        return None
    best = None
    for name, spec in town.needs.items():
        if spec.trips_per_week <= 0 or name in ("housing", "transport"):
            continue
        sellers = [f.spot for f in town.firms_for(name) if f.spot is not None]
        if not sellers:
            continue
        homes = []
        for agent in town.agents:
            if name in agent.subs or not wants(agent, spec):
                continue
            home = home_spot(agent)
            if home is None:
                continue
            limit = reach(town, agent)
            if all(dist(home, s) > limit for s in sellers):
                homes.append(home)
        if len(homes) >= cfg.unserved_entry_min and (best is None or len(homes) > len(best[1])):
            best = (spec, homes)
    if best is None:
        return None
    spec, homes = best
    walk = cfg.walk_range
    places = {h.id: h for h in homes}.values()
    target = max(places, key=lambda s: (sum(1 for h in homes if dist(h, s) <= walk), -s.id))
    return spec, len(homes), target


def choose_venture(town, capital: int):
    """What a founder with this much capital would start: (need, price), or None.
    They may invent a need. Otherwise they enter the need that is unserved or most
    profitable, undercutting the cheapest firm but never pricing below cost plus a margin."""
    cfg, rng = town.cfg, town.rng
    wage = town.typical_wage()
    if (town.map is not None and capital >= cfg.flow_entry_capital
            and town.reach_blocked_last >= cfg.transport_trigger
            and not town.firms_for("transport")):
        # Enough people were turned away by distance last quarter: transport is the gap to fill.
        spec = town.needs.get("transport")
        if spec is None:
            spec = transport_spec(town)
            town.needs["transport"] = spec
            town.rec.need(town.week, spec)
            town.event("need_invented", amount=spec.initial_price, need="transport",
                       turned_away=town.reach_blocked_last)
        return spec, spec.initial_price
    gap = unserved_gap(town) if capital >= cfg.flow_entry_capital else None
    if gap is not None:
        # People who cannot reach any seller: open near them, at the going price (no rival of theirs to undercut).
        spec, count, target = gap
        floor = int(round(unit_cost(cfg, spec, wage) * (1.0 + cfg.cost_floor_markup)))
        price = max(min(f.price for f in town.firms_for(spec.name)), floor)
        return spec, price, target, count
    # RTR 2 (Jason: "Why don't I just leave it up to the people who are actually going to create
    # things for fun?"): while people have ideas, founders of firms do not invent.
    people_invent = cfg.rtr and cfg.idea_rate > 0
    if capital >= cfg.flow_entry_capital and not people_invent and rng.random() < cfg.invent_prob:
        spec = invent_need(town)
        return spec, spec.initial_price
    best = None
    for name, spec in town.needs.items():
        if capital < (cfg.asset_entry_capital if spec.kind == "asset" else cfg.flow_entry_capital):
            continue
        cost = unit_cost(cfg, spec, wage)
        firms = town.firms_for(name)
        if not firms:
            score = 0.5 if spec.invented else 1.0
            price = int(round(cost * (1.0 + cfg.new_need_markup)))
        else:
            margins = [m for m in (margin(f) for f in firms) if m is not None]
            if not margins or max(margins) < cfg.entry_margin:
                continue
            score = max(margins)
            cheapest = min(f.price for f in firms)
            price = max(int(cheapest * (1.0 - cfg.undercut)),
                        int(round(cost * (1.0 + cfg.cost_floor_markup))))
            if price >= cheapest:
                continue                          # no room to undercut
        if best is None or score > best[0]:
            best = (score, spec, price)
    return (best[1], best[2]) if best else None


def start_venture(town, founder, capital: int, spec, price: int, near=None, unserved: int = 0):
    firm = found_firm(town, founder, capital, spec, price=price, near=near)
    if firm is None:
        return None
    if near is not None:
        town.event("unserved_entry", agent=founder, firm=firm, qty=unserved, need=spec.name,
                   aimed=near.id, spot=firm.spot.id if firm.spot is not None else None)
    if spec.kind == "asset":
        cost = firm.unit_build_cost()
        first = min(20, int(capital * 0.8) // cost) if cost > 0 else 0
        placed = town.map is not None and spec.name == "housing"
        for _ in range(first):
            project = Project(spec)
            if placed:
                project.spot = reserve_home(town, firm)
                if project.spot is None:
                    break
            firm.projects.append(project)
    return firm


def maybe_arrive_founder(town):
    """While the town is under its cap, a founder may turn up with capital (Jason, 12/11/2026).
    Like every arrival they must be able to rent a home, or in the RTR world to buy one the
    bank holds empty."""
    cfg, rng = town.cfg, town.rng
    if cfg.at_cap(town.population):
        return None
    if rng.random() >= cfg.founder_arrival_rate:
        return None
    capital = int(rng.lognormvariate(math.log(cfg.founder_capital_median), cfg.founder_capital_sigma))
    invest = int(capital * (1.0 - cfg.founder_keep_share))
    buy = None
    if not home_available(town):
        # RTR (Jason, 18/11/2026): with nothing to rent, a newcomer may buy a home the bank holds
        # empty. A founder has no income yet, so no loan: the cash they keep back must cover it.
        buy = rtr_owning.home_for_newcomer(town, capital - invest, 0)
        if buy is None:
            note_turned_away(town)
            town.no_home_week = town.week
            town.event("arrival_blocked", amount=capital, who="founder",
                       **({"reason": "no home free"} if town.map is not None else {}))
            return None
    venture = choose_venture(town, invest)
    if venture is None:
        return None
    founder = town.add_agent(cash=capital, origin="founder")
    if buy is None:
        settle_arrival(town, founder)          # they settle in first, as a customer of the firms already there
    else:
        rtr_owning.arrive_as_owner(town, founder, *buy, 0)
    town.event("arrival", agent=founder, amount=capital, who="founder", **({"bought": buy[0].id} if buy else {}))
    return start_venture(town, founder, invest, *venture)


def resident_founders(town) -> None:
    """Residents with enough cash and appetite for risk start firms."""
    cfg, rng = town.cfg, town.rng
    for agent in list(town.agents):
        if agent.hustle is not None and agent.hustle.spec is not None:
            continue                             # RTR 2: a maker of a need becomes a company by the makers' own rule
        if agent.cash < cfg.flow_entry_capital:
            continue
        if rng.random() >= cfg.resident_founder_rate * agent.risk:
            continue
        capital = int(agent.cash * cfg.founder_invest_share)
        venture = choose_venture(town, capital)
        if venture is not None:
            start_venture(town, agent, capital, *venture)


# --- failure, sale, wind-up -------------------------------------------------------------------
def _pay_out(town, firm, source, amount: int, kind: str) -> None:
    """Share `amount` of `source`'s cash among the firm's shareholders by holding."""
    if amount <= 0 or firm.shares_out <= 0 or not firm.holders:
        return
    per_share = amount // firm.shares_out
    paid = 0
    for agent_id, shares in list(firm.holders.items()):
        part = per_share * shares
        town.ledger.pay(source, town.agent(agent_id), part, kind)
        paid += part
    top = town.agent(max(firm.holders, key=lambda i: (firm.holders[i], -i)))
    town.ledger.pay(source, top, amount - paid, kind)      # the odd cents


def _cancel_shares(town, firm) -> None:
    if firm.shares_out <= 0:
        return
    town.event("shares_cancelled", firm=firm, qty=firm.shares_out, holders=len(firm.holders))
    for agent_id in list(firm.holders):
        town.agent(agent_id).shares.pop(firm.id, None)
    firm.holders = {}
    firm.shares_out = 0


def _dismiss_management(town, firm) -> None:
    for a in list(firm.execs):
        separate(town, a, "firm_failed")
    if firm.ceo is not None:
        separate(town, firm.ceo, "firm_failed")


def _close(town, firm, reason: str) -> None:
    """Settle up and shut: the bank first, then the shareholders, then the shares are cancelled."""
    if firm.loan > 0:
        take = min(firm.cash, firm.loan)
        town.ledger.pay(firm, OUTSIDE, take, "loan_recovery")
        firm.loan -= take
        town.bank.write_off_firm(firm)
    _pay_out(town, firm, firm, firm.cash, "liquidation")
    _cancel_shares(town, firm)
    town.broker.issues.pop(firm.id, None)
    firm.alive = False
    firm.closed_week = town.week
    firm.close_reason = reason
    town.event("firm_closed", firm=firm, reason=reason)


def wind_up(town, firm, reason: str) -> None:
    """Shut a firm with no business left: staff laid off, customers released, empty units scrapped."""
    if not firm.alive:
        return
    for a in list(firm.staff) + list(firm.execs) + ([firm.ceo] if firm.ceo is not None else []):
        separate(town, a, "wound_up")
    hand_back_leased_blocks(town, firm)        # leased homes go back to their owner, tenants and all
    for agent in list(firm.subs.values()):
        unsubscribe(town, agent, firm.need, "firm_closed")
    if firm.units:
        town.event("units_scrapped", firm=firm, qty=len(firm.units))
        if town.cfg.rtr:
            from .rtr_owning import scrap_single_homes
            scrap_single_homes(town, firm)     # the single homes it held off its blocks go too
    firm.units = []
    firm.projects = []
    give_up_spots(town, firm)                  # its land is freed or sold; the money joins its cash
    _close(town, firm, reason)


def _rival_buyer(town, firm, price: int):
    cfg = town.cfg
    best = None
    for rival in town.firms_for(firm.need):
        if rival is firm:
            continue
        funds = rival.cash - int(cfg.reserve_weeks * rival.last_opex) + town.bank.firm_credit(rival)
        if funds >= price and (best is None or rival.cash > best.cash):
            best = rival
    return best


def _merge(town, firm, rival, price: int) -> None:
    """A rival buys the failed firm: its customers, staff, units and remaining debt."""
    if rival.cash < price:
        town.bank.lend_firm(rival, price - rival.cash)
    price = min(price, rival.cash)
    to_bank = min(price, firm.loan)
    town.ledger.pay(rival, OUTSIDE, to_bank, "loan_recovery")
    firm.loan -= to_bank
    town.ledger.pay(rival, firm, price - to_bank, "takeover")   # anything above the debt
    rival.loan += firm.loan                                     # the debt stays on the units
    firm.loan = 0
    if rival.loan > 0:
        rival.loan_pay = -(-rival.loan // town.cfg.firm_term_weeks)
    _dismiss_management(town, firm)
    for a in list(firm.staff):
        owed = firm.accrual.pop(a.id, 0)
        town.ledger.pay(firm, a, min(owed, firm.cash), "wage")
        a.employer = rival
        a.wage = rival.wage
        rival.staff.append(a)
        town.event("employer_changed", agent=a, firm=rival, amount=rival.wage, old=firm.id)
    firm.staff = []
    for agent in list(firm.subs.values()):
        agent.subs[firm.need] = rival
        rival.subs[agent.id] = agent
    firm.subs = {}
    rival.extra += firm.extra
    firm.extra = 0
    for unit in firm.units:
        unit.firm = rival
        rival.units.append(unit)
    firm.units = []
    for spot in firm.lots:                     # the blocks its homes stand on go with them
        spot.user = rival
        if spot.owner is firm:
            spot.owner = rival
        if spot.owner is rival:
            spot.ground_rent = 0               # it was leasing from the rival: the lease ends
        rival.lots.append(spot)
    firm.lots = []
    if town.map is not None:
        for spot in town.map.spots:            # land it had leased out: the rival is the landlord now
            if spot.owner is firm and spot.user is not firm:
                spot.owner = rival
                if spot.user is rival:
                    spot.ground_rent = 0
    rival.projects.extend(firm.projects)
    firm.projects = []
    give_up_spots(town, firm)                  # its own premises are not needed
    town.event("takeover", firm=rival, amount=price, target=firm.id, buyer="rival")
    _close(town, firm, "absorbed")


def _sell_to_resident(town, firm, reserve_price: int) -> None:
    """The richest resident buys the failed firm for what they can pay, up to the reserve price."""
    cfg = town.cfg
    old_top = max(firm.holders, key=lambda i: (firm.holders[i], -i)) if firm.holders else None
    buyer = None
    for a in town.agents:
        if a.id != old_top and (buyer is None or a.cash > buyer.cash):
            buyer = a
    if buyer is None:
        buyer = town.agent(old_top)
    budget = int(buyer.cash * cfg.takeover_cash_share)
    price = min(reserve_price, budget)
    to_bank = min(price, firm.loan)
    town.ledger.pay(buyer, OUTSIDE, to_bank, "loan_recovery")
    firm.loan -= to_bank
    _pay_out(town, firm, buyer, price - to_bank, "takeover")    # anything above the debt
    _cancel_shares(town, firm)
    town.broker.issues.pop(firm.id, None)        # the old owners' share offer goes with them
    firm.q_revenue = firm.q_export = firm.q_wages = firm.q_goods = 0
    firm.q_interest = firm.q_capex = firm.q_wear = 0     # the new owner's first quarter starts clean
    _dismiss_management(town, firm)
    weekly = max(firm.last_opex, firm.payroll(cfg))
    capital = max(0, min(int(cfg.takeover_capital_weeks * weekly), budget - price))
    town.ledger.pay(buyer, firm, capital, "founding")
    town.issue_shares(firm, buyer, max(1, (price + capital) // cfg.share_par))
    firm.share_price = cfg.share_par
    firm.founder_id = buyer.id
    firm.sale_week = town.week
    firm.prefers_equity = buyer.prefers_equity
    firm.profit_hist, firm.eps_hist, firm.rev_hist, firm.dps_hist = [], [], [], []
    firm.retained = 0
    firm.last_dir = 0
    firm.profit_before_move = None
    firm.shortfall = False
    firm.loan_missed = 0
    if firm.loan > 0:
        firm.loan_pay = -(-firm.loan // cfg.firm_term_weeks)
    install_ceo(town, firm, buyer)
    buyer.last_trigger = "bought_firm"
    town.event("takeover", agent=buyer, firm=firm, amount=price, capital=capital, buyer="resident")


def fail_firm(town, firm, reason: str) -> None:
    """The firm cannot meet its wages or its loan. With customers it is sold as a going
    concern the same week; without them it is wound up."""
    cfg = town.cfg
    if not firm.alive:
        return
    if firm.sale_week is not None and town.week - firm.sale_week < cfg.quarter_weeks:
        return                                    # just sold: it sheds unpaid staff instead
    town.event("firm_failed", firm=firm, amount=firm.cash, reason=reason, debt=firm.loan,
               customers=len(firm.subs), staff=len(firm.staff))
    if not firm.subs:
        wind_up(town, firm, reason)
        return
    value = firm.collateral(cfg)
    town.bank.write_down(firm, int(cfg.ltv * value))   # debt cut to what the units can secure
    price = int(cfg.fire_sale * value)
    rival = _rival_buyer(town, firm, price)
    lived_in = firm.spec.kind == "asset" and any(u.occupant is not None for u in firm.units)
    sold_this_year = (firm.sale_week is not None
                      and town.week - firm.sale_week < cfg.weeks_per_year)
    kept_running = firm.need == "transport" and not cfg.transport_can_close
    if rival is not None:
        _merge(town, firm, rival, price)
    elif lived_in or kept_running or not sold_this_year:
        _sell_to_resident(town, firm, price)
    else:
        # A service firm that fails again within a year of being sold is not sold twice:
        # nobody is made to keep a loss-maker alive. Occupied homes are the exception above,
        # and transport is too when the `transport_can_close` dial is off.
        wind_up(town, firm, reason)


# --- wages ------------------------------------------------------------------------------------
def _fund_payroll(town, firm) -> bool:
    total = firm.payroll(town.cfg)
    if firm.cash >= total:
        return True
    town.bank.lend_firm(firm, total - firm.cash)
    if firm.cash >= total:
        return True
    cash_call(town, firm, total - firm.cash)
    return firm.cash >= total


def _shed_unpaid(town, firm) -> None:
    """Let go the people the firm cannot pay this week, last hired first."""
    cfg = town.cfg
    while firm.cash < firm.payroll(cfg) and (firm.staff or firm.execs):
        separate(town, firm.staff[-1] if firm.staff else firm.execs[-1], "unpaid")
        sync_pay(town, firm)


def _pay_wages(town, firm) -> None:
    cfg = town.cfg
    total = 0
    for a in firm.staff:
        wage = a.wage if firm.own_rates else firm.wage      # RTR: each on the rate they keep
        held = int(wage * firm.share_pay)
        town.ledger.pay(firm, a, wage - held, "wage")
        a.income_week += wage - held
        if held:
            firm.accrual[a.id] = firm.accrual.get(a.id, 0) + held
        total += wage
    pay = firm.exec_pay(cfg)
    for a in firm.execs:
        town.ledger.pay(firm, a, pay, "wage")
        a.income_week += pay
        total += pay
    if firm.ceo is not None:
        pay = min(firm.ceo_pay(cfg), firm.cash)        # an owner short of cash goes unpaid
        town.ledger.pay(firm, firm.ceo, pay, "wage")
        firm.ceo.income_week += pay
        total += pay
    firm.w_wages += total


def payroll(town) -> None:
    """Wages are paid. A firm that cannot pay, after borrowing and asking its largest
    shareholder, fails here."""
    for firm in list(town.alive_firms):
        if firm.alive:
            sync_pay(town, firm)
            if not _fund_payroll(town, firm):
                fail_firm(town, firm, "payroll")
    for firm in list(town.alive_firms):
        sync_pay(town, firm)
        if not _fund_payroll(town, firm):
            _shed_unpaid(town, firm)
        _pay_wages(town, firm)


# --- the quarter ----------------------------------------------------------------------------------
def quarterly(town) -> None:
    cfg = town.cfg
    for firm in list(town.alive_firms):
        if not firm.alive:
            continue
        review_firm(town, firm)
        grant_shares(town, firm)
        pay_dividends(town, firm)
        raise_money(town, firm)
        check_control(town, firm)
        firm.q_revenue = firm.q_export = firm.q_wages = firm.q_goods = 0
        firm.q_interest = firm.q_capex = firm.q_wear = 0
        if firm.idle_weeks >= cfg.idle_windup_weeks:
            wind_up(town, firm, "idle")
    for agent in town.agents:
        agent.div_quarters.append(agent.div_this_quarter)
        agent.div_this_quarter = 0
        if len(agent.div_quarters) > 8:
            del agent.div_quarters[0]
    resident_founders(town)


def transport_spec(town) -> NeedSpec:
    """Transport as a need: a fixed crew however few ride, a little labour per rider, and
    no trips of its own. Nobody starts with it (Jason, 12/11/2026)."""
    cfg = town.cfg
    per_rider = (cfg.transport_fixed_labour / max(1, cfg.transport_assumed_riders)
                 + cfg.transport_rider_labour)
    price = int(round(per_rider * town.typical_wage() * (1.0 + cfg.overhead_allowance)
                      * (1.0 + cfg.new_need_markup)))
    return NeedSpec(
        name="transport", kind="flow", weight=cfg.invented_weight, essential=False, priority=2,
        service_labour=cfg.transport_rider_labour, goods_per_sub=0.0, make_labour=0.0,
        import_price=0, export_price=0, export_quota=0.0, initial_price=price,
        appeal=1.0, invented=True, salt=0.0, trips_per_week=0.0,
        fixed_labour=cfg.transport_fixed_labour,
    )
