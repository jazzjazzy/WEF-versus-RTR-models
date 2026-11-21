"""Every dial in the model, with its starting value and the reason for it.

Money is whole cents. Time is weeks. A dial marked (J) carries a decision Jason
made on 12/11/2026; everything else is a starting value chosen by the builder
and is meant to be changed and tested.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields


@dataclass
class NeedSpec:
    """One thing agents need, and what it takes to supply it for a week."""

    name: str
    kind: str                # 'flow' (used up each week) or 'asset' (a home, an appliance set)
    weight: float            # share of "provision" this need carries
    essential: bool          # food and housing: agents borrow or sell shares to keep them
    priority: int            # order of payment each week (lower pays first; the bank loan is 2)
    service_labour: float    # worker-weeks per customer per week
    goods_per_sub: float     # units of its tradable good used per customer per week
    make_labour: float       # worker-weeks to make one unit of that good in town
    import_price: int        # cents per unit bought from outside
    export_price: int        # cents per unit sold outside
    export_quota: float      # units per week the outside will buy, shared by the firms that make it
    initial_price: int       # cents per week charged by the founding firm
    build_labour: float = 0.0    # worker-weeks to build one unit (asset needs)
    build_goods: float = 0.0     # units of the good to build one unit
    upkeep_labour: float = 0.0   # worker-weeks per unit per week when new
    upkeep_goods: float = 0.0    # units of the good per unit per week when new
    upkeep_growth: float = 0.0   # upkeep grows by this share per year of age (J: costs more as it ages)
    aging_rate: float = 0.0      # best achievable condition falls by this per year of age
    life_years: float = 0.0      # accounting life, used to value the unit as collateral
    initial_units: int = 0       # units the founding firm starts with
    appeal: float = 1.0          # share of agents an invented need suits
    trips_per_week: float = 0.0  # trips a customer makes to the firm's premises each week
    fixed_labour: float = 0.0    # worker-weeks it needs each week however few customers it has
    invented: bool = False
    salt: float = 0.0            # places an invented need on the taste circle


def base_needs() -> list[NeedSpec]:
    """The four founding needs (J). Costs are set so that, at the outside wage of
    $1,000 a week, a full basket costs $880 and takes about 0.57 of a worker to supply."""
    return [
        NeedSpec(
            name="food", kind="flow", weight=0.40, essential=True, priority=0,
            service_labour=0.18, goods_per_sub=1.0, make_labour=0.14,
            import_price=18_900, export_price=16_800, export_quota=1_100.0,
            initial_price=40_000, trips_per_week=2.0,
        ),
        NeedSpec(
            name="housing", kind="asset", weight=0.35, essential=True, priority=1,
            service_labour=0.01, goods_per_sub=0.0, make_labour=0.08,
            import_price=10_800, export_price=9_600, export_quota=1_100.0,
            initial_price=33_000,
            build_labour=30.0, build_goods=500.0,
            upkeep_labour=0.04, upkeep_goods=0.4, upkeep_growth=0.04,
            aging_rate=0.012, life_years=50.0, initial_units=60,     # (J) 16/11/2026: 60 homes
        ),
        NeedSpec(
            name="appliances", kind="asset", weight=0.15, essential=False, priority=3,
            service_labour=0.005, goods_per_sub=0.0, make_labour=0.10,
            import_price=13_500, export_price=12_000, export_quota=600.0,
            initial_price=5_500,
            build_labour=0.5, build_goods=40.0,
            upkeep_labour=0.010, upkeep_goods=0.03, upkeep_growth=0.15,
            aging_rate=0.06, life_years=10.0, initial_units=120,
        ),
        NeedSpec(
            name="entertainment", kind="flow", weight=0.10, essential=False, priority=4,
            service_labour=0.05, goods_per_sub=1.0, make_labour=0.03,
            import_price=2_700, export_price=2_000, export_quota=500.0,
            initial_price=9_500, trips_per_week=1.0,
        ),
    ]


def _founding_capital() -> dict[str, int]:
    return {
        "housing": 250_000_000,
        "food": 60_000_000,
        "appliances": 50_000_000,
        "entertainment": 40_000_000,
    }


@dataclass
class Config:
    # --- the run -------------------------------------------------------------
    world: str = "wef"                    # (J) 16/11/2026: 'wef' (everything rented) or 'rtr' (Right to Repair)
    seed: int = 1
    years: int = 60
    population_cap: int = 0               # (J) 16/11/2026: no cap; the homes that can be built are the limit.
                                          # (J) 12/11/2026 was 1,000. Above 0, arrivals stop there.
    snapshot_every: int = 1               # weeks between snapshots of every agent and firm
    register_every: int = 13              # weeks between share-register and unit snapshots
    weeks_per_year: int = 52
    quarter_weeks: int = 13

    # --- happiness and failure -------------------------------------------------
    failure_unhappy_share: float = 0.90   # (J) the run fails at 90% unhappy
    failure_min_population: int = 20      # guard: ignore the rule in a near-empty town
    stop_on_failure: bool = True
    happy_cutoff: float = 0.50
    w_security: float = 0.5
    w_provision: float = 0.3
    w_condition: float = 0.2

    # --- the outside world ------------------------------------------------------
    outside_wage: int = 100_000           # a worker moves to town only for at least this
    worker_cash_median: int = 300_000     # (J) each agent starts with a sum of money
    worker_cash_sigma: float = 0.6
    founder_arrival_rate: float = 0.04    # chance per week that a founder turns up (town under the cap)
    founder_capital_median: int = 50_000_000
    founder_capital_sigma: float = 0.7
    founder_keep_share: float = 0.10      # part of their capital a founder keeps as personal cash
    founding_capital: dict[str, int] = field(default_factory=_founding_capital)
    founder_personal_cash: int = 5_000_000

    # --- temperament, fixed at birth ---------------------------------------------
    loss_aversion_median: float = 2.0     # a loss weighs about twice a gain
    loss_aversion_sigma: float = 0.3
    loss_aversion_min: float = 1.0
    loss_aversion_max: float = 4.0
    horizon_median_weeks: float = 104.0
    horizon_sigma: float = 0.8
    horizon_min_weeks: float = 4.0
    horizon_max_weeks: float = 520.0
    growth_expect_low: float = 0.0        # (J) each shareholder's own expected growth in returns
    growth_expect_mode: float = 0.04
    growth_expect_high: float = 0.15

    # --- security ------------------------------------------------------------------
    security_start: float = 0.7
    security_up_rate: float = 0.04        # recovers slowly
    security_down_rate: float = 0.12      # falls fast, scaled by loss aversion
    horizon_floor: float = 0.10           # share of the natural horizon left at zero security
    shock_job_loss: float = 0.20
    shock_missed: float = 0.05
    shock_eviction: float = 0.20
    shock_loan_called: float = 0.10
    shock_default: float = 0.15
    shock_price_scale: float = 2.0        # a price rise costs (rise / income) x this
    boost_hired: float = 0.10
    sec_w_adequacy: float = 0.40          # income against the cost of their subscriptions
    sec_w_buffer: float = 0.30            # weeks of savings
    sec_w_position: float = 0.30          # has a job, or lives on dividends
    sec_w_debt: float = 0.15              # taken off for debt
    adequacy_low: float = 0.6             # income/basket at or below this scores 0
    adequacy_high: float = 1.2            # at or above this scores 1
    buffer_full_weeks: float = 26.0

    # --- household behaviour -----------------------------------------------------------
    calm_horizon_weeks: float = 26.0      # an effective horizon this long counts as calm
    buffer_weeks_min: float = 4.0
    buffer_weeks_max: float = 52.0
    buffer_horizon_divisor: float = 4.0   # savings target = horizon / this, in weeks of bills
    grace_weeks: int = 4                  # missed payments before eviction or repossession
    signup_min: int = 5                   # customers a service firm may take beyond what its staff can serve
    signup_headroom: float = 0.10         # and this share more, so it can grow
    switch_prob: float = 0.125            # chance per week of shopping around, per need
    switch_friction: float = 0.05
    habit_weeks: int = 52                 # (J) 16/11/2026: a lost luxury stops being missed a year after they last held it.
                                          # 0: missed for ever while someone sells it (as first written).
    adopt_margin: float = 1.2             # spare income needed, as a multiple of the price
    adopt_cushion_weeks: float = 26.0
    search_prob: float = 0.10             # employed staff looking around each week
    search_prob_squeezed: float = 0.50
    move_rise: float = 0.05               # wage rise that makes a move worthwhile
    reservation_decay: float = 0.05       # reservation wage falls this much per week out of work
    invest_prob: float = 0.25
    invest_fraction: float = 0.30
    bid_cap: float = 1.25                 # never bid above this multiple of the last price
    bid_edge: float = 0.02
    sell_review_prob: float = 1 / 13
    sell_discount: float = 0.10
    sell_fraction: float = 0.10
    sell_min_firm_age: int = 104
    book_weight: float = 0.5              # a share is worth at least this share of book value
    prior_yield: float = 0.10             # assumed dividend yield on book for a firm with no record
    horizon_value_cap: float = 520.0
    satisfaction_gain: float = 2.0
    satisfaction_min: float = 0.5
    satisfaction_max: float = 1.5
    rentier_cover: float = 1.0            # dividends must cover this multiple of their bills to count as living on them

    # --- firms ----------------------------------------------------------------------------
    share_par: int = 1_000                # shares start at $10
    price_rule: str = "ratchet"           # (J) 'ratchet': price only rises on a shortfall. 'search': back off a rise that lost profit
    price_step: float = 0.03
    wage_step_up: float = 0.02            # (J) bidding for scarce workers
    wage_unfilled_weeks: int = 2
    wage_step_down: float = 0.02          # (J) cutting when there is a queue
    wage_cut_unemployment: float = 0.05
    exec_span: int = 25                   # one executive per this many staff
    exec_pay_multiple: float = 2.5
    ceo_pay_base: float = 1.5
    ceo_pay_per_staff: float = 0.05
    ceo_pay_cap: float = 8.0
    reserve_weeks: float = 8.0            # cash kept back before dividends
    hire_min: int = 3                     # people a firm may bring in from outside in one week:
    hire_rate: float = 0.10               # this many, or this share of its staff if that is more
    layoff_min: int = 1
    layoff_rate: float = 0.10
    growth_allowance: float = 0.03        # staff are planned for a few more customers than today
    staff_slack: float = 0.05             # spare staff tolerated before anyone is laid off
    startup_weeks: int = 26               # a new service firm keeps one worker while it finds customers
    upkeep_floor: float = 0.2
    skimp_step: float = 0.10
    restore_step: float = 0.05
    skimp_horizon_ref: float = 52.0
    cond_recover: float = 0.02            # weekly climb toward the best condition under full upkeep
    cond_neglect: float = 0.01            # weekly fall under no upkeep
    cond_floor_best: float = 0.3
    replace_below: float = 0.5            # rebuild a unit whose best condition is below this
    build_crew: float = 6.0               # worker-weeks one project can absorb in a week
    vacancy_buffer_min: int = 4
    vacancy_buffer_share: float = 0.06
    unmet_decay: float = 0.9
    max_starts_week: int = 6
    spare_units_min: int = 2
    spare_units_share: float = 0.03
    overhead_allowance: float = 0.10      # executives' cost on top of staff wages, when costing a unit made in town
    make_hysteresis: float = 0.05
    export_margin: float = 0.02
    export_price_drop: float = 0.0        # the outside pays this much less for the last unit of a firm's quota
                                          # share than for the first. 0 means one price for the whole quota.
    payout_min: float = 0.3
    payout_horizon_ref: float = 26.0
    share_pay_firm_share: float = 0.30    # (J) part-wages in shares, at some firms
    share_pay_fraction: float = 0.05
    equity_pref_share: float = 0.5        # (J) founder chooses shares or debt by temperament
    issue_discount: float = 0.05
    issue_weeks: int = 13

    # --- new firms -------------------------------------------------------------------------
    invent_prob: float = 0.35             # (J) a founder may invent a new need; no limit
    entry_margin: float = 0.10
    undercut: float = 0.08
    cost_floor_markup: float = 0.05
    new_need_markup: float = 0.30
    resident_founder_rate: float = 0.05   # chance per quarter, times appetite for risk
    flow_entry_capital: int = 15_000_000
    asset_entry_capital: int = 60_000_000
    founder_invest_share: float = 0.7
    invented_weight: float = 0.08
    invented_labour_low: float = 0.03
    invented_labour_high: float = 0.10
    invented_appeal_low: float = 0.3
    invented_appeal_high: float = 0.9
    idle_windup_weeks: int = 26

    # --- failure and takeover -----------------------------------------------------------------
    fire_sale: float = 0.5                # share of asset value a buyer pays for a failed firm
    takeover_capital_weeks: float = 8.0
    takeover_min_weeks: float = 2.0
    takeover_cash_share: float = 0.8

    # --- the bank (J: federal backstop, never fails, interest leaves town) -----------------------
    firm_rate: float = 0.06
    ltv: float = 0.60                     # firms borrow against assets only
    firm_term_weeks: int = 520
    firm_missed_limit: int = 4
    personal_rate: float = 0.12
    personal_limit_weeks: float = 8.0     # individuals borrow against income only
    personal_term_weeks: int = 52
    call_grace_weeks: int = 8             # a called loan unpaid this long is written off
    default_block_weeks: int = 156
    bank_can_force_share_sale: bool = False   # (J) emotional state decides; the bank lent against income, not shares
    transport_can_close: bool = False         # (J) 16/11/2026: with riders it is always sold on; true = closes like any other
    fare_first_for_work: bool = True          # (J) 16/11/2026: a ride to work is paid after food and before rent; false = after rent
    shops_near_unserved: bool = True          # (J) 16/11/2026: a founder enters a shop need people cannot reach, near them
    unserved_entry_min: int = 20              # (C) residents who cannot reach any seller before that is a gap (as transport_trigger)
    # (J) 16/11/2026, decision 8: the well-off spend more, on a bigger plan and a better home
    well_off_income: float = 1.5          # (C) well-off: income this many times the week's bills at standard size, cushion full. 0: off
    well_off_drop: float = 1.2            # (C) no longer well-off below this, or with cash under half the cushion
    bigger_plan: int = 2                  # (J) a well-off plan of food, entertainment or a luxury is this many standard plans
    better_home: float = 1.5              # (C) a better home costs this many times as much to build, keep up and rent

    # --- the map (stage 2; J: distance is real, land runs out, transport is a subscription) ---------
    map_width: int = 13                   # spots across. 0 switches the map off: stage 1 behaviour
    map_height: int = 13                  # 169 spots is about what a full town of 1,000 needs
    homes_per_spot: int = 8               # homes one spot can hold
    walk_range: int = 6                   # blocks an agent will walk one way: about half an hour
    minutes_per_block: float = 5.0
    commute_trips: float = 5.0            # round trips to work a week
    transport_speed: float = 4.0          # times faster than walking; reach grows by the same
    time_value_share: float = 0.025       # an hour on the road is weighed as this share of the weekly staff wage
    location_premium: float = 0.25        # the best-placed home rents this much above average, the worst this much below
    access_jobs_weight: float = 0.6       # nearness to work against nearness to shops
    popularity_step: float = 0.02         # a spot let in full all quarter rises this much; an emptier one falls
    popularity_min: float = 0.8
    popularity_max: float = 1.25
    move_prob: float = 0.03               # chance per week a resident looks at moving home
    premises_cost: int = 3_000_000        # fitting out a firm's premises, bought from outside
    land_years: float = 6.0               # an owner values a spot at this many years of its rent roll
    land_markup: float = 0.25             # and asks this much more to sell
    land_floor: int = 2_000_000           # the least a spot sells for once land is scarce
    lease_rate: float = 0.10              # ground rent per year as a share of the asking price
    transport_trigger: int = 20           # people turned away for distance in a quarter before transport is started
    transport_fixed_labour: float = 6.0   # the crew it needs however few ride
    transport_rider_labour: float = 0.01  # worker-weeks per rider
    transport_assumed_riders: int = 150   # riders its first price is worked out for

    # --- the Right to Repair world (16/11/2026; read only when world is 'rtr') ----------------------
    free_hours: float = 60.0              # (C) hours a week anyone has beyond sleep and keeping themselves
    job_hours: float = 40.0               # (C) a job takes this many; one worker-week of the model's costs
    mortgage_ltv: float = 1.0             # (J) 18/11/2026: "Lend the whole price" where the income allows; it was (C) 0.80, a fifth in cash
    mortgage_weeks: int = 1040            # (C) over twenty years, at the rate firms pay
    mortgage_income_share: float = 0.30   # (C) "if their income allows" (J): the payment is at most this share of income
    foreclosed_price_drop: float = 0.05   # (C) a foreclosed home's asking price falls this much each quarter unsold
    empty_sale_weeks: int = 52            # (J) "Sells it cheap": a landlord's home empty this long is sold at its value
    newcomers_buy: bool = True            # (J) 18/11/2026: a newcomer who finds nothing to rent may buy a home the bank holds empty
    owners_pay_any_price: bool = True     # (J) 18/11/2026: the owner class has repairs done by anyone, at any price
    makers_weigh_jobs: bool = True        # (J) 18/11/2026: out of work with a side hustle, they take a job only if it pays more, or with a large loan
    home_loan_presses: bool = False       # (J) 18/11/2026: "No, stay": the loan against a home is not the large loan that sends a maker to the first job
    makers_buy_in_town: bool = True       # (J) 18/11/2026: a maker buys goods outside only if the town has none at a reasonable price
    town_goods_premium: float = 0.10      # (C) "reasonable": this much over the outside price at most (J: $200 for $189 yes, $298 no)
    line_is_who_would_take: bool = True   # (J) 19/11/2026: "they wouldn't even apply for the job": the line that lets a firm cut its wage is those out of work who would take the job
    staff_keep_pay: bool = True           # (J) 19/11/2026: "Old staff members still stay on the same pay rate": a cut in a firm's wage is for those hired after it
    loss_sheds_staff: bool = True         # (J) 19/11/2026: "we will sack the oldest staff member until the value of the total wages is less than the debt. Before we hire new staff": a firm in debt that lost money over the quarter lets its longest-serving staff go until their pay covers the loss ("No, only if in debt"); then it hires as it needs
    longest_serving_first: bool = True    # (J) 19/11/2026: "the oldest staff member": whoever an employer has to let go, the longest-serving goes first
    owners_judge_by_what_they_pay: bool = True   # (J) 20/11/2026: "it should be judged on what they actually pay because they own it. The reason they want to own it is because they don't want to know what the firms are being priced at": a home or appliance set of their own counts in their basket at its upkeep (and the loan payment), not the cheapest asking rent; the town's basket is the average of its people's
    reservation_covers_basket: bool = True   # (C) 21/11/2026, at Jason's "fix the issue" of pay falling to $100 a week: the least someone out of work will take never falls below what their own basics cost them a week (their basket); before it, it fell 5% a week to nothing, so the line never shrank and firms cut for decades
    going_without_at_lowest_price: bool = True   # (J) 21/11/2026: "The price that they can't afford should always be the one that's the lowest out of the possible two. neighbours entertainment or firms Entertainment. It will be the one that they could actually achieve, not the one that's way out of scope": in a person's basket a need they go without counts at the lowest price a firm or a neighbour asks (a maker's price, full or not; a small landlord's rent), not only what is on offer this week
    unhappy_makers_apply: bool = True     # (J) 19/11/2026: "Unless they're unhappy. and wanted to get out of this hard hustle": unhappy on a side hustle, they take a job as anyone out of work does
    maker_margin: float = 0.10            # (C) "cost plus a little": what a person making or letting adds to their cost
    # stage 2: makers. A side hustle is one person selling their own spare time to others.
    hustle_min_hours: float = 10.0        # (C) spare hours a week someone needs to start a side hustle
    hustle_rate: float = 0.01             # (C) chance a week of starting one, times their appetite for risk
    hustle_rate_struggling: float = 0.10  # (C) for someone out of work or whose income does not cover their
                                          # basket (J: "It gives them the opportunity to get out of the struggling")
    maker_hour_floor: float = 0.5         # (C) a maker's hour is never worth less than this share of the going hourly wage
    hustle_quit_share: float = 0.2        # (C) under a fifth of the customers they could serve for a quarter: they give it up
    hustle_full_share: float = 0.95       # (C) "full for a quarter": they sold at least this share of what they could
    hustle_loan_weeks: float = 26.0       # (C) the bank lends this many weeks of a side hustle's weekly profit
    hustle_loan_term_weeks: int = 260     # (C) over five years, at the rate firms pay
    idea_rate: float = 0.00002            # (C) chance a week of an idea, for every `idea_hours` spare hours they have left
    idea_hours: float = 20.0
    tools_entertainment: int = 0          # (J) "the computer they already have"; software too
    tools_invented: int = 50_000          # (C) the tools to start selling something someone thought up
    tools_food: int = 200_000             # (C)
    tools_repair: int = 100_000           # (C)
    tools_set_building: int = 500_000     # (J) his chairs: "table saws, drills, tools"; (C) the amount
    tools_home_building: int = 1_000_000  # (C)

    # --- needs ---------------------------------------------------------------------------------
    needs: list[NeedSpec] = field(default_factory=base_needs)

    # ------------------------------------------------------------------------------------------
    def need(self, name: str) -> NeedSpec:
        for n in self.needs:
            if n.name == name:
                return n
        raise KeyError(f"unknown need: {name}")

    @property
    def rtr(self) -> bool:
        """Is this the Right to Repair world?"""
        return self.world == "rtr"

    def at_cap(self, population: int) -> bool:
        """Has the town as many people as it may have? Never, when there is no cap."""
        return 0 < self.population_cap <= population

    @property
    def weeks(self) -> int:
        return self.years * self.weeks_per_year

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        d = dict(d)
        needs = [NeedSpec(**n) for n in d.pop("needs")]
        known = {f.name for f in fields(cls)}
        for key in d:
            if key not in known:
                raise KeyError(f"unknown dial: {key}")
        cfg = cls(needs=needs, **d)
        validate(cfg)
        return cfg


# The settings that give the model as it was built before Jason's rulings of 16/11/2026.
# With them a town gives the same record as it did then, event for event.
OLD_RULES = ["population_cap=1000", "habit_weeks=0", "needs.housing.initial_units=120", "transport_can_close=true",
             "fare_first_for_work=false", "shops_near_unserved=false", "well_off_income=0"]

CHOICES = {"price_rule": ("ratchet", "search"), "world": ("wef", "rtr")}

# The two worlds, as they are named to a reader. Each has a folder of its own (wef/, rtr/)
# with its settings, and is run from there.
WORLD_NAMES = {"wef": "WEF world", "rtr": "RTR world"}
WORLD_SAYS = {"wef": "everything is rented", "rtr": "people may rent or own, build and let"}
# Dials only the RTR world reads: they are left out of the WEF world's settings file.
MAKER_SHARES = ("hustle_rate", "hustle_rate_struggling", "maker_hour_floor", "hustle_quit_share",
                "hustle_full_share", "idea_rate")          # each a chance or a share: from 0 to 1
MAKER_TOOLS = ("tools_entertainment", "tools_invented", "tools_food", "tools_repair", "tools_set_building",
               "tools_home_building")
RTR_ONLY = ("free_hours", "job_hours", "mortgage_ltv", "mortgage_weeks", "mortgage_income_share",
            "foreclosed_price_drop", "empty_sale_weeks", "newcomers_buy", "owners_pay_any_price", "makers_weigh_jobs", "home_loan_presses", "makers_buy_in_town", "town_goods_premium",
            "line_is_who_would_take", "unhappy_makers_apply", "staff_keep_pay", "loss_sheds_staff", "longest_serving_first",
            "owners_judge_by_what_they_pay", "going_without_at_lowest_price", "reservation_covers_basket", "maker_margin",
            "hustle_min_hours", "hustle_loan_weeks", "hustle_loan_term_weeks", "idea_hours") + MAKER_SHARES + MAKER_TOOLS
AT_LEAST_ONE = ("snapshot_every", "register_every", "years", "quarter_weeks", "weeks_per_year",
                "mortgage_weeks", "hustle_loan_term_weeks")


def validate(cfg: "Config") -> None:
    """Refuse settings that would run something other than what was asked for, or crash part way."""
    for key, allowed in CHOICES.items():
        if getattr(cfg, key) not in allowed:
            raise ValueError(f"{key} must be one of {', '.join(allowed)}; got {getattr(cfg, key)!r}")
    for key in AT_LEAST_ONE:
        if getattr(cfg, key) < 1:
            raise ValueError(f"{key} must be at least 1")
    if cfg.map_width > 0 and (cfg.map_width < 3 or cfg.map_height < 3):
        raise ValueError("the map must be at least 3 by 3 spots, or map_width 0 for no map")
    for key in ("map_width", "map_height", "walk_range"):
        if getattr(cfg, key) < 0:
            raise ValueError(f"{key} cannot be negative")
    if not 0.0 <= cfg.mortgage_ltv <= 1.0:
        raise ValueError("mortgage_ltv must be between 0 and 1: the bank lends at most the home's price")
    if cfg.mortgage_income_share < 0 or not 0.0 <= cfg.foreclosed_price_drop < 1.0:
        raise ValueError("mortgage_income_share cannot be negative, and foreclosed_price_drop is from 0 up to 1")
    if cfg.job_hours <= 0 or cfg.free_hours < 0:
        raise ValueError("job_hours must be more than 0 and free_hours cannot be negative")
    for key in MAKER_SHARES:
        if not 0.0 <= getattr(cfg, key) <= 1.0:
            raise ValueError(f"{key} must be between 0 and 1")
    for key in MAKER_TOOLS:
        if getattr(cfg, key) < 0:
            raise ValueError(f"{key} cannot be negative: tools cost something or nothing")
    if cfg.town_goods_premium < 0:
        raise ValueError("town_goods_premium cannot be negative: 0 means no dearer than the outside price")
    if cfg.hustle_min_hours <= 0 or cfg.idea_hours <= 0 or cfg.hustle_loan_weeks < 0:
        raise ValueError("hustle_min_hours and idea_hours must be more than 0, and hustle_loan_weeks cannot be negative")
    if cfg.bigger_plan < 1 or cfg.better_home < 1:
        raise ValueError("bigger_plan and better_home must be at least 1")
    if cfg.homes_per_spot < 1 or cfg.transport_speed < 1:
        raise ValueError("homes_per_spot and transport_speed must be at least 1")
    if 0 < cfg.population_cap < len(cfg.needs):
        raise ValueError(f"population_cap must be at least {len(cfg.needs)}: "
                         "every founding firm brings its founder")


def _coerce(current, value, key: str):
    """Keep each dial's type: a typo like population_cap=abc must not run."""
    if isinstance(current, bool):
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be true or false")
        return value
    if isinstance(current, int):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{key} must be a whole number")
        return value
    if isinstance(current, float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a number")
        return float(value)
    if isinstance(current, str):
        return str(value)
    return value


def _set(cfg: Config, key: str, value) -> None:
    parts = key.split(".")
    if parts[0] == "needs" and len(parts) == 3:
        spec = cfg.need(parts[1])
        if parts[2] not in {f.name for f in fields(NeedSpec)}:
            raise KeyError(f"unknown dial: {key}")
        setattr(spec, parts[2], _coerce(getattr(spec, parts[2]), value, key))
        return
    if parts[0] == "founding_capital" and len(parts) == 2:
        if parts[1] not in cfg.founding_capital:
            raise KeyError(f"unknown dial: {key}")
        cfg.founding_capital[parts[1]] = _coerce(cfg.founding_capital[parts[1]], value, key)
        return
    if len(parts) != 1 or parts[0] in ("needs", "founding_capital"):
        raise KeyError(f"unknown dial: {key}")
    if parts[0] not in {f.name for f in fields(Config)}:
        raise KeyError(f"unknown dial: {key}")
    setattr(cfg, parts[0], _coerce(getattr(cfg, parts[0]), value, key))


def _apply(cfg: Config, data: dict, prefix: str = "") -> None:
    for key, value in data.items():
        full = f"{prefix}{key}"
        if isinstance(value, dict):
            _apply(cfg, value, prefix=f"{full}.")
        else:
            _set(cfg, full, value)


def load_config(path: str | None = None, overrides: list[str] | None = None) -> Config:
    """Defaults, then a settings file (JSON), then key=value overrides."""
    cfg = Config()
    unsaid: set[str] = set()
    if path:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data.get("needs"), list):
            cfg = Config.from_dict(data)       # a full set of settings, as a run folder keeps it
            unsaid = {f.name for f in fields(Config)} - set(data)
        else:
            _apply(cfg, data)                  # a short file that changes a few dials
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"override must be key=value: {item}")
        key, raw = item.split("=", 1)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        _set(cfg, key.strip(), value)
        unsaid.discard(key.strip().split(".")[0])
    if not cfg.rtr:
        unsaid -= set(RTR_ONLY)                # the WEF world does not read them: its file leaves them out
    if unsaid:
        # A full file is the record of one town's settings. A dial it does not name was added
        # after it was saved; to fill it in with today's value would run, without a word, a
        # town that file never stood for (the fresh review, 18/11/2026).
        names = sorted(unsaid)
        today = ", ".join(f"{name}={json.dumps(getattr(cfg, name))}" for name in names)
        raise ValueError(
            f"{path} is a full set of settings saved before these dials existed: {', '.join(names)}. "
            f"Today's values would be {today}, which may not be the town this file was saved from. "
            "Say which you mean: add each to the file, or give it with --set.")
    validate(cfg)
    return cfg
