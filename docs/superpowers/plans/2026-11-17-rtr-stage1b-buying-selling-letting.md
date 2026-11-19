# RTR stage 1b: buying, selling and letting. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In an RTR town a tenant can buy the home they rent, a renter can buy a home a landlord cannot let, a resident who owns can build or buy a home to let, and a foreclosed home goes down Jason's whole order (a renter, then a resident who owns, then a landlord firm); a WEF town is still the town it was.

**Architecture:** Two parts, each ending in whole towns under the weekly checks. **Part A** lets a landlord's home become a private one where it stands: the unit leaves the firm's `units` and its block's `units` and joins the block's `private_units`, so the renting code still sees only homes for rent. **Part B** adds homes for rent that stand on no landlord's block ("loose" homes): each has its own rent (`Unit.rent`), is found through `town.to_let`, and belongs either to a firm or to a person's `Letting`, a small object that stands where a firm stands in the tenancy code (`price`, `subs`, `spec`, `cash`). All new behaviour is in `wefworld/owning.py` and runs only when `cfg.rtr`.

**Tech Stack:** Python 3.12, standard library only; pytest (`python3 -m pytest -rN`).

**Spec:** `docs/superpowers/specs/2026-11-16-rtr-world-design.md`, sections 6 (last two points), 7, 10, 11, 12. Stage 1a (`docs/superpowers/plans/2026-11-16-rtr-stage1a-owning-your-own.md`, commit `c957e8c`) is the base.

## Global Constraints

- `world=wef` towns are unchanged: the WEF pins in `tests/test_rtr.py` hold after every task, and seed 74 of the 13 November batch under `configs/before-16-november.json` still gives `08251209eb136522` with 180,377 events (checked by hand at the end of each part).
- Every dollar moves through `Ledger.pay`. A home bought from a landlord or from a person is kind `home_sale` (inside town). A foreclosed home's buyer pays the bank as `loan_recovery`. Rent to a person is `subscription`, as rent to a firm is.
- Numbers from the spec: a let home's asking price is ten years (`horizon_value_cap` weeks, 520) of its rent net of upkeep; a home empty for `empty_sale_weeks` (52) is offered at its value as it stands; `mortgage_ltv` 0.80, `mortgage_weeks` 1040, `mortgage_income_share` 0.30; building or buying to let needs the rent to cover the loan payment and upkeep with `maker_margin` (0.10) to spare; a buyer keeps four weeks of bills in hand; the reluctance to change is `switch_friction`; a tenant of a person is put out after `grace_weeks` (4) missed rents, like any tenant.
- No sale puts a tenant out. A let home goes to its sitting tenant, or to someone who goes on letting it with the tenant staying.
- A block with a privately owned home on it is never sold whole or pulled down. Homes on land a landlord only leases are not sold.
- New weekly measures and event kinds only when `cfg.rtr`.
- No em dashes in docs, comments or pages. Every (C) call goes in `docs/build-ledger-rtr-stage1b-2026-11-17.md` as `Ruling: <what> ; <why> ; <cost if wrong>`.
- **Tests must bite.** Each part ends by breaking its rules one at a time in a scratch copy (`mutate.py`, as on 17 November): every break must fail a test in `tests/test_rtr_1b.py`, or a test is added until it does. The review of 1a found 13 breaks the tests let through; this step is why.

## Review Focus

1. A landlord closes while private homes stand on its blocks: the block becomes a block of plots, the owners keep their homes, and nothing is freed, sold or pulled down under them.
2. A tenant buys their home in the same week their landlord is taken over or fails: the home is theirs, and the firm that took over has neither the unit nor the tenant.
3. A person who lets a home loses their own job: the rent still counts as income for the bank; if payments are missed the bank takes a let home first, the tenant stays, and the debt taken with each home adds up to what was owed.
4. A loose home with no tenant for years: it is on offer, its rent follows the going rent, it ages and wears, and it is never counted as lived in.
5. A foreclosed home with a sitting tenant: only that tenant, a resident who will let it, or a landlord firm can take it; whoever does, the tenant never loses a week.

---

## Part A: buying from a landlord

### Task 1: A landlord's home can become a private one where it stands

**Files:**
- Modify: `wefworld/entities.py` (Unit slot `empty_since`, default None), `wefworld/places.py` (room counts; `_buy_or_lease`; `give_up_spots`, `_bare_lot`, `_free`), `wefworld/subscriptions.py` (`unsubscribe` and `Town.new_unit` set `empty_since`), `wefworld/owning.py`, `wefworld/recorder.py`, `wefworld/metrics.py`, `wefworld/config.py` (dials `empty_sale_weeks: int = 52`, `maker_margin: float = 0.10`)
- Test: `tests/test_rtr_1b.py` (new), `tests/test_town_invariants.py`

**Interfaces:**
- Produces:
  - `owning.make_private(town, unit, owner)`: for a firm's home. Removes it from `unit.firm.units` and `spot.units`, adds it to `spot.private_units` and `town.own_units`; if it was let, the tenant's subscription to the firm ends without an event of leaving (`firm.subs`, `agent.subs`, `spot.occupied`, `spot.better_let` kept right); `unit.firm = None`, `unit.owner = owner`. The caller sets who lives in it.
  - Every count of a block's room is `len(units) + len(private_units) + reserved` against `homes_per_spot` (`room_for_home`, `_buy_or_lease`'s candidates, the weekly check).
  - `_buy_or_lease` never offers a block with `private_units`. `give_up_spots`: a block the closing firm owns that has `private_units` becomes a block of plots (kind `plots`, no owner, no user, `units` emptied by the wind-up as now) and is not freed or sold; event `block_to_plots` (spot).
  - `unit.empty_since`: the week a firm's home last became empty (set when built and by `unsubscribe`; None while let).
  - Recorder and metrics: a landlord's block reports `homes = len(units) + len(private_units)`; lived-in private homes count as let for the page.
- `tests/test_town_invariants.py::check_places`: on a `homes` block every private unit has `firm is None` and `spot` the block; the room count includes them.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_landlords_home_becomes_private_where_it_stands_and_its_tenant_stops_being_one():
    town, a, landlord = tenant_with_a_job()
    unit, spot = a.unit["housing"], a.unit["housing"].spot
    make_private(town, unit, a)
    assert unit.firm is None and unit.owner is a and unit in town.own_units
    assert unit not in landlord.units and unit not in spot.units and spot.private_units == [unit]
    assert "housing" not in a.subs and a.id not in landlord.subs and spot.occupied == 0
    assert [e for e in town.rec.events if e["kind"] == "sub_end"] == []       # nobody left a home


def test_a_block_with_a_private_home_counts_it_as_room_taken_and_is_never_sold_or_pulled_down():
    town, a, landlord = tenant_with_a_job()
    spot = a.unit["housing"].spot
    make_private(town, a.unit["housing"], a)
    town.cfg.homes_per_spot = 2                                              # one private, one for rent: full
    assert room_for_home(town, landlord) is not spot
    for s in town.map.spots:                                                 # no empty land: a firm must buy
        if s.kind is None:
            s.kind = "service"
    shop = town.add_firm("food")
    shop.cash = 10**10
    assert take_spot(town, shop, "premises") is not spot


def test_when_the_landlord_closes_a_block_with_private_homes_becomes_a_block_of_plots():
    town, a, landlord = tenant_with_a_job()
    unit, spot = a.unit["housing"], a.unit["housing"].spot
    make_private(town, unit, a)
    a.unit["housing"], unit.occupant = unit, a
    wind_up(town, landlord, "test")
    assert spot.kind == "plots" and spot.owner is None and spot.user is None
    assert spot.private_units == [unit] and spot.units == [] and owns(a, "housing")
```

Helpers at the top of `tests/test_rtr_1b.py`, built on those of `tests/test_rtr.py`:
- `tenant_with_a_job(cash=2_000_000, *overrides)`, `renter_of_a_set(cash)`: `_tenant_with_a_job`, `_renter_of_a_set`.
- `owner_in_town(cash=0)`: `_owner(cash)`: returns `(town, owner, unit)`, the owner in work and living in `unit` on a plot.
- `foreclosed_home(debt=3_000_000)`: `_foreclosed(debt)`: returns `(town, former_owner, unit)`, the unit held by the bank.
- `second_owner(town, cash)`: adds a resident with a job at the town's food firm who owns and lives in a new home on a plot; returns them.
- `owner_with_a_tenant(rent)`: `owner_in_town(cash=0)`, a second home of theirs on a plot `put_to_let` at `rent`, and a renter with $10,000 living in it; returns `(town, owner, unit, second, renter)`.

- [ ] **Step 2: Run them.** `python3 -m pytest -rN tests/test_rtr_1b.py`. Expected: FAIL (`make_private` missing).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass, the WEF pins among them.
- [ ] **Step 5: Commit** (with Jason's approval; otherwise go on).

### Task 2: A tenant buys the home they rent

**Files:**
- Modify: `wefworld/owning.py`, `wefworld/ledger.py` (nothing: `home_sale` is an inside-town kind and needs no change; assert it in a test), `wefworld/town.py` (quarterly call)
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Consumes: `make_private`, `Bank.home_cap`, `Bank.home_credit`, `Bank.lend_home`, `Bank.home_first_payment`, `own_cost_week`, `_spare_cash`, `Bank.repay_excess`.
- Produces:
  - `owning.needs_cash(town, firm) -> bool`: `firm.cash < cfg.reserve_weeks * firm.last_opex` or `firm.loan_missed > 0` or `firm.rent_missed > 0`.
  - `owning.unit_value(town, firm, unit) -> int`: `firm.units_value(cfg, [unit])` (the cost of building it at the firm's costs, less wear).
  - `owning.let_price(town, firm, unit) -> int`: ten years of its rent net of upkeep, never under its value: `max(unit_value, horizon_value_cap * (unit_rent(unit) - upkeep))` where upkeep is `upkeep_need` at the firm's wage and goods cost.
  - `owning.buyer_terms(town, agent, price, rent=None) -> int | None`: what they would borrow, or None if they cannot or would not buy: `borrow = max(0, price - _spare_cash)` must be within `min(int(mortgage_ltv * price), home_cap(agent))`; with `rent`, the first payment on `borrow` plus `own_cost_week(housing, build=False)` must be under `rent * (1 - switch_friction)`.
  - `owning.offer_to_tenant(town, firm, unit) -> bool`: for a let home on land the firm owns, whose tenant has a job and no build under way. The price is `unit_value` if `needs_cash(firm)`, else `let_price`. If `buyer_terms(tenant, price, their rent)` is not None the sale is made: `lend_home`, `ledger.pay(tenant, firm, price, "home_sale")`, `firm.w_revenue += max(0, price - unit_value)` (the gain is income; the rest is capital coming back), `bank.repay_excess(firm)`, `make_private`, the tenant is its owner and occupant; event `home_bought` (agent, firm, amount, loan, value, `from`="tenant").
  - `owning.landlord_sales(town)`, at a quarter end in `owning.quarter`: for each housing firm, `offer_to_tenant` for each let home on land it owns, oldest tenancy first.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_let_home_is_priced_at_ten_years_of_its_rent_after_upkeep_or_at_its_value_when_the_landlord_is_short():
    town, a, landlord = tenant_with_a_job()
    unit = a.unit["housing"]
    labour, goods = upkeep_need(town.cfg, unit)
    upkeep = labour * landlord.wage + goods * landlord.goods_cost()
    assert let_price(town, landlord, unit) == int(520 * (unit_rent(unit) - upkeep))
    assert let_price(town, landlord, unit) > unit_value(town, landlord, unit) == landlord.units_value(town.cfg, [unit])
    assert not needs_cash(town, landlord)
    landlord.cash, landlord.last_opex = 100, 1_000
    assert needs_cash(town, landlord)


def test_a_tenant_who_can_borrow_for_it_buys_their_home_and_the_landlord_is_paid():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit, rent = a.unit["housing"], unit_rent(a.unit["housing"])
    price, value = let_price(town, landlord, unit), unit_value(town, landlord, unit)
    cash = landlord.cash
    assert offer_to_tenant(town, landlord, unit)
    assert owns(a, "housing") and a.unit["housing"] is unit and "housing" not in a.subs
    assert landlord.cash == cash + price and landlord.w_revenue == price - value
    assert a.home_loan == max(0, price - (5_000_000 - 4 * rent))              # they keep four weeks of bills
    assert town.ledger.week_internal["home_sale"] == price
    assert [e["kind"] for e in town.rec.events if e["kind"] == "home_bought"] == ["home_bought"]


def test_a_tenant_does_not_buy_when_owning_would_cost_as_much_as_renting_or_they_have_no_job():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    landlord.price = 60_000                                                   # ten years of $600 a week: too dear to carry
    assert not offer_to_tenant(town, landlord, unit) and "housing" in a.subs
    town2, b, landlord2 = tenant_with_a_job(cash=50_000_000)
    b.employer.staff.remove(b)
    b.employer = b.role = None
    b.wage = 0
    assert offer_to_tenant(town2, landlord2, b.unit["housing"])               # enough cash needs no bank: they buy outright
    town3, c, landlord3 = tenant_with_a_job(cash=500_000)
    c.employer.staff.remove(c)
    c.employer = c.role = None
    c.wage = 0
    assert not offer_to_tenant(town3, landlord3, c.unit["housing"])           # no income, no loan


def test_a_landlord_short_of_cash_sells_at_the_homes_value():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    landlord.cash, landlord.last_opex = 100, 1_000
    value = unit_value(town, landlord, unit)
    assert offer_to_tenant(town, landlord, unit)
    assert landlord.cash == 100 + value and landlord.w_revenue == 0
```

```python
def test_a_home_bought_just_before_the_landlord_is_taken_over_stays_the_buyers():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    offer_to_tenant(town, landlord, unit)
    rival = town.add_firm("housing")
    rival.cash = 10**9
    _merge(town, landlord, rival, 0)                                         # the landlord fails and a rival takes it over
    assert owns(a, "housing") and unit not in rival.units and a.id not in rival.subs
    assert unit.spot.private_units == [unit] and unit.spot.user is rival
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Decide and ledger whether a tenant with no job may buy outright for cash (the second case of the third test says yes: no loan is asked for).
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 3: A home a landlord cannot let is sold cheap; a short landlord sells empty homes too

**Files:**
- Modify: `wefworld/owning.py`
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Consumes: `_buyers`, `buyer_terms`, `make_private`, `unit.empty_since`.
- Produces:
  - `owning.offer_empty(town, firm, unit, buyers) -> bool`: for an empty home on land the firm owns that has stood empty `empty_sale_weeks` or more (J: "Sells it cheap"), or any empty home of a firm that `needs_cash`. The price is `unit_value`. The first of `buyers` (renters and the homeless with a job, in order of arrival, as for a foreclosed home) who can reach their work from it and for whom `buyer_terms(agent, price, their rent)` is not None buys it and moves in: as `offer_to_tenant`, with `from`="empty" on the event, and their rented home goes back.
  - `landlord_sales` calls it for each such home, after the offers to tenants.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_home_empty_for_a_year_is_sold_at_its_value_to_a_renter_who_moves_in():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    home = a.unit["housing"].spot
    empty = next(u for u in home.units if u.occupant is None)
    empty.empty_since = town.week - 52
    value = unit_value(town, landlord, empty)
    landlord_sales(town)
    assert empty.owner is a and a.unit["housing"] is empty and landlord.w_revenue == 0
    assert town.ledger.week_internal["home_sale"] == value


def test_a_home_empty_for_less_than_a_year_is_not_sold_unless_the_landlord_is_short():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    landlord.price = 60_000                                                   # so the tenant does not buy their own
    empty = next(u for u in a.unit["housing"].spot.units if u.occupant is None)
    empty.empty_since = town.week - 51
    landlord_sales(town)
    assert empty.owner is None
    landlord.cash, landlord.last_opex = 100, 1_000
    landlord_sales(town)
    assert empty.owner is a
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 4: The landlord of the block buys back a foreclosed home; appliance firms sell sets

**Files:**
- Modify: `wefworld/owning.py`
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Produces:
  - `owning.make_rented(town, unit, firm)`: the reverse of `make_private` for a home standing on that firm's block: back into `firm.units` and `spot.units`, out of `private_units` and `own_units`, `owner` None, `empty_since` this week.
  - In `sell_foreclosed`, after no renter takes a home: if it stands on a landlord's block, that landlord buys it when `unit.ask <= horizon_value_cap * (going rent for the block - upkeep)` and `firm.cash - reserve >= unit.ask`: `ledger.pay(firm, OUTSIDE, ask, "loan_recovery")`, the bank's loss written off, `make_rented`; event `foreclosed_sold` with the firm. (Homes on blocks of plots wait for Part B.)
  - `owning.offer_set(town, firm, unit) -> bool`: an appliance firm that `needs_cash` sells a let set to its renter at `unit_value` when the renter can pay from spare cash or a personal loan and it is cheaper than building one (parts and their hours); the unit becomes theirs (`unit.firm = None`, in `own_units`); the payment is kind `set_sale` (inside town). Called from `landlord_sales` for appliance firms. (C: spec section 6, "sells one by the landlord's rule"; only the short-of-cash half applies, since a set is rented for less than ten years of its upkeep would fetch.)

- [ ] **Step 1: Write the failing tests**

```python
def test_the_blocks_landlord_buys_back_a_foreclosed_home_nobody_else_takes():
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    offer_to_tenant(town, landlord, unit)
    a.home_missed, a.cash = 4, 0
    foreclosures(town)
    unit.ask = 1_000_000
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and unit in landlord.units and unit in unit.spot.units
    assert unit.owner is None and unit not in town.own_units and unit not in town.foreclosed
    assert town.ledger.week_out["loan_recovery"] == 1_000_000


def test_an_appliance_firm_short_of_cash_sells_a_set_to_its_renter():
    town, a, firm = renter_of_a_set()
    unit = a.unit["appliances"]
    firm.cash, firm.last_opex = 100, 1_000
    value = unit_value(town, firm, unit)
    assert offer_set(town, firm, unit)
    assert owns(a, "appliances") and "appliances" not in a.subs and firm.cash == 100 + value
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 5: Part A in whole towns

- [ ] **Step 1: Add to `tests/test_rtr_1b.py`** a whole-town test: two towns of 200 on a 7 by 7 map, 14 years, `run_checked(town, weeks) == []`, reaching `home_bought` from a tenant, `home_bought` of an empty home, a landlord buying back a foreclosed home, and `block_to_plots`. Choose seeds that reach them; record the choice.
- [ ] **Step 2: Mutation step.** Break each rule of Tasks 1 to 4 in a scratch copy, one at a time (the price of a let home; the year empty; needs cash; the tenant-first order; the four weeks; the reach of work; the room count; the block that cannot be sold; the gain as income). Every break must fail a test; add tests until each does. List them in the ledger.
- [ ] **Step 3: By hand:** the old-rules WEF town (seed 74) gives `08251209eb136522`, 180,377 events; three full RTR towns (seeds 1, 2, 3) for the ledger.
- [ ] **Step 4: Report to Jason** what Part A does to the three towns before going on.

---

## Part B: letting by people, and homes for rent on no landlord's block

### Task 6: Loose homes for rent

**Files:**
- Modify: `wefworld/entities.py` (Unit slot `rent`, default 0; class `Letting`; Agent slot `lets`, default None), `wefworld/places.py` (`unit_rent`, `find_home`), `wefworld/subscriptions.py` (`rent_home` with no map), `wefworld/town.py` (`town.to_let: list[Unit]`), `wefworld/owning.py`
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Produces:
  - `entities.Letting(owner)`: stands where a firm stands in the tenancy code. Attributes: `owner`, `id = -owner.id`, `need = "housing"`, `spec` (the housing need), `alive = True`, `price = 0`, `subs = {}`, `unserved = {}`, `units = []`, `w_revenue = 0`; property `cash` that reads and writes `owner.cash`. It is in no list of firms.
  - `owning.letting_of(town, agent) -> Letting`: theirs, made on first use and kept in `agent.lets`.
  - `Unit.rent`: the weekly rent of a loose home; `unit_rent(unit)` returns it when it is above 0.
  - `owning.put_to_let(town, unit, provider, rent)`: a home that stands on no block of its provider (a person's `Letting`, or a firm holding a single home): `unit.firm = provider`, in `provider.units`, `unit.rent = rent`, in `town.to_let` while empty.
  - `find_home` also offers each empty home in `town.to_let` (rent `unit.rent`, place `unit.spot`), by the same reckoning of cost; `subscribe` and `unsubscribe` keep `town.to_let` right (out when let, back when empty). With no map, `rent_home` takes the cheapest of the landlords' price and the loose rents.
  - `owning.going_rent(town, spot=None) -> int`: what a standard home lets for: the cheapest landlord's price, times the block's `rent_factor` when the home stands on a landlord's block; the last price of housing if no landlord is left.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_persons_letting_is_paid_like_a_landlord_and_the_money_is_theirs():
    town, owner, unit = owner_in_town(cash=0)                                # they own and live in `unit`
    second = town.new_own_unit(town.needs["housing"], owner)
    place_own_unit(take_plot(town), second)
    put_to_let(town, second, letting_of(town, owner), 30_000)
    renter = town.add_agent(cash=1_000_000)
    assert second in town.to_let
    assert rent_home(town, renter, "signup") and renter.unit["housing"] is second
    assert second not in town.to_let and unit_rent(second) == 30_000 and price_paid(renter, "housing") == 30_000
    pay_bills(town)
    assert owner.cash == 30_000 and renter.cash == 970_000
    assert town.ledger.week_internal["subscription"] == 30_000


def test_a_tenant_of_a_person_who_misses_four_rents_is_put_out_like_any_tenant():
    town, owner, unit = owner_in_town(cash=0)
    second = town.new_own_unit(town.needs["housing"], owner)
    place_own_unit(take_plot(town), second)
    put_to_let(town, second, letting_of(town, owner), 30_000)
    renter = town.add_agent(cash=0)
    rent_home(town, renter, "signup")
    for _ in range(4):
        pay_bills(town)
    assert "housing" not in renter.subs and second.occupant is None and second in town.to_let
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Find every place the tenancy code reads something of a firm that a `Letting` lacks (run a small town with one person letting under `run_checked` before going on) and ledger each.
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 7: One loan on everything a person owns; rent as income; upkeep of what they let

**Files:**
- Modify: `wefworld/bank.py` (`home_credit(agent, price, owned=0)`), `wefworld/owning.py` (`keep`, `borrowable`, `foreclose`), `wefworld/entities.py` (`Agent.income_estimate` adds the rent of their let homes that have tenants)
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Produces:
  - `owning.homes_of(town, agent) -> list[Unit]`: their own home (if owned) and the homes in their `Letting`.
  - `Bank.home_credit(agent, price, owned=0)`: `min(int(mortgage_ltv * (price + owned)), home_cap(agent)) - agent.home_loan`: the loan is one loan on all their homes. `borrowable` passes the value of all of them.
  - `Agent.income_estimate()`: plus the rents of their let homes that have a tenant.
  - `keep`: upkeep, by their hours and parts, of every home they own, their own first.
  - `foreclose`: with more than one home the bank takes one home each time: a let home first (the newest), their own last. The debt that goes with it is its share of the loan by value, and `home_loan` falls by that; `home_missed` returns to 0. A tenant in it stays: the home moves to `town.bank_lets`, a `Letting` with no owner that the bank's let homes belong to; the tenant's subscription moves to it at the same rent; each week, after the bills, whatever rent it has received is passed out of town as `loan_recovery` and comes off that home's `debt` and `ask` (C). It never holds money at the end of a week.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_rent_of_a_let_home_counts_as_income_and_one_loan_covers_all_their_homes():
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    wage = owner.wage
    assert owner.income_estimate() == wage + 30_000
    value = home_value(town, unit) + home_value(town, second)
    assert town.bank.home_credit(owner, 0, owned=value) == int(0.8 * value)
    owner.home_loan = 1_000_000
    assert borrowable(town, owner) == int(0.8 * value) - 1_000_000


def test_the_bank_takes_a_let_home_first_with_its_share_of_the_debt_and_the_tenant_stays():
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    assert second in town.foreclosed and second.owner is None and second.occupant is renter
    assert owns(owner, "housing") and second.debt + owner.home_loan == 4_000_000 and owner.home_missed == 0
    assert second.debt == round(4_000_000 * home_value(town, second) / (home_value(town, unit) + home_value(town, second)))
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 8: Building to let

**Files:**
- Modify: `wefworld/owning.py`, `wefworld/entities.py` (`OwnBuild` slot `to_let`, default False)
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Produces:
  - `owning.consider_building_to_let(town, agent)`, at a quarter end: for someone who owns the home they live in, has a job and no build under way. They build when (a) someone was turned away from town for want of a home in the quarter just ended (`town.no_home_week` within `quarter_weeks`); (b) `going_rent` covers the first payment on what they would borrow plus `own_cost_week(housing, build=False)` with `maker_margin` to spare; (c) the bank's credit on all they own and will own, with their spare cash, covers the materials; (d) there is a plot (anywhere: the tenant, not they, will live there). `agent.build = OwnBuild(..., to_let=True)`; event `home_started` with `to_let`.
  - When such a build is finished the home is theirs, nobody lives in it, and it is `put_to_let` at `going_rent` for its place; event `home_built` with `to_let`.
  - Each quarter a loose home with no tenant has its rent set again to `going_rent` (C).

- [ ] **Step 1: Write the failing tests** (the two below, and `test_a_loose_home_with_no_tenant_follows_the_going_rent_ages_and_is_never_counted_as_lived_in`: put a home to let at $300, move the landlords' price to $250, run `owning.quarter(town)` and `owning.after_bills(town)`: its rent is `going_rent`, its age is up by one, it is still in `town.to_let`, and the weekly `homes_vacant` counts it)

```python
def test_an_owner_builds_to_let_when_a_newcomer_was_turned_away_and_the_rent_would_cover_it():
    town, owner, unit = owner_in_town(cash=3_000_000)
    consider_building_to_let(town, owner)
    assert owner.build is None                                               # nobody was turned away
    town.no_home_week = town.week
    consider_building_to_let(town, owner)
    assert owner.build is not None and owner.build.to_let
    for _ in range(100):
        owner.spare_hours = 20.0
        work(town, owner)
        if owner.build is None:
            break
    built = letting_of(town, owner).units[0]
    assert built.owner is owner and built.occupant is None and built in town.to_let
    assert built.rent == going_rent(town) and owns(owner, "housing") and owner.unit["housing"] is unit


def test_nobody_builds_to_let_when_the_rent_would_not_cover_the_loan_and_upkeep_with_a_tenth_to_spare():
    town, owner, unit = owner_in_town(cash=3_000_000)
    town.no_home_week = town.week
    for landlord in town.firms_for("housing"):
        landlord.price = 10_000                                              # $100 a week
    consider_building_to_let(town, owner)
    assert owner.build is None
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 9: The rest of the order: owners who let, then landlord firms; let homes sold with their tenants

**Files:**
- Modify: `wefworld/owning.py`
- Test: `tests/test_rtr_1b.py`

**Interfaces:**
- Produces:
  - `owning.letting_terms(town, agent, price, rent) -> int | None`: what a resident who owns their home would borrow to buy a home to let, or None: the bank's credit on all they own and this home, with their spare cash, covers the price, and `rent` covers the first payment on what they borrow plus upkeep with `maker_margin` to spare.
  - `sell_foreclosed`, Jason's whole order for each home: (1) a renter: its sitting tenant if it is let, any renter or homeless person with a job if it is empty (stage 1a's rule); (2) a resident who owns their home, in order of arrival, by `letting_terms` at the home's rent (its tenant's rent, or `going_rent` if empty): it joins their `Letting`, a tenant stays and now pays them; (3) a landlord firm: the block's own landlord by Task 4's rule, or for a home on no landlord's block the housing firm with the most cash, when ten years of the rent net of upkeep is at least the price and its cash beyond its reserve covers it: the firm holds it as a loose home (`put_to_let`), a tenant stays.
  - `landlord_sales`: a let home whose tenant did not buy is offered at the same price to (2) and then to another landlord firm by the same tests, the tenant staying; an empty home past its year that no renter took is offered to (2).
  - Events `foreclosed_sold` and `home_bought` carry `to_let` and who the tenant is.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_foreclosed_home_no_renter_can_buy_goes_to_a_resident_who_owns_and_they_let_it():
    town, a, unit = foreclosed_home(debt=3_000_000)
    owner = second_owner(town, cash=5_000_000)                               # owns their own home, has a job
    sell_foreclosed(town)
    assert unit.owner is owner and unit in letting_of(town, owner).units and unit in town.to_let
    assert owner.unit["housing"] is not unit and unit.rent == going_rent(town)


def test_a_let_foreclosed_home_keeps_its_tenant_whoever_buys_it():
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    richest = max(town.firms_for("housing"), key=lambda f: f.cash)
    richest.cash = 50_000_000
    second.ask = 1_000_000
    sell_foreclosed(town)
    assert second.firm is richest and second.occupant is renter and renter.subs["housing"] is richest
    assert price_paid(renter, "housing") == 30_000


def test_with_no_renter_and_no_owner_able_a_landlord_firm_takes_a_home_on_a_block_of_plots():
    town, a, unit = foreclosed_home(debt=3_000_000)
    unit.ask = 500_000
    landlord = town.firms_for("housing")[0]
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and unit in landlord.units and unit.rent > 0 and unit in town.to_let
    assert unit.spot.kind == "plots" and unit not in unit.spot.units          # it stands where it stood
```

- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the whole suite.** Expected: all pass.
- [ ] **Step 5: Commit** (with approval).

### Task 10: The record, whole towns, the review

**Files:**
- Modify: `wefworld/metrics.py`, `wefworld/recorder.py`, `wefworld/runner.py`, `tests/test_town_invariants.py`, `README.md`, `docs/superpowers/specs/2026-11-16-rtr-world-design.md` (the "Built so far" paragraph), the ledger

**Interfaces:**
- Produces, only when `cfg.rtr`: weekly measures `homes_bought` (private homes that were once a landlord's), `homes_let_private` (homes let by people), `small_landlords` (people with at least one home to let), `homes_loose` (loose homes held by firms), `home_sales` (cents paid for homes in the week); `summary.json` gains the first three at the end. The weekly checks gain: every home in a `Letting` has its `owner` the `Letting`'s owner and `firm` the `Letting`; `town.to_let` is exactly the loose homes with no tenant; a tenant of a `Letting` or a loose home has it in `agent.unit`.

- [ ] **Step 1: Whole-town test** as in Task 5, reaching also: a home built to let and let; a foreclosed home bought by a resident who owns; one bought by a landlord firm; a let home sold with its tenant staying. A town with no map as well.
- [ ] **Step 2: Mutation step** for Tasks 6 to 9 (the tenth to spare; turned away last quarter; the order of the three kinds of buyer; the tenant staying; the bank taking a let home first; the share of the debt; rent as income; one loan on all their homes). Every break must fail a test.
- [ ] **Step 3: By hand:** the old-rules WEF town; three full RTR towns (seeds 1, 2, 3), set against the same towns under stage 1a (failed in years 23.0, 22.25 and 22.02) and in the WEF world (17.0, 18.0, 20.0).
- [ ] **Step 4: Fresh review** of the whole branch since `c957e8c` (most capable model), with this plan's Review Focus; one fix pass, a failing test first for each Critical or Important finding; minors to the ledger.
- [ ] **Step 5: README** (the RTR section brought up to stage 1b), the spec's "Built so far", the ledger's closing lines.
- [ ] **Step 6: Commit** (with approval). Merging is Jason's call.
