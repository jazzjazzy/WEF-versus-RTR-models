"""The RTR world: someone going without appliances counts them at what owning a set costs a week, when that is
less than any rent asked (22 November 2026).

The trace (seeds 1, 4, 9, 14, 21, 24, 60 years): the firm that rents out appliances loses nearly all its
customers within ten years, as people own their own sets (about 900 in a town of about 900 by year 60). It
falls short of its profit target every quarter and its price rises 3% each time (his rule: a price only rises).
Seed 1: $76 a week at year 5, $2,642 at year 40, $9,417 at year 60, with no customer; owning a set cost $20 to
$24 a week. Those going without a set (3 to 10 a town) had that rent in their basics. Put to him: should someone
without a fridge count it at what owning one costs, about $23 a week, when renting costs more? "yes, go ahead
with the fix" (J). Appliances only: a home takes a deposit and a loan (Claude's call, C)."""

from test_rtr_2 import quiet_town as _quiet_town

from engine.config import RTR_ONLY, load_config
from engine.household import basket_cost
from engine.rtr_owning import own_cost_week
from engine.subscriptions import cheapest_prices

DIAL = "going_without_appliances_at_owning"


def quiet_town(*overrides):
    return _quiet_town(f"{DIAL}=true", *overrides)


def _without_a_set(town, rent):
    firm = town.add_firm("appliances")
    firm.price = rent
    sam = town.add_agent(cash=0)
    sam.subs.pop("appliances", None)
    sam.unit.pop("appliances", None)
    return firm, sam


def test_the_dial_is_on_in_the_rtr_world_and_is_the_rtr_worlds_own():
    assert load_config(None, ["world=rtr"]).going_without_appliances_at_owning is True
    assert load_config("rtr/settings.json").going_without_appliances_at_owning is True
    assert DIAL in RTR_ONLY


def test_a_rent_nobody_would_pay_gives_way_to_what_owning_a_set_costs():
    town = quiet_town()
    _without_a_set(town, 941_700)                                          # seed 1 at year 60: $9,417 a week
    owning = own_cost_week(town, None, "appliances")
    assert 0 < owning < 941_700
    assert cheapest_prices(town).lowest["appliances"] == owning


def test_their_basics_count_the_set_at_what_owning_one_costs():
    town = quiet_town()
    _, sam = _without_a_set(town, 941_700)
    cheapest = cheapest_prices(town)
    others = sum(cheapest.lowest[n] for n, s in town.needs.items() if not s.invented and n != "appliances")
    assert basket_cost(town, sam, cheapest) == others + own_cost_week(town, None, "appliances")


def test_a_rent_below_what_owning_costs_still_counts():
    town = quiet_town()
    owning = own_cost_week(town, None, "appliances")
    _without_a_set(town, owning - 100)
    assert cheapest_prices(town).lowest["appliances"] == owning - 100


def test_what_is_on_offer_to_rent_this_week_is_not_changed():
    town = quiet_town()
    _without_a_set(town, 941_700)
    assert cheapest_prices(town)["appliances"] == 941_700


def test_a_home_is_not_counted_at_what_owning_one_costs():
    town = quiet_town()
    firm = town.add_firm("housing")
    firm.price = 5_000_000
    assert cheapest_prices(town).lowest["housing"] == 5_000_000


def test_with_the_dial_off_the_rent_counts():
    town = quiet_town(f"{DIAL}=false")
    _without_a_set(town, 941_700)
    assert cheapest_prices(town).lowest["appliances"] == 941_700


def test_with_the_lowest_price_rule_off_nothing_changes():
    town = quiet_town("going_without_at_lowest_price=false")
    _without_a_set(town, 941_700)
    assert cheapest_prices(town).lowest["appliances"] == 941_700


def test_a_wef_town_is_not_changed():
    town = quiet_town()
    town.cfg.world = "wef"
    _without_a_set(town, 941_700)
    assert cheapest_prices(town).lowest["appliances"] == 941_700
