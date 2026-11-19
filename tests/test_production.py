import pytest

from engine.entities import Project
from engine.production import (best_condition, choose_make_mode, export_target, operate,
                                 plan_building, update_condition, upkeep_need)
from conftest import empty_town


def firm_with(town, need, staff=0, subs=0, cash=0, units=0):
    firm = town.add_firm(need)
    if cash:
        banker = town.add_agent(cash=cash)
        town.ledger.pay(banker, firm, cash, "founding")
    for _ in range(staff):
        firm.staff.append(town.add_agent())
    for _ in range(subs):
        a = town.add_agent()
        firm.subs[a.id] = a
        a.subs[need] = firm
    for _ in range(units):
        town.new_unit(firm)
    return firm


def test_upkeep_rises_with_age(town):
    firm = firm_with(town, "housing", units=1)
    unit = firm.units[0]
    labour_new, goods_new = upkeep_need(town.cfg, unit)
    assert labour_new == pytest.approx(0.04) and goods_new == pytest.approx(0.4)
    unit.age = 10 * 52
    labour_old, goods_old = upkeep_need(town.cfg, unit)
    assert labour_old == pytest.approx(0.04 * (1 + 0.04 * 10))
    assert goods_old == pytest.approx(0.4 * (1 + 0.04 * 10))


def test_best_condition_falls_with_age(town):
    firm = firm_with(town, "housing", units=1)
    unit = firm.units[0]
    assert best_condition(town.cfg, unit) == pytest.approx(1.0)
    unit.age = 25 * 52
    assert best_condition(town.cfg, unit) == pytest.approx(1 - 0.012 * 25)
    unit.age = 200 * 52
    assert best_condition(town.cfg, unit) == pytest.approx(town.cfg.cond_floor_best)


def test_condition_falls_when_skimped_and_recovers_slowly(town):
    firm = firm_with(town, "housing", units=1)
    unit = firm.units[0]
    for _ in range(52):
        update_condition(town.cfg, unit, done=0.0)
    neglected = unit.cond
    assert 0.4 < neglected < 0.55
    for _ in range(52):
        update_condition(town.cfg, unit, done=1.0)
    assert neglected < unit.cond < 0.9          # a year of full upkeep does not undo a year of none


def test_units_age_one_week_per_step(town):
    firm = firm_with(town, "housing", staff=2, cash=1_000_000, units=3)
    operate(town)
    assert [u.age for u in firm.units] == [1, 1, 1]


def test_skimped_upkeep_shows_in_condition(town):
    kept = firm_with(town, "housing", staff=3, cash=10_000_000, units=20)
    skimped = firm_with(town, "housing", staff=3, cash=10_000_000, units=20)
    skimped.upkeep_level = 0.2
    for _ in range(26):
        operate(town)
    assert kept.units[0].cond > 0.97
    assert skimped.units[0].cond < kept.units[0].cond - 0.1
    assert skimped.upkeep_done == pytest.approx(0.2)


def test_make_or_import_follows_the_cheaper(town):
    firm = firm_with(town, "food")
    firm.wage = 100_000                       # making costs $140 plus overhead, importing $189
    assert choose_make_mode(town.cfg, firm) == "make"
    firm.wage = 150_000                       # making now costs $231
    firm.make_mode = choose_make_mode(town.cfg, firm)
    assert firm.make_mode == "import"
    firm.wage = 120_000                       # $184.80 with overhead: not enough cheaper to switch back
    assert choose_make_mode(town.cfg, firm) == "import"
    firm.wage = 100_000
    assert choose_make_mode(town.cfg, firm) == "make"


def test_making_in_town_sends_no_money_out(town):
    firm = firm_with(town, "food", staff=4, subs=10, cash=1_000_000)
    operate(town)
    assert firm.made_units == pytest.approx(10.0)
    assert "import" not in town.ledger.week_out
    assert firm.unserved == {}


def test_importing_sends_money_out(town):
    firm = firm_with(town, "food", staff=4, subs=10, cash=1_000_000)
    firm.make_mode = "import"
    operate(town)
    assert firm.import_units == pytest.approx(10.0)
    assert town.ledger.week_out["import"] == 189_000
    assert firm.w_goods == 189_000


def test_short_of_staff_the_gap_is_imported(town):
    firm = firm_with(town, "food", staff=2, subs=10, cash=1_000_000)
    operate(town)                             # 1.8 on service leaves 0.2 to make 1.43 units
    assert firm.unserved == {}
    assert 0 < firm.made_units < 2
    assert town.ledger.week_out["import"] > 150_000


def test_too_few_staff_leaves_newest_customers_unserved(town):
    firm = firm_with(town, "food", staff=1, subs=10, cash=1_000_000)
    operate(town)                             # one worker serves five customers
    assert len(firm.unserved) == 5
    assert list(firm.unserved) == list(firm.subs)[5:]


def test_exports_only_when_profitable(town):
    firm = firm_with(town, "food")
    firm.wage = 100_000
    assert export_target(town.cfg, firm, n_firms=1) == pytest.approx(1_100.0)
    assert export_target(town.cfg, firm, n_firms=2) == pytest.approx(550.0)
    firm.wage = 110_000                       # $154 a unit plus overhead and margin beats $168 no longer
    assert export_target(town.cfg, firm, n_firms=1) == 0.0


def test_exports_bring_money_in_and_share_the_quota(town):
    a = firm_with(town, "food", staff=200)
    b = firm_with(town, "food", staff=200)
    a.export_target = b.export_target = 1_100.0
    operate(town)
    assert a.export_units == pytest.approx(550.0) and b.export_units == pytest.approx(550.0)
    assert town.ledger.week_in["export"] == 2 * 550 * 16_800
    assert a.w_export == 550 * 16_800


def test_housing_firm_builds_when_buffer_runs_low(town):
    firm = firm_with(town, "housing", cash=100_000_000, units=10)
    for u in firm.units:
        u.occupant = town.add_agent()
    plan_building(town, firm)
    assert len(firm.projects) == 4            # buffer of four vacant homes


def test_people_turned_away_add_to_the_building_plan(town):
    firm = firm_with(town, "housing", cash=100_000_000, units=10)
    for u in firm.units:
        u.occupant = town.add_agent()
    firm.unmet_demand = 2.0
    plan_building(town, firm)
    assert len(firm.projects) == 6


def test_building_needs_funding():
    town = empty_town("ltv=0.0")
    firm = firm_with(town, "housing", cash=0, units=10)
    for u in firm.units:
        u.occupant = town.add_agent()
    plan_building(town, firm)
    assert firm.projects == []
    assert firm.funding_gap > 0


def test_project_becomes_a_unit_after_enough_labour(town):
    firm = firm_with(town, "housing", staff=6, cash=100_000_000)
    firm.projects.append(Project(firm.spec))
    for _ in range(4):
        operate(town)
    assert len(firm.units) == 0
    operate(town)                             # 30 worker-weeks at six a week
    assert len(firm.units) == 1
    assert [e["kind"] for e in town.rec.events].count("unit_built") == 1
    # the buffer rule has queued more homes behind it; none of those has had any labour yet
    assert all(p.labour_left == 30.0 for p in firm.projects)


def test_rebuild_resets_age_and_condition(town):
    firm = firm_with(town, "appliances", staff=2, cash=10_000_000, units=1)
    unit = firm.units[0]
    unit.age, unit.cond = 9 * 52, 0.4
    firm.projects.append(Project(firm.spec, unit))
    operate(town)
    assert unit.age == 0 and unit.cond == 1.0
    assert unit in firm.units                 # the same set, renewed, not a new one
    assert [e["kind"] for e in town.rec.events].count("unit_rebuilt") == 1


def test_firm_stops_exporting_when_its_own_wage_rise_makes_it_unprofitable(town):
    from engine.firmops import set_wage
    firm = firm_with(town, "food")
    firm.export_target = export_target(town.cfg, firm, n_firms=1)
    assert firm.export_target == pytest.approx(1_100.0)
    set_wage(town, firm, 110_000, "unfilled")          # bidding for staff has made exporting a loss
    assert firm.export_target == 0.0
    set_wage(town, firm, 100_000, "queue")             # and a cut makes it pay again
    assert firm.export_target == pytest.approx(1_100.0)


def test_sloped_outside_demand_tapers_exports():
    town = empty_town("export_price_drop=0.2", "needs.food.export_price=19600")
    firm = firm_with(town, "food")
    firm.wage = 100_000                                # cost with overhead and margin: $157.08
    assert export_target(town.cfg, firm, n_firms=1) == pytest.approx(1_100 * (1 - 15_708 / 19_600) / 0.2)
    firm.wage = 110_000
    assert export_target(town.cfg, firm, n_firms=1) == pytest.approx(1_100 * (1 - 17_278.8 / 19_600) / 0.2, rel=1e-3)
    firm.wage = 125_000                                # $196.35: above the best price on offer
    assert export_target(town.cfg, firm, n_firms=1) == 0.0
    firm.wage = 50_000                                 # never more than its share of the quota
    assert export_target(town.cfg, firm, n_firms=2) == pytest.approx(550.0)


def test_sloped_outside_demand_pays_less_for_the_last_units():
    town = empty_town("export_price_drop=0.2", "needs.food.export_price=19600")
    firm = firm_with(town, "food", staff=200)
    firm.export_target = 1_100.0                       # its whole share
    operate(town)
    assert firm.export_units == pytest.approx(1_100.0)
    assert firm.w_export == round(1_100 * 19_600 * 0.9)   # the average of the first price and 20% less
    half = firm_with(empty := empty_town("export_price_drop=0.2", "needs.food.export_price=19600"),
                     "food", staff=200)
    half.export_target = 550.0
    operate(empty)
    assert half.w_export == round(550 * 19_600 * 0.95)
