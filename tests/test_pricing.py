import pytest

from engine.corporate import review_firm, target_growth
from conftest import empty_town


def firm_with_holders(town, need="food", holders=((75, 0.02), (25, 0.10))):
    firm = town.add_firm(need)
    for shares, growth in holders:
        a = town.add_agent(growth_expect=growth, horizon=52.0)
        a.security = 1.0                       # effective horizon exactly one year
        town.issue_shares(firm, a, shares)
    return firm


def quarter(firm, profit, revenue=1_000_000):
    """Set the quarter's accounts so that profit is `profit` on `revenue` from customers."""
    firm.q_revenue = revenue
    firm.q_wages = revenue - profit
    firm.q_goods = firm.q_interest = firm.q_export = firm.q_capex = firm.q_wear = 0


def test_target_growth_is_holding_weighted_average(town):
    firm = firm_with_holders(town)
    assert target_growth(town, firm) == pytest.approx(0.04)


def test_shortfall_raises_price_one_step(town):
    firm = firm_with_holders(town)
    firm.price = 40_000
    quarter(firm, -200_000)
    review_firm(town, firm)
    assert firm.shortfall is True
    assert firm.price == 41_200
    assert [e["kind"] for e in town.rec.events].count("price_change") == 1


def test_loss_always_counts_as_shortfall(town):
    firm = firm_with_holders(town)
    quarter(firm, -1)
    review_firm(town, firm)
    assert firm.shortfall is True


def test_no_shortfall_leaves_price_alone(town):
    firm = firm_with_holders(town)
    firm.price = 40_000
    quarter(firm, 200_000)
    review_firm(town, firm)
    assert firm.shortfall is False and firm.price == 40_000


def test_growing_slower_than_shareholders_expect_is_a_shortfall(town):
    firm = firm_with_holders(town)             # holders expect 4% a year
    for _ in range(4):
        quarter(firm, 100_000)
        review_firm(town, firm)
    price = firm.price
    quarter(firm, 103_000)                     # up 3% on the same quarter a year ago
    review_firm(town, firm)
    assert firm.shortfall is True
    assert firm.price == round(price * 1.03)


def test_meeting_expected_growth_is_not_a_shortfall(town):
    firm = firm_with_holders(town)
    for _ in range(4):
        quarter(firm, 100_000)
        review_firm(town, firm)
    price = firm.price
    quarter(firm, 104_500)
    review_firm(town, firm)
    assert firm.shortfall is False and firm.price == price


def test_building_spend_is_not_a_cost_of_the_quarter(town):
    firm = firm_with_holders(town, need="housing")
    firm.q_revenue, firm.q_wages, firm.q_capex = 1_000_000, 3_000_000, 2_500_000
    firm.q_goods = firm.q_interest = firm.q_export = firm.q_wear = 0
    review_firm(town, firm)
    assert firm.profit_hist[-1] == 500_000     # 1.0m revenue less 0.5m of wages that were not building
    assert firm.shortfall is False


def test_wear_on_units_is_a_cost_of_the_quarter(town):
    firm = firm_with_holders(town, need="housing")
    firm.q_revenue, firm.q_wear = 1_000_000, 1_200_000
    firm.q_wages = firm.q_goods = firm.q_interest = firm.q_export = firm.q_capex = 0
    review_firm(town, firm)
    assert firm.profit_hist[-1] == -200_000 and firm.shortfall is True


def test_ratchet_never_lowers_a_price(town):
    firm = firm_with_holders(town)
    firm.price = 40_000
    quarter(firm, -10)
    review_firm(town, firm)
    assert firm.price == 41_200
    quarter(firm, -50)                         # the rise lost money; the rule raises it again
    review_firm(town, firm)
    assert firm.price == 42_436


def test_search_rule_reverses_after_a_move_that_lowered_profit():
    town = empty_town("price_rule=search")
    firm = firm_with_holders(town)
    firm.price = 40_000
    quarter(firm, -10)
    review_firm(town, firm)
    assert firm.price == 41_200                # the first move is up
    quarter(firm, -50)
    review_firm(town, firm)
    assert firm.price == 39_964                # that lost money: back down
    quarter(firm, -20)
    review_firm(town, firm)
    assert firm.price == 38_765                # down helped: keep going


def test_upkeep_level_cut_on_shortfall_and_restored_after(town):
    firm = firm_with_holders(town, need="housing")
    quarter(firm, -100)
    review_firm(town, firm)
    assert firm.upkeep_level == pytest.approx(0.9)
    quarter(firm, 100)
    review_firm(town, firm)
    assert firm.upkeep_level == pytest.approx(0.95)


def test_impatient_shareholders_skimp_harder(town):
    firm = firm_with_holders(town, need="housing")
    for agent_id in firm.holders:
        town.agent(agent_id).horizon = 26.0    # half the reference horizon: twice the cut
    quarter(firm, -100)
    review_firm(town, firm)
    assert firm.upkeep_level == pytest.approx(0.8)


def test_firm_that_never_had_a_customer_does_not_move_its_price(town):
    firm = firm_with_holders(town, need="housing")
    firm.price = 30_000
    quarter(firm, -500_000, revenue=0)         # building its first homes: costs, no customers yet
    review_firm(town, firm)
    assert firm.shortfall is True
    assert firm.price == 30_000 and firm.upkeep_level == 1.0
