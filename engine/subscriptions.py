"""Signing up for a need, dropping it, and finding who sells it."""

from __future__ import annotations

from .entities import Hustle
from .places import (dist, find_home, home_spot, note_stranded, reach, rides, time_cost,
                     travel_hours, unit_rent, work_spot)


def price_paid(agent, need_name: str) -> int:
    """What the agent pays a week for this need. A home's rent depends on where it stands
    and whether it is a better home; a bigger plan costs that many standard plans."""
    if need_name == "housing":
        unit = agent.unit.get("housing")
        if unit is not None:
            return unit_rent(unit)
    return agent.subs[need_name].price * agent.plan.get(need_name, 1)


def standard_price(agent, need_name: str) -> int:
    """What the agent would pay for this need at standard size: a standard plan, and for a
    home what it would rent for as a standard one."""
    if need_name == "housing":
        unit = agent.unit.get("housing")
        if unit is not None:
            return unit_rent(unit, standard=True)
    return agent.subs[need_name].price


def cheapest_prices(town) -> dict[str, int]:
    """The cheapest price on offer for each need. A base need that nobody sells at the
    moment keeps the last price it had, so the basket does not look cheaper because a
    firm closed. An invented need is in the result only while someone sells it."""
    out: dict[str, int] = {}
    for firm in town.firms:
        if firm.alive and (firm.need not in out or firm.price < out[firm.need]):
            out[firm.need] = firm.price
    if town.hustles:
        # RTR 2: the cheapest price someone could buy at. A maker with room this week is on
        # offer to anyone, so their price counts beside the firms'; a full one is not, and
        # moves nobody's yardstick. A need no firm sells is on offer at the cheapest maker's.
        made: dict[str, int] = {}
        with_room: dict[str, int] = {}
        for hustle in town.hustles:
            if hustle.spec is None:
                continue
            need, price = hustle.need, hustle.price
            if need not in made or price < made[need]:
                made[need] = price
            if hustle.load() < hustle.capacity and (need not in with_room or price < with_room[need]):
                with_room[need] = price
        for need, price in made.items():
            if need not in out:
                out[need] = price
        for need, price in with_room.items():
            if price < out[need]:
                out[need] = price
    town.last_price.update(out)
    for name, spec in town.needs.items():
        if not spec.invented and name not in out:
            out[name] = town.last_price.get(name, spec.initial_price)
    return out


def wants(agent, spec) -> bool:
    """The four base needs suit everyone. An invented need suits only some tastes."""
    if not spec.invented:
        return True
    return (agent.taste + spec.salt) % 1.0 < spec.appeal


def per_customer_labour(firm) -> float:
    """Worker-weeks it takes this firm to serve one customer for a week."""
    spec = firm.spec
    labour = spec.service_labour
    if firm.make_mode == "make":
        labour += spec.goods_per_sub * spec.make_labour
    return labour


def has_room(town, firm) -> bool:
    """Can the firm take one more customer? A home or appliance set must be free. A service
    firm signs up only about as many as its staff can serve: a little headroom so it can
    grow, and a few to get a new firm started."""
    if isinstance(firm, Hustle):
        return firm.load() < firm.capacity       # RTR 2: a maker serves what their hours this week allow
    spec = firm.spec
    if spec.kind == "asset":
        return any(u.occupant is None and u.rent <= 0 for u in firm.units)   # a single home (RTR) is let by name
    need = per_customer_labour(firm)
    if need <= 0:
        return True
    cfg = town.cfg
    staff = len(firm.staff) - spec.fixed_labour                # a fixed crew serves nobody by itself
    if spec.fixed_labour > 0 and staff <= 0:
        return False                                           # it cannot carry anyone yet
    return firm.load() < staff / need * (1.0 + cfg.signup_headroom) + cfg.signup_min


def all_told(town, agent, firm) -> int:
    """What buying from this firm costs the agent a week: its price, the time on the road to
    its premises, and the fare as well when it is beyond a walk and they need no ride for
    work. Just the price where there is no map, or nothing to travel to."""
    cost = firm.price
    spec = firm.spec
    if town.map is None or agent is None or spec.trips_per_week <= 0 or firm.spot is None:
        return cost
    home = home_spot(agent)
    if home is None:
        return cost
    cfg = town.cfg
    blocks = dist(home, firm.spot)
    cost += time_cost(town, travel_hours(cfg, spec.trips_per_week, blocks, rides(agent)))
    if blocks > cfg.walk_range and rides(agent):
        work = agent.employer.spot if agent.employer is not None and agent.role != "ceo" else None
        if work is None or dist(home, work) <= cfg.walk_range:
            cost += agent.subs["transport"].price    # the ride is for the shop, so the shop costs the fare
    return cost


def find_provider(town, agent, need_name: str, exclude=None):
    """The live firm for this need that costs the agent least and can take one more
    customer. Where there is a map, a need that means trips to the firm's premises can
    only be bought within reach, and the time on the road is added to the price. If the
    best firm is full it notes who it turned away, so it can staff up for them."""
    spec = town.needs.get(need_name)
    home = None
    if town.map is not None and agent is not None and spec is not None and spec.trips_per_week > 0:
        home = home_spot(agent)
    limit = reach(town, agent) if home is not None else 0
    fast = home is not None and rides(agent)
    best = cheapest = None
    best_cost = cheapest_cost = 0
    sellers = 0
    selling = town.firms_for(need_name)
    if town.hustles:                         # RTR 2: and the makers of it, though nobody buys from themselves
        selling = selling + [h for h in town.makers_of.get(need_name, ()) if h.owner is not agent]
    for firm in selling:
        if firm is exclude:
            continue
        sellers += 1
        if home is not None and firm.spot is not None and dist(home, firm.spot) > limit:
            continue                         # they cannot get there
        cost = all_told(town, agent, firm)
        if cheapest is None or cost < cheapest_cost:
            cheapest, cheapest_cost = firm, cost
        if has_room(town, firm) and (best is None or cost < best_cost):
            best, best_cost = firm, cost
    if agent is not None:
        if cheapest is None and sellers > 0 and home is not None:
            note_stranded(town, agent, need_name)        # sellers exist, none within reach
        elif cheapest is not None and cheapest is not best and cheapest.spec.kind == "flow":
            cheapest.turned_away[agent.id] = True
    return best


def subscribe(town, agent, firm, reason: str = "start", unit=None) -> bool:
    """Sign up. For a home or an appliance set the firm must have a free unit: the one
    named, or else its free unit in the best condition."""
    spec = firm.spec
    if spec.name in agent.subs:
        return False
    if spec.kind == "asset":
        if unit is None:
            free = [u for u in firm.units if u.occupant is None and u.rent <= 0]
            if not free:
                return False
            unit = max(free, key=lambda u: (u.scale == 1.0, u.cond, -u.id))   # a standard one first
        elif unit.occupant is not None or unit.firm is not firm:
            return False
        unit.occupant = agent
        unit.empty_since = None
        agent.unit[spec.name] = unit
        if unit.rent > 0:                    # RTR 1b: a home on no landlord's block is off the list of those to let
            if unit in town.to_let:
                town.to_let.remove(unit)
        elif unit.spot is not None:
            unit.spot.occupied += 1
            if unit.scale > 1.0:
                unit.spot.better_let += 1
    agent.subs[spec.name] = firm
    agent.arrears[spec.name] = 0
    firm.subs[agent.id] = agent
    if spec.invented:
        agent.had[spec.name] = town.week      # the week they last held it
    town.event("sub_start", agent=agent, firm=firm, amount=firm.price, need=spec.name, reason=reason,
               unit=agent.unit[spec.name].id if spec.kind == "asset" else None)
    return True


def unsubscribe(town, agent, need_name: str, reason: str) -> None:
    """Drop a need. A home or appliance set goes back to the firm. The agent stays in town."""
    firm = agent.subs.pop(need_name, None)
    if firm is None:
        return
    firm.subs.pop(agent.id, None)
    firm.unserved.pop(agent.id, None)
    firm.extra -= agent.plan.pop(need_name, 1) - 1
    unit = agent.unit.pop(need_name, None)
    if unit is not None:
        unit.occupant = None
        unit.empty_since = town.week
        if unit.rent > 0:                    # RTR 1b: back on the list of homes to let
            if unit.firm is firm and unit not in town.to_let:
                town.to_let.append(unit)
        elif unit.spot is not None:
            unit.spot.occupied -= 1
            if unit.scale > 1.0:
                unit.spot.better_let -= 1
    agent.arrears.pop(need_name, None)
    town.event("sub_end", agent=agent, firm=firm, need=need_name, reason=reason,
               unit=unit.id if unit is not None else None)


def set_plan(town, agent, firm, size: int) -> None:
    """A customer moves to a plan of `size` standard plans (1: standard)."""
    name = firm.need
    firm.extra += size - agent.plan.get(name, 1)
    if size == 1:
        agent.plan.pop(name, None)
    else:
        agent.plan[name] = size
    town.event("plan_change", agent=agent, firm=firm, amount=firm.price * size, qty=size, need=name)


def home_available(town, work=None) -> bool:
    """Is a home free? Where there is a map: one within reach of `work`."""
    if town.map is None:
        return bool(town.to_let) or find_provider(town, None, "housing") is not None   # RTR 1b: or a home someone lets
    return find_home(town, None, work=work) is not None


def rent_home(town, agent, reason: str, work=None, max_rent=None, better=False) -> bool:
    """Rent the home that suits the agent best: the cheapest once the time to work is
    counted, within reach of work. Without a map: the cheapest landlord with a free home.
    With `better`, only a better home."""
    if town.map is None:
        if better:
            unit = free_better_home(town, max_rent)
            return unit is not None and subscribe(town, agent, unit.firm, reason, unit=unit)
        firm = find_provider(town, agent, "housing")
        loose = min((u for u in town.to_let if max_rent is None or u.rent <= max_rent),
                    key=lambda u: (u.rent, u.id), default=None)   # RTR 1b: with no map, the cheapest rent wins
        if loose is not None and (firm is None or loose.rent < firm.price):
            return subscribe(town, agent, loose.firm, reason, unit=loose)
        if firm is None or (max_rent is not None and firm.price > max_rent):
            return False
        return subscribe(town, agent, firm, reason)
    unit = find_home(town, agent, work=work, max_rent=max_rent, better=better)
    if unit is None or not subscribe(town, agent, unit.firm, reason, unit=unit):
        return False
    job = work if work is not None else work_spot(agent)
    if job is not None and agent.role != "ceo" and dist(unit.spot, job) > town.cfg.walk_range:
        ensure_transport(town, agent)        # the home is a ride from work: the ride comes with it
    return True


def free_better_home(town, max_rent=None):
    """Without a map: the cheapest free better home any landlord has, or None."""
    free = [u for f in town.firms_for("housing") for u in f.units
            if u.occupant is None and u.scale > 1.0 and (max_rent is None or unit_rent(u) <= max_rent)]
    return min(free, key=lambda u: (unit_rent(u), -u.cond, u.id)) if free else None


def move_home(town, agent, unit, reason: str) -> None:
    old = home_spot(agent)
    unsubscribe(town, agent, "housing", "moved")
    subscribe(town, agent, unit.firm, "moved", unit=unit)
    town.event("moved_home", agent=agent, firm=unit.firm, reason=reason,
               old=old.id if old is not None else None,
               new=unit.spot.id if unit.spot is not None else None)


def ensure_transport(town, agent) -> bool:
    """Take up transport if they do not have it. False if there is none to be had."""
    if rides(agent):
        return True
    firm = find_provider(town, agent, "transport")
    return firm is not None and subscribe(town, agent, firm, "needed")


def settle_arrival(town, agent, work=None) -> bool:
    """A new arrival rents a home and signs up for the other base needs on offer.
    Returns False, and changes nothing, if no home is free (within reach of `work`)."""
    if not rent_home(town, agent, "arrival", work=work):    # a home a ride from work comes with the ride
        return False
    sign_up_for_the_rest(town, agent)
    return True


def sign_up_for_the_rest(town, agent) -> None:
    """A new arrival with a home signs up for the other base needs on offer."""
    for name, spec in town.needs.items():
        if spec.invented or name == "housing":
            continue
        firm = find_provider(town, agent, name)
        if firm is not None:
            subscribe(town, agent, firm, "arrival")


def note_turned_away(town) -> None:
    """Someone wanted to move to town and no home was free. Landlords see the demand."""
    for firm in town.firms_for("housing"):
        firm.unmet_demand += 1.0
