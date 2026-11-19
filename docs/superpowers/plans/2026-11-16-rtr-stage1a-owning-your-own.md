# RTR stage 1a: building and owning your own. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In a town run with `world=rtr`, a resident can build and own an appliance set and a home, keep them up with their own time and parts, borrow against the home, and lose it to foreclosure; a town run with `world=wef` is the same town as before, record for record.

**Architecture:** One new module, `wefworld/owning.py`, holds everything a person does as an owner; the bank gains the loan against a home; `Town.step` calls into `owning` only when `cfg.rtr`. Privately owned homes stand on blocks of their own kind (`plots`) and never in a firm's `units`, so the renting machinery (subscriptions, landlords, `find_home`) is not rewritten. Stage 1b (a separate plan) adds buying from landlords, selling, small landlords and landlord firms buying foreclosed homes.

**Tech Stack:** Python 3.12, standard library only; pytest (`python3 -m pytest -rN`; `-q` is set in `pyproject.toml`).

**Spec:** `docs/superpowers/specs/2026-11-16-rtr-world-design.md` (sections 3, 5, 6, 7, 10, 11, 12). Jason approved it on 16 November 2026.

## Global Constraints

- `world` is `wef` by default. With `wef`, no line of this plan changes any town: every existing test passes untouched, and the two new WEF pins of Task 1 hold after every task.
- Every dollar moves through `Ledger.pay`. Parts bought from outside are kind `import`; a loan drawn is `loan`; payments to the bank are `loan_principal`, `loan_interest`; a foreclosed home's buyer pays the bank as `loan_recovery`. Nothing is created or destroyed outside those.
- Money is whole cents; time is weeks; hours are floats. One worker-week is `job_hours` (40.0) hours.
- Numbers, copied from the spec: `free_hours` 60.0; `job_hours` 40.0; `mortgage_ltv` 0.80; `mortgage_weeks` 1040; `mortgage_income_share` 0.30; the home loan's rate is `firm_rate`; missed payments before foreclosure `grace_weeks` (4); a foreclosed home's asking price falls `foreclosed_price_drop` (0.05) each quarter unsold; the reluctance to change is `switch_friction` (0.05); an hour of one's own time is `town.hour_value` cents.
- An appliance set: `build_goods` (40) units at the appliances `import_price`, `build_labour` (0.5) worker-weeks, so 20 hours. A home: 500 units at the housing `import_price`, 30 worker-weeks, so 1,200 hours. Upkeep is `production.upkeep_need(cfg, unit)`: its labour times `job_hours` is hours, its goods are bought at the need's `import_price`.
- New weekly measures and new event kinds are written only when `cfg.rtr`, so WEF fingerprints do not move.
- No em dashes in any text written to docs, comments or pages.
- Every (C) call made while building goes in `docs/build-ledger-rtr-stage1a-2026-11-16.md` as `Ruling: <what> ; <why> ; <cost if wrong>`.

## Review Focus

1. An owner who loses their job half way through building a home: the build stops drawing the loan, the plot stays theirs, and nothing is foreclosed that has no loan on it.
2. Land runs out while plots are reserved for builds in progress: a reserved plot is never handed to anyone else, and a builder with a reserved plot finishes.
3. A foreclosed home nobody buys for years: its asking price falls 5% a quarter, never below 1 cent, and the bank's loss is written off exactly once, when it sells.
4. Someone who rents a set and builds their own: for the weeks of the build they hold the rented one, and they never hold two or none.
5. `world=rtr` with no map (`map_width=0`): homes are built with no plot and no block, and every weekly check still holds.

---

### Task 1: The `world` dial and the proof that WEF towns are unchanged

**Files:**
- Modify: `wefworld/config.py`
- Create: `tests/test_rtr.py`

**Interfaces:**
- Produces: `Config.world: str = "wef"`; `CHOICES["world"] = ("wef", "rtr")`; property `Config.rtr -> bool`; dials `free_hours: float = 60.0`, `job_hours: float = 40.0`, `mortgage_ltv: float = 0.80`, `mortgage_weeks: int = 1040`, `mortgage_income_share: float = 0.30`, `foreclosed_price_drop: float = 0.05`; `configs/rtr.json` holding `{"world": "rtr"}`.

- [ ] **Step 1: Record the WEF pins on the code as it stands.** Run, before any edit:

```bash
PYTHONPATH=. python3 - <<'EOF'
import sys; sys.path.insert(0, "tests")
from conftest import what_happened
from wefworld.config import load_config
from wefworld.town import Town
for over in (["seed=1", "stop_on_failure=false"], ["seed=5", "stop_on_failure=false", "founder_arrival_rate=0.25", "resident_founder_rate=0.2"]):
    town = Town(load_config(None, over))
    for _ in range(6 * 52):
        town.step()
    print(over, what_happened(town))
EOF
```

Write the two results into the build ledger and into `tests/test_rtr.py` as `WEF_PINS`.

- [ ] **Step 2: Write the failing tests**

```python
def test_the_world_is_wef_unless_asked_and_only_two_worlds_exist():
    assert load_config().world == "wef" and not load_config().rtr
    assert load_config("configs/rtr.json").rtr and load_config(None, ["world=rtr"]).rtr
    with pytest.raises(ValueError):
        load_config(None, ["world=mars"])


def test_the_rtr_dials_have_the_designs_values():
    cfg = load_config()
    assert (cfg.free_hours, cfg.job_hours) == (60.0, 40.0)
    assert (cfg.mortgage_ltv, cfg.mortgage_weeks, cfg.mortgage_income_share) == (0.80, 1040, 0.30)
    assert cfg.foreclosed_price_drop == 0.05


@pytest.mark.parametrize("overrides, record", WEF_PINS)
def test_a_wef_town_is_the_town_it_was_before_rtr_was_built(overrides, record):
    town = Town(load_config(None, overrides))
    for _ in range(6 * 52):
        town.step()
    assert what_happened(town) == record
```

- [ ] **Step 3: Run them.** `python3 -m pytest -rN tests/test_rtr.py`. Expected: the first two FAIL (no `world`), the pins PASS.
- [ ] **Step 4: Add the dials, `CHOICES`, the `rtr` property and `configs/rtr.json`.**
- [ ] **Step 5: Run the whole suite.** `python3 -m pytest -rN`. Expected: all pass (712 plus the new ones).
- [ ] **Step 6: Commit** (only with Jason's approval; otherwise leave staged and go on).

### Task 2: Spare time

**Files:**
- Create: `wefworld/owning.py`
- Modify: `wefworld/entities.py` (Agent slot `spare_hours`, default 0.0)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Produces: `owning.spare_hours(cfg, agent) -> float`: `free_hours`, less `job_hours` if `agent.role is not None`, less `agent.travel_hours`, never below 0. `owning.start_week(town)` sets `agent.spare_hours` for everyone (used by later tasks as the week's budget of hours).

- [ ] **Step 1: Write the failing test**

```python
def test_spare_time_is_what_a_job_and_the_road_leave():
    town = rtr_town()
    a = town.add_agent()
    assert spare_hours(town.cfg, a) == 60.0
    a.role, a.travel_hours = "staff", 6.5
    assert spare_hours(town.cfg, a) == 13.5
    a.travel_hours = 30.0
    assert spare_hours(town.cfg, a) == 0.0
```

(`rtr_town(*overrides)` is a helper in `tests/test_rtr.py`: `empty_town("world=rtr", *overrides)`.)

- [ ] **Step 2: Run it.** Expected: FAIL, `owning` does not exist.
- [ ] **Step 3: Implement `spare_hours` and `start_week`.**
- [ ] **Step 4: Run it.** Expected: PASS.
- [ ] **Step 5: Commit** (with approval).

### Task 3: Things a person owns, and plots to stand homes on

**Files:**
- Modify: `wefworld/entities.py` (Unit slot `owner`, default None; Agent slots `home_loan`, `home_pay`, `home_missed`, all 0), `wefworld/places.py` (Spot slots `private_units` list, `plots_reserved` int; kind `"plots"`), `wefworld/town.py` (`new_own_unit`), `wefworld/metrics.py` (homeless), `wefworld/owning.py`
- Test: `tests/test_rtr.py`, `tests/test_town_invariants.py`

**Interfaces:**
- Produces:
  - `Town.new_own_unit(spec, owner) -> Unit`: a unit with `firm=None`, `owner=owner`, in no firm's `units`; kept in `town.own_units` (list).
  - `owning.owns(agent, need: str) -> bool`: `agent.unit.get(need)` exists and its `owner is agent`.
  - `owning.housed(agent) -> bool`: `"housing" in agent.subs or owns(agent, "housing")`.
  - `places.take_plot(town) -> Spot | None`: a `plots` block with `len(private_units) + plots_reserved < homes_per_spot`, the best `access` first; else, while a block is empty, the empty block with the best access becomes kind `plots` (owner and user None; `land_scarce` is noted exactly as `take_spot` notes it); else None. It adds 1 to `plots_reserved`. With no map it returns None and callers build with no spot.
  - `places.place_own_unit(spot, unit)`: reserved minus 1, appended to `private_units`, `unit.spot = spot`.
- Consumes: nothing new.
- `metrics`: homeless counts `not housed(a)` (the same number while nobody owns).
- `tests/test_town_invariants.py::check_places`: a `plots` block has no owner, no user and no `units`; `len(private_units) + plots_reserved <= homes_per_spot`; every private unit's `spot` is its block and its `firm` is None. `check_week`: every unit in `agent.unit` is either rented from the firm in `agent.subs` or owned by the agent.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_owned_unit_belongs_to_no_firm():
    town = rtr_town()
    a = town.add_agent()
    unit = town.new_own_unit(town.needs["appliances"], a)
    a.unit["appliances"] = unit
    assert unit.firm is None and unit.owner is a and owns(a, "appliances")
    assert all(unit not in f.units for f in town.firms) and unit in town.own_units
    assert not housed(a)


def test_plots_fill_a_block_of_eight_then_take_another_and_stop_when_land_is_gone():
    town = map_rtr_town("map_width=3", "map_height=3")
    taken = [take_plot(town) for _ in range(9)]
    assert len({s.id for s in taken[:8]}) == 1 and taken[8].id != taken[0].id
    assert taken[0].kind == "plots" and taken[0].plots_reserved == 8
    for spot in town.map.spots:                      # the rest of the land goes to someone else
        if spot.kind is None:
            spot.kind = "service"
    assert [take_plot(town) for _ in range(7)].count(None) == 0      # seven plots left on the second block
    assert take_plot(town) is None


def test_with_no_map_there_are_no_plots():
    assert take_plot(rtr_town()) is None
```

(`map_rtr_town(*overrides)`: `map_town("world=rtr", *overrides)` from `tests/conftest.py`.)

- [ ] **Step 2: Run them.** Expected: FAIL (`new_own_unit`, `take_plot` missing).
- [ ] **Step 3: Implement the slots, `new_own_unit`, `owns`, `housed`, `take_plot`, `place_own_unit`, the homeless measure, and the two invariant checks.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass, the WEF pins among them.
- [ ] **Step 5: Commit** (with approval).

### Task 4: Owning an appliance set

**Files:**
- Modify: `wefworld/owning.py`, `wefworld/household.py` (`dues`, `pay_bills`, `_review_need`), `wefworld/town.py` (call `owning` in `step` when `cfg.rtr`), `wefworld/entities.py` (Agent slot `set_hours_left`: None, or the hours still to work on a set of their own)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Consumes: `spare_hours`, `owns`, `Town.new_own_unit`, `production.upkeep_need`, `production.update_condition`, `production.best_condition`.
- Produces:
  - `owning.parts_price(town, need: str) -> int`: the need's `import_price`.
  - `owning.own_cost_week(town, agent, need: str) -> int`: what owning costs a week, for the comparison with rent: build goods at `parts_price` spread over `life_years`, plus a new unit's upkeep goods at `parts_price`, plus the hours of both at `town.hour_value`.
  - `owning.consider_own_set(town, agent)`: someone who rents a set and has no build under way starts one when `own_cost_week < price_paid(agent, "appliances") * (1 - switch_friction)` and they can pay for the parts (their cash, then `bank.lend_person` for the gap); the parts are bought at once (`import`); `set_hours_left = 20.0`; event `own_started` (need, amount).
  - `owning.work(town, agent)`: spends `agent.spare_hours` in the spec's order (upkeep first, then the build). When the set's hours reach 0: the unit is made (`new_own_unit`), the rented one is given back (`unsubscribe(..., "owns")`), `agent.unit["appliances"]` is theirs; event `own_built`.
  - `owning.keep(town, agent)`: each owned unit ages a week; its upkeep needs `upkeep_need` hours and parts; `done` is the lesser of the share of hours they had and the share of parts they could pay for (`import`); `update_condition(cfg, unit, done)`. A unit whose `best_condition` is under `replace_below` is rebuilt as a new build (parts again, hours again), the old one used meanwhile.
  - `household.dues`: an owner's upkeep parts are not a bill (they are bought in `keep`); nothing is due to any firm for an owned need. `pay_bills`: `agent.met[need] = True` for an owned need. `_review_need`: returns at once for a need the agent owns.
  - `Town.step`, when `cfg.rtr`: `owning.start_week(town)` before step 1; `owning.work` and `owning.keep` for every agent after `pay_bills`; `owning.consider_own_set` for every agent at a quarter end before `review_subscriptions`.

- [ ] **Step 1: Write the failing tests**

```python
def _renter_of_a_set(cash=1_000_000):
    town = rtr_town("switch_prob=0.0")
    firm = town.add_firm("appliances")
    town.new_unit(firm)
    a = town.add_agent(cash=cash)
    assert subscribe(town, a, firm)
    return town, a, firm


def test_someone_renting_a_set_builds_their_own_when_it_is_clearly_cheaper():
    town, a, firm = _renter_of_a_set()
    assert own_cost_week(town, a, "appliances") < firm.price * 0.95      # about $25 a week, their hours counted, against $55
    consider_own_set(town, a)
    assert a.set_hours_left == 20.0 and a.cash == 1_000_000 - 40 * 13_500
    assert town.ledger.week_out == {"import": 540_000}
    a.spare_hours = 12.0
    work(town, a)
    assert a.set_hours_left == 8.0 and not owns(a, "appliances")           # still using the rented one
    a.spare_hours = 12.0
    work(town, a)
    assert owns(a, "appliances") and "appliances" not in a.subs and firm.subs == {}
    assert [e["kind"] for e in town.rec.events if e["kind"].startswith("own_")] == ["own_started", "own_built"]


def test_without_the_money_for_parts_they_go_on_renting():
    town, a, firm = _renter_of_a_set(cash=100_000)
    consider_own_set(town, a)
    assert a.set_hours_left is None and "appliances" in a.subs


def test_an_owned_set_is_kept_up_with_their_hours_and_parts_and_wears_without_them():
    town, a, firm = _renter_of_a_set()
    unit = town.new_own_unit(town.needs["appliances"], a)
    unsubscribe(town, a, "appliances", "owns")
    a.unit["appliances"] = unit
    unit.age, unit.cond = 260, 0.6
    a.spare_hours = 20.0
    cash = a.cash
    keep(town, a)
    hours, goods = upkeep_need(town.cfg, unit)                               # read before the week aged it
    assert unit.age == 261 and a.cash < cash and unit.cond > 0.6
    a.cash, a.spare_hours, before = 0, 0.0, unit.cond
    keep(town, a)
    assert unit.cond < before                                                # no parts, no hours: it wears


def test_nothing_is_billed_for_what_they_own_and_it_counts_as_met():
    town, a, firm = _renter_of_a_set()
    unit = town.new_own_unit(town.needs["appliances"], a)
    unsubscribe(town, a, "appliances", "owns")
    a.unit["appliances"] = unit
    assert dues(town, a) == []
    pay_bills(town)
    assert a.met["appliances"] is True
```

- [ ] **Step 2: Run them.** Expected: FAIL (functions missing).
- [ ] **Step 3: Implement as the Interfaces block says.** Hours: upkeep labour in worker-weeks times `job_hours`. `done = min(1.0, hours_had / hours_needed, parts_paid / parts_needed)` with a need of 0 counting as done.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 5: The loan against a home

**Files:**
- Modify: `wefworld/bank.py`, `wefworld/household.py` (`dues`, `pay_bills`)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Produces, on `Bank`:
  - `home_first_payment(amount: int) -> int`: `ceil(amount / mortgage_weeks) + round(amount * firm_rate / weeks_per_year)`.
  - `home_credit(agent, price: int) -> int`: 0 if `town.week < agent.credit_block_until`; else the largest loan that is at most `mortgage_ltv * price - agent.home_loan` and whose `home_first_payment` is at most `mortgage_income_share * agent.income_estimate()`.
  - `lend_home(agent, amount: int, price: int) -> int`: lends `min(amount, home_credit(agent, price))` as `loan`; `agent.home_loan` up; `agent.home_pay = ceil(home_loan / mortgage_weeks)`; event `home_loan` (amount, balance).
  - `service_home(agent) -> bool`: as `service_firm`, at `firm_rate`, into `loan_interest` and `loan_principal`; a missed week adds the unpaid interest to the loan, `home_missed += 1`, event `home_loan_missed`, and `agent.shock(cfg, cfg.shock_missed)`; a paid week sets `home_missed = 0`.
- `household.dues`: a home loan is a bill, kind `"home_loan"`, priority 1 (where the rent would be), amount the week's interest plus instalment. `pay_bills`: pays it through `bank.service_home`; like rent, a calm agent borrows a personal loan for it.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_bank_lends_four_fifths_of_the_price_if_the_payment_fits_their_income():
    town = rtr_town()
    a = town.add_agent()
    a.role, a.wage = "staff", 100_000
    assert town.bank.home_credit(a, 5_400_000) == 4_320_000                 # 80% of $54,000
    assert town.bank.home_first_payment(4_320_000) == 4154 + 4985           # instalment and a week's interest at 6%
    a.wage = 20_000                                                          # 30% of $200 is $60 a week
    credit = town.bank.home_credit(a, 5_400_000)
    assert 0 < credit < 4_320_000 and town.bank.home_first_payment(credit) <= 6_000
    a.role, a.wage = None, 0
    assert town.bank.home_credit(a, 5_400_000) == 0                          # no income, no loan (J)


def test_a_home_loan_is_paid_like_the_rent_and_a_missed_week_is_a_blow():
    town = rtr_town()
    a = town.add_agent(cash=1_000_000)
    a.role, a.wage = "staff", 100_000
    assert town.bank.lend_home(a, 4_320_000, 5_400_000) == 4_320_000
    assert [d[1:] for d in dues(town, a)] == [("home_loan", "home_loan", 4154 + 4985)]
    pay_bills(town)
    assert a.home_loan == 4_320_000 - 4154 and a.home_missed == 0
    assert town.ledger.week_out == {"loan_interest": 4985, "loan_principal": 4154}
    a.cash, a.role, security = 0, None, a.security
    pay_bills(town)
    assert a.home_missed == 1 and a.security < security
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** `home_credit` finds the largest amount by solving the first-payment formula, not by search: `amount <= income_share * income / (1 / mortgage_weeks + firm_rate / weeks_per_year)`, then rounded down until `home_first_payment` fits.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 6: Building a home on a plot

**Files:**
- Modify: `wefworld/owning.py`, `wefworld/entities.py` (class `OwnBuild` with slots `hours_left`, `goods_left`, `spot`, `spent`; Agent slot `build`, default None), `wefworld/town.py` (quarterly call), `wefworld/household.py` (`check_reach`, `consider_moving` do nothing for an owner), `wefworld/labour.py` (an owner does not move for a job)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Consumes: `take_plot`, `place_own_unit`, `Bank.home_credit`, `Bank.lend_home`, `own_cost_week`, `work`.
- Produces:
  - `owning.build_cost(town) -> int`: 500 units at the housing `import_price` (5,400,000 at the start).
  - `owning.consider_building(town, agent)`, at a quarter end: for someone who rents their home (or has none), has no build under way and has a job. They start when (a) `home_credit(agent, build_cost)` plus their cash, less four weeks of their bills, covers `build_cost`; (b) what owning would cost a week (the first loan payment on what they would borrow, plus `own_cost_week` without the spread of the build cost) is under their rent times `(1 - switch_friction)`, or they have no home; (c) `take_plot` gives a plot (with no map, no plot is needed). Then `agent.build = OwnBuild(1200.0, 500.0, spot, 0)`; event `home_started` (spot).
  - `owning.work` (extended): after upkeep and the set, hours go to the home. Each hour worked buys its share of the goods (500 / 1200 a unit an hour) at `parts_price`: `mortgage_ltv` of it by `lend_home(agent, share, build_cost)` and the rest from their cash; what the bank will not lend comes from their cash too; if the two will not pay for the hour, the hour is not worked. An owner with a build and no job keeps the plot and the build: no more loan is drawn (no income, no credit) and the work goes on only as their cash buys parts. When `hours_left` reaches 0: `new_own_unit(housing, agent)`, `place_own_unit`, the rented home is given back (`unsubscribe(..., "owns")`), `agent.unit["housing"]` is theirs; event `home_built` (spot, amount spent, loan).
  - An owner of their home is never moved by `check_reach`, `consider_moving` or the job search; a job out of reach means a ride or the job is lost, by the rules already there.

- [ ] **Step 1: Write the failing tests**

```python
def _tenant_with_a_job(cash=2_000_000, *overrides):
    from test_places import block, employ, premises, tenant
    town = map_rtr_town("switch_prob=0.0", "move_prob=0.0", "sell_review_prob=0.0", "invest_prob=0.0", *overrides)
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 5, 6, homes=2)
    shop = premises(town, "food", 6, 6)
    a = tenant(town, home, cash=cash)
    employ(a, shop)
    return town, a, landlord


def test_a_tenant_whose_income_allows_starts_a_home_of_their_own_on_a_plot():
    town, a, landlord = _tenant_with_a_job()
    consider_building(town, a)
    assert a.build is not None and (a.build.hours_left, a.build.goods_left) == (1200.0, 500.0)
    assert a.build.spot.kind == "plots" and a.build.spot.plots_reserved == 1
    assert "housing" in a.subs                                               # they rent until it is finished


def test_no_job_no_loan_no_build():
    town, a, landlord = _tenant_with_a_job()
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    consider_building(town, a)
    assert a.build is None


def test_each_hour_worked_buys_its_parts_a_fifth_from_cash_and_the_home_is_theirs_at_the_end():
    town, a, landlord = _tenant_with_a_job(cash=1_500_000)
    consider_building(town, a)
    spot, rent_unit = a.build.spot, a.unit["housing"]
    for _ in range(100):                                                     # 20 hours a week would take 60 weeks
        a.spare_hours = 20.0
        work(town, a)
        if a.build is None:
            break
    assert owns(a, "housing") and a.unit["housing"].spot is spot and spot.private_units == [a.unit["housing"]]
    assert spot.plots_reserved == 0 and rent_unit.occupant is None and "housing" not in a.subs
    assert town.ledger.total_out["import"] == 5_400_000                      # every part came from outside
    assert (a.home_loan, a.cash) == (4_320_000, 1_500_000 - 1_080_000)       # four fifths the bank's, a fifth theirs
    assert [e["kind"] for e in town.rec.events if e["kind"].startswith("home_")][-1] == "home_built"


def test_someone_who_loses_their_job_half_way_keeps_the_plot_and_builds_on_only_with_cash():
    town, a, landlord = _tenant_with_a_job(cash=1_500_000)
    consider_building(town, a)
    spot = a.build.spot
    for _ in range(30):
        a.spare_hours = 20.0
        work(town, a)
    owed, left = a.home_loan, a.build.hours_left
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    a.spare_hours = 60.0
    work(town, a)
    assert a.home_loan == owed and a.build is not None and a.build.spot is spot    # no more is lent; the plot is theirs
    assert a.build.hours_left < left                                              # their cash still buys parts
    a.cash, a.spare_hours, left = 0, 60.0, a.build.hours_left
    work(town, a)
    assert a.build.hours_left == left                                             # no cash, no parts, no work


def test_an_owner_is_not_moved_by_the_search_for_a_cheaper_home():
    town, a, landlord = _tenant_with_a_job("move_prob=1.0")
    unit = town.new_own_unit(town.needs["housing"], a)
    spot = take_plot(town)
    place_own_unit(spot, unit)
    unsubscribe(town, a, "housing", "owns")
    a.unit["housing"] = unit
    review_subscriptions(town)
    assert a.unit["housing"] is unit and "housing" not in a.subs
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 7: An owner's upkeep of their home, and how owning counts in wellbeing

**Files:**
- Modify: `wefworld/owning.py` (`keep` covers the home), `wefworld/household.py` (`update_agents`, `essentials_cost`)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Consumes: `keep`, `owns`, `Bank.home_credit`.
- Produces:
  - `owning.borrowable(town, agent) -> int`: for an owner of their home, `max(0, int(mortgage_ltv * value) - home_loan)` where value is `build_cost(town)` less wear by age over the housing `life_years`, never under a fifth of it (as `Firm.units_value` wears a unit); 0 for anyone else.
  - `update_agents`: the cushion term uses `agent.cash + borrowable(town, agent)`; the debt term is unchanged (it reads the personal loan only); the basket is unchanged (an owned need is priced at the cheapest on offer, as a need gone without is). `essentials_cost`: an owned need costs nothing.

- [ ] **Step 1: Write the failing tests**

```python
def _owner(cash=0):
    town, a, landlord = _tenant_with_a_job(cash=cash)
    unit = town.new_own_unit(town.needs["housing"], a)
    place_own_unit(take_plot(town), unit)
    unsubscribe(town, a, "housing", "owns")
    a.unit["housing"] = unit
    return town, a, unit


def test_owning_does_not_shrink_the_basket_and_what_they_could_borrow_counts_as_cushion():
    town, a, unit = _owner()
    renter = town.add_agent()
    assert basket_cost(town, a) == basket_cost(town, renter)                 # both at the going rent
    assert borrowable(town, a) == 4_320_000
    a.home_loan = 4_000_000
    assert borrowable(town, a) == 320_000
    a.home_loan = 0
    update_agents(town)
    with_home = a.security
    unit.owner = None                                                        # the same person with no home to borrow on
    a.unit.pop("housing")
    a.security = town.cfg.security_start
    update_agents(town)
    assert a.security < with_home


def test_a_home_loan_paid_on_time_is_not_counted_as_debt():
    town, a, unit = _owner(cash=50_000_000)                                  # a cushion full either way
    update_agents(town)
    clear = a.security
    a.home_loan, a.security = 4_320_000, town.cfg.security_start
    update_agents(town)
    assert a.security == clear                                               # a loan on the home: no debt counted
    a.home_loan, a.loan, a.security = 0, 800_000, town.cfg.security_start    # eight weeks of wages, unsecured
    update_agents(town)
    assert a.security < clear


def test_an_owned_home_wears_without_upkeep_and_holds_with_it():
    town, a, unit = _owner(cash=1_000_000)
    unit.age, unit.cond = 520, 0.7
    a.spare_hours = 20.0
    keep(town, a)
    assert unit.cond >= 0.7 and town.ledger.week_out.get("import", 0) > 0
    a.cash, a.spare_hours, before = 0, 0.0, unit.cond
    keep(town, a)
    assert unit.cond < before
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 8: Foreclosure, and the sale for the debt

**Files:**
- Modify: `wefworld/owning.py`, `wefworld/town.py` (weekly call after `pay_bills`; `town.foreclosed` list), `wefworld/entities.py` (Unit slots `debt`, `ask`, `since`)
- Test: `tests/test_rtr.py`

**Interfaces:**
- Consumes: `Bank.home_credit`, `Bank.lend_home`, `Bank._write_off`, `subscriptions.unsubscribe`, `owns`.
- Produces:
  - `owning.foreclose(town, agent)`: called when `agent.home_missed >= grace_weeks` and they own their home. The unit's `owner` and `occupant` become None; `unit.debt = unit.ask = agent.home_loan`; `unit.since = town.week`; the agent's `home_loan`, `home_pay`, `home_missed` are 0 and `agent.unit` loses the home; `agent.shock(cfg, cfg.shock_eviction)`; event `foreclosed` (agent, amount the debt, spot). A build under way with a loan on it is foreclosed the same way: the plot and what was built are lost (the plot is freed: `plots_reserved - 1`), and the debt is written off at once (nothing stands to sell).
  - `owning.foreclosures(town)`, weekly after `pay_bills`: `foreclose` for every agent with `home_missed >= grace_weeks`.
  - `owning.sell_foreclosed(town)`, weekly: at each quarter end since `unit.since`, `unit.ask = max(1, int(unit.ask * (1 - foreclosed_price_drop)))`. Then each foreclosed home is offered, in agent order, to renters and the homeless with a job for whom `home_credit(agent, unit.ask)` plus their cash, less four weeks of their bills, covers `unit.ask`, and whose first payment plus upkeep is under their rent times `(1 - switch_friction)` or who have no home, and who can reach their work from it. The first such buyer pays the bank: their cash and `lend_home` to OUTSIDE as `loan_recovery`, `unit.ask` in all; `bank._write_off(unit.debt - unit.ask)`; `unit.owner = buyer`; they move in (their rented home is given back). Event `foreclosed_sold` (agent, amount, debt).
  - The former owner then rents or is homeless by `review_subscriptions`, unchanged.
  - Landlord firms and residents who let are not offered it here: stage 1b.

- [ ] **Step 1: Write the failing tests**

```python
def test_four_missed_payments_and_the_bank_takes_the_home():
    town, a, unit = _owner()
    a.home_loan, a.home_pay, a.home_missed = 3_000_000, 2885, 4
    security = a.security
    foreclose(town, a)
    assert unit.owner is None and unit.occupant is None and (unit.debt, unit.ask) == (3_000_000, 3_000_000)
    assert (a.home_loan, a.home_missed) == (0, 0) and "housing" not in a.unit and a.security < security
    assert unit in town.foreclosed and not housed(a)


def test_a_renter_who_can_borrow_for_it_buys_it_for_the_debt_and_moves_in():
    town, a, unit = _owner()
    a.home_loan, a.home_missed = 3_000_000, 4
    foreclose(town, a)
    from test_places import block, employ, tenant
    landlord = town.firms_for("housing")[0]
    buyer = tenant(town, landlord.lots[0], cash=1_000_000)
    employ(buyer, town.firms_for("food")[0])
    sell_foreclosed(town)
    assert unit.owner is buyer and owns(buyer, "housing") and "housing" not in buyer.subs
    assert town.ledger.week_out == {"loan_recovery": 3_000_000}
    assert (buyer.cash, buyer.home_loan) == (132_000, 2_132_000)             # they keep four weeks of their $330 rent
    assert unit not in town.foreclosed and town.bank.writeoffs_total == 0


def test_unsold_it_stands_empty_and_the_price_falls_a_twentieth_each_quarter():
    town, a, unit = _owner()
    a.home_loan, a.home_missed = 3_000_000, 4
    foreclose(town, a)
    town.week = unit.since + 13
    sell_foreclosed(town)
    assert unit.ask == 2_850_000 and unit.owner is None
    town.week = unit.since + 26
    sell_foreclosed(town)
    assert unit.ask == 2_707_500
    unit.ask = 1
    town.week = unit.since + 39
    sell_foreclosed(town)
    assert unit.ask == 1                                                     # never below a cent


def test_the_banks_loss_is_written_off_once_when_it_sells_below_the_debt():
    town, a, unit = _owner()
    a.home_loan, a.home_missed = 3_000_000, 4
    foreclose(town, a)
    unit.ask = 2_000_000
    from test_places import employ, tenant
    buyer = tenant(town, town.firms_for("housing")[0].lots[0], cash=2_500_000)
    employ(buyer, town.firms_for("food")[0])
    sell_foreclosed(town)
    assert unit.owner is buyer and town.bank.writeoffs_total == 1_000_000
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** A buyer pays from their cash down to four weeks of their bills, and borrows the rest.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 9: The record

**Files:**
- Modify: `wefworld/metrics.py`, `wefworld/recorder.py`, `wefworld/runner.py`
- Test: `tests/test_rtr.py`, `tests/test_map_record.py`

**Interfaces:**
- Produces, only when `cfg.rtr`:
  - weekly town measures `homes_owned` (lived in by their owner), `homes_foreclosed` (standing empty on offer), `homes_building` (builds under way), `sets_owned`, `home_loans` (cents owed), `spare_hours` (mean, scope `all`);
  - `homes` and `homes_vacant` count privately owned homes as well as landlords' (a foreclosed home is vacant);
  - the `units` snapshot includes own units, with `firm` NULL and a new column `owner`;
  - the `places` snapshot writes a `plots` block with kind `homes`, label `owned`, `homes = len(private_units)`, `let` = those lived in, so the dashboard and the town view draw it as a block of homes without change;
  - `summary.json` gains `world`, and when RTR `homes_owned`, `sets_owned`, `foreclosures` (count of `foreclosed` events).
- In a WEF run none of these appear, and the record fingerprint is as before (Task 1's pins).

- [ ] **Step 1: Write the failing tests**

```python
def test_an_rtr_run_records_who_owns_and_a_wef_run_does_not(tmp_path):
    from wefworld.runner import run
    small = ["population_cap=60", "years=3", "seed=3", "stop_on_failure=false"]
    rtr = run(load_config(None, small + ["world=rtr"]), out_root=tmp_path / "rtr", quiet=True)
    wef = run(load_config(None, small), out_root=tmp_path / "wef", quiet=True)
    def metrics(folder):
        con = sqlite3.connect(folder / "run.sqlite")
        try:
            return {m for (m,) in con.execute("SELECT DISTINCT metric FROM series WHERE scope = 'town'")}
        finally:
            con.close()
    new = {"homes_owned", "homes_foreclosed", "homes_building", "sets_owned", "home_loans"}
    assert new <= metrics(rtr) and not (new & metrics(wef))
    assert json.loads((rtr / "summary.json").read_text())["world"] == "rtr"
    assert (rtr / "dashboard.html").exists() and (rtr / "town.html").exists()     # the pages still build
```

- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 10: Whole towns

**Files:**
- Modify: `tests/test_town_invariants.py` (the checks of Task 3 extended: a foreclosed unit has no owner and no occupant and is in `town.foreclosed`; `home_loan > 0` only for someone who owns a home or has a build; `plots_reserved` equals the builds under way on that block), `tests/test_rtr.py`
- Create: `docs/build-ledger-rtr-stage1a-2026-11-16.md` (kept from Task 1 on)
- Modify: `README.md` (a section "The second world: Right to Repair, stage 1a"), `docs/superpowers/specs/2026-11-16-rtr-world-design.md` (a line under section 14: what 1a built and what waits for 1b)

- [ ] **Step 1: Write the failing test**

```python
def test_an_rtr_town_keeps_its_accounts_and_places_and_reaches_every_rule_of_stage_1a():
    import collections
    from test_town_invariants import run_checked
    seen = collections.Counter()
    for seed in (1, 2):
        town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false", f"seed={seed}",
                                       "map_width=7", "map_height=7"]))
        assert run_checked(town, 14 * 52) == []
        for e in town.rec.events:
            seen[e["kind"]] += 1
    for kind in ("own_started", "own_built", "home_started", "home_built", "home_loan", "home_loan_missed",
                 "foreclosed", "foreclosed_sold"):
        assert seen[kind] > 0, f"these towns never reached '{kind}': pick seeds or settings that do"


def test_an_rtr_town_with_no_map_builds_homes_with_no_plots_and_keeps_its_accounts():
    from test_town_invariants import run_checked
    town = Town(load_config(None, ["world=rtr", "map_width=0", "population_cap=120", "stop_on_failure=false", "seed=1"]))
    assert run_checked(town, 8 * 52) == []
    built = [u for u in town.own_units if u.spec.name == "housing"]
    assert built and all(u.spot is None for u in built)
```

- [ ] **Step 2: Run it.** Expected: FAIL until every rule is reached with the checks clean; choose seeds and a population that reach them, and record the choice in the ledger.
- [ ] **Step 3: Run the whole suite, then by hand:** the WEF batch town of 13 November under the old rules (`configs/before-16-november.json`, seed 74, 60 years, `snapshot_every=13`) must still give `08251209eb136522` with 180,377 events; three full RTR towns (seeds 1, 2, 3, 60 years) for the README: when they fail if they do, homes owned, sets owned, foreclosures, and where the town's money sits.
- [ ] **Step 4: Fresh review** of the whole branch (superpowers:requesting-code-review, most capable model), one fix pass with a failing test first for each Critical or Important finding, minors to the ledger.
- [ ] **Step 5: Write the README section and the ledger's closing lines.**
- [ ] **Step 6: Commit** (with approval). Merging into `develop` is Jason's call.
