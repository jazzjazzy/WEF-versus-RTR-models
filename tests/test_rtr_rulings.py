"""The Right to Repair world: Jason's rulings of 18 November 2026.

Ruling 5, his words: "If a newcomer is coming into the town, they have an opportunity to rent
anything that's vacant or buy anything that's available as long as they have ... good enough
income", and, to "Should a newcomer with good enough income be able to buy a home on
arriving?": "Yes, they can buy".
"""

import math

import pytest
from conftest import what_happened  # noqa: F401
from test_rtr import _tenant_with_a_job, rtr_town

from engine.places import dist


# --- ruling 5: a newcomer may buy on arriving ------------------------------------------------------
class Purse:
    """The town's own dice, except that every newcomer comes with this much cash. `rolls`: how
    often a newcomer's cash was rolled."""

    def __init__(self, rng, cash, cfg):
        self.rng, self.cash, self.rolls = rng, cash, 0
        self.purses = {math.log(cfg.worker_cash_median), math.log(cfg.founder_capital_median)}

    def lognormvariate(self, mu, sigma):
        if mu not in self.purses:
            return self.rng.lognormvariate(mu, sigma)
        self.rolls += 1
        return self.cash

    def __getattr__(self, name):
        return getattr(self.rng, name)


def newcomers_bring(town, cash):
    town.rng = Purse(town.rng, cash, town.cfg)


def bank_home(town, ask=3_000_000, placed=True):
    """An empty home the bank holds and asks this much for."""
    from engine.places import place_own_unit, take_plot
    from engine.rtr_owning import _bank_takes
    unit = town.new_own_unit(town.needs["housing"], None)
    if placed:
        place_own_unit(take_plot(town), unit)
    _bank_takes(town, unit, ask)
    return unit


def nothing_to_rent(ask=3_000_000, *overrides):
    """A town on the map: a food shop with jobs at $1,000 a week, a landlord whose two homes
    are both let, and one empty home the bank holds."""
    from test_places import tenant
    town, a, landlord = _tenant_with_a_job(100_000, *overrides)
    other = tenant(town, a.unit["housing"].spot, cash=100_000)
    other.klass = "owner"                                                    # not looking for work
    unit = bank_home(town, ask)
    return town, unit, town.firms_for("food")[0]


def kinds(town, *wanted):
    return [e["kind"] for e in town.rec.events if e["kind"] in wanted]


def test_the_dial_is_on_in_the_rtr_world_and_is_one_of_its_own():
    from engine.config import RTR_ONLY, load_config
    assert load_config(None, ["world=rtr"]).newcomers_buy is True
    assert "newcomers_buy" in RTR_ONLY


def test_a_newcomer_who_finds_nothing_to_rent_buys_the_home_the_bank_holds_empty():
    from engine.labour import new_worker
    from engine.rtr_owning import newcomer_keeps, owns
    town, unit, shop = nothing_to_rent()
    assert dist(unit.spot, shop.spot) <= town.cfg.walk_range and shop.wage == 100_000
    newcomers_bring(town, 1_000_000)
    keep = newcomer_keeps(town)
    people = town.population
    town.ledger.start_week()
    b = new_worker(town, shop)
    assert b is not None and town.population == people + 1
    assert unit.owner is b and unit.occupant is b and owns(b, "housing") and "housing" not in b.subs
    assert unit not in town.foreclosed and (unit.debt, unit.ask) == (0, 0)
    assert (b.cash, b.home_loan) == (keep, 3_000_000 - (1_000_000 - keep))   # all their cash but four weeks of bills
    assert town.ledger.week_out == {"loan_recovery": 3_000_000}
    assert "food" in b.subs                                                  # and they sign up for the rest as any arrival
    assert b.wage == 0 and b.role is None                                    # the job itself is theirs when the firm takes them on
    assert town.no_home_week is None                                         # nobody was turned away
    assert kinds(town, "home_loan", "foreclosed_sold", "arrival") == ["home_loan", "foreclosed_sold", "arrival"]
    arrival = [e for e in town.rec.events if e["kind"] == "arrival"][-1]
    assert arrival["data"]["bought"] == unit.id and arrival["data"]["who"] == "worker"
    assert town.rng.rolls == 1 and arrival["amount"] == 1_000_000            # the cash they bought with is the cash they came with


def test_a_newcomer_rents_when_a_home_is_free_to_rent():
    from engine.labour import new_worker
    from engine.subscriptions import unsubscribe
    town, unit, shop = nothing_to_rent()
    newcomers_bring(town, 1_000_000)
    unsubscribe(town, town.agents[1], "housing", "left")
    b = new_worker(town, shop)
    assert "housing" in b.subs and b.home_loan == 0 and b.cash == 1_000_000
    assert unit.owner is None and unit in town.foreclosed
    assert "bought" not in [e for e in town.rec.events if e["kind"] == "arrival"][-1]["data"]


def test_where_the_dial_asks_a_fifth_in_cash_a_newcomer_without_it_does_not_come():
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent(3_000_000, "mortgage_ltv=0.8")
    newcomers_bring(town, 300_000)                                           # the usual $3,000: four fifths of $30,000 lent
    people = town.population
    assert new_worker(town, shop) is None
    assert town.population == people and unit.owner is None and unit in town.foreclosed
    assert kinds(town, "arrival", "home_loan", "foreclosed_sold") == []


def test_they_hold_back_four_weeks_of_the_other_base_needs_at_the_cheapest_prices():
    from engine.labour import new_worker
    from engine.rtr_owning import newcomer_keeps
    from engine.subscriptions import cheapest_prices
    from test_places import crew, premises, transport_spec
    town, unit, shop = nothing_to_rent()
    town.needs["transport"] = transport_spec(town)                           # not a base need: nothing is held back for it
    crew(town, premises(town, "transport", 6, 4))
    cheapest = cheapest_prices(town)
    assert cheapest["transport"] > 0 and cheapest["housing"] > 0
    keep = newcomer_keeps(town)
    assert keep == 4 * sum(price for name, price in cheapest.items()
                           if name != "housing" and not town.needs[name].invented) > 0
    newcomers_bring(town, keep + 100_000)
    b = new_worker(town, shop)
    assert unit.owner is b and (b.cash, b.home_loan) == (keep, 2_900_000)    # all beyond it goes into the home


def test_where_the_dial_asks_a_fifth_what_they_hold_back_is_not_counted_toward_it():
    from engine.labour import new_worker
    from engine.rtr_owning import newcomer_keeps
    town, unit, shop = nothing_to_rent(3_000_000, "mortgage_ltv=0.8")
    keep = newcomer_keeps(town)
    newcomers_bring(town, 600_000 + keep - 1)                                # a cent short of their fifth
    assert new_worker(town, shop) is None
    town.rng.cash += 1
    b = new_worker(town, shop)
    assert unit.owner is b and (b.cash, b.home_loan) == (keep, 2_400_000)


def test_the_wage_of_the_job_they_come_for_must_carry_the_loan():
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent()
    from engine.rtr_owning import newcomer_keeps
    newcomers_bring(town, 1_000_000)
    payment = town.bank.home_first_payment(3_000_000 - (1_000_000 - newcomer_keeps(town)))
    enough = int(payment / town.cfg.mortgage_income_share)                   # three tenths of the wage must cover it
    shop.wage = enough - 1
    assert new_worker(town, shop) is None and unit.owner is None
    shop.wage = enough + 2
    assert new_worker(town, shop) is unit.owner


def test_a_home_with_a_tenant_in_it_is_not_sold_to_a_newcomer():
    from test_places import tenant
    from engine.labour import new_worker
    from engine.rtr_owning import _bank_takes
    town, unit, shop = nothing_to_rent()
    town.foreclosed.remove(unit)                                             # the bank holds only a let home now
    landlord = town.firms_for("housing")[0]
    let = landlord.units[0]
    sitting = let.occupant
    _bank_takes(town, let, 1_000_000)
    assert let in town.foreclosed and let.occupant is sitting
    newcomers_bring(town, 5_000_000)
    assert new_worker(town, shop) is None and let.occupant is sitting and let.owner is None


def test_of_two_they_could_buy_they_take_the_cheaper():
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent()
    cheap = bank_home(town, 2_000_000)
    newcomers_bring(town, 1_000_000)
    b = new_worker(town, shop)
    assert cheap.owner is b and unit.owner is None and unit in town.foreclosed


def test_a_home_beyond_a_walk_from_the_job_is_bought_only_with_a_ride_on_offer():
    from test_places import crew, premises, transport_spec
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent()
    far = premises(town, "entertainment", 0, 12)                             # jobs too far to walk to from the bank's home
    assert town.cfg.walk_range < dist(unit.spot, far.spot) <= town.cfg.walk_range * town.cfg.transport_speed
    newcomers_bring(town, 1_000_000)
    assert new_worker(town, far) is None and unit.owner is None
    town.needs["transport"] = transport_spec(town)
    crew(town, premises(town, "transport", 6, 4))
    b = new_worker(town, far)
    assert unit.owner is b and "transport" in b.subs                         # the ride comes with the home, as with a rented one


def test_a_home_farther_than_a_ride_from_the_job_is_no_use():
    from test_places import crew, premises, transport_spec
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent(3_000_000, "walk_range=2", "transport_speed=2.0")
    far = premises(town, "entertainment", 0, 12)
    town.needs["transport"] = transport_spec(town)
    crew(town, premises(town, "transport", 6, 4))
    assert dist(unit.spot, far.spot) > 4                                     # a ride reaches four blocks here
    newcomers_bring(town, 1_000_000)
    assert new_worker(town, far) is None and unit.owner is None


def test_with_no_map_any_empty_home_the_bank_holds_will_do():
    from test_labour import busy_firm, landlord
    from engine.labour import new_worker
    town = rtr_town()
    firm = busy_firm(town)
    landlord(town, homes=0)
    unit = bank_home(town, placed=False)
    newcomers_bring(town, 1_000_000)
    b = new_worker(town, firm)
    assert unit.owner is b and b.home_loan > 0


def test_in_the_labour_market_the_buyer_is_hired_and_only_the_next_newcomer_is_turned_away():
    from test_labour import busy_firm, landlord
    from engine.labour import labour_market
    town = rtr_town()
    firm = busy_firm(town)                                                   # it wants three this week
    housing = landlord(town, homes=0)
    unit = bank_home(town, placed=False)
    newcomers_bring(town, 1_000_000)
    before = town.population
    labour_market(town)
    arrivals = town.agents[before:]
    assert len(arrivals) == 1 and unit.owner is arrivals[0]
    assert arrivals[0].employer is firm and arrivals[0].role == "staff" and arrivals[0].wage == firm.wage
    assert firm.housing_blocked is True and housing.unmet_demand == 1.0      # the second found nothing to rent or buy
    assert town.no_home_week == town.week
    assert kinds(town, "arrival", "arrival_blocked") == ["arrival", "arrival_blocked"]


def test_a_founder_buys_with_the_cash_they_keep_back_and_the_venture_gets_all_its_capital():
    from engine.corporate import maybe_arrive_founder
    from engine.rtr_owning import newcomer_keeps
    town = rtr_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0")
    unit = bank_home(town, 1_000_000, placed=False)
    newcomers_bring(town, 50_000_000)                                        # $500,000: they keep a tenth, $50,000
    keep = newcomer_keeps(town)
    firm = maybe_arrive_founder(town)
    founder = town.agent(firm.founder_id)
    assert unit.owner is founder and founder.home_loan == 0                  # no income yet, so no loan: cash only
    assert founder.cash == 50_000_000 - 45_000_000 - 1_000_000 and founder.cash >= keep   # the venture got its nine tenths
    assert kinds(town, "arrival", "arrival_blocked", "foreclosed_sold") == ["foreclosed_sold", "arrival"]
    arrival = [e for e in town.rec.events if e["kind"] == "arrival"][-1]
    assert arrival["data"]["bought"] == unit.id and arrival["data"]["who"] == "founder"


def test_a_founder_whose_kept_cash_does_not_cover_the_price_is_turned_away():
    from engine.corporate import maybe_arrive_founder
    town = rtr_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0")
    unit = bank_home(town, 5_000_001, placed=False)                          # a cent over the tenth they keep
    newcomers_bring(town, 50_000_000)
    assert maybe_arrive_founder(town) is None and town.population == 0 and unit.owner is None
    assert kinds(town, "arrival", "arrival_blocked") == ["arrival_blocked"] and town.no_home_week == town.week


def test_with_the_dial_off_a_newcomer_must_rent_as_before():
    off = ["newcomers_buy=false"]
    from engine.corporate import maybe_arrive_founder
    from engine.labour import new_worker
    town, unit, shop = nothing_to_rent(3_000_000, *off)
    newcomers_bring(town, 5_000_000)
    assert new_worker(town, shop) is None and unit.owner is None
    town = rtr_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0", *off)
    unit = bank_home(town, 1_000_000, placed=False)
    newcomers_bring(town, 50_000_000)
    assert maybe_arrive_founder(town) is None and unit.owner is None


def test_in_the_wef_world_the_dial_is_not_read():
    from test_labour import busy_firm, landlord
    from conftest import empty_town
    from engine.labour import new_worker
    town = empty_town()
    firm = busy_firm(town)
    landlord(town, homes=0)
    town.foreclosed = [object()]                                             # were it read, this would be looked at
    state = town.rng.getstate()
    assert new_worker(town, firm) is None and town.rng.getstate() == state   # and no dice are rolled for the cash


# --- ruling 1: the owner class pays for repair work at any price -------------------------------------
# His words: "Yes, unless they are an owner class, then they'll get anyone to do repair work for them at
# any price. as an owner class, needs more time than money."
def owner_and_hand(cash=100_000):
    """Two people in work who each own a home that needs 1.6 hours and $43.20 of parts a week: one
    of the owner class, one not. And a repairer in work, whose hour is dearer than their own."""
    from test_rtr_2 import hours_for_the_week, maker, own_home, quiet_town, worker
    town = quiet_town()
    boss, hand = worker(town, cash=cash), worker(town, cash=cash)
    boss.klass, hand.klass = "owner", "working"
    for a in (boss, hand):
        own_home(town, a)
    m, h = maker(town, "repair", agent=worker(town))                 # 2,750 an hour; their own hour is worth 2,500
    hours_for_the_week(town)
    return town, boss, hand, h


def test_someone_of_the_owner_class_pays_a_dearer_repairer_though_they_have_the_hours():
    from test_rtr_2 import kept
    from engine import rtr_owning
    town, boss, hand, h = owner_and_hand()
    hours = boss.spare_hours
    rtr_owning.keep(town, hand)
    assert h.sold == 0 and hand.cash == 100_000 - 4_320 and hand.spare_hours == pytest.approx(hours - 1.6)
    rtr_owning.keep(town, boss)
    assert h.sold == pytest.approx(1.6) and boss.spare_hours == hours        # not an hour of their own
    assert boss.cash == 100_000 - 9_152                                      # (4,320 + 4,000) x 1.1
    assert kept(town, boss.unit["housing"]) and kept(town, hand.unit["housing"])


def test_any_price_means_any_price():
    from engine import rtr_owning
    town, boss, hand, h = owner_and_hand(cash=10_000_000)
    h.price = 50_000                                                         # $500 an hour
    rtr_owning.keep(town, hand)
    assert h.sold == 0
    rtr_owning.keep(town, boss)
    assert h.sold == pytest.approx(1.6) and boss.cash == 10_000_000 - 84_752     # 1.6 x 50,000 and the parts with a tenth on


def test_the_owner_class_pays_from_the_same_purse_as_anyone_cash_beyond_four_weeks_of_bills():
    from test_rtr_2 import shop
    from engine import rtr_owning
    from engine.subscriptions import subscribe
    town, boss, hand, h = owner_and_hand(cash=40_000)
    assert subscribe(town, boss, shop(town, "food", 10_000))                 # four weeks of bills: $400, all they have
    hours = boss.spare_hours
    rtr_owning.keep(town, boss)
    assert h.sold == 0 and boss.cash == 40_000 - 4_320                       # nothing beyond their bills: their own hours
    assert boss.spare_hours == pytest.approx(hours - 1.6)


def test_with_that_dial_off_the_owner_class_weighs_the_price_as_anyone_does():
    from test_rtr_2 import hours_for_the_week, maker, own_home, quiet_town, worker
    from engine import rtr_owning
    from engine.config import RTR_ONLY, load_config
    assert load_config(None, ["world=rtr"]).owners_pay_any_price is True and "owners_pay_any_price" in RTR_ONLY
    town = quiet_town("owners_pay_any_price=false")
    boss = worker(town, cash=100_000)
    boss.klass = "owner"
    own_home(town, boss)
    m, h = maker(town, "repair", agent=worker(town))
    hours_for_the_week(town)
    rtr_owning.keep(town, boss)
    assert h.sold == 0 and boss.cash == 100_000 - 4_320                      # their own hours, their own parts


# --- the deposit: the bank lends the whole price where the income allows ----------------------------
# The four fifths was the builder's number. His words for the loan: "if their income allows" (16/11),
# "as long as they have enough cash. Oh, good Enough income" (18/11), and, to "Should the bank lend the
# whole price of a home, or still ask a fifth in cash?": "Lend the whole price" (18/11).
def test_the_bank_lends_the_whole_price_in_the_rtr_world():
    from engine.config import load_config
    assert load_config(None, ["world=rtr"]).mortgage_ltv == 1.0
    assert load_config("rtr/settings.json").mortgage_ltv == 1.0


def test_the_whole_price_is_lent_if_the_payment_fits_their_income_and_nothing_with_no_income():
    town = rtr_town()
    a = town.add_agent()
    a.role, a.wage = "staff", 100_000
    assert town.bank.home_credit(a, 5_400_000) == 5_400_000                 # all of $54,000
    a.wage = 20_000                                                          # 30% of $200 is $60 a week
    credit = town.bank.home_credit(a, 5_400_000)
    assert 0 < credit < 5_400_000 and town.bank.home_first_payment(credit) <= 6_000
    a.role, a.wage = None, 0
    assert town.bank.home_credit(a, 5_400_000) == 0                          # no income, no loan (J)


def test_a_newcomer_with_no_more_than_they_hold_back_buys_on_the_wage_alone():
    from engine.labour import new_worker
    from engine.rtr_owning import newcomer_keeps
    town, unit, shop = nothing_to_rent()
    keep = newcomer_keeps(town)
    newcomers_bring(town, keep - 1)                                          # nothing to put in
    b = new_worker(town, shop)
    assert unit.owner is b and (b.cash, b.home_loan) == (keep - 1, 3_000_000)


def test_someone_in_work_with_no_savings_buys_the_banks_home_and_someone_out_of_work_does_not():
    from test_rtr import _buyer, _foreclosed
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed()
    jobless = _buyer(town, 5_000)
    jobless.employer.staff.remove(jobless)
    jobless.employer = jobless.role = None
    jobless.wage = 0
    sell_foreclosed(town)
    assert unit.owner is None                                                # no income, no loan
    poor = _buyer(town, 5_000)                                               # $50 to their name, and a job at $1,000 a week
    sell_foreclosed(town)
    assert unit.owner is poor and (poor.cash, poor.home_loan) == (5_000, 3_000_000)


def test_a_tenant_in_work_with_no_savings_builds_and_every_part_is_the_banks():
    from engine.rtr_owning import consider_building, owns, work
    town, a, landlord = _tenant_with_a_job(cash=0)
    consider_building(town, a)
    assert a.build is not None
    for _ in range(100):
        a.spare_hours = 20.0
        work(town, a)
        if a.build is None:
            break
    assert owns(a, "housing") and (a.home_loan, a.cash) == (5_400_000, 0)
    assert town.ledger.total_out["import"] == 5_400_000


def test_where_the_dial_asks_a_fifth_in_cash_someone_without_it_goes_on_renting():
    from engine.rtr_owning import consider_building
    town, a, landlord = _tenant_with_a_job(1_000_000, "mortgage_ltv=0.8")   # a fifth is $10,800, plus four weeks of rent
    consider_building(town, a)
    assert a.build is None


def test_a_builder_brings_materials_the_bank_lends_in_full_and_the_owner_pays_for_the_hours():
    from test_rtr_2 import builder_next_door, building_tenant, hours_for_the_week
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    a.spare_hours, per_hour, cash = 20.0, 4_500, a.cash              # 500 units at $108 over 1,200 hours
    rtr_owning.work(town, a)
    paid = round(60 * (h.price + per_hour * 1.1))                    # sixty hours bought, materials with the tenth on
    assert a.build.hours_left == pytest.approx(1_200 - 80)           # and twenty of their own
    assert a.home_loan == 80 * per_hour == a.build.borrowed          # every part is the bank's, whoever did the hours
    assert a.cash == cash - (paid - 60 * per_hour)                   # theirs to find: the builder's hours and the tenth


def test_someone_with_no_savings_who_could_build_for_less_a_week_does_not_buy_the_banks_home():
    from test_rtr import _buyer, _foreclosed
    from engine.rtr_owning import sell_foreclosed
    town, a, unit = _foreclosed(debt=6_000_000)                      # $60,000 asked; a home costs $54,000 to build
    poor = _buyer(town, 5_000)
    sell_foreclosed(town)
    assert unit.owner is None and unit in town.foreclosed and poor.home_loan == 0    # they would build: the bank lends all of that too
    unit.ask = 5_000_000
    sell_foreclosed(town)
    assert unit.owner is poor                                        # at $50,000 buying comes to less


def test_an_owner_buys_a_home_to_let_against_the_whole_value_of_what_they_own():
    from test_rtr_1b import foreclosed_home, second_owner
    from engine.rtr_owning import _spare_cash, letting_terms
    town, a, unit = foreclosed_home(debt=3_000_000)
    owner = second_owner(town, cash=1_000_000)                       # $1,000 a week; their home is worth $54,000
    owner.home_loan = 5_400_000                                      # and they owe all of it: bought with the whole price lent
    assert letting_terms(town, owner, 3_000_000, 33_000) == 3_000_000 - _spare_cash(town, owner) > 0


def test_an_owner_with_no_savings_builds_to_let_and_every_part_is_the_banks():
    from test_rtr_1b import _build_out, owner_in_town
    from engine.rtr_owning import consider_building_to_let, letting_of
    town, owner, unit = owner_in_town(cash=0)
    town.no_home_week = town.week                                    # a newcomer was turned away: a home is wanted
    consider_building_to_let(town, owner)
    assert owner.build is not None and owner.build.to_let
    _build_out(town, owner)
    assert len(letting_of(town, owner).units) == 1 and (owner.home_loan, owner.cash) == (5_400_000, 0)


# --- whole towns as the RTR world now ships: every rule on, the whole price lent ----------------------
def _reached_today(town, seen):
    """What a town's record shows of the rulings of 18 November."""
    lent = {}
    for e in town.rec.events:
        kind = e["kind"]
        if kind == "home_loan":
            lent[(e["agent"], e["week"])] = e["amount"]
        elif kind in ("foreclosed_sold", "home_bought") and lent.get((e["agent"], e["week"])) == e["amount"]:
            seen["a home bought with the whole price lent"] += 1
        elif kind == "arrival" and "bought" in e["data"]:
            seen["a newcomer bought on arriving"] += 1
        elif kind == "offer_refused" and e["data"].get("why") == "side hustle":
            seen["a maker turned down a job that paid no more than the side hustle"] += 1


STRANDED = "the most weeks any one of these towns had more than half its people with no job"


def run_as_shipped(seeds, place, years=14):
    """Towns of 200 run under the weekly checks exactly as the RTR world ships, with a count of what
    they reached of the rulings of 18 and 19 November and of the rules of the stages before.
    Returns (what the checks found, what was reached)."""
    import collections
    import test_rtr_1b
    import test_rtr_2
    from engine import corporate, rtr_makers, rtr_owning
    from engine.config import load_config
    from engine.town import Town
    from test_town_invariants import run_checked
    real, real_least, real_share = rtr_owning._repairer, rtr_makers.least_wage, corporate.line_share
    problems, seen, weighed, home_only, wants_out = [], collections.Counter(), [], set(), []

    def least(town, agent, reservation):
        # someone whose side hustle brings in more than they would otherwise work for: with a large loan;
        # or with no large loan but more than half still owed on their home; or unhappy, with no large loan
        if agent.hustle is not None and agent.hustle.profit_week >= reservation:
            if rtr_makers.owes_a_large_loan(agent):
                weighed.append((agent, agent.hustle.profit_week))
            else:
                if rtr_makers.owes_a_large_loan(agent, home_counts=True):
                    home_only.add(agent.id)
                if not agent.happy:
                    wants_out.append((agent, agent.hustle.profit_week))
        return real_least(town, agent, reservation)

    def watched(town, agent, hours, cost, need=None):
        # someone of the owner class with the hours to do it, and no repairer cheaper than their own hour
        cheapest = rtr_makers.cheapest_hour(town, agent, "repair")
        dear = cheapest is not None and cheapest >= town.hour_value - cost / hours * town.cfg.maker_margin
        theirs = agent.klass == "owner" and agent.spare_hours >= hours and dear
        got = real(town, agent, hours, cost, need)
        if theirs and got > 0:
            seen["the owner class had a repair done at any price"] += 1
        return got

    def share(town, wage):
        # a firm short of profit with no job going: more than a twentieth of the town has no job,
        # and no more than a twentieth would take the lower rate
        got = real_share(town, wage)
        if town.jobless_share() > town.cfg.wage_cut_unemployment >= got:
            seen["a firm short of profit kept its rate: those with no job would not take less"] += 1
        return got

    rtr_owning._repairer, rtr_makers.least_wage, corporate.line_share = watched, least, share
    try:
        for seed in seeds:
            town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false",
                                           f"seed={seed}"] + place))
            cfg = town.cfg
            assert cfg.mortgage_ltv == 1.0 and cfg.newcomers_buy and cfg.owners_pay_any_price
            assert cfg.makers_weigh_jobs and cfg.makers_buy_in_town and not cfg.home_loan_presses
            assert cfg.line_is_who_would_take and cfg.unhappy_makers_apply and cfg.staff_keep_pay
            hours_sold, wages_paid, idle = 0.0, 0, 0
            for _ in range(years * 52):
                del weighed[:]
                del wants_out[:]
                home_only.clear()
                events = len(town.rec.events)
                problems += run_checked(town, 1)
                week = town.rec.events[events:]
                stayed = {e["agent"] for e in week
                          if e["kind"] == "offer_refused" and e["data"].get("why") == "side hustle"}
                if stayed & home_only:
                    seen["owing most of a home loan, a maker turned down a job that paid no more than the side hustle"] += 1
                hours_sold += sum(h.sold for h in town.hustles if h.spec is None)
                wages_paid += sum(h.w_wages for h in town.hustles)
                if any(a.build is not None and a.build.borrowed == a.build.spent > 0 for a in town.agents):
                    seen["a home being built with every part lent"] += 1
                if any(a.role == "staff" and a.wage <= brought for a, brought in weighed):
                    seen["with a large loan, a maker took a job that paid no more than the side hustle"] += 1
                if any(a.role == "staff" and a.wage <= brought for a, brought in wants_out):
                    seen["unhappy on a side hustle, a maker took a job that paid no more than it brought in"] += 1
                if town.ledger.week_internal.get("town_goods", 0) > 0:
                    seen["a maker bought goods from a firm in town"] += 1
                    if town.ledger.week_out.get("import", 0) > 0:
                        seen["and goods came from outside the same week"] += 1
                if any(f.town_target > 0 and f.staff for f in town.alive_firms):
                    seen["a firm had an order from the town's makers"] += 1
                for e in week:                                       # 19 November: whose pay a change of rate touches
                    if e["kind"] != "wage_change":
                        continue
                    firm = town.firm(e["firm"])
                    if e["data"]["reason"] == "queue" and firm.alive and any(a.wage > firm.wage for a in firm.staff):
                        seen["a firm cut its rate and its staff kept theirs"] += 1
                    if e["data"]["reason"] == "unfilled" and firm.alive and any(a.wage > firm.wage for a in firm.staff):
                        seen["a firm bid its rate up while some of its staff were on more"] += 1
                if any(len({a.wage for a in f.staff}) > 1 for f in town.alive_firms):
                    seen["a firm had staff on more than one rate"] += 1
                if any(w.wage > h.wage for h in town.hustles for w in h.staff):
                    seen["a small business kept its staff on more than the going wage"] += 1
                idle += town.jobless_share() > 0.5
                if len(problems) > 20:
                    break
            seen[STRANDED] = max(seen[STRANDED], idle)
            _reached_today(town, seen)
            seen += test_rtr_1b._reached(town)                   # and the rules of the stages before
            seen += test_rtr_2._reached(town, hours_sold, wages_paid)
    finally:
        rtr_owning._repairer, rtr_makers.least_wage, corporate.line_share = real, real_least, real_share
    return problems, seen


SHIPPED = (("map", (38, 40), ["map_width=7", "map_height=7"]), ("no map", (10, 14), ["map_width=0"]))


@pytest.fixture(scope="module")
def towns_of_today():
    """Towns of 200 run for fourteen years under the weekly checks exactly as the RTR world ships:
    seeds 38 and 40 on a 7 by 7 map, seeds 10 and 14 with no map (picked on 19 November from forty of
    each, all eighty clean under the checks, run with that day's rulings and the fresh review's fixes,
    for reaching the rules of the stages before as well and for not being towns that stop; the seeds
    of 18 November were picked the same way, twice). For each kind: (what the checks found, what was
    reached)."""
    return {kind: run_as_shipped(seeds, place) for kind, seeds, place in SHIPPED}


TODAY = ["a home bought with the whole price lent", "a home being built with every part lent",
         "the owner class had a repair done at any price",
         "a maker turned down a job that paid no more than the side hustle",
         "with a large loan, a maker took a job that paid no more than the side hustle",
         "owing most of a home loan, a maker turned down a job that paid no more than the side hustle",
         "a firm had an order from the town's makers", "a maker bought goods from a firm in town",
         # 19 November: who is in the line, and whose pay a change of rate touches
         "a firm short of profit kept its rate: those with no job would not take less",
         "unhappy on a side hustle, a maker took a job that paid no more than it brought in",
         "a firm cut its rate and its staff kept theirs", "a firm bid its rate up while some of its staff were on more",
         "a firm had staff on more than one rate", "a small business kept its staff on more than the going wage"]


# Not asked of these towns: "a newcomer bought on arriving". No town run so far reaches it (three full
# towns and forty small ones, 18 November): workers come only while a town grows and the bank holds
# homes only once it has stopped. Its own tests hold it.
@pytest.mark.parametrize("kind", ["map", "no map"])
def test_towns_as_shipped_keep_their_accounts_and_places_and_reach_the_rulings(towns_of_today, kind):
    problems, seen = towns_of_today[kind]
    assert problems == []
    for rule in TODAY:
        assert seen[rule] > 0, f"these towns never reached '{rule}': pick seeds that do ({dict(seen)})"
    # The books can balance in a town that has stopped. On 19 November a costing rule of the builder's
    # left towns like these with nine in ten out of work for years (a firm reckoned what it sells outside
    # at what its staff keep, so a cut for newcomers brought no work), and every weekly check passed.
    # A small capped town can stop without any fault (of eighty before that day's rules the worst had
    # more than half its people out of work for 304 weeks of 728); these four were picked among those
    # that do not (0 to 64 such weeks), so that a change which stops them is loud. With the fault the
    # worst of twenty had 600.
    assert seen[STRANDED] <= 156, f"one of these towns had more than half its people out of work for {seen[STRANDED]} weeks"


# --- ruling 2: someone out of work with a side hustle, and the jobs on offer ---------------------------
# His words: "they will only take the first job offered if they have a large loan, So they've only paid
# off less than 50% of their loan They will take the job." And, to "A side hustle brings in $200 a week,
# no loan: do they take a $600 a week job?": "Yes, take it".
def maker_and_a_job(brings=20_000, pays=60_000, *overrides):
    """Someone out of work whose side hustle brought in `brings` a week over the last quarter, who would
    take $100 a week if they had nothing else; and a firm with jobs going at `pays`."""
    from test_labour import busy_firm
    from test_rtr_2 import maker, quiet_town
    town = quiet_town(*overrides)
    firm = busy_firm(town)
    firm.wage = pays
    a, h = maker(town, "entertainment")
    a.last_wage = 10_000
    h.profit_week = brings
    return town, a, h, firm


def refusals(town):
    return [(e["amount"], e["data"].get("why")) for e in town.rec.events if e["kind"] == "offer_refused"]


def test_the_dial_for_makers_and_jobs_is_on_and_is_one_of_the_rtr_worlds_own():
    from engine.config import RTR_ONLY, load_config
    assert load_config(None, ["world=rtr"]).makers_weigh_jobs is True and "makers_weigh_jobs" in RTR_ONLY


def test_a_maker_out_of_work_takes_a_job_that_pays_more_than_the_side_hustle_brings_in():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=20_000, pays=60_000)           # his example: $200 a week against $600
    labour_market(town)
    assert a.employer is firm and a.wage == 60_000 and a.hustle is h         # the side hustle is still theirs
    assert refusals(town) == []


def test_with_no_loan_they_stay_when_the_job_pays_no_more_than_the_side_hustle():
    from engine.labour import labour_market
    for brings in (60_000, 70_000):
        town, a, h, firm = maker_and_a_job(brings=brings, pays=60_000)
        labour_market(town)
        assert a.employer is None and refusals(town) == [(60_000, "side hustle")]
    town, a, h, firm = maker_and_a_job(brings=59_999, pays=60_000)
    labour_market(town)
    assert a.employer is firm


def test_someone_out_of_work_with_no_side_hustle_takes_the_job_as_before():
    from test_rtr_2 import jobless
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)
    b = jobless(town)
    b.last_wage = 10_000
    labour_market(town)
    assert b.employer is firm and a.employer is None


def owe(a, h, which, amount):
    if which == "personal":
        a.loan = amount
    elif which == "home":
        a.home_loan = amount
    else:
        h.loan = amount


@pytest.mark.parametrize("which", ["personal", "business"])
def test_with_a_loan_less_than_half_paid_off_they_take_the_job_whatever_it_pays(which):
    from engine import rtr_makers
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)
    owe(a, h, which, 100_000)
    rtr_makers.start_week(town)                                              # the most owed is noted as the week starts
    owe(a, h, which, 50_000)                                                 # half paid off: not less than half
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, "side hustle")]
    owe(a, h, which, 50_001)                                                 # a cent less than half paid off
    labour_market(town)
    assert a.employer is firm


def test_the_most_owed_on_each_loan_is_remembered_until_that_loan_is_paid_off():
    from engine import rtr_makers
    town, a, h, firm = maker_and_a_job()
    assert not rtr_makers.owes_a_large_loan(a)
    a.loan, a.home_loan, h.loan = 100_000, 3_000_000, 500_000
    assert rtr_makers.owes_a_large_loan(a)                                   # a loan just taken counts at once
    rtr_makers.start_week(town)
    assert (a.loan_top, a.home_loan_top, h.loan_top) == (100_000, 3_000_000, 500_000)
    a.loan, a.home_loan, h.loan = 40_000, 3_100_000, 0                       # part paid; a missed week added interest; paid off
    rtr_makers.start_week(town)
    assert (a.loan_top, a.home_loan_top, h.loan_top) == (100_000, 3_100_000, 0)
    assert not rtr_makers.owes_a_large_loan(a)                               # the home loan is not one (Jason: "No, stay")
    assert rtr_makers.owes_a_large_loan(a, home_counts=True)                 # where the dial counts it, it is
    a.home_loan = 1_550_000
    assert not rtr_makers.owes_a_large_loan(a, home_counts=True)             # half of one paid, more than half of the other
    a.loan = 0
    rtr_makers.start_week(town)
    a.loan = 30_000                                                          # borrowed again, less than was once owed
    rtr_makers.start_week(town)
    assert a.loan_top == 30_000 and rtr_makers.owes_a_large_loan(a)


def test_with_that_dial_off_a_maker_out_of_work_takes_the_first_job_offered_as_anyone_does():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(70_000, 60_000, "makers_weigh_jobs=false")
    labour_market(town)
    assert a.employer is firm


def test_a_job_under_what_they_would_take_with_nothing_else_is_still_refused_as_before():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=0, pays=60_000)
    a.last_wage, a.security = 100_000, 1.0                                   # they would not work for under $1,000
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, None)]
    a.loan = 100_000                                                         # nor with a loan to pay
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, None)] * 2


def test_they_do_not_move_house_for_a_job_that_pays_no_more_than_the_side_hustle():
    from test_places import block, premises, tenant
    from test_rtr import map_rtr_town
    from test_rtr_2 import NOBODY_STARTS
    from engine.labour import labour_market
    from engine.rtr_makers import open_hustle
    for brings, goes in ((100_000, False), (99_999, True)):
        town = map_rtr_town(*NOBODY_STARTS)
        landlord = premises(town, "housing", 6, 5)
        old = block(town, landlord, 0, 0, homes=1)
        a = tenant(town, old)
        new = block(town, landlord, 11, 12)                                  # homes free beside the job, far from theirs
        firm = premises(town, "food", 12, 12, customers=10)                  # it pays $1,000 a week
        open_hustle(town, a, "entertainment").profit_week = brings
        labour_market(town)
        assert (a.employer is firm) is goes and (a.unit["housing"].spot is new) is goes


def test_a_small_business_takes_on_a_maker_out_of_work_only_by_the_same_rule():
    from test_rtr_2 import customers, hours_for_the_week, make_business, maker, quiet_town, turned_away
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town, cash=100_000)                                 # a week of a wage in hand
    make_business(town, h)                                           # it pays the going wage, $1,000 a week
    (rival, hr), (owing, ho) = maker(town, "food"), maker(town, "food")
    for m, hm in ((rival, hr), (owing, ho)):
        m.last_wage, hm.profit_week = 10_000, 100_000                # their own side hustles bring in as much as the job pays
    owing.loan = 50_000                                              # and one of them has a loan to pay
    customers(town, h, 30)
    turned_away(town, h, 20)                                         # 100 hours wanted, 60 of the owner's: one worker
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.staff == [owing] and rival.role is None


def test_between_them_the_towns_as_shipped_reach_every_rule_of_the_stages_before(towns_of_today):
    """The whole-town tests of stages 1b and 2 run the towns their seeds were picked for, as the world
    was then. These are towns as it is now. On the map they reach every rule those tests ask for
    but one (a landlord short of cash selling a let home to another landlord, which stage 1b's own
    towns and tests hold); with no map, all but that and a block made into plots (there are no
    blocks)."""
    import test_rtr_2
    older = (test_rtr_2.PART_A + test_rtr_2.PART_B + test_rtr_2.RARE
             + ["bought from the landlord by its tenant", "bought from the landlord by its empty", "foreclosed home to a renter",
                "block_to_plots", "home built to let and let", "foreclosed home to an owner who lets it",
                "let home sold to an owner, tenant staying", "let home sold to another landlord, tenant staying",
                "let home taken by the bank, tenant staying", "foreclosed home sold with its tenant staying"])
    on_the_map, no_map = towns_of_today["map"][1], towns_of_today["no map"][1]
    assert [r for r in older if on_the_map[r] == 0] == []
    assert [r for r in older if no_map[r] == 0] == ["block_to_plots"]        # with no map there are no blocks


def test_a_town_as_shipped_where_every_firm_closes_still_balances():
    """Stage 2's test of the same name, in a town as the world is now (its own seed no longer has a
    business with staff and a loan standing: someone with a side hustle of their own takes a job only
    if it pays more). The seed was picked again on 19 November, with that day's rulings: of seeds 1 to
    24, twelve have such a business by the seventh year."""
    from engine.config import load_config
    from engine.corporate import wind_up
    from engine.town import Town
    from test_town_invariants import run_checked
    town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false", "seed=1",
                                   "map_width=7", "map_height=7"]))
    for year in range(13):                       # on until businesses with staff and loans are standing
        assert run_checked(town, 52) == []
        if year >= 6 and any(h.staff for h in town.hustles) and any(h.loan > 0 for h in town.hustles):
            break
    else:
        pytest.fail("no business with staff and a loan in thirteen years: pick another seed")
    for firm in list(town.alive_firms):          # every landlord and shop is gone in a week
        wind_up(town, firm, "test")
    assert run_checked(town, 3 * 52) == []


# --- ruling 3: a maker buys their goods in town first ------------------------------------------------
# His words: "they can only buy outside the town if they can't get it inside town at a reasonable price
# first." And, of ingredients at $189 from outside and $200 in town: "I would say yes buys in town because
# it's only $11 difference and they get it sooner. where if it was $189 and in town it was $298 That would
# get it from out of town".
def food_town(*overrides):
    """A food firm with five staff and no customers of its own, paying $1,000 a week; and someone
    out of work selling food to eight customers (all their sixty hours will serve), who needs eight
    units of the good a week."""
    from test_rtr_2 import customers, maker, quiet_town, shop
    town = quiet_town(*overrides)
    firm = shop(town, "food", 40_000)
    a, h = maker(town, "food")
    customers(town, h, 8, cash=500_000)
    return town, firm, a, h


def pays_its_staff(firm, wage):
    """The firm's rate, and what everyone on its staff is paid (since 19 November 2026 its staff keep
    rates of their own, and what a unit costs it to make follows what it pays them)."""
    firm.wage = wage
    for a in firm.staff:
        a.wage = wage


def a_whole_week(town):
    """The week as the town runs it, for the parts that touch goods: orders, the firms' work, the
    makers' customers, the bills, and the goods bought out of the takings."""
    from engine import rtr_makers, rtr_owning
    from engine.household import pay_bills
    from engine.production import operate
    town.ledger.start_week()
    for f in town.firms:
        f.w_revenue = f.w_export = 0
    rtr_owning.start_week(town)
    rtr_makers.start_week(town)
    operate(town)
    rtr_makers.working_week(town)
    pay_bills(town)
    rtr_owning.after_bills(town)
    rtr_makers.after_bills(town)


def test_the_dials_for_buying_in_town_are_on_and_are_the_rtr_worlds_own():
    from engine.config import RTR_ONLY, load_config
    cfg = load_config(None, ["world=rtr"])
    assert cfg.makers_buy_in_town is True and cfg.town_goods_premium == 0.10
    assert {"makers_buy_in_town", "town_goods_premium"} <= set(RTR_ONLY)


def test_a_little_over_the_outside_price_is_reasonable_and_far_over_is_not():
    from engine.config import load_config
    from engine.rtr_makers import reasonable
    cfg = load_config(None, ["world=rtr"])
    assert reasonable(cfg, 18_900, 20_000)                                   # his example: $200 against $189, "yes buys in town"
    assert not reasonable(cfg, 18_900, 29_800)                               # and $298 against $189: "from out of town"
    assert reasonable(cfg, 18_900, 20_790) and not reasonable(cfg, 18_900, 20_791)   # the line between them: a tenth over


def test_a_firm_asks_what_a_unit_costs_it_to_make_and_a_tenth_and_never_less_than_the_outside_pays_it():
    from engine.rtr_makers import town_price
    town, firm, a, h = food_town()
    assert town_price(town, firm) == 16_940                                  # $140 of work, a tenth for overhead, a tenth on that
    pays_its_staff(firm, 60_000)
    assert town_price(town, firm) == 16_800                                  # it would make it for $101.64: it asks what it gets outside


def test_what_makers_wanted_last_week_the_towns_firm_makes_for_them_this_week_and_they_buy_it():
    from engine.labour import labour_need
    town, firm, a, h = food_town()
    a_whole_week(town)                                                       # nothing was ordered: all eight units from outside
    assert town.ledger.week_out["import"] == 151_200 and "town_goods" not in town.ledger.week_internal
    assert town.goods_wanted == {"food": 8.0} and (firm.town_target, firm.town_units) == (0.0, 0.0)
    without = labour_need(firm, town.cfg)
    a_whole_week(town)
    assert firm.town_target == 8.0 and town.goods_wanted == {"food": 8.0}    # last week's order made; this week's noted
    assert labour_need(firm, town.cfg) == pytest.approx(without + 8 * 0.14)  # and it staffs for it, as for exports
    assert town.ledger.week_internal["town_goods"] == 135_520 and town.ledger.week_out.get("import", 0) == 0
    assert firm.w_revenue == 135_520 and h.w_goods == 135_520 and firm.town_units == 0.0
    assert firm.w_export == 0                                                # nothing left over to send outside


def test_what_the_town_cannot_supply_comes_from_outside():
    from engine import rtr_makers
    town, firm, a, h = food_town()
    a_whole_week(town)
    firm.staff = firm.staff[:1]                                              # one worker makes 7.14 units, not eight
    a_whole_week(town)
    assert town.ledger.week_internal["town_goods"] == 121_000                # 7.14 units at $169.40
    assert town.ledger.week_out["import"] == 16_200                          # and the other 0.86 at $189
    assert h.w_goods == 121_000 + 16_200 and rtr_makers is not None


def test_a_firm_whose_price_is_more_than_a_tenth_over_the_outside_price_gets_no_orders():
    from engine.rtr_makers import town_price
    town, firm, a, h = food_town()
    pays_its_staff(firm, 122_000)
    assert town_price(town, firm) == 20_667                                  # dearer than $189, within the tenth: they buy in town
    a_whole_week(town)
    a_whole_week(town)
    assert firm.town_target == 8.0 and town.ledger.week_internal["town_goods"] == 165_336
    pays_its_staff(firm, 123_000)
    assert town_price(town, firm) == 20_836                                  # over $207.90
    a_whole_week(town)
    assert firm.town_target == 0.0 and town.ledger.week_out["import"] == 151_200
    assert "town_goods" not in town.ledger.week_internal


def test_two_firms_share_the_order_and_the_cheaper_is_bought_from_first():
    from test_rtr_2 import shop
    town, firm, a, h = food_town()
    dear = shop(town, "food", 40_000)
    pays_its_staff(dear, 110_000)                                            # it asks $186.34
    a_whole_week(town)
    a_whole_week(town)
    assert (firm.town_target, dear.town_target) == (4.0, 4.0)
    assert firm.w_revenue == 4 * 16_940 and dear.w_revenue == 4 * 18_634
    town.goods_wanted["food"] = 30.0                                         # were more made than wanted: the cheaper sells first
    a_whole_week(town)
    assert (firm.town_target, dear.town_target) == (15.0, 15.0)
    assert firm.w_revenue == 8 * 16_940 and dear.w_revenue == 0
    assert dear.w_export == 15 * 16_800 and firm.w_export == 7 * 16_800      # what nobody in town took went outside


def test_a_firm_makes_for_makers_in_town_before_it_makes_for_export():
    from engine.production import operate
    town, firm, a, h = food_town()
    firm.town_target, firm.export_target = 10.0, 20.0
    operate(town)                                                            # five staff could make 35.7 units
    assert firm.town_units == 10.0 and firm.export_units == pytest.approx(20.0)
    firm.staff = firm.staff[:2]                                              # two could make 14.3
    operate(town)
    assert firm.town_units == 10.0 and firm.export_units == pytest.approx(2 / 0.14 - 10)


def test_with_that_dial_off_a_maker_buys_everything_from_outside_as_before():
    town, firm, a, h = food_town("makers_buy_in_town=false")
    a_whole_week(town)
    a_whole_week(town)
    assert town.goods_wanted == {} and firm.town_target == 0.0
    assert town.ledger.week_out["import"] == 151_200 and "town_goods" not in town.ledger.week_internal


def test_a_repairers_parts_come_from_a_firm_in_town_when_it_has_them():
    from test_rtr_2 import hours_for_the_week, kept, maker, own_home, quiet_town, worker
    from engine import rtr_owning
    town = quiet_town()
    owner = worker(town, cash=100_000)                                       # on the staff of a landlord with no homes
    unit = own_home(town, owner)                                             # needs 1.6 hours and 0.4 units of materials a week
    m, h = maker(town, "repair")
    hours_for_the_week(town)
    landlord = owner.employer
    landlord.town_units = 1.0                                                # it asks $96.80 a unit; the outside asks $108
    rtr_owning.keep(town, owner)
    assert owner.cash == 100_000 - 7_832                                     # the customer pays what they paid before
    assert town.ledger.week_internal["town_goods"] == 3_872 and "import" not in town.ledger.week_out
    assert h.cash == 7_832 - 3_872 and landlord.town_units == pytest.approx(0.6) and kept(town, unit)
    assert town.goods_wanted == {"housing": pytest.approx(0.4)}


def test_a_premium_under_nothing_is_refused():
    from engine.config import load_config
    with pytest.raises(ValueError, match="town_goods_premium"):
        load_config(None, ["world=rtr", "town_goods_premium=-0.01"])
    assert load_config(None, ["world=rtr", "town_goods_premium=0"]).town_goods_premium == 0.0   # no dearer than outside


def test_a_builders_materials_come_from_a_firm_in_town_too():
    from test_rtr_2 import builder_next_door, building_tenant, hours_for_the_week
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    landlord = town.firms_for("housing")[0]
    landlord.town_units = 1_000.0                                    # it asks $96.80 a unit; the outside asks $108
    a.spare_hours, cash = 20.0, a.cash
    rtr_owning.work(town, a)                                         # sixty hours bought: 25 units of materials
    assert town.ledger.week_internal["town_goods"] == 242_000 and landlord.town_units == pytest.approx(975.0)
    assert a.cash == cash - (round(60 * (h.price + 4_500 * 1.1)) - 60 * 4_500)   # the owner pays what they paid before


def test_the_parts_come_from_town_whichever_way_the_repairer_was_hired():
    from test_rtr_2 import hours_for_the_week, maker, own_home, quiet_town, worker
    from engine import rtr_owning
    town, boss, hand, h = owner_and_hand()                           # the owner class: at any price
    landlord = boss.employer
    landlord.town_units = 1.0
    rtr_owning.keep(town, boss)
    assert town.ledger.week_internal["town_goods"] == 3_872 and "import" not in town.ledger.week_out
    town = quiet_town()                                              # someone with no hours of their own to spare
    busy = worker(town, cash=100_000)
    own_home(town, busy)
    m, h = maker(town, "repair", agent=worker(town))                 # dearer than their own hour
    hours_for_the_week(town)
    busy.spare_hours = 0.0
    busy.employer.town_units = 1.0
    rtr_owning.keep(town, busy)
    assert town.ledger.week_internal["town_goods"] == 3_872 and "import" not in town.ledger.week_out


# --- the fresh review of 18/11/2026: what it found, pinned ----------------------------------------------
def saved_settings(tmp_path, *left_out, world="rtr"):
    """A full set of settings as a run folder keeps it, less the dials named: a file saved
    before those dials existed."""
    import json
    from engine.config import load_config
    data = load_config(None, [f"world={world}"]).to_dict()
    for name in left_out:
        del data[name]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_a_full_settings_file_saved_before_a_dial_existed_is_refused_and_the_dials_are_named(tmp_path):
    from engine.config import load_config
    path = saved_settings(tmp_path, "makers_buy_in_town", "newcomers_buy")
    with pytest.raises(ValueError) as refused:
        load_config(path)
    said = str(refused.value)
    assert "makers_buy_in_town" in said and "newcomers_buy" in said          # each one missing, by name
    assert "owners_pay_any_price" not in said and "--set" in said            # and only those; and the way out


def test_the_file_loads_once_every_missing_dial_is_given():
    import tempfile, pathlib
    from engine.config import load_config
    with tempfile.TemporaryDirectory() as folder:
        path = saved_settings(pathlib.Path(folder), "makers_buy_in_town", "newcomers_buy")
        cfg = load_config(path, ["makers_buy_in_town=false", "newcomers_buy=false"])
        assert (cfg.makers_buy_in_town, cfg.newcomers_buy, cfg.makers_weigh_jobs) == (False, False, True)
        with pytest.raises(ValueError, match="newcomers_buy"):
            load_config(path, ["makers_buy_in_town=false"])                  # one given, one still missing


def test_a_full_file_with_every_dial_and_a_short_file_load_as_they_did(tmp_path):
    from engine.config import load_config
    assert load_config(saved_settings(tmp_path)).to_dict() == load_config(None, ["world=rtr"]).to_dict()
    short = tmp_path / "short.json"
    short.write_text('{"world": "rtr", "seed": 5}', encoding="utf-8")
    cfg = load_config(str(short))                                            # a short file changes a few dials of today's world
    assert cfg.seed == 5 and cfg.makers_buy_in_town is True


def test_a_wef_world_file_may_leave_out_only_what_the_rtr_world_alone_reads(tmp_path):
    from engine.config import RTR_ONLY, load_config
    assert load_config(saved_settings(tmp_path, *RTR_ONLY, world="wef")).world == "wef"
    with pytest.raises(ValueError, match="habit_weeks"):
        load_config(saved_settings(tmp_path, *RTR_ONLY, "habit_weeks", world="wef"))
    with pytest.raises(ValueError, match="mortgage_ltv"):                    # asked to be the RTR world, it reads them
        load_config(saved_settings(tmp_path, *RTR_ONLY, world="wef"), ["world=rtr"])


def test_goods_a_firm_asks_nothing_for_are_taken_for_nothing_and_the_week_goes_on():
    from engine.rtr_makers import town_price
    town, firm, a, h = food_town("needs.food.make_labour=0.0000001", "needs.food.export_price=0")
    assert town_price(town, firm) == 0
    a_whole_week(town)
    a_whole_week(town)                                                       # it stopped here, dividing by the price
    assert firm.town_target == 8.0 and firm.town_units == 0.0                # all eight taken from the town's firm
    assert h.w_goods == 0 and town.ledger.week_out.get("import", 0) == 0     # and nothing paid, in town or outside


def test_a_maker_short_of_cash_takes_from_the_towns_firm_only_what_the_till_will_pay_for():
    from engine.rtr_makers import buy_goods
    town, firm, a, h = food_town()
    spec = town.needs["food"]
    firm.town_units, h.cash, had = 8.0, 50_000, firm.cash                    # it asks $169.40 a unit; the till holds $500
    assert buy_goods(town, h, spec, 8.0, 8 * spec.import_price) == 50_000
    assert h.cash == 0 and firm.cash == had + 50_000
    assert firm.town_units == pytest.approx(8.0 - 50_000 / 16_940)           # 2.95 units, not the eight on the shelf


def test_the_rest_from_outside_is_held_to_what_is_left_in_the_till():
    from engine.rtr_makers import buy_goods
    town, firm, a, h = food_town()
    spec = town.needs["food"]
    firm.town_units, h.cash, had = 2.0, 50_000, firm.cash                    # two units in town, $338.80; six more wanted
    assert buy_goods(town, h, spec, 8.0, 8 * spec.import_price) == 50_000
    assert h.cash == 0 and firm.cash == had + 33_880 and firm.town_units == pytest.approx(0.0)


def test_what_nobody_took_is_counted_with_the_units_the_firm_sent_outside():
    from engine import rtr_makers
    town, firm, a, h = food_town()
    firm.town_units, sent, had = 3.0, firm.export_units, firm.cash
    rtr_makers.sell_leftovers(town)
    assert firm.cash == had + 3 * 16_800 and firm.town_units == 0.0          # three units at $168, what the outside pays
    assert firm.export_units == pytest.approx(sent + 3.0)


def test_a_home_loan_paid_off_is_forgotten_and_the_next_is_measured_on_its_own():
    from engine import rtr_makers
    town, a, h, firm = maker_and_a_job()
    a.home_loan = 3_000_000
    rtr_makers.start_week(town)
    a.home_loan = 0                                                          # paid off, or the home sold
    rtr_makers.start_week(town)
    assert a.home_loan_top == 0
    a.home_loan = 1_000_000                                                  # another home, a smaller loan
    rtr_makers.start_week(town)
    assert a.home_loan_top == 1_000_000 and rtr_makers.owes_a_large_loan(a, home_counts=True)


# --- Jason, 18/11/2026, evening: the loan against a home is not the "large loan" ------------------------
# The fresh review counted that a home loan under half paid off sent makers into a job paying no more
# than the side hustle 71 and 64 times in two small towns, against 39 and 41 jobs turned down. Put to
# him: "A side hustle brings in $700 a week and they have a new home loan: do they take a $600 job?"
# His answer: "No, stay".
def test_the_dial_for_the_home_loan_is_off_and_is_one_of_the_rtr_worlds_own():
    from engine.config import RTR_ONLY, load_config
    assert load_config(None, ["world=rtr"]).home_loan_presses is False and "home_loan_presses" in RTR_ONLY


def test_with_a_new_home_loan_they_stay_when_the_job_pays_no_more_than_the_side_hustle():
    from engine import rtr_makers
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)           # his example: $700 a week against $600
    a.home_loan = 30_000_000                                                 # a home just bought, nothing paid off
    rtr_makers.start_week(town)
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, "side hustle")]


def test_with_a_home_loan_they_take_a_job_that_pays_more_as_anyone_with_a_side_hustle_does():
    from engine import rtr_makers
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=59_999, pays=60_000)
    a.home_loan = 30_000_000
    rtr_makers.start_week(town)
    labour_market(town)
    assert a.employer is firm and refusals(town) == []


def test_a_personal_loan_still_sends_someone_with_a_home_loan_to_the_first_job_offered():
    from engine import rtr_makers
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)
    a.home_loan, a.loan = 30_000_000, 100_000
    rtr_makers.start_week(town)
    labour_market(town)
    assert a.employer is firm


def test_with_that_dial_on_a_home_loan_less_than_half_paid_off_sends_them_to_the_first_job_as_it_did():
    from engine import rtr_makers
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(70_000, 60_000, "home_loan_presses=true")
    a.home_loan = 100_000
    rtr_makers.start_week(town)
    a.home_loan = 50_000                                                     # half paid off: not less than half
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, "side hustle")]
    a.home_loan = 50_001                                                     # a cent less than half paid off
    labour_market(town)
    assert a.employer is firm


@pytest.mark.parametrize("dial, taken", [((), False), (("home_loan_presses=true",), True)])
def test_a_small_business_weighs_a_home_loan_by_the_same_rule(dial, taken):
    from test_rtr_2 import customers, hours_for_the_week, make_business, maker, quiet_town, turned_away
    from engine import rtr_makers
    town = quiet_town(*dial)
    a, h = maker(town, cash=100_000)
    make_business(town, h)                                           # it pays the going wage, $1,000 a week
    owing, ho = maker(town, "food")
    owing.last_wage, ho.profit_week = 10_000, 100_000                # their side hustle brings in as much as the job pays
    owing.home_loan = 3_000_000                                      # and the only loan they have is on their home
    customers(town, h, 30)
    turned_away(town, h, 20)                                         # 100 hours wanted, 60 of the owner's: one worker
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert (h.staff == [owing]) is taken


# --- 19 November 2026: who is in the line for a job, and whose pay a cut touches ------------------------
# The WEF world's rule (his, 12 November: "cutting when there is a queue") lets a firm short of profit
# with no job going cut its wage when more than a twentieth of the town has no job. That count took in
# people living on a side hustle who would turn the job down. Put to him as a shop paying $800 that wants
# to pay $784, and sixty people with no job who all make more than that from side hustles. His words:
# "if people have a side hustle that pays more than a wage for a job, then why would they get into the
# queue? ... I would assume they wouldn't even apply for the job. Unless they're unhappy. and wanted to
# get out of this hard hustle. So If a side hustle person is Actually happy they will never apply for a
# job Until they become unhappy then they might want to do something different. That should reduce the
# number of people in the queue. If the queue is long, then the employer can ask for pay less wages to
# the newcomers. Old staff members still stay on the same pay rate."
def out_of_work(town, would_take=10_000):
    """Someone with no job and no side hustle who would take a job at `would_take` a week and no less."""
    from test_rtr_2 import jobless
    a = jobless(town)
    a.last_wage, a.security = would_take, 1.0
    return a


def a_maker(town, brings, would_take=10_000, happy=True):
    """Someone with no job whose side hustle brought in `brings` a week over the last quarter."""
    from test_rtr_2 import maker
    a, h = maker(town, "entertainment")
    a.last_wage, a.security, a.happy = would_take, 1.0, happy
    h.profit_week = brings
    return a


def shop_short_of_profit(town, pays=80_000):
    """A firm that lost money this quarter, with no job going, whose two shareholders are of the owner
    class. By the rule it cuts its wage by a fiftieth if the line for work is long."""
    from test_pricing import firm_with_holders, quarter
    firm = firm_with_holders(town)
    for a in town.agents:
        a.klass = "owner"
    firm.wage = pays
    quarter(firm, -200_000)
    return firm


def test_the_dials_for_the_line_are_on_and_are_the_rtr_worlds_own():
    from engine.config import RTR_ONLY, load_config
    cfg = load_config(None, ["world=rtr"])
    assert cfg.line_is_who_would_take is True and "line_is_who_would_take" in RTR_ONLY
    assert cfg.unhappy_makers_apply is True and "unhappy_makers_apply" in RTR_ONLY


def test_someone_out_of_work_is_in_the_line_for_a_job_that_pays_what_they_would_take():
    from test_rtr_2 import quiet_town
    from engine.labour import in_the_line
    town = quiet_town()
    out_of_work(town, would_take=78_400)
    assert in_the_line(town, 78_400) == 1 and in_the_line(town, 78_399) == 0


def test_someone_happy_on_a_side_hustle_that_brings_in_as_much_as_the_job_is_not_in_the_line():
    from test_rtr_2 import quiet_town
    from engine.labour import in_the_line
    town = quiet_town()
    a_maker(town, brings=78_400)
    assert in_the_line(town, 78_400) == 0
    assert in_the_line(town, 78_401) == 1                                    # a job that pays more, they would take


def test_someone_unhappy_on_a_side_hustle_is_in_the_line():
    from test_rtr_2 import quiet_town
    from engine.labour import in_the_line
    town = quiet_town()
    a_maker(town, brings=90_000, happy=False)                                # "wanted to get out of this hard hustle"
    assert in_the_line(town, 78_400) == 1
    assert in_the_line(town, 9_999) == 0                                     # under what they would take with nothing else


def test_someone_on_a_side_hustle_with_a_large_loan_is_in_the_line():
    from test_rtr_2 import quiet_town
    from engine.labour import in_the_line
    town = quiet_town()
    a_maker(town, brings=90_000).loan = 100_000
    assert in_the_line(town, 78_400) == 1


def test_the_owner_class_and_people_in_work_are_not_in_the_line():
    from test_rtr_2 import quiet_town, worker
    from engine.labour import in_the_line
    town = quiet_town()
    out_of_work(town).klass = "owner"                                        # living on dividends: they do not apply
    worker(town)
    assert in_the_line(town, 78_400) == 0


def cuts(town):
    return [(e["data"]["old"], e["amount"]) for e in town.rec.events
            if e["kind"] == "wage_change" and e["data"]["reason"] == "queue"]


def test_a_shop_does_not_cut_its_wage_for_people_who_live_on_side_hustles_and_would_say_no():
    from test_rtr_2 import quiet_town
    from engine.corporate import review_firm
    town = quiet_town()
    firm = shop_short_of_profit(town, pays=80_000)                           # his example: $800, and it wants to pay $784
    for _ in range(6):
        a_maker(town, brings=90_000)                                         # all six make more than that, and are happy
    assert town.jobless_share() == 1.0                                       # nobody in town has a job
    review_firm(town, firm)
    assert firm.wage == 80_000 and cuts(town) == []


def test_the_line_is_counted_at_the_lower_rate_and_not_at_what_the_firm_pays_today():
    from test_rtr_2 import quiet_town
    from engine.corporate import review_firm
    town = quiet_town()
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        out_of_work(town, would_take=79_000)                                 # they would come for $800, and not for $784
    review_firm(town, firm)
    assert cuts(town) == [] and firm.wage == 80_000


def test_it_cuts_when_more_than_a_twentieth_of_the_town_would_take_the_lower_wage():
    from test_rtr_2 import quiet_town, worker
    from engine.corporate import review_firm
    town = quiet_town()
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(36):
        worker(town)                                                         # with the two shareholders, 38
    one, other = out_of_work(town, would_take=78_400), out_of_work(town, would_take=78_401)
    review_firm(town, firm)
    assert cuts(town) == []                                                  # one of forty would take $784: not a line
    other.last_wage = 78_400
    review_firm(town, firm)
    assert cuts(town) == []                                                  # two of forty: a twentieth, and long is more than that
    one.happy = False                                                        # (being unhappy changes nothing with no side hustle)
    a_maker(town, brings=90_000, happy=False)                                # and one who wants out of a side hustle
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)] and firm.wage == 78_400          # three of forty-one would take it


@pytest.mark.parametrize("world", ["rtr", "wef"])
def test_a_firm_with_a_job_going_does_not_cut_its_rate_however_long_the_line(world):
    from conftest import empty_town
    from engine.corporate import review_firm
    town = empty_town(f"world={world}", "hustle_rate=0.0", "hustle_rate_struggling=0.0", "idea_rate=0.0")
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        a = town.add_agent()
        a.last_wage, a.security = 10_000, 1.0                                # six with no job who would take it
    firm.vacancies = 1                                                       # and it cannot fill the job it has
    review_firm(town, firm)
    assert cuts(town) == []
    firm.vacancies = 0
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)]


def test_with_that_dial_off_everyone_without_a_job_is_counted_as_before():
    from test_rtr_2 import quiet_town
    from engine.corporate import review_firm
    town = quiet_town("line_is_who_would_take=false")
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        a_maker(town, brings=90_000)
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)]


def test_in_the_wef_world_everyone_without_a_job_is_counted():
    from conftest import empty_town
    from engine.corporate import review_firm
    town = empty_town("line_is_who_would_take=true")                         # given, and not read: there is no RTR world here
    firm = shop_short_of_profit(town, pays=80_000)
    for _ in range(6):
        a = town.add_agent()
        a.last_wage, a.security = 200_000, 1.0                               # they would not work for under $2,000
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)]


def test_an_unhappy_maker_takes_a_job_that_pays_less_than_the_side_hustle():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)           # $700 a week against a job at $600
    a.happy = False
    labour_market(town)
    assert a.employer is firm and a.hustle is h and refusals(town) == []


def test_an_unhappy_maker_still_turns_down_a_job_under_what_they_would_take_with_nothing_else():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(brings=70_000, pays=60_000)
    a.happy, a.last_wage, a.security = False, 100_000, 1.0                   # they would not work for under $1,000
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, None)]


def test_with_that_dial_off_an_unhappy_maker_weighs_the_side_hustle_as_before():
    from engine.labour import labour_market
    town, a, h, firm = maker_and_a_job(70_000, 60_000, "unhappy_makers_apply=false")
    a.happy = False
    labour_market(town)
    assert a.employer is None and refusals(town) == [(60_000, "side hustle")]


@pytest.mark.parametrize("dial, taken", [((), True), (("unhappy_makers_apply=false",), False)])
def test_a_small_business_takes_on_an_unhappy_maker_by_the_same_rule(dial, taken):
    from test_rtr_2 import customers, hours_for_the_week, make_business, maker, quiet_town, turned_away
    from engine import rtr_makers
    town = quiet_town(*dial)
    a, h = maker(town, cash=100_000)
    make_business(town, h)                                           # it pays the going wage, $1,000 a week
    other, ho = maker(town, "food")
    other.last_wage, ho.profit_week = 10_000, 100_000                # their side hustle brings in as much as the job pays
    other.happy = False                                              # and they want out of it
    customers(town, h, 30)
    turned_away(town, h, 20)                                         # 100 hours wanted, 60 of the owner's: one worker
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert (h.staff == [other]) is taken


# --- 19 November 2026: "Old staff members still stay on the same pay rate" ------------------------------
# A firm had one rate for all its staff, and a cut was everyone's. His rule: with a long line "the
# employer can ask for pay less wages to the newcomers. Old staff members still stay on the same pay
# rate." He asked first whether staff can get a rise ("If not, then I don't think it's fair that
# employers can actually reduce wages"): they can, when a firm cannot fill a job and bids its wage up.
def shop_and_staff(town, pays=80_000, staff=3, need="food", cash=10_000_000):
    """A firm paying `pays` a week with that many on its staff, hired the ordinary way."""
    from engine.labour import hire
    firm = town.add_firm(need)
    firm.founded, firm.wage, firm.cash = -100, pays, cash
    people = [town.add_agent() for _ in range(staff)]
    for a in people:
        hire(town, firm, a)
    return firm, people


def taken_on(town, firm):
    from engine.labour import hire
    a = town.add_agent()
    hire(town, firm, a)
    return a


def test_the_dial_for_keeping_pay_is_on_and_is_one_of_the_rtr_worlds_own():
    from engine.config import RTR_ONLY, load_config
    assert load_config(None, ["world=rtr"]).staff_keep_pay is True and "staff_keep_pay" in RTR_ONLY


def test_a_cut_is_for_those_hired_after_it_and_staff_already_there_keep_their_pay():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)                            # his example: staff on $800
    set_wage(town, firm, 78_400, "queue")                                    # the firm drops its rate to $784
    assert firm.wage == 78_400 and [a.wage for a in old] == [80_000] * 3
    assert taken_on(town, firm).wage == 78_400                               # the next person hired starts on $784


def test_the_review_that_cuts_the_rate_leaves_the_staff_on_theirs():
    from test_rtr_2 import quiet_town
    from engine.corporate import review_firm
    from engine.labour import hire
    town = quiet_town()
    firm = shop_short_of_profit(town, pays=80_000)
    staff = [town.add_agent() for _ in range(3)]
    for a in staff:
        hire(town, firm, a)
    out_of_work(town)                                                        # one of six would take the job: a line
    review_firm(town, firm)
    assert cuts(town) == [(80_000, 78_400)] and [a.wage for a in staff] == [80_000] * 3


def test_on_pay_day_each_is_paid_their_own_rate():
    from test_rtr_2 import quiet_town
    from engine.corporate import _pay_wages
    from engine.firmops import set_wage
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    new = taken_on(town, firm)
    _pay_wages(town, firm)
    assert [a.cash for a in old] == [80_000] * 3 and new.cash == 78_400
    assert firm.w_wages == 3 * 80_000 + 78_400 == 10_000_000 - firm.cash
    assert new.income_week == 78_400 and old[0].income_week == 80_000


def test_a_rise_lifts_those_under_the_new_rate_and_cuts_nobody():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    new = taken_on(town, firm)
    set_wage(town, firm, 79_968, "unfilled")                                 # it cannot fill a job and bids up a fiftieth
    assert new.wage == 79_968 and [a.wage for a in old] == [80_000] * 3
    set_wage(town, firm, 81_567, "unfilled")
    assert [a.wage for a in old + [new]] == [81_567] * 4


def test_what_a_firm_owes_its_staff_and_its_bosses_follows_what_it_pays():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    town = quiet_town()
    cfg = town.cfg
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 60_000, "queue")
    taken_on(town, firm)                                                     # three on $800 and one on $600: $750 each
    assert firm.staff_bill() == 300_000 and firm.staff_pay() == 75_000
    assert firm.payroll(cfg) == 300_000                                      # no executives, nobody in charge
    assert firm.exec_pay(cfg) == int(75_000 * cfg.exec_pay_multiple)         # the bosses' pay is a multiple of the staff's
    assert firm.ceo_pay(cfg) == int(75_000 * (cfg.ceo_pay_base + 4 * cfg.ceo_pay_per_staff))
    assert town.staff_pay() == 75_000                                        # what staff in town are paid, for the record


def test_what_one_more_unit_would_cost_a_firm_is_reckoned_at_the_rate_it_offers():
    """The fresh review, 19 November: reckoned at what its staff keep, a cut for newcomers changed
    nothing a firm decided, and it never took the newcomers on."""
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 60_000, "queue")
    taken_on(town, firm)
    assert firm.make_cost() == int(60_000 * firm.spec.make_labour)           # the next unit is made by someone on the new rate
    assert town.typical_wage() == 60_000                                     # and the going rate is what a job pays someone new
    landlord, _ = shop_and_staff(town, pays=80_000, need="housing")
    set_wage(town, landlord, 60_000, "queue")
    assert landlord.unit_build_cost() == 30 * 60_000 + 500 * int(60_000 * 0.08)


def test_a_firm_that_cut_its_rate_sells_outside_again_though_its_staff_keep_theirs():
    """The reviewer's case. After a boom everyone on a food firm's staff is on $1,082.43, and at that
    a unit costs more to make than the outside pays ($168): it stops selling outside. It cuts its
    rate. The staff keep theirs; the people it would take on to make the goods would be on the new
    rate, and at that the goods pay."""
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.production import choose_make_mode, export_target
    town = quiet_town()
    cfg = town.cfg
    firm, old = shop_and_staff(town, pays=108_243, staff=4)
    assert export_target(cfg, firm, 1) == 0.0                                # $1,082.43 x 0.14, overhead and margin: over $168
    set_wage(town, firm, 106_078, "queue")                                   # one cut of a fiftieth: under the $1,069.52 that pays
    assert [a.wage for a in old] == [108_243] * 4 and firm.staff_pay() == 108_243
    assert firm.export_target == export_target(cfg, firm, 1) == firm.spec.export_quota > 0
    assert choose_make_mode(cfg, firm) == "make"


@pytest.mark.parametrize("dial, each", [((), 75_000), (("staff_keep_pay=false",), 60_000)])
def test_building_ahead_is_reckoned_at_the_rate_offered_and_building_done_is_booked_at_what_was_paid(dial, each):
    from test_rtr_2 import quiet_town
    from engine.entities import Project
    from engine.firmops import set_wage
    from engine.production import operate, project_cost
    from engine.rtr_owning import _firm_upkeep
    town = quiet_town(*dial)
    firm, old = shop_and_staff(town, pays=80_000, need="housing", cash=100_000_000)
    set_wage(town, firm, 60_000, "queue")
    taken_on(town, firm)                                                     # three on $800 and one on $600, where they keep it
    home = Project(firm.spec)                                                # thirty weeks of work and 500 units of goods
    # what is still to be built, and what keeping a home up will cost, are reckoned at the rate it offers
    assert project_cost(firm, home) == firm.unit_build_cost() == 30 * 60_000 + 500 * 4_800
    unit = town.new_unit(firm)                                               # a new home: 0.04 of a week's work and 0.4 of goods
    assert _firm_upkeep(town, firm, unit) == pytest.approx(0.04 * 60_000 + 0.4 * 4_800)
    firm.units.remove(unit)
    firm.projects.append(home)
    operate(town)                                                            # the four build for a week; the goods are brought in
    assert home.labour_left == 26.0 and firm.w_capex == 4 * each + 720_000   # what was built is booked at what was paid


def test_a_firm_with_nobody_on_its_staff_reckons_at_the_rate_it_offers():
    from test_rtr_2 import quiet_town
    town = quiet_town()
    firm, _ = shop_and_staff(town, pays=80_000, staff=0)
    assert firm.staff_pay() == 80_000 and firm.staff_bill() == 0 and firm.make_cost() == int(80_000 * firm.spec.make_labour)


def test_pay_held_back_for_shares_is_a_share_of_their_own_pay():
    from test_rtr_2 import quiet_town
    from engine.corporate import _pay_wages
    from engine.firmops import set_wage
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000, staff=1)
    set_wage(town, firm, 60_000, "queue")
    new = taken_on(town, firm)
    firm.share_pay = 0.05
    _pay_wages(town, firm)
    assert (old[0].cash, new.cash) == (76_000, 57_000)
    assert firm.accrual == {old[0].id: 4_000, new.id: 3_000}


def test_someone_who_leaves_and_comes_back_starts_on_the_rate_for_new_hires():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.labour import hire, separate
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    separate(town, old[0], "laid_off")
    hire(town, firm, old[0])
    assert old[0].wage == 78_400 and old[1].wage == 80_000


def test_an_executive_put_back_on_the_staff_is_paid_what_they_kept_as_staff():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.labour import demote, promote
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    promote(town, firm, old[0])                                              # they were on $800 as staff
    set_wage(town, firm, 60_000, "queue")
    taken_on(town, firm)
    demote(town, firm, old[0])
    assert old[0].wage == 80_000 and old[0].role == "staff"                  # their own rate, not the new hires'
    promote(town, firm, old[1])
    set_wage(town, firm, 90_000, "unfilled")                                 # the firm's rate passes what they were on
    demote(town, firm, old[1])
    assert old[1].wage == 90_000


def test_with_the_dial_off_an_executive_put_back_on_the_staff_gets_the_firms_rate():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.labour import demote, promote
    town = quiet_town("staff_keep_pay=false")
    firm, old = shop_and_staff(town, pays=80_000)
    promote(town, firm, old[0])
    set_wage(town, firm, 60_000, "queue")
    demote(town, firm, old[0])
    assert old[0].wage == 60_000


def test_someone_who_left_as_an_executive_brings_no_old_rate_back():
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.labour import demote, hire, promote, separate
    town = quiet_town()
    firm, old = shop_and_staff(town, pays=80_000)
    promote(town, firm, old[0])
    separate(town, old[0], "laid_off")
    set_wage(town, firm, 60_000, "queue")
    hire(town, firm, old[0])
    promote(town, firm, old[0])
    set_wage(town, firm, 50_000, "queue")
    demote(town, firm, old[0])
    assert old[0].wage == 60_000                                             # what they were hired back on, not the $800 of before


def test_with_that_dial_off_a_cut_is_everyones_as_before():
    from test_rtr_2 import quiet_town
    from engine.corporate import _pay_wages
    from engine.firmops import set_wage
    town = quiet_town("staff_keep_pay=false")
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    assert [a.wage for a in old] == [78_400] * 3 and firm.staff_pay() == 78_400
    old[0].wage = 99_999                                                     # whatever their own figure says,
    _pay_wages(town, firm)
    assert old[0].cash == 78_400 and firm.payroll(town.cfg) == 3 * 78_400    # the firm's one rate is what is paid
    assert town.typical_wage() == 78_400


def test_in_the_wef_world_a_cut_is_everyones():
    from conftest import empty_town
    from engine.firmops import set_wage
    town = empty_town("staff_keep_pay=true")                                 # given, and not read
    firm, old = shop_and_staff(town, pays=80_000)
    set_wage(town, firm, 78_400, "queue")
    assert [a.wage for a in old] == [78_400] * 3
    old[0].wage = 99_999
    assert firm.staff_pay() == 78_400 and firm.payroll(town.cfg) == 3 * 78_400 and town.typical_wage() == 78_400


def business_with_a_worker(*dial):
    """A small business with work for one person beyond its owner, and that person on its staff at the
    going wage, $1,000 a week."""
    from test_rtr_2 import customers, hours_for_the_week, jobless, make_business, maker, on_the_staff, quiet_town, turned_away
    town = quiet_town(*dial)
    a, h = maker(town, cash=200_000)
    make_business(town, h)
    hand = jobless(town)
    on_the_staff(h, hand)
    customers(town, h, 30)
    turned_away(town, h, 20)                                         # 100 hours wanted, 60 of the owner's: one worker
    hours_for_the_week(town)
    return town, h, hand


def the_going_wage_becomes(town, wage):
    """The one firm in town with staff pays this."""
    from test_rtr_2 import worker
    boss = next((f for f in town.firms if f.need == "housing"), None) or worker(town).employer
    boss.wage = wage
    for a in boss.staff:
        a.wage = wage


@pytest.mark.parametrize("dial, kept", [((), True), (("staff_keep_pay=false",), False)])
def test_a_small_business_keeps_its_staff_on_their_pay_when_the_going_wage_falls(dial, kept):
    from engine import rtr_makers
    town, h, hand = business_with_a_worker(*dial)
    the_going_wage_becomes(town, 80_000)
    rtr_makers.hire_staff(town)
    assert h.wage == 80_000 and h.staff == [hand]                    # what it would pay someone new
    assert hand.wage == (100_000 if kept else 80_000)
    if not kept:
        hand.wage = 99_999                                           # whatever their own figure says, the going wage is paid
    rtr_makers.pay_staff(town)
    assert hand.cash == hand.income_week == h.w_wages == (100_000 if kept else 80_000)


def test_a_small_business_lifts_its_staff_when_the_going_wage_rises():
    from engine import rtr_makers
    town, h, hand = business_with_a_worker()
    hand.wage = 70_000                                               # taken on when the going wage was $700
    the_going_wage_becomes(town, 80_000)
    rtr_makers.hire_staff(town)
    assert hand.wage == 80_000 == h.wage and h.staff == [hand]
    the_going_wage_becomes(town, 75_000)
    rtr_makers.hire_staff(town)
    assert hand.wage == 80_000 and h.wage == 75_000                  # and it does not come back down


def test_a_small_business_that_cannot_pay_what_its_staff_keep_lets_the_last_hired_go():
    from engine import rtr_makers
    town, h, hand = business_with_a_worker()
    the_going_wage_becomes(town, 80_000)
    rtr_makers.hire_staff(town)
    h.owner.cash = 90_000                                            # enough for the going wage, not for what they keep
    rtr_makers.pay_staff(town)
    assert h.staff == [] and hand.role is None and hand.cash == 0


@pytest.mark.parametrize("dial, kept", [((), True), (("staff_keep_pay=false",), False)])
def test_staff_keep_their_pay_when_the_business_they_work_for_becomes_a_company(dial, kept):
    from test_rtr_2 import customers, jobless, maker, on_the_staff, quiet_town
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0", "population_cap=1000", *dial)
    a, h = maker(town, cash=22_000_000, risk=1.0)
    customers(town, h, 3)
    hand, newer = jobless(town), jobless(town)
    h.business, h.wage = True, 100_000
    on_the_staff(h, hand, newer)
    hand.wage, newer.wage = 120_000, 90_000                          # one keeps a rate from before the going wage fell
    town.week, h.q_sold, h.q_could = 13, 390, 390
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert firm.staff == [hand, newer] and firm.wage == 100_000      # the new company offers the going wage
    assert hand.wage == (120_000 if kept else 100_000) and newer.wage == 100_000
    hired = [(e["agent"], e["amount"]) for e in town.rec.events if e["kind"] == "hire" and e["firm"] == firm.id]
    assert hired == [(hand.id, hand.wage), (newer.id, 100_000)]      # and the record says what each is on


def test_the_record_keeps_what_staff_are_paid_and_what_a_job_pays_someone_new():
    """Since 19 November "the wage" of a town is two numbers. The record's `wage` (shown as the staff
    wage) is what staff are paid; `wage_offer` is the going wage, what a job pays someone taken on
    now. The WEF world has one number, and no second measure."""
    from conftest import empty_town
    from test_rtr_2 import quiet_town
    from engine.firmops import set_wage
    from engine.metrics import weekly_series
    for town, paid, has_offer in ((quiet_town(), 75_000, True), (empty_town(), 60_000, False)):
        firm, old = shop_and_staff(town, pays=80_000)
        set_wage(town, firm, 60_000, "queue")
        taken_on(town, firm)
        m = {metric: value for scope, metric, value in weekly_series(town) if scope == "town"}
        assert m["wage"] == paid and m["wage_index"] == paid / 100_000
        assert (m.get("wage_offer") == 60_000) is has_offer and ("wage_offer" in m) is has_offer
