"""The RTR world: an owner is judged on what they actually pay (Jason, 20 November 2026).

His words: "Yes, it should be judged on what they actually pay because they own it. The reason they want
to own it is because they don't want to know what the firms are being priced at or they don't want to
care." And for the town's basket: "yes, use what people actually pay".

Until then an owner's basket counted their own home and appliance set at the cheapest asking rent, as for
someone going without (Claude's call in the design, marked C). In full towns the landlord firms had no
tenants left and kept raising what they asked, so owners measured themselves against rents nobody paid."""

import pytest
from test_rtr import _owner, _own_set, _renter_of_a_set

from engine.config import RTR_ONLY, load_config
from engine.household import basket_cost
from engine.metrics import weekly_series
from engine.rtr_owning import own_cost_week
from engine.subscriptions import cheapest_prices
from engine.town import Town

DIAL = "owners_judge_by_what_they_pay"


def test_the_dial_is_on_in_the_rtr_world_and_is_the_rtr_worlds_own():
    assert load_config(None, ["world=rtr"]).owners_judge_by_what_they_pay is True
    assert load_config("rtr/settings.json").owners_judge_by_what_they_pay is True
    assert DIAL in RTR_ONLY


def test_an_owner_with_no_loan_counts_their_home_at_its_upkeep_not_the_asking_rent():
    town, a, unit = _owner()
    cheapest = cheapest_prices(town)
    renter = town.add_agent()
    assert cheapest["housing"] > 0
    upkeep = own_cost_week(town, a, "housing", build=False)
    assert 0 < upkeep < cheapest["housing"]
    assert basket_cost(town, a) == basket_cost(town, renter) - cheapest["housing"] + upkeep


def test_an_owner_with_a_loan_counts_the_loan_payment_too():
    town, a, unit = _owner()
    without = basket_cost(town, a)
    a.home_loan, a.home_pay = 4_000_000, 4_000
    interest = round(4_000_000 * town.cfg.firm_rate / town.cfg.weeks_per_year)
    assert basket_cost(town, a) == without + interest + 4_000


def test_a_set_of_their_own_counts_at_its_upkeep_not_the_firms_rent():
    town, a, firm = _renter_of_a_set()
    renting = basket_cost(town, a)
    paid = firm.price
    _own_set(town, a)
    assert basket_cost(town, a) == renting - paid + own_cost_week(town, a, "appliances", build=False)


def test_the_asking_rent_of_a_firm_no_longer_moves_an_owners_basket():
    town, a, unit = _owner()
    before = basket_cost(town, a)
    for f in town.firms:
        if f.need == "housing":
            f.price *= 50
    assert basket_cost(town, a) == before


@pytest.mark.parametrize("world", ["world=rtr", "world=wef"])
def test_with_the_dial_off_or_in_the_wef_world_an_owner_counts_the_asking_rent(world):
    town, a, unit = _owner()
    town.cfg.owners_judge_by_what_they_pay = False
    renter = town.add_agent()
    assert basket_cost(town, a) == basket_cost(town, renter)
    if world == "world=wef":
        town.cfg.owners_judge_by_what_they_pay = True
        town.cfg.world = "wef"
        assert not town.cfg.rtr
        assert basket_cost(town, a) == basket_cost(town, renter)


def test_an_owners_security_does_not_fall_when_the_empty_firms_raise_their_rent():
    from engine.household import update_agents
    town, a, unit = _owner(cash=500_000)
    a.wage = 80_000
    update_agents(town)
    usual = a.security
    for f in town.firms:
        if f.need == "housing":
            f.price *= 50
    a.security = town.cfg.security_start
    update_agents(town)
    assert a.security == pytest.approx(usual)


# --- the town's basket ---------------------------------------------------------------------------------
def _rows(town):
    return {m: v for s, m, v in weekly_series(town) if s == "town"}


def _small(*overrides):
    town = Town(load_config("rtr/settings.json", ["population_cap=40", "seed=3", *overrides]))
    for _ in range(3 * 52):
        town.step()
    return town


def test_the_rtr_towns_basket_is_what_its_people_count_and_the_asking_basket_is_kept_beside_it():
    town = _small()
    rows = _rows(town)
    cheapest = cheapest_prices(town)
    asking = sum(cheapest.get(s.name, 0) for s in town.needs.values() if not s.invented)
    people = [basket_cost(town, a, cheapest) for a in town.agents]
    assert rows["basket"] == pytest.approx(sum(people) / len(people))
    assert rows["basket_asking"] == asking
    assert rows["affordability"] == pytest.approx(rows["basket"] / town.staff_pay())
    base0 = sum(s.initial_price for s in town.needs.values() if not s.invented)
    assert rows["price_index"] == pytest.approx(asking / base0)            # prices on offer, as before


def test_with_the_dial_off_the_rtr_towns_basket_is_the_asking_basket():
    town = _small(f"{DIAL}=false")
    rows = _rows(town)
    assert rows["basket"] == rows["basket_asking"]


def test_a_wef_town_keeps_no_asking_basket_of_its_own():
    town = Town(load_config("wef/settings.json", ["population_cap=30", "years=1"]))
    for _ in range(10):
        town.step()
    assert "basket_asking" not in _rows(town)


# --- after the review (20 November 2026) ----------------------------------------------------------------
def test_an_aged_home_counts_at_the_upkeep_it_needs_now_not_a_new_ones():
    from engine.production import upkeep_need
    town, a, unit = _owner()
    new = basket_cost(town, a)
    unit.age = 20 * 52                                                       # twenty years old: more upkeep a week
    labour, goods = upkeep_need(town.cfg, unit)
    now = int(round(goods * town.needs["housing"].import_price
                    + labour * town.cfg.job_hours * town.hour_value))
    assert now > own_cost_week(town, a, "housing", build=False)
    assert basket_cost(town, a) == new - own_cost_week(town, a, "housing", build=False) + now


def test_a_bigger_home_of_their_own_counts_at_a_standard_homes_upkeep():
    town, a, unit = _owner()
    standard = basket_cost(town, a)
    unit.scale = 1.5                                                         # a better home is left out, as for a renter
    assert basket_cost(town, a) == standard


def test_someone_who_owes_on_a_home_they_do_not_live_in_counts_the_payment():
    town, a, landlord = __import__("test_rtr")._tenant_with_a_job()
    renting = basket_cost(town, a)                                           # they rent, and owe on a home elsewhere
    a.home_loan, a.home_pay = 2_000_000, 2_000
    interest = round(2_000_000 * town.cfg.firm_rate / town.cfg.weeks_per_year)
    assert basket_cost(town, a) == renting + interest + 2_000


# --- going without: the lowest price a firm or a neighbour charges (Jason, 21 November 2026) ----------
# His words: "happiness can be affected by the fact that you can't purchase entertainment. But unhappiness
# shouldn't be affected by not paying a $5,905 bill that no one is paying for." And: "The price that they
# can't afford should always be the one that's the lowest out of the possible two. neighbours entertainment
# or firms Entertainment. It will be the one that they could actually achieve, not the one that's way out of
# scope."
LOWEST = "going_without_at_lowest_price"


def _going_without_entertainment(*overrides):
    """A firm asking $5,905 a week for entertainment, a neighbour selling it at $205 who is full this
    week, and Sam, who has none."""
    from test_rtr_2 import maker, quiet_town
    town = quiet_town(*overrides)
    firm = town.add_firm("entertainment")
    firm.price = 590_500
    _, hustle = maker(town, "entertainment")
    hustle.price, hustle.capacity = 20_500, 0                  # full: no room for anyone new this week
    sam = town.add_agent(cash=100_000)
    return town, sam, firm, hustle


def test_the_rule_is_on_in_the_rtr_world_and_is_the_rtr_worlds_own():
    assert load_config(None, ["world=rtr"]).going_without_at_lowest_price is True
    assert load_config("rtr/settings.json").going_without_at_lowest_price is True
    assert LOWEST in RTR_ONLY


def test_going_without_counts_at_the_neighbours_price_when_it_is_the_lowest_even_if_they_are_full():
    town, sam, firm, hustle = _going_without_entertainment()
    cheapest = cheapest_prices(town)
    assert cheapest["entertainment"] == 590_500                # what is on offer to buy this week: unchanged
    others = sum(cheapest[n] for n, s in town.needs.items() if not s.invented and n != "entertainment")
    assert basket_cost(town, sam, cheapest) == others + 20_500
    assert basket_cost(town, sam) == others + 20_500


def test_going_without_counts_at_the_firms_price_when_that_is_the_lowest():
    town, sam, firm, hustle = _going_without_entertainment()
    hustle.price = 700_000
    cheapest = cheapest_prices(town)
    others = sum(cheapest[n] for n, s in town.needs.items() if not s.invented and n != "entertainment")
    assert basket_cost(town, sam, cheapest) == others + 590_500


def test_with_that_dial_off_going_without_counts_at_what_is_on_offer_this_week():
    town, sam, firm, hustle = _going_without_entertainment(f"{LOWEST}=false")
    cheapest = cheapest_prices(town)
    assert basket_cost(town, sam, cheapest) == sum(cheapest[n] for n, s in town.needs.items() if not s.invented)


def test_someone_with_no_home_counts_the_lowest_rent_a_firm_or_a_neighbour_asks():
    town, a, unit = _owner()
    landlord_firm = next(f for f in town.firms if f.need == "housing")
    landlord_firm.price = 1_264_800                            # an asking rent of $12,648 a week
    from engine.rtr_owning import make_private  # noqa: F401
    from engine.entities import Letting
    a.lets = Letting(a, town.needs["housing"], -a.id)
    let = town.new_own_unit(town.needs["housing"], a)
    let.rent = 30_000                                          # a neighbour's home to let at $300 a week
    a.lets.units.append(let)
    homeless = town.add_agent(cash=0)
    cheapest = cheapest_prices(town)
    others = sum(cheapest[n] for n, s in town.needs.items() if not s.invented and n != "housing")
    assert basket_cost(town, homeless, cheapest) == others + 30_000


def test_a_wef_town_keeps_going_without_at_the_price_on_offer():
    town = Town(load_config("wef/settings.json", ["population_cap=30", "years=1"]))
    for _ in range(5):
        town.step()
    cheapest = cheapest_prices(town)
    a = next(x for x in town.agents)
    expected = sum((__import__("engine.subscriptions", fromlist=["x"]).standard_price(a, n) if n in a.subs else cheapest[n])
                   for n, s in town.needs.items() if not s.invented)
    assert basket_cost(town, a, cheapest) == expected


def test_outside_the_rtr_world_a_neighbours_price_never_lowers_the_yardstick():
    town, sam, firm, hustle = _going_without_entertainment()
    town.cfg.world = "wef"
    assert not town.cfg.rtr
    cheapest = cheapest_prices(town)
    assert cheapest.lowest == dict(cheapest)
