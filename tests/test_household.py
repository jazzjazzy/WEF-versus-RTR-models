import pytest

from engine.corporate import invent_need
from engine.household import (pay_bills, plan_bills, review_subscriptions, update_agents,
                                valuation, wellbeing)
from engine.subscriptions import subscribe
from conftest import empty_town

BASE = ("food", "housing", "appliances", "entertainment")


@pytest.fixture
def town():
    """A town where nobody reviews holdings or invests by chance, so each test sees only its own orders."""
    return empty_town("sell_review_prob=0.0", "invest_prob=0.0")


def base_firms(town, homes=5, sets=5):
    firms = {}
    for need in BASE:
        firms[need] = town.add_firm(need)
        firms[need].founded = -200
    for _ in range(homes):
        town.new_unit(firms["housing"])
    for _ in range(sets):
        town.new_unit(firms["appliances"])
    return firms


def resident(town, firms, cash=0, wage=100_000, needs=BASE, **fixed):
    a = town.add_agent(cash=cash, **fixed)
    for need in needs:
        assert subscribe(town, a, firms[need])
    if wage:
        a.role, a.wage, a.employer = "staff", wage, firms["food"]
        firms["food"].staff.append(a)
    return a


CALM = dict(horizon=200.0, security=0.7)        # effective horizon 146 weeks
STRESSED = dict(horizon=20.0, security=0.3)     # effective horizon about 7 weeks


def give_shares(town, agent, firm, n=100, price=1_000):
    town.issue_shares(firm, agent, n)
    firm.share_price = price


def test_bills_paid_in_order_food_housing_loan_appliances_entertainment(town):
    firms = base_firms(town)
    a = resident(town, firms, **CALM)
    town.bank.lend_person(a, 520_000)             # $100 a week principal, $12 interest
    sink = town.add_agent()
    town.ledger.pay(a, sink, a.cash - 84_200, "subscription")   # exactly food, rent and the loan
    pay_bills(town)
    assert a.cash == 0
    assert a.met == {"food": True, "housing": True, "appliances": True, "entertainment": False}
    assert a.loan == 510_000
    assert (a.arrears["appliances"], a.arrears["entertainment"]) == (1, 1)
    assert firms["food"].w_revenue == 40_000 and firms["housing"].w_revenue == 33_000
    assert [e["kind"] for e in town.rec.events].count("missed_payment") == 2


def test_calm_agent_cuts_entertainment_and_keeps_shares(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=88_000, wage=60_000, **CALM)
    give_shares(town, a, firms["food"])
    plan_bills(town)
    assert set(a.subs) == {"food", "housing"}     # the two it cannot go without
    assert town.broker.asks == {}
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert [e["data"]["reason"] for e in ends] == ["budget", "budget"]
    assert [e["data"]["need"] for e in ends] == ["entertainment", "appliances"]


def test_calm_agent_with_savings_keeps_everything(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=10_000_000, wage=0, **CALM)   # out of work, a deep cushion
    plan_bills(town)
    assert set(a.subs) == set(BASE)


def test_stressed_agent_sells_shares_at_market(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=50_000, wage=60_000, **STRESSED)
    give_shares(town, a, firms["food"])
    plan_bills(town)
    assert set(a.subs) == set(BASE)               # cuts nothing
    order = town.broker.asks[firms["food"].id][0]
    assert (order.limit, order.qty, order.reason) == (0, 48, "distress")   # $380 short, plus a quarter


def test_calm_agent_sells_only_for_food_and_housing(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=30_000, wage=60_000, **CALM)
    give_shares(town, a, firms["food"])
    plan_bills(town)
    assert set(a.subs) == {"food", "housing"}
    order = town.broker.asks[firms["food"].id][0]
    assert (order.limit, order.qty) == (0, 54)    # $430 short of food and rent, plus a quarter


def test_stressed_agent_borrows_for_entertainment_and_calm_one_does_not(town):
    firms = base_firms(town)
    calm = resident(town, firms, cash=78_500, **CALM)          # everything but entertainment
    stressed = resident(town, firms, cash=78_500, **STRESSED)
    pay_bills(town)
    assert calm.loan == 0 and calm.met["entertainment"] is False
    assert stressed.loan == 9_500 and stressed.met["entertainment"] is True


def test_four_missed_rents_evicts_but_agent_stays_in_town(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=0, wage=0, needs=("housing",), loss_aversion=2.0, **CALM)
    home = a.unit["housing"]
    housed = []
    for _ in range(4):
        pay_bills(town)
        housed.append(a.met["housing"])
    assert housed == [True, True, True, False]
    assert "housing" not in a.subs and home.occupant is None
    assert a in town.agents
    kinds = [e["kind"] for e in town.rec.events]
    assert kinds.count("missed_payment") == 4
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert ends[0]["data"]["reason"] == "evicted"
    assert a.security < 0.7 - 0.2                 # four missed payments and an eviction


def test_customer_the_firm_could_not_serve_is_not_charged(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=1_000_000)
    firms["food"].unserved = {a.id: True}
    pay_bills(town)
    assert a.met["food"] is False
    assert firms["food"].w_revenue == 0 and a.arrears["food"] == 0


def test_low_security_shortens_horizon(town):
    a = town.add_agent(horizon=100.0)
    a.security = 1.0
    assert a.h_eff(town.cfg) == pytest.approx(100.0)
    a.security = 0.0
    assert a.h_eff(town.cfg) == pytest.approx(10.0)


def dividend_firm(town):
    firm = town.add_firm("food")
    firm.founded = -200
    owner = town.add_agent(cash=1_000_000)
    town.ledger.pay(owner, firm, 1_000_000, "founding")      # book value $10 a share
    town.issue_shares(firm, owner, 1_000)
    firm.dps_hist = [130, 130, 130, 130]                     # $5.20 a share a year: 10 cents a week
    return firm, owner


def test_longer_horizon_values_a_share_more(town):
    firm, _ = dividend_firm(town)
    patient = town.add_agent(horizon=400.0, security=1.0)
    hasty = town.add_agent(horizon=20.0, security=1.0)
    assert valuation(town, patient, firm) == 10 * 400 + 500
    assert valuation(town, hasty, firm) == 10 * 20 + 500


def test_unhappy_shareholder_offers_a_tenth():
    town = empty_town("sell_review_prob=1.0")
    firm, owner = dividend_firm(town)
    firm.eps_hist = [10.0] * 5                               # no growth in a year
    holder = town.add_agent(horizon=400.0, security=1.0, growth_expect=0.10)
    town.move_shares(firm, owner, holder, 200)
    firm.share_price = 4_500
    plan_bills(town)
    asks = [o for o in town.broker.asks[firm.id] if o.agent is holder]
    assert len(asks) == 1
    assert (asks[0].qty, asks[0].limit, asks[0].reason) == (20, 3_600, "unhappy")   # worth 80% to them


def test_content_shareholder_holds():
    town = empty_town("sell_review_prob=1.0")
    firm, owner = dividend_firm(town)
    firm.eps_hist = [10.0, 10.0, 10.0, 10.0, 11.0]           # 10% growth, as expected
    holder = town.add_agent(horizon=400.0, security=1.0, growth_expect=0.10)
    town.move_shares(firm, owner, holder, 200)
    firm.share_price = 4_500
    plan_bills(town)
    assert not [o for o in town.broker.asks.get(firm.id, []) if o.agent is holder]


def test_spare_cash_bids_for_shares_but_never_far_above_the_last_price():
    town = empty_town("invest_prob=1.0")
    firm, owner = dividend_firm(town)
    firm.share_price = 1_000
    saver = town.add_agent(cash=10_000_000, horizon=400.0, security=1.0)
    plan_bills(town)
    bids = [o for o in town.broker.bids[firm.id] if o.agent is saver]
    # a year of the $880 basket is the cushion; 30% of the rest is on offer at no more than $12.50
    assert len(bids) == 1 and bids[0].limit == 1_250
    assert bids[0].qty == int((10_000_000 - 52 * 88_000) * 0.30) // 1_250


def test_the_bank_cannot_force_a_sale_by_default(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=500_000, **CALM)
    give_shares(town, a, firms["food"])
    town.bank.lend_person(a, 400_000)
    a.role, a.wage, a.employer = None, 0, None
    town.bank.call(a)
    plan_bills(town)
    assert town.broker.asks == {}


def test_forced_sale_dial_makes_a_called_loan_sell_shares():
    town = empty_town("bank_can_force_share_sale=true")
    firms = base_firms(town)
    a = resident(town, firms, cash=500_000, **CALM)
    give_shares(town, a, firms["food"])
    town.bank.lend_person(a, 400_000)
    a.role, a.wage, a.employer = None, 0, None
    town.bank.call(a)
    plan_bills(town)
    assert town.broker.asks[firms["food"].id][0].reason == "forced"


def test_security_falls_fast_and_recovers_slowly(town):
    firms = base_firms(town)
    down = town.add_agent(loss_aversion=2.0)                 # no job, no money
    up = resident(town, firms, cash=50_000_000, wage=200_000)
    up.security = 0.2
    update_agents(town)
    assert down.security == pytest.approx(0.7 - 0.12 * 0.7)  # 12% of the way down in a week
    assert up.security == pytest.approx(0.2 + 0.04 * 0.8)    # 4% of the way back up


def test_wellbeing_is_half_security_plus_provision_and_condition(town):
    assert wellbeing(town.cfg, security=0.6, provision=1.0, condition=0.5) == pytest.approx(0.7)
    firms = base_firms(town)
    a = resident(town, firms, cash=50_000_000, wage=200_000)
    for need in BASE:
        a.met[need] = True
    a.unit["housing"].cond, a.unit["appliances"].cond = 0.6, 0.4
    update_agents(town)
    assert a.provision == pytest.approx(1.0) and a.condition == pytest.approx(0.5)
    assert a.wellbeing == pytest.approx(0.5 * a.security + 0.3 * 1.0 + 0.2 * 0.5)
    assert a.happy is True


def test_going_without_shows_in_provision_and_happiness(town):
    firms = base_firms(town)
    a = town.add_agent()                                     # no job, no home, nothing met
    update_agents(town)
    assert a.provision == 0.0 and a.condition == 0.0
    assert a.happy is False and a.destitute is True


def test_adopts_an_invented_need_only_with_spare_income_and_the_taste_for_it(town):
    firms = base_firms(town)
    spec = invent_need(town)
    spec.appeal = 1.0
    extra = town.add_firm(spec.name)
    comfortable = resident(town, firms, cash=500_000, wage=200_000)
    stretched = resident(town, firms, cash=100_000, wage=90_000)
    review_subscriptions(town)
    assert spec.name in comfortable.subs and spec.name in comfortable.had
    assert spec.name not in stretched.subs
    spec.appeal = 0.0                                        # now it suits nobody
    other = resident(town, firms, cash=500_000, wage=200_000)
    review_subscriptions(town)
    assert spec.name not in other.subs


def test_switches_to_a_provider_more_than_five_percent_cheaper():
    town = empty_town("switch_prob=1.0")
    firms = base_firms(town)
    a = resident(town, firms, cash=500_000)
    rival = town.add_firm("food")
    rival.price = 39_000                                     # 2.5% cheaper: not worth it
    review_subscriptions(town)
    assert a.subs["food"] is firms["food"]
    rival.price = 36_000                                     # 10% cheaper
    review_subscriptions(town)
    assert a.subs["food"] is rival
    assert a.id not in firms["food"].subs


def test_homeless_agent_rents_again_when_able(town):
    firms = base_firms(town)
    able = town.add_agent(cash=80_000)
    short = town.add_agent(cash=40_000)
    review_subscriptions(town)
    assert able.subs["housing"] is firms["housing"] and able.subs["food"] is firms["food"]
    assert set(short.subs) == {"food"}                       # food comes first; nothing left for rent


def test_agent_with_a_loan_does_not_cancel_and_rejoin_every_week(town):
    firms = base_firms(town)
    a = resident(town, firms, cash=200_000, wage=95_000, **CALM)   # covers the $880 basket, not the loan too
    town.bank.lend_person(a, 520_000)                              # $112 a week to the bank
    sink = town.add_agent()
    town.ledger.pay(a, sink, 520_000, "subscription")
    plan_bills(town)
    assert "entertainment" not in a.subs                           # income will not cover it with the loan
    review_subscriptions(town)
    assert "entertainment" not in a.subs                           # and it stays dropped
    starts = [e for e in town.rec.events
              if e["kind"] == "sub_start" and e["agent"] == a.id and e["data"]["reason"] == "signup"]
    assert starts == []


def test_cash_rich_agent_does_not_cancel_and_rejoin_luxuries(town):
    firms = base_firms(town)
    extras = []
    for _ in range(3):
        spec = invent_need(town)
        spec.appeal = 1.0
        firm = town.add_firm(spec.name)
        firm.price = 30_000
        extras.append(firm)
    a = resident(town, firms, cash=4_500_000, wage=100_000, **CALM)   # a cushion of a year's basics
    for firm in extras:
        assert subscribe(town, a, firm)
    before = set(a.subs)
    for _ in range(3):
        plan_bills(town)
        review_subscriptions(town)
    assert set(a.subs) == before                                   # spending above income, from savings
    ends = [e for e in town.rec.events if e["kind"] == "sub_end" and e["agent"] == a.id]
    assert ends == []


# --- lapsed luxuries ---------------------------------------------------------------------------
def luxury(town, sold=True):
    spec = invent_need(town)
    spec.appeal = 1.0
    firm = town.add_firm(spec.name) if sold else None
    return spec, firm


def fully_supplied(town, firms):
    a = resident(town, firms, cash=50_000_000, wage=200_000)
    for need in BASE:
        a.met[need] = True
    return a


def test_lapsed_luxury_counts_against_needs_met_while_it_is_still_sold(town):
    firms = base_firms(town)
    spec, firm = luxury(town)
    a = fully_supplied(town, firms)
    a.had[spec.name] = town.week                       # they had it once and dropped it
    update_agents(town)
    assert a.provision == pytest.approx(1.0 / 1.08)    # four base needs met, one luxury missed


def test_lapsed_luxury_nobody_sells_does_not_count(town):
    firms = base_firms(town)
    spec, _ = luxury(town, sold=False)                 # its only firm has closed
    a = fully_supplied(town, firms)
    a.had[spec.name] = town.week
    update_agents(town)
    assert a.provision == pytest.approx(1.0)


def test_habit_fades_when_the_dial_is_set():
    town = empty_town("habit_weeks=52", "sell_review_prob=0.0", "invest_prob=0.0")
    firms = base_firms(town)
    spec, firm = luxury(town)
    a = fully_supplied(town, firms)
    a.had[spec.name] = 0
    town.week = 52
    update_agents(town)
    assert a.provision == pytest.approx(1.0 / 1.08)    # still inside the year
    for need in BASE:
        a.met[need] = True
    town.week = 53
    update_agents(town)
    assert a.provision == pytest.approx(1.0)           # a year on, they no longer miss it


def test_a_luxury_they_hold_keeps_the_habit_fresh():
    town = empty_town("habit_weeks=52", "sell_review_prob=0.0", "invest_prob=0.0")
    firms = base_firms(town)
    spec, firm = luxury(town)
    a = fully_supplied(town, firms)
    assert subscribe(town, a, firm)
    town.week = 200
    a.met[spec.name] = True
    update_agents(town)
    assert a.had[spec.name] == 200
    assert a.provision == pytest.approx(1.0)
