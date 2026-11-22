"""The RTR world: a newcomer does not rent appliances that cost more than owning a set (22 November 2026).

Read in the code: someone arriving in town signed up for each base need at the cheapest firm, whatever it
charged (`subscriptions.sign_up_for_the_rest`), and so took on the appliance firm's runaway rent ($9,417 a week
in seed 1 at year 60, against about $23 a week to own a set). A newcomer buying a home held back four weeks of
the base needs at those rents (`rtr_owning.newcomer_keeps`): about $37,700. His words: "A rented house can also
buy appliances, not just rent them ... Who would pay $9,000 if they could pay $23." Put to him: on arrival, if
renting appliances costs more than owning a set, they build their own straight away if they can pay for the
parts, or go without until they can, as anyone in town does; the holdback counts appliances at what owning
costs. "yes, build it" (J).

The review found that the week's review of what people take up (`household._take_up`) signed the newcomer up for
the rental anyway, if they could afford it, even while building a set. And "go without until they can", read
literally, would leave most newcomers without a set from the first week: the rent starts at $55 against about $25
to own, and most cannot pay $5,400 for the parts. So, as anyone in town does (C, put to him before the commit): a
newcomer who can pay for the parts, and for whom owning is clearly cheaper, builds and does not rent; the rest
rent only if they can afford it, by the test everyone in town uses; nobody rents while building a set."""

from test_rtr_2 import quiet_town as _quiet_town

from engine.config import RTR_ONLY, load_config
from engine.rtr_owning import newcomer_keeps, own_cost_week
from engine.household import review_subscriptions
from engine.subscriptions import cheapest_prices, sign_up_for_the_rest

DIAL = "arrivals_own_appliances"
RUNAWAY = 941_700                                                          # $9,417 a week


def quiet_town(*overrides):
    return _quiet_town(f"{DIAL}=true", *overrides)


def _town_with_rent(rent, *overrides):
    town = quiet_town(*overrides)
    firm = next((f for f in town.firms if f.need == "appliances"), None) or town.add_firm("appliances")
    for other in town.firms:
        if other.need == "appliances" and other is not firm:
            other.price = rent
    firm.price = rent
    town.new_unit(firm)                                                    # a set free to rent
    return town, firm


def _arrival(town, cash):
    a = town.add_agent(cash=cash)
    a.subs.pop("appliances", None)
    a.unit.pop("appliances", None)
    return a


def test_the_dial_is_on_in_the_rtr_world_and_is_the_rtr_worlds_own():
    assert load_config(None, ["world=rtr"]).arrivals_own_appliances is True
    assert load_config("rtr/settings.json").arrivals_own_appliances is True
    assert DIAL in RTR_ONLY


def _arrive_and_review(town, a):
    sign_up_for_the_rest(town, a)
    review_subscriptions(town)


def test_a_newcomer_who_can_pay_for_the_parts_builds_a_set_and_does_not_rent_one_that_week():
    town, _ = _town_with_rent(RUNAWAY)
    a = _arrival(town, cash=5_000_000)
    a.wage = 100_000_000                                                   # could afford even the runaway rent
    sign_up_for_the_rest(town, a)
    assert "appliances" not in a.subs
    assert a.set_hours_left is not None                                    # building has started
    parts = int(round(town.needs["appliances"].build_goods * town.needs["appliances"].import_price))
    assert a.cash == 5_000_000 - parts
    review_subscriptions(town)
    assert "appliances" not in a.subs                                      # not while building


def test_a_newcomer_who_cannot_pay_for_the_parts_does_not_rent_at_a_runaway_rent_they_cannot_afford():
    town, _ = _town_with_rent(RUNAWAY)
    a = _arrival(town, cash=0)
    a.wage = 100_000
    _arrive_and_review(town, a)
    assert "appliances" not in a.subs
    assert a.set_hours_left is None


def test_a_newcomer_who_cannot_pay_for_the_parts_rents_a_set_they_can_afford():
    town, firm = _town_with_rent(5_500)                                    # the opening rent, $55 a week
    a = _arrival(town, cash=100_000)                                       # $1,000: the rent, not the $5,400 of parts
    a.wage = 100_000
    sign_up_for_the_rest(town, a)
    assert "appliances" not in a.subs                                      # left to the week's review
    review_subscriptions(town)
    assert a.subs.get("appliances") is firm
    assert a.set_hours_left is None


def test_owning_must_be_clearly_cheaper_as_for_anyone_in_town():
    town, _ = _town_with_rent(1)
    owning = own_cost_week(town, None, "appliances")
    town, firm = _town_with_rent(int(owning / (1.0 - town.cfg.switch_friction)) - 10)   # owning not clearly cheaper
    a = _arrival(town, cash=5_000_000)
    sign_up_for_the_rest(town, a)
    assert a.subs.get("appliances") is firm
    assert a.set_hours_left is None


def test_a_rent_below_what_owning_costs_is_still_taken_up():
    town, _ = _town_with_rent(1)
    town, firm = _town_with_rent(own_cost_week(town, None, "appliances") - 100)
    a = _arrival(town, cash=5_000_000)
    sign_up_for_the_rest(town, a)
    assert a.subs.get("appliances") is firm
    assert a.set_hours_left is None


def test_someone_in_town_building_a_set_does_not_take_up_a_rental_meanwhile():
    town, _ = _town_with_rent(5_500)
    a = _arrival(town, cash=5_000_000)
    a.wage = 100_000
    a.set_hours_left = 20.0
    review_subscriptions(town)
    assert "appliances" not in a.subs


def test_with_the_dial_off_someone_building_may_still_rent_meanwhile():
    town, firm = _town_with_rent(5_500, f"{DIAL}=false")
    a = _arrival(town, cash=5_000_000)
    a.wage = 100_000
    a.set_hours_left = 20.0
    review_subscriptions(town)
    assert a.subs.get("appliances") is firm


def test_the_other_base_needs_are_signed_up_for_as_before():
    town, _ = _town_with_rent(RUNAWAY)
    food = next((f for f in town.firms if f.need == "food"), None) or town.add_firm("food")
    a = _arrival(town, cash=0)
    sign_up_for_the_rest(town, a)
    assert "food" in a.subs


def test_with_the_dial_off_a_newcomer_rents_at_whatever_the_firm_asks():
    town, firm = _town_with_rent(RUNAWAY, f"{DIAL}=false")
    a = _arrival(town, cash=5_000_000)
    sign_up_for_the_rest(town, a)
    assert a.subs.get("appliances") is firm


def test_a_wef_newcomer_rents_as_before():
    town, firm = _town_with_rent(RUNAWAY)
    town.cfg.world = "wef"
    a = _arrival(town, cash=5_000_000)
    sign_up_for_the_rest(town, a)
    assert a.subs.get("appliances") is firm


def _others(town):
    cheapest = cheapest_prices(town)
    return sum(cheapest.get(n, 0) for n, s in town.needs.items()
               if not s.invented and n not in ("housing", "appliances"))


def test_a_newcomer_buying_holds_back_appliances_at_what_owning_costs():
    town, _ = _town_with_rent(RUNAWAY)
    assert newcomer_keeps(town) == 4 * (_others(town) + own_cost_week(town, None, "appliances"))


def test_a_newcomer_buying_holds_back_a_rent_below_owning_as_before():
    town, _ = _town_with_rent(1)
    rent = own_cost_week(town, None, "appliances") - 100
    town, _ = _town_with_rent(rent)
    assert newcomer_keeps(town) == 4 * (_others(town) + rent)


def test_with_the_dial_off_the_holdback_counts_the_rent():
    town, _ = _town_with_rent(RUNAWAY, f"{DIAL}=false")
    assert newcomer_keeps(town) == 4 * (_others(town) + RUNAWAY)
