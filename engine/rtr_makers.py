"""The Right to Repair world, stage 2: makers (Jason, 16/11/2026: "side hustles or actual
small businesses").

A maker is one person selling their own spare time to others: a need people go to a seller
for (food, entertainment, anything someone thought up), repairs to what people own, or
building appliance sets and homes for people who do not want to build them themselves.
Nothing here runs in the WEF world. The rules, and the calls behind each number, are in
docs/superpowers/specs/2026-11-16-rtr-world-design.md (sections 5, 8 and 9) and
docs/superpowers/plans/2026-11-18-rtr-stage2-makers.md.
"""

from __future__ import annotations

from .entities import Hustle
from .labour import can_get_to, first_to_go, hire, reservation_wage, separate
from .firmops import set_price
from .ledger import OUTSIDE
from .places import home_spot
from .production import unit_cost, upkeep_need
from .places import dist, reach
from .rtr_owning import _spare_cash, borrowable, home_value, homes_of, spare_hours
from .subscriptions import all_told, cheapest_prices, set_plan, subscribe, unsubscribe

HOUR_TRADES = ("repair", "set_building", "home_building")     # these sell hours, not a weekly need
NOT_FOR_MAKERS = ("housing", "appliances", "transport")       # letting is not making, and not the ride


# --- the trades ---------------------------------------------------------------------------------------
def trades(town) -> list:
    """Every trade a maker can take up, as (name, the need's spec or None): the needs people
    go to a seller for, then the three that sell hours. A need thought up this week is open
    to others only from next week."""
    out = []
    for name, spec in town.needs.items():
        if name in NOT_FOR_MAKERS or name in town.new_ideas or spec.kind != "flow":
            continue
        out.append((name, spec))
    out.extend((name, None) for name in HOUR_TRADES)
    return out


def tools_cost(cfg, trade: str, spec) -> int:
    """The one-off cost of the tools for a trade (Jason: their own money first)."""
    if spec is not None and spec.invented:
        return cfg.tools_invented
    return getattr(cfg, f"tools_{trade}", cfg.tools_invented)     # a need a settings file adds has no dial of its own


# --- what an hour is worth, and prices ---------------------------------------------------------------
def hour_worth(town, agent) -> float:
    """What an hour of a maker's is worth to them, in cents: their wage over the hours of a
    job, or for someone out of work the wage they would now accept (it falls the longer
    they are out), and never less than a share of the going hourly staff wage."""
    cfg = town.cfg
    if agent.role is not None:
        week = agent.wage
    else:
        week = int(agent.last_wage * agent.security
                   * max(0.0, 1.0 - cfg.reservation_decay * agent.weeks_out))   # as the labour market reckons it
    return max(week / cfg.job_hours, cfg.maker_hour_floor * town.typical_wage() / cfg.job_hours)


def hours_per_customer(cfg, spec) -> float:
    """Hours one customer takes a week: the firm's own service figure."""
    return spec.service_labour * cfg.job_hours


def need_price(town, agent, spec, worth=None) -> int:
    """A maker's weekly price for a need (Jason, tentative: cost plus a little): the goods at
    the outside price and their hours at what an hour of theirs is worth, plus the margin."""
    cfg = town.cfg
    if worth is None:
        worth = hour_worth(town, agent)
    cost = spec.goods_per_sub * spec.import_price + hours_per_customer(cfg, spec) * worth
    return max(1, int(round(cost * (1.0 + cfg.maker_margin))))


def hour_price(town, agent, worth=None) -> int:
    """What a maker charges for one hour of theirs: its worth, plus the margin."""
    if worth is None:
        worth = hour_worth(town, agent)
    return max(1, int(round(worth * (1.0 + town.cfg.maker_margin))))


def price_now(town, hustle, business=None) -> int:
    """Today's price for this side hustle: a week of its need, or one hour. A small business
    costs an hour at the going wage, which is what it pays its staff, and never at less than
    its owner's own: it prices as a business from the day it borrows. `business` asks what
    the price would be if it were one (or were not)."""
    worth = hour_worth(town, hustle.owner)
    if hustle.business if business is None else business:
        worth = max(worth, town.typical_wage() / town.cfg.job_hours)
    if hustle.spec is None:
        return hour_price(town, hustle.owner, worth)
    return need_price(town, hustle.owner, hustle.spec, worth)


# --- a side hustle ---------------------------------------------------------------------------------------
def open_hustle(town, agent, trade: str) -> Hustle:
    """A side hustle of this trade, theirs, at today's price. Nothing is charged here."""
    spec = None if trade in HOUR_TRADES else town.needs[trade]
    hustle = Hustle(agent, trade, spec, town.week)
    hustle.price = price_now(town, hustle)
    town.hustles.append(hustle)
    town.makers_of.setdefault(trade, []).append(hustle)
    agent.hustle = hustle
    if town.map is not None:
        hustle.spot = home_spot(agent)
    _set_hours(town, hustle, spare_hours(town.cfg, agent))       # people can sign up from this week
    return hustle


def _close(town, hustle) -> None:
    """Take a side hustle off the town's books: it is nobody's any more."""
    hustle.alive = False
    town.hustles.remove(hustle)
    town.makers_of[hustle.trade].remove(hustle)
    hustle.owner.hustle = None


def draw(town, hustle) -> None:
    """What is in the till is its owner's: they draw it at the week's end, when the goods and
    the staff have been paid out of it. What the bank lent the business stays in it."""
    town.ledger.pay(hustle, hustle.owner, hustle.cash - hustle.reserve, "drawings")


def stop(town, hustle, reason: str) -> None:
    """A side hustle ends: its customers are released and its tools are gone."""
    for agent in list(hustle.subs.values()):
        unsubscribe(town, agent, hustle.need, "maker_stopped")
    for agent in list(hustle.staff):
        separate(town, agent, "wound_up")
    if hustle.loan > 0:
        town.bank.settle_hustle(hustle)
    hustle.reserve = 0
    draw(town, hustle)
    owner = hustle.owner
    _close(town, hustle)
    town.event("hustle_stopped", agent=owner, reason=reason, trade=hustle.trade)


# --- the week ---------------------------------------------------------------------------------------------
def upkeep_hours(town, agent) -> float:
    """Hours the upkeep of what they own needs this week: it comes before the side hustle."""
    cfg = town.cfg
    units = homes_of(town, agent)
    own_set = agent.unit.get("appliances")
    if own_set is not None and own_set.owner is agent:
        units.append(own_set)
    return sum(upkeep_need(cfg, unit)[0] for unit in units) * cfg.job_hours


def _set_hours(town, hustle, spare: float) -> None:
    """The hours a side hustle has for customers out of its owner's `spare` hours, once
    their own things are kept up; and for a need, how many standard plans that serves."""
    hustle.own_hours = max(0.0, spare - upkeep_hours(town, hustle.owner))
    hustle.hours = hustle.own_hours + town.cfg.job_hours * len(hustle.staff)
    hustle.capacity = 0
    if hustle.spec is not None:
        hustle.capacity = int(hustle.hours / hours_per_customer(town.cfg, hustle.spec) + 1e-9)


def _cheaper_elsewhere(town, agent, hustle, cost: float) -> bool:
    """Is there another seller of it, within their reach and with room, that would cost them less?"""
    from .subscriptions import has_room
    home = home_spot(agent) if town.map is not None and hustle.spec.trips_per_week > 0 else None
    limit = reach(town, agent) if home is not None else 0
    for seller in town.firms_for(hustle.need) + town.makers_of.get(hustle.need, []):
        if seller is hustle or getattr(seller, "owner", None) is agent or not has_room(town, seller):
            continue
        if home is not None and seller.spot is not None and dist(home, seller.spot) > limit:
            continue
        if all_told(town, agent, seller) < cost:
            return True
    return False


def would_have_bought(town, agent, hustle, cheapest, price=None) -> bool:
    """Would this person, turned away because the maker was full, have signed up? They must
    have the cash for a week of it. Someone who buys it elsewhere would have switched only
    for a clearly lower cost; someone going without takes up what is not an essential only
    on the tests anyone applies (income to spare for it, or a full cushion and half a year
    of it besides). The selling code notes everyone who asked; a maker takes staff on, and
    goes to the bank, only for those who would have bought. With `price`: would they have,
    at that price in place of the one charged now? Then not if another seller with room
    would cost them less."""
    from .household import basket_cost, buffer_target, dues
    cfg, spec = town.cfg, hustle.spec
    cost = all_told(town, agent, hustle)
    if price is None:
        price = hustle.price
    else:
        cost += price - hustle.price
        if _cheaper_elsewhere(town, agent, hustle, cost):
            return False
    if agent.cash < price:
        return False
    current = agent.subs.get(hustle.need)
    if current is not None:                      # (their own customer is never clearly cheaper than themselves)
        return cost < all_told(town, agent, current) * (1.0 - cfg.switch_friction)
    if spec.essential:
        return True
    spare = agent.income_estimate() - sum(d[3] for d in dues(town, agent))
    if spare >= price * cfg.adopt_margin:
        return True
    cushion = buffer_target(cfg, agent, basket_cost(town, agent, cheapest))
    return agent.cash >= cushion + price * cfg.adopt_cushion_weeks


# --- Jason, 18/11/2026: someone out of work with a side hustle, and the jobs on offer ----------------------
def _mostly_unpaid(owed: int, top: int) -> bool:
    """Is less than half of a loan paid off? `top`: the most that was ever owed on it."""
    return owed > 0 and 2 * owed > top


def owes_a_large_loan(agent, home_counts: bool = False) -> bool:
    """Jason: "a large loan, So they've only paid off less than 50% of their loan". A personal
    loan, or the bank's loan on their side hustle; a loan just taken counts at once. Not the
    loan against their home: to "A side hustle brings in $700 a week and they have a new home
    loan: do they take a $600 job?" Jason said "No, stay" (nearly everyone who owns a home owes
    more than half of it for ten years). `home_counts`, the dial `home_loan_presses`, counts
    the home loan as well, as the rule first stood."""
    hustle = agent.hustle
    return (_mostly_unpaid(agent.loan, agent.loan_top)
            or (home_counts and _mostly_unpaid(agent.home_loan, agent.home_loan_top))
            or (hustle is not None and _mostly_unpaid(hustle.loan, hustle.loan_top)))


def remember_loans(town) -> None:
    """As the week starts: the most owed on each loan since it was last nil. A missed week adds
    its interest to a loan, so the most owed can be more than was borrowed."""
    for agent in town.agents:
        agent.loan_top = max(agent.loan_top, agent.loan) if agent.loan > 0 else 0
        agent.home_loan_top = max(agent.home_loan_top, agent.home_loan) if agent.home_loan > 0 else 0
    for hustle in town.hustles:
        hustle.loan_top = max(hustle.loan_top, hustle.loan) if hustle.loan > 0 else 0


def kept_with_a_job(town, hustle) -> int:
    """What a side hustle or small business would still bring in a week if its owner took a job (C,
    22/11/2026). Its takings less goods over the last quarter follow the hours it would have, never more
    than it used then: the owner's own beside a job (their week less the job, the road and the upkeep of
    their own things) and its staff's. Its staff's wages do not shrink with the hours. The road to the
    job itself is left out."""
    cfg = town.cfg
    if hustle.gross_week <= 0:
        return 0
    owner = hustle.owner
    own = max(0.0, cfg.free_hours - owner.travel_hours - cfg.job_hours - upkeep_hours(town, owner))
    with_job = own + cfg.job_hours * len(hustle.staff)
    share = 1.0 if hustle.used_week <= 0 else min(1.0, with_job / hustle.used_week)
    return max(0, int(hustle.gross_week * share) - wages_due(cfg, hustle))


def least_wage(town, agent, reservation: int) -> int:
    """The least a job must pay for someone out of work to take it. For anyone, their
    reservation. Someone with a side hustle takes a job only if it pays more than the side
    hustle brought in a week over the last quarter (Jason: "Yes, take it", of a job at $600
    beside a side hustle bringing in $200); unless they owe a large loan, when they "take the
    first job offered" as anyone does; or unless they are unhappy "and wanted to get out of
    this hard hustle" (Jason, 19/11/2026)."""
    cfg = town.cfg
    if not cfg.makers_weigh_jobs or agent.hustle is None or owes_a_large_loan(agent, cfg.home_loan_presses):
        return reservation
    if cfg.unhappy_makers_apply and not agent.happy:
        return reservation
    return max(reservation, agent.hustle.profit_week + 1)


def start_week(town) -> None:
    """The hours each side hustle has for customers this week: its owner's spare hours less
    what their own things need. It works from its owner's home. Someone who loses their
    home goes on from where they were; someone who never had one sells where they are found
    (Jason: "Anyone creates, even while struggling")."""
    town.new_ideas.clear()
    remember_loans(town)
    place_orders(town)
    cheapest = None
    for hustle in list(town.hustles):
        owner = hustle.owner
        hustle.waiting = 0                       # of those it turned away last week, the ones who would have bought
        hustle.asked = [agent_id for agent_id in hustle.turned_away if agent_id in town._agents]
        if hustle.asked and hustle.spec is not None:
            if cheapest is None:
                cheapest = cheapest_prices(town)
            hustle.waiting = sum(1 for agent_id in hustle.asked
                                 if would_have_bought(town, town._agents[agent_id], hustle, cheapest))
        hustle.turned_away = {}
        hustle.w_revenue = hustle.w_goods = hustle.w_wages = 0
        hustle.sold = 0.0
        if town.map is not None:
            home = home_spot(owner)
            if home is not None:
                hustle.spot = home
        _set_hours(town, hustle, owner.spare_hours)


def working_week(town) -> None:
    """Each maker of a need serves as many standard plans as their hours allow, oldest
    customer first. The rest go unserved this week and are not billed."""
    cfg = town.cfg
    for hustle in town.hustles:
        if hustle.spec is None:
            continue
        need = hustle.need
        hustle.unserved = {}
        served = plans = 0
        for agent_id, agent in hustle.subs.items():
            plans += agent.plan.get(need, 1)
            if plans > hustle.capacity:
                hustle.unserved[agent_id] = True
            else:
                served = plans
        used = served * hours_per_customer(cfg, hustle.spec)
        owner = hustle.owner
        owner.spare_hours = max(0.0, owner.spare_hours - min(used, hustle.own_hours))
        hustle.q_sold += served
        hustle.q_could += hustle.capacity


# --- Jason, 18/11/2026: a maker buys their goods in town first ------------------------------------------
def reasonable(cfg, outside: int, asked: int) -> bool:
    """Is a price asked in town for a unit of goods "a reasonable price" beside the outside's?
    Jason: $200 against $189, "yes buys in town because it's only $11 difference and they get
    it sooner"; $298 against $189, "from out of town". The line between is the builder's: no
    more than `town_goods_premium` over the outside price."""
    return asked <= outside * (1.0 + cfg.town_goods_premium)


def town_price(town, firm) -> int:
    """What a firm asks a maker in town for a unit of its good: what it costs it to make,
    overhead and all, and `maker_margin` on that; and never less than the outside pays it."""
    cfg = town.cfg
    cost = firm.make_cost() * (1.0 + cfg.overhead_allowance) * (1.0 + cfg.maker_margin)
    return max(firm.spec.export_price, int(round(cost)))


def place_orders(town) -> None:
    """As the week starts: what the makers wanted of each good last week is ordered, in equal
    shares, of the town's firms in that line whose price is reasonable. A firm makes its
    order with the staff it has to spare, before anything for export, and staffs for it."""
    cfg = town.cfg
    wanted, town.goods_wanted = town.goods_wanted, {}
    for firm in town.firms:
        firm.town_target = 0.0
    for name, units in wanted.items():               # (nothing is noted as wanted while `makers_buy_in_town` is off)
        spec = town.needs.get(name)
        if spec is None or spec.make_labour <= 0 or units <= 0:
            continue
        sellers = [f for f in town.firms_for(name) if reasonable(cfg, spec.import_price, town_price(town, f))]
        for firm in sellers:
            firm.town_target = units / len(sellers)


def buy_goods(town, hustle, spec, units: float, outside_cost: int) -> int:
    """A maker buys `units` of a good out of the till: from the town's firms that have made
    some for the makers this week, the cheapest first, and the rest from outside ("they can
    only buy outside the town if they can't get it inside town at a reasonable price first").
    `outside_cost`: what the whole lot would cost from outside. Returns what was spent."""
    budget, spent, left = hustle.cash, 0, units
    if town.cfg.makers_buy_in_town and units > 0:
        town.goods_wanted[spec.name] = town.goods_wanted.get(spec.name, 0.0) + units
        stocked = [(town_price(town, f), f.id, f) for f in town.firms_for(spec.name) if f.town_units > 1e-9]
        for price, _, firm in sorted(stocked):
            take = min(left, firm.town_units)
            if price > 0:                            # goods asked nothing for are not held to the till
                take = min(take, (budget - spent) / price)
            if take <= 1e-9:
                break
            cost = min(budget - spent, int(round(take * price)))
            town.ledger.pay(hustle, firm, cost, "town_goods")
            firm.w_revenue += cost
            firm.town_units -= take
            left -= take
            spent += cost
    rest = outside_cost if left == units else int(round(outside_cost * left / units)) if units > 0 else 0
    rest = min(max(0, rest), budget - spent)
    town.ledger.pay(hustle, OUTSIDE, rest, "import")
    return spent + rest


def sell_leftovers(town) -> None:
    """At the week's end: what a firm made for the town's makers and nobody took is sold
    outside at the export price."""
    for firm in town.alive_firms:
        if firm.town_units > 1e-9:
            revenue = int(round(firm.town_units * firm.spec.export_price))
            town.ledger.pay(OUTSIDE, firm, revenue, "export")
            firm.w_export += revenue
            firm.export_units += firm.town_units
        firm.town_units = 0.0


def _buy_goods(town, hustle) -> None:
    """The goods for every plan served and paid for this week, bought out of what the
    customers paid: so someone with no money can start."""
    need, spec = hustle.need, hustle.spec
    plans = sum(agent.plan.get(need, 1) for agent_id, agent in hustle.subs.items()
                if agent_id not in hustle.unserved and agent.met.get(need))
    units = plans * spec.goods_per_sub
    cost = buy_goods(town, hustle, spec, units, min(int(round(units * spec.import_price)), hustle.cash))
    hustle.w_goods += cost


def after_bills(town) -> None:
    """Once the bills are paid: makers buy the week's goods, and the week goes into the quarter."""
    for hustle in town.hustles:
        if hustle.spec is not None:
            _buy_goods(town, hustle)
        else:                                        # a trade that sells hours: what it sold of what it had
            hustle.q_sold += hustle.sold
            hustle.q_could += hustle.hours
        hustle.q_revenue += hustle.w_revenue
        hustle.q_goods += hustle.w_goods
    pay_staff(town)                                  # a business pays its staff, like its goods, out of the week's takings
    for hustle in town.hustles:
        draw(town, hustle)                           # and what is left in the till is its owner's
    for hustle in list(town.hustles):                # who then pays the bank; four missed in a row end it
        if hustle.loan > 0:
            town.bank.service_hustle(hustle)
            if hustle.loan_missed >= town.cfg.firm_missed_limit:
                stop(town, hustle, "loan")
    sell_leftovers(town)                             # what the town's firms made for makers and nobody took
    ideas(town)
    consider_hustles(town)


# --- the quarter ----------------------------------------------------------------------------------------
def makes_a_living(agent, basket: int) -> bool:
    """Does their side hustle bring in at least half their basket? Then, with no job, they
    count as working and have a position, as someone with a job has."""
    hustle = agent.hustle
    return hustle is not None and 2 * hustle.profit_week >= basket


def quarter(town) -> None:
    """At the end of a quarter each side hustle is reckoned up: what it brought in a week;
    whether it goes on (under a fifth of the customers they could serve, for a whole
    quarter, and they give it up); and its price again, from what their hour is worth now."""
    cfg = town.cfg
    for hustle in list(town.hustles):
        hustle.profit_week = max(0, (hustle.q_revenue - hustle.q_goods - hustle.q_wages) // cfg.quarter_weeks)
        hustle.gross_week = max(0, (hustle.q_revenue - hustle.q_goods) // cfg.quarter_weeks)
        sold_hours = hustle.q_sold if hustle.spec is None else hustle.q_sold * hours_per_customer(cfg, hustle.spec)
        hustle.used_week = sold_hours / cfg.quarter_weeks
        whole = town.week - hustle.started >= cfg.quarter_weeks
        if whole and hustle.q_could <= 0:
            stop(town, hustle, "no hours")
            continue
        if whole and hustle.q_sold < cfg.hustle_quit_share * hustle.q_could:
            stop(town, hustle, "few customers")
            continue
        set_price(town, hustle, price_now(town, hustle), "quarter")
        ask_bank(town, hustle)
        become_company(town, hustle)
        hustle.q_revenue = hustle.q_goods = hustle.q_wages = 0
        hustle.q_sold = hustle.q_could = 0.0


# --- selling hours: repairers and builders ---------------------------------------------------------------
def hour_makers(town, customer, trade: str, under=None) -> list:
    """The makers of this trade the customer could use this week, cheapest hour first: not
    themselves, with hours left, within their reach of home where there is a map, and with
    `under` only those whose hour costs less than that."""
    home = home_spot(customer) if town.map is not None else None
    limit = reach(town, customer) if home is not None else 0
    out = []
    for hustle in town.makers_of.get(trade, ()):
        if hustle.owner is customer or hustle.hours - hustle.sold <= 1e-9:
            continue
        if under is not None and hustle.price >= under:
            continue
        if home is not None and hustle.spot is not None and dist(home, hustle.spot) > limit:
            continue
        out.append(hustle)
    out.sort(key=lambda h: (h.price, h.owner.id))
    return out


def cheapest_hour(town, customer, trade: str):
    """The lowest price of an hour of this trade the customer could buy this week, or None."""
    makers = hour_makers(town, customer, trade)
    return makers[0].price if makers else None


def sell_hours(town, hustle, customer, hours: float, parts_per_hour: float, need=None) -> int:
    """One maker does `hours` for a customer: each hour at the maker's price, and that hour's
    parts with the margin on them. The maker buys the parts: in town first, where `need`
    says whose good they are, then from outside. Returns what the customer paid."""
    cfg, owner = town.cfg, hustle.owner
    charge = min(customer.cash, int(round(hours * (hustle.price + parts_per_hour * (1.0 + cfg.maker_margin)))))
    town.ledger.pay(customer, hustle, charge, "maker_hours")
    customer.spend_week += charge
    hustle.w_revenue += charge
    parts = min(hustle.cash, int(round(hours * parts_per_hour)))
    spec = town.needs.get(need) if need is not None else None
    if spec is not None and spec.import_price > 0 and parts > 0:
        parts = buy_goods(town, hustle, spec, hours * parts_per_hour / spec.import_price, parts)
    else:
        town.ledger.pay(hustle, OUTSIDE, parts, "import")
    hustle.w_goods += parts
    own = min(hours, max(0.0, hustle.own_hours - hustle.sold))       # the owner's own hours go first
    owner.spare_hours = max(0.0, owner.spare_hours - own)
    hustle.sold += hours
    return charge


def buy_hours(town, customer, trade: str, hours: float, parts_per_hour: float, budget: int, under=None,
              need=None) -> float:
    """Buy up to `hours` of this trade, cheapest maker first, spending no more than `budget`.
    `need`: whose good the parts are. Returns the hours done."""
    cfg = town.cfg
    done = 0.0
    for hustle in hour_makers(town, customer, trade, under):
        if hours - done <= 1e-9 or budget <= 0:
            break
        rate = hustle.price + parts_per_hour * (1.0 + cfg.maker_margin)
        take = min(hours - done, hustle.hours - hustle.sold, budget / rate)
        if take <= 1e-9:
            break
        budget -= sell_hours(town, hustle, customer, take, parts_per_hour, need)
        done += take
    return done


# --- starting one ---------------------------------------------------------------------------------------
def can_tool_up(town, agent, cost: int) -> bool:
    """Could they pay for the tools: their cash beyond four weeks of bills, a personal loan,
    and what the bank would lend against their home?"""
    if cost <= 0:
        return True
    return _spare_cash(town, agent) + town.bank.person_credit(agent) + borrowable(town, agent) >= cost


def pay_tools(town, agent, cost: int) -> bool:
    """Buy the tools from outside (Jason: their own money first): their cash beyond four
    weeks of bills, then a personal loan, then a loan against their home, for the gap.
    Nothing is borrowed unless the whole cost is covered."""
    if cost <= 0:
        return True
    if not can_tool_up(town, agent, cost):
        return False
    gap = cost - _spare_cash(town, agent)
    if gap > 0:
        gap -= town.bank.lend_person(agent, gap)
    if gap > 0:
        owned = sum(home_value(town, unit) for unit in homes_of(town, agent))
        town.bank.lend_home(agent, gap, 0, owned=owned)
    town.ledger.pay(agent, OUTSIDE, cost, "import")
    agent.spend_week += cost
    return True


def work_in_sight(town) -> dict:
    """The work there is for each trade that sells hours, in hours a week over the next
    quarter, by whose it is: the upkeep of what people own (repair), the hours left on sets
    being built and on homes being built, spread over the quarter's weeks."""
    cfg = town.cfg
    repair: dict = {}
    for unit in town.own_units:
        if unit.owner is not None:
            repair[unit.owner.id] = repair.get(unit.owner.id, 0.0) + upkeep_need(cfg, unit)[0] * cfg.job_hours
    weeks = cfg.quarter_weeks
    return {"repair": repair,
            "set_building": {a.id: a.set_hours_left / weeks for a in town.agents if a.set_hours_left},
            "home_building": {a.id: a.build.hours_left / weeks for a in town.agents if a.build is not None}}


def own_hour_limit(town, trade: str) -> float:
    """The price of a maker's hour below which it comes to less than an hour of a customer's
    own: what the model says an hour is worth, less the margin a maker puts on that hour's
    parts (a home's upkeep for a repairer, a home's materials for a home builder, none for
    a set builder, whose customer has the parts already)."""
    cfg, home = town.cfg, town.needs.get("housing")
    parts = 0.0
    if home is not None and trade == "repair" and home.upkeep_labour > 0:
        parts = home.upkeep_goods * home.import_price / (home.upkeep_labour * cfg.job_hours)
    elif home is not None and trade == "home_building" and home.build_labour > 0:
        parts = home.build_goods * home.import_price / (home.build_labour * cfg.job_hours)
    return town.hour_value - parts * cfg.maker_margin


def _cheapest_seller(town, agent, spec):
    """The lowest price for this need among the firms and makers within their reach from
    home (all of them where there is no map), or None if nobody in reach sells it."""
    home = home_spot(agent) if town.map is not None and spec.trips_per_week > 0 else None
    limit = reach(town, agent) if home is not None else 0
    best = None
    for seller in town.firms_for(spec.name) + town.makers_of.get(spec.name, []):
        if seller is agent.hustle:
            continue
        if home is not None and seller.spot is not None and dist(home, seller.spot) > limit:
            continue
        if best is None or seller.price < best:
            best = seller.price
    return best


def best_trade(town, agent, in_sight=None):
    """The trade, of those whose tools they can pay for, where their price most undercuts
    the cheapest seller within reach of them: (trade, their price), or None if they would
    undercut nobody. Where nobody in reach sells a need it is the best opening there is.
    A trade that sells hours is set against what an hour of a customer's own comes to, and
    against the cheapest other maker of it if that is less; and it is taken up only with
    enough work in sight to keep them past their first quarter: a fifth of their hours,
    once the hours other makers of it already offer are taken off."""
    cfg = town.cfg
    if in_sight is None:
        in_sight = work_in_sight(town)
    best = None
    for trade, spec in trades(town):
        if not can_tool_up(town, agent, tools_cost(cfg, trade, spec)):
            continue
        if spec is None:
            others = [h for h in town.makers_of.get(trade, ()) if h.owner is not agent]
            work = sum(hours for who, hours in in_sight[trade].items() if who != agent.id) - sum(h.hours for h in others)
            mine = spare_hours(cfg, agent) - upkeep_hours(town, agent)
            if mine <= 0 or work < cfg.hustle_quit_share * mine:
                continue
            price = hour_price(town, agent)
            against = min([own_hour_limit(town, trade)] + [h.price for h in others])
        else:
            price = need_price(town, agent, spec)
            against = _cheapest_seller(town, agent, spec)
        undercut = 1.0 if against is None or against <= 0 else 1.0 - price / against
        if undercut > 0 and (best is None or undercut > best[0]):
            best = (undercut, trade, price)
    return (best[1], best[2]) if best is not None else None


def start_hustle(town, agent, trade: str):
    """Pay for the tools and open the side hustle. None if they cannot pay for the tools."""
    spec = None if trade in HOUR_TRADES else town.needs[trade]
    cost = tools_cost(town.cfg, trade, spec)
    if not pay_tools(town, agent, cost):
        return None
    hustle = open_hustle(town, agent, trade)
    town.event("hustle_started", agent=agent, amount=cost, trade=trade, price=hustle.price)
    return hustle


def consider_hustles(town) -> None:
    """Each week someone with the spare hours and no side hustle may
    start one: one in ten of those out of work or whose income does not cover their basket
    (Jason: a way out of struggling), and of the rest one in a hundred times their appetite
    for risk. They take the trade where they undercut most."""
    from .household import basket_cost
    cfg, rng = town.cfg, town.rng
    if cfg.hustle_rate <= 0 and cfg.hustle_rate_struggling <= 0:
        return
    cheapest = in_sight = None
    for agent in town.agents:
        if agent.hustle is not None or spare_hours(cfg, agent) < cfg.hustle_min_hours:
            continue
        struggling = agent.role is None
        if not struggling:
            if cheapest is None:
                cheapest = cheapest_prices(town)
            struggling = agent.income_estimate() < basket_cost(town, agent, cheapest)
        chance = cfg.hustle_rate_struggling if struggling else cfg.hustle_rate * agent.risk
        if chance <= 0 or rng.random() >= chance:
            continue
        if in_sight is None:
            in_sight = work_in_sight(town)
        pick = best_trade(town, agent, in_sight)
        if pick is not None:
            start_hustle(town, agent, pick[0])


# --- ideas: where new things come from ---------------------------------------------------------------------
def ideas(town) -> None:
    """Jason, 16/11/2026: new things come from people, for the fun of it, and time is the
    main thing. Each week someone has a chance of an idea for every twenty spare hours they
    have left once their own things, their side hustle and their building have had theirs.
    An idea is a new need, made as the WEF world makes one, and it is open: its creator may
    start it as a side hustle at once, and anyone else from next week. Nobody is paid for it."""
    from .corporate import invent_need
    cfg, rng = town.cfg, town.rng
    if cfg.idea_rate <= 0:
        return
    for agent in town.agents:
        if agent.spare_hours <= 0:
            continue
        if rng.random() >= cfg.idea_rate * agent.spare_hours / cfg.idea_hours:
            continue
        spec = invent_need(town)
        town.new_ideas.add(spec.name)
        town.ideas_total += 1
        town.event("idea", agent=agent, need=spec.name)
        if agent.hustle is None and spare_hours(cfg, agent) >= cfg.hustle_min_hours:
            start_hustle(town, agent, spec.name)


# --- a small business: the loan on profit, and staff --------------------------------------------------------
def ask_bank(town, hustle) -> bool:
    """Jason: "loans is to make it a business ... if the bank thinks it's profitable". A side
    hustle that was full for a whole quarter borrows `hustle_loan_weeks` of its weekly profit,
    if that comes to at least four weeks of the going wage, and is from then a small business:
    still working from home, with no premises, executives or shareholders, it may take on staff."""
    cfg = town.cfg
    if hustle.spec is None:
        return False                             # a repairer's or builder's hour at the going wage would cost more than
                                                 # a customer's own: nobody but those short of hours would buy it
    if hustle.business or town.week - hustle.started < cfg.quarter_weeks:
        return False
    if hustle.q_could <= 0 or hustle.q_sold < cfg.hustle_full_share * hustle.q_could:
        return False
    if town.week < hustle.owner.credit_block_until:
        return False
    amount = int(cfg.hustle_loan_weeks * hustle.profit_week)
    wage = town.typical_wage()
    if amount < 4 * wage:
        return False
    price = price_now(town, hustle, business=True)
    cheapest = cheapest_prices(town)             # the queue is counted at the price the business will charge
    queue = sum(1 for agent_id in hustle.asked
                if would_have_bought(town, town._agents[agent_id], hustle, cheapest, price))
    if staff_wanted(town, hustle, wage, price, queue) < 1:
        return False                             # nobody to take on: they borrow to grow, not for the money
    town.bank.lend_hustle(hustle, amount)
    hustle.business = True
    set_price(town, hustle, price_now(town, hustle), "business")     # staff cost the going wage: so does its hour now
    return True


def staff_wanted(town, hustle, wage: int, price=None, waiting=None) -> int:
    """How many staff a business wants: a worker for every whole week of hours its customers
    need beyond its owner's own, and one more for what is left over if that work would pay
    their wage at the business's price. One it already has for the left-over hours is kept
    while they pay half of it, so that a customer more or less does not cost someone a job.
    `price`, `waiting`: at this price, with this many waiting, in place of what it has now.
    Only a business selling a need has staff."""
    cfg, spec = town.cfg, hustle.spec
    if price is None:
        price = hustle.price
    if waiting is None:
        waiting = hustle.waiting
    hours = hours_per_customer(cfg, spec)
    extra = (hustle.load() + waiting) * hours - hustle.own_hours     # its customers, and those it turned away
    if extra <= 1e-9:
        return 0
    pays = (price - spec.goods_per_sub * spec.import_price) / hours   # what an hour of serving them brings in
    whole = int(extra / cfg.job_hours + 1e-9)
    rest = extra - whole * cfg.job_hours
    if cfg.job_hours * pays < wage:
        return 0                                                      # at this price no worker pays their wage
    has_one_for_the_rest = len(hustle.staff) > whole
    if rest * pays >= (wage / 2 if has_one_for_the_rest else wage):
        whole += 1
    return whole


def hire_staff(town) -> None:
    """Each small business takes on the staff its customers need beyond its owner's own
    hours, at the going wage, and lets go those it no longer needs (the longest-serving first
    since Jason's ruling of 19/11/2026; the last hired where that dial is off).
    It hires residents with no job, after the firms have hired; it brings nobody to town."""
    cfg = town.cfg
    businesses = [h for h in town.hustles if h.business]
    if not businesses:
        return
    wage = town.typical_wage()
    prices = cheapest_prices(town)                                # once, for everyone's floor (the review, 21/11/2026)
    for hustle in businesses:
        hustle.wage = wage
        for agent in hustle.staff:
            if not cfg.staff_keep_pay or agent.wage < wage:      # (Jason, 19/11/2026) "Old staff members still stay on the same pay rate"
                agent.wage = wage
        want = staff_wanted(town, hustle, wage)
        while len(hustle.staff) > want:
            separate(town, first_to_go(cfg, hustle.staff), "laid_off")
        if len(hustle.staff) < want:
            # the first week of someone new brings in nothing until the customers have signed up:
            # they are taken on only with a week of their wage in hand (the bank's loan is for this)
            in_hand = hustle.cash + hustle.owner.cash
            for agent in town.agents:
                if len(hustle.staff) >= want or in_hand < wage:
                    break
                if agent.role is not None or agent.klass == "owner" or agent is hustle.owner:
                    continue
                if wage >= least_wage(town, agent, reservation_wage(cfg, agent, town, prices)) and can_get_to(town, agent, hustle):
                    hire(town, hustle, agent, "resident")              # (someone with a side hustle of their own weighs it)
                    in_hand -= wage
        _set_hours(town, hustle, hustle.owner.spare_hours)       # this week's hours, with the staff it now has


def wages_due(cfg, hustle) -> int:
    """What a small business owes its staff this week: the going wage each, or what each
    keeps where staff keep their pay (Jason, 19/11/2026)."""
    if cfg.staff_keep_pay:
        return sum(a.wage for a in hustle.staff)
    return hustle.wage * len(hustle.staff)


def pay_staff(town) -> None:
    """Each small business pays its staff out of its till, once the week's customers have
    paid and the goods are bought: a firm pays wages before it is paid and borrows if short;
    someone working from home cannot, and the takings are not theirs to live on until the
    people who earned them are paid. If the till is short its owner makes it up from their
    own cash; while till and owner together cannot pay them all, someone is let go (the
    longest-serving first since 19/11/2026; the last hired where that dial is off)."""
    cfg = town.cfg
    for hustle in town.hustles:
        if not hustle.staff:
            continue
        owner = hustle.owner
        while hustle.staff and hustle.cash + owner.cash < wages_due(cfg, hustle):
            separate(town, first_to_go(cfg, hustle.staff), "unpaid")
        short = wages_due(cfg, hustle) - hustle.cash
        if short > 0:
            town.ledger.pay(owner, hustle, short, "maker_capital")
        total = 0
        for agent in hustle.staff:
            wage = agent.wage if cfg.staff_keep_pay else hustle.wage
            town.ledger.pay(hustle, agent, wage, "wage")
            agent.income_week += wage
            total += wage
        hustle.reserve = min(hustle.reserve, hustle.cash)            # the bank's money goes before the owner's own
        hustle.w_wages += total
        hustle.q_wages += total


# --- becoming a company ----------------------------------------------------------------------------------------
def become_company(town, hustle):
    """A maker or small business owner who has saved the capital any resident needs to found
    a firm may found one by the WEF rule, with premises and shares, and bring their customers
    and staff. From then it is a company, and its price never falls (Jason). Only from a need:
    no firm in the model sells hours. The loan on profit is repaid first. Returns the firm, or
    None if they do not, or if no spot can be had (then nothing changes)."""
    from .corporate import found_firm
    cfg, owner, spec = town.cfg, hustle.owner, hustle.spec
    if spec is None:
        return None
    loan = hustle.loan
    capital = int((owner.cash + hustle.cash - loan) * cfg.founder_invest_share)
    if capital < cfg.flow_entry_capital:
        return None
    if town.rng.random() >= cfg.resident_founder_rate * owner.risk:
        return None
    floor = int(round(unit_cost(cfg, spec, town.typical_wage()) * (1.0 + cfg.cost_floor_markup)))
    firm = found_firm(town, owner, capital, spec, price=max(hustle.price, floor), near=hustle.spot)
    if firm is None:
        return None
    hustle.reserve = 0                           # what is in the business is its owner's now, and the loan theirs to repay
    draw(town, hustle)
    if loan > 0:
        town.ledger.pay(owner, OUTSIDE, loan, "loan_principal")
        hustle.loan = hustle.loan_pay = hustle.loan_missed = 0
    need, brought = hustle.need, len(hustle.subs)
    for agent in list(hustle.subs.values()):
        size = agent.plan.get(need, 1)
        unsubscribe(town, agent, need, "company")
        subscribe(town, agent, firm, "company")
        if size > 1:
            set_plan(town, agent, firm, size)
    for agent in list(hustle.staff):
        kept = agent.wage
        hustle.staff.remove(agent)
        # the same employer under a new name: where staff keep their pay, they keep it (Jason, 19/11/2026)
        hire(town, firm, agent, "company", wage=kept if firm.own_rates and kept > firm.wage else None)
    _close(town, hustle)
    town.event("maker_company", agent=owner, firm=firm, amount=capital, qty=brought, trade=need)
    return firm
