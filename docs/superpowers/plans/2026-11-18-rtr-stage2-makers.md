# RTR stage 2: makers, ideas, and side hustles that grow. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In a town of the RTR world a person can sell their own spare time to others as a side hustle (a need, repairs, or building for others), anyone can have an idea for a new thing, and a side hustle can grow into a small business and then a company; a town of the WEF world is still the town it was.

**Architecture:** Two parts, each ending in whole towns under the weekly checks. **Part A** adds the `Hustle`: a small object that stands where a firm stands in the selling code (`price`, `subs`, `spec`, `cash`, `spot`), as `Letting` does for homes, and is in no list of firms. Customers find it through `find_provider`; it serves them with its owner's spare hours. Repairers and builders sell hours through one function, `buy_hours`. **Part B** adds ideas (a new need from a person's spare time), the bank's loan on a side hustle's profit with staff taken on, and the move to a company by the WEF founding rule. Every maker rule lives in one new file, `engine/rtr_makers.py`, called from `Town.step` only when `cfg.rtr`.

**Tech Stack:** Python 3.12, standard library only; pytest (`python3 -m pytest -rN --tb=short` from the top folder; `addopts` already has `-q`).

**Spec:** `docs/superpowers/specs/2026-11-16-rtr-world-design.md`, sections 5, 8, 9, 10, 11, 12. Stage 1 (plans of 16 and 17 November; `develop` at `3d10127`) is the base. The spec names files as they were before 17 November: see `docs/README.md` (`wefworld/` is `engine/`, `owning.py` is `rtr_owning.py`).

## Global Constraints

- A WEF town is unchanged: the pins in `tests/test_rtr.py` (`WEF_PINS`) hold after every task, and seed 74 of the 13 November batch under `wef/before-16-november.json` still gives `08251209eb136522` with 180,377 events (checked by hand at the end of each part). Every edit outside `engine/rtr_makers.py` is behind `cfg.rtr`, `town.hustles` (empty in a WEF town) or `agent.hustle` (None in a WEF town), and draws no random number a WEF town did not draw.
- Every dollar moves through `Ledger.pay`. Goods, parts and tools a maker buys are kind `import` (they leave town). A customer paying a maker for a need is `subscription`; for hours it is `maker_hours` (inside town). Wages a small business pays are `wage`. The loan on profit enters as `loan` and leaves as `loan_principal` and `loan_interest`.
- Numbers from the spec, copied: a side hustle needs 10 or more spare hours (`hustle_min_hours`); chance a week `hustle_rate_struggling` 0.10 for someone out of work or whose income does not cover their basket, otherwise `hustle_rate` 0.01 times their appetite for risk; price is cost plus `maker_margin` 0.10; an hour is never worth less than `maker_hour_floor` 0.5 of the going hourly staff wage; tools: entertainment $0, an invented thing $500, food $2,000, repair $1,000, building appliance sets $5,000, building homes $10,000; a maker with fewer than a fifth (`hustle_quit_share` 0.2) of the customers they could serve for a quarter gives it up; the bank lends `hustle_loan_weeks` 26 weeks of the side hustle's weekly profit over five years (`hustle_loan_term_weeks` 260) at `firm_rate`; `idea_rate` 0.00002 a week for every 20 spare hours (`idea_hours`); a company needs the capital of the WEF rule (`flow_entry_capital`, $150,000). One worker-week is `job_hours` 40.
- Not the ride, and not letting homes or appliance sets: a maker sells food, entertainment, an invented need, repairs, or building.
- Spare time is spent in the spec's order: keeping up what they own, then the side hustle, then building for themselves; what is left counts toward ideas. Nobody's spare hours go below zero.
- New weekly measures and event kinds only when `cfg.rtr`. `rtr/settings.json` is the engine's own settings for the RTR world and `wef/settings.json` has none of the new dials (`tests/test_worlds.py` holds both).
- No em dashes in docs, comments or pages. Say "WEF world" or "RTR world", never the folder. Every (C) call goes in `docs/build-ledger-rtr-stage2-2026-11-18.md` as `Ruling: <what> ; <why> ; <cost if wrong>`. The calls this plan already makes are listed next and go into the ledger at the task that builds them.
- **Tests must bite.** Each part ends by breaking its rules one at a time in a scratch copy (`mutate.py`, as on 17 November): every break must fail a test in `tests/test_rtr_2.py`, or a test is added until it does.
- **Clean runs on three seeds are not evidence of no crash** (the review of stage 1b found a crash in one full town in ten that three towns missed). Each part ends with forty full towns of the RTR world, seeds 1 to 40, run from `rtr/` with `python batch.py <name> --seeds 1-40`: every one must end failed or survived, none with an error.

## Calls made in this plan (C), each for the ledger

1. **Goods from takings.** A maker buys the week's goods after the customers have paid, out of what they paid, so that someone with no money can start (J: "a way out of struggling"). Who is served is settled before the bills, by hours alone.
2. **The yardstick.** `cheapest_prices` counts a maker's price for a need only while no firm sells that need. A maker serves a handful; letting one cheap maker lower everyone's basket would make the whole town feel richer. A customer of a maker still counts what they really pay.
3. **From home.** A side hustle needs a home to work from. On a map its place is its owner's home; an owner with no home at the week's start gives it up.
4. **Never their own customer.** Food and services are bought, as now (spec section 8, last point).
5. **Hours trades.** Repairers and builders charge, for each hour, their hour and that hour's parts, plus the margin, and buy the parts from outside themselves. For an appliance set the customer has already bought the parts (stage 1a), so a set builder is paid for hours only. The bank's loan on a home being built is drawn by the customer as now, then paid on.
6. **"Does not have the hours"** means: for upkeep, short this week; for building, the hours left would take more than a quarter of their spare time at this week's rate. Hours are bought only with cash beyond four weeks of bills.
7. **Full** for a quarter means they sold at least `hustle_full_share` (0.95) of what they could. A side hustle is judged, to stop or to grow, only on a whole quarter.
8. **The loan on profit** is taken only when it comes to at least four weeks of the going wage. It is unsecured: if four payments in a row are missed, or the side hustle stops while it is owed, the owner pays what cash they have toward it, the bank writes off the rest, and they are refused credit for `default_block_weeks`, as after a personal default.
9. **A small business hires residents only**, after the firms have hired, at the going wage that week. Firms still bring people in from outside.
10. **A company** is founded only from a need trade (no firm in the model sells hours), with `founder_invest_share` of the owner's cash after the loan is repaid, at the higher of the maker's price and the WEF entrant's floor (`unit_cost` plus `cost_floor_markup`), near the owner's home. In an RTR town `resident_founders` leaves makers to this rule.
11. **An idea** is started by its creator at once, with no dice, if they have no side hustle, the hours, a home and the $500. It is open to everyone else from the week after.
12. **Against a home.** An owner borrows against their home for a side hustle's tools only. A business short of wages lets staff go; it does not borrow more.

## Review Focus

1. A maker loses their home, or moves, with customers signed up: the side hustle ends or follows them, customers out of reach drop it, and nobody is billed by a side hustle that has stopped. (Task 2.)
2. A maker takes a job (60 spare hours become 20) with customers signed up: the newest go unserved and unbilled that week and may move to another seller; no goods are bought for them. (Task 2.)
3. The last firm selling a need closes while makers sell it, and an invented need is sold only by a maker: the basket takes the cheapest maker's price, the need still counts toward provision, and people can still take it up. (Task 2.)
4. A repairer who owns a home: they sell only the hours left after their own upkeep, and their own home is still kept up. (Task 5.)
5. A small business cannot pay its wages or its loan: staff are let go last hired first, the loan is written off through the bank, the customers are released, and no money appears or vanishes. (Task 8.)
6. A maker becomes a company: every customer and every worker ends on exactly one seller's and one employer's books, that same week. (Task 9.)

---

## Part A: side hustles

### Task 1: Dials, the side hustle, what an hour is worth, and prices

**Files:**
- Create: `engine/rtr_makers.py`, `tests/test_rtr_2.py`, `docs/build-ledger-rtr-stage2-2026-11-18.md`
- Modify: `engine/config.py` (dials, `RTR_ONLY`, `AT_LEAST_ONE`, `validate`), `engine/entities.py` (class `Hustle`; Agent slot `hustle`, default None), `engine/town.py` (`self.hustles: list = []`, `self.ideas_total = 0`, `self.new_ideas: set = set()`), `rtr/settings.json` (made again from the engine), `tests/test_worlds.py` (its own `RTR_ONLY` set)

**Interfaces:**
- Produces:
  - Dials, all in `RTR_ONLY`: `hustle_min_hours: float = 10.0`, `hustle_rate: float = 0.01`, `hustle_rate_struggling: float = 0.10`, `maker_hour_floor: float = 0.5`, `hustle_quit_share: float = 0.2`, `hustle_full_share: float = 0.95`, `hustle_loan_weeks: float = 26.0`, `hustle_loan_term_weeks: int = 260`, `idea_rate: float = 0.00002`, `idea_hours: float = 20.0`, `tools_entertainment: int = 0`, `tools_invented: int = 50_000`, `tools_food: int = 200_000`, `tools_repair: int = 100_000`, `tools_set_building: int = 500_000`, `tools_home_building: int = 1_000_000`. `validate` refuses a rate or share outside 0 to 1, hours of 0 or less, a negative tools cost, a term under 1.
  - `entities.Hustle(owner, trade: str, spec, week: int)`: `owner`; `trade` (a need's name, or `"repair"`, `"set_building"`, `"home_building"`); `spec` (the need's `NeedSpec`, None for the three hour trades); `need = trade`; `id = -(1_000_000 + owner.id)`; `name`; `alive = True`; `started = week`; `price` (a week of the need, or one hour); `subs = {}`, `extra = 0`, `unserved = {}`, `turned_away = {}`, `waiting = 0`; `spot = None`; `hours = 0.0` (hours it has for customers this week), `sold = 0.0`, `capacity = 0`; `w_revenue`, `w_goods`, `w_wages`, `q_revenue`, `q_goods`, `q_wages`, `q_sold`, `q_could` (all 0); `profit_week = 0`; property `cash` that reads and writes `owner.cash`; `load()` as a firm's. It is in `town.hustles` and in no list of firms.
  - `rtr_makers.HOUR_TRADES = ("repair", "set_building", "home_building")`.
  - `rtr_makers.trades(town) -> list[tuple[str, NeedSpec | None]]`: food, entertainment, every invented need but transport and but those in `town.new_ideas`, then the three hour trades.
  - `rtr_makers.tools_cost(cfg, trade: str, spec) -> int`.
  - `rtr_makers.hour_worth(town, agent) -> float`: cents an hour. In work: `agent.wage / job_hours`. Out of work: the wage they would now accept, exactly as `labour_market` reckons it (`int(last_wage * security * max(0, 1 - reservation_decay * weeks_out))`), over `job_hours`. Never under `maker_hour_floor * town.typical_wage() / job_hours`.
  - `rtr_makers.need_price(town, agent, spec) -> int`: `round((goods_per_sub * import_price + service_labour * job_hours * hour_worth) * (1 + maker_margin))`, at least 1.
  - `rtr_makers.hour_price(town, agent) -> int`: `round(hour_worth * (1 + maker_margin))`.
  - `rtr_makers.hours_per_customer(cfg, spec) -> float`: `spec.service_labour * cfg.job_hours` (the firm's own service figure).
  - `rtr_makers.open_hustle(town, agent, trade: str) -> Hustle`: makes it with today's price, puts it in `town.hustles` and `agent.hustle`. No tools are charged and no event is logged here (Task 3 does both).

- [ ] **Step 1: Write the failing tests** (top of `tests/test_rtr_2.py`; the helpers are used by every later task)

```python
"""The Right to Repair world, stage 2: makers, ideas, and side hustles that grow."""

import pytest
from test_rtr import map_rtr_town, rtr_town  # noqa: F401

from engine.config import load_config

NOBODY_STARTS = ("hustle_rate=0.0", "hustle_rate_struggling=0.0", "idea_rate=0.0")


def quiet_town(*overrides):
    """An RTR town where nothing starts by chance: a test sees only what it set up."""
    return rtr_town(*NOBODY_STARTS, *overrides)


def jobless(town, cash=0, **fixed):
    a = town.add_agent(cash=cash, **fixed)
    a.last_wage = town.cfg.outside_wage              # they last earned $1,000 a week
    return a


def worker(town, cash=0, wage=100_000, **fixed):
    """Someone on the staff of a landlord with no homes: a job, and nothing for sale."""
    a = town.add_agent(cash=cash, **fixed)
    boss = next((f for f in town.firms if f.need == "housing"), None) or town.add_firm("housing")
    a.employer, a.role, a.wage = boss, "staff", wage
    boss.staff.append(a)
    return a


def shop(town, need, price):
    """A firm selling the need, with staff who will start nothing themselves."""
    from test_subscriptions import staffed
    firm = staffed(town, need, 5, price=price)
    for w in firm.staff:
        w.risk = 0.0
    return firm


def maker(town, trade="entertainment", agent=None, **fixed):
    from engine.rtr_makers import open_hustle
    a = agent if agent is not None else jobless(town, **fixed)
    return a, open_hustle(town, a, trade)


def test_the_maker_dials_have_the_designs_values():
    cfg = load_config()
    assert (cfg.hustle_min_hours, cfg.hustle_rate, cfg.hustle_rate_struggling) == (10.0, 0.01, 0.10)
    assert (cfg.maker_hour_floor, cfg.hustle_quit_share, cfg.hustle_full_share) == (0.5, 0.2, 0.95)
    assert (cfg.hustle_loan_weeks, cfg.hustle_loan_term_weeks) == (26.0, 260)
    assert (cfg.idea_rate, cfg.idea_hours) == (0.00002, 20.0)
    assert (cfg.tools_entertainment, cfg.tools_invented, cfg.tools_food) == (0, 50_000, 200_000)
    assert (cfg.tools_repair, cfg.tools_set_building, cfg.tools_home_building) == (100_000, 500_000, 1_000_000)
    with pytest.raises(ValueError):
        load_config(None, ["hustle_rate=1.5"])


def test_what_a_makers_hour_is_worth():
    from engine.rtr_makers import hour_worth
    town = quiet_town()
    assert hour_worth(town, worker(town)) == 2_500.0                 # their wage over the forty hours
    out = jobless(town)
    assert hour_worth(town, out) == 1_750.0                          # they would take 0.7 of $1,000 at first
    out.weeks_out = 10
    assert hour_worth(town, out) == 1_250.0                          # half that by now: the floor, half the going hour
    assert hour_worth(town, worker(town, wage=40_000)) == 1_250.0    # the floor holds for the low paid too


def test_a_maker_charges_cost_plus_a_tenth():
    from engine.rtr_makers import hour_price, hours_per_customer, need_price
    town = quiet_town()
    food, fun = town.needs["food"], town.needs["entertainment"]
    w, out = worker(town), jobless(town)
    assert (need_price(town, w, food), need_price(town, w, fun)) == (40_590, 8_470)
    assert (need_price(town, out, food), need_price(town, out, fun)) == (34_650, 6_820)
    out.weeks_out = 10                                               # the struggling undercut most
    assert (need_price(town, out, food), need_price(town, out, fun)) == (30_690, 5_720)
    assert (hour_price(town, w), hour_price(town, out)) == (2_750, 1_375)
    assert hours_per_customer(town.cfg, fun) == 2.0 and hours_per_customer(town.cfg, food) == pytest.approx(7.2)


def test_a_side_hustle_is_its_owners_and_is_no_firm():
    from engine.rtr_makers import tools_cost, trades
    town = quiet_town()
    a, h = maker(town, "entertainment", cash=500)
    assert a.hustle is h and town.hustles == [h] and h not in town.firms and h.id == -(1_000_000 + a.id)
    assert h.spec is town.needs["entertainment"] and h.need == "entertainment" and h.price == 6_820
    h.cash += 100
    assert a.cash == 600                                             # its money is theirs
    b, r = maker(town, "repair")
    assert r.spec is None and r.price == 1_925                       # an hour of theirs, plus a tenth
    assert [t for t, _ in trades(town)] == ["food", "entertainment", "repair", "set_building", "home_building"]
    assert [tools_cost(town.cfg, t, s) for t, s in trades(town)] == [200_000, 0, 100_000, 500_000, 1_000_000]
```

- [ ] **Step 2: Run them.** `python3 -m pytest tests/test_rtr_2.py -rN --tb=short`. Expected: FAIL (no module `engine.rtr_makers`; unknown dials).
- [ ] **Step 3: Implement.** Make `rtr/settings.json` again as it was made on 17 November (`{"world": "rtr", **load_config(None, ["world=rtr"]).to_dict()}`, laid out as the file is now); `wef/settings.json` must not change. Add the sixteen dials to the `RTR_ONLY` set in `tests/test_worlds.py`.
- [ ] **Step 4: Run the whole suite.** Expected: all pass, the WEF pins among them.
- [ ] **Step 5: Commit** (with approval).

### Task 2: A maker as a seller

**Files:**
- Modify: `engine/subscriptions.py` (`find_provider`, `has_room`, `cheapest_prices`), `engine/rtr_makers.py`, `engine/town.py` (three calls in `step`, each under `if cfg.rtr`)
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: Task 1.
- Produces:
  - `find_provider` also offers every live side hustle whose `need` is the need asked for and whose owner is not the customer, on the same reckoning (`all_told`, reach from the customer's home to `hustle.spot`). `has_room(town, hustle)` is `hustle.load() < hustle.capacity`.
  - `cheapest_prices`: a need no live firm sells takes the cheapest live maker's price (call 2).
  - `rtr_makers.start_week(town)`, called right after `rtr_owning.start_week`: `town.new_ideas` is emptied; for each side hustle, `waiting = len(turned_away)`, `turned_away = {}`, the week's sums to 0; on a map `spot` is the owner's home spot, and an owner with no home gives it up (`stop(town, hustle, "no home")`); `hours` = the owner's spare hours less the hours their own units' upkeep needs this week (`production.upkeep_need` over `rtr_owning.homes_of` and their own set), never under 0; `capacity = int(hours / hours_per_customer + 1e-9)` for a need trade.
  - `rtr_makers.working_week(town)`, called right after `operate(town)`: each need trade serves `min(load, capacity)` standard plans, oldest customer first; the rest are in `hustle.unserved` (plan by plan, as a firm's are); the owner's `spare_hours` falls by the hours used; `q_sold += served`, `q_could += capacity`.
  - `rtr_makers.after_bills(town)`, called right after `rtr_owning.after_bills`: for each need trade, the goods for every plan served and paid for (`agent.met[need]`) are bought from outside out of the owner's cash (`import`), into `w_goods`; then `q_revenue += w_revenue`, `q_goods += w_goods`.
  - `rtr_makers.stop(town, hustle, reason: str)`: every customer is unsubscribed (reason `maker_stopped`), `alive = False`, out of `town.hustles`, `owner.hustle = None`, event `hustle_stopped` (agent, reason, trade).

- [ ] **Step 1: Write the failing tests**

```python
def customers(town, hustle, n, cash=100_000):
    from engine.subscriptions import subscribe
    out = [town.add_agent(cash=cash) for _ in range(n)]
    for c in out:
        assert subscribe(town, c, hustle)
    return out


def hours_for_the_week(town):
    from engine import rtr_makers, rtr_owning
    rtr_owning.start_week(town)
    rtr_makers.start_week(town)


def a_week(town):
    """The parts of the week a side hustle lives through, in the week's order."""
    from engine import rtr_makers, rtr_owning
    from engine.household import pay_bills
    hours_for_the_week(town)
    rtr_makers.working_week(town)
    pay_bills(town)
    rtr_owning.after_bills(town)
    rtr_makers.after_bills(town)


def test_customers_find_a_maker_who_is_cheaper_and_a_maker_is_never_their_own_customer():
    from engine.subscriptions import find_provider
    town = quiet_town()
    firm = shop(town, "entertainment", 9_500)
    a, h = maker(town)                                               # sells it at 6,820
    hours_for_the_week(town)
    assert h.hours == 60.0 and h.capacity == 30
    assert find_provider(town, town.add_agent(), "entertainment") is h
    assert find_provider(town, a, "entertainment") is firm


def test_a_week_of_a_side_hustle_hours_then_takings_then_goods():
    town = quiet_town()
    a, h = maker(town)                                               # no money at all
    customers(town, h, 3)
    a_week(town)
    assert h.w_revenue == 20_460 and h.w_goods == 8_100 and a.cash == 12_360
    assert a.spare_hours == 54.0 and (h.q_sold, h.q_could) == (3, 30)
    assert town.ledger.week_out["import"] == 8_100 and town.ledger.week_internal["subscription"] == 20_460


def test_a_maker_who_takes_a_job_leaves_the_newest_unserved_and_unbilled():
    from engine.subscriptions import has_room
    town = quiet_town()
    a, h = maker(town)
    people = customers(town, h, 12, cash=6_820)
    hours_for_the_week(town)
    assert has_room(town, h)
    a.employer, a.role, a.wage = town.add_firm("housing"), "staff", 100_000
    a.employer.staff.append(a)
    a_week(town)                                                     # 20 spare hours: ten customers
    assert h.capacity == 10 and not has_room(town, h)
    assert sorted(h.unserved) == sorted(c.id for c in people[10:])
    assert [c.cash for c in people[10:]] == [6_820, 6_820]           # not served, not billed
    assert h.w_revenue == 68_200 and h.w_goods == 27_000             # and no goods bought for them


def test_a_customer_who_cannot_pay_gets_nothing_and_no_goods_are_bought_for_them():
    town = quiet_town()
    a, h = maker(town)
    customers(town, h, 1, cash=0)
    a_week(town)
    assert h.w_revenue == 0 and h.w_goods == 0 and a.cash == 0


def test_makers_do_not_move_the_yardstick_while_a_firm_sells_the_same_thing():
    from engine.corporate import invent_need
    from engine.subscriptions import cheapest_prices, find_provider
    town = quiet_town()
    firm = shop(town, "entertainment", 9_500)
    a, h = maker(town)
    assert cheapest_prices(town)["entertainment"] == 9_500
    firm.alive = False                                               # the last firm selling it has gone
    assert cheapest_prices(town)["entertainment"] == 6_820
    new = invent_need(town)
    assert new.name not in cheapest_prices(town)
    b, hb = maker(town, new.name)
    hours_for_the_week(town)
    assert cheapest_prices(town)[new.name] == hb.price               # an invented need only a maker sells is on offer
    assert find_provider(town, town.add_agent(), new.name) is hb


def test_a_maker_who_moves_takes_it_with_them_and_one_with_no_home_gives_it_up():
    from engine.household import check_reach, update_agents
    from engine.subscriptions import move_home, subscribe, unsubscribe
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    near, far = block(town, landlord, 5, 6, homes=2), block(town, landlord, 1, 1, homes=2)
    a = tenant(town, near, cash=0)
    a.last_wage = town.cfg.outside_wage
    _, h = maker(town, agent=a)
    c = tenant(town, near)
    hours_for_the_week(town)
    assert h.spot is near and subscribe(town, c, h)
    move_home(town, a, next(u for u in landlord.units if u.spot is far and u.occupant is None), "test")
    hours_for_the_week(town)
    check_reach(town, c)
    assert h.spot is far and "entertainment" not in c.subs           # nine blocks is past a walk
    d = tenant(town, far)
    assert subscribe(town, d, h)
    unsubscribe(town, a, "housing", "evicted")
    update_agents(town)                                              # nothing breaks in between
    hours_for_the_week(town)
    assert a.hustle is None and town.hustles == [] and "entertainment" not in d.subs
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "hustle_stopped"] == ["no home"]
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Before going on, run a small RTR town with one side hustle opened by hand under `run_checked` and ledger every place the selling code reads something of a firm that a `Hustle` lacks (as Task 6 of stage 1b did for `Letting`).
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 3: Starting a side hustle

**Files:**
- Modify: `engine/rtr_makers.py`
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: Tasks 1 and 2; `rtr_owning._spare_cash`, `rtr_owning.homes_of`, `rtr_owning.home_value`, `Bank.person_credit`, `Bank.lend_person`, `Bank.home_credit`, `Bank.lend_home`.
- Produces:
  - `rtr_makers.best_trade(town, agent) -> tuple[str, int] | None`: the trade, of those whose tools they can pay for, where their price most undercuts the cheapest seller within reach of them, with its price; None if they would undercut nobody. For a need: the cheapest live firm or maker of it within their reach from home (all of them where there is no map); with no seller in reach the undercut counts as 1.0. For an hour trade: the cheapest other maker of that trade, or, with none, what an hour of a customer's own is worth (`town.hour_value`); and an hour trade is looked at only while someone could use it (repair: someone else owns a home or a set; `set_building`: someone is building a set; `home_building`: someone is building a home). Ties go to the earlier trade in `trades(town)`.
  - `rtr_makers.pay_tools(town, agent, cost: int) -> bool`: their cash beyond four weeks of bills, then a personal loan, then a loan against their home, for the gap; nothing is borrowed unless the whole cost is covered; the tools are bought from outside (`import`).
  - `rtr_makers.start_hustle(town, agent, trade: str) -> Hustle | None`: pays for the tools, opens it, event `hustle_started` (agent, amount = the tools, trade, price).
  - `rtr_makers.consider_hustles(town)`, called at the end of `rtr_makers.after_bills`: each person with no side hustle, `spare_hours(cfg, agent) >= hustle_min_hours`, and on a map a home, draws once: `hustle_rate_struggling` if `role is None` or `income_estimate() < basket_cost`, otherwise `hustle_rate * agent.risk`; on a hit they start `best_trade`, if there is one.

- [ ] **Step 1: Write the failing tests**

```python
def test_someone_struggling_starts_the_side_hustle_that_undercuts_most():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    a = jobless(town, cash=1_000_000)
    assert best_trade(town, a) == ("entertainment", 6_820)           # 28% under, against 13% for food
    consider_hustles(town)
    assert a.hustle.trade == "entertainment" and a.cash == 1_000_000     # the computer they already have
    started = [(e["amount"], e["data"]["trade"], e["data"]["price"]) for e in town.rec.events
               if e["kind"] == "hustle_started"]
    assert started == [(0, "entertainment", 6_820)]
    consider_hustles(town)
    assert len(town.hustles) == 1                                    # one side hustle each


def test_a_trade_they_cannot_tool_up_for_is_not_theirs():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 6_900)                               # barely undercut: 1%
    shop(town, "food", 40_000)
    rich, poor = jobless(town, cash=1_000_000), jobless(town, cash=0)
    assert best_trade(town, rich) == ("food", 34_650) and best_trade(town, poor) == ("entertainment", 6_820)
    consider_hustles(town)
    assert rich.hustle.trade == "food" and rich.cash == 800_000 and town.ledger.week_out["import"] == 200_000
    assert poor.hustle.trade == "entertainment" and poor.cash == 0


def test_someone_in_work_borrows_for_the_tools():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=1.0")
    shop(town, "entertainment", 6_300)
    shop(town, "food", 40_000)
    low = worker(town, wage=60_000, risk=1.0)                        # an hour of theirs is $15
    assert best_trade(town, low) == ("food", 32_670)
    consider_hustles(town)
    assert low.hustle.trade == "food" and low.loan == 200_000 and low.cash == 0


def test_who_may_start_one():
    from engine.rtr_makers import consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=1.0")
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    busy = jobless(town)
    busy.travel_hours = 51.0                                         # nine spare hours: not enough
    keen, shy = worker(town, cash=5_000_000, risk=1.0), worker(town, cash=5_000_000, risk=0.0)
    consider_hustles(town)
    assert busy.hustle is None and shy.hustle is None                # in work and well enough off: by appetite for risk
    assert keen.hustle.trade == "entertainment" and keen.hustle.price == 8_470


def test_nobody_starts_what_would_undercut_nobody():
    from engine.rtr_makers import best_trade
    town = quiet_town()
    shop(town, "entertainment", 5_000)
    shop(town, "food", 20_000)
    assert best_trade(town, jobless(town, cash=1_000_000)) is None
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 4: The quarter, a maker's income, class and position

**Files:**
- Modify: `engine/rtr_makers.py`, `engine/entities.py` (`Agent.income_estimate`), `engine/household.py` (`classify`, `update_agents`), `engine/town.py` (`rtr_makers.quarter(town)` right after `rtr_owning.quarter(town)`)
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: Tasks 1 to 3; `firmops.set_price` (its event and its blow to customers on a rise serve a side hustle as they serve a firm).
- Produces:
  - `rtr_makers.quarter(town)`: for each side hustle, in order: `profit_week = max(0, (q_revenue - q_goods - q_wages) // quarter_weeks)`; if it has run a whole quarter (`town.week - started >= quarter_weeks`) and `q_sold < hustle_quit_share * q_could`, `stop(town, hustle, "few customers")`; otherwise its price is set again from today's worth (`set_price(town, hustle, new, "quarter")`; it can fall); then the quarter's sums go back to 0. (Part B adds two steps between the price and the reset.)
  - `Agent.income_estimate()` adds `self.hustle.profit_week` when they have a side hustle.
  - `rtr_makers.makes_a_living(agent, basket: int) -> bool`: they have a side hustle and `2 * hustle.profit_week >= basket`. No import of `household` at module level.
  - `household.classify`: someone with no job who makes a living from a side hustle is `working`, checked after staff and before dividends. `update_agents`: such a person has a position (`covered`); the flag it hands `classify` is living on dividends alone, as it is today for everyone else.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_maker_with_under_a_fifth_of_their_customers_for_a_whole_quarter_gives_it_up():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town), maker(town)
    people = customers(town, h, 2)
    town.week = 13
    (h.q_sold, h.q_could), (hb.q_sold, hb.q_could) = (77, 390), (78, 390)
    hc.started, hc.q_could = 5, 390                                  # not yet a whole quarter: not judged
    quarter(town)
    assert a.hustle is None and town.hustles == [hb, hc]
    assert all("entertainment" not in p.subs for p in people)
    assert [(e["data"]["reason"], e["agent"]) for e in town.rec.events if e["kind"] == "hustle_stopped"] == [
        ("few customers", a.id)]
    assert (hb.q_sold, hb.q_could, hb.q_revenue) == (0, 0, 0)        # a new quarter


def test_the_price_is_set_again_each_quarter_and_can_fall():
    from engine.rtr_makers import quarter
    town = quiet_town()
    a, h = maker(town)
    (c,) = customers(town, h, 1)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    a.weeks_out, before = 10, c.security
    quarter(town)
    assert h.price == 5_720 and c.security == before                 # a fall is no blow
    assert [(e["amount"], e["data"]["old"]) for e in town.rec.events if e["kind"] == "price_change"] == [(5_720, 6_820)]


def test_what_a_side_hustle_brings_in_is_income_and_half_a_basket_of_it_is_a_living():
    from engine.household import basket_cost, classify, update_agents
    from engine.rtr_makers import makes_a_living, quarter
    town = quiet_town()
    shop(town, "entertainment", 9_500)                               # so the basket is the plain $880
    a, h = maker(town)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    h.q_revenue, h.q_goods = 1_000_000, 428_000
    quarter(town)
    assert h.profit_week == 44_000 and a.income_estimate() == 44_000
    assert basket_cost(town, a) == 88_000 and makes_a_living(a, 88_000)
    assert classify(town, a) == "working"
    h.profit_week = 43_999
    assert not makes_a_living(a, 88_000) and classify(town, a) == "out"
    h.profit_week = 44_000
    a.security = 0.0
    update_agents(town)
    assert a.klass == "working" and not a.destitute and a.security > 0.0   # a position, as a job is
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass, the WEF pins among them (`classify` and `update_agents` are shared code).
- [ ] **Step 5: Commit** (with approval).

### Task 5: Selling hours: repairers and builders

**Files:**
- Modify: `engine/rtr_makers.py`, `engine/rtr_owning.py` (`keep`, `work`, `_work_on_home`)
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: Tasks 1 to 4; `rtr_owning._spare_cash`.
- Produces:
  - `rtr_makers.cheapest_hour(town, customer, trade: str) -> int | None`: the lowest price of an hour among live makers of that trade, other than the customer, who have hours left this week (`hours - sold > 0`) and, on a map, whose `spot` is within the customer's reach of the customer's home.
  - `rtr_makers.buy_hours(town, customer, trade: str, hours: float, parts_per_hour: float, budget: int) -> float`: buys up to `hours`, cheapest maker first (ties: the lower owner id), each at `hustle.price + parts_per_hour * (1 + maker_margin)` an hour, no more than `budget` in all. For each maker used: the customer pays them (`maker_hours`, into `w_revenue`, onto the customer's `spend_week`); the maker buys that many hours' parts from outside (`import`, into `w_goods`); `sold` rises and the owner's `spare_hours` falls by the hours. Returns the hours done.
  - `rtr_makers.start_week`: an hour trade's `hours` is set as a need trade's is; `working_week` leaves hour trades alone; at the end of `rtr_makers.after_bills` an hour trade adds `q_sold += sold`, `q_could += hours`.
  - `rtr_owning.keep`: for each unit, the hours they are short of this week are bought from a repairer, and all of its hours when the repairer comes to less than doing it themselves (`cheapest_hour + parts_per_hour * (1 + maker_margin) < parts_per_hour + town.hour_value`); with `budget = _spare_cash`. Hours bought count as upkeep done, parts and all; the rest is their own hours and parts as now.
  - `rtr_owning.work` (an appliance set): hours are bought from a `set_building` maker with `parts_per_hour = 0` when the maker's hour is cheaper than their own, or the hours left would take more than `quarter_weeks` times this week's spare hours. `rtr_owning._work_on_home`: the same test against a `home_building` maker, with `parts_per_hour` the home's materials per hour; the bank's share of those materials is drawn by the customer first (`lend_home`, as for their own hours, into `build.borrowed`), then the maker is paid; `build.spent` counts what the customer paid. Their own hours follow, as now.

- [ ] **Step 1: Write the failing tests**

```python
def own_home(town, a):
    unit = town.new_own_unit(town.needs["housing"], a)
    a.unit["housing"], unit.occupant = unit, a
    return unit


def kept(town, unit):
    from engine.production import best_condition
    return unit.cond == best_condition(town.cfg, unit)


def test_an_owner_pays_a_repairer_who_comes_to_less_than_their_own_hours():
    from engine import rtr_owning
    town = quiet_town()
    owner = worker(town, cash=100_000)
    unit = own_home(town, owner)                                     # needs 1.6 hours and $43.20 of parts a week
    m, h = maker(town, "repair")                                     # an hour of theirs at 1,750: 1,925 with the tenth
    hours_for_the_week(town)
    rtr_owning.keep(town, owner)
    assert owner.cash == 100_000 - 7_832 and owner.spare_hours == 20.0   # (4,320 + 2,800) x 1.1, and no hour of theirs
    assert m.cash == 7_832 - 4_320 and m.spare_hours == pytest.approx(58.4) and h.sold == pytest.approx(1.6)
    assert town.ledger.week_internal["maker_hours"] == 7_832 and town.ledger.week_out["import"] == 4_320
    assert kept(town, unit) and unit.age == 1


def test_a_dearer_repairer_is_used_only_by_someone_short_of_hours_who_has_the_money():
    from engine import rtr_owning
    town = quiet_town()
    has_time, no_time, no_money = worker(town, cash=100_000), worker(town, cash=100_000), worker(town, cash=0)
    for a in (has_time, no_time, no_money):
        own_home(town, a)
    m, h = maker(town, "repair", agent=worker(town))                 # in work: 2,750 an hour, dearer than their own 2,500
    hours_for_the_week(town)
    no_time.spare_hours = no_money.spare_hours = 0.0
    for a in (has_time, no_time, no_money):
        rtr_owning.keep(town, a)
    assert has_time.cash == 100_000 - 4_320 and has_time.spare_hours == pytest.approx(18.4)
    assert no_time.cash == 100_000 - 9_152 and h.sold == pytest.approx(1.6)      # (4,320 + 4,000) x 1.1
    assert kept(town, has_time.unit["housing"]) and kept(town, no_time.unit["housing"])
    assert no_money.cash == 0 and not kept(town, no_money.unit["housing"])       # it wears


def test_a_repairer_sells_only_the_hours_their_own_home_leaves_them():
    from engine import rtr_makers, rtr_owning
    town = quiet_town()
    m, h = maker(town, "repair", agent=worker(town, cash=1_000_000))
    mine = own_home(town, m)                                         # 1.6 of their 20 hours are spoken for
    hours_for_the_week(town)
    assert h.hours == pytest.approx(18.4)
    busy = worker(town, cash=10_000_000)
    busy.spare_hours = 0.0
    assert rtr_makers.buy_hours(town, busy, "repair", 30.0, 0.0, 10_000_000) == pytest.approx(18.4)
    assert m.spare_hours == pytest.approx(1.6) and busy.cash == 10_000_000 - 50_600
    rtr_owning.keep(town, m)
    assert kept(town, mine) and m.spare_hours == pytest.approx(0.0)


def test_a_builder_is_paid_for_hours_and_materials_and_the_bank_still_lends_on_the_materials():
    from engine import rtr_makers, rtr_owning
    from test_places import tenant
    from test_rtr import _tenant_with_a_job
    town, a, landlord = _tenant_with_a_job(5_000_000, *NOBODY_STARTS)
    rtr_owning.consider_building(town, a)
    assert a.build is not None
    b = tenant(town, a.unit["housing"].spot, cash=0)                 # the builder lives on the same block
    b.last_wage, b.weeks_out = town.cfg.outside_wage, 10             # an hour at the floor
    _, h = maker(town, "home_building", agent=b)
    hours_for_the_week(town)
    a.spare_hours, per_hour = 20.0, 4_500                            # 500 units at $108 over 1,200 hours
    assert h.price == round(1.1 * rtr_makers.hour_worth(town, b))
    rtr_owning.work(town, a)
    paid = round(60 * (h.price + per_hour * 1.1))
    assert a.build.hours_left == pytest.approx(1_200 - 80)           # sixty bought, twenty of their own
    assert town.ledger.week_internal["maker_hours"] == paid and b.cash == paid - 60 * per_hour
    assert b.spare_hours == pytest.approx(0.0) and a.build.borrowed == a.home_loan
    assert a.home_loan == round(0.8 * 80 * per_hour)                 # four fifths of the materials, whoever did the hours


def test_a_set_builder_is_paid_for_hours_only():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building")                               # 1,925 an hour
    hours_for_the_week(town)
    a.spare_hours, cash = 0.0, a.cash                                # twenty hours they do not have
    rtr_owning.work(town, a)
    assert rtr_owning.owns(a, "appliances") and a.cash == cash - 38_500 and m.cash == 38_500
```

(The builder test fixes what must hold. The tenant's wage in `_tenant_with_a_job` sets the loan the bank will give: if the bank's limit stops the draw short of four fifths, raise the wage through the helper's overrides and ledger it; do not weaken the assertion.)

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** A stage 1 town with no makers must keep every figure its tests pin: with `town.hustles` empty, `keep`, `work` and `_work_on_home` do what they did.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 6: The record, the weekly checks, and whole towns (end of Part A)

**Files:**
- Modify: `engine/metrics.py`, `tests/test_town_invariants.py`, `tests/test_rtr_2.py`
- Scratch (not in the repo): `mutate.py`, a full-town script

**Interfaces:**
- Produces:
  - Weekly measures, town scope, RTR only: `makers` (live side hustles), `maker_customers` (the loads of need trades), `maker_hours_sold` (hours sold this week by hour trades), `maker_revenue` (the week's takings of all of them).
  - `check_week` (RTR): every side hustle in `town.hustles` is alive and its owner is in town with `owner.hustle is hustle`; nobody has a side hustle that is not in the list; each customer in `hustle.subs` has `subs[need] is hustle`, and nobody is their own customer; `hustle.extra` is the bigger plans of its customers; `0 <= sold <= hours + 1e-6`; an hour trade has no `subs`; on a map a live side hustle has a `spot` that is its owner's home.

- [ ] **Step 1: Write the failing tests**: the measures on a hand-made town (two makers, three customers, 1.6 hours sold); a broken town for each new check (a side hustle whose owner does not know it; a customer the side hustle does not list) that `check_week` must name.
- [ ] **Step 2: Whole towns.** A module fixture as in stage 1b: two small map towns and one with no map (`population_cap=200`, fourteen years, `stop_on_failure=false`, RTR), run once under `run_checked`, with `_reached(town)` listing which rules each town met: a side hustle started in a need trade and in an hour trade; a customer signed up to a maker; a maker stopped for few customers; a maker's price changed; hours sold. Pick seeds that between them reach every one; a rule no seed reaches in a small town is said so in the ledger, with the unit test that covers it.
- [ ] **Step 3: Break the rules.** In a scratch copy, break each rule of Tasks 1 to 5 one at a time (every number in "Global Constraints", every `if` in `rtr_makers.py`, each gated edit elsewhere). Every break must fail a test in `tests/test_rtr_2.py`; add tests until it does. Ledger the count.
- [ ] **Step 4: By hand.** Old-rules seed 74 (`08251209eb136522`, 180,377 events). Three full RTR towns (seeds 1, 2, 3) under the weekly checks: the year each failed, and how many makers, customers of makers and hours sold at year 10 and at the end, beside the stage 1b figures. Forty full RTR towns from `rtr/` (`python batch.py stage2a --seeds 1-40`): none ends in an error. Ledger all of it; none of it is a finding.
- [ ] **Step 5: Run the whole suite.** Expected: all pass.
- [ ] **Step 6: Commit** (with approval). Part A ends here: show Jason before Part B.

---

## Part B: ideas, and side hustles that grow

### Task 7: Ideas

**Files:**
- Modify: `engine/rtr_makers.py`, `engine/corporate.py` (`choose_venture`)
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: `corporate.invent_need(town)` (the WEF world's own way of making a need); Task 3's `start_hustle`.
- Produces:
  - `rtr_makers.ideas(town)`, called in `rtr_makers.after_bills` before `consider_hustles`: each person with spare hours left draws once, with chance `idea_rate * spare_hours / idea_hours`; on a hit `invent_need(town)` makes the need, its name goes into `town.new_ideas`, `town.ideas_total += 1`, event `idea` (agent, need); the creator starts it as a side hustle at once if call 11 holds. Nobody is paid for the idea.
  - `choose_venture`: in an RTR town a founder never invents (`not cfg.rtr` before the draw, so a WEF town draws as it did).
  - Weekly measure `ideas` (`town.ideas_total`), RTR only.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_idea_comes_from_spare_time_and_its_creator_may_start_it_at_once():
    from engine import rtr_makers
    from engine.rtr_makers import ideas, trades
    town = rtr_town("idea_rate=1.0")
    a, idle = jobless(town, cash=60_000), jobless(town, cash=0)
    a.spare_hours, idle.spare_hours = 20.0, 0.0                      # a full chance, and none
    ideas(town)
    (new,) = [s for s in town.needs.values() if s.invented]
    assert a.hustle.trade == new.name and a.cash == 10_000           # $500 of tools
    assert idle.hustle is None and town.ideas_total == 1
    assert [(e["agent"], e["data"]["need"]) for e in town.rec.events if e["kind"] == "idea"] == [(a.id, new.name)]
    assert new.name not in [t for t, _ in trades(town)]              # open to everyone else from next week
    rtr_makers.start_week(town)
    assert new.name in [t for t, _ in trades(town)]


def test_the_chance_of_an_idea_grows_with_the_spare_hours_left():
    from engine.rtr_makers import ideas
    town = rtr_town("idea_rate=0.5")
    a, b = jobless(town), jobless(town)
    a.spare_hours, b.spare_hours = 40.0, 0.0
    ideas(town)
    assert town.ideas_total == 1                                     # 0.5 for each twenty hours: certain at forty


def test_founders_of_firms_do_not_invent_in_the_rtr_world():
    from engine.corporate import choose_venture
    for world, invented in (("rtr", 0), ("wef", 1)):
        town = rtr_town("invent_prob=1.0", f"world={world}")
        shop(town, "food", 40_000)
        choose_venture(town, 50_000_000)
        assert sum(1 for s in town.needs.values() if s.invented) == invented, world
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 8: A small business: the loan on profit, and staff

**Files:**
- Modify: `engine/entities.py` (`Hustle`: `business = False`, `staff = []`, `execs = []`, `ceo = None`, `accrual = {}`, `wage = 0`, `loan = 0`, `loan_pay = 0`, `loan_missed = 0`), `engine/bank.py`, `engine/rtr_makers.py`, `engine/town.py` (`rtr_makers.hire_staff(town)` right after `labour_market(town)`; `rtr_makers.pay_staff(town)` right after `payroll(town)`; both under `if cfg.rtr`)
- Test: `tests/test_rtr_2.py`, `tests/test_town_invariants.py`

**Interfaces:**
- Consumes: `labour.hire`, `labour.separate`, `labour.can_get_to`; Task 4's `quarter`.
- Produces:
  - `Bank.lend_hustle(hustle, amount: int) -> int`: `loan` in from outside to the owner; `hustle.loan`, `hustle.loan_pay = ceil(loan / hustle_loan_term_weeks)`; event `hustle_loan` (agent, amount). `Bank.service_hustle(hustle) -> bool`: a week's interest at `firm_rate` and the instalment, from the owner's cash; a missed week adds the unpaid interest and `loan_missed += 1`, as `service_home` does.
  - `rtr_makers.ask_bank(town, hustle) -> bool`, called from `quarter` after the price is set: a side hustle that is not yet a business, has run a whole quarter and was full for it (`q_could > 0 and q_sold >= hustle_full_share * q_could`), whose owner the bank is not refusing, borrows `int(hustle_loan_weeks * profit_week)` if that is at least four weeks of `town.typical_wage()`; then `business = True`.
  - `rtr_makers.hire_staff(town)`: for each business, `wage = town.typical_wage()` (and its staff's pay with it); the hours it needs are `(load + waiting) * hours_per_customer` for a need trade, and for an hour trade last week's `sold`, plus `job_hours` if it sold every hour it had; staff wanted is `ceil(max(0, needed - the owner's hours for it) / job_hours)`; extra staff are let go last hired first (`laid_off`); vacancies are filled from residents with no job who are not owners by class and not the owner of it, lowest id first, who would take the wage (the `labour_market` reservation) and can get to its `spot`.
  - `rtr_makers.start_week`: a business's `hours` also counts `job_hours` for each of its staff.
  - `rtr_makers.pay_staff(town)`: each business pays its staff the wage from the owner's cash (`wage`, onto each worker's `income_week`, into `w_wages` and `q_wages`); while it cannot pay them all it lets go the last hired (`unpaid`).
  - Price: a business with staff costs its hours at the higher of the owner's worth and the going hourly wage.
  - `rtr_makers.after_bills` services each loan; at `firm_missed_limit` missed in a row, `stop(town, hustle, "loan")`. `stop` now also lets the staff go (`wound_up`), and settles a loan still owed by call 8 (`loan_principal` for what cash they have, `Bank._write_off` for the rest, `credit_block_until`, `shock_default`).
  - Weekly measures: `small_businesses`, `maker_staff`, `maker_loans`. `check_week`: only a business has staff or a loan; each of its staff has it as `employer` with role `staff`; `loan >= 0`.

- [ ] **Step 1: Write the failing tests**

```python
def full_quarter(town, h, profit_week):
    town.week, h.q_sold, h.q_could = 13, 390, 390
    h.q_revenue, h.q_goods = 13 * profit_week, 0


def test_a_maker_full_for_a_quarter_borrows_on_the_profit_and_becomes_a_small_business():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town), maker(town)
    full_quarter(town, h, 20_000)
    full_quarter(town, hb, 15_000)                                   # 26 weeks of it is under four weeks' wages
    full_quarter(town, hc, 20_000)
    hc.q_sold = 370                                                  # not full: under 95%
    quarter(town)
    assert h.business and (h.loan, h.loan_pay, a.cash) == (520_000, 2_000, 520_000)
    assert not hb.business and b.cash == 0 and not hc.business
    assert [(e["agent"], e["amount"]) for e in town.rec.events if e["kind"] == "hustle_loan"] == [(a.id, 520_000)]
    assert town.ledger.week_in["loan"] == 520_000


def test_a_small_business_takes_on_the_staff_its_customers_need_and_serves_more():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town)
    h.business = True
    boss = jobless(town)
    boss.klass = "owner"                                             # lives on dividends: not looking for work
    people = customers(town, h, 30)
    h.turned_away = {n: True for n in range(900, 920)}               # twenty more wanted in last week
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)                                      # 100 hours wanted, 60 of their own: one worker
    hand = people[0]                                                 # the first resident with no job
    assert h.staff == [hand] and hand.employer is h and hand.role == "staff" and hand.wage == 100_000
    hours_for_the_week(town)
    assert h.hours == 100.0 and h.capacity == 50


def test_a_small_business_that_cannot_pay_everyone_lets_the_last_hired_go():
    from engine.rtr_makers import pay_staff
    town = quiet_town()
    a, h = maker(town, cash=150_000)
    h.business, h.wage = True, 100_000
    first, last = jobless(town), jobless(town)
    for w in (first, last):
        w.employer, w.role, w.wage = h, "staff", 100_000
        h.staff.append(w)
    pay_staff(town)
    assert h.staff == [first] and last.role is None
    assert (a.cash, first.cash, first.income_week, last.cash) == (50_000, 100_000, 100_000, 0)
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "layoff"] == ["unpaid"]


def test_the_loan_is_paid_weekly_and_four_missed_payments_end_the_business():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town)
    (c,) = customers(town, h, 1)
    h.business = True
    town.bank.lend_hustle(h, 520_000)
    town.ledger.pay(a, c, 517_400, "gift")                           # all but one week's payment is gone
    assert town.bank.service_hustle(h) and (h.loan, a.cash) == (518_000, 0)      # $6 of interest, $20 off the loan
    for _ in range(4):
        rtr_makers.after_bills(town)
    assert a.hustle is None and "entertainment" not in c.subs and town.hustles == []
    assert town.bank.writeoffs_total >= 518_000 and a.credit_block_until == town.week + town.cfg.default_block_weeks
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "hustle_stopped"] == ["loan"]
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Run a small RTR town with one business made by hand under `run_checked` and ledger every place the jobs code reads something of a firm that a `Hustle` lacks.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 9: Becoming a company

**Files:**
- Modify: `engine/rtr_makers.py`, `engine/corporate.py` (`resident_founders`: in an RTR town someone with a side hustle is left to this rule, tested before any draw)
- Test: `tests/test_rtr_2.py`

**Interfaces:**
- Consumes: `corporate.found_firm`, `production.unit_cost`, `subscriptions.subscribe`, `unsubscribe`, `set_plan`, `labour.hire`.
- Produces:
  - `rtr_makers.become_company(town, hustle) -> Firm | None`, called from `quarter` after `ask_bank`: for a need trade whose owner has `int((cash - loan) * founder_invest_share) >= flow_entry_capital`, with chance `resident_founder_rate * owner.risk`. The loan is repaid in full; the firm is founded by `found_firm(town, owner, capital, spec, price=..., near=hustle.spot)` at the higher of the maker's price and `round(unit_cost(cfg, spec, town.typical_wage()) * (1 + cost_floor_markup))`; if no spot can be had nothing changes. Then every customer moves to the firm with their plan (`sub_end` and `sub_start`, reason `company`), every worker is taken on by the firm (`hire`, source `company`, with no layoff), the side hustle is closed without `stop`'s releases, and event `maker_company` (agent, firm, amount = the capital, qty = the customers).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_maker_with_the_capital_founds_a_company_and_brings_customers_and_staff():
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0")
    a, h = maker(town, cash=22_000_000, risk=1.0)
    people = customers(town, h, 3)
    hand = jobless(town)
    h.business, hand.employer, hand.role, hand.wage = True, h, "staff", 100_000
    h.staff.append(hand)
    town.week, h.q_sold, h.q_could = 13, 390, 390
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert a.hustle is None and town.hustles == [] and firm.ceo is a and a.role == "ceo"
    assert all(p.subs["entertainment"] is firm for p in people) and len(firm.subs) == 3 and h.subs == {}
    assert hand.employer is firm and firm.staff == [hand] and h.staff == []
    assert firm.price == 8_610                                       # the entrant's floor, above the maker's own price
    assert [(e["agent"], e["firm"], e["qty"]) for e in town.rec.events if e["kind"] == "maker_company"] == [
        (a.id, firm.id, 3)]
    assert [e["kind"] for e in town.rec.events if e["kind"] in ("layoff", "hustle_stopped")] == []


def test_who_does_not_become_a_company():
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0")
    short, _ = maker(town, cash=21_000_000, risk=1.0)                # 70% of it is under $150,000
    owing, ho = maker(town, cash=22_000_000, risk=1.0)
    ho.business, ho.loan, ho.loan_pay = True, 1_000_000, 3_847       # after the loan: 70% of $210,000
    repairer, _ = maker(town, "repair", cash=22_000_000, risk=1.0)   # no firm sells hours
    timid, _ = maker(town, cash=22_000_000, risk=0.0)
    town.week = 13
    for h in town.hustles:
        h.q_sold, h.q_could = 390, 390
    quarter(town)
    assert town.firms_for("entertainment") == [] and len(town.hustles) == 4
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 10: Whole towns, the review, and the documents (end of Part B)

**Files:**
- Modify: `tests/test_rtr_2.py`, `rtr/README.md`, `README.md` (the count of tests; `engine/rtr_makers.py` in the layout table), `docs/superpowers/specs/2026-11-16-rtr-world-design.md` ("Built so far"), the ledger
- Scratch: `mutate.py`, the full-town script

- [ ] **Step 1: Whole towns.** Extend the fixture of Task 6 and `_reached`: an idea; a creator starting their idea; a loan on profit; a business hiring; a business paying wages. Raise `idea_rate` and `hustle_rate` in the small towns if the default rates never reach them in fourteen years, and say so in the ledger. A company is too rare for a small town (it needs $214,000 in one person's hands): its unit tests stand for it, and the ledger says so.
- [ ] **Step 2: A town where everything stops.** One small RTR town run under `run_checked` in which every landlord and shop is closed by hand at year five: makers, businesses, staff and loans must still balance every week to the end.
- [ ] **Step 3: Break the rules** of Tasks 7 to 9, as in Task 6. Ledger the count.
- [ ] **Step 4: By hand.** As Task 6, step 4: old-rules seed 74; three full RTR towns under the weekly checks, with the makers, businesses, ideas and companies each saw; forty full RTR towns, none ending in an error.
- [ ] **Step 5: Fresh review** of the whole branch (superpowers:requesting-code-review, most capable model), with the Review Focus above and the ledger's rulings. One fix pass, each fix test first.
- [ ] **Step 6: Documents.** `rtr/README.md`: a section "Stage 2: makers" (what a side hustle is, the trades, how one starts, stops and grows, ideas, the new measures and events, what the towns did, untuned). The spec's "Built so far". No em dashes.
- [ ] **Step 7: Run the whole suite.** Expected: all pass.
- [ ] **Step 8: Commit** (with approval).

## Where the build departed from this plan (added 18 November, after Part B was built)

Task 8 was built four ways different from what is written above, each after whole towns showed the
written rule did something plainly wrong. The reasons, the figures and the tests are in the ledger
(`docs/build-ledger-rtr-stage2-2026-11-18.md`, "What the small towns showed" and "What the first full
town showed").

- **Price.** Not "a business with staff costs its hours at the higher of the owner's worth and the going
  hourly wage", but: a small business prices its hour at the going wage from the day it borrows, staff or
  no staff, and taking someone on does not move its price.
- **Staff.** Not a worker for any hours over, but: a worker for every whole week of hours beyond the
  owner's, and one more for the hours left over only if that work would pay their wage at the business's
  price; one it already has for those hours is kept while they pay half their wage (`staff_wanted`).
- **Borrowing.** A maker asks the bank only when `staff_wanted`, at the price they would charge as a
  business, is at least 1.
- **Who is waiting.** `hustle.waiting` is not everyone turned away last week but those of them who would
  have bought (`would_have_bought`).

- **The till.** Not "property `cash` that reads and writes `owner.cash`" (Task 1), but: a side hustle has a
  till of its own for the week; goods, then wages, are paid out of it and its owner draws the rest. Staff
  are paid there, after the customers have paid, not right after the town's payroll.

Also: founders of firms stop inventing in an RTR town only while `idea_rate` is above 0 (Task 7), so that
an RTR town with stage 2 switched off is still the stage 1 town; and the pin for that is on the town's
events alone, not on its whole record.

The fresh review then changed these calls of this plan (the ledger's last section has each, with the
reviewer's figures): **call 2** (the yardstick now counts a maker with room); **call 3** withdrawn (no home
is no bar to a side hustle); **call 6** (their own hours first, then a maker's); **call 8** (the loan stays
in the business); and a trade that sells hours is taken up only with work in sight for a fifth of their
hours, and never becomes a small business.

## Not in this stage

- The pages (the town view marking people with a side hustle, charts of the new measures): stage 3.
- A maker choosing not to take a job that pays less than the side hustle: nothing in the design says they would; watch for it in the whole towns and put it to Jason if makers are pulled out of thriving side hustles.
- The eleven minors deferred from stage 1b (in its ledger). The one that touches this stage, that nothing checks an owner of many homes has the hours to keep them, is met in part here: they can now pay a repairer.
