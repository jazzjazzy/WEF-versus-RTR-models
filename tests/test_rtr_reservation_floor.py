"""The RTR world: the least someone out of work will take never falls below what their own basics cost
them a week (21 November 2026).

Jason asked why pay fell so low in the worst RTR towns, and to "fix the issue". Traced (seeds 15 and 49 of
`rtr/batches/lowest-rtr`): the least someone out of work would take fell 5% a week, with no floor, so after
twenty weeks out of work it was nothing; in seed 15 nearly all of those out of work would take any pay (145 of 153
at year 5, 215 of 222 at year 30). The line stayed above 5% of the town for decades, and a firm short of profit cut
its rate every quarter it did (his rule, "cutting when there is a queue"). Rates fell from about $950 to about $100
a week, against basics costing those out of work $430 to $640. No firm had a job it could not fill.

The 5% a week and the missing floor were Claude's numbers (C), not his. The floor is Claude's call too (C): their
basket, which by his rulings of 20 and 21 November is what they actually pay."""

import pytest
from test_rtr_2 import quiet_town as _quiet_town

from engine.config import RTR_ONLY, load_config
from engine.household import basket_cost
from engine.labour import in_the_line, reservation_wage

DIAL = "reservation_covers_basket"


def quiet_town(*overrides):
    return _quiet_town(f"{DIAL}=true", *overrides)


def out_of_work(town, weeks_out=100, last_wage=100_000, security=0.5):
    """With dividends that pay their basics: from 22/11/2026 the floor holds only while what comes in pays the
    basics on its own (Jason; test_floor_needs_money_coming_in.py)."""
    a = town.add_agent(cash=0)
    a.role, a.last_wage, a.weeks_out, a.security = None, last_wage, weeks_out, security
    a.div_quarters = [10_400_000]                                   # $2,000 a week: more than their basics
    return a


def test_the_dial_is_on_in_the_rtr_world_and_from_22_november_in_both():
    assert load_config(None, ["world=rtr"]).reservation_covers_basket is True
    assert load_config("rtr/settings.json").reservation_covers_basket is True
    assert DIAL not in RTR_ONLY                                     # Jason: "the same on both"


def test_long_out_of_work_they_still_will_not_take_less_than_their_basics_cost():
    town = quiet_town()
    a = out_of_work(town, weeks_out=100)
    assert reservation_wage(town.cfg, a) == 0                       # the formula alone: nothing after 20 weeks
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a)
    assert basket_cost(town, a) > 0


def test_recently_out_of_work_they_hold_out_for_more_as_before():
    town = quiet_town()
    a = out_of_work(town, weeks_out=1, last_wage=200_000, security=0.9)
    alone = reservation_wage(town.cfg, a)
    assert alone > basket_cost(town, a)
    assert reservation_wage(town.cfg, a, town) == alone


@pytest.mark.parametrize("world", ["rtr", "wef"])
def test_with_the_dial_off_there_is_no_floor(world):
    town = quiet_town(f"{DIAL}=false")
    town.cfg.world = world
    a = out_of_work(town, weeks_out=100)
    assert reservation_wage(town.cfg, a, town) == 0


def test_a_rate_below_their_basics_does_not_put_them_in_the_line():
    town = quiet_town()
    a = out_of_work(town, weeks_out=100)
    basics = basket_cost(town, a)
    assert in_the_line(town, basics - 1) == 0
    assert in_the_line(town, basics) == 1
    town.cfg.reservation_covers_basket = False
    assert in_the_line(town, basics - 1) == 1


def test_offered_a_job_below_their_basics_they_turn_it_down_and_at_their_basics_they_take_it():
    from engine.labour import labour_market
    from test_labour import busy_firm
    town = quiet_town()                                            # the rate is under the outside wage: no newcomers
    firm = busy_firm(town, customers=10)
    a = out_of_work(town, weeks_out=100)
    basics = basket_cost(town, a)
    firm.wage = basics - 1
    labour_market(town)
    assert a.role is None
    firm.wage = basics
    labour_market(town)
    assert a.employer is firm


# --- after the review (21 November 2026) ----------------------------------------------------------------
def test_the_floor_leaves_out_the_home_loan_payment():
    town = quiet_town()
    a = out_of_work(town, weeks_out=100)
    basics = basket_cost(town, a)
    a.home_loan, a.home_pay = 19_000_000, 20_000                  # a large home loan: about $419 a week to the bank
    assert basket_cost(town, a) > basics                          # they pay it, so their basket counts it
    assert reservation_wage(town.cfg, a, town) == basics          # but a job need not cover it for them to take one


def test_someone_who_owes_a_large_loan_still_takes_the_first_job_offered():
    town = quiet_town()
    a = out_of_work(town, weeks_out=100)
    a.loan = a.loan_top = 500_000                                 # a personal loan, none of it paid off (his rule: "take the first job offered")
    assert reservation_wage(town.cfg, a, town) == reservation_wage(town.cfg, a) == 0


def test_a_floor_applies_part_way_through_a_spell_too():
    town = quiet_town()
    a = out_of_work(town, weeks_out=10, last_wage=100_000, security=0.5)
    alone = reservation_wage(town.cfg, a)
    assert 0 < alone < basket_cost(town, a)
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a)


def test_a_small_business_taking_someone_on_asks_the_floor_too():
    from test_rtr_2 import customers, hours_for_the_week, make_business, maker, turned_away
    from engine import rtr_makers
    town = quiet_town()
    owner, h = maker(town, cash=100_000)
    make_business(town, h)
    town.typical_wage = lambda: 30_000                             # the going wage it pays: $300, under anyone's basics here
    a = out_of_work(town, weeks_out=100)
    customers(town, h, 30)
    turned_away(town, h, 20)
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert a not in h.staff
