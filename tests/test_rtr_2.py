"""The Right to Repair world, stage 2: makers, ideas, and side hustles that grow."""

import pytest
from conftest import BEFORE_THE_LINE, BEFORE_THE_RULINGS, FIFTH_IN_CASH
from test_rtr import map_rtr_town, rtr_town  # noqa: F401

from engine.config import load_config

NOBODY_STARTS = ("hustle_rate=0.0", "hustle_rate_struggling=0.0", "idea_rate=0.0")


def quiet_town(*overrides):
    """An RTR town where nothing starts by chance: a test sees only what it set up."""
    return rtr_town(*NOBODY_STARTS, *overrides)


def jobless(town, cash=0, **fixed):
    a = town.add_agent(cash=cash, **fixed)
    a.last_wage = town.cfg.outside_wage              # they last earned $1,000 a week
    return a


def worker(town, cash=0, wage=100_000, **fixed):
    """Someone on the staff of a landlord with no homes: a job, and nothing for sale."""
    a = town.add_agent(cash=cash, **fixed)
    boss = next((f for f in town.firms if f.need == "housing"), None) or town.add_firm("housing")
    a.employer, a.role, a.wage = boss, "staff", wage
    boss.staff.append(a)
    return a


def pays(firm, wage):
    """The firm's rate, and what everyone on its staff is paid: the going wage, if it is the only firm."""
    firm.wage = wage
    for a in firm.staff:
        a.wage = wage


def shop(town, need, price):
    """A firm selling the need, with staff who will start nothing themselves."""
    from test_subscriptions import staffed
    firm = staffed(town, need, 5, price=price)
    for w in firm.staff:
        w.risk = 0.0
    return firm


def maker(town, trade="entertainment", agent=None, **fixed):
    from engine.rtr_makers import open_hustle
    a = agent if agent is not None else jobless(town, **fixed)
    return a, open_hustle(town, a, trade)


# --- Part A, task 1: dials, the side hustle, what an hour is worth, and prices ----------------------
def test_the_maker_dials_have_the_designs_values():
    cfg = load_config()
    assert (cfg.hustle_min_hours, cfg.hustle_rate, cfg.hustle_rate_struggling) == (10.0, 0.01, 0.10)
    assert (cfg.maker_hour_floor, cfg.hustle_quit_share, cfg.hustle_full_share) == (0.5, 0.2, 0.95)
    assert (cfg.hustle_loan_weeks, cfg.hustle_loan_term_weeks) == (26.0, 260)
    assert (cfg.idea_rate, cfg.idea_hours) == (0.00002, 20.0)
    assert (cfg.tools_entertainment, cfg.tools_invented, cfg.tools_food) == (0, 50_000, 200_000)
    assert (cfg.tools_repair, cfg.tools_set_building, cfg.tools_home_building) == (100_000, 500_000, 1_000_000)
    with pytest.raises(ValueError):
        load_config(None, ["hustle_rate=1.5"])


@pytest.mark.parametrize("bad", ["hustle_rate_struggling=-0.1", "maker_hour_floor=2.0", "hustle_quit_share=1.1",
                                 "hustle_full_share=-1.0", "idea_rate=2.0", "hustle_min_hours=0.0", "idea_hours=0.0",
                                 "hustle_loan_weeks=-1.0", "tools_food=-1", "hustle_loan_term_weeks=0"])
def test_settings_for_makers_that_make_no_sense_are_refused(bad):
    with pytest.raises(ValueError):
        load_config(None, [bad])


def test_what_a_makers_hour_is_worth():
    from engine.rtr_makers import hour_worth
    town = quiet_town()
    assert hour_worth(town, worker(town)) == 2_500.0                 # their wage over the forty hours
    out = jobless(town)
    assert hour_worth(town, out) == 1_750.0                          # they would take 0.7 of $1,000 at first
    out.weeks_out = 10
    assert hour_worth(town, out) == 1_250.0                          # half that by now: the floor, half the going hour
    assert hour_worth(town, worker(town, wage=40_000)) == 1_250.0    # the floor holds for the low paid too


def test_a_maker_charges_cost_plus_a_tenth():
    from engine.rtr_makers import hour_price, hours_per_customer, need_price
    town = quiet_town()
    food, fun = town.needs["food"], town.needs["entertainment"]
    w, out = worker(town), jobless(town)
    assert (need_price(town, w, food), need_price(town, w, fun)) == (40_590, 8_470)
    assert (need_price(town, out, food), need_price(town, out, fun)) == (34_650, 6_820)
    out.weeks_out = 10                                               # the struggling undercut most
    assert (need_price(town, out, food), need_price(town, out, fun)) == (30_690, 5_720)
    assert (hour_price(town, w), hour_price(town, out)) == (2_750, 1_375)
    assert hours_per_customer(town.cfg, fun) == 2.0 and hours_per_customer(town.cfg, food) == pytest.approx(7.2)


def test_a_side_hustle_is_its_owners_and_is_no_firm():
    from engine.rtr_makers import tools_cost, trades
    town = quiet_town()
    a, h = maker(town, "entertainment", cash=500)
    assert a.hustle is h and town.hustles == [h] and h not in town.firms and h.id == -(1_000_000 + a.id)
    assert h.spec is town.needs["entertainment"] and h.need == "entertainment" and h.price == 6_820
    assert h.owner is a and h.alive and h.started == 0 and h.load() == 0
    assert h.cash == 0 and a.cash == 500                             # it has a till of its own, empty until customers pay
    b, r = maker(town, "repair")
    assert r.spec is None and r.price == 1_925                       # an hour of theirs, plus a tenth
    assert [t for t, _ in trades(town)] == ["food", "entertainment", "repair", "set_building", "home_building"]
    assert [tools_cost(town.cfg, t, s) for t, s in trades(town)] == [200_000, 0, 100_000, 500_000, 1_000_000]


def test_an_invented_need_is_a_trade_and_the_ride_is_not():
    from engine.corporate import invent_need, transport_spec
    from engine.rtr_makers import tools_cost, trades
    town = quiet_town()
    new = invent_need(town)
    town.needs["transport"] = transport_spec(town)
    names = [t for t, _ in trades(town)]
    assert names == ["food", "entertainment", new.name, "repair", "set_building", "home_building"]
    assert tools_cost(town.cfg, new.name, new) == 50_000
    town.new_ideas.add(new.name)                                     # thought of this week: not yet open to others
    assert new.name not in [t for t, _ in trades(town)]


def test_a_wef_town_has_no_side_hustles_and_nobody_in_it_has_one():
    from conftest import empty_town
    town = empty_town()
    assert town.hustles == [] and town.add_agent().hustle is None


# --- task 2: a maker as a seller ---------------------------------------------------------------------
def customers(town, hustle, n, cash=100_000):
    from engine.subscriptions import subscribe
    out = [town.add_agent(cash=cash) for _ in range(n)]
    for c in out:
        assert subscribe(town, c, hustle)
    return out


def hours_for_the_week(town):
    from engine import rtr_makers, rtr_owning
    rtr_owning.start_week(town)
    rtr_makers.start_week(town)


def a_week(town):
    """The parts of the week a side hustle lives through, in the week's order."""
    from engine import rtr_makers, rtr_owning
    from engine.household import pay_bills
    hours_for_the_week(town)
    rtr_makers.working_week(town)
    pay_bills(town)
    rtr_owning.after_bills(town)
    rtr_makers.after_bills(town)


def test_customers_find_a_maker_who_is_cheaper_and_a_maker_is_never_their_own_customer():
    from engine.subscriptions import find_provider
    town = quiet_town()
    firm = shop(town, "entertainment", 9_500)
    a, h = maker(town)                                               # sells it at 6,820
    hours_for_the_week(town)
    assert h.hours == 60.0 and h.capacity == 30
    assert find_provider(town, town.add_agent(), "entertainment") is h
    assert find_provider(town, a, "entertainment") is firm


def test_a_maker_who_charges_more_than_the_shop_gets_nobody():
    from engine.subscriptions import find_provider
    town = quiet_town()
    firm = shop(town, "entertainment", 6_000)
    a, h = maker(town)
    hours_for_the_week(town)
    assert find_provider(town, town.add_agent(), "entertainment") is firm


def test_a_week_of_a_side_hustle_hours_then_takings_then_goods():
    town = quiet_town()
    a, h = maker(town)                                               # no money at all
    customers(town, h, 3)
    a_week(town)
    assert h.w_revenue == 20_460 and h.w_goods == 8_100 and a.cash == 12_360
    assert a.spare_hours == 54.0 and (h.q_sold, h.q_could) == (3, 30)
    assert (h.q_revenue, h.q_goods) == (20_460, 8_100)
    assert town.ledger.week_out["import"] == 8_100 and town.ledger.week_internal["subscription"] == 20_460
    a_week(town)                                                     # the week's figures start again; the quarter's add up
    assert (h.w_revenue, h.w_goods, h.q_revenue, h.q_goods) == (20_460, 8_100, 40_920, 16_200)
    assert (h.q_sold, h.q_could) == (6, 60) and a.cash == 24_720


def test_a_full_maker_takes_no_more():
    from engine.subscriptions import find_provider, has_room
    town = quiet_town()
    a, h = maker(town)
    customers(town, h, 29)
    hours_for_the_week(town)
    assert has_room(town, h) and find_provider(town, town.add_agent(), "entertainment") is h
    customers(town, h, 1)
    late, broke = worker(town, cash=1_000_000), worker(town, cash=6_819)
    assert not has_room(town, h) and find_provider(town, late, "entertainment") is None
    assert find_provider(town, broke, "entertainment") is None
    assert h.turned_away == {late.id: True, broke.id: True}
    hours_for_the_week(town)
    assert h.waiting == 1 and h.turned_away == {}                    # only the one who had the money for a week of it


def test_a_maker_who_takes_a_job_leaves_the_newest_unserved_and_unbilled():
    from engine.subscriptions import has_room
    town = quiet_town()
    a, h = maker(town)
    people = customers(town, h, 12, cash=6_820)
    hours_for_the_week(town)
    assert has_room(town, h)
    a.employer, a.role, a.wage = town.add_firm("housing"), "staff", 100_000
    a.employer.staff.append(a)
    a_week(town)                                                     # 20 spare hours: ten customers
    assert h.capacity == 10 and not has_room(town, h)
    assert sorted(h.unserved) == sorted(c.id for c in people[10:])
    assert [c.cash for c in people[10:]] == [6_820, 6_820]           # not served, not billed
    assert h.w_revenue == 68_200 and h.w_goods == 27_000             # and no goods bought for them
    assert a.spare_hours == 0.0 and (h.q_sold, h.q_could) == (10, 10)


def test_a_bigger_plan_takes_the_hours_and_goods_of_that_many():
    from engine.subscriptions import set_plan
    town = quiet_town()
    a, h = maker(town)
    (c,) = customers(town, h, 1)
    set_plan(town, c, h, 2)
    a_week(town)
    assert h.load() == 2 and h.w_revenue == 13_640 and h.w_goods == 5_400 and a.spare_hours == 56.0


def test_a_customer_who_cannot_pay_gets_nothing_and_no_goods_are_bought_for_them():
    town = quiet_town()
    a, h = maker(town, cash=10_000)
    customers(town, h, 1, cash=0)
    customers(town, h, 1, cash=6_820)                                # one of the two can pay
    a_week(town)
    assert h.w_revenue == 6_820 and h.w_goods == 2_700 and a.cash == 10_000 + 6_820 - 2_700


def test_the_yardstick_is_the_cheapest_price_someone_could_buy_at():
    from engine.corporate import invent_need
    from engine.subscriptions import cheapest_prices, find_provider
    town = quiet_town()
    firm = shop(town, "entertainment", 9_500)
    a, h = maker(town)
    hours_for_the_week(town)
    assert cheapest_prices(town)["entertainment"] == 6_820           # a maker with room is on offer to anyone
    customers(town, h, 30)
    assert cheapest_prices(town)["entertainment"] == 9_500           # a full one is not: the shop's price stands
    firm.alive = False                                               # the last firm selling it has gone
    assert cheapest_prices(town)["entertainment"] == 6_820           # then the cheapest maker's, room or not
    b, hb = maker(town)
    hb.price, hb.capacity = 6_000, 0                                 # both full: still the cheaper of the two
    assert cheapest_prices(town)["entertainment"] == 6_000
    hb.capacity = 30
    firm.alive = True
    hb.price = 9_600                                                 # a maker with room who is dearer than the shop
    assert cheapest_prices(town)["entertainment"] == 9_500
    new = invent_need(town)
    assert new.name not in cheapest_prices(town)
    c, hc = maker(town, new.name)
    hours_for_the_week(town)
    assert cheapest_prices(town)[new.name] == hc.price               # an invented need only a maker sells is on offer
    assert find_provider(town, town.add_agent(), new.name) is hc
    r, hr = maker(town, "repair")                                    # a trade that sells hours is no need at all
    assert "repair" not in cheapest_prices(town)


def test_people_take_up_an_invented_need_that_only_a_maker_sells_and_it_counts_toward_what_they_have():
    from engine.corporate import invent_need
    from engine.household import pay_bills, review_subscriptions, update_agents
    town = quiet_town()
    new = invent_need(town)
    a, h = maker(town, new.name)
    c = town.add_agent(cash=10_000_000, taste=(1.0 - new.salt) % 1.0)     # it suits them
    hours_for_the_week(town)
    review_subscriptions(town)
    assert c.subs.get(new.name) is h
    from engine import rtr_makers
    rtr_makers.working_week(town)
    pay_bills(town)
    update_agents(town)
    assert c.met[new.name] and c.cash == 10_000_000 - h.price


def test_a_maker_who_moves_takes_it_with_them_and_one_who_loses_their_home_keeps_it():
    from engine.household import check_reach, update_agents
    from engine.subscriptions import move_home, subscribe, unsubscribe
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    near, far = block(town, landlord, 5, 6, homes=2), block(town, landlord, 1, 1, homes=2)
    a = tenant(town, near, cash=0)
    a.last_wage = town.cfg.outside_wage
    _, h = maker(town, agent=a)
    c = tenant(town, near)
    hours_for_the_week(town)
    assert h.spot is near and subscribe(town, c, h)
    move_home(town, a, next(u for u in landlord.units if u.spot is far and u.occupant is None), "test")
    hours_for_the_week(town)
    check_reach(town, c)
    assert h.spot is far and "entertainment" not in c.subs           # nine blocks is past a walk
    d = tenant(town, far)
    assert subscribe(town, d, h)
    unsubscribe(town, a, "housing", "evicted")
    update_agents(town)
    hours_for_the_week(town)                     # Jason: anyone creates, even while struggling
    assert a.hustle is h and h.alive and h.spot is far and d.subs["entertainment"] is h
    assert stopped(town) == [] and h.capacity == 30


def test_a_maker_keeps_up_what_they_own_before_the_side_hustle():
    from engine import rtr_owning
    town = quiet_town()
    a, h = maker(town)
    unit = town.new_own_unit(town.needs["housing"], a)
    a.unit["housing"], unit.occupant = unit, a                       # their home needs 1.6 hours a week
    hours_for_the_week(town)
    assert h.hours == pytest.approx(58.4) and h.capacity == 29
    customers(town, h, 29)
    a_week(town)
    assert a.spare_hours == pytest.approx(0.4)                       # 58 for customers, 1.6 for the home


def test_the_week_of_a_whole_town_runs_a_side_hustle_in_its_place():
    from conftest import small_town
    from engine.rtr_makers import open_hustle
    from test_town_invariants import run_checked
    town = small_town("world=rtr", *NOBODY_STARTS, "stop_on_failure=false")
    for _ in range(26):
        town.step()
    someone = next(a for a in town.agents if a.role == "staff" and "housing" in a.unit)
    h = open_hustle(town, someone, "entertainment")
    assert run_checked(town, 52) == []
    signed = [e for e in town.rec.events if e["kind"] == "sub_start" and e["firm"] == h.id]
    assert signed or not h.alive                                     # it found customers, or was given up


# --- task 3: starting a side hustle --------------------------------------------------------------------
def started(town):
    return [(e["agent"], e["amount"], e["data"]["trade"], e["data"]["price"]) for e in town.rec.events
            if e["kind"] == "hustle_started"]


def test_someone_struggling_starts_the_side_hustle_that_undercuts_most():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    a = jobless(town, cash=1_000_000)
    assert best_trade(town, a) == ("entertainment", 6_820)           # 28% under, against 13% for food
    consider_hustles(town)
    assert a.hustle.trade == "entertainment" and a.cash == 1_000_000     # the computer they already have
    assert started(town) == [(a.id, 0, "entertainment", 6_820)]
    assert a.hustle.capacity == 30                                   # people can sign up from this week
    consider_hustles(town)
    assert len(town.hustles) == 1                                    # one side hustle each


def test_a_trade_they_cannot_tool_up_for_is_not_theirs():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 6_900)                               # barely undercut: 1%
    shop(town, "food", 40_000)
    rich, poor = jobless(town, cash=1_000_000), jobless(town, cash=0)
    assert best_trade(town, rich) == ("food", 34_650) and best_trade(town, poor) == ("entertainment", 6_820)
    consider_hustles(town)
    assert rich.hustle.trade == "food" and rich.cash == 800_000 and town.ledger.week_out["import"] == 200_000
    assert poor.hustle.trade == "entertainment" and poor.cash == 0
    assert started(town) == [(rich.id, 200_000, "food", 34_650), (poor.id, 0, "entertainment", 6_820)]


def test_someone_in_work_borrows_for_the_tools():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=1.0")
    shop(town, "entertainment", 6_300)
    shop(town, "food", 40_000)
    low = worker(town, wage=60_000, risk=1.0)                        # an hour of theirs is $15
    assert best_trade(town, low) == ("food", 32_670)
    consider_hustles(town)
    assert low.hustle.trade == "food" and low.loan == 200_000 and low.cash == 0


def test_tools_come_from_cash_then_a_personal_loan_then_a_loan_against_their_home():
    from engine.rtr_makers import pay_tools
    town = quiet_town()
    owner, renter = worker(town, cash=300_000), worker(town, cash=300_000)
    unit = town.new_own_unit(town.needs["housing"], owner)
    owner.unit["housing"], unit.occupant = unit, owner
    assert pay_tools(town, owner, 1_200_000)                         # $3,000 of theirs, $8,000 on their wage, $1,000 on the home
    assert (owner.cash, owner.loan, owner.home_loan, owner.spend_week) == (0, 800_000, 100_000, 1_200_000)
    assert not pay_tools(town, renter, 1_200_000)                    # no home to borrow on: nothing is borrowed at all
    assert (renter.cash, renter.loan, renter.home_loan) == (300_000, 0, 0)
    assert pay_tools(town, renter, 0) and renter.cash == 300_000     # tools that cost nothing
    assert town.ledger.week_out["import"] == 1_200_000


def test_who_may_start_one():
    from engine.rtr_makers import consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=1.0")
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    busy = jobless(town)
    busy.travel_hours = 51.0                                         # nine spare hours: not enough
    keen, shy = worker(town, cash=5_000_000, risk=1.0), worker(town, cash=5_000_000, risk=0.0)
    consider_hustles(town)
    assert busy.hustle is None and shy.hustle is None                # in work and well enough off: by appetite for risk
    assert keen.hustle.trade == "entertainment" and keen.hustle.price == 8_470


class Dice:
    """Rolls what it is told to."""

    def __init__(self, roll):
        self.roll = roll

    def random(self):
        return self.roll

    def uniform(self, low, high):
        return (low + high) / 2


def a_town_with_room_for_one_more(*who):
    town = rtr_town()
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    return town


def test_the_chance_is_a_tenth_a_week_for_someone_out_of_work_or_whose_income_does_not_cover_their_basket():
    from engine.rtr_makers import consider_hustles
    for make in (lambda town: jobless(town), lambda town: worker(town, wage=50_000, risk=0.0)):
        town = a_town_with_room_for_one_more()
        a = make(town)
        town.rng = Dice(0.1)
        consider_hustles(town)
        assert a.hustle is None
        town.rng = Dice(0.0999)
        consider_hustles(town)
        assert a.hustle is not None


def test_the_chance_is_a_hundredth_a_week_times_their_appetite_for_risk_for_everyone_else():
    from engine.rtr_makers import consider_hustles
    town = a_town_with_room_for_one_more()
    a = worker(town, cash=5_000_000, risk=0.5)
    town.rng = Dice(0.005)
    consider_hustles(town)
    assert a.hustle is None
    town.rng = Dice(0.00499)
    consider_hustles(town)
    assert a.hustle is not None


def test_nobody_starts_what_would_undercut_nobody():
    from engine.rtr_makers import best_trade
    town = quiet_town()
    shop(town, "entertainment", 5_000)
    shop(town, "food", 20_000)
    assert best_trade(town, jobless(town, cash=1_000_000)) is None


def owners(town, n):
    """n people in work who own a home: 1.6 hours of upkeep a week each."""
    out = [worker(town) for _ in range(n)]
    for o in out:
        own_home(town, o)
    return out


def test_a_trade_that_sells_hours_is_taken_up_only_with_work_in_sight_to_keep_them_past_a_quarter():
    from engine.rtr_makers import best_trade, stop
    town = quiet_town()
    shop(town, "entertainment", 5_000)
    shop(town, "food", 20_000)
    a = jobless(town, cash=2_000_000)                                # sixty hours a week: a fifth is twelve
    assert best_trade(town, a) is None                               # nobody owns anything to repair
    people = owners(town, 7)                                         # 11.2 hours of upkeep a week: not twelve
    assert best_trade(town, a) is None
    own_too = jobless(town, cash=2_000_000)
    own_home(town, own_too)                                          # with their own home that is 12.8, but their own is no custom
    assert best_trade(town, own_too) is None
    people += owners(town, 1)                                        # 12.8 without it
    assert best_trade(town, a) == ("repair", 1_925)                  # 14% under the 2,230 an owner's own hour comes to
    assert best_trade(town, people[0]) is None                       # in work at the going wage: no undercut
    rival, hr = maker(town, "repair")
    hr.price = 2_100                                                 # dearer than they would be
    hours_for_the_week(town)                                         # but the rival offers sixty hours: the work is spoken for
    assert best_trade(town, a) is None
    stop(town, hr, "test")
    people[0].set_hours_left = 20.0                                  # one set being built: an hour and a half a week
    assert best_trade(town, a) == ("repair", 1_925)
    for o in people:
        o.set_hours_left = 20.0                                      # eight at once: 12.3 hours a week
    assert best_trade(town, a) == ("set_building", 1_925)            # 23% under: nothing to pay on parts
    a.cash = 499_999                                                 # $5,000 of tools is out of reach
    assert best_trade(town, a) == ("repair", 1_925)
    a.cash = 99_999
    assert best_trade(town, a) is None
    a.cash = 2_000_000
    for trade in ("repair", "set_building"):                         # someone cheaper in both
        _, rival = maker(town, trade)
        rival.price = 1_900
    people[0].build = type("B", (), {"hours_left": 150.0})()         # the end of one home: 11.5 hours a week
    assert best_trade(town, a) is None
    people[0].build.hours_left = 1_200.0                             # a home just begun: 92 hours a week
    assert best_trade(town, a) == ("home_building", 1_925)           # 6% under the 2,050 it comes to with materials
    a.weeks_out = 0
    a.security = 0.75                                                # an hour of theirs at 1,875: 2,063 with the tenth
    assert best_trade(town, a) is None


def test_a_seller_out_of_reach_is_no_seller_at_all():
    from engine.rtr_makers import best_trade
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS)
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 5, 6, homes=2)
    premises(town, "food", 6, 6, price=20_000)
    premises(town, "entertainment", 12, 12, price=5_000)             # thirteen blocks away: past a walk
    a = tenant(town, home, cash=0)
    a.last_wage = town.cfg.outside_wage
    assert best_trade(town, a) == ("entertainment", 6_820)           # nobody near sells it: the best opening there is
    premises(town, "entertainment", 4, 6, price=5_000)
    assert best_trade(town, a) is None


def test_on_a_map_someone_with_no_home_can_start_a_side_hustle_too():
    from engine.rtr_makers import consider_hustles
    from engine.subscriptions import find_provider
    from test_places import block, premises, tenant
    town = map_rtr_town("hustle_rate_struggling=1.0")
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 5, 6, homes=2)
    homeless = jobless(town)
    housed = tenant(town, home, cash=0)
    consider_hustles(town)
    assert homeless.hustle is not None and homeless.hustle.spot is None      # they sell where they are found
    assert housed.hustle is not None and housed.hustle.spot is home          # and someone with a home, from home
    other = jobless(town)
    housed.hustle.capacity = 0                                               # the housed one is full
    assert find_provider(town, other, "entertainment") is homeless.hustle    # anyone can get to the one with no home


# --- task 4: the quarter, a maker's income, class and position ---------------------------------------
def stopped(town):
    return [(e["data"]["reason"], e["agent"]) for e in town.rec.events if e["kind"] == "hustle_stopped"]


def test_a_maker_with_under_a_fifth_of_their_customers_for_a_whole_quarter_gives_it_up():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town), maker(town)
    people = customers(town, h, 2)
    town.week = 13
    (h.q_sold, h.q_could), (hb.q_sold, hb.q_could) = (77, 390), (78, 390)
    hc.started, hc.q_could = 1, 390                                  # not yet a whole quarter: not judged
    hb.q_revenue, hb.q_goods, hb.q_wages = 500, 200, 100
    quarter(town)
    assert a.hustle is None and town.hustles == [hb, hc] and hb.q_wages == 0
    assert all("entertainment" not in p.subs for p in people)
    assert stopped(town) == [("few customers", a.id)]
    assert (hb.q_sold, hb.q_could, hb.q_revenue, hb.q_goods) == (0, 0, 0, 0)     # a new quarter
    (hb.q_sold, hb.q_could), hc.q_could = (78, 390), 390
    town.week = 14                                                   # thirteen weeks old now
    quarter(town)
    assert stopped(town) == [("few customers", a.id), ("few customers", c.id)]


def test_a_maker_with_no_hours_for_customers_for_a_whole_quarter_gives_it_up():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb) = maker(town), maker(town)
    town.week, hb.started = 13, 1
    quarter(town)
    assert stopped(town) == [("no hours", a.id)] and town.hustles == [hb]


def test_the_price_is_set_again_each_quarter_and_can_fall():
    from engine.rtr_makers import quarter
    town = quiet_town()
    a, h = maker(town)
    (c,) = customers(town, h, 1)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    a.weeks_out, before = 10, c.security
    quarter(town)
    assert h.price == 5_720 and c.security == before                 # a fall is no blow
    assert [(e["amount"], e["data"]["old"], e["firm"]) for e in town.rec.events if e["kind"] == "price_change"] == [
        (5_720, 6_820, h.id)]
    a.weeks_out, h.q_sold, h.q_could = 0, 300, 390                   # and it can rise again, which is one
    quarter(town)
    assert h.price == 6_820 and c.security < before


def test_a_repairers_hour_is_priced_again_each_quarter_too():
    from engine.rtr_makers import quarter
    town = quiet_town()
    a, h = maker(town, "repair")
    town.week, h.q_sold, h.q_could = 13, 300, 390
    a.weeks_out = 10
    quarter(town)
    assert h.price == 1_375


def test_what_a_side_hustle_brings_in_is_income_and_half_a_basket_of_it_is_a_living():
    from engine.household import basket_cost, classify, update_agents
    from engine.rtr_makers import makes_a_living, quarter
    town = quiet_town()
    shop(town, "entertainment", 9_500)                               # so the basket is the plain $880
    a, h = maker(town)
    h.capacity = 0                                                   # (no room: their own price is not on offer)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    h.q_revenue, h.q_goods = 1_000_000, 428_000
    quarter(town)
    assert h.profit_week == 44_000 and a.income_estimate() == 44_000
    assert basket_cost(town, a) == 88_000 and makes_a_living(a, 88_000)
    assert classify(town, a) == "working"
    h.profit_week = 43_999
    assert not makes_a_living(a, 88_000) and classify(town, a) == "out"
    h.profit_week = 44_000
    a.security = 0.0
    update_agents(town)
    assert a.klass == "working" and not a.destitute and a.security > 0.0   # a position, as a job is
    h.profit_week = 43_999
    a.security = 0.0
    update_agents(town)
    assert a.klass == "out" and a.destitute and a.security == 0.0


def test_a_quarter_that_lost_money_counts_as_nothing_brought_in_and_wages_come_off():
    from engine.rtr_makers import quarter
    town = quiet_town()
    a, h = maker(town)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    h.q_revenue, h.q_goods, h.q_wages = 1_000_000, 428_000, 312_000
    quarter(town)
    assert h.profit_week == 20_000
    h.q_sold, h.q_could, h.q_revenue, h.q_goods = 300, 390, 100, 200
    quarter(town)
    assert h.profit_week == 0 and a.income_estimate() == 0


def test_someone_with_a_job_and_a_side_hustle_has_both_incomes_and_stays_working():
    from engine.household import classify
    town = quiet_town()
    a = worker(town)
    _, h = maker(town, agent=a)
    h.profit_week = 30_000
    assert a.income_estimate() == 130_000 and classify(town, a) == "working"


def test_the_quarter_of_a_whole_town_judges_its_side_hustles():
    from conftest import small_town
    from engine.rtr_makers import open_hustle
    town = small_town("world=rtr", *NOBODY_STARTS, "stop_on_failure=false")
    for _ in range(13):
        town.step()
    someone = next(a for a in town.agents if a.role == "staff" and "housing" in a.unit)
    h = open_hustle(town, someone, "repair")                         # nobody owns anything: no customers
    for _ in range(13):
        town.step()
    assert not h.alive and stopped(town) == [("few customers", someone.id)]


# --- task 5: selling hours: repairers and builders ---------------------------------------------------
def own_home(town, a):
    unit = town.new_own_unit(town.needs["housing"], a)
    a.unit["housing"], unit.occupant = unit, a
    return unit


def kept(town, unit):
    from engine.production import best_condition
    return unit.cond == best_condition(town.cfg, unit)


def test_an_owner_pays_a_repairer_who_comes_to_less_than_their_own_hours():
    from engine import rtr_makers, rtr_owning
    town = quiet_town()
    owner = worker(town, cash=100_000)
    unit = own_home(town, owner)                                     # needs 1.6 hours and $43.20 of parts a week
    m, h = maker(town, "repair")                                     # an hour of theirs at 1,750: 1,925 with the tenth
    hours_for_the_week(town)
    assert rtr_makers.cheapest_hour(town, owner, "repair") == 1_925 and rtr_makers.cheapest_hour(town, m, "repair") is None
    rtr_owning.keep(town, owner)
    assert owner.cash == 100_000 - 7_832 and owner.spare_hours == 20.0   # (4,320 + 2,800) x 1.1, and no hour of theirs
    assert owner.spend_week == 7_832
    assert h.cash == 7_832 - 4_320 and m.cash == 0                   # in the till until the week's end
    assert m.spare_hours == pytest.approx(58.4) and h.sold == pytest.approx(1.6)
    assert (h.w_revenue, h.w_goods) == (7_832, 4_320)
    assert town.ledger.week_internal["maker_hours"] == 7_832 and town.ledger.week_out["import"] == 4_320
    assert kept(town, unit) and unit.age == 1
    rtr_makers.after_bills(town)
    assert (h.q_sold, h.q_could, h.q_revenue, h.q_goods) == (pytest.approx(1.6), 60.0, 7_832, 4_320)
    assert h.cash == 0 and m.cash == 7_832 - 4_320                   # and then theirs


def test_a_dearer_repairer_is_used_only_by_someone_short_of_hours_who_has_the_money():
    from engine import rtr_owning
    town = quiet_town()
    has_time, no_time, no_money = worker(town, cash=100_000), worker(town, cash=100_000), worker(town, cash=0)
    for a in (has_time, no_time, no_money):
        own_home(town, a)
    m, h = maker(town, "repair", agent=worker(town))                 # in work: 2,750 an hour, dearer than their own 2,500
    hours_for_the_week(town)
    no_time.spare_hours = no_money.spare_hours = 0.0
    for a in (has_time, no_time, no_money):
        rtr_owning.keep(town, a)
    assert has_time.cash == 100_000 - 4_320 and has_time.spare_hours == pytest.approx(18.4)
    assert no_time.cash == 100_000 - 9_152 and h.sold == pytest.approx(1.6)      # (4,320 + 4,000) x 1.1
    assert kept(town, has_time.unit["housing"]) and kept(town, no_time.unit["housing"])
    assert no_money.cash == 0 and not kept(town, no_money.unit["housing"])       # it wears


def test_someone_with_half_the_hours_does_those_and_buys_the_rest():
    from engine import rtr_owning
    town = quiet_town()
    owner = worker(town, cash=100_000)
    unit = own_home(town, owner)
    m, h = maker(town, "repair", agent=worker(town))                 # dearer than their own hour
    hours_for_the_week(town)
    owner.spare_hours = 0.8
    rtr_owning.keep(town, owner)
    assert h.sold == pytest.approx(0.8) and owner.spare_hours == 0.0
    assert owner.cash == 100_000 - 4_576 - 2_160                     # half from the repairer, parts and all; half their own parts
    assert kept(town, unit)


def test_hours_are_bought_only_with_cash_beyond_four_weeks_of_bills():
    from engine import rtr_owning
    from engine.subscriptions import subscribe
    town = quiet_town()
    owner = worker(town, cash=44_576)
    unit = own_home(town, owner)
    food = shop(town, "food", 10_000)
    assert subscribe(town, owner, food)                              # four weeks of bills: $400
    m, h = maker(town, "repair", agent=worker(town))
    hours_for_the_week(town)
    owner.spare_hours = 0.0
    rtr_owning.keep(town, owner)                                     # $45.76 to spare: half the job
    assert h.sold == pytest.approx(0.8) and not kept(town, unit)
    assert owner.cash == 40_000 - 2_160                              # and the parts for the other half, as in stage 1


def test_a_repairer_sells_only_the_hours_their_own_home_leaves_them():
    from engine import rtr_makers, rtr_owning
    town = quiet_town()
    m, h = maker(town, "repair", agent=worker(town, cash=1_000_000))
    mine = own_home(town, m)                                         # 1.6 of their 20 hours are spoken for
    hours_for_the_week(town)
    assert h.hours == pytest.approx(18.4)
    busy = worker(town, cash=10_000_000)
    busy.spare_hours = 0.0
    assert rtr_makers.buy_hours(town, busy, "repair", 30.0, 0.0, 10_000_000) == pytest.approx(18.4)
    assert m.spare_hours == pytest.approx(1.6) and busy.cash == 10_000_000 - 50_600
    assert rtr_makers.cheapest_hour(town, busy, "repair") is None    # sold out for the week
    rtr_owning.keep(town, m)
    assert kept(town, mine) and m.spare_hours == pytest.approx(0.0)


def test_the_cheapest_maker_is_used_first_then_the_next_and_never_past_the_budget():
    from engine import rtr_makers
    town = quiet_town()
    (a, ha), (b, hb) = maker(town, "repair", agent=worker(town)), maker(town, "repair")      # 2,750 and 1,925 an hour
    hours_for_the_week(town)
    c = worker(town, cash=10_000_000)
    assert rtr_makers.buy_hours(town, c, "repair", 70.0, 0.0, 10_000_000) == pytest.approx(70.0)
    assert hb.sold == pytest.approx(60.0) and ha.sold == pytest.approx(10.0)
    assert c.cash == 10_000_000 - 60 * 1_925 - 10 * 2_750
    d = worker(town, cash=10_000_000)
    assert rtr_makers.buy_hours(town, d, "repair", 5.0, 0.0, 5_500) == pytest.approx(2.0) and d.cash == 10_000_000 - 5_500
    assert rtr_makers.buy_hours(town, d, "repair", 5.0, 0.0, 10_000_000, under=2_750) == 0.0     # none under that price
    hours_for_the_week(town)
    e = worker(town, cash=10_000_000)                                # $1,292.50: all sixty of the cheap hours and five more
    assert rtr_makers.buy_hours(town, e, "repair", 70.0, 0.0, 129_250) == pytest.approx(65.0)


def test_on_a_map_a_maker_out_of_reach_sells_them_no_hours():
    from engine import rtr_makers
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS)
    landlord = premises(town, "housing", 6, 5)
    near, far = block(town, landlord, 5, 6, homes=2), block(town, landlord, 12, 12, homes=1)
    c, m = tenant(town, near), tenant(town, far, cash=0)
    m.last_wage = town.cfg.outside_wage
    _, h = maker(town, "repair", agent=m)
    hours_for_the_week(town)
    assert rtr_makers.cheapest_hour(town, c, "repair") is None
    assert rtr_makers.buy_hours(town, c, "repair", 5.0, 0.0, 1_000_000) == 0.0
    n = tenant(town, near, cash=0)
    n.last_wage = town.cfg.outside_wage
    maker(town, "repair", agent=n)
    hours_for_the_week(town)
    assert rtr_makers.cheapest_hour(town, c, "repair") == 1_925


def building_tenant(cash=5_000_000):
    from engine import rtr_owning
    from test_rtr import _tenant_with_a_job
    town, a, landlord = _tenant_with_a_job(cash, *NOBODY_STARTS)
    rtr_owning.consider_building(town, a)
    assert a.build is not None
    return town, a


def builder_next_door(town, a, weeks_out=10, job=False):
    from test_places import employ, tenant
    b = tenant(town, a.unit["housing"].spot, cash=0)                 # the builder lives on the same block
    b.last_wage, b.weeks_out = town.cfg.outside_wage, weeks_out      # ten weeks out: an hour at the floor
    if job:
        employ(b, a.employer)
    return maker(town, "home_building", agent=b)


@pytest.mark.fifth_in_cash
def test_a_builder_is_paid_for_hours_and_materials_and_the_bank_still_lends_on_the_materials():
    from engine import rtr_makers, rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    a.spare_hours, per_hour = 20.0, 4_500                            # 500 units at $108 over 1,200 hours
    assert h.price == round(1.1 * rtr_makers.hour_worth(town, b))
    rtr_owning.work(town, a)
    paid = round(60 * (h.price + per_hour * 1.1))
    assert a.build.hours_left == pytest.approx(1_200 - 80)           # sixty bought, twenty of their own
    assert a.build.goods_left == pytest.approx(500 * (1 - 80 / 1_200))
    assert town.ledger.week_internal["maker_hours"] == paid and h.cash == paid - 60 * per_hour
    assert b.spare_hours == pytest.approx(0.0) and a.build.borrowed == a.home_loan
    assert a.home_loan == round(0.8 * 80 * per_hour)                 # four fifths of the materials, whoever did the hours
    assert a.build.spent == paid + 20 * per_hour


def test_a_dearer_builder_is_hired_while_the_home_would_take_them_more_than_a_quarter_and_not_after():
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a, weeks_out=0, job=True)         # in work: dearer than their own hour
    hours_for_the_week(town)
    a.spare_hours, a.build.hours_left = 20.0, 300.0                  # fifteen weeks of theirs: more than a quarter
    assert h.hours == pytest.approx(b.spare_hours) and h.hours > 0
    had = h.hours
    rtr_owning.work(town, a)
    assert h.sold == pytest.approx(had) and a.build.hours_left == pytest.approx(300 - had - 20)
    hours_for_the_week(town)
    a.spare_hours, a.build.hours_left = 20.0, 260.0                  # thirteen weeks of theirs: they have the hours
    rtr_owning.work(town, a)
    assert h.sold == 0.0 and a.build.hours_left == pytest.approx(240.0)


@pytest.mark.fifth_in_cash
def test_someone_with_little_money_buys_the_builder_hours_it_pays_for():
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    a.spare_hours = 0.0
    bills = rtr_owning._bills(town, a)
    a.cash = 4 * bills + 27_250                                      # each hour costs them $27.25 beyond the bank's $36
    rtr_owning.work(town, a)
    assert h.sold == pytest.approx(10.0, abs=0.01) and a.cash == pytest.approx(4 * bills, abs=2)
    assert a.home_loan == pytest.approx(36_000, abs=4)               # the bank's $36 on each of the ten hours


def test_a_builder_builds_their_own_home_with_the_hours_nobody_bought():
    from engine import rtr_owning
    from test_places import employ
    town, a = building_tenant()
    b, h = builder_next_door(town, a, weeks_out=0, job=True)
    b.cash = 5_000_000
    rtr_owning.consider_building(town, b)
    assert b.build is not None and town.agents.index(a) < town.agents.index(b)
    hours_for_the_week(town)
    a.spare_hours, a.build.hours_left = 20.0, 5.0                    # the customer needs only five hours, and has them
    left = b.spare_hours
    rtr_owning.after_bills(town)
    assert h.sold == 0.0 and b.build.hours_left == pytest.approx(1_200 - left)
    town2, a2 = building_tenant()
    b2, h2 = builder_next_door(town2, a2, weeks_out=0, job=True)
    b2.cash = 5_000_000
    rtr_owning.consider_building(town2, b2)
    town2.agents.remove(b2)
    town2.agents.insert(0, b2)                                       # the builder comes first in the week's order
    hours_for_the_week(town2)
    a2.spare_hours = 0.0
    left = b2.spare_hours
    rtr_owning.after_bills(town2)
    assert h2.sold == pytest.approx(left) and b2.build.hours_left == pytest.approx(1_200)     # customers first


def test_a_set_builder_is_paid_for_hours_only():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building")                               # 1,925 an hour
    hours_for_the_week(town)
    a.spare_hours, cash = 0.0, a.cash                                # twenty hours they do not have
    rtr_owning.work(town, a)
    assert rtr_owning.owns(a, "appliances") and a.cash == cash - 38_500 and h.cash == 38_500
    assert "maker_hours" in town.ledger.week_internal and "import" not in {k for k, v in town.ledger.week_out.items()
                                                                           if v != 540_000}


def test_someone_with_the_hours_builds_their_own_set_whatever_a_builder_charges():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building")                               # 1,925 an hour: cheaper than their own, and not needed
    hours_for_the_week(town)
    a.spare_hours, cash = 20.0, a.cash
    rtr_owning.work(town, a)
    assert rtr_owning.owns(a, "appliances") and a.cash == cash and h.sold == 0.0 and a.spare_hours == 0.0


# --- task 6: the record and the weekly checks ---------------------------------------------------------
def measures(town):
    from engine.metrics import weekly_series
    return {measure: value for scope, measure, value in weekly_series(town) if scope == "town"}


def test_the_week_counts_makers_their_customers_their_hours_and_their_takings():
    from engine import rtr_owning
    town = quiet_town()
    a, h = maker(town)
    people = customers(town, h, 3)
    from engine.subscriptions import set_plan
    set_plan(town, people[0], h, 2)
    owner = worker(town, cash=100_000)
    own_home(town, owner)
    m, hm = maker(town, "repair")
    a_week(town)
    got = measures(town)
    assert (got["makers"], got["maker_customers"]) == (2, 4)         # a bigger plan counts as two
    assert got["maker_hours_sold"] == pytest.approx(1.6)
    assert got["maker_revenue"] == 4 * 6_820 + 7_832


def test_a_wef_town_has_no_measures_of_makers():
    from conftest import empty_town
    assert not [m for m in measures(empty_town()) if m.startswith("maker")]


def _problems(town):
    from test_town_invariants import check_week
    return check_week(town, town.money_in_town(), town.population, {a.id for a in town.agents})


def test_the_weekly_checks_know_a_sound_side_hustle_from_a_broken_one():
    town = quiet_town("population_cap=1000")
    a, h = maker(town)
    people = customers(town, h, 2)
    m, hm = maker(town, "repair")
    from engine.household import update_agents
    update_agents(town)
    town.ledger.start_week()
    assert _problems(town) == []
    for breakage, undo, word in (
            (lambda: setattr(a, "hustle", None), lambda: setattr(a, "hustle", h), "owner does not know it"),
            (lambda: town.hustles.remove(h), lambda: town.hustles.insert(0, h), "not in the town's list"),
            (lambda: setattr(h, "alive", False), lambda: setattr(h, "alive", True), "stopped"),
            (lambda: h.subs.pop(people[0].id), lambda: h.subs.__setitem__(people[0].id, people[0]), "subscription"),
            (lambda: people[0].subs.pop("entertainment"), lambda: people[0].subs.__setitem__("entertainment", h),
             "not a customer"),
            (lambda: setattr(h, "extra", 1), lambda: setattr(h, "extra", 0), "bigger plans"),
            (lambda: setattr(hm, "sold", 61.0), lambda: setattr(hm, "sold", 0.0), "more hours than it had"),
            (lambda: hm.subs.__setitem__(a.id, a), lambda: hm.subs.clear(), "sells hours")):
        breakage()
        found = _problems(town)
        assert any(word in line for line in found), (word, found)
        undo()
    assert _problems(town) == []


def test_the_weekly_checks_know_a_maker_who_is_their_own_customer():
    from engine.subscriptions import subscribe
    town = quiet_town("population_cap=1000")
    a, h = maker(town)
    from engine.household import update_agents
    assert subscribe(town, a, h)
    update_agents(town)
    town.ledger.start_week()
    assert any("own customer" in line for line in _problems(town))


# --- task 6: Part A in whole towns ----------------------------------------------------------------------
# With stage 2's rules switched off an RTR town is the stage 1 town. On 18/11, before the weekly measures of
# makers were added, three such towns gave the very record the code before stage 2 gave (see the ledger).
# These are two of them at six years. The pin is on the events alone, so that a new weekly measure does
# not trip it: what happened in the town is what must not change.
RTR_STAGE_ONE_PINS = [(["seed=11", "map_width=7", "map_height=7"], ("5a3cac3b44fe4507", 12038)),
                      (["seed=5", "map_width=0"], ("5d0659b32590395a", 9617))]


def events_alone(town):
    import hashlib
    import json
    text = json.dumps(town.rec.events, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:16], len(town.rec.events)


@pytest.mark.parametrize("place, record", RTR_STAGE_ONE_PINS)
def test_an_rtr_town_with_stage_two_switched_off_is_the_stage_one_town(place, record):
    from engine.town import Town
    # and with the bank asking its fifth in cash, as it did until Jason's ruling of 18 November; and with
    # one rate for all a firm's staff, cut when anyone has no job, as it was until his rulings of the 19th
    town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false", *NOBODY_STARTS,
                                   *FIFTH_IN_CASH, *BEFORE_THE_LINE, *place]))
    for _ in range(6 * 52):
        town.step()
    assert events_alone(town) == record and town.hustles == [] and town.ideas_total == 0


def _reached(town, hours_sold, wages_paid=0):
    """Which rules of stage 2 a town's own record shows it reached."""
    import collections
    from engine.rtr_makers import HOUR_TRADES
    seen, thought_up = collections.Counter(), set()
    for e in town.rec.events:
        kind, data = e["kind"], e["data"]
        by_a_maker = e["firm"] is not None and e["firm"] <= -1_000_000
        if kind == "hustle_started":
            seen["a side hustle started that sells hours" if data["trade"] in HOUR_TRADES
                 else "a side hustle started in a need"] += 1
            seen["started: " + data["trade"]] += 1
            if (e["agent"], data["trade"]) in thought_up:
                seen["a creator started their idea"] += 1
        elif kind == "hustle_stopped":
            seen["a maker gave it up: " + data["reason"]] += 1
        elif kind == "sub_start" and by_a_maker:
            seen["a customer signed up to a maker"] += 1
        elif kind == "price_change" and by_a_maker:
            seen["a maker's price " + ("rose" if e["amount"] > data["old"] else "fell")] += 1
            if data["reason"] == "business":
                seen["a new business priced its hour at the going wage"] += 1
        elif kind == "idea":
            seen["an idea"] += 1
            thought_up.add((e["agent"], data["need"]))
        elif kind == "hustle_loan":
            seen["a loan on profit"] += 1
        elif kind == "hustle_loan_missed":
            seen["a payment on it missed"] += 1
        elif kind == "default" and data.get("what") == "side hustle":
            seen["a loan on profit written off"] += 1
        elif kind == "hire" and by_a_maker:
            seen["a business took someone on"] += 1
        elif kind == "layoff" and by_a_maker:
            seen["a business let someone go: " + data["reason"]] += 1
        elif kind == "maker_company":
            seen["a maker became a company"] += 1
    if hours_sold > 0:
        seen["hours sold"] += 1
    if wages_paid > 0:
        seen["a business paid wages"] += 1
    return seen


@pytest.fixture(scope="module")
def whole_towns():
    """Towns of 200 run for fourteen years under the weekly checks with every rule of stage 2 on:
    seeds 10 and 2 on a 7 by 7 map, and seeds 5 and 3 with no map. For each kind: (what the checks
    found, what was reached)."""
    import collections
    from engine.town import Town
    from test_town_invariants import run_checked
    out = {}
    for kind, seeds, place in (("map", (10, 2), ["map_width=7", "map_height=7"]), ("no map", (5, 3), ["map_width=0"])):
        problems, seen = [], collections.Counter()
        for seed in seeds:
            town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false",
                                           f"seed={seed}", *BEFORE_THE_RULINGS] + place))   # the towns the seeds were picked for
            hours_sold, wages_paid = 0.0, 0
            for _ in range(14 * 52):
                problems += run_checked(town, 1)
                hours_sold += sum(h.sold for h in town.hustles if h.spec is None)
                wages_paid += sum(h.w_wages for h in town.hustles)
                if len(problems) > 20:
                    break
            seen += _reached(town, hours_sold, wages_paid)
        out[kind] = (problems, seen)
    return out


PART_A = ["a side hustle started in a need", "a side hustle started that sells hours", "started: food",
          "started: entertainment", "started: repair", "started: set_building", "started: home_building",
          "a customer signed up to a maker", "a maker gave it up: few customers", "a maker's price fell",
          "a maker's price rose", "hours sold"]


def _all_reached(seen, kinds):
    for kind in kinds:
        assert seen[kind] > 0, f"these towns never reached '{kind}': pick seeds that do"


# Part B. A maker becoming a company is rare in a town of 200 (it needs about $214,000 in one maker's hands)
# and is asked of the four towns together, not of each kind. Three things have become too rare for a small
# town since the fresh review's fixes and are held by their own tests alone: a worker let go unpaid (staff
# are paid out of the takings, and nobody is taken on without a week of their wage in hand); a loan payment
# missed; and a business ended by its loan (what the bank lent stays in the business and pays the bank).
RARE = ["a maker became a company"]
PART_B = ["an idea", "a creator started their idea", "a loan on profit", "a new business priced its hour at the going wage",
          "a business took someone on", "a business paid wages", "a business let someone go: laid_off"]


def test_part_a_towns_keep_their_accounts_and_places_and_reach_every_rule(whole_towns):
    problems, seen = whole_towns["map"]
    assert problems == []
    _all_reached(seen, PART_A + ["a maker gave it up: no hours"])


def test_part_b_towns_reach_every_rule_too(whole_towns):
    problems, seen = whole_towns["map"]
    assert problems == []
    _all_reached(seen, PART_B)


def test_a_town_with_no_map_keeps_its_accounts_and_reaches_the_rules_too(whole_towns):
    problems, seen = whole_towns["no map"]
    assert problems == []
    _all_reached(seen, PART_A + PART_B)


def test_between_them_the_towns_reach_the_rare_rules_too(whole_towns):
    _all_reached(whole_towns["map"][1] + whole_towns["no map"][1], RARE)


def test_a_town_where_every_firm_closes_still_balances_with_its_makers_businesses_staff_and_loans():
    from engine.corporate import wind_up
    from engine.town import Town
    from test_town_invariants import run_checked
    town = Town(load_config(None, ["world=rtr", "population_cap=200", "stop_on_failure=false", "seed=2",
                                   "map_width=7", "map_height=7", *BEFORE_THE_RULINGS]))   # the town this seed was picked for
    for year in range(13):                       # on until businesses with staff and loans are standing
        assert run_checked(town, 52) == []
        if year >= 6 and any(h.staff for h in town.hustles) and any(h.loan > 0 for h in town.hustles):
            break
    else:
        pytest.fail("no business with staff and a loan in thirteen years: pick another seed")
    for firm in list(town.alive_firms):          # every landlord and shop is gone in a week
        wind_up(town, firm, "test")
    assert run_checked(town, 3 * 52) == []


# --- found by breaking the rules on purpose (18/11) -------------------------------------------------------
def test_the_floor_under_a_makers_hour_follows_the_going_wage():
    from engine.rtr_makers import hour_worth
    town = quiet_town()
    firm = shop(town, "food", 40_000)
    pays(firm, 120_000)                                              # the going wage is now $1,200
    out = jobless(town)
    out.weeks_out = 20
    assert hour_worth(town, out) == 1_500.0


def test_a_maker_keeps_up_their_own_set_before_the_side_hustle_too():
    town = quiet_town()
    a, h = maker(town)
    unit = town.new_own_unit(town.needs["appliances"], a)
    a.unit["appliances"], unit.occupant = unit, a                    # 0.4 hours a week
    hours_for_the_week(town)
    assert h.hours == pytest.approx(59.6)


def test_a_need_thought_up_this_week_is_open_to_everyone_from_the_next():
    from engine import rtr_makers
    town = quiet_town()
    town.new_ideas.add("something")
    rtr_makers.start_week(town)
    assert town.new_ideas == set()


def test_customers_who_went_unserved_are_served_again_when_the_hours_come_back():
    town = quiet_town()
    a, h = maker(town)
    customers(town, h, 12, cash=1_000_000)
    boss = town.add_firm("housing")
    a.employer, a.role, a.wage = boss, "staff", 100_000
    boss.staff.append(a)
    a_week(town)
    assert len(h.unserved) == 2
    boss.staff.remove(a)
    a.employer = a.role = None
    a_week(town)
    assert h.unserved == {} and h.w_revenue == 12 * 6_820


def test_tools_are_not_bought_out_of_the_four_weeks_of_bills_they_keep():
    from engine.rtr_makers import can_tool_up, pay_tools
    from engine.subscriptions import subscribe
    town = quiet_town()
    a = worker(town, cash=240_000)
    assert subscribe(town, a, shop(town, "food", 10_000))            # four weeks of bills: $400
    assert can_tool_up(town, a, 220_000) and pay_tools(town, a, 220_000)     # $2,200 of tools: $200 short
    assert (a.cash, a.loan) == (40_000, 20_000)                      # borrowed, not taken from the bills money
    b = jobless(town, cash=240_000)
    assert subscribe(town, b, town.firms_for("food")[0])
    assert not can_tool_up(town, b, 200_001) and not pay_tools(town, b, 200_001)
    assert b.cash == 240_000


def test_a_second_maker_must_undercut_the_first_not_the_shop():
    from engine.rtr_makers import best_trade, consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 9_500)
    shop(town, "food", 40_000)
    first, second = jobless(town), jobless(town)
    consider_hustles(town)
    assert first.hustle is not None and second.hustle is None        # the same hour, the same price: no undercut
    second.weeks_out = 10
    assert best_trade(town, second) == ("entertainment", 5_720)      # now they would


def test_a_repairer_who_does_not_come_to_less_once_the_margin_on_parts_is_counted_is_not_used():
    from engine import rtr_owning
    town = quiet_town()
    owner = worker(town, cash=100_000)
    unit = own_home(town, owner)
    m, h = maker(town, "repair")
    h.price = 2_300                              # under their own 2,500 an hour, but 10% on $27 of parts an hour is 270 more
    hours_for_the_week(town)
    rtr_owning.keep(town, owner)
    assert h.sold == 0.0 and owner.spare_hours == pytest.approx(18.4) and kept(town, unit)
    h.price = 2_229
    owner.spare_hours = 20.0
    rtr_owning.keep(town, owner)
    assert h.sold == pytest.approx(1.6, abs=0.01) and owner.spare_hours == 20.0      # a week older: a shade more upkeep


def test_a_cheap_repairer_is_paid_only_with_cash_beyond_four_weeks_of_bills():
    from engine import rtr_owning
    from engine.subscriptions import subscribe
    town = quiet_town()
    owner = worker(town, cash=43_916)
    unit = own_home(town, owner)
    assert subscribe(town, owner, shop(town, "food", 10_000))        # four weeks of bills: $400
    m, h = maker(town, "repair")                                     # $48.95 an hour with the parts: $39.16 buys 0.8 hours
    hours_for_the_week(town)
    rtr_owning.keep(town, owner)
    assert h.sold == pytest.approx(0.8) and owner.spare_hours == pytest.approx(20.0 - 0.8)
    assert owner.cash == 40_000 - 2_160 and kept(town, unit)         # the other half they did themselves


def test_a_repairer_is_no_builder_of_sets():
    from engine import rtr_makers
    town = quiet_town()
    maker(town, "set_building")
    hours_for_the_week(town)
    c = worker(town, cash=1_000_000)
    assert rtr_makers.cheapest_hour(town, c, "repair") is None
    assert rtr_makers.buy_hours(town, c, "repair", 5.0, 0.0, 1_000_000) == 0.0


def test_someone_short_of_hours_does_what_they_can_and_pays_a_dearer_set_builder_for_the_rest():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building", agent=worker(town))           # 2,750 an hour: dearer than their own
    hours_for_the_week(town)
    a.spare_hours, cash = 1.0, a.cash                                # twenty hours is twenty weeks of theirs
    rtr_owning.work(town, a)
    assert h.sold == pytest.approx(19.0) and rtr_owning.owns(a, "appliances") and a.cash == cash - 52_250
    assert a.spare_hours == 0.0                                      # their own hour went into it first


def test_a_builder_whose_hour_and_margin_on_materials_come_to_more_than_their_own_is_not_hired_near_the_end():
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    h.price = 2_200                              # under 2,500, but the 10% on $45 of materials an hour is 450 more
    a.spare_hours, a.build.hours_left = 20.0, 200.0
    rtr_owning.work(town, a)
    assert h.sold == 0.0 and a.build.hours_left == pytest.approx(180.0)
    h.price = 2_049
    a.spare_hours = 20.0
    rtr_owning.work(town, a)
    assert h.sold == pytest.approx(60.0) and a.build.hours_left == pytest.approx(180.0 - 80)


def test_a_home_a_builder_finishes_is_theirs_that_week():
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)
    hours_for_the_week(town)
    a.spare_hours, a.build.hours_left, a.build.goods_left = 0.0, 30.0, 12.5
    rtr_owning.work(town, a)
    assert a.build is None and rtr_owning.owns(a, "housing") and h.sold == pytest.approx(30.0)
    assert [e["kind"] for e in town.rec.events if e["kind"] == "home_built"] == ["home_built"]


def test_a_whole_week_of_the_town_gives_a_side_hustle_its_hours_its_customers_and_its_goods():
    town = quiet_town()
    a, h = maker(town)
    people = customers(town, h, 3, cash=10_000_000)                  # with a cushion, so they keep a luxury
    town.step()
    town.step()
    assert (h.w_revenue, h.w_goods) == (20_460, 8_100)               # this week's alone: the week began afresh
    assert (h.q_sold, h.q_could, h.q_revenue) == (6, 60, 40_920) and a.cash == 24_720
    assert [p.cash for p in people] == [10_000_000 - 2 * 6_820] * 3


def test_the_quarter_of_a_whole_town_sets_a_makers_price_again():
    town = quiet_town()
    a, h = maker(town)
    customers(town, h, 10, cash=10_000_000)
    for _ in range(13):
        town.step()
    assert h.alive and h.price < 6_820 and h.profit_week > 0         # thirteen weeks out of work: their hour is worth less


def test_someone_at_the_going_wage_undercuts_nobodys_own_hour_and_the_cheapest_rival_is_the_one_to_beat():
    from engine.rtr_makers import best_trade
    town = quiet_town()
    shop(town, "entertainment", 5_000)
    shop(town, "food", 20_000)
    owners(town, 60)                                                 # plenty to repair: 96 hours a week
    assert best_trade(town, worker(town, cash=2_000_000)) is None    # 2,750 an hour against their own 2,500
    a = jobless(town, cash=2_000_000)
    assert best_trade(town, a) == ("repair", 1_925)
    for price in (2_000, 1_900):
        _, rival = maker(town, "repair")
        rival.price = price
        rival.hours = 0.0                                            # (they have no hours this week: the work is still there)
    assert best_trade(town, a) is None                               # under one repairer, not under the cheapest


def test_nobody_starts_a_trade_whose_tools_they_cannot_pay_for():
    from engine.rtr_makers import start_hustle
    town = quiet_town()
    a = jobless(town, cash=199_999)
    assert start_hustle(town, a, "food") is None and a.hustle is None and town.hustles == [] and a.cash == 199_999
    a.cash = 200_000
    assert start_hustle(town, a, "food") is a.hustle and a.cash == 0


def test_ten_spare_hours_exactly_is_enough_to_start():
    from engine.rtr_makers import consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 9_500)
    a = jobless(town)
    a.travel_hours = 50.0
    consider_hustles(town)
    assert a.hustle is not None


def test_a_set_builder_is_paid_only_with_cash_beyond_four_weeks_of_bills():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building")                               # 1,925 an hour
    hours_for_the_week(town)
    bills = rtr_owning._bills(town, a)
    assert bills > 0
    a.spare_hours, a.cash = 0.0, 4 * bills + 19_250                  # ten hours' worth to spare
    rtr_owning.work(town, a)
    assert h.sold == pytest.approx(10.0) and a.set_hours_left == pytest.approx(10.0) and a.cash == 4 * bills


# === Part B: ideas, and side hustles that grow ==========================================================
# --- task 7: ideas ---------------------------------------------------------------------------------------
def invented(town):
    return [s for s in town.needs.values() if s.invented]


def test_an_idea_comes_from_spare_time_and_its_creator_may_start_it_at_once():
    from engine import rtr_makers
    from engine.rtr_makers import ideas, trades
    town = rtr_town("idea_rate=1.0")
    a, idle = jobless(town, cash=60_000), jobless(town, cash=0)
    a.spare_hours, idle.spare_hours = 20.0, 0.0                      # a full chance, and none
    ideas(town)
    (new,) = invented(town)
    assert a.hustle.trade == new.name and a.cash == 10_000           # $500 of tools
    assert idle.hustle is None and town.ideas_total == 1
    assert [(e["agent"], e["data"]["need"]) for e in town.rec.events if e["kind"] == "idea"] == [(a.id, new.name)]
    assert started(town) == [(a.id, 50_000, new.name, a.hustle.price)]
    assert new.name not in [t for t, _ in trades(town)]              # open to everyone else from next week
    rtr_makers.start_week(town)
    assert new.name in [t for t, _ in trades(town)]
    assert measures(town)["ideas"] == 1


def test_the_chance_of_an_idea_grows_with_the_spare_hours_left():
    from engine.rtr_makers import ideas
    town = rtr_town("idea_rate=0.5")
    a, b = jobless(town), jobless(town)
    a.spare_hours, b.spare_hours = 40.0, 0.0
    ideas(town)
    assert town.ideas_total == 1                                     # 0.5 for each twenty hours: certain at forty
    town2 = rtr_town("idea_rate=0.01")
    c = jobless(town2)
    c.spare_hours = 20.0
    town2.rng = Dice(0.01)
    ideas(town2)
    assert town2.ideas_total == 0
    town2.rng = Dice(0.00999)
    c.spare_hours = 20.0
    ideas(town2)
    assert town2.ideas_total == 1
    c.spare_hours = 10.0                                             # half the hours, half the chance
    town2.rng = Dice(0.005)
    ideas(town2)
    assert town2.ideas_total == 1


def test_a_creator_who_cannot_start_it_still_had_the_idea_and_nobody_is_paid_for_it():
    from engine.rtr_makers import ideas
    town = rtr_town("idea_rate=1.0")
    broke, busy = jobless(town, cash=49_999), jobless(town, cash=1_000_000)
    _, h = maker(town, agent=busy)                                   # already has a side hustle
    tired = jobless(town, cash=1_000_000)
    tired.travel_hours = 51.0                                        # an idea needs any spare time; starting needs ten hours
    for a in (broke, busy, tired):
        a.spare_hours = 20.0
    money = town.money_in_town()
    ideas(town)
    assert town.ideas_total == 3 and len(invented(town)) == 3
    assert broke.hustle is None and busy.hustle is h and tired.hustle is None
    assert town.money_in_town() == money and started(town) == []


def test_on_a_map_a_creator_with_no_home_can_start_their_idea():
    from engine.rtr_makers import ideas
    town = map_rtr_town("idea_rate=1.0", "hustle_rate=0.0", "hustle_rate_struggling=0.0")
    a = jobless(town, cash=1_000_000)
    a.spare_hours = 20.0
    ideas(town)
    assert town.ideas_total == 1 and a.hustle is not None and a.hustle.spot is None


def test_ideas_come_in_the_week_after_upkeep_side_hustle_and_building_have_had_their_hours():
    town = rtr_town("idea_rate=0.0125", "hustle_rate=0.0", "hustle_rate_struggling=0.0")
    a, h = maker(town)
    customers(town, h, 30, cash=10_000_000)                          # every hour of theirs goes to customers
    b = jobless(town)                                                # sixty hours left: 0.0375 a week
    town.rng = Dice(0.03)
    a_week(town)
    had = [e["agent"] for e in town.rec.events if e["kind"] == "idea"]
    assert a.id not in had and b.id in had                           # the maker had no hour left to think in
    assert town.ideas_total == 31                                    # b and the thirty customers, idle all week


def test_founders_of_firms_do_not_invent_in_the_rtr_world():
    from engine.corporate import choose_venture
    for overrides, count in ((["world=rtr"], 0), (["world=wef"], 1), (["world=rtr", "idea_rate=0.0"], 1)):
        town = rtr_town("invent_prob=1.0", *overrides)
        shop(town, "food", 40_000)
        choose_venture(town, 50_000_000)
        assert len(invented(town)) == count, overrides


# --- task 8: a small business: the loan on profit, and staff -------------------------------------------
def turned_away(town, h, n):
    """n people the maker turned away last week who would have bought: in work, with money to spare."""
    wanting = [worker(town, cash=1_000_000) for _ in range(n)]
    h.turned_away = {w.id: True for w in wanting}
    return wanting


def full_quarter(town, h, profit_week, waiting=20):
    """A quarter in which they sold all they could, with thirty customers and twenty more turned
    away last week who would have bought."""
    if not h.subs:
        customers(town, h, 30)
    h.asked = [w.id for w in turned_away(town, h, waiting)]
    h.turned_away = {}
    town.week, h.q_sold, h.q_could, h.waiting = 13, 390, 390, waiting
    h.q_revenue, h.q_goods = 13 * profit_week, 0


def make_business(town, h):
    """A side hustle made a small business by hand: it prices as one."""
    from engine.rtr_makers import price_now
    h.business, h.wage = True, town.typical_wage()
    h.price = price_now(town, h)
    return h


def on_the_staff(h, *people):
    for w in people:
        w.employer, w.role, w.wage = h, "staff", h.wage
        h.staff.append(w)


def test_a_maker_full_for_a_quarter_borrows_on_the_profit_and_becomes_a_small_business():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town), maker(town)
    full_quarter(town, h, 20_000)
    full_quarter(town, hb, 15_000)                                   # 26 weeks of it is under four weeks' wages
    full_quarter(town, hc, 20_000)
    hc.q_sold = 370                                                  # not full: under 95%
    quarter(town)
    assert h.business and (h.loan, h.loan_pay) == (520_000, 2_000)
    assert (a.cash, h.cash, h.reserve) == (0, 520_000, 520_000)      # the loan is the business's, not their pocket money
    assert h.price == 8_470                      # it prices as a business at once: its hour at the going wage
    assert [(e["amount"], e["data"]["reason"]) for e in town.rec.events if e["kind"] == "price_change"] == [
        (8_470, "business")]
    assert not hb.business and b.cash == 0 and not hc.business and (hb.loan, hc.loan) == (0, 0)
    assert (hb.price, hc.price) == (6_820, 6_820)
    assert [(e["agent"], e["amount"]) for e in town.rec.events if e["kind"] == "hustle_loan"] == [(a.id, 520_000)]
    assert town.ledger.week_in["loan"] == 520_000
    full_quarter(town, h, 40_000)                                    # a business does not ask again
    town.week = 26
    quarter(town)
    assert h.loan == 520_000


def test_the_bank_lends_on_a_whole_quarter_only_and_not_to_someone_it_is_refusing():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town), maker(town)
    for x in (h, hb, hc):
        full_quarter(town, x, 20_000)
    h.started = 1                                                    # twelve weeks old
    b.credit_block_until = 14                                        # refused credit until next week
    hc.q_sold = 371                                                  # 95% and a little: full
    quarter(town)
    assert not h.business and not hb.business and hc.business


def test_a_maker_borrows_only_when_there_is_a_workers_worth_of_customers_they_cannot_serve():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb) = maker(town), maker(town)
    full_quarter(town, h, 20_000, waiting=17)                        # 34 hours over at the business's price: not a wage
    full_quarter(town, hb, 20_000, waiting=18)                       # 36 hours over: it is
    quarter(town)
    assert not h.business and hb.business


def test_a_repairer_or_builder_never_becomes_a_small_business():
    from engine.rtr_makers import quarter
    town = quiet_town()
    made = [maker(town, trade) for trade in ("repair", "set_building", "home_building")]
    town.week = 13
    for _, h in made:                                                # each sold every hour, at a good profit
        h.q_sold, h.q_could, h.q_revenue, h.sold, h.hours = 780.0, 780.0, 13 * 50_000, 60.0, 60.0
    quarter(town)
    assert not any(h.business for _, h in made) and all(h.loan == 0 for _, h in made)
    assert [h.price for _, h in made] == [1_925] * 3                 # at the going wage nobody would buy their hour


def test_the_queue_for_a_loan_is_counted_at_the_price_the_business_will_charge():
    from engine.rtr_makers import quarter
    for shop_price, borrows in ((8_000, False), (9_500, True)):      # the business will charge 8,470
        town = quiet_town()
        shop(town, "entertainment", shop_price)
        a, h = maker(town)
        full_quarter(town, h, 20_000, waiting=0)
        turned_away(town, h, 28)                                     # all would have bought at 6,820
        hours_for_the_week(town)
        assert h.waiting == 28
        town.week, h.q_sold, h.q_could, h.q_revenue = 13, 390, 390, 13 * 20_000
        quarter(town)
        assert h.business is borrows, shop_price                     # at 8,470 they would sooner use a shop at 8,000
        assert h.price == (8_470 if borrows else 6_820)
def test_a_small_business_takes_on_the_staff_its_customers_need_and_serves_more():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town, cash=100_000)                                 # a week of a wage in hand
    make_business(town, h)
    busy = worker(town)                                              # has a job already
    boss = jobless(town)
    boss.klass = "owner"                                             # lives on dividends: not looking for work
    proud = jobless(town, security=1.0)
    proud.last_wage = 300_000                                        # would not take $1,000 a week
    people = customers(town, h, 30)
    turned_away(town, h, 20)                                         # twenty more wanted in last week
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)                                      # 100 hours wanted, 60 of their own: one worker
    hand = people[0]                                                 # the first resident with no job who will take it
    assert h.staff == [hand] and hand.employer is h and hand.role == "staff" and hand.wage == 100_000
    assert h.wage == 100_000 and h.hours == 100.0 and h.capacity == 50       # and they serve more this very week
    assert h.price == 8_470                                          # taking someone on does not move the price
    assert [(e["agent"], e["firm"]) for e in town.rec.events if e["kind"] == "hire"] == [(hand.id, h.id)]
    hours_for_the_week(town)
    assert h.hours == 100.0 and h.capacity == 50
    rtr_makers.hire_staff(town)                                      # nobody turned away this week: thirty need no staff
    assert h.staff == [] and hand.role is None and h.price == 8_470
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "layoff"] == ["laid_off"]


def test_a_worker_is_taken_on_for_a_full_weeks_paying_work_and_kept_while_they_pay_half_their_wage():
    from engine.rtr_makers import staff_wanted
    town = quiet_town()
    a, h = maker(town)
    make_business(town, h)                       # an hour sold brings in (8,470 - 2,700) / 2 = 2,885: a wage is 34.7 hours
    hours_for_the_week(town)
    people = customers(town, h, 47)              # 94 hours wanted, 60 their own: 34 over
    assert staff_wanted(town, h, 100_000) == 0
    people += customers(town, h, 1)              # 36 over: it pays a wage
    assert staff_wanted(town, h, 100_000) == 1
    people += customers(town, h, 21)             # 78 over: one whole week and 38 more
    assert staff_wanted(town, h, 100_000) == 2
    from engine.subscriptions import unsubscribe
    for c in people[39:]:
        unsubscribe(town, c, "entertainment", "test")
    on_the_staff(h, jobless(town))               # 39 customers, 18 hours over: the worker they have pays half their wage
    assert h.load() == 39 and staff_wanted(town, h, 100_000) == 1
    unsubscribe(town, people[38], "entertainment", "test")           # 16 over: not half
    assert staff_wanted(town, h, 100_000) == 0


def test_at_a_price_that_would_not_pay_a_wage_nobody_is_taken_on():
    from engine.rtr_makers import staff_wanted
    town = quiet_town()
    a, h = maker(town)
    h.business, h.wage = True, 100_000           # a business by name, still at their own cheap hour: 2,060 an hour sold
    hours_for_the_week(town)
    customers(town, h, 80)
    assert h.price == 6_820 and staff_wanted(town, h, 100_000) == 0


def test_a_side_hustle_that_is_not_a_business_takes_on_nobody():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town)
    people = customers(town, h, 30)
    h.price = 8_470                                                  # even at a price that would pay a worker
    turned_away(town, h, 20)
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.waiting == 20 and h.staff == []


def test_a_business_takes_someone_on_only_with_a_week_of_their_wage_in_hand():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town)
    make_business(town, h)
    customers(town, h, 30)
    idle = [jobless(town) for _ in range(3)]
    turned_away(town, h, 40)                                         # 140 hours wanted, 60 their own: two workers
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.staff == []                                             # nothing in hand: the first week brings in nothing new
    turned_away(town, h, 40)
    a.cash = 150_000
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert len(h.staff) == 1                                         # $1,500 in hand: one worker's first week
    turned_away(town, h, 40)
    a.cash, h.cash, h.reserve = 0, 100_000, 100_000                  # and what the bank lent it counts as in hand
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert len(h.staff) == 2


def test_staff_are_paid_the_going_wage_and_a_fall_in_it_is_for_those_taken_on_after():
    from engine import rtr_makers
    from engine.rtr_makers import pay_staff
    town = quiet_town()
    firm = shop(town, "food", 40_000)
    a, h = maker(town, cash=1_000_000)
    make_business(town, h)
    customers(town, h, 50)
    w = jobless(town)
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.staff and h.wage == 100_000
    hand = h.staff[0]
    cash = hand.cash
    pay_staff(town)
    assert (hand.cash, hand.income_week, a.cash) == (cash + 100_000, 100_000, 900_000)
    assert (h.w_wages, h.q_wages) == (100_000, 100_000) and town.ledger.week_internal["wage"] == 100_000
    pays(firm, 90_000)                                               # the going wage falls
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.wage == 90_000                                          # what it would pay someone new
    assert hand.wage == 100_000                                      # (Jason, 19/11/2026) "Old staff members still stay on the same pay rate"
    pays(firm, 110_000)
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.wage == 110_000 and hand.wage == 110_000                # and a rise is theirs too


def test_a_small_business_that_cannot_pay_everyone_lets_the_last_hired_go():
    """As built on 18 November. Since Jason's ruling of 19 November the longest-serving goes first;
    this is the rule with that dial off (the ruling's own tests hold it on)."""
    from engine.rtr_makers import pay_staff
    town = quiet_town("longest_serving_first=false")
    a, h = maker(town, cash=150_000)
    h.business, h.wage = True, 100_000
    first, last = jobless(town), jobless(town)
    on_the_staff(h, first, last)
    pay_staff(town)
    assert h.staff == [first] and last.role is None
    assert (a.cash, first.cash, first.income_week, last.cash) == (50_000, 100_000, 100_000, 0)
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "layoff"] == ["unpaid"]


def test_a_small_business_prices_its_hour_at_the_going_wage_and_a_side_hustle_at_its_owners():
    from engine.rtr_makers import quarter
    town = quiet_town()
    (a, h), (b, hb), (c, hc) = maker(town), maker(town, "repair"), maker(town)
    for x in (h, hb):
        x.business = True
    for x in (h, hb, hc):
        town.week, x.q_sold, x.q_could = 13, 300, 390
    a.weeks_out = b.weeks_out = c.weeks_out = 10                     # their own hour is at the floor
    quarter(town)
    assert (h.price, hb.price) == (8_470, 2_750)                     # (2,700 + 2 x 2,500) x 1.1; 2,500 x 1.1
    assert hc.price == 5_720                                         # not a business: their own hour
    boss = worker(town, wage=200_000)
    _, hd = maker(town, agent=boss)                                  # an owner whose own hour is worth more than the going one
    hd.business = True
    for x in (h, hb, hc, hd):
        x.q_sold, x.q_could = 300, 390
    town.week = 26
    quarter(town)
    assert hd.price == round((2_700 + 2 * 5_000) * 1.1)


def test_the_loan_is_paid_weekly_and_four_missed_payments_end_the_business():
    from engine import rtr_makers
    town = quiet_town()
    a, h = maker(town)
    (c,) = customers(town, h, 1)
    h.business, h.wage = True, 100_000
    town.bank.lend_hustle(h, 520_000)
    town.ledger.pay(h, c, 517_400, "gift")                           # all but one week's payment is gone
    h.reserve = h.cash
    assert town.bank.service_hustle(h) and (h.loan, h.cash, h.reserve, a.cash, h.loan_missed) == (518_000, 0, 0, 0, 0)
    assert (town.ledger.week_out["loan_interest"], town.ledger.week_out["loan_principal"]) == (600, 2_000)
    for n in range(1, 4):
        rtr_makers.after_bills(town)
        assert h.alive and h.loan_missed == n
    assert h.loan == 518_000 + 598 + 598 + 599                       # the unpaid interest is added
    rtr_makers.after_bills(town)
    assert a.hustle is None and "entertainment" not in c.subs and town.hustles == []
    assert town.bank.writeoffs_total == 520_395 and h.loan == 0      # four weeks of unpaid interest on top
    assert [(e["amount"], e["data"]["what"]) for e in town.rec.events if e["kind"] == "default"] == [
        (520_395, "side hustle")]
    assert a.credit_block_until == town.week + town.cfg.default_block_weeks
    assert stopped(town) == [("loan", a.id)]


def test_a_business_that_stops_lets_its_staff_go():
    from engine.rtr_makers import stop
    town = quiet_town()
    a, h = maker(town)
    make_business(town, h)
    first, second = jobless(town), jobless(town)
    on_the_staff(h, first, second)
    stop(town, h, "few customers")
    assert h.staff == [] and first.role is None and second.employer is None
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "layoff"] == ["wound_up", "wound_up"]


def test_a_business_that_stops_owing_pays_what_it_can_and_the_rest_is_written_off():
    from engine.rtr_makers import stop
    town = quiet_town()
    (a, h), (b, hb) = maker(town), maker(town)
    for x in (h, hb):
        x.business = True
        town.bank.lend_hustle(x, 520_000)
    town.ledger.pay(hb, a, 400_000, "gift")                          # one business has $1,200 left; the other owner has $4,000 too
    hb.reserve = hb.cash
    stop(town, h, "few customers")
    assert (a.cash, h.cash, a.credit_block_until, town.bank.writeoffs_total) == (400_000, 0, 0, 0)      # paid in full
    stop(town, hb, "few customers")
    assert (b.cash, hb.cash, town.bank.writeoffs_total) == (0, 0, 400_000)
    c, hc = maker(town, cash=600_000)
    hc.business = True
    town.bank.lend_hustle(hc, 520_000)
    town.ledger.pay(hc, a, 520_000, "gift")                          # nothing left in the business; $6,000 of their own
    hc.reserve = 0
    stop(town, hc, "few customers")
    assert (c.cash, c.credit_block_until, town.bank.writeoffs_total) == (80_000, 0, 400_000)     # paid from their pocket
    assert b.credit_block_until == town.cfg.default_block_weeks and b.security < a.security
    assert town.ledger.week_out["loan_principal"] == 520_000 + 120_000 + 520_000


def test_the_week_counts_small_businesses_their_staff_and_what_they_owe():
    town = quiet_town()
    (a, h), (b, hb) = maker(town), maker(town)
    h.business, h.wage = True, 100_000
    on_the_staff(h, jobless(town), jobless(town))
    town.bank.lend_hustle(h, 520_000)
    got = measures(town)
    assert (got["small_businesses"], got["maker_staff"], got["maker_loans"]) == (1, 2, 520_000)


def test_the_weekly_checks_know_a_sound_small_business_from_a_broken_one():
    town = quiet_town("population_cap=1000")
    (a, h), (b, hb) = maker(town), maker(town)
    h.business, h.wage = True, 100_000
    hand, other = jobless(town), jobless(town)
    on_the_staff(h, hand)
    from engine.household import update_agents
    update_agents(town)
    town.ledger.start_week()
    assert _problems(town) == []
    for breakage, undo, word in (
            (lambda: setattr(hb, "loan", 5), lambda: setattr(hb, "loan", 0), "not a business"),
            (lambda: setattr(h, "cash", 7), lambda: setattr(h, "cash", 0), "till"),
            (lambda: setattr(hb, "reserve", 7), lambda: setattr(hb, "reserve", 0), "not a business"),
            (lambda: hb.staff.append(other), lambda: hb.staff.clear(), "not a business"),
            (lambda: setattr(h, "loan", -1), lambda: setattr(h, "loan", 0), "negative"),
            (lambda: setattr(hand, "employer", None), lambda: setattr(hand, "employer", h), "staff"),
            (lambda: h.staff.append(a), lambda: h.staff.remove(a), "own staff")):
        breakage()
        found = _problems(town)
        assert any(word in line for line in found), (word, found)
        undo()
    assert _problems(town) == []


def test_a_whole_week_of_the_town_staffs_and_pays_a_small_business():
    town = quiet_town()
    a, h = maker(town, cash=1_000_000)
    make_business(town, h)
    customers(town, h, 50, cash=10_000_000)                          # fifty want it; their own hours serve thirty
    idle = jobless(town, cash=10_000_000)
    for _ in range(3):
        town.step()
    assert len(h.staff) == 1 and h.capacity == 50 and h.load() == 50 and h.unserved == {}
    hand = h.staff[0]
    assert hand.klass == "working" and hand.income_week == h.wage and hand.employer is h
    assert h.w_wages == h.wage and h.q_wages == 3 * h.wage
    assert h.w_revenue == 50 * 8_470 and h.price == 8_470


# --- task 9: becoming a company ----------------------------------------------------------------------------
def companies(town):
    return [(e["agent"], e["firm"], e["amount"], e["qty"]) for e in town.rec.events if e["kind"] == "maker_company"]


def test_a_maker_with_the_capital_founds_a_company_and_brings_customers_and_staff():
    from engine.rtr_makers import quarter
    from engine.subscriptions import set_plan
    town = quiet_town("resident_founder_rate=1.0", "population_cap=1000")
    a, h = maker(town, cash=22_000_000, risk=1.0)
    people = customers(town, h, 3)
    set_plan(town, people[0], h, 2)
    hand = jobless(town)
    h.business, h.wage = True, 100_000
    on_the_staff(h, hand)
    town.week, h.q_sold, h.q_could = 13, 390, 390
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert a.hustle is None and town.hustles == [] and not h.alive and firm.ceo is a and a.role == "ceo"
    assert all(p.subs["entertainment"] is firm for p in people) and len(firm.subs) == 3 and h.subs == {}
    assert people[0].plan == {"entertainment": 2} and firm.extra == 1 and firm.load() == 4
    assert hand.employer is firm and firm.staff == [hand] and h.staff == []
    assert firm.price == 8_610                                       # the entrant's floor, above the maker's own price
    assert a.cash == 22_000_000 - 15_399_999 and firm.shares_out > 0 and a.shares[firm.id] == firm.shares_out
    assert companies(town) == [(a.id, firm.id, 15_399_999, 3)]
    assert [e["kind"] for e in town.rec.events if e["kind"] in ("layoff", "hustle_stopped")] == []
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "sub_start" and e["firm"] == firm.id] == [
        "company"] * 3
    from engine.household import update_agents
    update_agents(town)
    town.ledger.start_week()
    assert _problems(town) == []                                     # everyone on one seller's and one employer's books


def test_who_does_not_become_a_company():
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0")
    short, _ = maker(town, cash=21_000_000, risk=1.0)                # 70% of it is under $150,000
    owing, ho = maker(town, cash=22_000_000, risk=1.0)
    ho.business, ho.loan, ho.loan_pay = True, 1_000_000, 3_847       # after the loan: 70% of $210,000
    repairer, _ = maker(town, "repair", cash=22_000_000, risk=1.0)   # no firm sells hours
    timid, _ = maker(town, cash=22_000_000, risk=0.0)
    town.week = 13
    for h in town.hustles:
        h.q_sold, h.q_could = 390, 390
    quarter(town)
    assert town.firms == [] and len(town.hustles) == 4 and companies(town) == []


def test_the_loan_is_repaid_when_a_business_becomes_a_company():
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0")
    a, h = maker(town, risk=1.0)
    h.business = True
    town.bank.lend_hustle(h, 1_000_000)
    from engine.ledger import OUTSIDE
    town.ledger.pay(OUTSIDE, a, 22_000_000, "arrival")               # $220,000 of theirs, and the bank's $10,000 in the business
    town.week, h.q_sold, h.q_could = 13, 390, 390
    out_before = town.ledger.week_out.get("loan_principal", 0)
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert h.loan == 0 and h.cash == 0 and town.ledger.week_out["loan_principal"] - out_before == 1_000_000
    assert a.cash == 23_000_000 - 15_399_999 - 1_000_000 and town.bank.writeoffs_total == 0
    assert a.credit_block_until == 0


def test_the_chance_of_becoming_a_company_is_the_wef_founders_chance():
    from engine.rtr_makers import quarter
    town = quiet_town()                                              # 5% a quarter, times their appetite for risk
    a, h = maker(town, cash=22_000_000, risk=0.5)
    town.week, h.q_sold, h.q_could = 13, 390, 390
    town.rng = Dice(0.025)
    quarter(town)
    assert town.firms == [] and a.hustle is h
    h.q_sold, h.q_could = 390, 390
    town.rng = Dice(0.02499)
    quarter(town)
    assert len(town.firms) == 1 and a.hustle is None


def test_with_no_spot_to_be_had_nothing_changes(monkeypatch):
    from engine.rtr_makers import quarter
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "resident_founder_rate=1.0", "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 1, 11, homes=2)                     # a corner of town, far from the middle
    a = tenant(town, home, cash=22_000_000, risk=1.0)
    a.last_wage = town.cfg.outside_wage
    _, h = maker(town, agent=a)
    (c,) = customers(town, h, 1)
    h.business = True
    town.bank.lend_hustle(h, 400_000)
    town.week, h.q_sold, h.q_could = 13, 390, 390
    monkeypatch.setattr("engine.corporate.take_spot", lambda *args, **kwargs: None)
    cash = a.cash
    quarter(town)
    assert a.hustle is h and h.alive and c.subs["entertainment"] is h
    assert (a.cash, h.loan, h.cash, h.reserve) == (cash, 400_000, 400_000, 400_000)
    assert town.firms_for("entertainment") == [] and companies(town) == []
    monkeypatch.undo()
    h.q_sold, h.q_could = 390, 390
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert firm.spot is not None and c.subs["entertainment"] is firm and a.hustle is None    # premises near their home
    from engine.places import dist
    assert dist(firm.spot, home) <= 2


def test_a_maker_of_a_need_is_left_to_the_makers_rule_by_the_wef_founders_rule():
    from engine.corporate import resident_founders
    town = quiet_town("resident_founder_rate=1.0")
    a, h = maker(town, cash=30_000_000, risk=1.0)
    resident_founders(town)
    assert town.firms == [] and a.hustle is h
    b, hb = maker(town, "repair", cash=30_000_000, risk=1.0)         # a repairer is an ordinary resident here
    resident_founders(town)
    assert len(town.firms) == 1 and town.firms[0].founder_id == b.id and b.hustle is hb


# --- found by breaking Part B's rules on purpose (18/11) -----------------------------------------------
def test_the_last_hired_is_the_first_let_go_when_a_business_needs_fewer():
    """As built on 18 November; with the dial of 19 November off (see the test above)."""
    from engine import rtr_makers
    town = quiet_town("longest_serving_first=false")
    a, h = maker(town)
    make_business(town, h)
    first, last = jobless(town), jobless(town)
    on_the_staff(h, first, last)
    customers(town, h, 49)                       # 98 hours wanted, 60 their own: 38 over, one worker's worth
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert h.staff == [first] and last.role is None


def test_a_business_takes_on_nobody_who_could_not_get_to_it():
    from engine import rtr_makers
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    near, far = block(town, landlord, 5, 6, homes=3), block(town, landlord, 12, 12, homes=1)
    a = tenant(town, near, cash=100_000)
    a.last_wage = town.cfg.outside_wage
    _, h = maker(town, agent=a)
    make_business(town, h)
    faraway = tenant(town, far, cash=10_000_000)                     # thirteen blocks off: past a walk
    people = customers(town, h, 30, cash=10_000_000)
    neighbour = tenant(town, near, cash=10_000_000)
    turned_away(town, h, 20)
    hours_for_the_week(town)
    rtr_makers.hire_staff(town)
    assert faraway.id < neighbour.id and faraway.role is None and len(h.staff) == 1
    assert h.staff[0] is not faraway


def test_a_paid_week_wipes_the_missed_ones_and_a_missed_one_is_a_blow():
    town = quiet_town()
    a, h = maker(town)
    h.business = True
    town.bank.lend_hustle(h, 520_000)
    (c,) = customers(town, h, 1)
    town.ledger.pay(h, c, 520_000, "gift")                           # nothing left to pay with
    h.reserve = 0
    before = a.security
    assert not town.bank.service_hustle(h) and h.loan_missed == 1 and a.security < before
    assert [e["data"]["missed"] for e in town.rec.events if e["kind"] == "hustle_loan_missed"] == [1]
    town.ledger.pay(c, a, 10_000, "gift")
    assert town.bank.service_hustle(h) and h.loan_missed == 0


def test_a_company_keeps_its_makers_price_when_that_is_above_the_entrants_floor():
    from engine.rtr_makers import quarter
    town = quiet_town("resident_founder_rate=1.0")
    a = worker(town, cash=22_000_000, wage=200_000, risk=1.0)        # an hour of theirs is worth $50
    _, h = maker(town, agent=a)
    town.week, h.q_sold, h.q_could = 13, 300, 390
    quarter(town)
    (firm,) = town.firms_for("entertainment")
    assert firm.price == h.price == 13_970                           # (2,700 + 2 x 5,000) x 1.1, over the floor


def test_only_those_who_would_have_bought_count_as_waiting():
    from engine.subscriptions import find_provider, subscribe
    town = quiet_town()
    dear, close = shop(town, "entertainment", 9_500), shop(town, "entertainment", 7_100)
    a, h = maker(town)                                               # 6,820 a week, and full
    customers(town, h, 30)
    hours_for_the_week(town)
    keen = worker(town, cash=1_000_000)                              # $1,000 a week and no bills: a luxury is easily had
    saver = jobless(town, cash=10_000_000)                           # no income, but a cushion and half a year of it besides
    cautious = jobless(town, cash=500_000)                           # the cash for a week, no income, a thin cushion
    switcher, content = worker(town, cash=1_000_000), worker(town, cash=1_000_000)
    assert subscribe(town, switcher, dear) and subscribe(town, content, close)   # one would save 28%, the other 4%
    for person in (keen, saver, cautious):
        assert find_provider(town, person, "entertainment", exclude=dear) is close   # the maker is cheapest, and full
    for person, theirs in ((switcher, dear), (content, close)):
        find_provider(town, person, "entertainment", exclude=theirs)
    assert len(h.turned_away) == 5
    hours_for_the_week(town)
    assert h.waiting == 3                                            # keen, saver and the one who would switch


def test_who_would_have_bought_from_a_full_maker():
    from engine.household import basket_cost, buffer_target
    from engine.rtr_makers import would_have_bought
    from engine.subscriptions import cheapest_prices, subscribe
    town = quiet_town()
    dear = shop(town, "entertainment", 7_178)                        # 5% under this is 6,819.10: the maker's 6,820 is not
    a, h = maker(town)
    _, food = maker(town, "food", agent=jobless(town))
    cheapest = cheapest_prices(town)
    hungry = jobless(town, cash=food.price)                          # food is an essential: the cash is enough
    assert would_have_bought(town, hungry, food, cheapest)
    hungry.cash -= 1
    assert not would_have_bought(town, hungry, food, cheapest)
    earner = worker(town, cash=6_820, wage=8_184)                    # $81.84 a week to spare: 1.2 times the price exactly
    assert would_have_bought(town, earner, h, cheapest)
    earner.wage -= 1
    assert not would_have_bought(town, earner, h, cheapest)
    billed = worker(town, cash=20_000, wage=18_184)                  # the same to spare once $100 of food is paid for
    assert subscribe(town, billed, shop(town, "food", 10_000)) and would_have_bought(town, billed, h, cheapest)
    billed.wage -= 1
    assert not would_have_bought(town, billed, h, cheapest)
    saver = jobless(town)
    saver.cash = buffer_target(town.cfg, saver, basket_cost(town, saver, cheapest)) + 26 * 6_820     # a cushion and half a year of it
    assert would_have_bought(town, saver, h, cheapest)
    saver.cash -= 1
    assert not would_have_bought(town, saver, h, cheapest)
    theirs = worker(town, cash=1_000_000)
    assert subscribe(town, theirs, h) and not would_have_bought(town, theirs, h, cheapest)   # a customer already
    other = worker(town, cash=1_000_000)
    assert subscribe(town, other, dear) and not would_have_bought(town, other, h, cheapest)  # not clearly cheaper
    dear.price += 1
    assert would_have_bought(town, other, h, cheapest)
    other.cash = 6_819
    assert not would_have_bought(town, other, h, cheapest)


def test_a_small_business_pays_its_staff_out_of_the_weeks_takings():
    town = quiet_town()
    a, h = maker(town)                                               # not a cent on payday
    make_business(town, h)
    hand = jobless(town)
    on_the_staff(h, hand)
    customers(town, h, 50, cash=10_000_000)                          # fifty paying customers this week
    town.step()
    assert h.staff == [hand] and hand.income_week == 100_000 and hand.cash == 100_000
    assert [e for e in town.rec.events if e["kind"] == "layoff"] == []
    assert a.cash == 50 * 8_470 - 50 * 2_700 - 100_000               # takings, less the goods, less the wage


def test_a_business_has_a_till_for_the_week_goods_then_wages_then_what_is_left_to_its_owner():
    from engine import rtr_makers, rtr_owning
    from engine.household import pay_bills
    from engine.subscriptions import subscribe
    town = quiet_town()
    a, h = maker(town, cash=30_000)
    make_business(town, h)
    hand = jobless(town)
    on_the_staff(h, hand)
    landlord = town.add_firm("housing")
    town.new_unit(landlord)
    assert subscribe(town, a, landlord)                              # the owner's own rent: $330, more than they have
    customers(town, h, 20, cash=10_000_000)                          # $1,694 of takings; $540 of goods; a $1,000 wage
    hours_for_the_week(town)
    rtr_makers.working_week(town)
    pay_bills(town)
    assert h.cash == 20 * 8_470 and a.cash == 30_000                 # the takings are in the till, not in their pocket
    assert a.arrears["housing"] == 1                                 # so the owner's rent went unpaid, not the worker
    rtr_owning.after_bills(town)
    rtr_makers.after_bills(town)
    assert hand.cash == 100_000 and h.staff == [hand]                # the worker is paid out of the takings
    assert h.cash == 0 and a.cash == 30_000 + 20 * 8_470 - 20 * 2_700 - 100_000      # and the owner draws the rest
    assert town.ledger.week_internal["drawings"] == 20 * 8_470 - 20 * 2_700 - 100_000
    assert [e for e in town.rec.events if e["kind"] == "layoff"] == []


def test_an_owner_tops_up_the_till_for_wages_when_the_takings_fall_short_and_no_more_than_that():
    from engine.rtr_makers import pay_staff
    town = quiet_town()
    a, h = maker(town, cash=500_000)
    h.business, h.wage = True, 100_000
    on_the_staff(h, jobless(town), jobless(town))
    town.ledger.pay(a, h, 120_000, "test")                           # $1,200 in the till, $2,000 of wages due
    pay_staff(town)
    assert len(h.staff) == 2 and h.cash == 0 and a.cash == 500_000 - 200_000
    assert town.ledger.week_internal["maker_capital"] == 80_000
    first, second = jobless(town), jobless(town)
    b, hb = maker(town, cash=500_000)
    hb.business, hb.wage = True, 100_000
    on_the_staff(hb, first, second)
    town.bank.lend_hustle(hb, 150_000)                               # $1,500 of the bank's in the business
    town.ledger.pay(b, hb, 20_000, "test")                           # and $200 of takings in the till
    pay_staff(town)
    assert (hb.cash, hb.reserve, b.cash) == (0, 0, 500_000 - 20_000 - 30_000)    # the bank's money before their own


def test_money_in_a_till_is_money_in_town_and_a_side_hustle_that_stops_hands_it_to_its_owner():
    from engine import rtr_makers
    from engine.household import pay_bills
    from engine.rtr_makers import stop
    town = quiet_town()
    a, h = maker(town)
    customers(town, h, 3)
    hours_for_the_week(town)
    rtr_makers.working_week(town)
    money = town.money_in_town()
    pay_bills(town)
    assert h.cash == 20_460 and town.money_in_town() == money        # it moved from pockets to the till, no more
    stop(town, h, "test")
    assert h.cash == 0 and a.cash == 20_460 and town.money_in_town() == money


# --- the fresh review of stage 2 (18/11) -----------------------------------------------------------------
def test_a_base_need_with_no_tools_of_its_own_takes_the_tools_of_something_thought_up():
    from engine.config import NeedSpec
    from engine.rtr_makers import best_trade, tools_cost
    town = quiet_town()
    spec = NeedSpec(name="clothing", kind="flow", weight=0.05, essential=False, priority=4, service_labour=0.05,
                    goods_per_sub=1.0, make_labour=0.03, import_price=2_700, export_price=2_000, export_quota=0.0,
                    initial_price=9_500, trips_per_week=1.0)
    town.needs["clothing"] = spec                # a settings file may add a need of its own
    assert tools_cost(town.cfg, "clothing", spec) == 50_000
    assert best_trade(town, jobless(town, cash=1_000_000)) is not None       # and nothing breaks when someone looks


@pytest.mark.fifth_in_cash
def test_someone_building_a_home_uses_their_own_hours_first_and_a_builder_with_what_money_is_left():
    from engine import rtr_owning
    town, a = building_tenant()
    b, h = builder_next_door(town, a)                                # cheap: 1,375 an hour
    hours_for_the_week(town)
    bills = rtr_owning._bills(town, a)
    a.spare_hours, a.cash = 20.0, 4 * bills + 30_000                 # twenty hours of their own and $300 to spare
    rtr_owning.work(town, a)
    # their own twenty hours take $900 of materials, $180 of it theirs; what is left of the $120 once the new
    # loan's payments are in their four weeks of bills buys a little over four builder's hours at $27.25 each
    assert a.spare_hours == 0.0 and 4.1 < h.sold < 12_000 / 2_725
    assert a.build.hours_left == pytest.approx(1_200 - 20 - h.sold)
    assert a.cash == pytest.approx(4 * rtr_owning._bills(town, a), abs=500)      # to within the last loan draw's payments


def test_what_the_bank_lent_a_business_is_no_cushion_for_its_owner():
    from engine.household import update_agents
    town = quiet_town()
    (a, h), (b, hb) = maker(town), maker(town)
    for x in (h, hb):
        x.business, x.profit_week = True, 60_000
    town.bank.lend_hustle(h, 1_560_000)
    a.security = b.security = 0.3
    for _ in range(30):
        update_agents(town)
    assert a.security == b.security and a.cash == b.cash == 0        # the same $600 a week: the same security
    assert town.money_in_town() == 1_560_000                         # and the money is in town, in the business


def test_a_business_pays_the_bank_out_of_what_the_bank_lent_it_before_its_owners_pocket():
    town = quiet_town()
    a, h = maker(town, cash=10_000)
    h.business = True
    town.bank.lend_hustle(h, 520_000)
    assert town.bank.service_hustle(h)                               # $6 of interest and $20 off the loan
    assert (h.cash, h.reserve, a.cash, h.loan) == (517_400, 517_400, 10_000, 518_000)
    town.ledger.pay(h, a, 516_400, "test")                           # only $10 left in the business
    h.reserve = h.cash
    assert town.bank.service_hustle(h)
    assert h.cash == 0 and h.reserve == 0 and a.cash == 10_000 + 516_400 - (round(518_000 * 0.06 / 52) + 2_000 - 1_000)


def test_someone_out_of_work_has_the_strugglings_chance_whatever_else_they_live_on():
    from engine.rtr_makers import consider_hustles
    town = rtr_town("hustle_rate_struggling=1.0", "hustle_rate=0.0")
    shop(town, "entertainment", 9_500)
    a = jobless(town, cash=1_000_000)
    a.div_quarters = [2_000_000] * 4                                 # dividends well over their basket
    assert a.income_estimate() > 88_000
    consider_hustles(town)
    assert a.hustle is not None                                      # the design: "out of work, or their income does not cover"


def test_where_food_can_be_had_counts_a_food_maker_with_room():
    from engine.places import essential_shops, far_from_food, needs_ride
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    here, there = block(town, landlord, 1, 1, homes=3), block(town, landlord, 12, 12, homes=2)
    firm = premises(town, "food", 12, 11)                            # the only food firm is across town
    a, c = tenant(town, here, cash=0), tenant(town, here)
    a.last_wage = town.cfg.outside_wage
    assert far_from_food(town, here) and needs_ride(town, c)
    _, h = maker(town, "food", agent=a)
    hours_for_the_week(town)
    assert not far_from_food(town, here) and not needs_ride(town, c)     # a food maker with room lives on their block
    assert here in essential_shops(town)[0]
    h.capacity = 0                                                   # full: no food to be had from them
    assert far_from_food(town, here) and needs_ride(town, c)
    h.capacity = 8
    firm.alive = False                                               # no food firm at all: the maker is all there is
    assert not far_from_food(town, here) and far_from_food(town, there)
    d = tenant(town, there)
    assert needs_ride(town, d)


def test_from_a_real_queue_to_a_loan_to_staff_to_customers_served():
    town = quiet_town()
    a, h = maker(town)                                               # out of work, no money, full from the first week
    customers(town, h, 30, cash=10_000_000)
    wanting = [jobless(town, cash=10_000_000) for _ in range(40)]    # forty more who want it and can well afford it
    for _ in range(13):
        town.step()
    assert h.business and h.price == 8_470 and h.loan > 0 and h.cash == h.reserve > 0 and h.staff == []
    for _ in range(3):
        town.step()
    assert len(h.staff) == 2 and h.load() == 70 and h.unserved == {} and h.capacity == 70
    assert all(w.subs.get("entertainment") is h for w in wanting)
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "layoff"] == []
    assert h.w_revenue == 70 * 8_470 and h.w_wages == 2 * h.wage
    assert h.cash == h.reserve > 0 and a.cash > 0        # the owner has drawn the takings; the bank's money is still in the business


def test_a_missed_loan_payment_takes_the_interest_and_leaves_nothing_of_the_owners_in_the_till():
    town = quiet_town()
    a, h = maker(town, cash=1_000)                                   # $10: enough for the $6 of interest, not the $26 due
    h.business = True
    town.bank.lend_hustle(h, 520_000)
    (c,) = customers(town, h, 1)
    town.ledger.pay(h, c, 520_000, "gift")
    h.reserve = 0
    assert not town.bank.service_hustle(h)
    assert (h.cash, h.reserve, a.cash, h.loan, h.loan_missed) == (0, 0, 400, 520_000, 1)


def test_a_tie_between_trades_goes_to_the_one_thought_of_first():
    from engine.corporate import invent_need
    from engine.rtr_makers import best_trade
    town = quiet_town()
    shop(town, "entertainment", 5_000)
    shop(town, "food", 20_000)
    first, second = invent_need(town), invent_need(town)             # nobody sells either: the best opening there is
    assert best_trade(town, jobless(town, cash=1_000_000))[0] == first.name


def test_someone_who_has_the_hours_within_a_quarter_does_not_pay_a_dearer_set_builder_for_the_rest():
    from engine import rtr_owning
    from test_rtr import _renter_of_a_set
    town, a, firm = _renter_of_a_set(cash=10_000_000)
    assert rtr_owning._start_set(town, a)
    m, h = maker(town, "set_building", agent=worker(town))           # 2,750 an hour: dearer than their own
    hours_for_the_week(town)
    a.spare_hours, cash = 2.0, a.cash                                # twenty hours is ten weeks of theirs: within a quarter
    rtr_owning.work(town, a)
    assert h.sold == 0.0 and a.set_hours_left == pytest.approx(18.0) and a.cash == cash


def test_a_food_maker_with_no_home_can_be_reached_from_anywhere():
    from engine.places import far_from_food, needs_ride, sold_at
    from test_places import block, premises, tenant
    town = map_rtr_town(*NOBODY_STARTS, "switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    here = block(town, landlord, 1, 1, homes=2)
    premises(town, "food", 12, 11)
    c = tenant(town, here)
    assert far_from_food(town, here) and needs_ride(town, c)
    _, h = maker(town, "food", agent=jobless(town))                  # no home: they sell where they are found
    hours_for_the_week(town)
    assert h.spot is None and sold_at(town, "food") is None
    assert not far_from_food(town, here) and not needs_ride(town, c)
