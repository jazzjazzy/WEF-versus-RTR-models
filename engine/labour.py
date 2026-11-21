"""Jobs: hiring, leaving, promotion, and the weekly labour market."""

from __future__ import annotations

INVOLUNTARY = frozenset({"laid_off", "firm_failed", "wound_up", "ousted", "unpaid", "out_of_reach"})


def hire(town, firm, agent, source: str = "resident", wage: int | None = None) -> None:
    """`wage`: what they are taken on at, where that is not the firm's wage (RTR: the staff of
    a business that becomes a company keep their rate)."""
    cfg = town.cfg
    agent.employer = firm
    agent.role = "staff"
    agent.wage = firm.wage if wage is None else wage
    agent.weeks_out = 0
    agent.hired_week = town.week
    firm.staff.append(agent)
    agent.security = min(1.0, agent.security + cfg.boost_hired)
    town.bank.reinstate(agent)
    agent.last_trigger = "hired"
    town.event("hire", agent=agent, firm=firm, amount=agent.wage, source=source)


def separate(town, agent, reason: str) -> None:
    """The agent leaves their job. Losing it against their will is a shock and calls any loan."""
    firm = agent.employer
    if firm is None:
        return
    cfg = town.cfg
    role = agent.role
    if role == "staff":
        firm.staff.remove(agent)
    elif role == "exec":
        firm.execs.remove(agent)
    elif role == "ceo":
        firm.ceo = None
    owed = firm.accrual.pop(agent.id, 0)          # wages held back for shares not yet granted
    if owed > 0:
        town.ledger.pay(firm, agent, min(owed, firm.cash), "wage")
    agent.last_wage = agent.wage
    agent.employer = None
    agent.role = None
    agent.wage = 0
    agent.weeks_out = 0
    agent.last_trigger = reason
    involuntary = reason in INVOLUNTARY
    town.event("layoff" if involuntary else "quit", agent=agent, firm=firm,
               amount=agent.last_wage, reason=reason, role=role)
    if involuntary:
        agent.shock(cfg, cfg.shock_job_loss)
        if town.bank.call(agent):
            agent.shock(cfg, cfg.shock_loan_called)


def first_to_go(cfg, staff):
    """Whoever an employer has to let go: the last hired; in the RTR world the longest-serving
    (Jason, 19/11/2026: "we will sack the oldest staff member"). Staff are kept in order of hiring."""
    return staff[0] if cfg.rtr and cfg.longest_serving_first else staff[-1]


def promote(town, firm, agent) -> None:
    firm.staff.remove(agent)
    firm.execs.append(agent)
    agent.role = "exec"
    agent.staff_wage = agent.wage           # the rate they were on as staff
    agent.wage = firm.exec_pay(town.cfg)
    agent.last_trigger = "promoted"
    town.event("promotion", agent=agent, firm=firm, amount=agent.wage)


def demote(town, firm, agent) -> None:
    firm.execs.remove(agent)
    cfg = town.cfg
    if cfg.rtr and cfg.longest_serving_first:
        # Where the longest-serving goes first the list is read as the order people joined, so
        # someone put back takes their place by when they joined, not the newest's (the fresh
        # review, 19/11/2026: added at the end, the oldest hand was passed over as the newest).
        place = next((i for i, a in enumerate(firm.staff) if a.hired_week > agent.hired_week), len(firm.staff))
        firm.staff.insert(place, agent)
    else:
        firm.staff.append(agent)
    agent.role = "staff"
    agent.wage = firm.wage
    if firm.own_rates and agent.staff_wage > firm.wage:
        agent.wage = agent.staff_wage       # RTR (Jason, 19/11/2026): "Old staff members still stay on the same pay rate"
    agent.last_trigger = "demoted"
    town.event("demotion", agent=agent, firm=firm, amount=agent.wage)


def reservation_wage(cfg, agent, town=None, cheapest=None) -> int:
    """The least someone out of work would take with nothing else to live on: what they last
    earned, less for feeling insecure, less for every week out of work. In the RTR world, given
    the town, never less than what their own basics cost them a week, the home loan payment left
    out (C, 21/11/2026); but someone who owes a large loan "take[s] the first job offered"
    (Jason, 19/11/2026), so for them there is no floor."""
    least = int(agent.last_wage * agent.security
                * max(0.0, 1.0 - cfg.reservation_decay * agent.weeks_out))
    if town is not None and cfg.rtr and cfg.reservation_covers_basket:
        from .household import basket_cost
        from .rtr_makers import owes_a_large_loan
        if not owes_a_large_loan(agent, cfg.home_loan_presses):
            least = max(least, basket_cost(town, agent, cheapest, loan=False))
    return least


def in_the_line(town, wage: int) -> int:
    """How many residents out of work would take a job at this wage: the line outside a firm.
    Those living on dividends do not apply. RTR (Jason, 19/11/2026): nor does someone whose
    side hustle brings in as much, "unless they're unhappy"."""
    cfg = town.cfg
    line = 0
    cheapest = cheapest_prices(town) if cfg.rtr else None
    for agent in town.agents:
        if agent.role is not None or agent.klass == "owner":
            continue
        least = reservation_wage(cfg, agent, town, cheapest)
        if cfg.rtr and agent.hustle is not None:
            from .rtr_makers import least_wage
            least = least_wage(town, agent, least)
        if wage >= least:
            line += 1
    return line


# --- the weekly labour market ----------------------------------------------------------------
import math

from . import rtr_owning
from .firmops import set_wage, sync_pay
from .places import (dist, find_home, home_cost, home_spot, note_stranded, reach, rides,
                     time_cost, transport_fare, travel_hours, unit_rent)
from .production import upkeep_need
from .subscriptions import (cheapest_prices, ensure_transport, home_available, move_home, note_turned_away,
                            settle_arrival)


def labour_need(firm, cfg) -> float:
    """Worker-weeks of work the firm has this week: service, upkeep, building, making, exports."""
    spec = firm.spec
    customers = firm.load()                # a bigger plan counts as that many customers
    if spec.kind == "flow":
        customers += firm.waiting              # people it turned away last week for want of staff
    if spec.fixed_labour > 0:
        customers = max(customers, cfg.signup_min)   # it staffs for its first few before any come
    customers *= 1.0 + cfg.growth_allowance
    need = customers * spec.service_labour + spec.fixed_labour   # a crew it needs however few it serves
    goods = customers * spec.goods_per_sub
    for unit in firm.units:
        labour, materials = upkeep_need(cfg, unit)
        need += labour * firm.upkeep_level
        goods += materials * firm.upkeep_level
    for project in firm.projects:
        use = min(project.labour_left, cfg.build_crew)
        need += use
        if project.labour_left > 1e-9:
            goods += project.goods_left * use / project.labour_left
    if spec.make_labour > 0:
        if firm.make_mode == "make":
            need += goods * spec.make_labour
        need += firm.export_target * spec.make_labour
        if firm.town_target > 0:                 # RTR: and what the town's makers ordered of it
            need += firm.town_target * spec.make_labour
    return need


def desired_staff(firm, cfg, week: int = 0) -> int:
    need = math.ceil(labour_need(firm, cfg) - 1e-9)
    if need <= 0 and firm.spec.kind == "flow" and week - firm.founded < cfg.startup_weeks:
        return 1                                  # a start-up keeps one worker while it finds customers
    return need


def adjust_executives(town, firm) -> None:
    """One executive for every 25 staff, promoted by skill, demoted when the firm shrinks."""
    target = (len(firm.staff) + len(firm.execs)) // (town.cfg.exec_span + 1)
    while len(firm.execs) < target and firm.staff:
        promote(town, firm, max(firm.staff, key=lambda a: (a.skill, -a.id)))
    while len(firm.execs) > target:
        demote(town, firm, min(firm.execs, key=lambda a: (a.skill, a.id)))


def can_get_to(town, agent, firm) -> bool:
    """Is the firm's premises within the agent's reach from home?"""
    if town.map is None or firm.spot is None:
        return True
    return dist(home_spot(agent), firm.spot) <= reach(town, agent)


def reach_job(town, agent, firm) -> bool:
    """Get within reach of a job that is too far to walk to. They ride from where they
    live if transport can be had and that costs no more than moving; otherwise they move
    to a free home within reach of the job, if there is one they can pay for."""
    cfg = town.cfg
    home = home_spot(agent)
    blocks = dist(home, firm.spot)
    fare = 0 if rides(agent) else transport_fare(town)
    can_ride = home is not None and fare is not None and blocks <= cfg.walk_range * cfg.transport_speed
    unit = None
    if "housing" in agent.subs or home is None:      # RTR: someone who owns their home does not move for a job
        unit = find_home(town, agent, work=firm.spot, max_rent=agent.cash)
    if unit is not None and unit.spot is not home:
        moving = unit_rent(unit) + time_cost(town, travel_hours(
            cfg, cfg.commute_trips, dist(unit.spot, firm.spot), rides(agent)))
        riding = None
        if can_ride:
            riding = (unit_rent(agent.unit["housing"]) + fare
                      + time_cost(town, travel_hours(cfg, cfg.commute_trips, blocks, True)))
        if riding is None or moving < riding:
            far = dist(unit.spot, firm.spot) > cfg.walk_range
            move_home(town, agent, unit, "job")
            if far:
                ensure_transport(town, agent)
            return True
    return can_ride and ensure_transport(town, agent)


def new_worker(town, firm=None):
    """Someone moves to town for a job. None if the town is full or no home is free
    within reach of the job: free to rent or, in the RTR world, one the bank holds empty that
    they can buy (Jason, 18/11/2026)."""
    cfg, rng = town.cfg, town.rng
    work = firm.spot if firm is not None else None
    if cfg.at_cap(town.population):
        return None
    cash = buy = None
    wage = firm.wage if firm is not None else 0
    if not home_available(town, work):
        # RTR (Jason, 18/11/2026): with nothing to rent, a newcomer may buy a home the bank holds empty
        if not (cfg.rtr and cfg.newcomers_buy and town.foreclosed):
            return None
        cash = int(rng.lognormvariate(math.log(cfg.worker_cash_median), cfg.worker_cash_sigma))
        buy = rtr_owning.home_for_newcomer(town, cash, wage, work)
        if buy is None:
            return None
    if cash is None:
        cash = int(rng.lognormvariate(math.log(cfg.worker_cash_median), cfg.worker_cash_sigma))
    agent = town.add_agent(cash=cash, origin="worker")
    if buy is None:
        settle_arrival(town, agent, work=work)
    else:
        rtr_owning.arrive_as_owner(town, agent, *buy, wage, work)
    agent.last_wage = cfg.outside_wage
    town.event("arrival", agent=agent, amount=cash, who="worker", **({"bought": buy[0].id} if buy else {}))
    return agent


def let_go_for_loss(town, firm) -> None:
    """RTR (Jason, 19/11/2026): "if we have five staff members in a business and we have debts
    of Say $2,000, we will sack the oldest staff member until the value of the total wages is
    less than the debt. Before we hire new staff". And, of a firm with cash and no debts that
    loses a little: "No, only if in debt". A firm that owes the bank and lost money over the
    quarter lets its longest-serving staff go, one at a time, until what they were paid a week
    covers a week's share of the loss (never the last of them: a firm with nobody cannot
    work). It is the first thing in the week's hiring; then the firm takes people on as it
    needs them, at its wage.

    Built first at the quarter's review for any firm with a loss, and with a hold on hiring
    until a quarter without one. Counts overturned all three: the hold doubled the share of
    people with no job; a loss alone is more than half of all reviews; and letting go in the
    quarter's last week put everyone let go in that week's record as out of work."""
    loss, firm.loss_to_cover = firm.loss_to_cover, 0
    saved = gone = 0
    while saved < loss and len(firm.staff) > 1:
        who = firm.staff[0]                              # staff are kept in the order they joined
        saved += who.wage
        separate(town, who, "laid_off")
        gone += 1
    if gone:
        sync_pay(town, firm)
        town.event("staff_shed", firm=firm, amount=saved, qty=gone, loss=loss)


def labour_market(town) -> None:
    cfg, rng = town.cfg, town.rng
    firms = town.alive_firms

    # 1. each firm plans: lay off what it does not need, set its executives, count vacancies
    for firm in firms:
        firm.waiting = len(firm.turned_away)
        firm.turned_away = {}
        if firm.loss_to_cover:
            let_go_for_loss(town, firm)
        need = labour_need(firm, cfg)
        desired = desired_staff(firm, cfg, town.week)
        keep = max(desired, math.ceil(need * (1.0 + cfg.staff_slack) - 1e-9))
        spare = len(firm.staff) - keep
        if spare > 0:
            limit = max(cfg.layoff_min, math.ceil(cfg.layoff_rate * len(firm.staff)))
            for _ in range(min(spare, limit)):
                separate(town, first_to_go(cfg, firm.staff), "laid_off")
        adjust_executives(town, firm)
        firm.desired_staff = desired
        firm.vacancies = max(0, desired - len(firm.staff))
        firm.housing_blocked = False

    # Best wage first. Firms paying the same are taken in a fresh random order each week,
    # so no firm gets every applicant just because it was founded first.
    openings = [f for f in firms if f.vacancies > 0]
    tiebreak = {f.id: rng.random() for f in openings}
    openings.sort(key=lambda f: (-f.wage, tiebreak[f.id]))
    room = {f.id: f.vacancies for f in openings}
    # Residents are hired as fast as a firm wants them. People from outside come in more slowly.
    outside = {f.id: max(cfg.hire_min, math.ceil(cfg.hire_rate * len(f.staff))) for f in openings}

    def take(firm, agent, source):
        hire(town, firm, agent, source)
        room[firm.id] -= 1
        firm.vacancies -= 1

    def commute(agent, firm) -> int:
        """What the time to and from this job is worth to the agent each week (Jason: agents
        weigh nearness when choosing jobs). Nothing where there is no map or they have no home."""
        home = home_spot(agent) if town.map is not None else None
        if home is None or firm is None or firm.spot is None:
            return 0
        return time_cost(town, travel_hours(cfg, cfg.commute_trips, dist(home, firm.spot), rides(agent)))

    def ranked(agent):
        """The jobs on offer, best first for this agent: the wage less the cost of the journey."""
        if town.map is None or home_spot(agent) is None:
            return openings
        return sorted(openings, key=lambda f: commute(agent, f) - f.wage)

    # 2. residents out of work apply, best-paid vacancy first. Those living on dividends do not.
    seekers = [a for a in town.agents if a.role is None and a.klass != "owner"]
    rng.shuffle(seekers)
    prices = cheapest_prices(town) if cfg.rtr and seekers else None
    for agent in seekers:
        least = reservation = reservation_wage(cfg, agent, town, prices)
        if cfg.rtr and agent.hustle is not None:     # RTR (Jason, 18/11/2026): a side hustle is weighed against the job
            from .rtr_makers import least_wage
            least = least_wage(town, agent, reservation)
        for firm in ranked(agent):
            if room[firm.id] <= 0:
                continue
            if not can_get_to(town, agent, firm):
                # out of reach: they move for it if a home is free near it, or look at the next
                if firm.wage >= least and reach_job(town, agent, firm):
                    take(firm, agent, "resident")
                    break
                note_stranded(town, agent, "job")
                continue
            if firm.wage >= least:
                take(firm, agent, "resident")
            else:
                why = {"why": "side hustle"} if firm.wage >= reservation else {}
                town.event("offer_refused", agent=agent, firm=firm, amount=firm.wage,
                           reservation=reservation, **why)
            break                                 # the best offer is the only one worth a look

    # 3. staff look around: now and then, or constantly if the bills are not being met
    for agent in town.agents:
        if agent.role != "staff":
            continue
        squeezed = agent.income_week < agent.spend_week or any(agent.arrears.values())
        if rng.random() >= (cfg.search_prob_squeezed if squeezed else cfg.search_prob):
            continue
        rise = 0.0 if squeezed else cfg.move_rise
        journey_now = commute(agent, agent.employer)
        for firm in ranked(agent):
            if room[firm.id] <= 0 or firm is agent.employer or not can_get_to(town, agent, firm):
                continue
            if firm.wage - commute(agent, firm) > agent.wage * (1.0 + rise) - journey_now:
                separate(town, agent, "moved")
                take(firm, agent, "moved")
            break

    # 4. what is still open is filled from outside: at the outside wage or better, a home
    #    must be free, and only while the town is under its cap
    for firm in openings:
        while room[firm.id] > 0 and outside[firm.id] > 0 and not cfg.at_cap(town.population):
            if firm.wage < cfg.outside_wage:
                break
            agent = new_worker(town, firm)
            if agent is None:
                firm.housing_blocked = True
                note_turned_away(town)
                town.no_home_week = town.week
                # homes are free, just not near; or none can be built where anyone could walk from
                far = town.map is not None and (home_available(town)
                                                or town.week - town.reach_stops_building <= 1)
                if far:
                    town.far_arrivals += 1
                why = {"reason": "no home within reach" if far else "no home free"} if town.map is not None else {}
                town.event("arrival_blocked", firm=firm, amount=firm.wage, who="worker", **why)
                break
            take(firm, agent, "outside")
            outside[firm.id] -= 1

    # 5. a firm that cannot fill a vacancy for two weeks bids its wage up
    full = cfg.at_cap(town.population)
    for firm in openings:
        # short of people it was free to take: not merely this week's limit on outside hires
        if room[firm.id] > 0 and (full or outside[firm.id] > 0) and not firm.housing_blocked:
            firm.unfilled_weeks += 1
        else:
            firm.unfilled_weeks = 0
        if firm.unfilled_weeks >= cfg.wage_unfilled_weeks:
            firm.unfilled_weeks = 0
            if not (firm.profit_hist and firm.profit_hist[-1] <= 0):   # not while losing money
                set_wage(town, firm, int(round(firm.wage * (1.0 + cfg.wage_step_up))), "unfilled")

    for agent in town.agents:
        if agent.role is None:
            agent.weeks_out += 1
