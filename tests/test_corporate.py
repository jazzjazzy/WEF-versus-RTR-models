import pytest

from engine.corporate import (choose_venture, fail_firm, found_firm, invent_need,
                                maybe_arrive_founder, pay_dividends, wind_up)
from engine.labour import hire
from engine.production import unit_cost
from engine.subscriptions import subscribe
from conftest import empty_town


def staffed_firm(town, need, founder_cash, capital, staff=0, customers=0, units=0):
    founder = town.add_agent(cash=founder_cash)
    firm = found_firm(town, founder, capital, town.needs[need], in_kind_units=units)
    people = [town.add_agent() for _ in range(staff)]
    for a in people:
        hire(town, firm, a)
    buyers = [town.add_agent() for _ in range(customers)]
    for a in buyers:
        assert subscribe(town, a, firm)
    return founder, firm, people, buyers


def test_founding_moves_capital_and_issues_shares_at_ten_dollars(town):
    founder = town.add_agent(cash=10_000_000)
    firm = found_firm(town, founder, 9_000_000, town.needs["food"])
    assert (firm.cash, founder.cash) == (9_000_000, 1_000_000)
    assert firm.shares_out == 9_000 and founder.shares[firm.id] == 9_000
    assert firm.share_price == 1_000
    assert firm.ceo is founder and founder.role == "ceo"
    assert [e["kind"] for e in town.rec.events].count("firm_founded") == 1


def test_starting_units_are_paid_for_in_shares(town):
    founder = town.add_agent(cash=10_000_000)
    firm = found_firm(town, founder, 10_000_000, town.needs["housing"], in_kind_units=10)
    assert len(firm.units) == 10
    assert firm.shares_out == (10_000_000 + 10 * 7_000_000) // 1_000


def test_unit_cost_of_food_at_the_outside_wage(town):
    # 0.18 of a worker plus 10% overhead, and one unit of goods made in town for $140 plus overhead
    assert unit_cost(town.cfg, town.needs["food"], 100_000) == 35_200


def test_dividends_split_by_holding_and_leave_reserve(town):
    founder, firm, _, _ = staffed_firm(town, "food", 2_000_000, 1_000_000)
    other = town.add_agent()
    town.move_shares(firm, founder, other, 250)       # 750 and 250 of 1,000 shares
    firm.last_opex = 50_000                           # reserve is eight weeks: $4,000
    firm.retained = 10_000_000
    paid = pay_dividends(town, firm)
    assert paid == 600_000 and firm.cash == 400_000
    assert founder.cash == 1_000_000 + 450_000 and other.cash == 150_000
    assert founder.div_this_quarter == 450_000


def test_dividends_never_exceed_undistributed_profit(town):
    founder, firm, _, _ = staffed_firm(town, "food", 2_000_000, 1_000_000)
    firm.last_opex = 50_000
    firm.retained = 100_000
    assert pay_dividends(town, firm) == 100_000
    assert firm.retained == 0
    firm.retained = -5_000                            # a firm in the red pays nothing
    assert pay_dividends(town, firm) == 0


def test_failed_firm_with_customers_is_sold_and_staff_keep_jobs(town):
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=3, customers=5)
    rich = town.add_agent(cash=50_000_000)
    before = town.money_in_town()
    fail_firm(town, firm, "payroll")
    assert firm.alive
    assert firm.holders == {rich.id: firm.shares_out}
    assert founder.shares == {} and founder.role is None
    assert [a.employer for a in staff] == [firm] * 3
    assert firm.ceo is rich and len(firm.subs) == 5
    assert firm.cash == 500_000 + 8 * firm.payroll(town.cfg) - 8 * firm.ceo_pay(town.cfg)
    assert town.money_in_town() == before
    kinds = [e["kind"] for e in town.rec.events]
    assert kinds.count("firm_failed") == 1 and kinds.count("takeover") == 1
    assert kinds.count("shares_cancelled") == 1


def test_rival_absorbs_a_failed_firm_in_the_same_need(town):
    _, rival, _, _ = staffed_firm(town, "food", 5_000_000, 4_000_000)
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=2, customers=4)
    before = town.money_in_town()
    fail_firm(town, firm, "payroll")
    assert not firm.alive and firm.cash == 0
    assert [a.employer for a in staff] == [rival] * 2
    assert all(a.subs["food"] is rival for a in buyers) and len(rival.subs) == 4
    assert founder.role is None and founder.shares == {}
    assert founder.cash == 500_000 + 500_000          # the firm's leftover cash went back to its shareholder
    assert town.money_in_town() == before


def test_failed_firm_without_customers_is_wound_up(town):
    founder, firm, staff, _ = staffed_firm(town, "food", 1_000_000, 500_000, staff=2)
    fail_firm(town, firm, "payroll")
    assert not firm.alive and firm.cash == 0 and firm.holders == {}
    assert all(a.role is None for a in staff)
    assert [e["kind"] for e in town.rec.events].count("layoff") == 3      # two staff and the CEO


def test_wind_up_pays_the_bank_first_then_shareholders(town):
    founder, firm, _, _ = staffed_firm(town, "housing", 2_000_000, 1_500_000, units=10)
    town.bank.lend_firm(firm, 1_000_000)
    assert firm.cash == 2_500_000
    wind_up(town, firm, "idle")
    assert town.ledger.week_out["loan_recovery"] == 1_000_000
    assert founder.cash == 500_000 + 1_500_000
    assert firm.cash == 0 and firm.loan == 0 and not firm.alive


def test_sale_keeps_the_debt_on_the_units(town):
    founder, firm, _, tenants = staffed_firm(town, "housing", 2_000_000, 1_000_000, customers=10, units=10)
    town.bank.lend_firm(firm, 42_000_000)             # the full 60% of $700,000
    firm.loan += 8_000_000                            # unpaid interest piled on top
    rich = town.add_agent(cash=100_000_000)
    fail_firm(town, firm, "loan")
    assert firm.alive and firm.ceo is rich
    assert town.bank.writeoffs_total == 8_000_000     # written down to what the homes can secure
    assert town.ledger.week_out["loan_recovery"] == 35_000_000   # half the homes' value, paid to the bank
    assert firm.loan == 7_000_000
    assert town.bank.firm_credit(firm) == 35_000_000  # no more room than the buyer paid in
    assert all(a.subs["housing"] is firm for a in tenants)


def test_firm_just_sold_cannot_fail_again_for_a_quarter(town):
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=3, customers=5)
    town.add_agent(cash=50_000_000)
    fail_firm(town, firm, "payroll")
    owner = firm.ceo
    fail_firm(town, firm, "payroll")                  # ignored: it was sold this week
    assert firm.alive and firm.ceo is owner
    assert [e["kind"] for e in town.rec.events].count("firm_failed") == 1


def test_invented_need_is_discretionary_and_not_transport(town):
    specs = [invent_need(town) for _ in range(25)]
    assert all(s.invented and s.kind == "flow" and not s.essential for s in specs)
    assert all(s.export_quota == 0 for s in specs)
    assert len({s.name for s in specs}) == 25
    assert "transport" not in town.needs              # transport waits for the map


def two_markets(town, food_margin, fun_margin):
    _, food, _, _ = staffed_firm(town, "food", 20_000_000, 10_000_000)
    _, fun, _, _ = staffed_firm(town, "entertainment", 20_000_000, 10_000_000)
    food.profit_hist, food.rev_hist = [food_margin, food_margin], [1_000, 1_000]
    fun.profit_hist, fun.rev_hist = [fun_margin, fun_margin], [1_000, 1_000]
    return food, fun


def test_entrant_undercuts_but_not_below_cost():
    town = empty_town("invent_prob=0.0")
    two_markets(town, food_margin=120, fun_margin=50)                 # 12% and 5%
    spec, price = choose_venture(town, 20_000_000)
    assert spec.name == "food"
    assert price == 36_960                            # 8% under $400 would be below cost plus 5%


def test_no_entry_into_a_thin_market():
    town = empty_town("invent_prob=0.0")
    two_markets(town, food_margin=50, fun_margin=50)
    assert choose_venture(town, 20_000_000) is None


def test_a_need_nobody_serves_is_the_first_choice():
    town = empty_town("invent_prob=0.0")
    _, food, _, _ = staffed_firm(town, "food", 20_000_000, 10_000_000)
    food.profit_hist, food.rev_hist = [120, 120], [1_000, 1_000]
    spec, price = choose_venture(town, 20_000_000)    # too little capital to be a landlord
    assert spec.name == "entertainment"
    assert price == round(8_200 * 1.3)


def test_founder_cannot_arrive_without_a_free_home():
    town = empty_town("founder_arrival_rate=1.0", "invent_prob=1.0")
    assert maybe_arrive_founder(town) is None
    assert town.population == 0
    assert [e["kind"] for e in town.rec.events].count("arrival_blocked") == 1


def test_founder_arrival_starts_a_firm_and_rents_a_home():
    town = empty_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0")
    landlord, housing, _, _ = staffed_firm(town, "housing", 1_000_000, 500_000, units=5)
    firm = maybe_arrive_founder(town)
    assert firm is not None and firm.spec.invented
    founder = town.agent(firm.founder_id)
    assert founder.origin == "founder" and founder.subs["housing"] is housing
    assert firm.ceo is founder


def test_arriving_founder_settles_in_before_their_firm_opens():
    town = empty_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0")
    staffed_firm(town, "housing", 1_000_000, 500_000, units=5)
    firm = maybe_arrive_founder(town)
    founder = town.agent(firm.founder_id)
    kinds = [e["kind"] for e in town.rec.events if e["agent"] == founder.id]
    assert kinds.index("sub_start") < kinds.index("arrival") < kinds.index("firm_founded")
    assert firm.need not in founder.subs                 # they took nothing from a firm not yet open


def test_no_founder_arrives_once_the_town_is_full():
    town = empty_town("founder_arrival_rate=1.0", "invent_prob=1.0", "population_cap=4")
    staffed_firm(town, "housing", 1_000_000, 500_000, units=5)
    for _ in range(3):
        town.add_agent()                                 # four people: the town is at its cap
    assert maybe_arrive_founder(town) is None
    assert town.population == 4


def test_service_firm_failing_again_within_a_year_is_wound_up(town):
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=3, customers=5)
    rich = town.add_agent(cash=50_000_000)
    fail_firm(town, firm, "payroll")                  # sold to the richest resident
    assert firm.alive and firm.ceo is rich
    town.week += 20                                   # past the quarter's grace, inside the year
    spent = rich.cash
    fail_firm(town, firm, "payroll")
    assert not firm.alive                             # nobody is made to buy it a second time
    assert rich.cash >= spent                         # and the last buyer puts no more money in
    assert all("food" not in a.subs for a in buyers)
    assert [e["kind"] for e in town.rec.events].count("takeover") == 1


def test_service_firm_can_be_sold_again_after_a_year(town):
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=3, customers=5)
    town.add_agent(cash=50_000_000)
    fail_firm(town, firm, "payroll")
    town.week += 60
    town.add_agent(cash=90_000_000)
    fail_firm(town, firm, "payroll")
    assert firm.alive
    assert [e["kind"] for e in town.rec.events].count("takeover") == 2


def test_landlord_with_tenants_is_always_sold(town):
    founder, firm, _, tenants = staffed_firm(town, "housing", 2_000_000, 1_000_000, customers=6, units=6)
    first = town.add_agent(cash=40_000_000)
    fail_firm(town, firm, "loan")
    town.week += 20
    second = town.add_agent(cash=80_000_000)
    fail_firm(town, firm, "loan")                     # inside the year, but people live there
    assert firm.alive and firm.ceo is second
    assert all(a.subs["housing"] is firm for a in tenants)
    assert len(firm.units) == 6


def test_pending_share_offer_does_not_survive_a_sale(town):
    founder, firm, staff, buyers = staffed_firm(town, "food", 1_000_000, 500_000, staff=3, customers=5)
    town.broker.issue(firm, 950, 200)                 # the old owners were raising money
    firm.q_revenue, firm.q_wages = 123_456, 654_321
    rich = town.add_agent(cash=50_000_000)
    fail_firm(town, firm, "payroll")
    assert town.broker.pending_issue(firm) == 0
    assert (firm.q_revenue, firm.q_wages) == (0, 0)   # the new owner's first quarter starts clean
