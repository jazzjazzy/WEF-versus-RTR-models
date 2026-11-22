"""The town: all state, one random generator, and the week in order."""

from __future__ import annotations

import json
import math
import random

from . import rtr_makers, rtr_owning
from .bank import Bank
from .broker import Broker
from .corporate import fail_firm, found_firm, maybe_arrive_founder, payroll, quarterly
from .entities import Agent, Firm, Unit
from .firmops import idle_this_week
from .household import pay_bills, plan_bills, review_subscriptions, update_agents
from .labour import labour_market
from .ledger import OUTSIDE, Ledger
from .metrics import weekly_series
from .places import (TownMap, house, pay_ground_rents, place_service, refresh_access,
                     refresh_land_values, tally_stranded, update_popularity)
from .production import operate
from .recorder import NullRecorder
from .subscriptions import settle_arrival


class Town:
    def __init__(self, cfg, recorder=None, setup: bool = True) -> None:
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)
        self.week = 0
        self.agents: list[Agent] = []
        self.firms: list[Firm] = []
        self._agents: dict[int, Agent] = {}
        self._firms: dict[int, Firm] = {}
        self.needs = {n.name: n for n in cfg.needs}      # invented needs are added as they appear
        self.last_price = {n.name: n.initial_price for n in cfg.needs}   # what each need last cost
        self.ledger = Ledger()
        self.rec = recorder if recorder is not None else NullRecorder()
        self.map = TownMap(cfg) if cfg.map_width > 0 and cfg.map_height > 0 else None
        self.hour_value = cfg.outside_wage * cfg.time_value_share   # what an hour on the road is weighed at
        self.stranded: dict = {}                 # (agent id, what) turned away for distance this quarter
        self.far_arrivals = 0                    # outside workers turned away for distance this quarter
        self.reach_stops_building = -1_000       # the last week a landlord had only out-of-reach land to build on
        self.reach_blocked_last = 0              # both, for the quarter just ended
        self.reach_blocked_by = {"job": 0, "food": 0, "other": 0}   # and what it kept them from
        self.broker = Broker(self)
        self.bank = Bank(self)
        self.failed_week = None
        self.no_home_week = None          # the last week someone was turned away from town for want of a home
        self.cap_week = None
        self.endowment: dict[str, dict] = {}             # starting units, outside the five flows
        self.moves_up = 0                                # class moves this week
        self.moves_down = 0
        self._next_unit = 1
        self.own_units: list[Unit] = []                  # RTR: homes and appliance sets people own
        self.foreclosed: list[Unit] = []                 # RTR: homes the bank has taken and not yet sold
        self.foreclosures_total = 0                      # RTR: how many times the bank has foreclosed
        self.to_let: list[Unit] = []                     # RTR 1b: homes for rent on no landlord's block, with no tenant
        self.bank_sales_week = 0                         # RTR 1b: what the bank was paid for homes this week
        self.bank_lets = None                            # RTR 1b: the Letting of homes the bank holds that have tenants
        self.hustles: list = []                          # RTR 2: every live side hustle
        self.makers_of: dict = {}                        # RTR 2: the same, by what they sell (a need, or a trade of hours)
        self.goods_wanted: dict = {}                     # RTR: units of each need's good the makers wanted this week
        self.ideas_total = 0                             # RTR 2: how many new things people have thought up
        self.new_ideas: set = set()                      # RTR 2: needs thought up this week, open to others from next week
        for spec in cfg.needs:
            self.rec.need(0, spec)
        if setup:
            self._setup()

    # --- lookups ---------------------------------------------------------------------
    def agent(self, agent_id: int) -> Agent:
        return self._agents[agent_id]

    def firm(self, firm_id: int) -> Firm:
        return self._firms[firm_id]

    @property
    def population(self) -> int:
        return len(self.agents)

    @property
    def alive_firms(self) -> list[Firm]:
        return [f for f in self.firms if f.alive]

    def firms_for(self, need_name: str) -> list[Firm]:
        return [f for f in self.firms if f.alive and f.need == need_name]

    def money_in_town(self) -> int:
        tills = sum(h.cash for h in self.hustles) if self.hustles else 0     # RTR 2: a side hustle's takings this week
        return sum(a.cash for a in self.agents) + sum(f.cash for f in self.firms) + tills

    def typical_wage(self) -> int:
        """The going wage in town: the average of its firms' wages, each counted once for every
        one of its staff; the outside wage if nobody is employed. It is what a job pays
        someone taken on now. Where staff keep rates of their own what they are paid is
        `staff_pay`."""
        total = count = 0
        for f in self.firms:
            if f.alive and f.staff:
                total += f.wage * len(f.staff)
                count += len(f.staff)
        return total // count if count else self.cfg.outside_wage

    def staff_pay(self) -> int:
        """The average of what the staff of the town's firms are paid, or the outside wage if
        nobody is employed. The going wage, wherever a firm pays all its staff one rate."""
        total = count = 0
        for f in self.firms:
            if f.alive and f.staff:
                total += f.staff_bill()
                count += len(f.staff)
        return total // count if count else self.cfg.outside_wage

    def jobless_share(self) -> float:
        if not self.agents:
            return 0.0
        return sum(1 for a in self.agents if a.role is None) / len(self.agents)

    # --- creating things ----------------------------------------------------------------
    def add_agent(self, cash: int = 0, origin: str = "worker", **fixed) -> Agent:
        """A new resident with a randomised temperament. Their cash arrives from outside."""
        cfg, rng = self.cfg, self.rng
        a = Agent(len(self.agents) + 1, self.week)
        a.origin = origin
        a.loss_aversion = min(cfg.loss_aversion_max, max(
            cfg.loss_aversion_min,
            rng.lognormvariate(math.log(cfg.loss_aversion_median), cfg.loss_aversion_sigma)))
        a.horizon = min(cfg.horizon_max_weeks, max(
            cfg.horizon_min_weeks,
            rng.lognormvariate(math.log(cfg.horizon_median_weeks), cfg.horizon_sigma)))
        a.growth_expect = rng.triangular(cfg.growth_expect_low, cfg.growth_expect_high,
                                         cfg.growth_expect_mode)
        a.skill = rng.random()
        a.risk = rng.random()
        a.taste = rng.random()
        a.prefers_equity = rng.random() < cfg.equity_pref_share
        a.security = cfg.security_start
        for key, value in fixed.items():
            setattr(a, key, value)
        self.agents.append(a)
        self._agents[a.id] = a
        a.start_cash = cash
        self.ledger.pay(OUTSIDE, a, cash, "arrival")
        self.rec.agent_static(a)
        return a

    def add_firm(self, need_name: str, founder: Agent | None = None, name: str | None = None) -> Firm:
        """A bare firm: no capital, no shares, no staff. Founding fills it in."""
        spec = self.needs[need_name]
        firm_id = len(self.firms) + 1
        f = Firm(firm_id, name or f"{need_name.title()} {firm_id}", spec, self.week,
                 founder.id if founder is not None else None)
        f.wage = self.cfg.outside_wage
        f.own_rates = self.cfg.staff_keep_pay                  # both worlds (Jason, 22/11/2026)
        f.share_price = self.cfg.share_par
        self.firms.append(f)
        self._firms[f.id] = f
        return f

    def new_unit(self, firm: Firm) -> Unit:
        u = Unit(self._next_unit, firm.spec, firm)
        self._next_unit += 1
        u.empty_since = self.week
        firm.units.append(u)
        return u

    def new_own_unit(self, spec, owner: Agent) -> Unit:
        """A home or appliance set that belongs to a person, not to any firm (RTR)."""
        u = Unit(self._next_unit, spec, None)
        self._next_unit += 1
        u.owner = owner
        self.own_units.append(u)
        return u

    # --- shares -----------------------------------------------------------------------
    def issue_shares(self, firm: Firm, agent: Agent, qty: int) -> None:
        if qty <= 0:
            return
        firm.shares_out += qty
        firm.holders[agent.id] = firm.holders.get(agent.id, 0) + qty
        agent.shares[firm.id] = agent.shares.get(firm.id, 0) + qty

    def move_shares(self, firm: Firm, seller: Agent, buyer: Agent, qty: int) -> None:
        if qty <= 0:
            return
        if seller.shares.get(firm.id, 0) < qty:
            raise ValueError("seller does not hold that many shares")
        for holder, delta in ((seller, -qty), (buyer, qty)):
            n = holder.shares.get(firm.id, 0) + delta
            if n:
                holder.shares[firm.id] = n
                firm.holders[holder.id] = n
            else:
                holder.shares.pop(firm.id, None)
                firm.holders.pop(holder.id, None)

    # --- the record ----------------------------------------------------------------------
    def event(self, kind: str, agent=None, firm=None, amount=None, qty=None, **data) -> None:
        """Log one event. An agent's security and effective horizon at that moment go with it."""
        if agent is not None:
            data["sec"] = round(agent.security, 3)
            data["h"] = round(agent.h_eff(self.cfg), 1)
        self.rec.event(self.week, kind,
                       agent.id if agent is not None else None,
                       firm.id if firm is not None else None,
                       amount, qty, data)

    # --- day one ---------------------------------------------------------------------------
    def _setup(self) -> None:
        """Four founders, four firms, each owned by its founder (Jason, 12/11/2026). The
        housing and appliance firms start with units already standing."""
        cfg = self.cfg
        names = [n.name for n in cfg.needs]
        if "housing" in names:                           # homes first, so everyone can be housed
            names.remove("housing")
            names.insert(0, "housing")
        if self.map is not None:                         # the bank and the broker hold the middle
            homes = sum(n.initial_units for n in cfg.needs if n.name == "housing")
            needed = 2 + len(names) + -(-homes // cfg.homes_per_spot)
            if len(self.map.spots) < needed:
                raise ValueError(
                    f"a {cfg.map_width} by {cfg.map_height} map is too small for the town's first day: "
                    f"the bank, the broker, {len(names)} founding firms and {homes} starting homes "
                    f"need {needed} spots")
            centre = self.map.centre
            place_service(self, centre, "bank")
            place_service(self, self.map.at(centre.x + 1, centre.y), "broker")
        founders = []
        for name in names:
            spec = self.needs[name]
            capital = cfg.founding_capital.get(name, cfg.founder_capital_median)
            if self.map is not None:
                capital += cfg.premises_cost             # each founder also fits out premises
            founder = self.add_agent(cash=capital + cfg.founder_personal_cash, origin="founder")
            firm = found_firm(self, founder, capital, spec, in_kind_units=spec.initial_units)
            self.endowment[name] = {"units": spec.initial_units,
                                    "value": spec.initial_units * firm.unit_build_cost()}
            founders.append(founder)
        if self.map is not None:                         # the starting homes go on the best-placed spots
            refresh_access(self)
            for firm in self.firms:
                if firm.need == "housing":
                    for unit in firm.units:
                        house(self, firm, unit)
            refresh_access(self)
        for founder in founders:
            settle_arrival(self, founder)
            self.event("arrival", agent=founder, amount=founder.start_cash, who="founder")
        self.rec.meta("endowment", json.dumps(self.endowment, sort_keys=True))
        update_agents(self)
        self._record()          # week 0: the founders' capital is the first of the five flows

    # --- the week, in order -------------------------------------------------------------------
    def step(self) -> None:
        cfg = self.cfg
        self.week += 1
        self.ledger.start_week()
        self.bank.start_week()
        self.moves_up = self.moves_down = 0
        self.hour_value = self.typical_wage() * cfg.time_value_share
        refresh_land_values(self)
        for f in self.firms:
            f.w_revenue = f.w_export = f.w_wages = f.w_goods = 0
            f.w_interest = f.w_capex = f.w_wear = 0

        if cfg.rtr:
            rtr_owning.start_week(self)                      #    RTR: everyone's spare hours for the week
            rtr_makers.start_week(self)                      #    and the hours each side hustle has for customers
        elif cfg.reservation_covers_basket:
            rtr_makers.remember_loans(self)                  #    WEF: the most owed on each loan, for the floor (the review, 22/11)
        maybe_arrive_founder(self)                       # 1. a founder may arrive
        labour_market(self)                              # 2. layoffs, promotions, hiring, arrivals
        if cfg.rtr:
            rtr_makers.hire_staff(self)                      #    RTR: small businesses take on who is left
        operate(self)                                    # 3. the working week; units age
        if cfg.rtr:
            rtr_makers.working_week(self)                    #    RTR: makers serve their customers
        for a in self.agents:
            a.income_week = a.spend_week = a.div_week = 0
        payroll(self)                                    # 4. wages; a firm that cannot pay fails
        for f in pay_ground_rents(self):                 #    and ground rent on leased land
            fail_firm(self, f, "ground_rent")
        plan_bills(self)                                 # 5. agents plan, trim, place share orders
        self.broker.clear_all()                          # 6. the broker clears
        pay_bills(self)                                  # 7. bills in order; missed payments
        if cfg.rtr:
            rtr_owning.after_bills(self)                     #    RTR: upkeep of what people own, and their building
            rtr_makers.after_bills(self)                     #    makers buy the week's goods out of the week's takings
        for f in list(self.alive_firms):                 # 8. firms service their loans
            if f.loan > 0:
                self.bank.service_firm(f)
                if f.loan_missed >= cfg.firm_missed_limit:
                    fail_firm(self, f, "loan")
        for f in self.alive_firms:
            f.q_revenue += f.w_revenue
            f.q_export += f.w_export
            f.q_wages += f.w_wages
            f.q_goods += f.w_goods
            f.q_interest += f.w_interest
            f.q_capex += f.w_capex
            f.q_wear += f.w_wear
            f.last_opex = max(0, f.w_wages + f.w_goods + f.w_interest - f.w_capex)
            f.idle_weeks = f.idle_weeks + 1 if idle_this_week(f) else 0
        quarter_end = self.week % cfg.quarter_weeks == 0
        if self.map is not None:
            update_popularity(self, quarter_end)
        if quarter_end:
            quarterly(self)                              # 9. reviews, dividends, new firms
            if self.map is not None:
                refresh_access(self)                     #    where the jobs and shops now are
                tally_stranded(self)                     #    who distance kept from what, this quarter
        if cfg.rtr and quarter_end:
            rtr_owning.quarter(self)                         #     RTR: people look at owning
            rtr_makers.quarter(self)                         #     and each side hustle is reckoned up
        review_subscriptions(self)                       # 10. sign up, switch
        update_agents(self)                              #     security, wellbeing, class
        if self.cap_week is None:
            if cfg.at_cap(self.population):
                self.cap_week = self.week
                self.event("town_full", qty=self.population)
            elif (cfg.population_cap <= 0 and self.map is not None and self.map.scarce
                  and self.no_home_week == self.week):
                # (C) 16/11/2026: with no cap the town is full when the land has run out and a
                # newcomer is turned away for want of a home
                self.cap_week = self.week
                self.event("town_full", qty=self.population, reason="no home, no land")
        self._record()                                   # 11. the record, then the failure rule
        self._check_failure()

    def _record(self) -> None:
        self.rec.series(self.week, weekly_series(self))
        self.rec.snapshot(self)

    def unhappy_share(self) -> float:
        if not self.agents:
            return 0.0
        return sum(1 for a in self.agents if not a.happy) / len(self.agents)

    def _check_failure(self) -> None:
        """The run fails the first week 90% of all agents are unhappy (Jason, 12/11/2026)."""
        cfg = self.cfg
        n = len(self.agents)
        if self.failed_week is not None or n < cfg.failure_min_population:
            return
        unhappy = sum(1 for a in self.agents if not a.happy)
        if unhappy >= cfg.failure_unhappy_share * n:
            self.failed_week = self.week
            self.event("town_failed", amount=unhappy, qty=n)

    def run(self, weeks: int | None = None) -> str:
        """Run for `weeks` (default: the settings' years). Stops at failure unless told not to."""
        cfg = self.cfg
        for _ in range(cfg.weeks if weeks is None else weeks):
            self.step()
            if self.failed_week is not None and cfg.stop_on_failure:
                break
        return "failed" if self.failed_week is not None else "survived"
