"""The Right to Repair world: what a person does as an owner (Jason, 16/11/2026).

Nothing here runs in the WEF world. Stage 1a: spare time, an appliance set and a home
of one's own, their upkeep, the loan against a home, foreclosure. Rules and the calls
behind each number are in docs/superpowers/specs/2026-11-16-rtr-world-design.md.
"""

from __future__ import annotations

from .entities import Letting, OwnBuild
from .ledger import OUTSIDE
from .places import dist, place_own_unit, plot_free, reach, take_plot, transport_fare, unit_rent
from .production import best_condition, update_condition, upkeep_need
from .subscriptions import (cheapest_prices, ensure_transport, price_paid, sign_up_for_the_rest,
                            unsubscribe)


# --- time ---------------------------------------------------------------------------------------
def spare_hours(cfg, agent) -> float:
    """Hours left in the week after a job and the road. Never less than none."""
    hours = cfg.free_hours - agent.travel_hours
    if agent.role is not None:
        hours -= cfg.job_hours
    return max(0.0, hours)


def start_week(town) -> None:
    """Everyone's hours for the week ahead."""
    cfg = town.cfg
    town.bank_sales_week = 0
    for agent in town.agents:
        agent.spare_hours = spare_hours(cfg, agent)


# --- owning ---------------------------------------------------------------------------------------
def owns(agent, need: str) -> bool:
    """Is the unit they use for this need their own?"""
    unit = agent.unit.get(need)
    return unit is not None and unit.owner is agent


def housed(agent) -> bool:
    """A rented home, or one of their own."""
    return "housing" in agent.subs or owns(agent, "housing")


def home_value(town, unit) -> int:
    """What a home is worth as it stands: the materials to build it, less wear over its
    life, and never under a fifth (as a firm's units are valued)."""
    cfg, spec = town.cfg, unit.spec
    life = spec.life_years * cfg.weeks_per_year
    return int(build_cost(town) * max(0.2, 1.0 - unit.age / life)) if life > 0 else build_cost(town)


def homes_of(town, agent) -> list:
    """Every home they own: the one they live in, if it is theirs, then the ones they let."""
    out = []
    own = agent.unit.get("housing")
    if own is not None and own.owner is agent:
        out.append(own)
    if agent.lets is not None:
        out.extend(agent.lets.units)
    return out


def borrowable(town, agent) -> int:
    """What the bank would still lend an owner against the homes they own: it counts toward
    their cushion. (J) no income, no loan: then it is no cushion."""
    homes = homes_of(town, agent)
    if not homes:
        return 0
    return town.bank.home_credit(agent, 0, owned=sum(home_value(town, u) for u in homes))


def make_private(town, unit, owner) -> None:
    """A landlord's home becomes a private one where it stands (stage 1b). It leaves the
    firm and the block's homes for rent; if it was let, the tenancy ends without anyone
    leaving. The caller says who lives in it."""
    firm, spot, tenant = unit.firm, unit.spot, unit.occupant
    if tenant is not None:
        firm.subs.pop(tenant.id, None)
        firm.unserved.pop(tenant.id, None)
        tenant.subs.pop("housing", None)
        tenant.arrears.pop("housing", None)
        tenant.unit.pop("housing", None)
        unit.occupant = None
        if spot is not None:
            spot.occupied -= 1
            if unit.scale > 1.0:
                spot.better_let -= 1
    firm.units.remove(unit)
    firm.projects = [p for p in firm.projects if p.unit is not unit]   # nobody rebuilds a home that is sold
    if spot is not None:
        spot.units.remove(unit)
        if unit.scale > 1.0:
            spot.better -= 1
        spot.private_units.append(unit)
    unit.firm = None
    unit.owner = owner
    unit.empty_since = None
    unit.bought = True
    town.own_units.append(unit)


# --- what owning costs ----------------------------------------------------------------------------
def parts_price(town, need: str) -> int:
    """Parts at cost: what the outside charges for a unit of the need's good."""
    return town.needs[need].import_price


def own_cost_week(town, agent, need: str, build: bool = True) -> int:
    """What owning costs a week, for setting against a rent: a new unit's upkeep, and with
    `build` the cost of building it spread over its life; goods at the outside price and
    their own hours at what the model says an hour is worth."""
    cfg, spec = town.cfg, town.needs[need]
    goods, labour = spec.upkeep_goods, spec.upkeep_labour
    life = spec.life_years * cfg.weeks_per_year
    if build and life > 0:
        goods += spec.build_goods / life
        labour += spec.build_labour / life
    return int(round(goods * spec.import_price + labour * cfg.job_hours * town.hour_value))


def _bills(town, agent) -> int:
    from .household import dues
    return sum(d[3] for d in dues(town, agent))


def _spare_cash(town, agent) -> int:
    """Their cash beyond four weeks of their bills: what they will put into something of their own."""
    return max(0, agent.cash - 4 * _bills(town, agent))


# --- an appliance set of their own ---------------------------------------------------------------------
def _start_set(town, agent) -> bool:
    """Buy the parts for a set of their own (their cash beyond four weeks of bills, then a
    personal loan for the gap). False if they cannot pay for them."""
    spec = town.needs["appliances"]
    cost = int(round(spec.build_goods * spec.import_price))
    gap = cost - _spare_cash(town, agent)
    if gap > 0:
        if town.bank.person_credit(agent) < gap:
            return False                             # nothing is borrowed unless it buys the parts
        town.bank.lend_person(agent, gap)
    town.ledger.pay(agent, OUTSIDE, cost, "import")
    agent.spend_week += cost
    agent.set_hours_left = spec.build_labour * town.cfg.job_hours
    town.event("own_started", agent=agent, amount=cost, need="appliances")
    return True


def consider_own_set(town, agent) -> None:
    """Someone renting a set starts one of their own when owning would cost clearly less a
    week than their rent and they can pay for the parts."""
    if (agent.set_hours_left is not None or owns(agent, "appliances")
            or "appliances" not in town.needs):
        return
    if "appliances" not in agent.subs:               # no set at all: they build one if they can pay
        _start_set(town, agent)
        return
    rent = price_paid(agent, "appliances")
    if own_cost_week(town, agent, "appliances") < rent * (1.0 - town.cfg.switch_friction):
        _start_set(town, agent)


def _finish_set(town, agent) -> None:
    old = agent.unit.get("appliances")
    if old is not None and old.owner is agent:           # a worn-out set of their own is scrapped
        old.occupant = None
        town.own_units.remove(old)
        agent.unit.pop("appliances")
    elif "appliances" in agent.subs:                     # the rented one goes back
        unsubscribe(town, agent, "appliances", "owns")
    unit = town.new_own_unit(town.needs["appliances"], agent)
    unit.occupant = agent
    agent.unit["appliances"] = unit
    agent.set_hours_left = None
    town.event("own_built", agent=agent, qty=unit.id, need="appliances")


def _hours_wanted(town, agent, hours_left: float, parts_per_hour: float):
    """What someone building would pay a maker for (stage 2): `under`, the price of a maker's
    hour below which it comes to less than an hour of their own, and `short`, whether they
    do not have the hours: the job would take more than a quarter of their spare time."""
    cfg = town.cfg
    under = town.hour_value - parts_per_hour * cfg.maker_margin
    short = hours_left > cfg.quarter_weeks * agent.spare_hours
    return under, short


def _set_builder(town, agent, under: float, short: bool) -> None:
    """Hours on their set bought from someone who builds sets (stage 2). The parts are theirs
    already, so the builder is paid for hours only."""
    from .rtr_makers import buy_hours
    agent.set_hours_left -= buy_hours(town, agent, "set_building", agent.set_hours_left, 0.0,
                                      _spare_cash(town, agent), None if short else under)


def work(town, agent) -> None:
    """Spend the spare hours left after upkeep on what they are building: the set first,
    then the home. In stage 2 a maker's hours may be bought for either."""
    if agent.set_hours_left is not None:
        wanted = _hours_wanted(town, agent, agent.set_hours_left, 0.0) if town.hustles else None
        if agent.spare_hours > 0:                    # their own hours first: they cost them nothing
            use = min(agent.spare_hours, agent.set_hours_left)
            agent.set_hours_left -= use
            agent.spare_hours -= use
        if wanted is not None and agent.set_hours_left > 1e-9:
            _set_builder(town, agent, *wanted)       # then a builder's, for hours they are short of or that cost less
        if agent.set_hours_left <= 1e-9:
            _finish_set(town, agent)
    if agent.build is not None and (agent.spare_hours > 0 or town.hustles):
        _work_on_home(town, agent)


# --- a home of their own, built on a plot ------------------------------------------------------------
def build_cost(town) -> int:
    """The materials for a home, at the outside price."""
    spec = town.needs["housing"]
    return int(round(spec.build_goods * spec.import_price))


def consider_building(town, agent) -> None:
    """A tenant (or someone with no home) who has a job starts a home of their own when the
    bank's loan and their cash beyond four weeks of bills cover the materials, owning would
    cost clearly less a week than their rent, and there is a plot."""
    cfg = town.cfg
    if ("housing" not in town.needs or owns(agent, "housing") or agent.build is not None
            or agent.role is None):
        return
    cost = build_cost(town)
    rent = price_paid(agent, "housing") if "housing" in agent.subs else None
    if _build_loan(town, _spare_cash(town, agent), town.bank.home_credit(agent, cost), rent) is None:
        return
    spot = None
    if town.map is not None:
        work = agent.employer.spot if agent.employer is not None and agent.role != "ceo" else None
        spot = take_plot(town, work, reach(town, agent))
        if spot is None:
            return                               # no land left that they could get to work from
    spec = town.needs["housing"]
    agent.build = OwnBuild(spec.build_labour * cfg.job_hours, spec.build_goods, spot)
    town.event("home_started", agent=agent, amount=cost, qty=spot.id if spot is not None else None)


def _build_loan(town, spare: int, credit: int, rent):
    """What someone would borrow to build a home of their own, or None if they cannot or
    would not: the bank's loan (its share of the materials, `mortgage_ltv`) and their spare cash
    must cover the materials, and for someone who rents, owning must cost clearly less a
    week than their rent."""
    cfg = town.cfg
    cost = build_cost(town)
    loan = min(credit, int(cfg.mortgage_ltv * cost))
    if loan + spare < cost:
        return None
    if rent is not None:
        weekly = town.bank.home_first_payment(loan) + own_cost_week(town, None, "housing", build=False)
        if weekly >= rent * (1.0 - cfg.switch_friction):
            return None
    return loan


def build_weekly(town, agent):
    """What a home they built themselves would cost them a week (the first payment on the
    loan, and the upkeep), or None if they could not or would not start one now: the tests
    of `consider_building`, and a plot they could get to work from."""
    if ("housing" not in town.needs or owns(agent, "housing") or agent.build is not None
            or agent.role is None):
        return None
    rent = price_paid(agent, "housing") if "housing" in agent.subs else None
    loan = _build_loan(town, _spare_cash(town, agent), town.bank.home_credit(agent, build_cost(town)), rent)
    if loan is None:
        return None
    if town.map is not None:
        work = agent.employer.spot if agent.employer is not None and agent.role != "ceo" else None
        if not plot_free(town, work, reach(town, agent)):
            return None
    return town.bank.home_first_payment(loan) + own_cost_week(town, agent, "housing", build=False)


def _rather_build(town, agent, borrow: int) -> bool:
    """The design: of buying, building and renting they take the cheapest by weekly cost
    (loan payment and upkeep). Would a home they built cost them less a week than buying
    with this loan? The upkeep is the same either way."""
    building = build_weekly(town, agent)
    return (building is not None and building
            < town.bank.home_first_payment(borrow) + own_cost_week(town, agent, "housing", build=False))


def _work_on_home(town, agent) -> None:
    """Hours on the home. Each hour buys its share of the materials from outside: the
    bank's share (`mortgage_ltv`) while it will lend, the rest from their cash. An hour they cannot
    buy materials for is not worked."""
    cfg, build = town.cfg, agent.build
    spec = town.needs["housing"]
    per_hour = spec.build_goods / (spec.build_labour * cfg.job_hours)
    wanted = None
    if town.hustles:                             # stage 2: reckoned on the hours they have before they work them
        wanted = _hours_wanted(town, agent, build.hours_left, per_hour * spec.import_price)
    _own_hours_on_home(town, agent, per_hour)    # their own hours first: only the materials cost them money
    if wanted is not None and build.hours_left > 1e-6:
        _home_builder(town, agent, per_hour, *wanted)    # then a builder's, with what money is left
    if build.hours_left <= 1e-6:
        _finish_home(town, agent)


def _own_hours_on_home(town, agent, per_hour: float) -> None:
    """Their own hours on the home, each buying its share of the materials."""
    cfg, build = town.cfg, agent.build
    spec = town.needs["housing"]
    hours = min(agent.spare_hours, build.hours_left)
    full = int(round(hours * per_hour * spec.import_price))
    total = build_cost(town)
    owned = sum(home_value(town, u) for u in homes_of(town, agent))   # one loan on all their homes
    share, credit = cfg.mortgage_ltv, town.bank.home_credit(agent, total, owned)
    cash = _spare_cash(town, agent)              # they keep four weeks of bills in hand, as at the start
    can = min(full, int(cash / (1.0 - share))) if share < 1.0 else full
    if int(share * can) > credit:                # the bank will not lend its whole share: more from cash
        can = min(full, cash + credit)
    if can <= 0:
        return
    if can < full:
        hours = hours * can / full
    build.borrowed += town.bank.lend_home(agent, min(int(share * can), credit), total, log=False, owned=owned)
    town.ledger.pay(agent, OUTSIDE, can, "import")
    agent.spend_week += can
    build.spent += can
    build.hours_left -= hours
    build.goods_left = max(0.0, build.goods_left - hours * per_hour)
    agent.spare_hours -= hours


def _home_builder(town, agent, per_hour: float, under: float, short: bool) -> None:
    """Hours on their home bought from people who build homes (stage 2), cheapest first, once
    their own hours are worked: while a builder's hour comes to less than their own, or while
    they do not have the hours. The builder brings the materials and charges for them with the
    margin; the bank lends its share of the materials to the owner as it does for their
    own hours, and they pay the rest from their cash beyond four weeks of bills."""
    from .rtr_makers import hour_makers, sell_hours
    cfg, build = town.cfg, agent.build
    materials = per_hour * town.needs["housing"].import_price        # cents of materials an hour
    total, share = build_cost(town), cfg.mortgage_ltv
    owned = sum(home_value(town, u) for u in homes_of(town, agent))
    for hustle in hour_makers(town, agent, "home_building", None if short else under):
        if build.hours_left <= 1e-6:
            break
        rate = hustle.price + materials * (1.0 + cfg.maker_margin)
        take = min(build.hours_left, hustle.hours - hustle.sold)
        credit, cash = town.bank.home_credit(agent, total, owned), _spare_cash(town, agent)
        if take * rate - min(share * take * materials, credit) > cash:      # fewer: what cash and the bank pay for
            take = cash / (rate - share * materials)
            if share * take * materials > credit:
                take = (cash + credit) / rate
        if take <= 1e-9:
            break
        build.borrowed += town.bank.lend_home(agent, min(int(share * take * materials), credit), total,
                                              log=False, owned=owned)
        build.spent += sell_hours(town, hustle, agent, take, materials, "housing")
        build.hours_left -= take
        build.goods_left = max(0.0, build.goods_left - take * per_hour)


def _finish_home(town, agent) -> None:
    build = agent.build
    unit = town.new_own_unit(town.needs["housing"], agent)
    if build.spot is not None:
        place_own_unit(build.spot, unit)
    if build.to_let:                             # stage 1b: built to let, at the going rent
        agent.build = None
        put_to_let(town, unit, letting_of(town, agent), going_rent(town, build.spot))
        town.event("home_built", agent=agent, amount=build.spent, qty=unit.id, loan=agent.home_loan,
                   to_let=True, rent=unit.rent,
                   **({"spot": build.spot.id} if build.spot is not None else {}))
        return
    if "housing" in agent.subs:                  # the rented home goes back
        unsubscribe(town, agent, "housing", "owns")
    unit.occupant = agent
    agent.unit["housing"] = unit
    agent.build = None
    town.event("home_built", agent=agent, amount=build.spent, qty=unit.id, loan=agent.home_loan,
               **({"spot": build.spot.id} if build.spot is not None else {}))


def _repairer(town, agent, hours: float, cost: int, need=None) -> float:
    """Hours of a unit's upkeep bought from a repairer (stage 2): all of them from any repairer
    who comes to less than doing it themselves, and beyond that the hours they are short of
    this week. Someone of the owner class buys all of them from whoever will do them, the
    cheapest first, whatever the price. Only with cash beyond four weeks of bills. Returns
    the hours bought."""
    from .rtr_makers import buy_hours
    cfg = town.cfg
    parts = cost / hours
    if cfg.owners_pay_any_price and agent.klass == "owner":
        # Jason, 18/11/2026: the owner class "needs more time than money": anyone, at any price
        return buy_hours(town, agent, "repair", hours, parts, _spare_cash(town, agent), need=need)
    under = town.hour_value - parts * cfg.maker_margin   # a maker's hour below this comes to less than their own
    got = buy_hours(town, agent, "repair", hours, parts, _spare_cash(town, agent), under, need)
    short = hours - got - agent.spare_hours
    if short > 1e-9:
        got += buy_hours(town, agent, "repair", short, parts, _spare_cash(town, agent), need=need)
    return got


def keep(town, agent) -> None:
    """A week of upkeep on what they own: their hours and parts at cost. With too few of
    either it wears, as a neglected unit does. A set past keeping is replaced."""
    cfg = town.cfg
    theirs = [(need, agent.unit[need]) for need in ("housing", "appliances")
              if need in agent.unit and agent.unit[need].owner is agent]
    if agent.lets is not None:                       # then the homes they let (stage 1b)
        theirs.extend(("housing", unit) for unit in agent.lets.units)
    for need, unit in theirs:
        labour, goods = upkeep_need(cfg, unit)
        hours = labour * cfg.job_hours
        cost = int(round(goods * parts_price(town, need)))
        bought = _repairer(town, agent, hours, cost, need) if town.hustles and hours > 0 else 0.0
        if bought > 0:                               # stage 2: a repairer did those hours, parts and all
            rest = max(0.0, hours - bought)
            cost = int(round(cost * rest / hours))
        else:
            rest = hours
        worked = min(agent.spare_hours, rest)
        paid = min(agent.cash, cost)
        if paid > 0:
            town.ledger.pay(agent, OUTSIDE, paid, "import")
            agent.spend_week += paid
        agent.spare_hours -= worked
        done = min(1.0, worked / rest if rest > 0 else 1.0, paid / cost if cost > 0 else 1.0)
        if bought > 0:
            done = min(1.0, (bought + done * rest) / hours)
        unit.age += 1
        update_condition(cfg, unit, done)
        if (need == "appliances" and agent.set_hours_left is None
                and best_condition(cfg, unit) < cfg.replace_below):
            _start_set(town, agent)


# --- the week ---------------------------------------------------------------------------------------
def after_bills(town) -> None:
    """Each week, once the bills are paid: upkeep of what people own, then their building."""
    late = []
    for agent in town.agents:
        keep(town, agent)
        if agent.hustle is not None and agent.hustle.spec is None:
            late.append(agent)                       # stage 2: their hours are for customers first
        else:
            work(town, agent)
    for agent in late:
        work(town, agent)                            # a repairer or builder builds with the hours nobody bought
    _bank_rents(town)
    foreclosures(town)
    sell_foreclosed(town)


def quarter(town) -> None:
    """At the end of a quarter people look at owning."""
    landlord_sales(town)
    for unit in town.to_let:                         # a loose home with no tenant follows the going rent
        if unit.owner is not None or unit.firm is not town.bank_lets:
            unit.rent = max(1, going_rent(town, unit.spot))
    for agent in list(town.agents):
        consider_own_set(town, agent)
        consider_building(town, agent)
        consider_building_to_let(town, agent)


# --- foreclosure, and the sale for the debt ----------------------------------------------------------
def bank_lets(town) -> Letting:
    """The Letting of homes the bank holds that have tenants in them."""
    if town.bank_lets is None:
        town.bank_lets = Letting(None, town.needs["housing"], 0)
    return town.bank_lets


def _bank_takes(town, unit, debt: int) -> None:
    """A home passes to the bank with this much owed on it. A tenant in it stays and pays
    their rent to the bank from now on."""
    tenant, old = unit.occupant, unit.firm
    if old is not None:                              # a home that was let: out of its owner's Letting
        old.units.remove(unit)
        if tenant is not None:
            old.subs.pop(tenant.id, None)
    if tenant is not None and tenant is not unit.owner:
        holder = bank_lets(town)
        holder.units.append(unit)
        holder.subs[tenant.id] = tenant
        tenant.subs["housing"] = holder
        unit.firm = holder
    else:
        unit.firm = None
        unit.rent = 0
        unit.occupant = None
        if unit in town.to_let:
            town.to_let.remove(unit)
    unit.owner = None
    unit.debt = unit.ask = max(1, debt)
    unit.since = town.week
    town.foreclosed.append(unit)


def foreclose(town, agent) -> None:
    """The bank takes a home for its loan (Jason: a home borrowed against can be
    foreclosed). One thing each time. First a home they are still building while they own
    another: it is lost with its plot and what the bank lent on it written off, since
    nothing stands to sell. Then the newest home they let, with its share of the loan by
    value, and its tenant stays; the home they live in last. A home taken is then on offer
    for the debt owed. Someone with no home but the one they are building loses it and the
    whole debt is written off. They are refused credit as after any default."""
    cfg = town.cfg
    owed = agent.home_loan
    homes = homes_of(town, agent)
    own = agent.unit.get("housing")
    unit = spot = None
    debt = owed
    if agent.build is not None and homes:
        build, agent.build = agent.build, None
        spot = build.spot
        if spot is not None:
            spot.plots_reserved -= 1
        debt = min(owed, build.borrowed)
        if debt > 0:
            town.bank._write_off(debt)
            town.event("writeoff", agent=agent, amount=debt)
        agent.shock(cfg, cfg.shock_default)
    elif agent.lets is not None and agent.lets.units:
        unit = max(agent.lets.units, key=lambda u: u.id)
        total = sum(home_value(town, u) for u in homes)
        debt = round(owed * home_value(town, unit) / total) if total > 0 else owed
        _bank_takes(town, unit, debt)
        agent.shock(cfg, cfg.shock_default)
    elif own is not None and own.owner is agent:
        unit = own
        agent.unit.pop("housing")
        _bank_takes(town, unit, debt)
        agent.shock(cfg, cfg.shock_eviction)
    else:
        if agent.build is not None:
            spot = agent.build.spot
            if spot is not None:
                spot.plots_reserved -= 1
            agent.build = None
        if debt > 0:
            town.bank._write_off(debt)
            town.event("writeoff", agent=agent, amount=debt)
        agent.shock(cfg, cfg.shock_eviction)
    if unit is not None:
        spot = unit.spot
    agent.home_loan = owed - debt
    agent.home_pay = -(-agent.home_loan // cfg.mortgage_weeks) if agent.home_loan > 0 else 0
    agent.home_missed = 0
    town.foreclosures_total += 1
    agent.credit_block_until = town.week + cfg.default_block_weeks
    town.event("foreclosed", agent=agent, amount=debt, qty=unit.id if unit is not None else None,
               **({"spot": spot.id} if spot is not None else {}),
               **({"tenant": unit.occupant.id} if unit is not None and unit.occupant is not None else {}))


def foreclosures(town) -> None:
    """Anyone who has missed `grace_weeks` payments in a row on the loan against their home."""
    limit = town.cfg.grace_weeks
    for agent in town.agents:
        if agent.home_loan > 0 and agent.home_missed >= limit:
            foreclose(town, agent)


def _terms(town, price: int, spare: int, cap: int, rent, upkeep: int):
    """What a buyer borrows for a home at this price, or None if they cannot or would not buy:
    their spare cash first; the rest within the bank's share of the price (`mortgage_ltv`: all
    of it since Jason's ruling of 18/11/2026, four fifths before) and what their income allows; and, for someone who rents, owning must cost clearly less a week than the rent."""
    cfg = town.cfg
    borrow = max(0, price - spare)
    if borrow > min(int(cfg.mortgage_ltv * price), cap):
        return None
    if rent is not None and town.bank.home_first_payment(borrow) + upkeep >= rent * (1.0 - cfg.switch_friction):
        return None
    return borrow


def buyer_terms(town, agent, price: int, rent=None):
    """`_terms` for one person, worked out afresh."""
    return _terms(town, price, _spare_cash(town, agent), town.bank.home_cap(agent), rent,
                  own_cost_week(town, agent, "housing", build=False))


def _buyers(town) -> list:
    """Who could buy a foreclosed home this week: a job, no home of their own, not building
    one. For each: their cash beyond four weeks of bills, the most their income lets them
    owe, their rent if they rent, where they work and how far they can get."""
    bank, out = town.bank, []
    for agent in town.agents:
        if agent.role is None or agent.build is not None or owns(agent, "housing"):
            continue
        work = agent.employer.spot if agent.employer is not None and agent.role != "ceo" else None
        rent = price_paid(agent, "housing") if "housing" in agent.subs else None
        out.append([agent, _spare_cash(town, agent), bank.home_cap(agent), rent, work, reach(town, agent), None])
    return out


def _buyer_for(town, unit, buyers: list):
    """The first of them, in order of arrival, who can reach their work from it, can pay the
    asking price with the bank's loan and their spare cash, for whom owning it would cost
    clearly less a week than their rent (anyone with no home will take it), and for whom
    building a home would not cost less a week than buying this one.
    Returns (place in the list, what they borrow), or None."""
    return _first_buyer(town, unit, unit.ask, buyers)


def _first_buyer(town, unit, price: int, buyers: list):
    cfg = town.cfg
    upkeep = own_cost_week(town, None, "housing", build=False)
    for i, entry in enumerate(buyers):
        agent, spare, cap, rent, work, far = entry[:6]
        if unit.spot is not None and work is not None and dist(unit.spot, work) > far:
            continue
        borrow = _terms(town, price, spare, cap, rent, upkeep)
        if borrow is None:
            continue
        if entry[6] is None:                         # what building would cost them a week; False if they cannot
            credit = max(0, min(int(cfg.mortgage_ltv * build_cost(town)), cap) - agent.home_loan)
            loan = _build_loan(town, spare, credit, rent)
            can = loan is not None and (town.map is None or plot_free(town, work, far))
            entry[6] = town.bank.home_first_payment(loan) + upkeep if can else False
        if entry[6] is not False and entry[6] < town.bank.home_first_payment(borrow) + upkeep:
            continue                                 # building would cost them less a week: they build
        return i, borrow
    return None


def _sell(town, unit, buyer, borrow: int) -> None:
    if borrow > 0:
        town.bank.lend_home(buyer, borrow, unit.ask)
    price, debt = _pay_bank(town, buyer, unit, {"agent": buyer})   # the bank's loss is taken once, when it sells
    if unit.firm is not None:                        # a home the bank was letting: the tenancy ends in place
        holder = unit.firm
        holder.units.remove(unit)
        if unit.occupant is not None:
            holder.subs.pop(unit.occupant.id, None)
            unit.occupant.subs.pop("housing", None)
            unit.occupant.arrears.pop("housing", None)
            unit.occupant.unit.pop("housing", None)
        unit.firm = None
    unit.rent = 0
    if unit in town.to_let:
        town.to_let.remove(unit)
    if "housing" in buyer.subs:                      # the home they rented elsewhere goes back
        unsubscribe(town, buyer, "housing", "owns")
    unit.owner = unit.occupant = buyer
    buyer.unit["housing"] = unit
    unit.debt = unit.ask = 0
    unit.since = None
    town.foreclosed.remove(unit)
    town.event("foreclosed_sold", agent=buyer, amount=price, qty=unit.id, debt=debt,
               **({"spot": unit.spot.id} if unit.spot is not None else {}))


def sell_foreclosed(town) -> None:
    """Each home the bank holds is offered for what it asks, in Jason's order: a renter who
    can pay or borrow for it (the sitting tenant of a let home; anyone with a job and no
    home of their own for an empty one); then a resident who owns their home, who lets it;
    then a landlord firm. A tenant stays through the sale. Unsold, it ages and wears, and
    the price falls each quarter."""
    if not town.foreclosed:
        return
    cfg = town.cfg
    buyers = _buyers(town)
    owners = None
    wanted = home_wanted(town)
    for unit in list(town.foreclosed):
        unit.age += 1
        update_condition(cfg, unit, 0.0)             # nobody keeps an empty home up
        held = town.week - unit.since
        if held > 0 and held % cfg.quarter_weeks == 0:
            unit.ask = max(1, int(unit.ask * (1.0 - cfg.foreclosed_price_drop)))
        tenant = unit.occupant
        if tenant is not None:                       # a let home: only its tenant may buy it to live in
            if tenant.build is None and not owns(tenant, "housing"):
                borrow = buyer_terms(town, tenant, unit.ask, unit.rent)
                if borrow is not None and not _rather_build(town, tenant, borrow):
                    buyers[:] = [b for b in buyers if b[0] is not tenant]
                    _sell(town, unit, tenant, borrow)
                    continue
        else:
            found = _buyer_for(town, unit, buyers)
            if found is not None:
                i, borrow = found
                _sell(town, unit, buyers.pop(i)[0], borrow)
                owners = None                        # they may have left a home someone lets: that owner's
                continue                             # income, and what the bank will lend them, has changed
        if tenant is None and not wanted:
            continue                                 # an empty home is bought to let, by a person or a firm,
        if owners is None:                           # only when there is a sign that a home is wanted
            owners = _owners(town)
        rent = unit.rent if tenant is not None else going_rent(town, unit.spot)
        found = _first_owner(town, unit.ask, rent, owners)   # a resident who owns, who lets it
        if found is not None:
            i, borrow = found
            _sell_to_let(town, unit, owners.pop(i), borrow)
            continue
        _landlord_takes(town, unit)                  # a landlord firm


# --- Jason, 18/11/2026: a newcomer may buy --------------------------------------------------------------
def newcomer_keeps(town) -> int:
    """The cash a newcomer holds back when they buy: four weeks of the base needs other than a
    home at the cheapest prices on offer, as a resident holds back four weeks of their bills."""
    cheapest = cheapest_prices(town)
    return 4 * sum(cheapest.get(name, 0) for name, spec in town.needs.items()
                   if not spec.invented and name != "housing")


def home_for_newcomer(town, cash: int, income: int, work=None):
    """Jason: a newcomer may "rent anything that's vacant or buy anything that's available as
    long as they have ... good enough income". The home someone arriving with this cash, for
    this much a week, would buy when nothing is free to rent: the cheapest empty home the bank
    holds that they can get to `work` from (a walk, or a ride where one is on offer, as for a
    rented home) and can pay for as anyone in town does: their cash beyond what they hold
    back, the rest borrowed within the bank's share of the price and what their income allows.
    Returns (home, what they borrow), or None."""
    cfg = town.cfg
    if not (cfg.rtr and cfg.newcomers_buy and town.foreclosed):
        return None
    spare = max(0, cash - newcomer_keeps(town))
    cap = town.bank.home_cap_income(income)
    upkeep = own_cost_week(town, None, "housing", build=False)
    ride = None
    best = None
    for unit in town.foreclosed:
        if unit.occupant is not None:                # a let home is only its tenant's to buy
            continue
        if work is not None and unit.spot is not None:
            blocks = dist(unit.spot, work)
            if blocks > cfg.walk_range:
                if ride is None:
                    ride = transport_fare(town) is not None
                if not ride or blocks > cfg.walk_range * cfg.transport_speed:
                    continue
        borrow = _terms(town, unit.ask, spare, cap, None, upkeep)
        if borrow is not None and (best is None or (unit.ask, unit.id) < (best[0].ask, best[0].id)):
            best = (unit, borrow)
    return best


def arrive_as_owner(town, agent, unit, borrow: int, income: int, work=None) -> None:
    """A newcomer buys the home `home_for_newcomer` found and moves in; then the other base
    needs, as any arrival. The bank lends on the job they have come for."""
    wage, agent.wage = agent.wage, income
    _sell(town, unit, agent, borrow)
    agent.wage = wage
    if work is not None and unit.spot is not None and dist(unit.spot, work) > town.cfg.walk_range:
        ensure_transport(town, agent)                # the home is a ride from work: the ride comes with it
    sign_up_for_the_rest(town, agent)


# --- stage 1b, part B: the rest of the order, and homes sold with their tenants ---------------------------
def home_wanted(town) -> bool:
    """The sign that a home is wanted: a newcomer was turned away from town for want of one
    within the last quarter."""
    return town.no_home_week is not None and town.week - town.no_home_week < town.cfg.quarter_weeks


def _owners(town) -> list:
    """Residents who could take on a home to let, in order of arrival: they own the home
    they live in, are not building, and are not behind on their loan. Each is
    [who, value of the homes they own, spare cash, the most their income lets them owe];
    the last three are worked out only when first needed."""
    return [[a, None, None, None] for a in town.agents
            if a.build is None and a.home_missed == 0 and owns(a, "housing")]


def _owner_terms(town, entry: list, price: int, rent: int, upkeep: int):
    """What this owner would borrow to buy a home to let at this price, or None: the bank's
    credit on all they own and this home (the bank's share of their value, within what their
    income allows, less what they owe), with their spare cash, covers the price; and the
    rent covers the first payment on what they borrow and the upkeep, with `maker_margin`
    to spare."""
    cfg, agent = town.cfg, entry[0]
    if entry[1] is None:
        entry[1] = sum(home_value(town, u) for u in homes_of(town, agent))
    room = max(0, int(cfg.mortgage_ltv * (price + entry[1])) - agent.home_loan)   # the bank's share, less what they owe
    if agent.cash + room < price:
        return None                                  # (their spare cash is never more than their cash)
    if entry[2] is None:
        entry[2] = _spare_cash(town, agent)
    borrow = max(0, price - entry[2])
    if borrow > room:
        return None
    if rent < (town.bank.home_first_payment(borrow) + upkeep) * (1.0 + cfg.maker_margin):
        return None
    if borrow > 0:
        if entry[3] is None:
            entry[3] = town.bank.home_cap(agent)
        if borrow > max(0, entry[3] - agent.home_loan):  # and within what their income lets them owe
            return None
    return borrow


def letting_terms(town, agent, price: int, rent: int):
    """`_owner_terms` for one person, worked out afresh."""
    return _owner_terms(town, [agent, None, None, None], price, rent,
                        own_cost_week(town, agent, "housing", build=False))


def _first_owner(town, price: int, rent: int, owners: list):
    """The first of `_owners` who can and would buy a home to let at this price and rent.
    Returns (place in the list, what they borrow), or None."""
    upkeep = own_cost_week(town, None, "housing", build=False)
    if rent < upkeep * (1.0 + town.cfg.maker_margin):
        return None                                  # the rent would not cover the upkeep for anyone
    for i, entry in enumerate(owners):
        borrow = _owner_terms(town, entry, price, rent, upkeep)
        if borrow is not None:
            return i, borrow
    return None


def _keep_tenant(town, unit, provider, tenant, rent: int, arrears: int) -> None:
    """The home is let by `provider` from now on, at a rent of its own, and the tenant in it
    stays: no week is lost and what they owe in missed rents goes with them."""
    unit.firm = provider
    if unit not in provider.units:
        provider.units.append(unit)
    unit.rent = max(1, int(rent))
    unit.occupant = tenant
    unit.empty_since = None
    tenant.unit["housing"] = unit
    tenant.subs["housing"] = provider
    tenant.arrears["housing"] = arrears
    provider.subs[tenant.id] = tenant


def _let_by(town, unit, provider, tenant, rent: int, arrears: int) -> None:
    """Whoever bought it lets it: to the tenant in it at their rent, or, empty, at the going
    rent for its place."""
    if tenant is not None:
        _keep_tenant(town, unit, provider, tenant, rent, arrears)
    else:
        put_to_let(town, unit, provider, going_rent(town, unit.spot))


def _firm_holds(town, unit, firm, tenant, rent: int, arrears: int) -> None:
    """A landlord firm holds a single home off its blocks' books: it stands where it stood
    and is let at a rent of its own."""
    if unit in town.own_units:
        town.own_units.remove(unit)
    unit.owner = None
    _let_by(town, unit, firm, tenant, rent, arrears)


def _pay_bank(town, payer, unit, who: dict):
    """The asking price goes to the bank; what it was owed beyond that is its loss."""
    price, debt = unit.ask, unit.debt
    town.ledger.pay(payer, OUTSIDE, price, "loan_recovery")
    town.bank_sales_week += price
    if debt > price:
        town.bank._write_off(debt - price)
        town.event("writeoff", amount=debt - price, **who)
    return price, debt


def _leave_bank(town, unit):
    """A home the bank held is sold and leaves its books. Returns (tenant, rent, missed
    rents) for whoever lets it next: a tenant in it is not moved."""
    holder, tenant, rent = unit.firm, unit.occupant, unit.rent
    arrears = tenant.arrears.get("housing", 0) if tenant is not None else 0
    if holder is not None:                           # the bank was letting it
        holder.units.remove(unit)
        if tenant is not None:
            holder.subs.pop(tenant.id, None)
    if unit in town.to_let:
        town.to_let.remove(unit)
    unit.firm = None
    unit.rent = 0
    unit.debt = unit.ask = 0
    unit.since = None
    town.foreclosed.remove(unit)
    return tenant, rent, arrears


def _sold_event(unit, tenant) -> dict:
    out = {"to_let": True}
    if tenant is not None:
        out["tenant"] = tenant.id
    if unit.spot is not None:
        out["spot"] = unit.spot.id
    return out


def _sell_to_let(town, unit, entry: list, borrow: int) -> None:
    """A resident who owns buys a home the bank holds, and lets it."""
    buyer = entry[0]
    if borrow > 0:
        town.bank.lend_home(buyer, borrow, unit.ask, owned=entry[1])
    price, debt = _pay_bank(town, buyer, unit, {"agent": buyer})
    tenant, rent, arrears = _leave_bank(town, unit)
    unit.owner = buyer
    _let_by(town, unit, letting_of(town, buyer), tenant, rent, arrears)
    town.event("foreclosed_sold", agent=buyer, amount=price, qty=unit.id, debt=debt, loan=borrow,
               **_sold_event(unit, tenant))


def _firm_worth(town, firm, unit, rent: int) -> int:
    """What a home is worth to a landlord firm: ten years of its rent after upkeep."""
    return int(town.cfg.horizon_value_cap * (rent - _firm_upkeep(town, firm, unit)))


def _firm_can_pay(town, firm, price: int) -> bool:
    return firm.cash - int(town.cfg.reserve_weeks * firm.last_opex) >= price


def _richest_landlord(town, but=None):
    best = None
    for firm in town.firms_for("housing"):
        if firm is not but and (best is None or firm.cash > best.cash):
            best = firm
    return best


def _landlord_takes(town, unit) -> bool:
    """The last of Jason's order: a landlord firm. A home on a landlord's own block goes to
    that landlord or to none; any other to the landlord with the most cash. It buys when
    the price is no more than ten years of the rent after upkeep and its cash beyond its
    reserve covers it. An empty home on its own block is a home of the block again; any
    other it holds as a single home, and a tenant stays."""
    spot, tenant = unit.spot, unit.occupant
    if spot is not None and spot.kind == "homes" and spot.user is not None:
        if spot.owner is not spot.user:
            return False                             # a block on leased land: nobody
        firm = spot.user
        if tenant is None:
            return _landlord_buys_back(town, unit)
    else:
        firm = _richest_landlord(town)
        if firm is None:
            return False
    rent = unit.rent if tenant is not None else going_rent(town, spot)
    if unit.ask > _firm_worth(town, firm, unit, rent) or not _firm_can_pay(town, firm, unit.ask):
        return False
    price, debt = _pay_bank(town, firm, unit, {"firm": firm})
    tenant, rent, arrears = _leave_bank(town, unit)
    _firm_holds(town, unit, firm, tenant, rent, arrears)
    town.event("foreclosed_sold", firm=firm, amount=price, qty=unit.id, debt=debt, **_sold_event(unit, tenant))
    return True


def scrap_single_homes(town, firm) -> None:
    """A landlord that closes with no rival to take it over scraps its homes; the single
    homes it held off its blocks go the same way, and their plots are free again."""
    for unit in firm.units:
        if unit.rent > 0:
            if unit in town.to_let:
                town.to_let.remove(unit)
            if unit.spot is not None and unit in unit.spot.private_units:
                unit.spot.private_units.remove(unit)


# --- stage 1b, part A: buying from a landlord ----------------------------------------------------------
def needs_cash(town, firm) -> bool:
    """Is the firm short: its cash under its usual reserve, or a loan or ground rent payment missed?"""
    return (firm.cash < town.cfg.reserve_weeks * firm.last_opex
            or firm.loan_missed > 0 or firm.rent_missed > 0)


def unit_value(town, firm, unit) -> int:
    """What a firm's unit is worth as it stands: the cost of building it, less wear."""
    return firm.units_value(town.cfg, [unit])


def _firm_upkeep(town, firm, unit) -> float:
    labour, goods = upkeep_need(town.cfg, unit)
    return labour * firm.wage + goods * firm.goods_cost()


def let_price(town, firm, unit) -> int:
    """What a landlord asks for a let home (Jason: it sells when the price is worth more than
    the rent it would collect): ten years of its rent after upkeep, never less than its value."""
    net = unit_rent(unit) - _firm_upkeep(town, firm, unit)
    return max(unit_value(town, firm, unit), int(town.cfg.horizon_value_cap * net))


def _book_gain(firm, gain: int) -> None:
    """The gain over a home's value is the landlord's income (the rest is its capital coming
    back). The quarter's sales come after the quarter's review, so the gain is counted in
    the week's record and in the quarter that has just begun."""
    if gain > 0:
        firm.w_revenue += gain
        firm.q_revenue += gain


def _own_land(firm, unit) -> bool:
    """Homes on land the landlord only leases are not sold. A single home it holds off its
    blocks has its own plot."""
    return unit.rent > 0 or unit.spot is None or unit.spot.owner is firm


def _leave_firm(town, firm, unit):
    """A home leaves the landlord firm that held it and stands where it stood, nobody's yet.
    Returns (tenant, rent, missed rents): the tenancy ends without anyone leaving, and
    whoever lets it next takes the tenant on."""
    tenant = unit.occupant
    rent = price_paid(tenant, "housing") if tenant is not None else 0
    arrears = tenant.arrears.get("housing", 0) if tenant is not None else 0
    if unit.rent <= 0:                               # a home of one of its blocks
        make_private(town, unit, None)
        return tenant, rent, arrears
    firm.units.remove(unit)                          # a single home it held
    firm.projects = [p for p in firm.projects if p.unit is not unit]
    if tenant is not None:
        firm.subs.pop(tenant.id, None)
        firm.unserved.pop(tenant.id, None)
        tenant.subs.pop("housing", None)
        tenant.arrears.pop("housing", None)
        tenant.unit.pop("housing", None)
        unit.occupant = None
    elif unit in town.to_let:
        town.to_let.remove(unit)
    unit.firm = None
    unit.rent = 0
    unit.empty_since = None
    town.own_units.append(unit)
    return tenant, rent, arrears


def _buy_from_firm(town, firm, unit, buyer, price: int, borrow: int, source: str) -> None:
    """The sale of a landlord's home to a person who will live in it. The gain over the
    home's value is the landlord's income; the rest is its capital coming back."""
    value = unit_value(town, firm, unit)
    if borrow > 0:
        town.bank.lend_home(buyer, borrow, price)
    town.ledger.pay(buyer, firm, price, "home_sale")
    _book_gain(firm, price - value)
    if buyer.unit.get("housing") is not unit and "housing" in buyer.subs:
        unsubscribe(town, buyer, "housing", "owns")      # the home they rented elsewhere goes back
    _leave_firm(town, firm, unit)
    unit.owner = buyer
    buyer.unit["housing"] = unit
    unit.occupant = buyer
    town.bank.repay_excess(firm)                         # what it sold no longer secures its loan
    town.event("home_bought", agent=buyer, firm=firm, amount=price, qty=unit.id, loan=borrow, value=value,
               **{"from": source}, **({"spot": unit.spot.id} if unit.spot is not None else {}))


def offer_to_tenant(town, firm, unit) -> bool:
    """A landlord offers a let home to the tenant in it: at its value if the landlord is
    short of cash, otherwise at ten years of its rent. The tenant buys if the bank's loan
    and their spare cash cover it, owning would cost clearly less than their rent, and
    building a home would not cost them less a week."""
    tenant = unit.occupant
    if tenant is None or unit.firm is not firm or tenant.build is not None or not _own_land(firm, unit):
        return False
    price = unit_value(town, firm, unit) if needs_cash(town, firm) else let_price(town, firm, unit)
    borrow = buyer_terms(town, tenant, price, price_paid(tenant, "housing"))
    if borrow is None or _rather_build(town, tenant, borrow):
        return False
    _buy_from_firm(town, firm, unit, tenant, price, borrow, "tenant")
    return True


def make_rented(town, unit, firm) -> None:
    """The reverse of `make_private`, for a home standing on this firm's block: it is the
    landlord's again, empty and for rent."""
    spot = unit.spot
    spot.private_units.remove(unit)
    spot.units.append(unit)
    if unit.scale > 1.0:
        spot.better += 1
    town.own_units.remove(unit)
    firm.units.append(unit)
    unit.firm = firm
    unit.bought = False
    unit.owner = unit.occupant = None
    unit.empty_since = town.week


def _landlord_buys_back(town, unit) -> bool:
    """An empty foreclosed home nobody else took, standing on a landlord's own block: that
    landlord buys it from the bank when the price is no more than ten years of the rent it
    would bring, after upkeep, and its cash beyond its reserve covers it. It is a home of
    the block again."""
    spot = unit.spot
    if spot is None or spot.kind != "homes" or spot.user is None or spot.owner is not spot.user:
        return False
    firm = spot.user
    rent = int(round(firm.price * spot.rent_factor * unit.scale))
    if unit.ask > _firm_worth(town, firm, unit, rent) or not _firm_can_pay(town, firm, unit.ask):
        return False
    price, debt = _pay_bank(town, firm, unit, {"firm": firm})
    _leave_bank(town, unit)                              # off the bank's books, and its list of homes to let
    make_rented(town, unit, firm)
    town.event("foreclosed_sold", firm=firm, amount=price, qty=unit.id, debt=debt, spot=spot.id)
    return True


def _sell_let(town, firm, unit, price: int, entry: list, borrow: int) -> None:
    """A landlord's home is sold to a resident who owns, who lets it: a tenant in it stays
    and pays them from now on."""
    buyer = entry[0]
    value = unit_value(town, firm, unit)
    if borrow > 0:
        town.bank.lend_home(buyer, borrow, price, owned=entry[1])
    town.ledger.pay(buyer, firm, price, "home_sale")
    _book_gain(firm, price - value)
    tenant, rent, arrears = _leave_firm(town, firm, unit)
    unit.owner = buyer
    _let_by(town, unit, letting_of(town, buyer), tenant, rent, arrears)
    town.bank.repay_excess(firm)
    town.event("home_bought", agent=buyer, firm=firm, amount=price, qty=unit.id, loan=borrow, value=value,
               **{"from": "let" if tenant is not None else "empty"}, **_sold_event(unit, tenant))


def _sell_to_landlord(town, firm, unit, price: int, other) -> None:
    """A landlord's let home is sold to another landlord firm, which holds it as a single
    home where it stands; the tenant stays."""
    value = unit_value(town, firm, unit)
    town.ledger.pay(other, firm, price, "home_sale")
    _book_gain(firm, price - value)
    tenant, rent, arrears = _leave_firm(town, firm, unit)
    _firm_holds(town, unit, other, tenant, rent, arrears)
    town.bank.repay_excess(firm)
    town.event("home_bought", firm=firm, amount=price, qty=unit.id, value=value, buyer_firm=other.id,
               **{"from": "let"}, **_sold_event(unit, tenant))


def offer_let(town, firm, unit, owners: list) -> bool:
    """A let home its tenant did not buy is offered at the same price to someone who will go
    on letting it (the design: so no sale puts a tenant out): a resident who owns, by
    `letting_terms`; then the other landlord firm with the most cash, if the home is worth
    the price to it with `maker_margin` to spare and its cash beyond its reserve covers it."""
    tenant = unit.occupant
    if tenant is None or unit.firm is not firm or not _own_land(firm, unit):
        return False                                 # (it may have been vacated and sold earlier in the same quarter)
    price = unit_value(town, firm, unit) if needs_cash(town, firm) else let_price(town, firm, unit)
    rent = price_paid(tenant, "housing")
    found = _first_owner(town, price, rent, owners)
    if found is not None:
        i, borrow = found
        _sell_let(town, firm, unit, price, owners.pop(i), borrow)
        return True
    other = _richest_landlord(town, but=firm)
    if (other is None or not _firm_can_pay(town, other, price)
            or _firm_worth(town, other, unit, rent) < price * (1.0 + town.cfg.maker_margin)):
        return False
    _sell_to_landlord(town, firm, unit, price, other)
    return True


def offer_empty_to_let(town, firm, unit, owners: list) -> bool:
    """A home empty for its year that no renter took is offered at its value to a resident
    who owns, who lets it at the going rent for its place."""
    if (unit.occupant is not None or unit.firm is not firm or not _own_land(firm, unit)
            or not _long_empty(town, unit)):
        return False
    price = unit_value(town, firm, unit)
    found = _first_owner(town, price, going_rent(town, unit.spot), owners)
    if found is None:
        return False
    i, borrow = found
    _sell_let(town, firm, unit, price, owners.pop(i), borrow)
    return True


def _long_empty(town, unit) -> bool:
    return unit.empty_since is not None and town.week - unit.empty_since >= town.cfg.empty_sale_weeks


def offer_set(town, firm, unit) -> bool:
    """A firm that rents appliance sets and is short of cash sells a let set to its renter at
    its value, if they can pay (spare cash, then a personal loan) and it costs them less than
    building one. (Spec 6: "sells one by the landlord's rule"; only the short-of-cash half
    applies to a set.)"""
    renter = unit.occupant
    if renter is None or renter.set_hours_left is not None or not needs_cash(town, firm):
        return False
    spec = unit.spec
    price = unit_value(town, firm, unit)
    build = int(round(spec.build_goods * spec.import_price
                      + spec.build_labour * town.cfg.job_hours * town.hour_value))
    if price >= build:
        return False
    gap = price - _spare_cash(town, renter)
    if gap > 0:
        if town.bank.person_credit(renter) < gap:
            return False
        town.bank.lend_person(renter, gap)
    town.ledger.pay(renter, firm, price, "set_sale")
    firm.units.remove(unit)
    firm.projects = [p for p in firm.projects if p.unit is not unit]
    firm.subs.pop(renter.id, None)
    firm.unserved.pop(renter.id, None)
    renter.subs.pop(spec.name, None)
    renter.arrears.pop(spec.name, None)
    unit.firm = None
    unit.owner = renter
    town.own_units.append(unit)
    town.bank.repay_excess(firm)
    town.event("set_bought", agent=renter, firm=firm, amount=price, qty=unit.id, need=spec.name)
    return True


def offer_empty(town, firm, unit, buyers: list) -> bool:
    """A landlord sells an empty home at its value (Jason: "Sells it cheap") once it has
    stood empty `empty_sale_weeks`, or at once if the landlord is short of cash. The first
    renter or homeless person with a job who can reach their work from it, can pay, and
    would be clearly better off buys it and moves in."""
    if unit.occupant is not None or unit.firm is not firm or not _own_land(firm, unit):
        return False
    if not (_long_empty(town, unit) or needs_cash(town, firm)):
        return False
    price = unit_value(town, firm, unit)
    found = _first_buyer(town, unit, price, buyers)
    if found is None:
        return False
    i, borrow = found
    _buy_from_firm(town, firm, unit, buyers.pop(i)[0], price, borrow, "empty")
    return True


def landlord_sales(town) -> None:
    """Each quarter every landlord offers the homes it cannot let to anyone who will live in
    them, then its let homes to their tenants. What is left is offered to those who
    would let it: a let home to a resident who owns and then to another landlord, its
    tenant staying; a home empty for its year to a resident who owns, when there is a sign
    that a home is wanted."""
    landlords = town.firms_for("housing")
    let, empty = [], []
    buyers = None
    for firm in landlords:                               # empty homes first: they go at their value, so a
        for unit in list(firm.units):                    # tenant who could buy either takes the cheaper
            if unit.occupant is None:
                if buyers is None:
                    buyers = _buyers(town)
                if not offer_empty(town, firm, unit, buyers):
                    empty.append((firm, unit))
    for firm in landlords:
        for tenant in list(firm.subs.values()):          # the oldest tenancy first
            unit = tenant.unit.get("housing")
            if unit is not None and unit.firm is firm and not offer_to_tenant(town, firm, unit):
                let.append((firm, unit))
    owners = _owners(town) if let or empty else []
    for firm, unit in let:
        offer_let(town, firm, unit, owners)
    if home_wanted(town):
        for firm, unit in empty:
            offer_empty_to_let(town, firm, unit, owners)
    for firm in town.firms_for("appliances"):
        if needs_cash(town, firm):
            for unit in list(firm.units):
                offer_set(town, firm, unit)


# --- stage 1b, part B: homes for rent on no landlord's block ---------------------------------------------
def letting_of(town, agent) -> Letting:
    """A person's homes to let: made the first time they let one."""
    if agent.lets is None:
        agent.lets = Letting(agent, town.needs["housing"], -agent.id)
    return agent.lets


def put_to_let(town, unit, provider, rent: int) -> None:
    """A home that stands on no block of its provider (a person's Letting, or a firm holding
    a single home) is offered for rent at a rent of its own."""
    unit.firm = provider
    if unit not in provider.units:
        provider.units.append(unit)
    unit.rent = max(1, int(rent))
    unit.empty_since = town.week
    if unit.occupant is None and unit not in town.to_let:
        town.to_let.append(unit)


def going_rent(town, spot=None) -> int:
    """What a standard home lets for: the cheapest landlord's price, for its place if it
    stands on a landlord's block; the last price of housing if no landlord is left."""
    prices = [f.price for f in town.firms_for("housing")]
    rent = min(prices) if prices else town.last_price.get("housing", town.needs["housing"].initial_price)
    if spot is not None and spot.kind == "homes":
        rent = int(round(rent * spot.rent_factor))
    return rent


def _bank_rents(town) -> None:
    """Rent paid this week on homes the bank holds goes to the bank and comes off what is
    owed on each. The bank's Letting never ends a week holding money."""
    holder = town.bank_lets
    if holder is None:
        return
    for unit in holder.units:
        tenant = unit.occupant
        if tenant is not None and tenant.arrears.get("housing", 0) == 0:
            unit.debt = max(1, unit.debt - unit.rent)
            unit.ask = max(1, min(unit.ask, unit.debt))
    if holder.cash > 0:
        town.ledger.pay(holder, OUTSIDE, holder.cash, "loan_recovery")


def consider_building_to_let(town, agent) -> None:
    """Someone in work who owns the home they live in builds a home to let (Jason: "if
    someone believes that they can rent"). They believe it when a newcomer was turned away
    for want of a home in the quarter just ended and the going rent would cover the loan
    payment and upkeep with `maker_margin` to spare. One at a time."""
    cfg = town.cfg
    if agent.role is None or agent.build is not None or not owns(agent, "housing"):
        return
    if not home_wanted(town):
        return
    cost = build_cost(town)
    owned = sum(home_value(town, u) for u in homes_of(town, agent))
    loan = min(town.bank.home_credit(agent, cost, owned), int(cfg.mortgage_ltv * cost))
    if loan + _spare_cash(town, agent) < cost:
        return
    weekly = town.bank.home_first_payment(loan) + own_cost_week(town, agent, "housing", build=False)
    if going_rent(town) < weekly * (1.0 + cfg.maker_margin):
        return
    spot = None
    if town.map is not None:
        spot = take_plot(town)                       # anywhere: the tenant, not they, will live there
        if spot is None:
            return
    spec = town.needs["housing"]
    agent.build = OwnBuild(spec.build_labour * cfg.job_hours, spec.build_goods, spot, to_let=True)
    town.event("home_started", agent=agent, amount=cost, qty=spot.id if spot is not None else None, to_let=True)
