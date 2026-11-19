import pytest

from engine.metrics import gini, top_share, weekly_series
from conftest import small_town


def test_gini_known_values():
    assert gini([1, 1, 1, 1]) == pytest.approx(0.0)
    assert gini([0, 0, 0, 1]) == pytest.approx(0.75)
    assert gini([]) == 0.0
    assert gini([0, 0, 0]) == 0.0
    assert gini([5]) == 0.0


def test_top_share():
    assert top_share([1] * 9 + [91]) == pytest.approx(0.91)
    assert top_share([]) == 0.0
    assert top_share([0, 0]) == 0.0
    assert top_share([10], 0.10) == pytest.approx(1.0)


def test_series_covers_everyone_both_classes_and_the_out_of_work():
    town = small_town()
    town.run(60)
    rows = weekly_series(town)
    scopes = {scope for scope, _, _ in rows}
    assert scopes == {"all", "owner", "working", "out", "town"}
    by = {(scope, metric): value for scope, metric, value in rows}
    for metric in ("n", "unhappy", "security", "wellbeing", "provision", "condition", "income",
                   "cash_mean", "cash_median", "shares_pct", "destitute"):
        for scope in ("all", "owner", "working", "out"):
            assert (scope, metric) in by, (scope, metric)
    assert by[("all", "n")] == town.population
    assert by[("owner", "n")] + by[("working", "n")] + by[("out", "n")] == town.population
    assert by[("all", "unhappy")] == pytest.approx(town.unhappy_share())
    assert by[("town", "unhappy_share")] == pytest.approx(town.unhappy_share())
    assert by[("town", "money")] == town.money_in_town()


def test_share_split_between_classes_adds_to_one():
    town = small_town()
    town.run(60)
    by = {(s, m): v for s, m, v in weekly_series(town)}
    assert by[("owner", "shares_pct")] + by[("working", "shares_pct")] + by[("out", "shares_pct")] \
        == pytest.approx(1.0)
    assert by[("all", "shares_pct")] == pytest.approx(1.0)


def test_five_flows_are_reported_every_week():
    town = small_town()
    town.run(30)
    by = {(s, m): v for s, m, v in weekly_series(town)}
    for metric in ("in_arrival", "in_loan", "in_export", "out_repay", "out_interest", "out_import"):
        assert ("town", metric) in by
    net = (by[("town", "in_arrival")] + by[("town", "in_loan")] + by[("town", "in_export")]
           - by[("town", "out_repay")] - by[("town", "out_interest")] - by[("town", "out_import")])
    assert net == town.ledger.net_week()


def test_empty_class_reports_zero_not_an_error():
    town = small_town("founder_arrival_rate=0.0", "needs.housing.initial_units=4")
    town.run(4)                                   # four founders only: no working class, nobody out of work
    by = {(s, m): v for s, m, v in weekly_series(town)}
    assert by[("working", "n")] == 0 and by[("working", "unhappy")] == 0.0
    assert by[("working", "cash_median")] == 0.0


def test_base_need_with_no_seller_keeps_its_last_price():
    from engine.corporate import wind_up
    from engine.household import basket_cost
    town = small_town()
    town.run(20)
    before = {(s, m): v for s, m, v in weekly_series(town)}
    fun = town.firms_for("entertainment")[0]
    price = fun.price
    resident = town.agents[0]
    owed = basket_cost(town, resident)
    wind_up(town, fun, "idle")                    # the only entertainment firm closes
    after = {(s, m): v for s, m, v in weekly_series(town)}
    assert after[("town", "firms_entertainment")] == 0
    assert after[("town", "price_entertainment")] == price
    assert after[("town", "basket")] == before[("town", "basket")]
    assert basket_cost(town, resident) == owed    # the yardstick does not shrink because a firm closed
