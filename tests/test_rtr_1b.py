"""The Right to Repair world, stage 1b: buying, selling and letting."""

import pytest
from conftest import BEFORE_THE_LINE, FIFTH_IN_CASH, what_happened  # noqa: F401
from test_rtr import _buyer, _foreclosed, _owner, _renter_of_a_set, _tenant_with_a_job

from engine.config import load_config
from engine.town import Town
from test_rtr import map_rtr_town  # noqa: E402

tenant_with_a_job = _tenant_with_a_job
renter_of_a_set = _renter_of_a_set
owner_in_town = _owner
foreclosed_home = _foreclosed
buyer_in = _buyer


# --- Part A, task 1: a landlord's home can become a private one where it stands ---------------------
def test_the_new_dials_have_the_designs_values():
    cfg = load_config()
    assert (cfg.empty_sale_weeks, cfg.maker_margin) == (52, 0.10)


def test_a_landlords_home_becomes_private_where_it_stands_and_its_tenant_stops_being_one():
    from engine.rtr_owning import make_private
    town, a, landlord = tenant_with_a_job()
    unit, spot = a.unit["housing"], a.unit["housing"].spot
    make_private(town, unit, a)
    assert unit.firm is None and unit.owner is a and unit in town.own_units
    assert unit not in landlord.units and unit not in spot.units and spot.private_units == [unit]
    assert "housing" not in a.subs and a.id not in landlord.subs and spot.occupied == 0
    assert [e for e in town.rec.events if e["kind"] == "sub_end"] == []       # nobody left a home


def test_a_block_with_a_private_home_counts_it_as_room_taken_and_is_never_sold_or_pulled_down():
    from engine.rtr_owning import make_private
    from engine.places import room_for_home, take_spot
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
    got = take_spot(town, shop, "premises")
    assert got is not None and got is not spot and spot.kind == "homes" and spot.user is landlord


def test_when_the_landlord_closes_a_block_with_private_homes_becomes_a_block_of_plots():
    from engine.corporate import wind_up
    from engine.rtr_owning import make_private, owns
    town, a, landlord = tenant_with_a_job()
    unit, spot = a.unit["housing"], a.unit["housing"].spot
    make_private(town, unit, a)
    a.unit["housing"], unit.occupant = unit, a
    wind_up(town, landlord, "test")
    assert spot.kind == "plots" and spot.owner is None and spot.user is None
    assert spot.private_units == [unit] and spot.units == [] and owns(a, "housing")
    assert [e["qty"] for e in town.rec.events if e["kind"] == "block_to_plots"] == [spot.id]


def test_a_landlords_home_remembers_when_it_fell_empty():
    from engine.subscriptions import subscribe, unsubscribe
    town, a, landlord = tenant_with_a_job()
    unit = a.unit["housing"]
    assert unit.empty_since is None
    town.week = 30
    unsubscribe(town, a, "housing", "test")
    assert unit.empty_since == 30
    subscribe(town, a, landlord, unit=unit)
    assert unit.empty_since is None
    assert town.new_unit(landlord).empty_since == 30


# --- task 2: a tenant buys the home they rent ----------------------------------------------------------
def test_a_let_home_is_priced_at_ten_years_of_its_rent_after_upkeep_or_at_its_value_when_the_landlord_is_short():
    from engine.rtr_owning import let_price, needs_cash, unit_value
    from engine.places import unit_rent
    from engine.production import upkeep_need
    town, a, landlord = tenant_with_a_job()
    unit = a.unit["housing"]
    labour, goods = upkeep_need(town.cfg, unit)
    upkeep = labour * landlord.wage + goods * landlord.goods_cost()
    assert let_price(town, landlord, unit) == int(520 * (unit_rent(unit) - upkeep)) == 13_416_000
    assert unit_value(town, landlord, unit) == landlord.units_value(town.cfg, [unit]) == 7_000_000
    landlord.price = 5_000                                                   # a rent so low the building is worth more
    assert let_price(town, landlord, unit) == 7_000_000
    assert not needs_cash(town, landlord)
    landlord.cash, landlord.last_opex = 100, 1_000
    assert needs_cash(town, landlord)
    landlord.cash, landlord.loan_missed = 10**9, 1
    assert needs_cash(town, landlord)


def test_a_tenant_who_can_borrow_for_it_buys_their_home_and_the_landlord_is_paid():
    from engine.rtr_owning import let_price, offer_to_tenant, owns, unit_value
    from engine.places import unit_rent
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    _no_free_plots(town)                                                     # (with a plot they would build: it costs less a week)
    unit, rent = a.unit["housing"], unit_rent(a.unit["housing"])
    price, value = let_price(town, landlord, unit), unit_value(town, landlord, unit)
    cash = landlord.cash
    assert offer_to_tenant(town, landlord, unit)
    assert owns(a, "housing") and a.unit["housing"] is unit and "housing" not in a.subs and unit.occupant is a
    assert landlord.cash == cash + price and landlord.w_revenue == price - value
    assert a.home_loan == price - (5_000_000 - 4 * rent) == 8_548_000        # they keep four weeks of bills
    assert a.cash == 4 * rent
    assert town.ledger.week_internal["home_sale"] == price
    [event] = [e for e in town.rec.events if e["kind"] == "home_bought"]
    assert (event["agent"], event["firm"], event["amount"], event["data"]["from"]) == (a.id, landlord.id, price, "tenant")


def test_a_tenant_does_not_buy_when_the_price_is_beyond_the_bank_or_owning_would_cost_as_much():
    from engine.rtr_owning import offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    landlord.price = 60_000                                                   # ten years of $600 a week: beyond the loan
    assert not offer_to_tenant(town, landlord, a.unit["housing"]) and "housing" in a.subs
    town2, b, landlord2 = tenant_with_a_job(cash=2_000_000)
    landlord2.price = 25_000                                                  # $250 rent: the bank would lend four fifths of
    assert not offer_to_tenant(town2, landlord2, b.unit["housing"])           # $92,560, but paying that off costs as much as renting
    b.cash = 6_000_000                                                        # with more of their own money in, it is cheaper
    assert offer_to_tenant(town2, landlord2, b.unit["housing"])


def test_a_tenant_with_no_job_buys_only_if_their_own_cash_covers_it():
    from engine.rtr_owning import offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=50_000_000)
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    assert offer_to_tenant(town, landlord, a.unit["housing"]) and a.home_loan == 0   # no bank needed
    town2, b, landlord2 = tenant_with_a_job(cash=500_000)
    b.employer.staff.remove(b)
    b.employer = b.role = None
    b.wage = 0
    assert not offer_to_tenant(town2, landlord2, b.unit["housing"])           # no income, no loan


def test_a_landlord_short_of_cash_sells_at_the_homes_value():
    from engine.rtr_owning import offer_to_tenant, unit_value
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    landlord.cash, landlord.last_opex = 100, 1_000
    value = unit_value(town, landlord, unit)
    assert offer_to_tenant(town, landlord, unit)
    assert landlord.cash == 100 + value and landlord.w_revenue == 0 and a.home_loan == value - (5_000_000 - 4 * 33_000)


def test_homes_on_land_the_landlord_only_leases_are_not_sold():
    from engine.rtr_owning import offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    other = town.add_firm("housing")
    a.unit["housing"].spot.owner = other                                      # the land is another firm's
    assert not offer_to_tenant(town, landlord, a.unit["housing"])


def test_a_home_bought_just_before_the_landlord_is_taken_over_stays_the_buyers():
    from engine.corporate import _merge
    from engine.rtr_owning import offer_to_tenant, owns
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    _no_free_plots(town)
    unit = a.unit["housing"]
    offer_to_tenant(town, landlord, unit)
    rival = town.add_firm("housing")
    rival.cash = 10**9
    _merge(town, landlord, rival, 0)                                         # the landlord fails and a rival takes it over
    assert owns(a, "housing") and unit not in rival.units and a.id not in rival.subs
    assert unit.spot.private_units == [unit] and unit.spot.user is rival


def test_each_quarter_a_landlord_offers_its_let_homes_to_their_tenants():
    from engine.rtr_owning import owns, quarter
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    _no_free_plots(town)
    quarter(town)
    assert owns(a, "housing")


# --- task 3: a home a landlord cannot let is sold cheap ------------------------------------------------
def _homeless_worker(town, cash):
    from test_places import employ
    b = town.add_agent(cash=cash)
    employ(b, town.firms_for("food")[0])
    return b


def _empty_home(town, a):
    return next(u for u in a.unit["housing"].spot.units if u.occupant is None)


def test_a_home_empty_for_a_year_is_sold_at_its_value_to_someone_who_moves_in():
    from engine.rtr_owning import landlord_sales, owns, unit_value
    town, a, landlord = tenant_with_a_job(cash=100_000)                      # the sitting tenant cannot buy anything
    b = _homeless_worker(town, 5_000_000)
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 52
    value = unit_value(town, landlord, empty)
    landlord_sales(town)
    assert empty.owner is b and owns(b, "housing") and b.unit["housing"] is empty and landlord.w_revenue == 0
    assert town.ledger.week_internal["home_sale"] == value and b.home_loan == value - 5_000_000
    assert [e["data"]["from"] for e in town.rec.events if e["kind"] == "home_bought"] == ["empty"]


def test_a_home_empty_for_less_than_a_year_is_not_sold_unless_the_landlord_is_short():
    from engine.rtr_owning import landlord_sales
    town, a, landlord = tenant_with_a_job(cash=100_000)
    b = _homeless_worker(town, 5_000_000)
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 51
    landlord_sales(town)
    assert empty.owner is None
    landlord.cash, landlord.last_opex = 100, 1_000
    landlord_sales(town)
    assert empty.owner is b


def test_a_renter_who_buys_an_empty_home_gives_back_the_one_they_rented():
    from test_places import block, employ, tenant
    from engine.rtr_owning import landlord_sales
    town, a, landlord = tenant_with_a_job(cash=100_000)
    other = block(town, landlord, 7, 6, homes=1)
    c = tenant(town, other, cash=5_000_000)
    employ(c, town.firms_for("food")[0])
    landlord.price = 60_000                                                  # too dear for c to buy the home they rent
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 52
    landlord_sales(town)
    assert empty.owner is c and other.units[0].occupant is None and "housing" not in c.subs


def test_nobody_whose_work_is_out_of_reach_of_it_buys_an_empty_home():
    from test_places import employ, premises
    from engine.rtr_owning import landlord_sales
    town, a, landlord = tenant_with_a_job(cash=100_000)
    far = premises(town, "entertainment", 0, 12)
    b = town.add_agent(cash=5_000_000)
    employ(b, far)
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 52
    landlord_sales(town)
    assert empty.owner is None


# --- task 4: the block's landlord buys back a foreclosed home; appliance firms sell sets ------------------
def _bought_then_foreclosed(ask):
    from engine.rtr_owning import foreclosures, offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    _no_free_plots(town)                                                     # so they buy; with a plot they would build
    unit = a.unit["housing"]
    assert offer_to_tenant(town, landlord, unit)
    a.home_missed, a.cash = 4, 0
    foreclosures(town)
    debt, unit.ask = unit.debt, ask
    town.no_home_week = town.week                                            # a home is wanted (a firm buys an empty one only then)
    town.ledger.start_week()
    return town, a, landlord, unit, debt


def test_the_blocks_landlord_buys_back_a_foreclosed_home_nobody_else_takes():
    from engine.rtr_owning import sell_foreclosed
    town, a, landlord, unit, debt = _bought_then_foreclosed(1_000_000)
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and unit in landlord.units and unit in unit.spot.units
    assert unit.owner is None and unit not in town.own_units and unit not in town.foreclosed
    assert unit.spot.private_units == [] and unit.empty_since == town.week and (unit.debt, unit.ask) == (0, 0)
    assert town.ledger.week_out == {"loan_recovery": 1_000_000} and landlord.cash == 49_000_000
    assert town.bank.writeoffs_total == debt - 1_000_000
    [event] = [e for e in town.rec.events if e["kind"] == "foreclosed_sold"]
    assert (event["firm"], event["agent"], event["amount"]) == (landlord.id, None, 1_000_000)


def test_the_landlord_does_not_buy_it_back_for_more_than_ten_years_of_its_rent_or_without_the_cash():
    from engine.rtr_owning import sell_foreclosed
    town, a, landlord, unit, debt = _bought_then_foreclosed(14_000_000)      # ten years of its net rent is $134,160
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed
    unit.ask = 1_000_000
    landlord.cash, landlord.last_opex = 1_100_000, 100_000                   # its reserve is $8,000: $3,000 short
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed


def test_a_renter_still_comes_before_the_landlord():
    from engine.rtr_owning import sell_foreclosed
    town, a, landlord, unit, debt = _bought_then_foreclosed(1_000_000)
    landlord.cash = 50_000_000
    b = _homeless_worker(town, 5_000_000)
    sell_foreclosed(town)
    assert unit.owner is b


def test_an_appliance_firm_short_of_cash_sells_a_set_to_its_renter():
    from engine.rtr_owning import offer_set, owns, unit_value
    town, a, firm = renter_of_a_set()
    unit = a.unit["appliances"]
    assert not offer_set(town, firm, unit)                                    # not short: it keeps renting it out
    firm.cash, firm.last_opex = 100, 1_000
    value = unit_value(town, firm, unit)
    assert value == 450_000 and offer_set(town, firm, unit)
    assert owns(a, "appliances") and "appliances" not in a.subs and firm.cash == 100 + value
    assert unit not in firm.units and unit in town.own_units and firm.subs == {}
    assert town.ledger.week_internal["set_sale"] == value


def test_a_renter_who_cannot_pay_or_is_building_their_own_does_not_buy_the_set():
    from engine.rtr_owning import offer_set
    town, a, firm = renter_of_a_set(cash=10_000)
    firm.cash, firm.last_opex = 100, 1_000
    assert not offer_set(town, firm, a.unit["appliances"])
    town2, b, firm2 = renter_of_a_set()
    firm2.cash, firm2.last_opex = 100, 1_000
    b.set_hours_left = 12.0
    assert not offer_set(town2, firm2, b.unit["appliances"])


# --- task 5: Part A in whole towns ------------------------------------------------------------------------
def _reached(town):
    """Which rules of stage 1b a town's own record shows it reached."""
    import collections
    seen, built_to_let = collections.Counter(), set()
    for e in town.rec.events:
        kind, data = e["kind"], e["data"]
        if kind == "home_bought":
            if data.get("buyer_firm") is not None:
                seen["let home sold to another landlord, tenant staying"] += 1
            elif data.get("to_let"):
                seen["let home sold to an owner, tenant staying" if data.get("tenant") is not None
                     else "empty home sold to an owner to let"] += 1
            else:
                seen["bought from the landlord by its " + data["from"]] += 1
        elif kind == "foreclosed_sold":
            if e["firm"] is not None:
                seen["foreclosed home to a landlord as a single home" if data.get("to_let")
                     else "foreclosed home to the block's landlord"] += 1
            elif data.get("to_let"):
                seen["foreclosed home to an owner who lets it"] += 1
            else:
                seen["foreclosed home to a renter"] += 1
            if data.get("tenant") is not None:
                seen["foreclosed home sold with its tenant staying"] += 1
        elif kind == "home_built" and data.get("to_let"):
            built_to_let.add(e["qty"])
        elif kind == "sub_start" and data.get("unit") in built_to_let:
            seen["home built to let and let"] += 1
        elif kind == "foreclosed" and data.get("tenant") is not None:
            seen["let home taken by the bank, tenant staying"] += 1
        elif kind == "block_to_plots":
            seen[kind] += 1
    return seen


# Stage 2's rules (makers and ideas) switched off, and the bank asking its fifth in cash as it did
# until 18 November, so these stay the towns the seeds were picked for. Towns with the whole price
# lent are run under the same checks in test_rtr_rulings.py.
# the towns these seeds were picked for: no makers, a fifth in cash, and (until 19 November) one rate for all a firm's staff
STAGE_ONE_ONLY = ["hustle_rate=0.0", "hustle_rate_struggling=0.0", "idea_rate=0.0", *FIFTH_IN_CASH, *BEFORE_THE_LINE]


@pytest.fixture(scope="module")
def whole_towns():
    """Towns of 200 run for fourteen years under the weekly checks: seeds 11 and 10 on a 7 by 7
    map, and seed 5 with no map. For each kind: (what the checks found, what was reached)."""
    import collections
    from test_town_invariants import run_checked
    out = {}
    for kind, seeds, place in (("map", (11, 10), ["map_width=7", "map_height=7"]), ("no map", (5,), ["map_width=0"])):
        problems, seen = [], collections.Counter()
        for seed in seeds:
            town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false",
                                           f"seed={seed}"] + STAGE_ONE_ONLY + place))
            problems += run_checked(town, 14 * 52)
            seen += _reached(town)
        out[kind] = (problems, seen)
    return out


# Not asked of these towns, because no small town reaches them (60 tried on 17/11, after the review's
# fixes): a landlord firm taking a home from the bank, and an empty home sold to an owner to let. Both
# need a newcomer turned away for want of a home while such a home is on offer. Their own tests hold them.
def _all_reached(seen, kinds):
    for kind in kinds:
        assert seen[kind] > 0, f"these towns never reached '{kind}': pick seeds that do"


def test_part_a_towns_keep_their_accounts_and_places_and_reach_every_rule(whole_towns):
    problems, seen = whole_towns["map"]
    assert problems == []
    _all_reached(seen, ("bought from the landlord by its tenant", "bought from the landlord by its empty",
                        "foreclosed home to a renter", "block_to_plots"))


# ======================================================================================================
# Part B: letting by people, and homes for rent on no landlord's block
# ======================================================================================================
def second_home(town, owner):
    """Another home of theirs on a plot, lived in by nobody."""
    from engine.places import place_own_unit, take_plot
    unit = town.new_own_unit(town.needs["housing"], owner)
    place_own_unit(take_plot(town), unit)
    return unit


def second_owner(town, cash):
    """Another resident with a job at the food firm who owns and lives in a home on a plot."""
    from test_places import employ
    from engine.places import place_own_unit, take_plot
    b = town.add_agent(cash=cash)
    employ(b, town.firms_for("food")[0])
    unit = town.new_own_unit(town.needs["housing"], b)
    place_own_unit(take_plot(town), unit)
    b.unit["housing"], unit.occupant = unit, b
    return b


def owner_with_a_tenant(rent=30_000):
    from engine.rtr_owning import letting_of, put_to_let
    from engine.subscriptions import rent_home
    town, owner, unit = owner_in_town(cash=0)
    second = second_home(town, owner)
    put_to_let(town, second, letting_of(town, owner), rent)
    renter = town.add_agent(cash=1_000_000)
    assert rent_home(town, renter, "signup") and renter.unit["housing"] is second
    return town, owner, unit, second, renter


# --- task 6: loose homes for rent -------------------------------------------------------------------------
def test_a_persons_letting_is_paid_like_a_landlord_and_the_money_is_theirs():
    from engine.household import pay_bills
    from engine.rtr_owning import letting_of, put_to_let
    from engine.places import unit_rent
    from engine.subscriptions import price_paid, rent_home
    town, owner, unit = owner_in_town(cash=0)                                # they own and live in `unit`
    for firm in town.firms_for("housing"):
        firm.price = 50_000                                                  # the landlord's homes are dearer
    second = second_home(town, owner)
    put_to_let(town, second, letting_of(town, owner), 30_000)
    renter = town.add_agent(cash=1_000_000)
    assert second in town.to_let and second.owner is owner and second.firm is letting_of(town, owner)
    assert rent_home(town, renter, "signup") and renter.unit["housing"] is second
    assert second not in town.to_let and unit_rent(second) == 30_000 and price_paid(renter, "housing") == 30_000
    pay_bills(town)
    assert owner.cash == 30_000 and renter.cash == 970_000
    assert town.ledger.week_internal["subscription"] == 30_000
    assert second.spot.occupied == 0                                         # a block's count of let homes is its landlord's


def test_the_cheaper_of_a_landlords_home_and_a_persons_is_taken():
    from engine.rtr_owning import letting_of, put_to_let
    from engine.subscriptions import rent_home
    town, owner, unit = owner_in_town(cash=0)
    second = second_home(town, owner)
    put_to_let(town, second, letting_of(town, owner), 60_000)                # dearer than the landlord's $330
    renter = town.add_agent(cash=1_000_000)
    assert rent_home(town, renter, "signup") and renter.unit["housing"] is not second
    assert second in town.to_let


def test_a_tenant_of_a_person_who_misses_four_rents_is_put_out_like_any_tenant():
    from engine.household import pay_bills
    town, owner, unit, second, renter = owner_with_a_tenant()
    renter.cash = 0
    for _ in range(4):
        pay_bills(town)
    assert "housing" not in renter.subs and second.occupant is None and second in town.to_let


def test_what_a_standard_home_lets_for_is_the_cheapest_landlords_price_for_its_place():
    from engine.rtr_owning import going_rent
    town, a, landlord = tenant_with_a_job()
    other = town.add_firm("housing")
    other.price = 28_000
    assert going_rent(town) == 28_000
    spot = a.unit["housing"].spot
    spot.rent_factor = 1.2
    assert going_rent(town, spot) == round(28_000 * 1.2)
    for firm in town.firms_for("housing"):
        firm.alive = False
    town.last_price["housing"] = 31_000
    assert going_rent(town) == 31_000


def test_a_real_town_with_people_letting_homes_keeps_its_weekly_checks():
    from test_town_invariants import run_checked
    from engine.rtr_owning import going_rent, letting_of, owns, put_to_let
    town = Town(load_config(None, ["world=rtr", "population_cap=150", "stop_on_failure=false", "seed=1",
                                   "map_width=7", "map_height=7", *FIFTH_IN_CASH]))   # the town this was written for
    assert run_checked(town, 4 * 52) == []
    owners = [a for a in town.agents if owns(a, "housing")][:5]
    assert len(owners) == 5
    for o in owners:
        put_to_let(town, second_home(town, o), letting_of(town, o), going_rent(town) - 5_000)
    assert run_checked(town, 2 * 52) == []
    assert any(u.occupant is not None for o in owners for u in o.lets.units)   # someone rented one


# --- task 7: one loan on everything a person owns; rent as income; upkeep of what they let --------------
@pytest.mark.fifth_in_cash
def test_the_rent_of_a_let_home_counts_as_income_and_one_loan_covers_all_their_homes():
    from engine.rtr_owning import borrowable, home_value, homes_of
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    wage = owner.wage
    assert owner.income_estimate() == wage + 30_000
    assert homes_of(town, owner) == [unit, second]
    value = home_value(town, unit) + home_value(town, second)
    assert town.bank.home_credit(owner, 0, owned=value) == int(0.8 * value) == 8_640_000
    owner.home_loan = 1_000_000
    assert borrowable(town, owner) == 7_640_000
    renter.cash = 0
    from engine.subscriptions import unsubscribe
    unsubscribe(town, renter, "housing", "test")
    assert owner.income_estimate() == wage                                   # an empty home brings nothing in


def test_an_owner_keeps_up_the_homes_they_let_with_their_own_hours_and_parts():
    from engine.rtr_owning import keep
    town, owner, unit, second, renter = owner_with_a_tenant()
    second.age, second.cond = 520, 0.6
    owner.cash, owner.spare_hours = 1_000_000, 20.0
    keep(town, owner)
    assert second.age == 521 and second.cond > 0.6 and unit.age == 1
    assert owner.spare_hours < 20.0 - 3.0 and owner.cash < 1_000_000         # two homes' upkeep
    owner.cash, owner.spare_hours, before = 0, 0.0, second.cond
    keep(town, owner)
    assert second.cond < before


def test_the_bank_takes_a_let_home_first_with_its_share_of_the_debt_and_the_tenant_stays():
    from engine.rtr_owning import foreclosures, home_value, owns
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    share = round(4_000_000 * home_value(town, second) / (home_value(town, unit) + home_value(town, second)))
    foreclosures(town)
    assert second in town.foreclosed and second.owner is None and second.occupant is renter
    assert owns(owner, "housing") and unit not in town.foreclosed
    assert second.debt == second.ask == share and owner.home_loan == 4_000_000 - share and owner.home_missed == 0
    assert owner.lets.units == [] and renter.subs["housing"] is town.bank_lets and second.firm is town.bank_lets
    assert [e for e in town.rec.events if e["kind"] == "sub_end" and e["agent"] == renter.id] == []   # the tenant never left


def test_rent_on_a_home_the_bank_holds_goes_to_the_bank_and_comes_off_what_is_owed_on_it():
    from engine.household import pay_bills
    from engine.rtr_owning import after_bills, foreclosures
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    debt = second.debt
    town.ledger.start_week()
    pay_bills(town)
    after_bills(town)
    assert town.ledger.week_out.get("loan_recovery") == 30_000
    assert (second.debt, second.ask) == (debt - 30_000, debt - 30_000) and town.bank_lets.cash == 0


def test_only_its_tenant_can_buy_a_let_home_from_the_bank_to_live_in():
    from engine.rtr_owning import foreclosures, owns, sell_foreclosed
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    other = _homeless_worker(town, 50_000_000)
    sell_foreclosed(town)
    assert second.owner is None and second.occupant is renter                # a renter from elsewhere cannot take it
    from test_places import employ
    employ(renter, town.firms_for("food")[0])
    renter.cash = 50_000_000
    sell_foreclosed(town)
    assert owns(renter, "housing") and renter.unit["housing"] is second and "housing" not in renter.subs
    assert second.rent == 0 and second.firm is None and second not in town.foreclosed


def test_with_no_let_home_left_the_bank_takes_their_own_home():
    from engine.rtr_owning import foreclosures, housed
    town, owner, unit, second, renter = owner_with_a_tenant()
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    owner.home_missed = 4
    foreclosures(town)
    assert unit in town.foreclosed and not housed(owner) and owner.home_loan == 0


# --- task 8: building to let -----------------------------------------------------------------------------
def _build_out(town, agent, weeks=100):
    from engine.rtr_owning import work
    for _ in range(weeks):
        agent.spare_hours = 20.0
        work(town, agent)
        if agent.build is None:
            return


@pytest.mark.fifth_in_cash
def test_an_owner_builds_to_let_when_a_newcomer_was_turned_away_and_the_rent_would_cover_it():
    from engine.rtr_owning import consider_building_to_let, going_rent, letting_of, owns
    town, owner, unit = owner_in_town(cash=3_000_000)
    consider_building_to_let(town, owner)
    assert owner.build is None                                               # nobody was turned away
    town.no_home_week = town.week
    consider_building_to_let(town, owner)
    assert owner.build is not None and owner.build.to_let
    assert [e["data"].get("to_let") for e in town.rec.events if e["kind"] == "home_started"] == [True]
    _build_out(town, owner)
    built = letting_of(town, owner).units[0]
    assert built.owner is owner and built.occupant is None and built in town.to_let
    assert built.rent == going_rent(town) and owns(owner, "housing") and owner.unit["housing"] is unit
    assert owner.home_loan == 4_320_000 and owner.cash == 3_000_000 - 1_080_000


@pytest.mark.fifth_in_cash
def test_nobody_builds_to_let_when_the_rent_would_not_cover_the_loan_and_upkeep_with_a_tenth_to_spare():
    from engine.rtr_owning import consider_building_to_let
    town, owner, unit = owner_in_town(cash=3_000_000)
    town.no_home_week = town.week
    for landlord in town.firms_for("housing"):
        landlord.price = 19_000                                              # $190: costs are $174.59 a week; a tenth more is $192
    consider_building_to_let(town, owner)
    assert owner.build is None
    for landlord in town.firms_for("housing"):
        landlord.price = 19_300
    consider_building_to_let(town, owner)
    assert owner.build is not None


def test_only_someone_in_work_who_owns_the_home_they_live_in_builds_to_let_and_one_at_a_time():
    from engine.rtr_owning import consider_building_to_let
    town, a, landlord = tenant_with_a_job(cash=3_000_000)                    # a tenant: they would build to live in
    town.no_home_week = town.week
    consider_building_to_let(town, a)
    assert a.build is None
    town2, owner, unit = owner_in_town(cash=3_000_000)
    town2.no_home_week = town2.week
    owner.employer.staff.remove(owner)
    owner.employer = owner.role = None
    owner.wage = 0
    consider_building_to_let(town2, owner)
    assert owner.build is None
    town3, owner3, unit3 = owner_in_town(cash=9_000_000)
    town3.no_home_week = town3.week
    consider_building_to_let(town3, owner3)
    first = owner3.build
    consider_building_to_let(town3, owner3)
    assert owner3.build is first


def test_someone_turned_away_more_than_a_quarter_ago_is_no_sign_a_home_is_wanted():
    from engine.rtr_owning import consider_building_to_let
    town, owner, unit = owner_in_town(cash=3_000_000)
    town.week = 40
    town.no_home_week = 27
    consider_building_to_let(town, owner)
    assert owner.build is None
    town.no_home_week = 28
    consider_building_to_let(town, owner)
    assert owner.build is not None


def test_a_loose_home_with_no_tenant_follows_the_going_rent_ages_and_is_never_counted_as_lived_in():
    from engine.metrics import weekly_series
    from engine.rtr_owning import after_bills, going_rent, letting_of, put_to_let, quarter
    town, owner, unit = owner_in_town(cash=1_000_000)
    second = second_home(town, owner)
    put_to_let(town, second, letting_of(town, owner), 30_000)
    for landlord in town.firms_for("housing"):
        landlord.price = 25_000
    quarter(town)
    assert second.rent == going_rent(town) == 25_000
    owner.spare_hours, age = 20.0, second.age
    after_bills(town)
    assert second.age == age + 1 and second in town.to_let and second.occupant is None
    rows = {(scope, metric): value for scope, metric, value in weekly_series(town)}
    assert rows[("town", "homes_vacant")] >= 1 and rows[("town", "homes_owned")] == 2


def test_the_bank_takes_an_unfinished_build_to_let_first_and_writes_off_only_what_it_lent_on_it():
    """Found by a whole town (seed 2): the bank took the owner's home for the whole debt and
    left the half-built home to let, which they went on building for three years."""
    from engine.rtr_owning import consider_building_to_let, foreclosures, owns, work
    town, owner, unit = owner_in_town(cash=3_000_000)
    owner.home_loan = 1_000_000                                              # what they owe on the home they live in
    town.no_home_week = town.week
    consider_building_to_let(town, owner)
    owner.spare_hours = 20.0
    work(town, owner)
    lent = owner.build.borrowed
    assert lent > 0 and owner.home_loan == 1_000_000 + lent
    owner.home_missed = 4
    foreclosures(town)
    assert owner.build is None and owns(owner, "housing") and unit not in town.foreclosed
    assert owner.home_loan == 1_000_000 and owner.home_missed == 0
    assert [e["amount"] for e in town.rec.events if e["kind"] == "writeoff"] == [lent]
    assert [e["qty"] for e in town.rec.events if e["kind"] == "foreclosed"] == [None]
    owner.home_missed = 4
    foreclosures(town)                                                       # and then the home, as before
    assert unit in town.foreclosed and owner.home_loan == 0


def test_a_build_to_let_on_the_map_gives_its_plot_back_when_the_bank_takes_it():
    from engine.rtr_owning import consider_building_to_let, foreclosures, work
    town, owner, unit = owner_in_town(cash=3_000_000)
    town.no_home_week = town.week
    consider_building_to_let(town, owner)
    spot = owner.build.spot
    reserved = spot.plots_reserved
    owner.spare_hours = 20.0
    work(town, owner)
    owner.home_missed = 4
    foreclosures(town)
    assert owner.build is None and spot.plots_reserved == reserved - 1


# --- task 9: the rest of the order: owners who let, then landlord firms -----------------------------------
def _out_of_work(agent):
    agent.employer.staff.remove(agent)
    agent.employer = agent.role = None
    agent.wage = 0


def _sold(town, kind="foreclosed_sold"):
    return [e for e in town.rec.events if e["kind"] == kind]


def _never_left(town, tenant):
    return [e for e in town.rec.events if e["kind"] == "sub_end" and e["agent"] == tenant.id] == []


@pytest.mark.fifth_in_cash
def test_what_a_resident_who_owns_would_borrow_to_buy_a_home_to_let():
    from engine.rtr_owning import _spare_cash, letting_terms
    town, a, unit = foreclosed_home(debt=3_000_000)
    owner = second_owner(town, cash=1_000_000)                               # $1,000 a week; their home is worth $54,000
    assert letting_terms(town, owner, 3_000_000, 13_808) == 2_000_000        # payment $42.32, upkeep $83.20, and a tenth
    assert letting_terms(town, owner, 3_000_000, 13_807) is None
    assert letting_terms(town, owner, 15_181_699, 100_000) == 14_181_699     # the most $1,000 a week lets them owe
    assert letting_terms(town, owner, 15_181_700, 100_000) is None
    owner.wage = 1_000_000                                                   # on $10,000 a week the bank's four fifths binds
    assert letting_terms(town, owner, 26_600_000, 10**7) == 25_600_000       # four fifths of both homes: $256,000
    assert letting_terms(town, owner, 26_600_005, 10**7) is None
    owner.wage, owner.home_loan = 100_000, 1_000_000                         # what they owe comes off what they may borrow
    assert letting_terms(town, owner, 3_000_000, 33_000) == 3_000_000 - _spare_cash(town, owner)
    spare = _spare_cash(town, owner)
    assert letting_terms(town, owner, spare + 13_181_699, 100_000) == 13_181_699   # $141,817 their income allows, less $10,000
    assert letting_terms(town, owner, spare + 13_181_700, 100_000) is None
    owner.home_loan = 6_000_000                                              # $67,200 on both homes, $60,000 owed
    assert letting_terms(town, owner, 3_000_000, 33_000) is None
    owner.home_loan = 0
    _out_of_work(owner)
    assert letting_terms(town, owner, 3_000_000, 33_000) is None             # no income, no loan
    owner.cash = 3_000_000
    assert letting_terms(town, owner, 3_000_000, 33_000) == 0                # their own cash covers it


def test_a_foreclosed_home_no_renter_can_buy_goes_to_a_resident_who_owns_and_they_let_it():
    from engine.rtr_owning import going_rent, letting_of, sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    owner = second_owner(town, cash=5_000_000)                               # owns their own home, has a job
    sell_foreclosed(town)
    assert unit.owner is None and unit in town.foreclosed                    # an empty home, and no sign one is wanted
    town.no_home_week = town.week
    town.ledger.start_week()
    sell_foreclosed(town)
    assert unit.owner is owner and unit in letting_of(town, owner).units and unit in town.to_let
    assert owner.unit["housing"] is not unit and unit.rent == going_rent(town) and unit.occupant is None
    assert unit not in town.foreclosed and (unit.debt, unit.ask) == (0, 0) and owner.cash == 2_000_000
    assert town.ledger.week_out == {"loan_recovery": 3_000_000}
    [event] = _sold(town)
    assert (event["agent"], event["firm"], event["data"]["to_let"]) == (owner.id, None, True)


def test_someone_building_or_behind_on_their_loan_does_not_buy_a_home_to_let():
    from engine.entities import OwnBuild
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    owner = second_owner(town, cash=5_000_000)
    owner.home_missed = 1
    sell_foreclosed(town)
    assert unit.owner is None
    owner.home_missed, owner.build = 0, OwnBuild(10.0, 10.0)
    sell_foreclosed(town)
    assert unit.owner is None
    owner.build = None
    sell_foreclosed(town)
    assert unit.owner is owner


def test_a_renter_comes_before_an_owner_and_an_owner_before_a_landlord_firm():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    town.firms_for("housing")[0].cash = 50_000_000
    owner = second_owner(town, cash=5_000_000)
    sell_foreclosed(town)
    assert unit.owner is owner                                               # the landlord had the cash too
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    owner = second_owner(town, cash=5_000_000)
    b = _homeless_worker(town, 5_000_000)                                    # arrived after the owner
    sell_foreclosed(town)
    assert unit.owner is b and b.unit["housing"] is unit and owner.lets is None


def test_a_let_foreclosed_home_keeps_its_tenant_whoever_buys_it():
    from engine.rtr_owning import foreclosures, sell_foreclosed
    from engine.subscriptions import price_paid
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    richest = max(town.firms_for("housing"), key=lambda f: f.cash)
    richest.cash = 50_000_000
    second.ask = 1_000_000
    sell_foreclosed(town)
    assert second.firm is richest and second.occupant is renter and renter.subs["housing"] is richest
    assert price_paid(renter, "housing") == 30_000 and second.rent == 30_000 and _never_left(town, renter)
    assert second in richest.units and second not in town.own_units and second.owner is None
    assert second in second.spot.private_units and second not in town.to_let and second not in town.foreclosed
    assert town.bank_lets.units == [] and renter.id not in town.bank_lets.subs and richest.subs[renter.id] is renter
    [event] = _sold(town)
    assert (event["firm"], event["agent"], event["data"]["tenant"]) == (richest.id, None, renter.id)


def test_a_resident_who_owns_buys_a_let_home_from_the_bank_and_its_tenant_pays_them_from_then_on():
    from engine.household import pay_bills
    from engine.rtr_owning import foreclosures, sell_foreclosed
    from engine.subscriptions import price_paid
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    buyer = second_owner(town, cash=5_000_000)
    second.ask = 1_000_000
    sell_foreclosed(town)                                                    # no sign needed: its rent is being paid
    assert second.owner is buyer and second.firm is buyer.lets and second.occupant is renter
    assert renter.subs["housing"] is buyer.lets and price_paid(renter, "housing") == 30_000
    assert second not in town.to_let and _never_left(town, renter) and town.bank_lets.units == []
    assert buyer.income_estimate() == 100_000 + 30_000 and buyer.cash == 4_000_000
    assert _sold(town)[0]["data"]["tenant"] == renter.id
    town.ledger.start_week()
    pay_bills(town)
    assert buyer.cash == 4_030_000


def test_with_no_renter_and_no_owner_able_a_landlord_firm_takes_a_home_on_a_block_of_plots():
    from engine.rtr_owning import going_rent, sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    landlord = town.firms_for("housing")[0]
    landlord.cash = 50_000_000
    unit.ask = 13_416_001                                                    # ten years of $330 less $72 upkeep: $134,160
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed
    unit.ask = 500_000
    landlord.cash, landlord.last_opex = 899_999, 50_000                      # its reserve is eight weeks: $1 short
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed
    landlord.cash, landlord.last_opex = 50_000_000, 0
    sell_foreclosed(town)
    assert unit.firm is landlord and unit in landlord.units and unit.rent > 0 and unit in town.to_let
    assert unit.spot.kind == "plots" and unit not in unit.spot.units          # it stands where it stood
    assert unit.rent == going_rent(town) and unit not in town.own_units and unit.owner is None
    assert landlord.cash == 49_500_000 and unit not in town.foreclosed


def test_an_empty_foreclosed_home_on_a_landlords_own_block_goes_to_that_landlord_or_to_none():
    from test_places import premises
    from engine.rtr_owning import sell_foreclosed
    town, a, landlord, unit, debt = _bought_then_foreclosed(1_000_000)
    other = premises(town, "housing", 1, 1)
    other.cash, landlord.cash = 50_000_000, 0                                # the block's landlord cannot pay; another could
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed and other.units == []


def _let_home_sold_to_an_owner():
    from engine.rtr_owning import landlord_sales
    town, a, landlord = tenant_with_a_job(cash=0)                            # the tenant cannot pay $134,160
    unit = a.unit["housing"]
    buyer = second_owner(town, cash=14_000_000)
    landlord_sales(town)
    return town, a, landlord, unit, buyer


def test_a_let_home_its_tenant_cannot_buy_is_sold_to_a_resident_who_owns_and_the_tenant_stays():
    from engine.subscriptions import price_paid
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()
    assert unit.owner is buyer and unit.firm is buyer.lets and unit.occupant is a and a.subs["housing"] is buyer.lets
    assert a.unit["housing"] is unit and price_paid(a, "housing") == 33_000 and _never_left(town, a)
    assert unit in unit.spot.private_units and unit not in unit.spot.units and unit.spot.occupied == 0
    assert unit not in landlord.units and a.id not in landlord.subs and unit in town.own_units
    assert landlord.cash == 13_416_000 and buyer.cash == 584_000 and unit not in town.to_let
    [event] = _sold(town, "home_bought")
    assert (event["agent"], event["firm"], event["amount"]) == (buyer.id, landlord.id, 13_416_000)
    assert (event["data"]["to_let"], event["data"]["tenant"]) == (True, a.id)


def test_an_owner_buys_one_home_to_let_in_a_quarter():
    from test_places import employ, tenant
    from engine.rtr_owning import landlord_sales
    town, a, landlord = tenant_with_a_job(cash=0)
    b = tenant(town, a.unit["housing"].spot, cash=0)
    employ(b, a.employer)
    buyer = second_owner(town, cash=40_000_000)
    landlord_sales(town)
    assert len(buyer.lets.units) == 1 and a.unit["housing"].owner is buyer and b.unit["housing"].owner is None


def test_a_landlord_short_of_cash_sells_a_let_home_to_another_landlord_and_the_tenant_stays():
    from test_places import premises
    from engine.rtr_owning import landlord_sales
    from engine.subscriptions import price_paid
    town, a, landlord = tenant_with_a_job(cash=0)
    unit = a.unit["housing"]
    other = premises(town, "housing", 1, 1)
    other.cash = 50_000_000
    landlord_sales(town)
    assert unit.firm is landlord                                             # at ten years of its rent the other gains nothing
    landlord.loan_missed = 1                                                 # short of cash: it asks the home's value, $70,000
    other.cash = 6_999_999
    landlord_sales(town)
    assert unit.firm is landlord                                             # the other cannot pay it
    other.cash = 50_000_000
    landlord_sales(town)
    assert unit.firm is other and unit in other.units and unit not in landlord.units and unit.occupant is a
    assert a.subs["housing"] is other and price_paid(a, "housing") == 33_000 and unit.rent == 33_000
    assert unit in unit.spot.private_units and unit not in town.own_units and unit.owner is None
    assert other.cash == 43_000_000 and landlord.cash == 7_000_000 and _never_left(town, a)
    assert other.subs[a.id] is a and a.id not in landlord.subs
    [event] = _sold(town, "home_bought")
    assert (event["agent"], event["firm"], event["data"]["buyer_firm"], event["data"]["tenant"]) == (
        None, landlord.id, other.id, a.id)


def test_an_empty_home_past_its_year_goes_to_a_resident_who_owns_when_a_home_is_wanted():
    from engine.rtr_owning import going_rent, landlord_sales, quarter
    from engine.subscriptions import unsubscribe
    town, a, landlord = tenant_with_a_job(cash=0)
    empty = _empty_home(town, a)
    unsubscribe(town, a, "housing", "test")                                  # a has a job and no home, and cannot pay $70,000
    empty.empty_since = town.week - 52
    buyer = second_owner(town, cash=8_000_000)
    landlord_sales(town)
    assert empty.owner is None and empty.firm is landlord                    # nobody was turned away: no sign one is wanted
    town.no_home_week = town.week
    landlord_sales(town)
    assert empty.owner is buyer and empty in buyer.lets.units and empty in town.to_let
    assert empty in empty.spot.private_units and empty not in landlord.units
    assert buyer.cash == 1_000_000 and landlord.cash == 7_000_000 and empty.rent == 33_000
    empty.spot.rent_factor = 1.2
    quarter(town)
    assert empty.rent == going_rent(town, empty.spot) == 39_600              # an empty home follows the rent of its place


def _single_home_held_by_a_landlord():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    unit.ask = 500_000
    landlord = town.firms_for("housing")[0]
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord
    return town, a, unit, landlord


def test_the_tenant_of_a_single_home_a_landlord_holds_can_buy_it_like_any_tenant():
    from engine.rtr_owning import let_price, offer_to_tenant, owns
    from engine.subscriptions import subscribe
    town, a, unit, landlord = _single_home_held_by_a_landlord()
    b = _homeless_worker(town, 20_000_000)
    assert subscribe(town, b, landlord, unit=unit) and unit not in town.to_let
    price = let_price(town, landlord, unit)                                  # ten years of its own rent after upkeep
    assert 13_400_000 < price <= 13_416_000
    assert offer_to_tenant(town, landlord, unit)
    assert owns(b, "housing") and b.unit["housing"] is unit and "housing" not in b.subs
    assert unit not in landlord.units and b.id not in landlord.subs and unit in town.own_units
    assert (unit.rent, unit.firm) == (0, None) and unit in unit.spot.private_units
    assert landlord.cash == 49_500_000 + price


def test_a_landlords_single_home_is_let_at_its_own_rent_and_never_as_one_of_its_block():
    from test_places import tenant
    from engine.subscriptions import has_room, subscribe
    town, a, unit, landlord = _single_home_held_by_a_landlord()
    block = landlord.lots[0]
    tenant(town, block)
    tenant(town, block)                                                      # both homes of its block are let
    c = town.add_agent(cash=1_000_000)
    assert not has_room(town, landlord) and not subscribe(town, c, landlord)
    assert subscribe(town, c, landlord, unit=unit) and c.unit["housing"] is unit


def test_a_landlord_taken_over_passes_on_its_single_homes_and_one_that_closes_scraps_them():
    from engine.corporate import _merge, wind_up
    from engine.subscriptions import price_paid, subscribe
    town, a, unit, landlord = _single_home_held_by_a_landlord()
    b = town.add_agent(cash=1_000_000)
    assert subscribe(town, b, landlord, unit=unit)
    rival = town.add_firm("housing")
    rival.cash = 10**9
    _merge(town, landlord, rival, 0)
    assert unit.firm is rival and unit in rival.units and b.subs["housing"] is rival
    assert price_paid(b, "housing") == unit.rent == 33_000 and unit in unit.spot.private_units
    spot = unit.spot
    wind_up(town, rival, "test")
    assert "housing" not in b.subs and unit not in spot.private_units and unit not in town.to_let
    assert unit not in town.own_units and rival.units == []


@pytest.mark.fifth_in_cash
def test_a_let_home_taken_by_the_bank_on_a_landlords_block_goes_back_to_that_landlord_with_its_tenant():
    from test_places import premises
    from engine.rtr_owning import foreclosures, sell_foreclosed
    from engine.subscriptions import price_paid
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()
    buyer.home_loan, buyer.home_missed = 4_000_000, 4
    foreclosures(town)
    assert unit in town.foreclosed and unit.occupant is a
    other = premises(town, "housing", 1, 1)
    other.cash, landlord.cash = 90_000_000, 50_000_000
    unit.ask = 1_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and unit.occupant is a and a.subs["housing"] is landlord and _never_left(town, a)
    assert price_paid(a, "housing") == 33_000 and unit in unit.spot.private_units and unit not in unit.spot.units
    assert landlord.cash == 49_000_000 and other.units == []


@pytest.mark.fifth_in_cash
def test_once_empty_it_goes_back_to_the_landlord_as_a_home_of_the_block():
    from engine.rtr_owning import foreclosures, sell_foreclosed
    from engine.subscriptions import unsubscribe
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()
    buyer.home_loan, buyer.home_missed = 4_000_000, 4
    foreclosures(town)
    unsubscribe(town, a, "housing", "test")                                  # the bank's tenant leaves
    assert unit in town.to_let and unit.firm is town.bank_lets
    town.no_home_week = town.week
    landlord.cash = 50_000_000
    unit.ask = 1_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and unit in landlord.units and unit in unit.spot.units
    assert unit not in unit.spot.private_units and unit.rent == 0 and unit not in town.to_let
    assert town.bank_lets.units == [] and unit not in town.own_units


# --- task 10: the record ---------------------------------------------------------------------------------
def _town_measures(town):
    from engine.metrics import weekly_series
    return {metric: value for scope, metric, value in weekly_series(town) if scope == "town"}


def test_the_weekly_measures_count_homes_bought_homes_people_let_and_what_was_paid():
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()            # a let home, sold to someone who lets it
    m = _town_measures(town)
    assert (m["homes_bought"], m["homes_let_private"], m["small_landlords"], m["homes_loose"]) == (1, 1, 1, 0)
    assert m["home_sales"] == 13_416_000 and m["homes_owned"] == 2           # the buyer's own home, and this one
    town2, a2, landlord2 = tenant_with_a_job(cash=50_000_000)
    from engine.rtr_owning import offer_to_tenant
    assert offer_to_tenant(town2, landlord2, a2.unit["housing"])             # bought by its tenant, to live in
    m = _town_measures(town2)
    assert (m["homes_bought"], m["homes_let_private"], m["small_landlords"]) == (1, 0, 0)


def test_the_weekly_measures_count_single_homes_landlords_hold_and_sales_by_the_bank():
    from engine.rtr_owning import start_week
    town, a, unit, landlord = _single_home_held_by_a_landlord()
    m = _town_measures(town)
    assert (m["homes_loose"], m["homes_bought"], m["homes_let_private"], m["home_sales"]) == (1, 0, 0, 500_000)
    assert m["homes_owned"] == 0 and m["homes"] == 3                         # two on its block and this one, once each
    town.ledger.start_week()
    start_week(town)
    assert _town_measures(town)["home_sales"] == 0                           # a new week


def test_a_home_bought_from_a_landlord_that_goes_back_to_it_is_no_longer_a_bought_home():
    from engine.rtr_owning import sell_foreclosed
    town, a, landlord, unit, debt = _bought_then_foreclosed(1_000_000)
    assert unit.bought
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is landlord and not unit.bought


# --- task 10: whole towns --------------------------------------------------------------------------------
def test_part_b_towns_keep_their_accounts_and_places_and_reach_every_rule(whole_towns):
    problems, seen = whole_towns["map"]
    assert problems == []
    _all_reached(seen, ("home built to let and let", "foreclosed home to an owner who lets it",
                        "let home sold to an owner, tenant staying",
                        "let home sold to another landlord, tenant staying",
                        "let home taken by the bank, tenant staying", "foreclosed home sold with its tenant staying"))


def test_a_town_with_no_map_keeps_its_accounts_and_reaches_the_rules_too(whole_towns):
    problems, seen = whole_towns["no map"]
    assert problems == []
    _all_reached(seen, ("home built to let and let", "foreclosed home to an owner who lets it",
                        "let home sold to an owner, tenant staying",
                        "let home sold to another landlord, tenant staying",
                        "let home taken by the bank, tenant staying", "foreclosed home sold with its tenant staying"))


# --- found by the break-the-rules step: rules no test held ---------------------------------------------------
def test_the_bank_takes_the_newest_of_the_homes_they_let():
    from engine.rtr_owning import foreclosures, letting_of, put_to_let
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    third = second_home(town, owner)
    put_to_let(town, third, letting_of(town, owner), 30_000)
    owner.home_loan, owner.home_missed = 6_000_000, 4
    foreclosures(town)
    assert third in town.foreclosed and second.owner is owner and unit.owner is owner
    assert third.debt == 2_000_000 and owner.home_loan == 4_000_000          # a third of the debt: three homes of one value


def test_missed_rents_go_with_a_tenant_through_a_sale():
    from engine.rtr_owning import foreclosures, landlord_sales, sell_foreclosed
    town, a, landlord = tenant_with_a_job(cash=0)
    a.arrears["housing"] = 2
    buyer = second_owner(town, cash=14_000_000)
    landlord_sales(town)
    assert a.unit["housing"].owner is buyer and a.arrears["housing"] == 2
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    renter.arrears["housing"] = 3
    owner.home_loan, owner.home_missed = 4_000_000, 4
    foreclosures(town)
    town.firms_for("housing")[0].cash = 50_000_000
    second.ask = 1_000_000
    sell_foreclosed(town)
    assert second.firm is town.firms_for("housing")[0] and renter.arrears["housing"] == 3


def test_of_two_landlords_the_one_with_the_most_cash_takes_a_home_on_a_block_of_plots():
    from test_places import premises
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)
    town.no_home_week = town.week
    unit.ask = 500_000
    town.firms_for("housing")[0].cash = 10_000_000
    other = premises(town, "housing", 1, 1)
    other.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is other and other.cash == 49_500_000


@pytest.mark.fifth_in_cash
def test_a_let_home_the_bank_holds_on_a_block_its_landlord_only_leases_goes_to_no_landlord():
    from test_places import premises
    from engine.rtr_owning import foreclosures, sell_foreclosed
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()
    buyer.home_loan, buyer.home_missed = 4_000_000, 4
    foreclosures(town)
    other = premises(town, "housing", 1, 1)
    unit.spot.owner, unit.spot.ground_rent = other, 100                      # the landlord now leases its block
    other.cash, landlord.cash = 90_000_000, 50_000_000
    unit.ask = 1_000_000
    sell_foreclosed(town)
    assert unit in town.foreclosed and unit.firm is town.bank_lets and unit.occupant is a


def test_a_single_home_counts_as_security_for_its_landlords_loan():
    town, a, unit, landlord = _single_home_held_by_a_landlord()
    cfg = town.cfg
    assert len(landlord.units) == 3
    assert landlord.collateral(cfg) == landlord.units_value(cfg, landlord.units) + landlord.land_value


def test_an_empty_home_the_bank_lets_keeps_its_rent_when_the_going_rent_moves():
    from engine.rtr_owning import foreclosures, quarter
    from engine.subscriptions import unsubscribe
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()
    buyer.home_loan, buyer.home_missed = 4_000_000, 4
    foreclosures(town)
    unsubscribe(town, a, "housing", "test")
    landlord.price = 25_000
    quarter(town)
    assert unit in town.foreclosed and unit.rent == 33_000


def test_a_build_to_let_draws_on_the_one_loan_against_all_their_homes():
    from engine.rtr_owning import consider_building_to_let, work
    town, owner, unit = owner_in_town(cash=3_000_000)
    owner.home_loan, owner.home_pay = 4_320_000, 4154                        # all the bank lends on the home they live in
    town.no_home_week = town.week
    consider_building_to_let(town, owner)
    assert owner.build is not None                                           # four fifths of both homes is $86,400
    owner.spare_hours = 20.0
    work(town, owner)
    assert owner.build.borrowed > 0 and owner.home_loan == 4_320_000 + owner.build.borrowed


def test_someone_out_of_work_does_not_build_to_let_even_with_the_cash():
    from test_places import employ
    from engine.rtr_owning import consider_building_to_let
    town, owner, unit = owner_in_town(cash=10_000_000)                       # the materials are $54,000
    town.no_home_week = town.week
    shop = owner.employer
    _out_of_work(owner)
    consider_building_to_let(town, owner)
    assert owner.build is None
    employ(owner, shop)
    consider_building_to_let(town, owner)
    assert owner.build is not None and owner.build.to_let


# ======================================================================================================
# Found by the fresh review of stage 1b (17/11): each of these failed before its fix
def _a_home_vacated_and_sold_in_the_same_quarter():
    """The reviewer's case: a tenant buys an old empty home and leaves; the home they left is
    sold at once (the landlord is short of cash) to someone else, who lives in it."""
    from engine.subscriptions import subscribe, unsubscribe
    town, a, landlord = tenant_with_a_job(cash=1_500_000)
    first, second = landlord.units
    if a.unit["housing"] is first:
        unsubscribe(town, a, "housing", "test")
        assert subscribe(town, a, landlord, unit=second)
    first.age = 35 * 52                                                      # an old home: worth a fifth of a new one
    b = _homeless_worker(town, 6_000_000)
    landlord.cash, landlord.last_opex = 100, 5_000_000                       # short of cash: every home is on offer at its value
    return town, a, b, landlord, first, second


def test_a_home_its_tenant_left_and_someone_else_bought_is_not_offered_on_as_a_let_home():
    from engine.rtr_owning import landlord_sales, owns
    town, a, b, landlord, old, left = _a_home_vacated_and_sold_in_the_same_quarter()
    landlord_sales(town)                                                     # it crashed here
    assert old.owner is a and owns(a, "housing") and left.owner is b and owns(b, "housing")
    assert b.lets is None and left.rent == 0 and landlord.units == []


def test_a_home_that_is_no_longer_the_landlords_is_never_sold_by_it():
    from engine.rtr_owning import _owners, offer_empty_to_let, offer_let, offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=50_000_000)
    unit = a.unit["housing"]
    assert offer_to_tenant(town, landlord, unit)                             # a owns and lives in it now
    buyer = second_owner(town, cash=50_000_000)
    town.no_home_week = town.week
    assert not offer_let(town, landlord, unit, _owners(town))
    assert not offer_empty_to_let(town, landlord, unit, _owners(town))
    assert not offer_to_tenant(town, landlord, unit)                         # nor offered again to the one who owns it
    assert unit.owner is a and unit.occupant is a and buyer.lets is None


def test_the_gain_on_a_home_sold_counts_in_the_landlords_quarter():
    """The sales happen after the quarter's review, so the gain belongs to the quarter that
    has just begun: it was being dropped from every quarter."""
    town, a, landlord, unit, buyer = _let_home_sold_to_an_owner()            # sold for $134,160; worth $70,000
    assert landlord.w_revenue == 6_416_000 and landlord.q_revenue == 6_416_000
    from engine.rtr_owning import offer_to_tenant
    town, a, landlord = tenant_with_a_job(cash=50_000_000)
    assert offer_to_tenant(town, landlord, a.unit["housing"])
    assert landlord.w_revenue == 6_416_000 and landlord.q_revenue == 6_416_000


def test_an_owners_borrowing_is_worked_out_again_once_their_tenant_has_bought_a_home_and_left():
    """The reviewer's case: the owner's rent counted toward what the bank would lend them; in
    the same week their tenant bought a bank home and left, and they then bought a home on
    the strength of a rent they no longer had (and the payment could not be made)."""
    from test_places import employ
    from engine.rtr_owning import _bank_takes, sell_foreclosed
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    shop = town.firms_for("food")[0]
    owner.wage = 35_000
    employ(renter, shop)
    renter.wage, renter.cash = 35_000, 2_000_000
    for f in town.firms_for("housing"):
        f.cash = 0
    town.no_home_week = town.week
    first, cheap, last = (second_home(town, owner) for _ in range(3))
    for u, ask in ((first, 9_500_000), (cheap, 1_000_000), (last, 7_000_000)):
        _bank_takes(town, u, ask)
    sell_foreclosed(town)
    assert cheap.owner is renter and second.occupant is None                 # the tenant bought and left
    assert last.owner is None and last in town.foreclosed                    # on $350 a week alone the owner cannot
    assert owner.home_loan == 0 and owner.cash >= 0


def test_with_no_map_a_home_someone_lets_counts_as_a_home_that_is_free():
    from conftest import empty_town
    from engine.household import review_subscriptions
    from engine.labour import new_worker
    from engine.rtr_owning import letting_of, put_to_let
    from engine.subscriptions import home_available, subscribe
    town = empty_town("world=rtr", "switch_prob=0.0", "move_prob=0.0")
    landlord = town.add_firm("housing")
    town.new_unit(landlord)
    food = town.add_firm("food")
    assert subscribe(town, town.add_agent(cash=1_000_000), landlord)         # the landlord's only home is let
    owner = town.add_agent(cash=0)
    own = town.new_own_unit(town.needs["housing"], owner)
    own.occupant, owner.unit["housing"] = owner, own
    homes = [town.new_own_unit(town.needs["housing"], owner) for _ in range(2)]
    for home in homes:
        put_to_let(town, home, letting_of(town, owner), landlord.price)
    assert home_available(town)
    worker = new_worker(town, food)
    assert worker is not None and worker.unit["housing"] in homes and town.no_home_week is None
    resident = town.add_agent(cash=5_000_000)                                # no home, and plenty of cash
    town.week += 1
    review_subscriptions(town)
    assert resident.unit.get("housing") in homes and town.to_let == []


def test_a_landlord_firm_buys_an_empty_home_from_the_bank_only_when_a_home_is_wanted():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=3_000_000)                          # on a block of plots
    unit.ask = 500_000
    landlord = town.firms_for("housing")[0]
    landlord.cash = 50_000_000
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed                     # nobody was turned away
    town.no_home_week = town.week
    sell_foreclosed(town)
    assert unit.firm is landlord
    town, a, landlord, unit, debt = _bought_then_foreclosed(1_000_000)       # on the landlord's own block
    landlord.cash, town.no_home_week = 50_000_000, None
    sell_foreclosed(town)
    assert unit.firm is None and unit in town.foreclosed
    town.no_home_week = town.week
    sell_foreclosed(town)
    assert unit.firm is landlord


def _no_free_plots(town):
    """Every empty block is taken for something else and every plot is spoken for: nobody can
    start a home of their own."""
    for spot in town.map.spots:
        if spot.kind is None:
            spot.kind = "service"
        elif spot.kind == "plots":
            spot.plots_reserved = town.cfg.homes_per_spot - len(spot.private_units)


@pytest.mark.fifth_in_cash
def test_a_tenant_who_could_build_for_less_a_week_builds_and_does_not_buy_their_home():
    """The design: of buying, building and renting they take the cheapest by weekly cost. The
    reviewer's case: with $50,000 they bought for $134,160 on a loan of about $85,000 when a
    home of their own would have cost them $174.59 a week."""
    from engine.rtr_owning import build_weekly, offer_to_tenant, owns, quarter
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    unit = a.unit["housing"]
    assert build_weekly(town, a) == 9_139 + 8_320                            # the payment on $43,200, and upkeep
    assert not offer_to_tenant(town, landlord, unit) and unit.firm is landlord
    quarter(town)
    assert a.build is not None and not owns(a, "housing") and unit.firm is landlord
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    _no_free_plots(town)
    assert build_weekly(town, a) is None
    assert offer_to_tenant(town, landlord, a.unit["housing"]) and owns(a, "housing")   # no plot: buying is all there is


@pytest.mark.fifth_in_cash
def test_someone_who_can_pay_outright_buys_rather_than_builds():
    from engine.rtr_owning import build_weekly, offer_to_tenant, owns
    town, a, landlord = tenant_with_a_job(cash=50_000_000)
    assert build_weekly(town, a) == 9_139 + 8_320                            # they could build; buying costs upkeep alone
    assert offer_to_tenant(town, landlord, a.unit["housing"]) and owns(a, "housing") and a.home_loan == 0


@pytest.mark.fifth_in_cash
def test_what_building_would_cost_a_week_and_who_can():
    from engine.rtr_owning import build_weekly
    town, a, landlord = tenant_with_a_job(cash=5_000_000)
    assert build_weekly(town, a) == 17_459
    a.cash = 1_080_000 + 4 * 33_000 - 1                                      # a fifth of the materials, less a cent
    assert build_weekly(town, a) is None
    a.cash = 5_000_000
    landlord.price = 18_377                                                  # $174.59 is not clearly under 95% of the rent
    assert build_weekly(town, a) is None
    landlord.price = 18_378
    assert build_weekly(town, a) == 17_459
    a.cash = 10_000_000                                                      # the materials twice over
    assert build_weekly(town, a) == 17_459
    _out_of_work(a)
    assert build_weekly(town, a) is None                                     # no job, whatever their cash
    town2, owner, unit = owner_in_town(cash=5_000_000)
    assert build_weekly(town2, owner) is None                                # they own the home they live in


@pytest.mark.fifth_in_cash
def test_a_buyer_who_could_build_for_less_is_passed_over_for_the_next_in_line():
    from engine.rtr_owning import landlord_sales, owns
    town, a, landlord = tenant_with_a_job(cash=0)
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 52                                       # on offer at its value, $70,000
    b = _homeless_worker(town, 2_000_000)                                    # would borrow $50,000 to buy: building costs less
    c = _homeless_worker(town, 5_000_000)                                    # would borrow $20,000: buying costs less
    landlord_sales(town)
    assert empty.owner is c and owns(c, "housing") and not owns(b, "housing")


@pytest.mark.fifth_in_cash
def test_a_bank_home_goes_to_the_next_in_line_when_the_first_could_build_for_less():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = foreclosed_home(debt=7_000_000)
    b = _homeless_worker(town, 2_000_000)
    c = _homeless_worker(town, 5_000_000)
    sell_foreclosed(town)
    assert unit.owner is c


def test_empty_homes_are_sold_before_tenants_are_offered_the_homes_they_rent():
    """So a tenant who could buy either takes the cheaper: an empty home at its value before
    their own at ten years of its rent."""
    from engine.rtr_owning import landlord_sales, owns
    town, a, landlord = tenant_with_a_job(cash=50_000_000)                   # they could pay for either outright
    rented, empty = a.unit["housing"], _empty_home(town, a)
    empty.empty_since = town.week - 52
    landlord_sales(town)
    assert empty.owner is a and owns(a, "housing") and a.unit["housing"] is empty and a.home_loan == 0
    assert rented.firm is landlord and rented.occupant is None and landlord.cash == 7_000_000


def test_a_landlord_never_sells_a_home_that_is_someone_elses_to_a_renter_either():
    from engine.rtr_owning import _buyers, offer_empty, offer_to_tenant
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    landlord = town.firms_for("housing")[0]
    landlord.loan_missed = 1                                                 # short of cash: it would sell any empty home
    renter.cash = 50_000_000                                                 # the tenant could pay for it outright
    assert not offer_to_tenant(town, landlord, second) and second.owner is owner
    third = second_home(town, owner)                                         # an empty home the owner has to let
    from engine.rtr_owning import _owners, letting_of, offer_empty_to_let, put_to_let
    put_to_let(town, third, letting_of(town, owner), 30_000)
    _homeless_worker(town, 50_000_000)
    assert not offer_empty(town, landlord, third, _buyers(town)) and third.owner is owner
    third.empty_since = town.week - 52                                       # and it has stood empty a year
    town.no_home_week = town.week
    rich = second_owner(town, cash=50_000_000)
    assert not offer_empty_to_let(town, landlord, third, _owners(town)) and third.owner is owner and rich.lets is None


@pytest.mark.fifth_in_cash
def test_the_banks_tenant_who_could_build_for_less_does_not_buy_the_home_from_the_bank():
    from test_places import employ
    from engine.rtr_owning import foreclosures, sell_foreclosed
    town, owner, unit, second, renter = owner_with_a_tenant(rent=30_000)
    employ(renter, town.firms_for("food")[0])
    renter.cash = 2_000_000
    owner.home_loan, owner.home_missed = 14_000_000, 4
    foreclosures(town)                                                       # half the debt goes with the let home: $70,000
    assert second.ask == 7_000_000
    sell_foreclosed(town)                                                    # they would borrow $50,000; building takes $43,200
    assert second.owner is None and second.occupant is renter
    _no_free_plots(town)
    sell_foreclosed(town)
    assert second.owner is renter


def test_whether_a_plot_is_free_agrees_with_taking_one():
    from test_places import premises
    from engine.places import plot_free, take_plot
    town = map_rtr_town()
    shop = premises(town, "food", 6, 6)
    assert plot_free(town) and plot_free(town, shop.spot, 6)
    _no_free_plots(town)
    assert not plot_free(town) and take_plot(town) is None
    far = town.map.at(0, 0)
    far.kind = "plots"                                                       # twelve blocks from the shop
    assert plot_free(town) and not plot_free(town, shop.spot, 6) and plot_free(town, shop.spot, 12)
    assert take_plot(town, shop.spot, 6) is None
    far.plots_reserved = town.cfg.homes_per_spot - 1
    assert plot_free(town)
    far.plots_reserved = town.cfg.homes_per_spot                             # every plot of the block is kept for a build
    assert not plot_free(town) and take_plot(town) is None


@pytest.mark.fifth_in_cash
def test_a_buyer_in_line_who_has_no_plot_to_build_on_buys():
    from engine.rtr_owning import landlord_sales, owns
    town, a, landlord = tenant_with_a_job(cash=0)
    empty = _empty_home(town, a)
    empty.empty_since = town.week - 52
    b = _homeless_worker(town, 2_000_000)                                    # building would cost less, had they a plot
    _no_free_plots(town)
    landlord_sales(town)
    assert empty.owner is b and owns(b, "housing")


def test_with_no_map_the_cheaper_of_a_landlords_home_and_one_someone_lets_is_taken():
    from conftest import empty_town
    from engine.rtr_owning import letting_of, put_to_let
    from engine.subscriptions import rent_home, subscribe
    town = empty_town("world=rtr")
    landlord = town.add_firm("housing")
    for _ in range(3):
        town.new_unit(landlord)
    owner = town.add_agent(cash=0)
    own = town.new_own_unit(town.needs["housing"], owner)
    own.occupant, owner.unit["housing"] = owner, own
    cheap, dear = (town.new_own_unit(town.needs["housing"], owner) for _ in range(2))
    put_to_let(town, cheap, letting_of(town, owner), landlord.price - 1_000)
    put_to_let(town, dear, letting_of(town, owner), landlord.price + 1_000)
    first, second = town.add_agent(cash=1_000_000), town.add_agent(cash=1_000_000)
    assert rent_home(town, first, "signup") and first.unit["housing"] is cheap
    assert rent_home(town, second, "signup") and second.unit["housing"].firm is landlord
    assert town.to_let == [dear]
