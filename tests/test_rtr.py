"""The Right to Repair world, stage 1a: building and owning your own. A town run with
world=wef must stay the town it was; a town run with world=rtr gets the rules here."""

import json
import sqlite3

import pytest
from conftest import empty_town, map_town, what_happened

from engine.config import load_config
from engine.town import Town

# Records made by the code at 958d19f, before any of RTR was built (ledger of 16/11).
WEF_PINS = [
    (["seed=1", "stop_on_failure=false"], ("889a87a96629fed5", 14113)),
    (["seed=5", "stop_on_failure=false", "founder_arrival_rate=0.25", "resident_founder_rate=0.2"],
     ("f92ac66689bf0bc5", 25843)),
]


def rtr_town(*overrides):
    """Rules but no founders and no map, in the RTR world."""
    return empty_town("world=rtr", *overrides)


def map_rtr_town(*overrides):
    return map_town("world=rtr", *overrides)


# --- the world dial ------------------------------------------------------------------------------
def test_the_world_is_wef_unless_asked_and_only_two_worlds_exist():
    assert load_config().world == "wef" and not load_config().rtr
    assert load_config("rtr/settings.json").rtr and load_config(None, ["world=rtr"]).rtr
    with pytest.raises(ValueError):
        load_config(None, ["world=mars"])


def test_the_rtr_dials_have_the_designs_values():
    cfg = load_config()
    assert (cfg.free_hours, cfg.job_hours) == (60.0, 40.0)
    assert (cfg.mortgage_ltv, cfg.mortgage_weeks, cfg.mortgage_income_share) == (1.0, 1040, 0.30)   # the design's 0.80 until 18/11 (J)
    assert cfg.foreclosed_price_drop == 0.05


@pytest.mark.parametrize("overrides, record", WEF_PINS)
def test_a_wef_town_is_the_town_it_was_before_rtr_was_built(overrides, record):
    town = Town(load_config(None, overrides))
    for _ in range(6 * 52):
        town.step()
    assert what_happened(town) == record


# --- spare time -----------------------------------------------------------------------------------
def test_spare_time_is_what_a_job_and_the_road_leave():
    from engine.rtr_owning import spare_hours
    town = rtr_town()
    a = town.add_agent()
    assert spare_hours(town.cfg, a) == 60.0
    a.role, a.travel_hours = "staff", 6.5
    assert spare_hours(town.cfg, a) == 13.5
    a.travel_hours = 30.0
    assert spare_hours(town.cfg, a) == 0.0


def test_the_week_starts_by_giving_everyone_their_spare_hours():
    from engine.rtr_owning import start_week
    town = rtr_town()
    a, b = town.add_agent(), town.add_agent()
    b.role = "staff"
    start_week(town)
    assert (a.spare_hours, b.spare_hours) == (60.0, 20.0)


# --- things a person owns, and plots -----------------------------------------------------------------
def test_an_owned_unit_belongs_to_no_firm():
    from engine.rtr_owning import housed, owns
    town = rtr_town()
    a = town.add_agent()
    unit = town.new_own_unit(town.needs["appliances"], a)
    a.unit["appliances"] = unit
    assert unit.firm is None and unit.owner is a and owns(a, "appliances")
    assert all(unit not in f.units for f in town.firms) and unit in town.own_units
    assert not housed(a)


def test_someone_with_a_rented_home_or_a_home_of_their_own_is_housed():
    from engine.rtr_owning import housed
    from engine.subscriptions import subscribe
    town = rtr_town()
    landlord = town.add_firm("housing")
    town.new_unit(landlord)
    renter, owner, nobody = town.add_agent(), town.add_agent(), town.add_agent()
    subscribe(town, renter, landlord)
    owner.unit["housing"] = town.new_own_unit(town.needs["housing"], owner)
    assert housed(renter) and housed(owner) and not housed(nobody)


def test_plots_fill_a_block_of_eight_then_take_another_and_stop_when_land_is_gone():
    from engine.places import take_plot
    town = map_rtr_town("map_width=3", "map_height=3")
    taken = [take_plot(town) for _ in range(9)]
    assert len({s.id for s in taken[:8]}) == 1 and taken[8].id != taken[0].id
    assert taken[0].kind == "plots" and taken[0].plots_reserved == 8
    assert taken[0].owner is None and taken[0].user is None
    for spot in town.map.spots:                      # the rest of the land goes to someone else
        if spot.kind is None:
            spot.kind = "service"
    assert [take_plot(town) for _ in range(7)].count(None) == 0      # seven plots left on the second block
    assert take_plot(town) is None


def test_a_finished_home_takes_its_reserved_plot():
    from engine.places import place_own_unit, take_plot
    town = map_rtr_town()
    a = town.add_agent()
    spot = take_plot(town)
    unit = town.new_own_unit(town.needs["housing"], a)
    place_own_unit(spot, unit)
    assert spot.private_units == [unit] and unit.spot is spot and spot.plots_reserved == 0 and spot.units == []


def test_with_no_map_there_are_no_plots():
    from engine.places import take_plot
    assert take_plot(rtr_town()) is None


# --- an appliance set of their own -------------------------------------------------------------------
def _renter_of_a_set(cash=1_000_000):
    from engine.subscriptions import subscribe
    town = rtr_town("switch_prob=0.0")
    firm = town.add_firm("appliances")
    town.new_unit(firm)
    a = town.add_agent(cash=cash)
    assert subscribe(town, a, firm)
    return town, a, firm


def _own_set(town, a):
    """Give them a set of their own in place of the rented one."""
    from engine.subscriptions import unsubscribe
    unit = town.new_own_unit(town.needs["appliances"], a)
    unsubscribe(town, a, "appliances", "owns")
    a.unit["appliances"] = unit
    unit.occupant = a
    return unit


def test_someone_renting_a_set_builds_their_own_when_it_is_clearly_cheaper():
    from engine.rtr_owning import consider_own_set, own_cost_week, owns, work
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
    assert a.spare_hours == 4.0 and a.unit["appliances"].occupant is a
    assert [e["kind"] for e in town.rec.events if e["kind"].startswith("own_")] == ["own_started", "own_built"]


def test_without_the_money_for_parts_they_go_on_renting():
    from engine.rtr_owning import consider_own_set
    town, a, firm = _renter_of_a_set(cash=100_000)
    consider_own_set(town, a)
    assert a.set_hours_left is None and "appliances" in a.subs and a.cash == 100_000


def test_someone_in_work_may_borrow_for_the_parts_but_keeps_four_weeks_of_bills():
    from engine.rtr_owning import consider_own_set
    town, a, firm = _renter_of_a_set(cash=300_000)
    a.role, a.wage = "staff", 100_000
    consider_own_set(town, a)
    assert a.set_hours_left == 20.0
    assert a.cash == 4 * firm.price and a.loan == 540_000 - (300_000 - 4 * firm.price)


def test_an_owned_set_is_kept_up_with_their_hours_and_parts_and_wears_without_them():
    from engine.rtr_owning import keep
    from engine.production import upkeep_need
    town, a, firm = _renter_of_a_set()
    unit = _own_set(town, a)
    unit.age, unit.cond = 260, 0.6
    labour, goods = upkeep_need(town.cfg, unit)
    a.spare_hours, cash = 20.0, a.cash
    keep(town, a)
    assert unit.age == 261 and unit.cond > 0.6
    assert a.cash == cash - round(goods * 13_500) and a.spare_hours == pytest.approx(20.0 - labour * 40.0)
    a.cash, a.spare_hours, before = 0, 0.0, unit.cond
    keep(town, a)
    assert unit.cond < before                                                # no parts, no hours: it wears


def test_nothing_is_billed_for_what_they_own_and_it_counts_as_met():
    from engine.household import dues, pay_bills, review_subscriptions
    town, a, firm = _renter_of_a_set()
    unit = _own_set(town, a)
    assert dues(town, a) == []
    pay_bills(town)
    assert a.met["appliances"] is True
    review_subscriptions(town)
    assert "appliances" not in a.subs and a.unit["appliances"] is unit       # they do not rent one as well


def test_a_set_past_keeping_is_replaced_by_building_another():
    from engine.rtr_owning import keep, owns, work
    town, a, firm = _renter_of_a_set()
    old = _own_set(town, a)
    old.age = 10 * 52                                                        # best condition 0.4: under the line
    a.spare_hours = 20.0
    keep(town, a)
    assert a.set_hours_left == 20.0 and a.unit["appliances"] is old          # they use the old one meanwhile
    a.spare_hours = 20.0
    work(town, a)
    assert owns(a, "appliances") and a.unit["appliances"] is not old and old not in town.own_units


# --- the loan against a home -------------------------------------------------------------------------
@pytest.mark.fifth_in_cash
def test_the_bank_lends_four_fifths_of_the_price_if_the_payment_fits_their_income():
    town = rtr_town()
    a = town.add_agent()
    a.role, a.wage = "staff", 100_000
    assert town.bank.home_credit(a, 5_400_000) == 4_320_000                 # 80% of $54,000
    assert town.bank.home_first_payment(4_320_000) == 4154 + 4985           # instalment and a week's interest at 6%
    a.wage = 20_000                                                          # 30% of $200 is $60 a week
    credit = town.bank.home_credit(a, 5_400_000)
    assert 0 < credit < 4_320_000 and town.bank.home_first_payment(credit) <= 6_000
    assert town.bank.home_first_payment(credit + 100) > 6_000                # and it is the most that fits
    a.role, a.wage = None, 0
    assert town.bank.home_credit(a, 5_400_000) == 0                          # no income, no loan (J)


@pytest.mark.fifth_in_cash
def test_what_is_already_owed_on_the_home_comes_off_what_the_bank_will_lend():
    town = rtr_town()
    a = town.add_agent()
    a.role, a.wage = "staff", 100_000
    assert town.bank.lend_home(a, 1_000_000, 5_400_000) == 1_000_000
    assert town.bank.home_credit(a, 5_400_000) == 3_320_000
    assert town.bank.lend_home(a, 9_000_000, 5_400_000) == 3_320_000 and a.home_loan == 4_320_000
    assert a.home_pay == 4154
    assert [e["amount"] for e in town.rec.events if e["kind"] == "home_loan"] == [1_000_000, 3_320_000]


def test_a_home_loan_is_paid_like_the_rent_and_a_missed_week_is_a_blow():
    from engine.household import dues, pay_bills
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
    assert a.home_loan == 4_320_000 - 4154 + round((4_320_000 - 4154) * 0.06 / 52)   # the unpaid interest is added


# --- building a home on a plot ------------------------------------------------------------------------
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
    from engine.rtr_owning import build_cost, consider_building
    town, a, landlord = _tenant_with_a_job()
    assert build_cost(town) == 5_400_000
    consider_building(town, a)
    assert a.build is not None and (a.build.hours_left, a.build.goods_left) == (1200.0, 500.0)
    assert a.build.spot.kind == "plots" and a.build.spot.plots_reserved == 1
    assert "housing" in a.subs                                               # they rent until it is finished
    assert [e["kind"] for e in town.rec.events if e["kind"] == "home_started"] == ["home_started"]
    consider_building(town, a)
    assert a.build.spot.plots_reserved == 1                                  # one build at a time


def test_no_job_no_loan_no_build():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job()
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    consider_building(town, a)
    assert a.build is None


@pytest.mark.fifth_in_cash
def test_too_little_cash_for_their_fifth_and_they_go_on_renting():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job(cash=1_000_000)                  # a fifth is $10,800, plus four weeks of rent
    consider_building(town, a)
    assert a.build is None


def test_with_no_land_left_nobody_starts_a_home():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job()
    for spot in town.map.spots:
        if spot.kind is None:
            spot.kind = "service"
    consider_building(town, a)
    assert a.build is None


@pytest.mark.fifth_in_cash
def test_each_hour_worked_buys_its_parts_a_fifth_from_cash_and_the_home_is_theirs_at_the_end():
    from engine.rtr_owning import consider_building, owns, work
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
    assert a.unit["housing"].occupant is a
    assert town.ledger.total_out["import"] == 5_400_000                      # every part came from outside
    assert (a.home_loan, a.cash) == (4_320_000, 1_500_000 - 1_080_000)       # four fifths the bank's, a fifth theirs
    assert [e["kind"] for e in town.rec.events if e["kind"].startswith("home_")][-1] == "home_built"


@pytest.mark.fifth_in_cash
def test_someone_who_loses_their_job_half_way_keeps_the_plot_and_builds_on_only_with_cash():
    from engine.rtr_owning import consider_building, work
    town, a, landlord = _tenant_with_a_job(cash=1_500_000)
    consider_building(town, a)
    spot = a.build.spot
    for _ in range(30):
        a.spare_hours = 20.0
        work(town, a)
    owed, left = a.home_loan, a.build.hours_left
    assert (owed, left) == (30 * 72_000, 600.0)
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    a.spare_hours = 60.0
    work(town, a)
    assert a.home_loan == owed and a.build is not None and a.build.spot is spot    # no more is lent; the plot is theirs
    assert a.build.hours_left == left - 60.0                                      # their cash still buys parts
    a.cash, a.spare_hours, left = 0, 60.0, a.build.hours_left
    work(town, a)
    assert a.build.hours_left == left                                             # no cash, no parts, no work


def test_an_owner_is_not_moved_by_the_search_for_a_cheaper_home():
    from engine.household import review_subscriptions
    from engine.places import place_own_unit, take_plot
    from engine.subscriptions import unsubscribe
    town, a, landlord = _tenant_with_a_job(2_000_000, "move_prob=1.0")
    unit = town.new_own_unit(town.needs["housing"], a)
    place_own_unit(take_plot(town), unit)
    unsubscribe(town, a, "housing", "owns")
    a.unit["housing"] = unit
    unit.occupant = a
    review_subscriptions(town)
    assert a.unit["housing"] is unit and "housing" not in a.subs


def test_a_well_off_owner_is_not_sent_looking_for_a_better_rented_home():
    from engine.household import review_subscriptions
    from engine.places import place_own_unit, take_plot
    from engine.subscriptions import unsubscribe
    town, a, landlord = _tenant_with_a_job(50_000_000)
    unit = town.new_own_unit(town.needs["housing"], a)
    place_own_unit(take_plot(town), unit)
    unsubscribe(town, a, "housing", "owns")
    a.unit["housing"], unit.occupant = unit, a
    a.wage = 1_000_000                                                       # well-off by any measure
    review_subscriptions(town)
    assert a.well_off and not a.wants_better and a.unit["housing"] is unit


# --- an owner's upkeep, and how owning counts in wellbeing ---------------------------------------------
def _owner(cash=0):
    from engine.places import place_own_unit, take_plot
    from engine.subscriptions import unsubscribe
    town, a, landlord = _tenant_with_a_job(cash=cash)
    unit = town.new_own_unit(town.needs["housing"], a)
    place_own_unit(take_plot(town), unit)
    unsubscribe(town, a, "housing", "owns")
    a.unit["housing"], unit.occupant = unit, a
    return town, a, unit


@pytest.mark.fifth_in_cash
def test_owning_does_not_shrink_the_basket_and_what_they_could_borrow_counts_as_cushion():
    from engine.household import basket_cost, update_agents
    from engine.rtr_owning import borrowable
    town, a, unit = _owner()
    renter = town.add_agent()
    assert basket_cost(town, a) == basket_cost(town, renter)                 # both at the going rent
    assert borrowable(town, a) == 4_320_000 and borrowable(town, renter) == 0
    a.home_loan = 4_000_000
    assert borrowable(town, a) == 320_000
    unit.age = 25 * 52                                                       # half its life gone: worth half
    assert borrowable(town, a) == 0
    a.home_loan, unit.age = 0, 0
    update_agents(town)
    with_home = a.security
    unit.owner = unit.occupant = None                                        # the same person with no home to borrow on
    a.unit.pop("housing")
    a.security = town.cfg.security_start
    update_agents(town)
    assert a.security < with_home


def test_a_home_loan_paid_on_time_is_not_counted_as_debt():
    from engine.household import update_agents
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
    from engine.rtr_owning import keep
    town, a, unit = _owner(cash=1_000_000)
    unit.age, unit.cond = 520, 0.7
    a.spare_hours = 20.0
    keep(town, a)
    assert unit.cond > 0.7 and town.ledger.week_out.get("import", 0) > 0
    a.cash, a.spare_hours, before = 0, 0.0, unit.cond
    keep(town, a)
    assert unit.cond < before


def test_what_an_owner_must_find_each_week_is_food_and_the_loan_not_a_rent():
    from engine.household import essentials_cost
    from engine.subscriptions import cheapest_prices
    town, a, unit = _owner()
    cheapest = cheapest_prices(town)
    assert essentials_cost(town, a, cheapest) == cheapest["food"]            # no rent; nothing owed on the home
    a.home_loan, a.home_pay = 4_320_000, 4154
    assert essentials_cost(town, a, cheapest) == cheapest["food"] + 4154 + 4985


# --- foreclosure, and the sale for the debt -----------------------------------------------------------
def _foreclosed(debt=3_000_000):
    from engine.rtr_owning import foreclose
    town, a, unit = _owner()
    a.home_loan, a.home_pay, a.home_missed = debt, 2885, 4
    foreclose(town, a)
    return town, a, unit


def _buyer(town, cash):
    from test_places import employ, tenant
    buyer = tenant(town, town.firms_for("housing")[0].lots[0], cash=cash)
    employ(buyer, town.firms_for("food")[0])
    return buyer


def test_four_missed_payments_and_the_bank_takes_the_home():
    from engine.rtr_owning import foreclosures, housed
    town, a, unit = _owner()
    a.home_loan, a.home_pay, a.home_missed = 3_000_000, 2885, 3
    foreclosures(town)
    assert unit.owner is a                                                   # three missed: not yet
    a.home_missed, security = 4, a.security
    foreclosures(town)
    assert unit.owner is None and unit.occupant is None and (unit.debt, unit.ask) == (3_000_000, 3_000_000)
    assert (a.home_loan, a.home_pay, a.home_missed) == (0, 0, 0) and "housing" not in a.unit and a.security < security
    assert unit in town.foreclosed and not housed(a) and unit.since == town.week
    assert [e["amount"] for e in town.rec.events if e["kind"] == "foreclosed"] == [3_000_000]


@pytest.mark.fifth_in_cash
def test_a_build_with_a_loan_on_it_is_lost_and_the_debt_written_off_at_once():
    from engine.rtr_owning import consider_building, foreclosures, work
    town, a, landlord = _tenant_with_a_job(cash=1_500_000)
    consider_building(town, a)
    spot = a.build.spot
    a.spare_hours = 20.0
    work(town, a)
    a.home_missed = 4
    foreclosures(town)
    assert a.build is None and spot.plots_reserved == 0 and a.home_loan == 0
    assert town.bank.writeoffs_total == 72_000 and town.foreclosed == []
    assert "housing" in a.subs                                               # they still rent


def test_a_renter_who_can_borrow_for_it_buys_it_for_the_debt_and_moves_in():
    from engine.rtr_owning import owns, sell_foreclosed
    town, a, unit = _foreclosed()
    buyer = _buyer(town, 1_000_000)
    rented = buyer.unit["housing"]
    sell_foreclosed(town)
    assert unit.owner is buyer and owns(buyer, "housing") and "housing" not in buyer.subs
    assert unit.occupant is buyer and rented.occupant is None
    assert town.ledger.week_out == {"loan_recovery": 3_000_000}
    assert (buyer.cash, buyer.home_loan) == (132_000, 2_132_000)             # they keep four weeks of their $330 rent
    assert unit not in town.foreclosed and town.bank.writeoffs_total == 0
    assert [e["kind"] for e in town.rec.events if e["kind"] in ("home_loan", "foreclosed_sold")] == ["home_loan", "foreclosed_sold"]


@pytest.mark.fifth_in_cash
def test_nobody_without_a_job_or_without_the_means_buys_it():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    poor = _buyer(town, 100_000)                                             # a job, but the bank's four fifths is not enough
    jobless = _buyer(town, 5_000_000)
    jobless.employer.staff.remove(jobless)
    jobless.employer = jobless.role = None
    jobless.wage = 0
    sell_foreclosed(town)
    assert unit.owner is None and unit in town.foreclosed


def test_unsold_it_stands_empty_and_the_price_falls_a_twentieth_each_quarter():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    town.week = unit.since + 13
    sell_foreclosed(town)
    assert unit.ask == 2_850_000 and unit.owner is None
    town.week = unit.since + 20
    sell_foreclosed(town)
    assert unit.ask == 2_850_000                                             # only at a quarter's end
    town.week = unit.since + 26
    sell_foreclosed(town)
    assert unit.ask == 2_707_500
    unit.ask = 1
    town.week = unit.since + 39
    sell_foreclosed(town)
    assert unit.ask == 1                                                     # never below a cent


def test_the_banks_loss_is_written_off_once_when_it_sells_below_the_debt():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    unit.ask = 2_000_000
    buyer = _buyer(town, 2_500_000)
    sell_foreclosed(town)
    assert unit.owner is buyer and town.bank.writeoffs_total == 1_000_000 and buyer.home_loan == 0
    sell_foreclosed(town)
    assert town.bank.writeoffs_total == 1_000_000


def test_someone_foreclosed_on_is_refused_credit_as_after_any_default():
    town, a, unit = _foreclosed()
    assert a.credit_block_until == town.week + town.cfg.default_block_weeks
    assert town.bank.home_credit(a, 5_400_000) == 0


# --- the record ---------------------------------------------------------------------------------------
def test_an_rtr_run_records_who_owns_and_a_wef_run_does_not(tmp_path):
    from engine.runner import run
    small = ["population_cap=60", "years=3", "seed=3", "stop_on_failure=false"]
    rtr = run(load_config(None, small + ["world=rtr"]), out_root=tmp_path / "rtr", quiet=True)
    wef = run(load_config(None, small), out_root=tmp_path / "wef", quiet=True)

    def read(folder, sql):
        con = sqlite3.connect(folder / "run.sqlite")
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()

    def metrics(folder):
        return {m for (m,) in read(folder, "SELECT DISTINCT metric FROM series WHERE scope = 'town'")}

    new = {"homes_owned", "homes_foreclosed", "homes_building", "sets_owned", "home_loans",
           "homes_bought", "homes_let_private", "small_landlords", "homes_loose", "home_sales"}    # the last five: stage 1b
    assert new <= metrics(rtr) and not (new & metrics(wef))
    summary = json.loads((rtr / "summary.json").read_text())
    assert summary["world"] == "rtr" and summary["sets_owned"] > 0 and "foreclosures" in summary
    assert {"homes_bought", "homes_let_private", "small_landlords"} <= set(summary)
    wef_summary = json.loads((wef / "summary.json").read_text())
    assert wef_summary["world"] == "wef" and "sets_owned" not in wef_summary
    owned = read(rtr, "SELECT COUNT(*) FROM units WHERE firm IS NULL AND owner IS NOT NULL")[0][0]
    assert owned > 0 and read(wef, "SELECT COUNT(*) FROM units WHERE firm IS NULL")[0][0] == 0
    assert (rtr / "dashboard.html").exists() and (rtr / "town.html").exists()     # the pages still build


def test_a_block_of_plots_is_written_to_the_record_as_a_block_of_owned_homes(tmp_path):
    from engine.places import place_own_unit, take_plot
    from engine.recorder import Recorder
    cfg = load_config(None, ["world=rtr", "population_cap=30"])
    path = tmp_path / "run.sqlite"
    rec = Recorder(path, cfg, run_id="plots")
    town = Town(cfg, rec)
    owner = town.agents[0]
    spot = take_plot(town)
    unit = town.new_own_unit(town.needs["housing"], owner)
    place_own_unit(spot, unit)
    take_plot(town)                                                           # and one more plot kept for a build
    town.week = 13
    rec.snapshot(town) if hasattr(rec, "snapshot") else town._record()
    rec.finish("survived", {})
    con = sqlite3.connect(path)
    try:
        row = con.execute("SELECT kind, label, owner, user, homes, let, building FROM places "
                          "WHERE week = 13 AND spot = ?", (spot.id,)).fetchone()
    finally:
        con.close()
    assert row == ("homes", "owned", None, None, 1, 0, 1)


# --- whole towns --------------------------------------------------------------------------------------
def test_an_rtr_town_keeps_its_accounts_and_places_and_reaches_every_rule_of_stage_1a():
    import collections
    from test_town_invariants import run_checked
    seen = collections.Counter()
    for seed in (2, 3):
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


def test_the_same_rtr_town_twice_is_the_same_town():
    def record(seed):
        town = Town(load_config(None, ["world=rtr", "population_cap=120", "seed=3", "stop_on_failure=false"]))
        for _ in range(5 * 52):
            town.step()
        return what_happened(town)
    assert record(3) == record(3)


# --- the review of 17/11: what stage 1a got wrong, now pinned -------------------------------------------
def test_short_of_credit_for_the_parts_nothing_is_borrowed_and_no_set_is_started():
    from engine.rtr_owning import consider_own_set
    town, a, firm = _renter_of_a_set(cash=50_000)
    a.role, a.wage, a.loan = "staff", 100_000, 600_000             # they could borrow $2,000 more; the parts are $5,400
    consider_own_set(town, a)
    assert (a.cash, a.loan, a.set_hours_left) == (50_000, 600_000, None)
    assert [e for e in town.rec.events if e["kind"] == "loan"] == []


def test_someone_with_no_set_at_all_builds_one_if_they_can_pay():
    from engine.rtr_owning import consider_own_set
    town = rtr_town()
    a = town.add_agent(cash=1_000_000)                              # nobody rents sets in this town
    consider_own_set(town, a)
    assert a.set_hours_left == 20.0 and a.cash == 1_000_000 - 540_000


def test_a_plot_is_taken_within_reach_of_their_work_or_not_at_all():
    from engine.rtr_owning import consider_building
    from engine.places import dist, reach, take_plot
    town, a, landlord = _tenant_with_a_job()
    for spot in town.map.spots:                                      # the only free land is in the far corner
        if spot.kind is None and dist(spot, town.map.at(0, 0)) > 1:
            spot.kind = "service"
    assert dist(town.map.at(0, 0), a.employer.spot) > reach(town, a)
    consider_building(town, a)
    assert a.build is None and all(s.kind != "plots" for s in town.map.spots)
    spot = take_plot(town, a.employer.spot, 30)                       # with a ride they could get there
    assert spot is not None and dist(spot, a.employer.spot) <= 30


def test_a_builder_keeps_four_weeks_of_bills_in_hand_while_building():
    from engine.household import dues
    from engine.rtr_owning import consider_building, work
    town, a, landlord = _tenant_with_a_job(cash=1_500_000)
    consider_building(town, a)
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0                                                       # out of work: no more is lent
    for _ in range(40):
        a.spare_hours = 60.0
        work(town, a)
    assert a.build is not None and a.cash >= 4 * sum(d[3] for d in dues(town, a)) - 1
    assert a.cash < 4 * sum(d[3] for d in dues(town, a)) + 300_000    # and they did spend down to it


@pytest.mark.fifth_in_cash
def test_what_an_owner_could_borrow_counts_only_if_the_bank_would_lend_it():
    from engine.rtr_owning import borrowable
    town, a, unit = _owner()
    assert borrowable(town, a) == 4_320_000
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    assert borrowable(town, a) == 0                                   # no income, no loan (J)
    a.role, a.wage, a.credit_block_until = "staff", 100_000, town.week + 10
    assert borrowable(town, a) == 0                                   # nor while the bank refuses them


def test_a_home_the_bank_holds_ages_and_wears_like_any_empty_home():
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    age, cond = unit.age, unit.cond
    sell_foreclosed(town)
    assert unit.age == age + 1 and unit.cond < cond


def test_the_rtr_dials_are_refused_when_they_cannot_work():
    for bad in ("mortgage_weeks=0", "mortgage_ltv=1.5", "mortgage_ltv=-0.1", "foreclosed_price_drop=1.0",
                "job_hours=0", "mortgage_income_share=-1"):
        with pytest.raises(ValueError):
            load_config(None, [bad])


def test_the_most_the_bank_lends_on_income_is_found_at_once_and_is_the_most():
    town = rtr_town()
    a = town.add_agent()
    a.role = "staff"
    for wage in (7_300, 20_000, 55_555, 100_000, 912_345):
        a.wage = wage
        credit = town.bank.home_credit(a, 10**12)
        afford = 0.30 * wage
        assert town.bank.home_first_payment(credit) <= afford < town.bank.home_first_payment(credit + 1040)


# --- tests the review showed would pass with their rule broken, made to bite ---------------------------
def test_someone_with_plenty_of_cash_and_no_job_does_not_build():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job(cash=50_000_000)
    a.employer.staff.remove(a)
    a.employer = a.role = None
    a.wage = 0
    consider_building(town, a)
    assert a.build is None


@pytest.mark.fifth_in_cash
def test_the_fifth_and_the_four_weeks_are_both_needed_to_start_a_home():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job(cash=1_080_000 + 4 * 33_000 - 1)
    consider_building(town, a)
    assert a.build is None
    a.cash += 1
    consider_building(town, a)
    assert a.build is not None


def test_nobody_builds_or_buys_when_their_rent_is_already_as_cheap():
    from engine.rtr_owning import consider_building, consider_own_set, sell_foreclosed
    town, a, landlord = _tenant_with_a_job()
    landlord.price = 9_000                                           # $90 a week: owning would cost more
    consider_building(town, a)
    assert a.build is None
    town2, b, unit = _foreclosed()
    buyer = _buyer(town2, 3_500_000)
    town2.firms_for("housing")[0].price = 2_000
    sell_foreclosed(town2)
    assert unit.owner is None
    town3, c, firm = _renter_of_a_set()
    firm.price = 1_000                                               # $10 a week for a rented set
    consider_own_set(town3, c)
    assert c.set_hours_left is None


def test_a_buyer_must_be_able_to_reach_their_work_from_the_home():
    from test_places import block, employ, premises, tenant
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    far = premises(town, "entertainment", 0, 12)                     # a job in the far corner, beyond a walk of the home
    home = block(town, town.firms_for("housing")[0], 1, 11, homes=1)
    buyer = tenant(town, home, cash=3_500_000)
    employ(buyer, far)
    sell_foreclosed(town)
    assert unit.owner is None


def test_upkeep_needs_the_hours_and_the_parts_each():
    from engine.rtr_owning import keep
    town, a, firm = _renter_of_a_set()
    unit = _own_set(town, a)
    unit.age, unit.cond = 260, 0.6
    a.cash, a.spare_hours = 1_000_000, 0.0                           # parts but no hours
    keep(town, a)
    assert unit.cond < 0.6
    unit.cond = 0.6
    a.cash, a.spare_hours = 0, 20.0                                  # hours but no parts
    keep(town, a)
    assert unit.cond < 0.6


def test_upkeep_has_first_call_on_their_hours_before_building():
    from engine.rtr_owning import after_bills
    from engine.production import upkeep_need
    town, a, firm = _renter_of_a_set()
    unit = _own_set(town, a)
    unit.age, unit.cond = 100, 0.5
    a.set_hours_left = 20.0
    labour, _ = upkeep_need(town.cfg, unit)
    a.spare_hours = labour * 40.0                                    # just enough hours for the upkeep
    after_bills(town)
    assert a.set_hours_left == 20.0 and unit.cond > 0.5              # the upkeep was done; the build waited


def test_what_owning_costs_a_week_counts_their_hours():
    from engine.rtr_owning import own_cost_week
    town, a, firm = _renter_of_a_set()
    goods = (40 / 520 + 0.03) * 13_500
    hours = (0.5 / 520 + 0.010) * 40.0
    assert own_cost_week(town, a, "appliances") == round(goods + hours * town.hour_value)
    assert round(hours * town.hour_value) > 1_000                    # the hours are a real part of it


def test_a_home_loan_is_paid_before_the_bills_that_come_after_rent_and_borrowed_for_like_rent():
    from engine.household import dues, pay_bills
    from engine.subscriptions import subscribe
    town = rtr_town()
    show = town.add_firm("entertainment")
    a = town.add_agent(cash=0)
    a.role, a.wage = "staff", 100_000
    subscribe(town, a, show)
    a.home_loan, a.home_pay = 4_320_000, 4154
    assert [d[2] for d in dues(town, a)] == ["home_loan", "entertainment"]
    pay_bills(town)
    assert a.home_missed == 0 and a.loan > 0                         # a personal loan kept the home loan paid


def test_an_owner_is_not_counted_homeless():
    from engine.metrics import weekly_series
    town, a, unit = _owner()
    rows = {(scope, metric): value for scope, metric, value in weekly_series(town)}
    assert rows[("all", "homeless")] == 0
