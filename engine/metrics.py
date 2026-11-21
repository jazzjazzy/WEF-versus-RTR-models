"""The weekly measures. Every per-person measure is reported four ways: for everyone,
for the owner class, for the working class and for the out of work (Jason, 12/11/2026)."""

from __future__ import annotations

import math

from .rtr_owning import housed
from .places import dist, home_spot, unit_rent
from .subscriptions import cheapest_prices

SCOPES = ("all", "owner", "working", "out")
RANK = {"out": 0, "working": 1, "owner": 2}


def gini(values) -> float:
    """0 when everyone holds the same, towards 1 when one holds it all. 0 for nothing at all."""
    xs = sorted(values)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total <= 0:
        return 0.0
    weighted = sum(i * x for i, x in enumerate(xs, 1))
    return 2.0 * weighted / (n * total) - (n + 1.0) / n


def top_share(values, frac: float = 0.10) -> float:
    """The share of the total held by the top `frac` of holders."""
    xs = sorted(values, reverse=True)
    total = sum(xs)
    if not xs or total <= 0:
        return 0.0
    return sum(xs[:max(1, math.ceil(frac * len(xs)))]) / total


def _median(xs) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    mid = len(s) // 2
    return float(s[mid]) if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0


def weekly_series(town) -> list[tuple[str, str, float]]:
    """(scope, measure, value) for this week. Scopes: all, owner, working, out, town."""
    cfg = town.cfg
    rows: list[tuple[str, str, float]] = []
    agents = town.agents
    firms = town.alive_firms
    share_price = {f.id: f.share_price for f in firms}
    worth = {a.id: sum(n * share_price.get(fid, 0) for fid, n in a.shares.items()) for a in agents}
    all_worth = sum(worth.values())

    groups = {"all": agents, "owner": [], "working": [], "out": []}
    for a in agents:
        groups[a.klass].append(a)

    for scope in SCOPES:
        group = groups[scope]
        n = len(group)

        def add(measure, value, scope=scope):
            rows.append((scope, measure, float(value)))

        def mean(fn, group=group, n=n):
            return sum(fn(a) for a in group) / n if n else 0.0

        held = sum(worth[a.id] for a in group)
        add("n", n)
        add("unhappy", mean(lambda a: 0.0 if a.happy else 1.0))
        add("security", mean(lambda a: a.security))
        add("wellbeing", mean(lambda a: a.wellbeing))
        add("provision", mean(lambda a: a.provision))
        add("condition", mean(lambda a: a.condition))
        add("income", mean(lambda a: a.income_estimate()))
        add("pay", mean(lambda a: a.wage))
        add("spend", mean(lambda a: a.spend_week))
        add("cash_mean", mean(lambda a: a.cash))
        add("cash_median", _median([a.cash for a in group]))
        add("cash_total", sum(a.cash for a in group))
        add("shares_value", held)
        add("shares_pct", held / all_worth if all_worth > 0 else (1.0 if scope == "all" else 0.0))
        add("holders", sum(1 for a in group if a.shares))
        add("debt", sum(a.loan for a in group))
        add("destitute", sum(1 for a in group if a.destitute))
        add("homeless", sum(1 for a in group if not housed(a)))
        if cfg.rtr:
            add("spare_hours", mean(lambda a: a.spare_hours))
        add("horizon", mean(lambda a: a.h_eff(cfg)))
        if town.map is not None:                 # distance: hours on the road, blocks to work, transport
            add("travel_hours", mean(lambda a: a.travel_hours))
            commutes = [dist(home_spot(a), a.employer.spot) for a in group
                        if a.employer is not None and home_spot(a) is not None]
            add("blocks_to_work", sum(commutes) / len(commutes) if commutes else 0.0)
            add("riders", mean(lambda a: 1.0 if "transport" in a.subs else 0.0))

    def town_add(measure, value):
        rows.append(("town", measure, float(value)))

    population = len(agents)
    cheapest = cheapest_prices(town)          # a base need nobody sells keeps its last price
    count: dict[str, int] = {}
    for f in firms:
        count[f.need] = count.get(f.need, 0) + 1
    base = [s for s in town.needs.values() if not s.invented]
    basket = sum(cheapest.get(s.name, 0) for s in base)
    basket0 = sum(s.initial_price for s in base)
    wage = town.staff_pay()                   # what staff are paid; the going wage, where a firm pays one rate
    town_add("population", population)
    town_add("firms", len(firms))
    town_add("staff", sum(len(f.staff) for f in firms))
    town_add("execs", sum(len(f.execs) for f in firms))
    town_add("vacancies", sum(f.vacancies for f in firms))
    town_add("jobless", sum(1 for a in agents if a.role is None))
    town_add("jobless_rate", town.jobless_share())
    town_add("unhappy_share", town.unhappy_share())
    town_add("destitute", sum(1 for a in agents if a.destitute))
    town_add("wage", wage)
    if cfg.rtr:
        town_add("wage_offer", town.typical_wage())   # RTR: the going wage, what a job pays someone taken on now
    town_add("wage_index", wage / cfg.outside_wage if cfg.outside_wage else 0.0)
    asking = basket
    if cfg.rtr and cfg.owners_judge_by_what_they_pay and agents:
        # RTR (J, 20/11/2026): "use what people actually pay": the average of its people's own baskets
        from .household import basket_cost
        basket = sum(basket_cost(town, a, cheapest) for a in agents) / len(agents)
    town_add("basket", basket)
    if cfg.rtr:
        town_add("basket_asking", asking)         # the cheapest price on offer of each need, kept beside it
    town_add("price_index", asking / basket0 if basket0 else 0.0)
    town_add("affordability", basket / wage if wage else 0.0)
    for s in base:
        town_add(f"price_{s.name}", cheapest.get(s.name, 0))
        town_add(f"firms_{s.name}", count.get(s.name, 0))
    # transport is a need of its own, counted with the map below, not one somebody thought up
    town_add("firms_invented", sum(1 for f in firms if f.spec.invented and f.need != "transport"))
    town_add("needs_invented", sum(1 for s in town.needs.values() if s.invented and s.name != "transport"))
    town_add("gini_shares", gini(worth.values()))
    town_add("top10_shares", top_share(worth.values()))
    cash = [a.cash for a in agents]
    town_add("gini_cash", gini(cash))
    town_add("top10_cash", top_share(cash))
    town_add("share_value", all_worth)
    town_add("money", town.money_in_town())
    town_add("money_firms", sum(f.cash for f in town.firms))
    town_add("money_people", sum(cash))
    wi, wo = town.ledger.week_in, town.ledger.week_out
    town_add("in_arrival", wi.get("arrival", 0))
    town_add("in_loan", wi.get("loan", 0))
    town_add("in_export", wi.get("export", 0))
    town_add("out_repay", wo.get("loan_principal", 0) + wo.get("loan_recovery", 0))
    town_add("out_interest", wo.get("loan_interest", 0))
    town_add("out_import", wo.get("import", 0))
    town_add("net_flow", town.ledger.net_week())
    town_add("loans_firms", sum(f.loan for f in firms))
    town_add("loans_people", sum(a.loan for a in agents))
    town_add("writeoffs", town.bank.writeoffs_week)
    homes = [u for f in firms if f.need == "housing" for u in f.units]
    sets = [u for f in firms if f.need == "appliances" for u in f.units]
    if town.own_units:                           # RTR: what people own counts with what firms let
        homes += [u for u in town.own_units if u.spec.name == "housing"]
        sets += [u for u in town.own_units if u.spec.name == "appliances"]
    lived = [u.cond for u in homes if u.occupant is not None]
    used = [u.cond for u in sets if u.occupant is not None]
    town_add("homes", len(homes))
    town_add("homes_vacant", len(homes) - len(lived))
    town_add("home_cond", sum(lived) / len(lived) if lived else 0.0)
    town_add("appl_cond", sum(used) / len(used) if used else 0.0)
    asset_units = sum(len(f.units) for f in firms if f.spec.kind == "asset")
    town_add("upkeep_level", sum(f.upkeep_level * len(f.units) for f in firms if f.spec.kind == "asset")
             / asset_units if asset_units else 1.0)
    if cfg.rtr:                                  # who owns (measured only in the Right to Repair world)
        town_add("homes_owned", sum(1 for u in town.own_units
                                    if u.spec.name == "housing" and u.owner is not None))
        town_add("homes_foreclosed", len(town.foreclosed))
        town_add("homes_foreclosed_debt", sum(u.debt for u in town.foreclosed))   # owed on homes the bank holds
        town_add("homes_building", sum(1 for a in agents if a.build is not None))
        town_add("sets_owned", sum(1 for u in town.own_units if u.spec.name == "appliances"))
        town_add("home_loans", sum(a.home_loan for a in agents))
        lets = [a.lets for a in agents if a.lets is not None and a.lets.units]   # stage 1b: buying, selling, letting
        town_add("homes_bought", sum(1 for u in town.own_units if u.bought and u.owner is not None))
        town_add("homes_let_private", sum(len(letting.units) for letting in lets))
        town_add("small_landlords", len(lets))
        town_add("homes_loose", sum(1 for f in firms if f.need == "housing" for u in f.units if u.rent > 0))
        town_add("home_sales", town.ledger.week_internal.get("home_sale", 0) + town.bank_sales_week)
        makers = town.hustles                    # stage 2: side hustles, their customers, hours and takings
        town_add("makers", len(makers))
        town_add("maker_customers", sum(h.load() for h in makers if h.spec is not None))
        town_add("maker_hours_sold", sum(h.sold for h in makers if h.spec is None))
        town_add("maker_revenue", sum(h.w_revenue for h in makers))
        town_add("ideas", town.ideas_total)      # new things people have thought up, so far
        town_add("small_businesses", sum(1 for h in makers if h.business))
        town_add("maker_staff", sum(len(h.staff) for h in makers))
        town_add("maker_loans", sum(h.loan for h in makers))
    town_add("moved_up", town.moves_up)
    town_add("moved_down", town.moves_down)
    m = town.map
    if m is not None:                            # the map: how full it is, what land costs, rent by place
        town_add("spots_empty", sum(1 for s in m.spots if s.kind is None))
        town_add("spots_homes", sum(1 for s in m.spots if s.kind == "homes"))
        town_add("spots_premises", sum(1 for s in m.spots if s.kind == "premises"))
        town_add("land_scarce", 1.0 if m.scarce else 0.0)
        town_add("land_price", m.land_price)
        town_add("ground_rent", sum(s.ground_rent for s in m.spots))
        town_add("turned_away", town.reach_blocked_last)
        for what, count in town.reach_blocked_by.items():
            town_add(f"turned_away_{what}", count)
        riders = town.firms_for("transport")
        town_add("transport_firms", len(riders))
        town_add("transport_price", min((f.price for f in riders), default=0))
        middle = [unit_rent(u, standard=True) for s in m.spots if s.kind == "homes" and dist(s, m.centre) <= 3
                  for u in s.units]
        edge = [unit_rent(u, standard=True) for s in m.spots if s.kind == "homes" and dist(s, m.centre) > cfg.walk_range
                for u in s.units]
        town_add("rent_middle", sum(middle) / len(middle) if middle else 0.0)
        town_add("rent_edge", sum(edge) / len(edge) if edge else 0.0)
    return rows
