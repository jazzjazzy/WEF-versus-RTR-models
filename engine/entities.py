"""The things in the town: agents, firms, and the units (homes, appliance sets) firms rent out."""

from __future__ import annotations


class Agent:
    """One resident. Owns nothing but cash and shares."""

    __slots__ = (
        "id", "arrived", "origin", "start_cash",
        # temperament, fixed at birth
        "loss_aversion", "horizon", "growth_expect", "skill", "risk", "taste", "prefers_equity",
        # money and work
        "cash", "employer", "role", "wage", "last_wage", "weeks_out", "hired_week", "staff_wage",
        "loan", "loan_pay", "loan_called", "called_weeks", "loan_missed", "credit_block_until",
        # subscriptions
        "subs", "unit", "arrears", "had", "met", "plan", "well_off", "wants_better",
        # shares
        "shares", "div_quarters", "div_this_quarter",
        # state
        "security", "wellbeing", "happy", "destitute", "provision", "condition", "klass",
        "income_week", "spend_week", "div_week", "last_trigger", "travel_hours", "far", "no_ride",
        # the Right to Repair world (16/11/2026)
        "spare_hours", "home_loan", "home_pay", "home_missed", "set_hours_left", "build", "lets",
        "hustle", "loan_top", "home_loan_top",
    )

    def __init__(self, id: int, arrived: int) -> None:
        self.id = id
        self.arrived = arrived
        self.origin = "worker"
        self.start_cash = 0
        self.loss_aversion = 2.0
        self.horizon = 104.0
        self.growth_expect = 0.04
        self.skill = 0.5
        self.risk = 0.5
        self.taste = 0.5
        self.prefers_equity = False
        self.cash = 0
        self.employer = None          # Firm or None
        self.role = None              # None, 'staff', 'exec', 'ceo'
        self.wage = 0                 # weekly pay in their current role
        self.last_wage = 0            # last wage earned, for the reservation wage
        self.staff_wage = 0           # an executive's rate as staff when last promoted (RTR: they keep it if put back)
        self.weeks_out = 0            # weeks without a job
        self.hired_week = 0
        self.loan = 0
        self.loan_pay = 0             # weekly principal instalment
        self.loan_called = False
        self.called_weeks = 0
        self.loan_missed = 0
        self.credit_block_until = 0
        self.subs = {}                # need name -> Firm
        self.unit = {}                # need name -> Unit, for homes and appliance sets
        self.arrears = {}             # need name -> missed payments in a row
        self.had = {}                 # invented need -> the week they last held it
        self.met = {}                 # need name -> met this week
        self.plan = {}                # need name -> plan size, for a bigger plan only (16/11/2026)
        self.well_off = False
        self.wants_better = False     # well-off, in a standard home, and found no better one free
        self.shares = {}              # firm id -> shares
        self.div_quarters = []        # dividends received in each of the last four quarters
        self.div_this_quarter = 0
        self.security = 0.7
        self.wellbeing = 0.7
        self.happy = True
        self.destitute = False
        self.provision = 1.0
        self.condition = 1.0
        self.klass = "out"
        self.income_week = 0          # pay received this week
        self.spend_week = 0
        self.div_week = 0             # dividends received this week
        self.last_trigger = "arrived"
        self.travel_hours = 0.0       # hours on the road this week: to work and to the shops
        self.far = -1_000_000         # the last week distance kept them from a job or a shop
        self.no_ride = 0              # weeks running that their transport firm did not carry them
        self.spare_hours = 0.0        # hours left this week after the job and the road (RTR)
        self.home_loan = 0            # owed to the bank against their home
        self.home_pay = 0             # its weekly principal instalment
        self.home_missed = 0          # payments on it missed in a row
        self.set_hours_left = None    # hours still to work on an appliance set of their own, or None
        self.build = None             # an OwnBuild: the home they are building, or None
        self.lets = None              # their Letting: the homes they let to others, or None
        self.hustle = None            # their Hustle: the side hustle they run in their spare time, or None
        self.loan_top = 0             # the most owed on their personal loan since it was last nil,
        self.home_loan_top = 0        # and on the loan against their home (Jason, 18/11/2026: "less than 50%" paid off)

    def h_eff(self, cfg) -> float:
        """Effective horizon in weeks: the natural horizon, shortened by insecurity."""
        return self.horizon * (cfg.horizon_floor + (1.0 - cfg.horizon_floor) * self.security)

    def dividends_year(self) -> int:
        """Dividends over the last four completed quarters."""
        return sum(self.div_quarters[-4:])

    def income_estimate(self) -> int:
        """What they expect to receive in a week: their pay plus a year's dividends spread over it."""
        income = self.wage + self.dividends_year() // 52
        if self.lets is not None:                # RTR 1b: the rents of the homes they let that have tenants
            income += sum(u.rent for u in self.lets.units if u.occupant is not None)
        if self.hustle is not None:              # RTR 2: what their side hustle brought in a week over the last quarter
            income += self.hustle.profit_week
        return income

    def shock(self, cfg, size: float) -> None:
        """A blow to security. It lands harder on the loss averse."""
        self.security = max(0.0, self.security - size * self.loss_aversion / cfg.loss_aversion_median)

    def __repr__(self) -> str:
        return f"<Agent {self.id} {self.role or 'no job'} cash={self.cash}>"


class Unit:
    """A home or an appliance set. It ages, wears, and belongs to a firm."""

    __slots__ = ("id", "spec", "firm", "age", "cond", "occupant", "spot", "scale",
                 "owner", "debt", "ask", "since", "empty_since", "rent", "bought")

    def __init__(self, id: int, spec, firm) -> None:
        self.id = id
        self.spec = spec
        self.firm = firm
        self.age = 0                  # weeks
        self.cond = 1.0               # condition, 0 to 1
        self.occupant = None          # Agent or None
        self.spot = None              # where a home stands; an appliance set has no place of its own
        self.scale = 1.0              # a better home costs this many times a standard one (16/11/2026)
        self.owner = None             # the person who owns it (RTR); a firm's unit has none
        self.debt = 0                 # foreclosed: what was owed on it,
        self.ask = 0                  # what the bank now asks for it,
        self.since = None             # and the week the bank took it
        self.empty_since = None       # a landlord's home: the week it last fell empty (None while let)
        self.rent = 0                 # a home let on no landlord's block (RTR 1b): its own weekly rent
        self.bought = False           # a private home that was once a landlord's (RTR 1b)


class Letting:
    """A person's homes to let (RTR 1b). It stands where a firm stands in the tenancy code
    (a tenant subscribes to it, is billed by it, pays it) and is in no list of firms. What
    it is paid is its owner's cash. With no owner it is the bank's: the homes the bank
    holds that have tenants; what it is paid is passed on to the bank each week."""

    def __init__(self, owner, spec, ident: int) -> None:
        self.owner = owner
        self.id = ident
        self.name = f"Homes let by person {owner.id}" if owner is not None else "Homes held by the bank"
        self.need = spec.name
        self.spec = spec
        self.alive = True
        self.price = 0                # each home has its own rent
        self.subs = {}                # agent id -> Agent
        self.unserved = {}
        self.units = []
        self.extra = 0
        self.w_revenue = 0
        self._held = 0

    @property
    def cash(self) -> int:
        return self.owner.cash if self.owner is not None else self._held

    @cash.setter
    def cash(self, value: int) -> None:
        if self.owner is not None:
            self.owner.cash = value
        else:
            self._held = value


class Hustle:
    """One person's side hustle (RTR stage 2): their own spare time, sold to others. For a
    need (food, entertainment, something thought up) it stands where a firm stands in the
    selling code: customers subscribe to it, are billed by it and pay it. For repairs and
    building it sells hours. It is in no list of firms. It has a till for the week: what
    customers pay goes into it, the goods and any staff are paid out of it, and what is left
    is its owner's at the week's end."""

    def __init__(self, owner, trade: str, spec, week: int) -> None:
        self.owner = owner
        self.trade = trade            # a need's name, or 'repair', 'set_building', 'home_building'
        self.spec = spec              # the need's NeedSpec; None for the three trades that sell hours
        self.need = trade
        self.id = -(1_000_000 + owner.id)
        self.name = f"Side hustle of person {owner.id}: {trade}"
        self.alive = True
        self.started = week
        self.price = 0                # a week of the need, or one hour of theirs
        self.cash = 0                 # its till: this week's takings, until its owner draws them,
        self.reserve = 0              # and of that, what the bank lent the business: it stays in the business
        self.subs = {}                # agent id -> Agent, oldest customer first
        self.extra = 0                # standard plans beyond one per customer
        self.unserved = {}            # agent id -> True for customers it could not serve this week
        self.turned_away = {}         # agent id -> True for people who wanted in this week and found it full
        self.waiting = 0              # how many were turned away last week
        self.spot = None              # where there is a map: its owner's home
        self.hours = 0.0              # hours it has for customers this week
        self.own_hours = 0.0          # of those, its owner's own
        self.sold = 0.0               # hours sold this week (the trades that sell hours)
        self.capacity = 0             # standard plans it can serve this week (a need)
        self.w_revenue = 0            # this week,
        self.w_goods = 0
        self.w_wages = 0
        self.q_revenue = 0            # and this quarter so far
        self.q_goods = 0
        self.q_wages = 0
        self.q_sold = 0.0             # customers served (or hours sold), summed over the quarter's weeks
        self.q_could = 0.0            # and how many it could have
        self.profit_week = 0          # what it brought in a week over the last quarter
        self.gross_week = 0           # its takings less goods a week over the last quarter (RTR, 22/11/2026)
        self.used_week = 0.0          # and the hours a week it used to serve them
        self.asked = []               # ids of those it turned away last week
        # a small business: it has borrowed on its profit and may take on staff
        self.business = False
        self.staff = []               # Agents, in order of hiring
        self.execs = []               # it has none; the jobs code looks
        self.ceo = None
        self.accrual = {}             # no wages are held back for shares
        self.wage = 0                 # the going wage, each week
        self.loan = 0                 # owed to the bank on its profit
        self.loan_pay = 0             # its weekly principal instalment
        self.loan_missed = 0          # payments missed in a row
        self.loan_top = 0             # the most owed on it since it was last nil

    def load(self) -> int:
        """Customers counted in standard plans: a bigger plan counts as that many."""
        return len(self.subs) + self.extra

    def __repr__(self) -> str:
        return f"<Hustle of {self.owner.id} {self.trade} {'alive' if self.alive else 'stopped'}>"


class OwnBuild:
    """A home someone is building for themselves (RTR): the hours and goods still to go,
    the plot kept for it, and what it has cost so far."""

    __slots__ = ("hours_left", "goods_left", "spot", "spent", "to_let", "borrowed")

    def __init__(self, hours: float, goods: float, spot=None, to_let: bool = False) -> None:
        self.hours_left = float(hours)
        self.goods_left = float(goods)
        self.spot = spot
        self.spent = 0
        self.to_let = to_let          # built to let to someone else (stage 1b), not to live in
        self.borrowed = 0             # what the bank has lent on it so far


class Project:
    """A unit being built, or an old unit being rebuilt."""

    __slots__ = ("unit", "labour_left", "goods_left", "spot", "scale")

    def __init__(self, spec, unit=None, scale=None) -> None:
        self.unit = unit              # None for a new unit; an existing Unit for a rebuild
        if scale is None:
            scale = unit.scale if unit is not None else 1.0
        self.scale = scale            # a better home takes this many times the work and goods
        self.labour_left = float(spec.build_labour) * scale
        self.goods_left = float(spec.build_goods) * scale
        self.spot = None              # the spot a new home is being built on, when there is a map


class Firm:
    """One firm selling one need at one weekly price, paying one staff wage."""

    def __init__(self, id: int, name: str, spec, founded: int, founder_id: int | None) -> None:
        self.id = id
        self.name = name
        self.spec = spec
        self.need = spec.name
        self.founded = founded
        self.founder_id = founder_id
        self.alive = True
        self.closed_week = None
        self.close_reason = None

        self.cash = 0
        self.loan = 0
        self.loan_pay = 0             # weekly principal instalment
        self.loan_missed = 0
        self.price = spec.initial_price
        self.wage = 0                 # the rate it pays: everyone on its staff, or (own_rates) those it hires from now
        self.own_rates = False        # RTR (Jason, 19/11/2026): its staff each keep the rate they were hired or last lifted to
        self.loss_to_cover = 0        # RTR (Jason, 19/11/2026): a week's share of last quarter's loss, if it is in debt: staff are let go for it at the next hiring

        self.shares_out = 0
        self.holders = {}             # agent id -> shares
        self.share_price = 0          # last trade (starts at the issue price)

        self.staff = []               # Agents, in order of hiring
        self.execs = []
        self.ceo = None
        self.subs = {}                # agent id -> Agent, oldest customer first
        self.extra = 0                # standard plans beyond one per customer: the bigger plans (16/11/2026)
        self.units = []
        self.projects = []
        self.spot = None              # its premises: workplace and shop front in one
        self.lots = []                # the spots its homes stand on
        self.land_value = 0           # the land it owns, at the going price; security for a loan
        self.rent_missed = 0          # ground rent payments missed in a row

        # policy
        self.upkeep_level = 1.0
        self.make_mode = "make"       # 'make' or 'import'
        self.export_target = 0.0      # units a week it would like to sell outside
        self.town_target = 0.0        # RTR: units a week ordered of it by the town's makers (Jason, 18/11/2026),
        self.town_units = 0.0         # and what it has made for them this week and not yet sold
        self.share_pay = 0.0          # part of staff wages paid in shares
        self.prefers_equity = False
        self.accrual = {}             # agent id -> wages held back to be paid in shares

        # this week's plan and outcome
        self.desired_staff = 0
        self.vacancies = 0
        self.unfilled_weeks = 0
        self.housing_blocked = False
        self.unmet_demand = 0.0       # people turned away for want of a free unit
        self.funding_gap = 0          # building it wants to do and cannot pay for
        self.unserved = {}            # agent id -> True for customers it could not serve this week
        self.turned_away = {}         # agent id -> True for people who wanted in this week and found it full
        self.waiting = 0              # how many were turned away last week; it staffs up for them
        self.upkeep_done = 1.0
        self.made_units = 0.0
        self.import_units = 0.0
        self.export_units = 0.0
        self.idle_weeks = 0

        # accounts: this week, this quarter, history
        self.w_revenue = 0
        self.w_export = 0
        self.w_wages = 0
        self.w_goods = 0
        self.w_interest = 0
        self.last_opex = 0
        self.q_revenue = 0
        self.q_export = 0
        self.q_wages = 0
        self.q_goods = 0
        self.q_interest = 0
        self.w_capex = 0              # part of this week's wages and goods that went into building units
        self.w_wear = 0               # wear on its units this week (building cost spread over their life)
        self.q_capex = 0
        self.q_wear = 0
        self.last_dividend = 0
        self.retained = 0             # profit made and not yet paid out; dividends come only from this
        self.rev_hist = []            # revenue, one per quarter
        self.sale_week = None         # week it was last sold as a going concern
        self.profit_hist = []         # profit, one per quarter
        self.eps_hist = []            # profit per share, one per quarter
        self.dps_hist = []            # dividend per share, one per quarter
        self.target_growth = 0.0
        self.shortfall = False
        self.last_dir = 0             # direction of the last price move
        self.profit_before_move = None

    # --- people --------------------------------------------------------------------
    def staff_bill(self) -> int:
        """What its staff are paid a week between them."""
        if self.own_rates:
            return sum(a.wage for a in self.staff)
        return self.wage * len(self.staff)

    def staff_pay(self) -> int:
        """What one of its staff is paid a week: its wage, or where each keeps a rate of their
        own the average of them (its wage while it has no staff). What its staff have cost it:
        its bosses' pay is a multiple of this, and building done is booked at it. What it
        would cost to make or build one more of anything is reckoned at its wage."""
        if self.own_rates and self.staff:
            return self.staff_bill() // len(self.staff)
        return self.wage

    def exec_pay(self, cfg) -> int:
        return int(self.staff_pay() * cfg.exec_pay_multiple)

    def ceo_pay(self, cfg) -> int:
        multiple = min(cfg.ceo_pay_cap, cfg.ceo_pay_base + cfg.ceo_pay_per_staff * len(self.staff))
        return int(self.staff_pay() * multiple)

    def payroll(self, cfg) -> int:
        total = self.staff_bill() + self.exec_pay(cfg) * len(self.execs)
        if self.ceo is not None:
            total += self.ceo_pay(cfg)
        return total

    def load(self) -> int:
        """Customers counted in standard plans: a bigger plan counts as that many."""
        return len(self.subs) + self.extra

    def headcount(self) -> int:
        return len(self.staff) + len(self.execs) + (1 if self.ceo is not None else 0)

    # --- costs and value ---------------------------------------------------------------
    def make_cost(self) -> int:
        """Cost of making one more unit of its good in town: at its wage, the rate of whoever
        it would take on to make it. (Not what its staff keep, where they keep rates of their
        own: reckoned at that, a cut for newcomers changed nothing a firm decided and it never
        took the newcomers on. The fresh review, 19/11/2026.)"""
        return int(self.wage * self.spec.make_labour)

    def goods_cost(self) -> int:
        """What a unit of its good costs it: the cheaper of making and importing."""
        return min(self.make_cost(), self.spec.import_price)

    def unit_build_cost(self) -> int:
        return int(self.spec.build_labour * self.wage + self.spec.build_goods * self.goods_cost())

    def units_value(self, cfg, units) -> int:
        """What these homes or appliance sets are worth as they stand: the cost of building
        them new, less wear, and never under a fifth of it."""
        cost = self.unit_build_cost()
        life = self.spec.life_years * cfg.weeks_per_year
        return sum(int(cost * u.scale * max(0.2, 1.0 - u.age / life)) for u in units)

    def collateral(self, cfg) -> int:
        """Value of its homes or appliance sets, and of its land, as security for a loan.
        Homes standing on land the firm only leases are not its to pledge."""
        if self.spec.kind != "asset" or not self.units:
            return self.land_value
        own = [u for u in self.units if u.spot is None or u.spot.owner is self or u.rent > 0]   # a single home has its plot
        return self.units_value(cfg, own) + self.land_value

    def book_value(self, cfg) -> int:
        return self.cash + self.collateral(cfg) - self.loan

    def book_per_share(self, cfg) -> int:
        if self.shares_out <= 0:
            return 0
        return max(0, self.book_value(cfg)) // self.shares_out

    def weighted(self, town, fn) -> float:
        """Average of fn(agent) over shareholders, weighted by holding."""
        if self.shares_out <= 0:
            return 0.0
        total = 0.0
        for agent_id, n in self.holders.items():
            total += n * fn(town.agent(agent_id))
        return total / self.shares_out

    def controller(self):
        """Id of the agent holding half or more of the shares, if any."""
        for agent_id, n in self.holders.items():
            if n * 2 >= self.shares_out:
                return agent_id
        return None

    def vacant_units(self) -> list:
        return [u for u in self.units if u.occupant is None]

    def age_weeks(self, week: int) -> int:
        return week - self.founded

    def __repr__(self) -> str:
        return f"<Firm {self.id} {self.name} {'alive' if self.alive else 'closed'}>"
