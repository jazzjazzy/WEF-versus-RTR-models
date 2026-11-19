"""Jason's rulings of 16 November 2026. Each is a dial: the default is his ruling, and
config.OLD_RULES gives the model as it was built before, record for record."""

from conftest import what_happened

from engine.config import OLD_RULES, load_config
from engine.town import Town

# Records made by the code at 6115ebe, before any ruling was built (ledger of 16/11).
MAP_SMALL = (["population_cap=120", "stop_on_failure=false", "seed=1"], ("8695200c6089e105", 33859))
MAP_ROUGH = (["population_cap=160", "stop_on_failure=false", "seed=4", "founder_arrival_rate=0.25",
              "resident_founder_rate=0.2", "invent_prob=0.1"], ("4037d21bbcc64ec2", 24416))


def _ten_years(overrides):
    town = Town(load_config(None, overrides))
    for _ in range(10 * 52):
        town.step()
    return what_happened(town)


# --- the defaults are his rulings ----------------------------------------------------------------
def test_a_lost_luxury_fades_after_a_year():                       # decision 2
    assert load_config().habit_weeks == 52


def test_the_town_starts_with_sixty_homes_and_the_appliance_sets_as_before():   # decision 5
    cfg = load_config()
    assert cfg.need("housing").initial_units == 60
    assert cfg.need("appliances").initial_units == 120


def test_a_transport_firm_with_riders_is_always_sold_on():         # decision 10
    assert load_config().transport_can_close is False


def test_the_old_rules_give_the_old_values():
    cfg = load_config(None, OLD_RULES)
    assert cfg.habit_weeks == 0
    assert cfg.need("housing").initial_units == 120
    assert cfg.transport_can_close is True


# --- the old rules give the old records -----------------------------------------------------------
def test_old_rules_on_the_map_give_the_record_made_before_the_rulings():
    for overrides, record in (MAP_SMALL, MAP_ROUGH):
        assert _ten_years(OLD_RULES + overrides) == record


def test_the_rulings_change_the_town():
    overrides, record = MAP_SMALL
    assert _ten_years(overrides) != record


# --- decision 13: the fare before the rent when the ride is for work -----------------------------------
def _rider_to_work(*overrides):
    """A tenant at one corner who works at the food shop in the far corner and rides there."""
    from test_places import employ, far_job_scene, tenant
    from engine.subscriptions import subscribe
    town, landlord, home, food, bus = far_job_scene(*overrides)
    rider = tenant(town, home)
    employ(rider, food)
    assert subscribe(town, rider, food) and subscribe(town, rider, bus)
    return town, rider, landlord, food, bus


def test_a_ride_to_work_is_paid_after_food_and_before_the_rent():
    from engine.household import dues
    town, rider, *_ = _rider_to_work()
    assert [name for _, _, name, _ in dues(town, rider)] == ["food", "transport", "housing"]


def test_as_first_written_the_fare_came_after_the_rent():
    from engine.household import dues
    town, rider, *_ = _rider_to_work("fare_first_for_work=false")
    assert [name for _, _, name, _ in dues(town, rider)] == ["food", "housing", "transport"]


def test_a_ride_that_is_only_for_food_keeps_its_place_after_the_rent():
    from engine.household import dues
    town, rider, landlord, food, bus = _rider_to_work()
    food.staff.remove(rider)
    near = premises_near(town, rider)
    employ_at(rider, near)
    assert [name for _, _, name, _ in dues(town, rider)] == ["food", "housing", "transport"]


def test_a_chief_executive_is_not_bound_by_the_walk_so_their_fare_keeps_its_place():
    from engine.household import dues
    town, rider, *_ = _rider_to_work()
    rider.role = "ceo"
    assert [name for _, _, name, _ in dues(town, rider)] == ["food", "housing", "transport"]


def test_short_of_money_a_rider_to_work_keeps_the_ride_and_misses_the_rent():
    from engine.household import dues, pay_bills
    from engine.subscriptions import price_paid
    town, rider, *_ = _rider_to_work()
    rider.cash = price_paid(rider, "food") + price_paid(rider, "transport")   # enough for food and the fare only
    rider.credit_block_until = 10_000                                          # and the bank will not lend
    rider.horizon = 1_000.0                                                    # calm: no selling, no borrowing for luxuries
    pay_bills(town)
    assert rider.met["food"] and rider.met["transport"]
    assert (rider.arrears["transport"], rider.arrears["housing"]) == (0, 1)   # the rent is missed (the home is kept for the grace weeks)


def premises_near(town, agent):
    """A firm whose premises are within a walk of the agent's home."""
    from test_places import premises
    from engine.places import home_spot
    home = home_spot(agent)
    return premises(town, "entertainment", home.x + 1, home.y)


def employ_at(agent, firm):
    agent.employer, agent.role, agent.wage = firm, "staff", firm.wage
    firm.staff.append(agent)


# --- decision 12: a shop opens where people are unserved -------------------------------------------------
def _far_corner(people=24, *overrides):
    """People living in the top left corner; the only entertainment is in the far corner, beyond a walk."""
    from conftest import map_town
    from test_places import block, premises, tenant
    town = map_town("switch_prob=0.0", "move_prob=0.0", *overrides)
    landlord = premises(town, "housing", 6, 5)
    homes = [block(town, landlord, x, y, homes=-(-people // 3)) for x, y in ((0, 0), (1, 0), (0, 1))]
    show = premises(town, "entertainment", 12, 12, price=9_000)
    folk = [tenant(town, homes[i % 3]) for i in range(people)]
    return town, show, folk


def test_a_founder_enters_the_need_people_cannot_reach_and_aims_for_where_they_live():
    from engine.corporate import choose_venture
    from engine.places import dist
    town, show, folk = _far_corner()
    spec, price, target, count = choose_venture(town, 20_000_000)
    assert spec.name == "entertainment" and count == 24
    assert target.id in {town.map.at(x, y).id for x, y in ((0, 0), (1, 0), (0, 1))}
    assert price == show.price                     # nobody to undercut: their customers cannot reach the rival


def test_the_price_is_never_below_cost_and_the_floor_margin():
    from engine.corporate import choose_venture
    from engine.production import unit_cost
    town, show, folk = _far_corner()
    show.price = 100                               # a rival selling for almost nothing
    spec, price, *_ = choose_venture(town, 20_000_000)
    assert price == round(unit_cost(town.cfg, spec, town.typical_wage()) * (1 + town.cfg.cost_floor_markup))


def test_the_new_shop_opens_within_a_walk_of_them_and_says_why():
    from engine.corporate import choose_venture, start_venture
    from engine.places import dist, reach
    town, show, folk = _far_corner()
    founder = town.add_agent(cash=50_000_000)
    firm = start_venture(town, founder, 20_000_000, *choose_venture(town, 20_000_000))
    assert firm.need == "entertainment" and firm.spot is not None
    assert all(dist(a.unit["housing"].spot, firm.spot) <= reach(town, a) for a in folk)
    [event] = [e for e in town.rec.events if e["kind"] == "unserved_entry"]
    assert (event["firm"], event["qty"], event["data"]["need"]) == (firm.id, 24, "entertainment")


def test_too_few_unserved_is_not_a_gap():
    from engine.corporate import unserved_gap
    town, show, folk = _far_corner(people=19)
    assert unserved_gap(town) is None
    town, show, folk = _far_corner(people=20)
    assert unserved_gap(town) is not None


def test_people_who_already_have_it_or_can_reach_it_are_not_unserved():
    from test_places import premises
    from engine.corporate import unserved_gap
    from engine.subscriptions import subscribe
    town, show, folk = _far_corner(people=40)
    for a in folk[:12]:
        subscribe(town, a, show)                   # they get there somehow: not unserved
    assert unserved_gap(town)[1] == 28
    premises(town, "entertainment", 2, 2)          # a second seller within a walk of all of them
    assert unserved_gap(town) is None


def test_homes_and_rides_are_not_shops():
    from engine.corporate import unserved_gap
    town, show, folk = _far_corner()
    show.alive = False
    town.firms.remove(show)                        # no seller of entertainment at all: that is the old rule's case
    assert unserved_gap(town) is None


def test_as_first_written_founders_did_not_look_for_the_unserved():
    from engine.corporate import choose_venture, unserved_gap
    town, show, folk = _far_corner(24, "shops_near_unserved=false")
    assert unserved_gap(town) is None
    venture = choose_venture(town, 20_000_000)
    assert venture is None or len(venture) == 2


# --- decision 8: the well-off spend more (a bigger plan and a better home) -------------------------------
def _resident(wage, cash=10_000_000, *overrides):
    """A town with no map: one landlord, food and entertainment, and a resident who has all three."""
    from conftest import empty_town
    from engine.subscriptions import subscribe
    town = empty_town("switch_prob=0.0", *overrides)
    landlord, food, show = town.add_firm("housing"), town.add_firm("food"), town.add_firm("entertainment")
    town.new_unit(landlord)
    a = town.add_agent(cash=cash)
    a.wage = wage
    for firm in (landlord, food, show):
        assert subscribe(town, a, firm)
    return town, a, landlord, food, show


def test_a_well_off_resident_takes_a_bigger_plan_of_what_they_use_up_and_pays_for_it():
    from engine.household import review_subscriptions
    from engine.subscriptions import price_paid
    town, a, landlord, food, show = _resident(wage=200_000)        # bills are $825 a week; pay is $2,000
    review_subscriptions(town)
    assert a.plan == {"food": 2, "entertainment": 2}                 # not the home: that is a better home, not a bigger plan
    assert price_paid(a, "food") == 2 * food.price and price_paid(a, "entertainment") == 2 * show.price
    changes = [(e["data"]["need"], e["qty"]) for e in town.rec.events if e["kind"] == "plan_change"]
    assert sorted(changes) == [("entertainment", 2), ("food", 2)]


def test_a_firm_counts_a_bigger_plan_as_that_many_customers():
    from engine.household import review_subscriptions
    from engine.labour import labour_need
    town, a, landlord, food, show = _resident(wage=200_000)
    before = labour_need(food, town.cfg)
    review_subscriptions(town)
    two = town.add_agent()
    from engine.subscriptions import subscribe
    subscribe(town, two, food)
    assert food.load() == 3 and labour_need(food, town.cfg) > before


def test_a_firm_short_of_staff_leaves_the_last_plans_unserved_counting_their_size():
    from engine.household import review_subscriptions
    from engine.production import _work
    from engine.subscriptions import subscribe
    town, rich, landlord, food, show = _resident(wage=200_000)
    food.subs.clear()                                                 # put the rich customer last
    others = [town.add_agent() for _ in range(4)]
    for o in others:
        subscribe(town, o, food)
    food.subs[rich.id] = rich
    food.make_mode, food.cash = "import", 10_000_000
    food.staff = [town.add_agent()]                                   # one worker serves five plans of food (0.18 each)
    review_subscriptions(town)
    assert rich.plan["food"] == 2 and food.load() == 6
    _work(town, food)
    assert set(food.unserved) == {rich.id}


def test_someone_no_longer_well_off_goes_back_to_the_standard_plan_and_stops_waiting():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000)
    review_subscriptions(town)
    assert a.wants_better
    a.wage = 50_000
    review_subscriptions(town)
    assert a.plan == {} and food.load() == 1 and not a.wants_better


def test_between_the_two_lines_nobody_changes_plan():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=110_000)         # 1.33 times the bills
    review_subscriptions(town)
    assert a.plan == {}                                               # not yet well-off
    a.wage = 200_000
    review_subscriptions(town)
    a.wage = 110_000
    review_subscriptions(town)
    assert a.plan == {"food": 2, "entertainment": 2}                 # and not yet no longer well-off


def test_a_thin_cushion_is_not_well_off():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000, cash=100_000)
    review_subscriptions(town)
    assert a.plan == {}


def test_a_ride_is_never_a_bigger_plan():
    from engine.household import review_subscriptions
    from engine.corporate import transport_spec
    from engine.subscriptions import subscribe
    town, a, landlord, food, show = _resident(wage=200_000)
    town.needs["transport"] = transport_spec(town)
    bus = town.add_firm("transport")
    subscribe(town, a, bus)
    review_subscriptions(town)
    assert "transport" not in a.plan


def test_dropping_a_need_drops_its_plan():
    from engine.household import review_subscriptions
    from engine.subscriptions import unsubscribe
    town, a, landlord, food, show = _resident(wage=200_000)
    review_subscriptions(town)
    unsubscribe(town, a, "food", "budget")
    assert "food" not in a.plan and food.load() == 0


def test_moving_up_does_not_move_the_yardstick():
    from engine.household import basket_cost, review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000)
    before = basket_cost(town, a)
    review_subscriptions(town)
    assert basket_cost(town, a) == before


def test_as_first_written_nobody_spends_more():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(200_000, 10_000_000, "well_off_income=0")
    review_subscriptions(town)
    assert a.plan == {} and not a.well_off


def test_a_better_home_costs_half_as_much_again_to_build_keep_up_rent_and_pledge():
    from engine.entities import Project
    from engine.places import unit_rent
    from engine.production import upkeep_need
    town, a, landlord, food, show = _resident(wage=50_000)
    cfg = town.cfg
    plain, better = town.new_unit(landlord), town.new_unit(landlord)
    better.scale = cfg.better_home
    for u in (plain, better):
        u.age = 520
    assert unit_rent(better) == round(1.5 * unit_rent(plain))
    assert upkeep_need(cfg, better) == tuple(1.5 * x for x in upkeep_need(cfg, plain))
    assert Project(landlord.spec, scale=1.5).labour_left == 1.5 * Project(landlord.spec).labour_left
    assert Project(landlord.spec, better).goods_left == 1.5 * Project(landlord.spec, plain).goods_left
    assert abs(landlord.units_value(cfg, [better]) - 1.5 * landlord.units_value(cfg, [plain])) <= 2   # whole cents


def test_well_off_with_no_map_takes_a_free_better_home_and_otherwise_the_landlord_hears_of_it():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000)
    review_subscriptions(town)
    assert a.unit["housing"].scale == 1.0 and a.wants_better                    # none free: they wait for one
    better = town.new_unit(landlord)
    better.scale = town.cfg.better_home
    a.well_off = False                                                           # so they look again when they become well-off
    review_subscriptions(town)
    assert a.unit["housing"] is better and not a.wants_better
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "moved_home"] == ["better"]


def test_the_biggest_landlord_builds_better_homes_for_those_still_waiting():
    from engine.production import _finish_projects, plan_building
    town, a, landlord, food, show = _resident(wage=50_000)
    small = town.add_firm("housing")
    landlord.cash = small.cash = 100_000_000
    landlord.wage = small.wage = 100_000
    waiting = [town.add_agent() for _ in range(3)]
    for w in waiting:
        w.wants_better = True
    spare = town.new_unit(landlord)
    spare.scale = town.cfg.better_home                    # one better home already stands free
    plan_building(town, small)
    assert not [p for p in small.projects if p.scale > 1.0]   # the smaller landlord leaves it to the biggest
    plan_building(town, landlord)
    better = [p for p in landlord.projects if p.scale > 1.0]
    assert len(better) == 2                               # three waiting, one free home already
    plan_building(town, landlord)
    assert len([p for p in landlord.projects if p.scale > 1.0]) == 2      # the two under way count
    for p in landlord.projects:
        p.labour_left = 0.0
    _finish_projects(town, landlord)
    built = [e for e in town.rec.events if e["kind"] == "unit_built"]
    assert sum(1 for e in built if e["data"].get("grade") == "better") == 2
    assert sum(1 for u in landlord.units if u.scale > 1.0) == 3


def test_on_the_map_a_well_off_resident_moves_to_a_free_better_home_within_reach():
    from conftest import map_town
    from test_places import block, premises, tenant
    from engine.household import review_subscriptions
    town = map_town("switch_prob=0.0", "move_prob=0.0", "sell_review_prob=0.0", "invest_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    near, other = block(town, landlord, 5, 6, homes=2), block(town, landlord, 7, 6, homes=1)
    from engine.places import make_better
    make_better(other.units[0], town.cfg.better_home)
    premises(town, "food", 6, 6)
    a = tenant(town, near, cash=10_000_000)
    a.wage = 200_000
    review_subscriptions(town)
    assert a.unit["housing"] is other.units[0]


# --- all of it at once: the accounts hold, and every new rule is reached ---------------------------------
def test_under_the_rulings_the_accounts_and_places_hold_and_every_new_rule_happens():
    import collections
    from test_town_invariants import ROUGH_MAP, run_checked
    seen = collections.Counter()
    for seed in (8, 28):
        town = Town(load_config(None, ROUGH_MAP + [f"seed={seed}"]))
        assert run_checked(town, 12 * 52) == []
        for e in town.rec.events:
            kind, data = e["kind"], e["data"]
            seen[kind] += 1
            if kind == "unit_built" and data.get("grade") == "better":
                seen["better home built"] += 1
            if kind == "moved_home":
                seen[f"moved: {data['reason']}"] += 1
            if kind == "plan_change":
                seen[f"plan {e['qty']}"] += 1
    for kind in ("unserved_entry", "plan 2", "plan 1", "better home built", "moved: better"):
        assert seen[kind] > 0, f"these runs never reached '{kind}'"



def test_the_settings_file_for_the_old_rules_is_the_same_as_the_list():
    assert load_config("wef/before-16-november.json").to_dict() == load_config(None, OLD_RULES).to_dict()


# --- the review of 16/11: what the well-off rules got wrong, now pinned ------------------------------------
def test_well_off_and_short_of_cash_they_go_back_to_the_standard_plan_before_dropping_anything():
    from engine.household import basket_cost, buffer_target, plan_bills, review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000)
    a.horizon = 1_000.0                                        # calm: they trim rather than borrow
    review_subscriptions(town)
    assert a.plan == {"food": 2, "entertainment": 2}
    a.wage = 130_000                                           # under the bigger bills ($1,320), over the standard ($825)
    a.cash = int(0.75 * buffer_target(town.cfg, a, basket_cost(town, a)))   # still well-off, cushion thin
    plan_bills(town)
    assert "entertainment" in a.subs and a.plan == {"food": 2}     # stepped down as far as they needed, least needed first
    review_subscriptions(town)
    assert a.plan == {"food": 2}                                    # and not straight back up: they could not afford it


def test_a_bigger_plan_is_taken_only_while_income_stays_well_over_the_bills_with_it():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=135_000)        # 1.64 times the standard bills of $825
    review_subscriptions(town)
    assert a.well_off and a.plan == {"entertainment": 2}           # double food ($1,225 a week) is too much for $1,350 pay;
                                                                    # double entertainment ($920) is not


def test_empty_better_homes_do_not_stop_the_usual_building():
    from engine.production import plan_building
    def starts(better_free):
        town, a, landlord, food, show = _resident(wage=50_000)
        landlord.cash, landlord.wage = 100_000_000, 100_000
        from engine.subscriptions import subscribe
        for _ in range(19):
            town.new_unit(landlord)
            subscribe(town, town.add_agent(), landlord)
        for _ in range(better_free):
            town.new_unit(landlord).scale = town.cfg.better_home
        plan_building(town, landlord)
        return sum(1 for p in landlord.projects if p.scale == 1.0)
    assert starts(4) == starts(0) > 0


def test_no_longer_well_off_they_can_move_to_a_cheaper_home_on_their_own_block():
    from conftest import map_town
    from test_places import block, premises, tenant
    from engine.household import review_subscriptions
    from engine.places import make_better
    from engine.subscriptions import subscribe
    town = map_town("switch_prob=0.0", "move_prob=1.0", "sell_review_prob=0.0", "invest_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 5, 6, homes=2)
    make_better(home.units[0], town.cfg.better_home)
    premises(town, "food", 6, 6)
    a = town.add_agent(cash=1_000_000)
    assert subscribe(town, a, landlord, unit=home.units[0])
    a.wage = 60_000
    review_subscriptions(town)
    assert a.unit["housing"] is home.units[1]


def test_with_no_map_someone_waiting_takes_the_better_home_when_one_comes_free():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=200_000)
    review_subscriptions(town)
    assert a.wants_better
    better = town.new_unit(landlord)
    better.scale = town.cfg.better_home
    review_subscriptions(town)
    assert a.unit["housing"] is better and not a.wants_better


def test_with_no_map_a_well_off_newcomer_signs_up_for_a_better_home_first_or_waits():
    from engine.household import review_subscriptions
    from engine.subscriptions import unsubscribe
    town, a, landlord, food, show = _resident(wage=200_000)
    unsubscribe(town, a, "housing", "test")
    a.well_off = True
    review_subscriptions(town)
    assert a.unit["housing"].scale == 1.0 and a.wants_better       # only a standard home free: they take it and wait
    unsubscribe(town, a, "housing", "test")
    better = town.new_unit(landlord)
    better.scale = town.cfg.better_home
    review_subscriptions(town)
    assert a.unit["housing"] is better and not a.wants_better


def test_on_the_map_a_well_off_newcomer_who_finds_only_a_standard_home_waits_for_a_better_one():
    from conftest import map_town
    from test_places import block, premises
    from engine.household import review_subscriptions
    town = map_town("switch_prob=0.0", "move_prob=0.0", "sell_review_prob=0.0", "invest_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 5, 6, homes=2)
    premises(town, "food", 6, 6)
    a = town.add_agent(cash=10_000_000)
    a.wage = 200_000
    review_subscriptions(town)
    assert a.unit["housing"].spot is home and a.well_off and a.wants_better


def test_losing_a_bill_does_not_make_anyone_well_off():
    from engine.household import review_subscriptions
    from engine.subscriptions import subscribe, unsubscribe
    town, a, landlord, food, show = _resident(wage=90_000)         # bills $825: not well-off
    review_subscriptions(town)
    assert not a.well_off
    unsubscribe(town, a, "housing", "evicted")
    other = town.add_agent()
    subscribe(town, other, landlord)                               # their home goes to someone else
    review_subscriptions(town)
    assert not a.well_off and a.plan == {}                         # homeless is not well-off


def test_only_someone_who_could_pay_for_a_better_home_waits_for_one():
    from engine.household import review_subscriptions
    town, a, landlord, food, show = _resident(wage=135_000)
    review_subscriptions(town)
    assert a.well_off and a.wants_better                  # $495 of better rent fits under their pay with room to spare
    town, a, landlord, food, show = _resident(wage=170_000)
    review_subscriptions(town)
    assert a.plan == {"food": 2, "entertainment": 2}      # their pay went on bigger plans first
    assert a.well_off and not a.wants_better              # and a better home would not leave room to spare


# --- no cap on people: the only limit is the homes that can be built (Jason, 16/11/2026) ---------------
def _crowded(*overrides):
    """A town with no map that already has 1,000 people, one landlord and one free home."""
    from conftest import empty_town
    town = empty_town(*overrides)
    landlord = town.add_firm("housing")
    town.add_firm("food")
    for _ in range(1000):
        town.add_agent()
    town.new_unit(landlord)
    return town


def test_there_is_no_cap_on_people():
    cfg = load_config()
    assert cfg.population_cap == 0
    assert load_config(None, OLD_RULES).population_cap == 1000


def test_with_no_cap_a_worker_still_comes_while_a_home_is_free():
    from engine.labour import new_worker
    town = _crowded()
    assert new_worker(town) is not None and town.population == 1001
    assert new_worker(town) is None                          # but only to a home: none is free now


def test_with_the_old_cap_nobody_comes_past_a_thousand():
    from engine.labour import new_worker
    town = _crowded("population_cap=1000")
    assert new_worker(town) is None and town.population == 1000


def test_with_no_cap_founders_keep_coming_while_a_home_is_free():
    from engine.corporate import maybe_arrive_founder
    town = _crowded("founder_arrival_rate=1.0")
    before = town.population
    maybe_arrive_founder(town)
    assert town.population == before + 1


def test_a_cap_below_the_founders_is_refused_but_no_cap_is_fine():
    import pytest
    with pytest.raises(ValueError):
        load_config(None, ["population_cap=3"])
    load_config(None, ["population_cap=0"])


def test_with_no_cap_the_town_is_full_when_land_has_run_out_and_a_newcomer_finds_no_home():
    town = Town(load_config(None, ["map_width=5", "map_height=5", "homes_per_spot=4", "stop_on_failure=false",
                                   "founder_arrival_rate=0.0"]))
    for _ in range(6 * 52):
        town.step()
    full = [e for e in town.rec.events if e["kind"] == "town_full"]
    assert len(full) == 1 and full[0]["data"]["reason"] == "no home, no land"
    assert town.map.scarce and town.cap_week == full[0]["week"]
    blocked = [e for e in town.rec.events if e["kind"] == "arrival_blocked" and e["week"] == full[0]["week"]]
    assert blocked                                         # someone was turned away that week
    housed = {(e["week"], e["agent"]) for e in town.rec.events
              if e["kind"] == "sub_start" and e["data"]["need"] == "housing"}
    arrivals = [(e["week"], e["agent"]) for e in town.rec.events if e["kind"] == "arrival"]
    assert len(arrivals) > 40 and all(a in housed for a in arrivals)   # nobody moves in without a home
