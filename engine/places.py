"""The map: spots, distance, reach, time on the road, rents by location, and land.

Jason, 12/11/2026: distance is real; everyone walks until a transport firm exists;
land is free while empty spots remain and changes hands only by sale or lease once
the map is full; rent depends on nearness to work, to shops, and on how popular
the area is.

Anything with no spot is at distance zero from everything. A town with the map
switched off (`map_width = 0`) therefore behaves as it did in stage 1.
"""

from __future__ import annotations


class Spot:
    """One place on the map. It holds one building: a block of homes, a firm's premises
    or a town service."""

    __slots__ = ("id", "x", "y", "kind", "owner", "user", "units", "occupied", "reserved",
                 "ground_rent", "access", "popularity", "rent_factor", "label",
                 "weeks", "full_weeks", "better", "better_let", "private_units", "plots_reserved")

    def __init__(self, id: int, x: int, y: int) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.kind = None            # None (empty), 'homes', 'premises' or 'service'
        self.owner = None           # the firm that owns the land
        self.user = None            # the firm that uses what stands on it (the owner unless leased)
        self.units = []             # the homes on it
        self.occupied = 0           # how many of them are let
        self.better = 0             # how many of them are better homes, and how many of those are let
        self.better_let = 0
        self.private_units = []     # homes on it owned by the people who built them (RTR: a block of plots)
        self.plots_reserved = 0     # plots kept for homes being built
        self.reserved = 0           # homes being built here
        self.ground_rent = 0        # weekly, paid by the user to the owner when the land is leased
        self.access = 0.0           # share of the town's jobs and shops within a walk
        self.popularity = 1.0
        self.rent_factor = 1.0      # a home here rents for the firm's price times this
        self.label = None           # 'bank' or 'broker' for a town service
        self.weeks = 0              # weeks counted this quarter, and weeks its homes were all let
        self.full_weeks = 0

    def __repr__(self) -> str:
        return f"<Spot {self.id} ({self.x},{self.y}) {self.kind or 'empty'}>"


def dist(a, b) -> int:
    """Blocks between two spots, along the grid. Zero if either has no place."""
    if a is None or b is None:
        return 0
    return abs(a.x - b.x) + abs(a.y - b.y)


class TownMap:
    def __init__(self, cfg) -> None:
        self.width = cfg.map_width
        self.height = cfg.map_height
        self.spots = [Spot(y * self.width + x, x, y)
                      for y in range(self.height) for x in range(self.width)]
        self.centre = self.at(self.width // 2, self.height // 2)
        self.scarce = False         # true from the first week no spot is empty, and for good
        self.land_price = 0         # what a spot last sold for, on average

    def at(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.spots[y * self.width + x]
        return None

    def empty(self) -> list:
        return [s for s in self.spots if s.kind is None]

    @property
    def full(self) -> bool:
        return all(s.kind is not None for s in self.spots)

    def homes(self) -> list:
        return [s for s in self.spots if s.kind == "homes"]


# --- putting things on the map ------------------------------------------------------------------
def place_service(town, spot, label: str) -> None:
    spot.kind = "service"
    spot.label = label
    town.event("spot_taken", qty=spot.id, purpose=label, x=spot.x, y=spot.y, price=0)


def _occupy(town, spot, firm, purpose: str, owner) -> None:
    spot.kind = purpose
    spot.owner = owner
    spot.user = firm
    if purpose == "premises":
        firm.spot = spot
    else:
        firm.lots.append(spot)


def take_spot(town, firm, purpose: str, near=None):
    """A firm takes a spot for 'homes' or 'premises'. Free while any spot is empty: a
    housing firm takes the empty spot with the best access, any other firm the empty spot
    nearest where it wants to be. Returns the spot, or None if none can be had."""
    m = town.map
    if m is None:
        return None
    empty = m.empty()
    if empty:
        if purpose == "homes":
            spot = max(empty, key=lambda s: (s.access, -dist(s, m.centre), -s.id))
        else:
            target = near if near is not None else m.centre
            spot = min(empty, key=lambda s: (dist(s, target), s.id))
        _occupy(town, spot, firm, purpose, owner=firm)
        town.event("spot_taken", firm=firm, qty=spot.id, purpose=purpose, x=spot.x, y=spot.y, price=0)
        if len(empty) == 1:
            _land_is_scarce(town)
        return spot
    _land_is_scarce(town)
    return _buy_or_lease(town, firm, purpose, near)


def _land_is_scarce(town) -> None:
    """The first week no spot is empty, land becomes scarce and stays so."""
    m = town.map
    if not m.scarce:
        m.scarce = True
        town.event("land_scarce", qty=len(m.spots))


def room_for_home(town, firm, building: bool = False):
    """A spot where this firm can put one more home: one of its own with room, the
    best-placed first, or else a new spot. When building, it does not take a new spot
    that nobody could get to work or the shops from."""
    cap = town.cfg.homes_per_spot
    best = None
    for spot in firm.lots:
        if len(spot.units) + len(spot.private_units) + spot.reserved < cap:
            if best is None or (spot.access, -spot.id) > (best.access, -best.id):
                best = spot
    if best is not None:
        return best
    if building and town.map is not None:
        empty = town.map.empty()
        if empty and max(s.access for s in empty) <= 0.0:
            town.reach_stops_building = town.week
            return None                      # the only land left is out of everyone's reach
    return take_spot(town, firm, "homes")


def house(town, firm, unit) -> bool:
    """Put a finished home on a spot. False if the firm has nowhere to put it."""
    spot = room_for_home(town, firm)
    if spot is None:
        return False
    place_unit(spot, unit)
    return True


def take_plot(town, work=None, limit=None):
    """A plot for someone to build their own home on (RTR). A block of plots with room, the
    best placed first; or, while a block is empty, the best-placed empty block becomes a block
    of plots, free as land is to a firm while it is not scarce. With `work` and `limit`, only
    a plot within that many blocks of their work: nobody builds where they could not get to
    their job from. The plot is kept for the builder. None when there is no such land, or
    no map."""
    m = town.map
    if m is None:
        return None
    cap = town.cfg.homes_per_spot

    def near(spot) -> bool:
        return work is None or dist(spot, work) <= limit

    best = None
    for spot in m.spots:
        if spot.kind == "plots" and len(spot.private_units) + spot.plots_reserved < cap and near(spot):
            if best is None or (spot.access, -spot.id) > (best.access, -best.id):
                best = spot
    if best is None:
        empty = m.empty()
        if not empty:
            _land_is_scarce(town)
            return None
        within = [s for s in empty if near(s)]
        if not within:
            return None
        best = max(within, key=lambda s: (s.access, -dist(s, m.centre), -s.id))
        best.kind = "plots"
        town.event("spot_taken", qty=best.id, purpose="plots", x=best.x, y=best.y, price=0)
        if len(empty) == 1:
            _land_is_scarce(town)
    best.plots_reserved += 1
    return best


def plot_free(town, work=None, limit=None) -> bool:
    """Would `take_plot` find a plot (within `limit` blocks of `work`, if given)? Nothing is
    taken or kept."""
    m = town.map
    if m is None:
        return False
    cap = town.cfg.homes_per_spot
    for spot in m.spots:
        if work is not None and dist(spot, work) > limit:
            continue
        if spot.kind is None or (spot.kind == "plots" and len(spot.private_units) + spot.plots_reserved < cap):
            return True
    return False


def place_own_unit(spot, unit) -> None:
    """A home someone built goes on the plot kept for it."""
    spot.plots_reserved -= 1
    spot.private_units.append(unit)
    unit.spot = spot


def place_unit(spot, unit) -> None:
    """A home goes up on a spot."""
    spot.units.append(unit)
    unit.spot = spot
    if unit.scale > 1.0:
        spot.better += 1
        if unit.occupant is not None:
            spot.better_let += 1


def make_better(unit, scale: float) -> None:
    """A home becomes a better one (or a standard one again), and its spot keeps count."""
    spot = unit.spot
    if spot is not None:
        step = (scale > 1.0) - (unit.scale > 1.0)
        spot.better += step
        if unit.occupant is not None:
            spot.better_let += step
    unit.scale = scale


# --- access and rent -----------------------------------------------------------------------------
def refresh_access(town) -> None:
    """How well placed each spot is: the share of the town's jobs and of its shops within a
    walk. Then each home's rent factor: its firm's price is the average rent across that
    firm's homes; a better-placed or more popular spot pays more than that, a worse one less."""
    m, cfg = town.map, town.cfg
    if m is None:
        return
    jobs = []
    shops = []
    for firm in town.alive_firms:
        if firm.spot is None:
            continue
        jobs.append((firm.spot, firm.headcount() or 1))
        if firm.spec.trips_per_week > 0:
            shops.append(firm.spot)
    all_jobs = sum(n for _, n in jobs)
    rides = any(f.need == "transport" for f in town.alive_firms)
    w = cfg.access_jobs_weight
    for spot in m.spots:
        near_jobs = sum(n for s, n in jobs if dist(spot, s) <= cfg.walk_range)
        near_shops = sum(1 for s in shops if dist(spot, s) <= cfg.walk_range)
        access = ((w * near_jobs / all_jobs if all_jobs else 0.0)
                  + ((1.0 - w) * near_shops / len(shops) if shops else 0.0))
        if rides:
            access += 0.5 * (1.0 - access)       # somewhere that can be reached is worth something
        spot.access = access
    for firm in town.alive_firms:
        if not firm.lots:
            continue
        raw = {s.id: (1.0 + cfg.location_premium * (2.0 * s.access - 1.0)) * s.popularity
               for s in firm.lots}
        homes = sum(len(s.units) for s in firm.lots)
        mean = (sum(raw[s.id] * len(s.units) for s in firm.lots) / homes) if homes else 1.0
        for s in firm.lots:
            s.rent_factor = raw[s.id] / mean if mean > 0 else 1.0


def unit_rent(unit, standard: bool = False) -> int:
    """A home's weekly rent: its firm's price times the factor for its spot, and for a better
    home times its scale. `standard`: what it would rent for as a standard home."""
    if unit.rent > 0:
        return unit.rent                     # RTR 1b: a home let on no landlord's block has its own rent
    factor = unit.spot.rent_factor if unit.spot is not None else 1.0
    if not standard:
        factor *= unit.scale
    return int(round(unit.firm.price * factor))


# --- where an agent is, how far they can go, what the time costs ---------------------------------
def home_spot(agent):
    unit = agent.unit.get("housing")
    return unit.spot if unit is not None else None


def work_spot(agent):
    return agent.employer.spot if agent.employer is not None else None


def rides(agent) -> bool:
    return "transport" in agent.subs


def reach(town, agent) -> int:
    """Blocks the agent can go one way: a walk, or four times that with transport."""
    cfg = town.cfg
    return int(cfg.walk_range * (cfg.transport_speed if rides(agent) else 1.0))


def travel_hours(cfg, trips: float, blocks: int, fast: bool) -> float:
    """Hours a week spent on `trips` round trips of `blocks` each way."""
    hours = trips * 2.0 * blocks * cfg.minutes_per_block / 60.0
    return hours / cfg.transport_speed if fast else hours


def time_cost(town, hours: float) -> int:
    """What that time is worth to an agent weighing one choice against another."""
    return int(round(hours * town.hour_value))


def note_stranded(town, agent, what: str) -> None:
    """Someone could not get to a job or a shop because of distance. Counted once a quarter."""
    if agent is not None:
        if (agent.id, what) not in town.stranded:
            town.stranded[(agent.id, what)] = True
            town.event("too_far", agent=agent, what=what)
        agent.far = town.week


def tally_stranded(town) -> None:
    """At the end of a quarter: how many people distance kept from a job, from something
    they cannot do without (food), and from any other shop. One person can be in more than
    one count. The total, with the outside workers who found no home within reach of the
    job, is what a founder looks at when deciding whether the town needs transport."""
    job, must, other = set(), set(), set()
    for agent_id, what in town.stranded:
        spec = town.needs.get(what)
        if what == "job":
            job.add(agent_id)
        elif spec is not None and spec.essential:
            must.add(agent_id)
        else:
            other.add(agent_id)
    town.reach_blocked_last = len(job | must | other) + town.far_arrivals
    town.reach_blocked_by = {"job": len(job) + town.far_arrivals, "food": len(must), "other": len(other)}
    town.stranded = {}
    town.far_arrivals = 0


def transport_fare(town):
    """The price of the cheapest transport firm that can take another rider, or None."""
    from .subscriptions import has_room
    best = None
    for firm in town.firms_for("transport"):
        if has_room(town, firm) and (best is None or firm.price < best):
            best = firm.price
    return best


def sold_at(town, name: str) -> list:
    """The spots where this need can be had: the firms that sell it, and in the RTR world the
    makers of it who have room this week (a full maker has none to sell). A maker with room
    and no place of their own sells where they are found: then it can be had anywhere, and
    the answer is None."""
    spots = [f.spot for f in town.firms_for(name) if f.spot is not None]
    if town.hustles:
        for maker in town.makers_of.get(name, ()):
            if maker.load() < maker.capacity:
                if maker.spot is None:
                    return None
                spots.append(maker.spot)
    return spots


def essential_shops(town) -> list:
    """For each need people cannot do without and must make trips for (food), the spots
    where it is sold."""
    out = []
    for name, spec in town.needs.items():
        if spec.essential and spec.trips_per_week > 0:
            spots = sold_at(town, name)
            if spots:
                out.append(spots)
    return out


def far_from_food(town, spot, shops=None) -> bool:
    """Is something people cannot do without sold only beyond a walk of this spot?"""
    walk = town.cfg.walk_range
    for spots in (essential_shops(town) if shops is None else shops):
        if all(dist(spot, s) > walk for s in spots):
            return True
    return False


def ride_for_work(town, agent) -> bool:
    """Do they ride, and is their job beyond a walk of home? A chief executive is not bound
    by the walk to work."""
    if town.map is None or not rides(agent):
        return False
    home = home_spot(agent)
    employer = agent.employer
    return (home is not None and employer is not None and agent.role != "ceo"
            and employer.spot is not None and dist(home, employer.spot) > town.cfg.walk_range)


def needs_ride(town, agent) -> bool:
    """Do they need a ride to get to work or to food? Their job is beyond a walk of home;
    or the food shop they use is; or they have no food shop and none is within a walk.
    A ride they need for either is not something they give up to save money."""
    if town.map is None:
        return False
    home = home_spot(agent)
    if home is None:
        return False
    walk = town.cfg.walk_range
    if (agent.employer is not None and agent.role != "ceo" and agent.employer.spot is not None
            and dist(home, agent.employer.spot) > walk):
        return True
    for name, spec in town.needs.items():
        if not (spec.essential and spec.trips_per_week > 0):
            continue
        shop = agent.subs.get(name)
        if shop is not None:
            if shop.spot is not None and dist(home, shop.spot) > walk:
                return True              # dropping the ride would cost them the shop they use
        else:
            spots = sold_at(town, name)
            if spots and all(dist(home, s) > walk for s in spots):
                return True
    return False


def cut_off_from_food(town, agent, spot) -> bool:
    """Living here, could they get to no food at all: none within a walk, and no ride to be had?"""
    return far_from_food(town, spot) and not rides(agent) and transport_fare(town) is None


def wants_transport(town, agent, fare: int) -> bool:
    """An agent takes transport up when they need it to get to work, when distance has
    lately kept them from a job or a shop, or when the time it would save is worth more
    than it costs."""
    cfg = town.cfg
    if needs_ride(town, agent):
        return True
    if town.week - agent.far <= cfg.quarter_weeks:
        return True
    saved = agent.travel_hours * (1.0 - 1.0 / cfg.transport_speed)
    return time_cost(town, saved) >= fare * cfg.adopt_margin


def find_home(town, agent, work=None, max_rent=None, better=False):
    """The free home that costs least once rent, any transport fare it would need and the
    time to work are added up. It must be within reach of `work` (the agent's own job if not
    given). With `better`, only better homes. Returns the home, or None."""
    cfg = town.cfg
    if work is None and agent is not None:
        work = work_spot(agent)
    riding = agent is not None and rides(agent)
    boss = agent is not None and agent.role == "ceo"     # a chief executive is not bound by the walk to work
    fare = agent.subs["transport"].price if riding else transport_fare(town)   # what a ride costs them
    far = cfg.walk_range * cfg.transport_speed
    shops = essential_shops(town)
    best = None
    for spot in town.map.spots:
        if spot.kind != "homes" or spot.occupied >= len(spot.units) or spot.user is None:
            continue
        kinds = (False,)                     # standard homes only, unless better ones stand here
        if spot.better:
            free_better = spot.better > spot.better_let
            free_plain = len(spot.units) - spot.better > spot.occupied - spot.better_let
            kinds = tuple(k for k, free in ((False, free_plain), (True, free_better)) if free)
        if better:
            kinds = tuple(k for k in kinds if k)
        for is_better in kinds:
            scale = cfg.better_home if is_better else 1.0
            rent = int(round(spot.user.price * spot.rent_factor * scale))
            if max_rent is not None and rent > max_rent:
                continue
            cost = rent
            must_ride = cut_off = False
            if work is not None:
                blocks = dist(spot, work)
                if blocks <= cfg.walk_range or boss:
                    fast = riding
                elif blocks <= far and fare is not None and (max_rent is None or rent + fare <= max_rent):
                    fast = must_ride = True  # a ride from work, and they can pay for the ride as well
                else:
                    continue                 # too far to get to work from here
                cost += time_cost(town, travel_hours(cfg, cfg.commute_trips, blocks, fast))
            if far_from_food(town, spot, shops):
                must_ride = fare is not None
                cut_off = fare is None       # nothing to eat within a walk and no ride: a last resort
            if must_ride:
                cost += fare
            if best is None or (cut_off, cost, spot.id, is_better) < best[0]:
                best = ((cut_off, cost, spot.id, is_better), spot)
    loose = None                             # RTR 1b: homes let on no landlord's block, by the same reckoning
    if town.to_let and not better:
        for unit in town.to_let:
            spot, rent = unit.spot, unit.rent
            if max_rent is not None and rent > max_rent:
                continue
            cost = rent
            must_ride = cut_off = False
            if work is not None and spot is not None:
                blocks = dist(spot, work)
                if blocks <= cfg.walk_range or boss:
                    fast = riding
                elif blocks <= far and fare is not None and (max_rent is None or rent + fare <= max_rent):
                    fast = must_ride = True
                else:
                    continue
                cost += time_cost(town, travel_hours(cfg, cfg.commute_trips, blocks, fast))
            if spot is not None and far_from_food(town, spot, shops):
                must_ride = fare is not None
                cut_off = fare is None
            if must_ride:
                cost += fare
            key = (cut_off, cost, spot.id if spot is not None else -1, False)
            if loose is None or (key, unit.id) < (loose[0], loose[1].id):
                loose = (key, unit)
    if loose is not None and (best is None or loose[0] < best[0]):
        return loose[1]
    if best is None:
        return None
    is_better = best[0][3]
    free = [u for u in best[1].units if u.occupant is None and (u.scale > 1.0) == is_better]
    return max(free, key=lambda u: (u.cond, -u.id))


def home_cost(town, agent, spot, scale: float = 1.0, rent=None) -> int:
    """What living on this spot costs the agent a week: rent (times `scale` for a better
    home; `rent` itself for a home with a rent of its own), the time to work, and the fare
    if they could not get to work or to food from here without a ride."""
    cfg = town.cfg
    if rent is not None:
        cost = rent
    else:
        cost = int(round(spot.user.price * spot.rent_factor * scale)) if spot.user is not None else 0
    work = work_spot(agent)
    must_ride = far_from_food(town, spot)
    if work is not None:
        blocks = dist(spot, work)
        must_ride = must_ride or (blocks > cfg.walk_range and agent.role != "ceo")
        cost += time_cost(town, travel_hours(cfg, cfg.commute_trips, blocks, rides(agent)))
    if must_ride:
        fare = agent.subs["transport"].price if rides(agent) else transport_fare(town)
        cost += fare or 0
    return cost


def reserve_home(town, firm):
    """Room for one more home to be built: a spot of the firm's own, or a new one. A housing
    firm does not build where nobody could get to work or the shops from."""
    spot = room_for_home(town, firm, building=True)
    if spot is not None:
        spot.reserved += 1
    return spot


def update_popularity(town, quarter_end: bool) -> None:
    """Count the week for every block of homes. At the end of a quarter, a block that was
    let in full every week grows more popular, and one with clearly more empty homes than
    its firm's average grows less (Jason: rent depends on how popular the area is)."""
    m, cfg = town.map, town.cfg
    if m is None:
        return
    for spot in m.spots:
        if spot.kind == "homes" and spot.units:
            spot.weeks += 1
            if spot.occupied >= len(spot.units):
                spot.full_weeks += 1
    if not quarter_end:
        return
    for firm in town.alive_firms:
        homes = sum(len(s.units) for s in firm.lots)
        if not homes:
            continue
        empty_share = 1.0 - sum(s.occupied for s in firm.lots) / homes
        for spot in firm.lots:
            if not spot.units:
                continue
            if spot.weeks > 0 and spot.full_weeks == spot.weeks:
                spot.popularity = min(cfg.popularity_max, spot.popularity * (1.0 + cfg.popularity_step))
            elif 1.0 - spot.occupied / len(spot.units) > empty_share + 0.1:
                spot.popularity = max(cfg.popularity_min, spot.popularity * (1.0 - cfg.popularity_step))
            spot.weeks = spot.full_weeks = 0


# --- land once it is scarce ----------------------------------------------------------------------
def asking_price(town, spot) -> int:
    """What its owner asks for a spot, plus a quarter: the most of the floor, six years of
    the rent its homes bring in, and what the homes standing on it are worth."""
    cfg = town.cfg
    rent_roll = sum(unit_rent(u) for u in spot.units if u.occupant is not None)
    standing = spot.user.units_value(cfg, spot.units) if spot.units and spot.user is not None else 0
    value = max(cfg.land_floor, int(rent_roll * cfg.weeks_per_year * cfg.land_years), standing)
    return int(value * (1.0 + cfg.land_markup))


def _buy_or_lease(town, firm, purpose: str, near):
    """No spot is empty. The firm buys the cheapest spot another firm will sell, or leases
    it if it cannot pay (Jason: once the map is full, land changes hands by sale or lease)."""
    cfg, m = town.cfg, town.map
    cap = cfg.homes_per_spot
    candidates = [s for s in m.spots
                  if s.kind == "homes" and s.owner is not None and s.owner is not firm
                  and s.owner.alive and s.user is s.owner and s.reserved == 0
                  and not s.private_units          # RTR: a block with a privately owned home is never sold
                  and (purpose != "homes" or len(s.units) < cap)]
    if not candidates:
        return None
    target = near if near is not None else m.centre
    own_roof = None                          # nobody pulls down the home they live in if another can be had
    if purpose != "homes" and firm.founder_id is not None:
        own_roof = home_spot(town.agent(firm.founder_id))
    spot = min(candidates, key=lambda s: (s is own_roof, asking_price(town, s), dist(s, target), s.id))
    price = asking_price(town, spot)
    seller = spot.owner
    funds = firm.cash - int(cfg.reserve_weeks * firm.last_opex) + town.bank.firm_credit(firm)
    leased = funds < price
    rent = max(1, int(price * cfg.lease_rate / cfg.weeks_per_year))
    if leased and firm.cash < 8 * rent:
        return None                          # cannot even carry the ground rent
    if leased and purpose != "homes" and spot.units:
        return None                          # homes are not pulled down for a ground rent: it must buy them
    if not leased:
        if firm.cash < price:
            town.bank.lend_firm(firm, price - firm.cash)
        town.ledger.pay(firm, seller, price, "land_sale")
    _hand_over(town, spot, firm, purpose, seller)
    spot.owner = seller if leased else firm
    spot.ground_rent = rent if leased else 0
    refresh_land_values(town)
    if not leased:
        m.land_price = price if m.land_price == 0 else int(0.7 * m.land_price + 0.3 * price)
        town.bank.repay_excess(seller)       # what it sold no longer secures its loan
    if leased:
        town.event("lease_started", firm=firm, amount=rent, qty=spot.id, owner=seller.id,
                   purpose=purpose, asked=price)
    else:
        town.event("spot_sold", firm=firm, amount=price, qty=spot.id, seller=seller.id, purpose=purpose)
    return spot


def _hand_over(town, spot, firm, purpose: str, seller) -> None:
    """What stands on the spot passes to the new user. A housing firm keeps the homes and
    the tenants. Any other firm pulls the homes down for its premises: the tenants are put
    out first and stay in town."""
    from .subscriptions import unsubscribe
    seller.lots.remove(spot)
    if purpose == "homes":
        _pass_homes(spot, seller, firm)
        spot.user = firm
        firm.lots.append(spot)
        return
    seller.projects = [p for p in seller.projects if p.unit is None or p.unit.spot is not spot]
    put_out = 0                              # nobody goes on rebuilding a home that is coming down
    for unit in spot.units:
        if unit.occupant is not None:
            tenant = unit.occupant
            unsubscribe(town, tenant, "housing", "redeveloped")
            tenant.shock(town.cfg, town.cfg.shock_eviction)
            put_out += 1
        seller.units.remove(unit)
        unit.spot = None
    town.event("homes_pulled_down", firm=firm, qty=len(spot.units), spot=spot.id, tenants=put_out,
               seller=seller.id)
    spot.units = []
    spot.occupied = spot.better = spot.better_let = 0
    spot.popularity = 1.0
    spot.kind = "premises"
    spot.user = firm
    firm.spot = spot


def _pass_homes(spot, old, new) -> None:
    """The homes on a block pass from one landlord to another as they stand: the tenants
    stay, and a rebuild under way goes with its home."""
    for unit in spot.units:
        old.units.remove(unit)
        unit.firm = new
        new.units.append(unit)
        tenant = unit.occupant
        if tenant is not None:
            old.subs.pop(tenant.id, None)
            tenant.subs[new.need] = new
            new.subs[tenant.id] = tenant
    rebuilds = [p for p in old.projects if p.unit is not None and p.unit.spot is spot]
    if rebuilds:
        old.projects = [p for p in old.projects if p.unit is None or p.unit.spot is not spot]
        new.projects.extend(rebuilds)


def hand_back_leased_blocks(town, firm) -> None:
    """A landlord that is closing gives back the blocks it leased as they stand. The homes
    and the people in them go to the landlord who owns the land."""
    for spot in list(firm.lots):
        owner = spot.owner
        if owner is None or owner is firm or not owner.alive or owner.need != firm.need:
            continue
        _pass_homes(spot, firm, owner)
        firm.lots.remove(spot)
        owner.lots.append(spot)
        spot.user = owner
        spot.ground_rent = 0
        spot.reserved = 0                    # whatever the closing firm was building there is abandoned
        town.event("lease_ended", firm=firm, qty=spot.id, owner=owner.id, homes=len(spot.units))


def _bare_lot(spot, owner) -> None:
    """Land with nothing on it, held by a housing firm that can build homes there."""
    spot.kind = "homes"
    spot.owner = spot.user = owner
    spot.units = []
    spot.occupied = spot.reserved = spot.better = spot.better_let = 0
    spot.ground_rent = 0
    spot.popularity = 1.0
    if spot not in owner.lots:
        owner.lots.append(spot)


def _free(spot) -> None:
    spot.kind = spot.owner = spot.user = spot.label = None
    spot.units = []
    spot.occupied = spot.reserved = spot.ground_rent = spot.better = spot.better_let = 0
    spot.popularity = spot.rent_factor = 1.0


def give_up_spots(town, firm) -> None:
    """A firm that is closing gives up its land. Before land is scarce the spot is simply
    empty again. Once it is scarce the spot is sold to the housing firm with the most cash,
    at the floor price or whatever that firm can pay, and the money joins the closing
    firm's cash. Leased land goes back to its owner."""
    m = town.map
    if m is None:
        return
    cfg = town.cfg
    for spot in m.spots:
        if spot.user is not firm and spot.owner is not firm:
            continue
        if spot.user is not firm:            # it was only the landlord: the firm using it now owns it
            spot.owner = spot.user
            spot.ground_rent = 0
            continue
        if spot.owner is not firm:           # it was leasing: the land goes back, bare
            _bare_lot(spot, spot.owner)
            continue
        if spot.private_units:               # RTR: people own homes here: it becomes a block of plots
            spot.kind = "plots"
            spot.owner = spot.user = None
            spot.units = []
            spot.occupied = spot.reserved = spot.ground_rent = spot.better = spot.better_let = 0
            spot.popularity = spot.rent_factor = 1.0
            town.event("block_to_plots", firm=firm, qty=spot.id, homes=len(spot.private_units))
            continue
        buyer = None
        if m.scarce:
            for other in town.firms_for("housing"):
                if other is not firm and other.cash > 0 and (buyer is None or other.cash > buyer.cash):
                    buyer = other
        if buyer is None:
            _free(spot)
            continue
        price = min(cfg.land_floor, buyer.cash)
        town.ledger.pay(buyer, firm, price, "land_sale")
        _bare_lot(spot, buyer)
        town.event("spot_sold", firm=buyer, amount=price, qty=spot.id, seller=firm.id, purpose="homes")
    firm.spot = None
    firm.lots = []


def pay_ground_rents(town) -> list:
    """Ground rent on leased land, paid each week by the firm using it to the firm that
    owns it. Returns the firms that have now missed too many payments."""
    m = town.map
    if m is None:
        return []
    paid, short = {}, {}
    for spot in m.spots:
        if spot.ground_rent <= 0 or spot.user is None or spot.owner is None or spot.user is spot.owner:
            continue
        user, owner = spot.user, spot.owner
        if user.cash >= spot.ground_rent:
            town.ledger.pay(user, owner, spot.ground_rent, "ground_rent")
            owner.w_revenue += spot.ground_rent
            user.w_goods += spot.ground_rent
            paid[user.id] = user
        else:
            short[user.id] = user
    late = []
    for user in paid.values():
        if user.id not in short:
            user.rent_missed = 0             # every ground rent it owed this week was paid
    for user in short.values():
        user.rent_missed += 1                # a week with any ground rent unpaid is a week missed
        if user.rent_missed >= town.cfg.firm_missed_limit:
            late.append(user)
    return late


def refresh_land_values(town) -> None:
    """Land a firm owns is security for a loan at the floor price once land is scarce.
    While spots are free for the taking, land is worth nothing. What spots actually
    change hands for is recorded on the map and secures nothing: one dear sale does not
    revalue every owner's land."""
    m = town.map
    if m is None:
        return
    worth = town.cfg.land_floor if m.scarce else 0
    owned: dict[int, int] = {}
    for spot in m.spots:
        if spot.owner is not None:
            owned[spot.owner.id] = owned.get(spot.owner.id, 0) + 1
    for firm in town.firms:
        firm.land_value = owned.get(firm.id, 0) * worth if firm.alive else 0
