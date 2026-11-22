"""Both worlds: the floor on what someone out of work will take holds only while money is coming in
(22 November 2026).

The floor (C, 21/11/2026): the least someone out of work will take never falls below what their own
basics cost them a week. Opened to the WEF world on his word ("all six of these issues should be the
same on both"), the fresh review found WEF towns with nine in ten out of work by year 14 (seeds 2 and 3,
500 people: 94% against 4% with the floor off): everything is rented, rents only rise, basics came to
cost more than any job paid, and everyone out of work turned every offer down. Put to him as Sam, a
year out of work with no income, basics of $1,494 a week, offered a job at $1,445: "So we'd have to
take the job there. Even though it's lower than his expenses, he can pay off most of his expenses."
And of whether Sam would take $100 a week: "If there is no money coming in, he will take any offer
that is put forward to him. Because you can't pay anything if he doesn't have money coming in." (J)

The review then found that a few dollars of dividends brought the whole floor back. Put to him: Sam's
shares pay him $5 a week; "he takes any offer unless the money he already has coming in pays his basics
on its own"; someone whose rents bring in $1,600 a week could still hold out. "Yes, that's right" (J).

Money coming in, for someone out of work (C): what the model already expects them to receive in a
week (`Agent.income_estimate`): a year's dividends spread over it, the rents of homes they let that
have tenants, and what a side hustle brought in a week over the last quarter. When it pays their
basics, the floor holds; otherwise it does not, and the least they would take is what it was before the
floor: what they last earned, less for feeling insecure, less 5% for every week out of work."""

import pytest
from conftest import empty_town

from engine.config import RTR_ONLY, load_config
from engine.household import basket_cost
from engine.labour import in_the_line, reservation_wage

DIAL = "floor_needs_money_coming_in"
WORLDS = ["wef", "rtr"]


def town_of(world, *overrides):
    return empty_town(f"world={world}", "hustle_rate=0.0", "hustle_rate_struggling=0.0", "idea_rate=0.0",
                      *overrides)


def out_of_work(town, weeks_out=100, last_wage=100_000, security=0.5):
    a = town.add_agent(cash=0)
    a.role, a.wage, a.last_wage, a.weeks_out, a.security = None, 0, last_wage, weeks_out, security
    return a


def test_the_dial_is_on_in_both_worlds():
    assert DIAL not in RTR_ONLY
    for path in ("wef/settings.json", "rtr/settings.json"):
        assert getattr(load_config(path), DIAL) is True
    assert getattr(load_config(None), DIAL) is True


@pytest.mark.parametrize("world", WORLDS)
def test_with_no_money_coming_in_they_take_any_offer(world):
    town = town_of(world)
    a = out_of_work(town, weeks_out=100)
    assert a.income_estimate() == 0
    assert reservation_wage(town.cfg, a, town) == 0                  # Sam: any offer
    assert in_the_line(town, 10_000) == 1                            # $100 a week


@pytest.mark.parametrize("world", WORLDS)
def test_just_out_of_work_with_no_money_coming_in_they_hold_out_as_before_the_floor(world):
    town = town_of(world)
    a = out_of_work(town, weeks_out=2, last_wage=200_000, security=0.9)
    assert reservation_wage(town.cfg, a, town) == reservation_wage(town.cfg, a) == int(200_000 * 0.9 * 0.9)


@pytest.mark.parametrize("world", WORLDS)
def test_sam_with_five_dollars_a_week_from_shares_takes_any_offer(world):
    town = town_of(world)
    a = out_of_work(town, weeks_out=100)
    a.div_quarters = [26_000]                                        # $260 a year: $5 a week
    assert a.income_estimate() == 500
    assert reservation_wage(town.cfg, a, town) == 0


@pytest.mark.parametrize("world", WORLDS)
def test_with_dividends_that_pay_their_basics_the_floor_holds(world):
    town = town_of(world)
    a = out_of_work(town, weeks_out=100)
    basics = basket_cost(town, a, loan=False)
    a.div_quarters = [basics * 52]
    assert a.income_estimate() == basics
    assert reservation_wage(town.cfg, a, town) == basics
    a.div_quarters = [basics * 52 - 52]                              # a dollar a week short of them
    assert reservation_wage(town.cfg, a, town) == 0


def _landlord(town, rent):
    from engine.entities import Letting
    a = out_of_work(town, weeks_out=100)
    lets = Letting(a, town.needs["housing"], 1)
    home = town.new_unit(town.add_firm("housing"))
    home.rent, home.occupant = rent, town.add_agent()
    lets.units.append(home)
    a.lets = lets
    return a


def test_rents_that_pay_their_basics_hold_the_floor_and_rents_that_do_not_leave_any_offer():
    town = town_of("rtr")
    rich = _landlord(town, 160_000)                                  # his example: $1,600 a week of rents
    assert reservation_wage(town.cfg, rich, town) == basket_cost(town, rich, loan=False) < 160_000
    poor = _landlord(town, 30_000)                                   # $300 a week
    assert reservation_wage(town.cfg, poor, town) == 0


def test_a_side_hustle_that_does_not_pay_their_basics_leaves_any_offer():
    from test_rtr_2 import maker
    town = town_of("rtr")
    a, hustle = maker(town, "entertainment")
    a.role, a.wage, a.last_wage, a.weeks_out, a.security = None, 0, 100_000, 100, 0.5
    hustle.profit_week = 62_000                                      # Mia's $620, against basics above it
    assert hustle.profit_week < basket_cost(town, a, loan=False)
    assert reservation_wage(town.cfg, a, town) == 0


@pytest.mark.parametrize("world", WORLDS)
def test_with_the_dial_off_the_floor_holds_with_nothing_coming_in(world):
    town = town_of(world, f"{DIAL}=false")
    a = out_of_work(town, weeks_out=100)
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a, loan=False) > 0


@pytest.mark.parametrize("world", WORLDS)
def test_with_the_floor_off_this_dial_changes_nothing(world):
    town = town_of(world, "reservation_covers_basket=false")
    a = out_of_work(town, weeks_out=100)
    a.div_quarters = [10_400_000]
    assert reservation_wage(town.cfg, a, town) == 0


# The review: in the WEF world nobody kept the most owed on a loan, so any loan at all counted as large.
def test_in_the_wef_world_the_most_owed_on_a_loan_is_kept_so_a_loan_mostly_paid_is_not_large():
    from engine.rtr_makers import owes_a_large_loan
    town = town_of("wef")
    a = out_of_work(town)
    a.loan = 100_000
    town.step()
    a.loan = 10_000                                                  # nine tenths paid off
    town.step()
    assert a.loan_top >= 100_000 and not owes_a_large_loan(a)
