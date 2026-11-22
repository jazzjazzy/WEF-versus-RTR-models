"""Six rules of the RTR world hold in the WEF world too (22 November 2026).

Six rules about jobs, pay and what basics cost were built for the RTR world only, though none of them
needs anyone to own anything. Put to him as a list, with the WEF world "rent only", he said: "From RTR
world, all six of these issues should be the same on both." (J)

1. reservation_covers_basket (C, 21/11/2026): the least someone out of work will take never falls below
   what their own basics cost them a week.
2. line_is_who_would_take (J, 19/11/2026): the line that lets a firm cut its wage is those out of work
   who would take the job.
3. staff_keep_pay (J, 19/11/2026): a cut in a firm's wage is for those hired after it.
4. loss_sheds_staff (J, 19/11/2026): a firm in debt that lost money lets staff go until their pay covers
   the loss.
5. longest_serving_first (J, 19/11/2026): whoever a firm has to let go, the longest-serving goes first.
6. going_without_at_lowest_price (J, 21/11/2026): a need someone goes without counts at the lowest price
   asked. The WEF world has only firms, so it is the cheapest firm's price, as it already was."""

import pytest
from conftest import empty_town
from test_rtr_rulings import (cuts, firm_in_a_quarter, firm_with_too_many, let_go, out_of_work,
                              review_then_next_week, shed, shop_and_staff, shop_short_of_profit, taken_on)

from engine.config import RTR_ONLY, load_config

SIX = ("reservation_covers_basket", "line_is_who_would_take", "staff_keep_pay", "loss_sheds_staff",
       "longest_serving_first", "going_without_at_lowest_price")


def wef_town(*overrides):
    town = empty_town(*overrides)
    assert town.cfg.world == "wef"
    return town


@pytest.mark.parametrize("dial", SIX)
def test_each_is_on_in_both_worlds_and_no_longer_the_rtr_worlds_own(dial):
    assert dial not in RTR_ONLY
    assert getattr(load_config("wef/settings.json"), dial) is True
    assert getattr(load_config("rtr/settings.json"), dial) is True
    assert getattr(load_config(None), dial) is True


# 1. the least someone out of work will take
def long_out_of_work(town):
    """Out of work a long time, with dividends that pay their basics, so the floor holds: his rule of the
    same day is that otherwise they take any offer (test_floor_needs_money_coming_in.py)."""
    a = town.add_agent(cash=0)
    a.role, a.last_wage, a.weeks_out, a.security = None, 100_000, 100, 0.5
    a.div_quarters = [10_400_000]                                   # $2,000 a week: more than their basics
    return a


def test_long_out_of_work_they_will_not_take_less_than_their_basics_cost():
    from engine.household import basket_cost
    from engine.labour import reservation_wage
    town = wef_town()
    a = long_out_of_work(town)
    assert reservation_wage(town.cfg, a) == 0                       # the formula alone: nothing after 20 weeks
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a) > 0


def test_with_the_floor_off_it_falls_to_nothing_as_before():
    from engine.labour import reservation_wage
    town = wef_town("reservation_covers_basket=false")
    assert reservation_wage(town.cfg, long_out_of_work(town), town) == 0


def test_a_rate_below_their_basics_does_not_put_them_in_the_line():
    from engine.household import basket_cost
    from engine.labour import in_the_line
    town = wef_town()
    basics = basket_cost(town, long_out_of_work(town))
    assert in_the_line(town, basics - 1) == 0 and in_the_line(town, basics) == 1


# 2. the line
def test_people_who_would_not_take_the_job_are_not_a_line():
    from engine.corporate import review_firm
    town = wef_town()
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        out_of_work(town, would_take=200_000)                       # they would not work for under $2,000
    review_firm(town, firm)
    assert cuts(town) == []


def test_people_who_would_take_it_are():
    from engine.corporate import review_firm
    town = wef_town("reservation_covers_basket=false")              # $784 is under an empty town's basket
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        out_of_work(town, would_take=10_000)
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)]


def test_with_the_line_dial_off_everyone_without_a_job_is_counted_as_before():
    from engine.corporate import review_firm
    town = wef_town("line_is_who_would_take=false")
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        out_of_work(town, would_take=200_000)
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)]


# 3. staff keep their pay
def test_a_cut_is_for_those_hired_after_it():
    from engine.firmops import set_wage
    town = wef_town()
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    assert firm.wage == 78_400 and [a.wage for a in old] == [80_000] * 3
    assert taken_on(town, firm).wage == 78_400


def test_with_that_dial_off_a_cut_is_everyones_as_before():
    from engine.firmops import set_wage
    town = wef_town("staff_keep_pay=false")
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    assert [a.wage for a in old] == [78_400] * 3


def test_on_pay_day_each_is_paid_their_own_rate():
    from engine.corporate import _pay_wages
    from engine.firmops import set_wage
    town = wef_town()
    firm, old = shop_and_staff(town, pays=80_000, staff=2)
    set_wage(town, firm, 78_400, "queue")
    new = taken_on(town, firm)
    before = {a.id: a.cash for a in old + [new]}
    _pay_wages(town, firm)
    assert [a.cash - before[a.id] for a in old + [new]] == [80_000, 80_000, 78_400]


# 4. a firm in debt that lost money lets staff go
def test_a_firm_in_debt_that_lost_money_lets_its_longest_serving_go_until_their_pay_covers_the_loss():
    town = wef_town()
    firm, people = firm_in_a_quarter(town)                          # five staff, $2,000 a week lost
    review_then_next_week(town, firm)
    assert firm.staff == people[2:]
    assert shed(town) == [(firm.id, 2, 225_400, 200_000)]


def test_with_that_dial_off_a_loss_lets_nobody_go_as_before():
    town = wef_town("loss_sheds_staff=false")
    firm, people = firm_in_a_quarter(town)
    review_then_next_week(town, firm)
    assert firm.staff == people and shed(town) == []


# 5. the longest-serving goes first
@pytest.mark.parametrize("dial, first", [((), 0), (("longest_serving_first=false",), -1)])
def test_for_want_of_work_the_longest_serving_goes_first(dial, first):
    from engine.labour import labour_market
    town = wef_town(*dial)
    firm, people = firm_with_too_many(town)
    labour_market(town)
    assert let_go(town) == [(people[first].id, "laid_off")]


@pytest.mark.parametrize("dial, order", [((), (0, 1)), (("longest_serving_first=false",), (2, 1))])
def test_a_firm_that_cannot_pay_lets_the_longest_serving_go_first(dial, order):
    from engine.corporate import _shed_unpaid
    town = wef_town(*dial)
    firm, people = firm_with_too_many(town, staff=3)
    firm.cash = 100_000
    _shed_unpaid(town, firm)
    assert let_go(town) == [(people[i].id, "unpaid") for i in order]


# 6. going without, at the lowest price asked
def test_going_without_counts_at_the_cheapest_firms_price_and_not_at_owning():
    from engine.subscriptions import cheapest_prices
    town = wef_town()
    for price in (941_700, 950_000):
        town.add_firm("appliances").price = price
    cheapest = cheapest_prices(town)
    assert cheapest.lowest["appliances"] == cheapest["appliances"] == 941_700   # nobody can own a set here


# A whole WEF town under the weekly checks, with the six as the world now ships
@pytest.fixture(scope="module")
def wef_town_of_today():
    from test_town_invariants import run_checked
    from engine.town import Town
    town = Town(load_config("wef/settings.json", ["population_cap=120", "seed=1", "stop_on_failure=false"]))
    return town, run_checked(town, 6 * 52)


def test_a_wef_town_keeps_its_accounts_and_places_under_the_six(wef_town_of_today):
    town, problems = wef_town_of_today
    assert problems == []


def test_in_a_wef_town_the_rules_happen(wef_town_of_today):
    town, _ = wef_town_of_today
    kinds = {e["kind"] for e in town.rec.events}
    queue = [e for e in town.rec.events if e["kind"] == "wage_change" and e["data"]["reason"] == "queue"]
    assert "staff_shed" in kinds and queue                                   # 4, and a cut for the line
    assert any(a.wage > f.wage for f in town.alive_firms for a in f.staff)  # 3, staff kept their pay


def test_in_a_wef_town_nobody_out_of_work_with_money_coming_in_takes_less_than_their_basics(wef_town_of_today):
    from engine.household import basket_cost
    from engine.labour import reservation_wage
    from engine.rtr_makers import owes_a_large_loan
    town, _ = wef_town_of_today
    out = [a for a in town.agents if a.role is None and a.klass != "owner"]
    held = [a for a in out if a.income_estimate() > 0 and not owes_a_large_loan(a)]
    assert out and all(reservation_wage(town.cfg, a, town) >= basket_cost(town, a, loan=False) for a in held)
    for a in out:
        if a.income_estimate() <= 0:                                # nothing coming in: any offer, after a while
            assert reservation_wage(town.cfg, a, town) == reservation_wage(town.cfg, a)


def test_the_six_change_a_wef_town_from_its_first_years():
    from conftest import what_happened
    from engine.config import BEFORE_SHARED_RULES
    from engine.town import Town
    towns = [Town(load_config("wef/settings.json", ["population_cap=120", "seed=1"] + extra))
             for extra in ([], BEFORE_SHARED_RULES)]
    for town in towns:
        for _ in range(2 * 52):
            town.step()
    assert what_happened(towns[0]) != what_happened(towns[1])


def test_a_boss_put_back_on_the_staff_takes_their_place_by_when_they_joined():
    from engine.labour import demote, hire, promote
    town = wef_town()
    firm = town.add_firm("food")
    firm.founded = -100
    people = [town.add_agent() for _ in range(3)]
    for week, a in enumerate(people):
        town.week = week
        hire(town, firm, a)
    promote(town, firm, people[0])
    demote(town, firm, people[0])
    assert firm.staff == people                                     # the longest-serving is first again
