"""Households: the week's bills, what an agent does when money is short, what they
do with money to spare, and how secure and how well off they are.

The agent's effective horizon decides (Jason, 12/11/2026: the emotional state
decides how they handle each situation). Calm agents cut what they can do
without and hold their shares. Stressed agents keep consuming, sell shares at
whatever the market gives, and borrow.
"""

from __future__ import annotations

from .labour import separate
from .metrics import RANK
from .rtr_makers import makes_a_living
from .rtr_owning import borrowable, own_upkeep_week, owns
from .places import (cut_off_from_food, dist, find_home, home_cost, home_spot, needs_ride, reach, ride_for_work,
                     rides, transport_fare, travel_hours, unit_rent, wants_transport)
from .subscriptions import (all_told, cheapest_prices, ensure_transport, find_provider, free_better_home,
                            has_room, move_home, note_turned_away, price_paid, rent_home,
                            set_plan, standard_price, subscribe, unsubscribe, wants)

LOAN_PRIORITY = 2          # the bank is paid after food and housing, before everything else
HOME_LOAN_PRIORITY = 1     # (C) 16/11/2026, RTR: a loan against a home is paid where the rent is
WORK_RIDE_PRIORITY = 0.5   # (J) 16/11/2026: a ride to work is paid after food and before the rent


# --- costs ------------------------------------------------------------------------------------
def basket_cost(town, agent, cheapest=None, loan: bool = True) -> int:
    """A week of the four base needs at standard size: what they pay for each, or the
    cheapest price on offer for one they are going without. In the RTR world a home or set of
    their own counts at its upkeep, with the loan payment on a home (Jason, 20/11/2026). Invented needs, bigger plans and
    better homes are left out on purpose, so that taking up a luxury or moving up does not
    move the yardstick the agent measures their income, cushion and security against."""
    if cheapest is None:
        cheapest = cheapest_prices(town)
    paid = town.cfg.rtr and town.cfg.owners_judge_by_what_they_pay
    total = 0
    for name, spec in town.needs.items():
        if spec.invented:
            continue
        if name in agent.subs:
            total += standard_price(agent, name)
        elif paid and owns(agent, name):         # RTR (J, 20/11/2026): what owning it costs them, not a firm's asking rent
            total += own_upkeep_week(town, name, agent.unit[name])
        else:                                    # going without: in the RTR world the lowest a firm or neighbour asks
            total += getattr(cheapest, "lowest", cheapest).get(name, 0)
    if paid and loan and agent.home_loan > 0:    # and the loan against a home, as their bills count it
        total += (round(agent.home_loan * town.cfg.firm_rate / town.cfg.weeks_per_year)
                  + min(agent.home_loan, agent.home_pay))
    return total


def essentials_cost(town, agent, cheapest) -> int:
    total = 0
    for name, spec in town.needs.items():
        if spec.essential:
            if name in agent.subs:
                total += price_paid(agent, name)
            elif not owns(agent, name):
                total += cheapest.get(name, 0)
    if agent.home_loan > 0:                        # RTR: an owner's housing cost is the loan, not a rent
        total += (round(agent.home_loan * town.cfg.firm_rate / town.cfg.weeks_per_year)
                  + min(agent.home_loan, agent.home_pay))
    return total


def buffer_target(cfg, agent, basket: int) -> int:
    """The cushion they want: 4 to 52 weeks of bills, longer for longer horizons."""
    weeks = agent.h_eff(cfg) / cfg.buffer_horizon_divisor
    return int(min(cfg.buffer_weeks_max, max(cfg.buffer_weeks_min, weeks)) * basket)


def lives_on_dividends(town, agent, basket=None) -> bool:
    """No job, and a year of dividends that covers a year of their bills."""
    if agent.role is not None:
        return False
    if basket is None:
        basket = basket_cost(town, agent)
    need = int(town.cfg.rentier_cover * basket * town.cfg.weeks_per_year)
    return need > 0 and agent.dividends_year() >= need


# --- class, by role (Jason, 12/11/2026) ----------------------------------------------------------
def classify(town, agent, covered=None, basket=None) -> str:
    """'owner': runs a firm, is an executive, founded or controls a live firm, or lives on
    dividends alone. 'working': staff drawing a wage, with or without shares; in the RTR
    world also someone with no job whose side hustle brings in half their basket. 'out': the
    rest. `covered`: do they live on dividends alone?"""
    if agent.role in ("ceo", "exec"):
        return "owner"
    for firm_id, shares in agent.shares.items():
        firm = town.firm(firm_id)
        if firm.alive and (firm.founder_id == agent.id or shares * 2 >= firm.shares_out):
            return "owner"
    if agent.role == "staff":
        return "working"
    if agent.hustle is not None and makes_a_living(
            agent, basket if basket is not None else basket_cost(town, agent)):
        return "working"                         # RTR 2: a maker with no job who makes a living at it
    if covered is None:
        covered = lives_on_dividends(town, agent)
    return "owner" if covered else "out"


def wellbeing(cfg, security: float, provision: float, condition: float) -> float:
    return cfg.w_security * security + cfg.w_provision * provision + cfg.w_condition * condition


# --- what a share is worth to this agent ---------------------------------------------------------
def valuation(town, agent, firm, book=None) -> int:
    """Expected dividends over the agent's horizon, plus half of book value, marked down
    if the firm's profit per share has grown more slowly than this holder expects."""
    cfg = town.cfg
    if firm.shares_out <= 0:
        return 0
    if book is None:
        book = firm.book_per_share(cfg)
    last_year = firm.dps_hist[-4:]
    if len(last_year) >= 4:
        weekly = sum(last_year) / cfg.weeks_per_year
    else:
        weekly = book * cfg.prior_yield / cfg.weeks_per_year      # no record yet
    horizon = min(agent.h_eff(cfg), cfg.horizon_value_cap)
    mood = 1.0
    if len(firm.eps_hist) >= 5 and firm.eps_hist[-5] > 0:
        grown = firm.eps_hist[-1] / firm.eps_hist[-5] - 1.0
        mood = 1.0 + cfg.satisfaction_gain * (grown - agent.growth_expect)
        mood = min(cfg.satisfaction_max, max(cfg.satisfaction_min, mood))
    return int((weekly * horizon + cfg.book_weight * book) * mood)


# --- the week's bills --------------------------------------------------------------------------
def dues(town, agent) -> list[tuple[int, str, str, int]]:
    """What falls due this week, in the order it is paid: (priority, kind, name, amount)."""
    cfg = town.cfg
    out = []
    work_ride = cfg.fare_first_for_work and ride_for_work(town, agent)
    for name, firm in agent.subs.items():
        if agent.id not in firm.unserved:          # a firm that could not serve them does not bill them
            priority = WORK_RIDE_PRIORITY if work_ride and name == "transport" else firm.spec.priority
            out.append((priority, "sub", name, price_paid(agent, name)))
    if agent.loan > 0:
        amount = 0
        if not agent.loan_called:
            interest = round(agent.loan * cfg.personal_rate / cfg.weeks_per_year)
            amount = interest + min(agent.loan, agent.loan_pay)
        out.append((LOAN_PRIORITY, "loan", "loan", amount))
    if agent.home_loan > 0:                        # RTR: a loan against their home, paid where the rent would be
        interest = round(agent.home_loan * cfg.firm_rate / cfg.weeks_per_year)
        out.append((HOME_LOAN_PRIORITY, "home_loan", "home_loan", interest + min(agent.home_loan, agent.home_pay)))
    out.sort(key=lambda d: d[0])
    return out


def _sell_for_cash(town, agent, cash_needed: int, books, reason: str) -> None:
    """Offer shares at whatever the market gives, the least valued holding first."""
    remaining = int(cash_needed * 1.25)            # room for the price to slip
    ranked = []
    for firm_id, held in agent.shares.items():
        firm = town.firm(firm_id)
        price = max(1, firm.share_price)
        ranked.append((valuation(town, agent, firm, books.get(firm_id)) / price, firm_id, held, price))
    ranked.sort()
    for _, firm_id, held, price in ranked:
        if remaining <= 0:
            break
        qty = min(held, -(-remaining // price))
        town.broker.ask(agent, town.firm(firm_id), 0, qty, reason)
        remaining -= qty * price


def _review_holdings(town, agent, books) -> None:
    """An unhappy shareholder offers a tenth of the holding at what it is worth to them."""
    cfg = town.cfg
    for firm_id, held in list(agent.shares.items()):
        firm = town.firm(firm_id)
        if town.week - firm.founded < cfg.sell_min_firm_age:
            continue
        worth = valuation(town, agent, firm, books.get(firm_id))
        if worth < firm.share_price * (1.0 - cfg.sell_discount):
            town.broker.ask(agent, firm, max(1, worth), max(1, int(held * cfg.sell_fraction)), "unhappy")


def _bid(town, agent, excess: int, listed, books) -> None:
    """Put part of the spare cash toward the share that looks best value to this agent."""
    cfg, rng = town.cfg, town.rng
    candidates = rng.sample(listed, 3) if len(listed) > 3 else list(listed)
    for firm_id in agent.shares:
        firm = town.firm(firm_id)
        if firm.alive and firm not in candidates:
            candidates.append(firm)
    best = None
    for firm in candidates:
        price = max(1, firm.share_price)
        worth = valuation(town, agent, firm, books.get(firm.id))
        if worth >= price * (1.0 + cfg.bid_edge) and (best is None or worth / price > best[0]):
            best = (worth / price, firm, worth, price)
    if best is None:
        return
    _, firm, worth, price = best
    limit = min(worth, int(price * cfg.bid_cap))
    qty = int(excess * cfg.invest_fraction) // limit
    if qty >= 1:
        town.broker.bid(agent, firm, limit, qty)


def plan_bills(town) -> None:
    """Before the broker opens: each agent looks at the week's bills, trims or sells if
    short, and offers spare cash for shares."""
    cfg, rng = town.cfg, town.rng
    cheapest = cheapest_prices(town)
    listed = [f for f in town.alive_firms if f.shares_out > 0]
    books = {f.id: f.book_per_share(cfg) for f in listed}
    for agent in town.agents:
        calm = agent.h_eff(cfg) >= cfg.calm_horizon_weeks
        bills = dues(town, agent)
        total = sum(d[3] for d in bills)
        basket = basket_cost(town, agent, cheapest)
        cushion = buffer_target(cfg, agent, basket)
        income = agent.income_estimate()

        # a calm agent whose income will not cover the bills, and whose cushion is thin,
        # drops what they can do without, least essential first
        if calm and income < total and agent.cash < cushion and agent.plan:
            for _, kind, name, amount in reversed(bills):    # a bigger plan goes back to standard first
                if income >= total:
                    break
                size = agent.plan.get(name, 1) if kind == "sub" else 1
                if size > 1:
                    set_plan(town, agent, agent.subs[name], 1)
                    total -= amount - amount // size
            bills = dues(town, agent)
        if calm and income < total and agent.cash < cushion:
            for _, kind, name, amount in reversed(bills):
                if income >= total:
                    break
                if kind != "sub" or town.needs[name].essential:
                    continue
                if name == "transport" and needs_ride(town, agent):
                    continue                     # it is how they get to work or to food
                unsubscribe(town, agent, name, "budget")
                total -= amount

        shortfall = total - agent.cash
        if shortfall > 0 and agent.shares:
            # the stressed sell to keep everything going; the calm sell only for food and housing
            needed = shortfall
            if calm:
                needed = essentials_cost(town, agent, cheapest) - agent.cash
            if needed > 0:
                _sell_for_cash(town, agent, needed, books, "distress")

        if cfg.bank_can_force_share_sale and agent.loan_called and agent.shares:
            _sell_for_cash(town, agent, agent.loan, books, "forced")

        if agent.shares and cfg.sell_review_prob > 0 and rng.random() < cfg.sell_review_prob:
            _review_holdings(town, agent, books)

        if shortfall <= 0 and listed and cfg.invest_prob > 0:
            excess = agent.cash - total - cushion
            if excess > 0 and rng.random() < cfg.invest_prob:
                _bid(town, agent, excess, listed, books)


def _missed(town, agent, firm, name: str, amount: int) -> None:
    """A payment was missed. A home or appliance set is kept for the grace period; food
    and services stop at once. After the grace period the subscription ends."""
    cfg, spec = town.cfg, firm.spec
    agent.arrears[name] = agent.arrears.get(name, 0) + 1
    town.event("missed_payment", agent=agent, firm=firm, amount=amount, need=name,
               missed=agent.arrears[name])
    agent.shock(cfg, cfg.shock_missed)
    agent.met[name] = spec.kind == "asset"
    if agent.arrears[name] >= cfg.grace_weeks:
        if name == "housing":
            reason = "evicted"
            agent.shock(cfg, cfg.shock_eviction)
        else:
            reason = "repossessed" if spec.kind == "asset" else "cut_off"
        unsubscribe(town, agent, name, reason)
        agent.met[name] = False


def pay_bills(town) -> None:
    """Each agent pays the week's bills in order. Short of cash, they borrow if they can
    and choose to; otherwise the payment is missed."""
    cfg = town.cfg
    bank = town.bank
    for agent in town.agents:
        calm = agent.h_eff(cfg) >= cfg.calm_horizon_weeks
        agent.met = {}
        refused = False
        for _, kind, name, amount in dues(town, agent):
            if kind == "loan":
                before = agent.cash
                if agent.loan_called:
                    if bank.weekly_called(agent) == "default":
                        agent.shock(cfg, cfg.shock_default)
                else:
                    bank.service_person(agent)
                agent.spend_week += before - agent.cash
                continue
            if kind == "home_loan":                  # RTR: like the rent, they borrow to keep it paid
                if agent.cash < amount and bank.lend_person(agent, amount - agent.cash) == 0 and not refused:
                    refused = True
                    town.event("credit_refused", agent=agent, amount=amount - agent.cash, need="home_loan")
                before = agent.cash
                bank.service_home(agent)
                agent.spend_week += before - agent.cash
                continue
            firm = agent.subs[name]
            if agent.cash < amount and (firm.spec.essential or not calm):
                if bank.lend_person(agent, amount - agent.cash) == 0 and not refused:
                    refused = True
                    town.event("credit_refused", agent=agent, amount=amount - agent.cash, need=name)
            if agent.cash >= amount:
                town.ledger.pay(agent, firm, amount, "subscription")
                firm.w_revenue += amount
                agent.spend_week += amount
                agent.arrears[name] = 0
                agent.met[name] = True
            else:
                _missed(town, agent, firm, name, amount)
        for name, firm in agent.subs.items():
            if agent.id in firm.unserved:
                agent.met[name] = False
        for name, unit in agent.unit.items():
            if unit.owner is agent:
                agent.met[name] = True               # RTR: what they own is theirs to use
        ride = agent.subs.get("transport")
        if ride is None or agent.id not in ride.unserved:
            agent.no_ride = 0
        else:
            agent.no_ride += 1
            if agent.no_ride >= cfg.grace_weeks:       # a ride that never comes is given up
                unsubscribe(town, agent, "transport", "unserved")
                agent.no_ride = 0


# --- distance ----------------------------------------------------------------------------------------
def check_reach(town, agent) -> None:
    """An agent whose job or shops have fallen out of reach (their transport was cut off,
    or they were put out and re-rented far away). For a job they ride if they can, move
    closer if a home is free there, and otherwise lose it. A shop out of reach is dropped."""
    cfg = town.cfg
    home = home_spot(agent)
    if home is None:
        return
    employer = agent.employer
    if (employer is not None and agent.role != "ceo" and employer.spot is not None
            and dist(home, employer.spot) > reach(town, agent)):
        blocks = dist(home, employer.spot)
        fare = transport_fare(town)
        rides_again = (blocks <= cfg.walk_range * cfg.transport_speed and fare is not None
                       and agent.cash >= fare and ensure_transport(town, agent))   # only if they can pay
        if not rides_again:
            unit = None if owns(agent, "housing") else find_home(town, agent, work=employer.spot,
                                                                 max_rent=agent.cash)   # an owner does not move
            if unit is not None and dist(unit.spot, employer.spot) <= reach(town, agent):
                move_home(town, agent, unit, "reach")
                home = home_spot(agent)
            else:
                separate(town, agent, "out_of_reach")
    drop_far_shops(town, agent)


def consider_moving(town, agent) -> None:
    """Now and then a resident looks at the homes on offer and moves if one would cost
    clearly less once the time to work is counted. They do not move out of reach of work.
    A well-off resident in a standard home looks for a better one instead (16/11/2026);
    one already in a better home looks only at better homes."""
    home = home_spot(agent)
    if home is None:
        return
    current = agent.unit["housing"]
    if agent.well_off and current.scale <= 1.0:
        look_for_better_home(town, agent)
        if agent.unit.get("housing") is not current:
            return
    unit = find_home(town, agent, max_rent=agent.cash, better=agent.well_off and current.scale > 1.0)
    if unit is None or (unit.spot is home and unit.scale == current.scale):
        return
    if (agent.employer is not None and agent.role != "ceo"
            and dist(unit.spot, agent.employer.spot) > reach(town, agent)):
        return
    hungry_here = cut_off_from_food(town, agent, home)
    hungry_there = cut_off_from_food(town, agent, unit.spot)
    if hungry_there and not hungry_here:
        return                                   # no rent is low enough to move away from the only food
    if hungry_here and not hungry_there:
        move_home(town, agent, unit, "food")     # they move to where they can eat, whatever the rent
    elif (home_cost(town, agent, unit.spot, unit.scale, unit.rent or None)
          < home_cost(town, agent, home, current.scale, current.rent or None) * (1.0 - town.cfg.switch_friction)):
        move_home(town, agent, unit, "cheaper")


# --- the well-off spend more (Jason, 16/11/2026) --------------------------------------------------------
def standard_bills(town, agent, cheapest) -> int:
    """A week's bills at standard size: the basket of the four base needs (what they pay, or the
    cheapest on offer for one they go without), the luxuries and the ride they hold at a standard
    plan, and the loan payment. So going without something does not make anyone well-off."""
    total = basket_cost(town, agent, cheapest)
    for name, firm in agent.subs.items():
        if town.needs[name].invented or name == "transport":
            total += firm.price
    for _, kind, _, amount in dues(town, agent):
        if kind == "loan":
            total += amount
    return total


def look_for_better_home(town, agent) -> None:
    """A well-off resident in a standard home moves to the better home that costs them least,
    within reach of work and within what they hold. If none is free they wait for one, and
    the landlords build for those waiting."""
    current = agent.unit.get("housing")
    if current is None or current.scale > 1.0:
        return
    if current.owner is agent:                    # RTR: they own their home; they are not looking to rent
        agent.wants_better = False
        return
    paying = sum(d[3] for d in dues(town, agent)) - unit_rent(current)
    room = int(agent.income_estimate() / town.cfg.well_off_drop) - paying   # the most rent that keeps income well over the bills
    most = min(agent.cash, room)
    landlords = town.firms_for("housing")
    if not landlords or most < round(min(f.price for f in landlords) * town.cfg.better_home):
        agent.wants_better = False                # they could not pay for one: they are not waiting
        return
    if town.map is None:
        unit = free_better_home(town, max_rent=most)
    else:
        unit = find_home(town, agent, max_rent=most, better=True)
        if unit is not None and cut_off_from_food(town, agent, unit.spot) \
                and not cut_off_from_food(town, agent, current.spot):
            unit = None                          # not away from the only food
        employer = agent.employer
        if (unit is not None and employer is not None and agent.role != "ceo" and employer.spot is not None
                and dist(unit.spot, employer.spot) > reach(town, agent)):
            unit = None                          # not out of reach of work
    if unit is None:
        agent.wants_better = True
        return
    agent.wants_better = False
    move_home(town, agent, unit, "better")


def review_spending(town, agent, cheapest) -> None:
    """Is the resident well-off? Income at least `well_off_income` times the week's bills at
    standard size, with their cushion full; no longer once income falls below `well_off_drop`
    times those bills or their cash below half the cushion. The well-off take a bigger plan of
    what they use up (not the ride) and, on becoming well-off, look for a better home."""
    cfg = town.cfg
    if cfg.well_off_income <= 0:
        return
    bills = standard_bills(town, agent, cheapest)
    income = agent.income_estimate()
    cushion = buffer_target(cfg, agent, basket_cost(town, agent, cheapest))
    was = agent.well_off
    if was:
        agent.well_off = not (income < cfg.well_off_drop * bills or agent.cash < cushion // 2)
    else:
        agent.well_off = income >= cfg.well_off_income * bills and agent.cash >= cushion
    if not agent.well_off:
        agent.wants_better = False
    size = cfg.bigger_plan if agent.well_off else 1
    paying = sum(d[3] for d in dues(town, agent))      # what they really pay a week now
    for name, firm in sorted(agent.subs.items(), key=lambda item: item[1].spec.priority):
        if firm.spec.kind != "flow" or name == "transport":
            continue
        have = agent.plan.get(name, 1)
        if have == size:
            continue
        if size > have:
            more = firm.price * (size - have)
            if not has_room(town, firm) or income < cfg.well_off_drop * (paying + more):
                continue                              # only while income stays well over the bills with it
            paying += more
        set_plan(town, agent, firm, size)
    if agent.well_off and (not was or agent.wants_better):
        look_for_better_home(town, agent)             # on becoming well-off, and each week while waiting


# --- signing up, switching -------------------------------------------------------------------------
class _Budget:
    """What an agent has to work with during one review of their subscriptions."""

    __slots__ = ("available", "committed", "income", "cushion")

    def __init__(self, town, agent) -> None:
        self.available = agent.cash
        self.committed = sum(d[3] for d in dues(town, agent))   # the same bills plan_bills counts, loan included
        self.income = agent.income_estimate()
        self.cushion = None


def _review_need(town, agent, spec, budget, cheapest, has_map: bool) -> None:
    """One need for one agent: keep it, shop around, or take it up if they lack it and can pay."""
    cfg, rng = town.cfg, town.rng
    name = spec.name
    if owns(agent, name):
        return                                   # RTR: it is theirs; nothing to rent or shop for
    current = agent.subs.get(name)
    if has_map and name == "housing":
        # Homes differ by where they are: take the one that suits, and look at moving now and then.
        if current is None:
            rode = rides(agent)
            if agent.well_off and rent_home(town, agent, "signup", max_rent=budget.available, better=True):
                agent.wants_better = False
                rent = unit_rent(agent.unit["housing"])
                if rides(agent) and not rode:
                    rent += agent.subs["transport"].price
                budget.available -= rent
                budget.committed += rent
            elif rent_home(town, agent, "signup", max_rent=budget.available):
                if agent.well_off:
                    agent.wants_better = True    # no better home free: they wait for one
                rent = unit_rent(agent.unit["housing"])
                if rides(agent) and not rode:
                    rent += agent.subs["transport"].price    # the ride that came with the home
                budget.available -= rent
                budget.committed += rent
            elif budget.available >= cheapest.get(name, 0):
                note_turned_away(town)           # could pay, but no home is free within reach
        elif rng.random() < cfg.move_prob:
            consider_moving(town, agent)
        return
    if current is not None:
        # A customer the firm could not serve this week goes to any seller with room.
        # Otherwise they shop around now and then and move for a clearly lower price.
        unserved = agent.id in current.unserved
        if unserved or rng.random() < cfg.switch_prob:
            other = find_provider(town, agent, name, exclude=current)
            if other is not None and (
                    unserved or all_told(town, agent, other)
                    < all_told(town, agent, current) * (1.0 - cfg.switch_friction)):
                unsubscribe(town, agent, name, "unserved" if unserved else "switch")
                subscribe(town, agent, other, "switch")
                budget.committed += other.price - current.price
        return
    _take_up(town, agent, spec, budget, cheapest)


def _take_up(town, agent, spec, budget, cheapest) -> None:
    """Sign up for a need they lack, if a seller is within reach and they can pay."""
    cfg = town.cfg
    name = spec.name
    if name not in cheapest or not wants(agent, spec) or owns(agent, name):
        return
    if (name == "appliances" and agent.set_hours_left is not None
            and cfg.rtr and cfg.arrivals_own_appliances):
        return                                   # RTR (22/11/2026): building a set of their own, they rent none meanwhile
    if name == "housing" and agent.well_off:
        better = free_better_home(town, max_rent=budget.available)
        if better is not None and subscribe(town, agent, better.firm, "signup", unit=better):
            agent.wants_better = False
            budget.available -= unit_rent(better)
            budget.committed += unit_rent(better)
            return
        agent.wants_better = True                # none free: a standard home, and they wait
    if name == "housing" and town.to_let and town.map is None:
        # RTR 1b, no map: a home someone lets may be the cheapest free home, or the only one
        if rent_home(town, agent, "signup", max_rent=budget.available):
            rent = unit_rent(agent.unit["housing"])
            budget.available -= rent
            budget.committed += rent
            return
    firm = find_provider(town, agent, name)
    if firm is None:
        if name == "housing" and budget.available >= cheapest[name]:
            note_turned_away(town)               # could pay, but no home is free
        return
    must_ride = False
    if name == "transport":
        if not wants_transport(town, agent, firm.price):
            return
        must_ride = needs_ride(town, agent)      # for work or for food: taken like an essential
    if budget.available < firm.price:
        return
    if not spec.essential and not must_ride:
        if budget.cushion is None:
            budget.cushion = buffer_target(cfg, agent, basket_cost(town, agent, cheapest))
        spare = budget.income - budget.committed
        if not (spare >= firm.price * cfg.adopt_margin
                or agent.cash >= budget.cushion + firm.price * cfg.adopt_cushion_weeks):
            return
    if subscribe(town, agent, firm, "signup"):
        budget.available -= firm.price
        budget.committed += firm.price


def drop_far_shops(town, agent) -> None:
    """Drop any shop that is out of reach of where the agent now lives."""
    home = home_spot(agent)
    if home is None:
        return
    limit = reach(town, agent)
    for name, firm in list(agent.subs.items()):
        if firm.spec.trips_per_week > 0 and firm.spot is not None and dist(home, firm.spot) > limit:
            unsubscribe(town, agent, name, "out_of_reach")


def review_subscriptions(town) -> None:
    """Take up what they lack and can afford, in order of need. Now and then, shop around.
    On a map, an agent whose home changed during the review, or who took up or lost a
    ride, picks their shops again from what they can now reach."""
    cheapest = cheapest_prices(town)
    order = sorted(town.needs.values(), key=lambda s: s.priority)
    has_map = town.map is not None
    for agent in town.agents:
        if has_map:
            check_reach(town, agent)
        home_before = home_spot(agent) if has_map else None
        rode_before = has_map and rides(agent)
        review_spending(town, agent, cheapest)         # a move to a better home is a move like any other
        budget = _Budget(town, agent)
        for spec in order:
            _review_need(town, agent, spec, budget, cheapest, has_map)
        if has_map and (home_spot(agent) is not home_before or rides(agent) != rode_before):
            drop_far_shops(town, agent)
            for spec in order:
                if spec.name != "housing" and spec.name not in agent.subs:
                    _take_up(town, agent, spec, budget, cheapest)


# --- security, wellbeing, class -----------------------------------------------------------------
def _unit(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def update_agents(town) -> None:
    """End of the week: each agent's security moves toward what their situation supports,
    falling fast and recovering slowly; wellbeing and class follow."""
    cfg = town.cfg
    cheapest = cheapest_prices(town)
    specs = list(town.needs.values())
    asset_needs = [s.name for s in specs if s.kind == "asset" and not s.invented]
    span = cfg.adequacy_high - cfg.adequacy_low
    for agent in town.agents:
        basket = basket_cost(town, agent, cheapest)
        income = agent.income_estimate()
        rentier = lives_on_dividends(town, agent, basket)          # never someone with a job
        covered = (agent.role is not None or rentier
                   or (agent.hustle is not None and makes_a_living(agent, basket)))   # RTR 2: a maker has a position
        if basket > 0:
            adequacy = _unit((income / basket - cfg.adequacy_low) / span)
            buffer = _unit((agent.cash + borrowable(town, agent)) / (basket * cfg.buffer_full_weeks))
        else:
            adequacy = buffer = 1.0
        debt = _unit(agent.loan / (cfg.personal_limit_weeks * max(agent.wage, agent.last_wage, 1)))
        target = _unit(cfg.sec_w_adequacy * adequacy + cfg.sec_w_buffer * buffer
                       + cfg.sec_w_position * (1.0 if covered else 0.0) - cfg.sec_w_debt * debt)
        if target >= agent.security:
            rate = cfg.security_up_rate
        else:
            rate = min(1.0, cfg.security_down_rate * agent.loss_aversion / cfg.loss_aversion_median)
        agent.security = _unit(agent.security + rate * (target - agent.security))

        met = total = 0.0
        for spec in specs:
            name = spec.name
            if spec.invented:
                if name in agent.subs:
                    agent.had[name] = town.week   # holding it keeps the habit fresh
                elif (name not in agent.had or name not in cheapest
                      or (cfg.habit_weeks > 0 and town.week - agent.had[name] > cfg.habit_weeks)):
                    continue                      # never had it, nobody sells it now, or the habit has faded
            total += spec.weight
            if agent.met.get(name):
                met += spec.weight
        agent.provision = met / total if total > 0 else 1.0
        if asset_needs:
            agent.condition = sum(agent.unit[n].cond if n in agent.unit else 0.0
                                  for n in asset_needs) / len(asset_needs)
        else:
            agent.condition = 1.0
        agent.wellbeing = wellbeing(cfg, agent.security, agent.provision, agent.condition)

        if town.map is not None:                  # hours on the road this week: to work and to the shops
            hours = 0.0
            home = home_spot(agent)
            if home is not None:
                fast = rides(agent)
                if agent.employer is not None:
                    hours += travel_hours(cfg, cfg.commute_trips, dist(home, agent.employer.spot), fast)
                for firm in agent.subs.values():
                    trips = firm.spec.trips_per_week
                    if trips > 0:
                        hours += travel_hours(cfg, trips, dist(home, firm.spot), fast)
            agent.travel_hours = hours
        agent.happy = agent.wellbeing >= cfg.happy_cutoff
        agent.destitute = (agent.role is None and not covered and not agent.shares
                           and agent.cash < essentials_cost(town, agent, cheapest))

        klass = classify(town, agent, rentier, basket)
        if klass != agent.klass:
            town.event("class_change", agent=agent, old=agent.klass, new=klass,
                       trigger=agent.last_trigger)
            if RANK[klass] > RANK[agent.klass]:
                town.moves_up += 1
            else:
                town.moves_down += 1
            agent.klass = klass
