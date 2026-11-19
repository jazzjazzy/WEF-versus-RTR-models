import pytest

from engine.places import dist, home_cost, home_spot, needs_ride, transport_fare
from conftest import empty_town, map_town, small_town


# --- the map ------------------------------------------------------------------------------------
def test_default_map_is_169_spots():
    town = map_town()
    assert len(town.map.spots) == 169
    assert (town.map.centre.x, town.map.centre.y) == (6, 6)
    assert len(town.map.empty()) == 169 and not town.map.full
    assert [s.id for s in town.map.spots] == list(range(169))


def test_distance_is_blocks_along_the_grid():
    town = map_town()
    assert dist(town.map.at(0, 0), town.map.at(3, 4)) == 7
    assert dist(town.map.at(5, 5), town.map.at(5, 5)) == 0
    assert town.map.at(13, 0) is None and town.map.at(-1, 2) is None


def test_no_spot_means_no_distance():
    town = map_town()
    assert dist(None, town.map.at(0, 0)) == 0 and dist(None, None) == 0


def test_map_off_when_width_is_zero():
    assert empty_town().map is None
    assert empty_town("map_width=0", "map_height=9").map is None


def test_too_small_a_map_is_refused():
    with pytest.raises(ValueError, match="map"):
        map_town("map_width=2", "map_height=2")


# --- places on day one ----------------------------------------------------------------------------
def test_bank_and_broker_hold_the_middle():
    town = small_town()
    centre = town.map.centre
    assert (centre.kind, centre.label) == ("service", "bank")
    broker = town.map.at(centre.x + 1, centre.y)
    assert (broker.kind, broker.label) == ("service", "broker")


def test_founding_firms_sit_next_to_the_middle():
    town = small_town()
    for firm in town.firms:
        assert firm.spot is not None and firm.spot.kind == "premises"
        assert firm.spot.user is firm and firm.spot.owner is firm
        assert dist(firm.spot, town.map.centre) <= 2
    assert len({f.spot.id for f in town.firms}) == 4


def test_starting_homes_fill_the_best_placed_spots_eight_to_a_spot():
    town = small_town()
    housing = town.firms_for("housing")[0]
    assert len(housing.units) == 60 and all(u.spot is not None for u in housing.units)   # (J) 16/11: 60 homes
    assert sorted(len(spot.units) for spot in housing.lots) == [4] + [8] * 7
    for spot in housing.lots:
        assert spot.kind == "homes" and spot.user is housing
    appliances = town.firms_for("appliances")[0]
    assert all(u.spot is None for u in appliances.units)      # an appliance set lives in the agent's home


def test_early_town_is_within_walking_reach():
    town = small_town()
    homes = town.firms_for("housing")[0].lots
    for firm in town.firms:
        assert all(dist(h, firm.spot) <= town.cfg.walk_range for h in homes)


def test_founders_live_in_the_starting_homes():
    town = small_town()
    for firm in town.firms:
        founder = town.agent(firm.founder_id)
        assert founder.unit["housing"].spot is not None


def test_new_firm_pays_to_fit_out_its_premises():
    from engine.corporate import found_firm
    town = map_town()
    founder = town.add_agent(cash=20_000_000)
    town.ledger.start_week()
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])
    assert firm.spot is not None and firm.spot.user is firm
    assert town.ledger.week_out["import"] == 3_000_000        # the fit-out is bought from outside
    assert firm.cash == 12_000_000
    kinds = [e["kind"] for e in town.rec.events]
    assert kinds.count("spot_taken") == 1


def test_arriving_founder_settles_in_before_their_firm_opens_on_the_map_too():
    from engine.corporate import maybe_arrive_founder
    town = map_town("founder_arrival_rate=1.0", "invent_prob=1.0", "flow_entry_capital=0")
    landlord = premises(town, "housing", 6, 5)
    block(town, landlord, 6, 6, homes=4)
    refresh_access(town)
    firm = maybe_arrive_founder(town)
    assert firm is not None and firm.spot is not None
    founder = town.agent(firm.founder_id)
    kinds = [e["kind"] for e in town.rec.events if e["agent"] == founder.id]
    assert kinds.index("sub_start") < kinds.index("arrival") < kinds.index("firm_founded")
    assert firm.need not in founder.subs


def test_map_too_small_for_the_towns_first_day_is_refused():
    from engine.config import load_config
    from engine.town import Town
    with pytest.raises(ValueError, match="too small"):
        Town(load_config(None, ["map_width=3", "map_height=4"]))       # 12 spots; day one needs 13
    town = Town(load_config(None, ["map_width=5", "map_height=5"]))
    assert all(u.spot is not None for u in town.firms[0].units)


def test_founder_who_cannot_get_a_spot_keeps_their_capital():
    from engine.corporate import found_firm
    town = map_town("map_width=3", "map_height=3")
    for spot in town.map.spots:
        spot.kind = "service"                                  # nothing free, and nobody to buy from
    founder = town.add_agent(cash=20_000_000)
    assert found_firm(town, founder, 15_000_000, town.needs["food"]) is None
    assert founder.cash == 20_000_000
    assert town.firms == [] and founder.shares == {}
    assert [e["kind"] for e in town.rec.events].count("founding_blocked") == 1


# --- reach and time -------------------------------------------------------------------------------
from engine.corporate import transport_spec
from engine.household import review_subscriptions, update_agents
from engine.labour import labour_market
from engine.places import find_home, reach, travel_hours
from engine.subscriptions import find_provider, rent_home, subscribe, unsubscribe


def premises(town, need, x, y, price=None, customers=0):
    """A firm with its premises at (x, y) and, if asked, customers who are not looking for work."""
    firm = town.add_firm(need)
    firm.founded = -200
    spot = town.map.at(x, y)
    spot.kind, spot.owner, spot.user = "premises", firm, firm
    firm.spot = spot
    if price is not None:
        firm.price = price
    for _ in range(customers):
        a = town.add_agent()
        a.klass = "owner"
        subscribe(town, a, firm)
    return firm


def block(town, landlord, x, y, homes=8):
    spot = town.map.at(x, y)
    spot.kind, spot.owner, spot.user = "homes", landlord, landlord
    landlord.lots.append(spot)
    for _ in range(homes):
        unit = town.new_unit(landlord)
        spot.units.append(unit)
        unit.spot = spot
    return spot


def tenant(town, spot, cash=1_000_000, **fixed):
    a = town.add_agent(cash=cash, **fixed)
    free = [u for u in spot.units if u.occupant is None]
    assert subscribe(town, a, spot.user, unit=free[0])
    return a


def test_walking_reach_is_six_blocks_and_transport_makes_it_twenty_four():
    town = map_town()
    a = town.add_agent()
    assert reach(town, a) == 6
    a.subs["transport"] = object()
    assert reach(town, a) == 24


def test_time_on_the_road():
    cfg = map_town().cfg
    assert travel_hours(cfg, trips=5, blocks=6, fast=False) == pytest.approx(5.0)   # half an hour each way
    assert travel_hours(cfg, trips=5, blocks=6, fast=True) == pytest.approx(1.25)


def test_spot_counts_its_let_homes():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    spot = block(town, landlord, 0, 0, homes=3)
    a = tenant(town, spot)
    assert spot.occupied == 1 and a.unit["housing"].spot is spot
    unsubscribe(town, a, "housing", "moved")
    assert spot.occupied == 0


def test_home_search_takes_only_homes_within_reach_of_work():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    far = block(town, landlord, 0, 0)
    job = town.map.at(12, 12)
    a = town.add_agent()
    assert find_home(town, a, work=job) is None                 # 24 blocks: no walking that
    near = block(town, landlord, 11, 12)
    assert find_home(town, a, work=job).spot is near
    assert find_home(town, a).spot is far                       # no job to reach: first of equal rents


def test_job_out_of_reach_is_refused():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 0, 0, homes=1)
    a = tenant(town, home)
    firm = premises(town, "food", 12, 12, customers=10)         # ten customers, no staff: vacancies
    labour_market(town)
    assert a.role is None and firm.staff == []
    assert (a.id, "job") in town.stranded


def test_resident_moves_to_take_a_job_when_a_home_is_free_near_it():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    old = block(town, landlord, 0, 0, homes=1)
    a = tenant(town, old)
    new = block(town, landlord, 11, 12)
    firm = premises(town, "food", 12, 12, customers=10)
    labour_market(town)
    assert a.employer is firm and a.unit["housing"].spot is new
    assert old.occupied == 0 and new.occupied >= 1       # workers from outside took the homes beside them
    moves = [e for e in town.rec.events if e["kind"] == "moved_home"]
    assert len(moves) == 1 and moves[0]["data"]["reason"] == "job"


def two_jobs(far_wage, *overrides):
    """Someone out of work with a job on offer next door and another six blocks away."""
    town = map_town("switch_prob=0.0", "move_prob=0.0", *overrides)
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    a.last_wage = 50_000
    near = premises(town, "food", 1, 0, customers=10)
    far = premises(town, "entertainment", 6, 0, customers=100)
    near.wage, far.wage = 100_000, far_wage
    town.cfg.population_cap = town.population                 # nobody arrives from outside
    return town, a, near, far


def test_job_seeker_weighs_the_walk_against_the_wage():
    town, a, near, far = two_jobs(100_100)                    # a dollar a week more, an hour a day further
    labour_market(town)
    assert a.employer is near


def test_job_seeker_takes_the_far_job_when_it_pays_for_the_walk():
    town, a, near, far = two_jobs(115_000)                    # $150 more: the extra walk is weighed at about $104
    labour_market(town)
    assert a.employer is far


def test_worker_does_not_change_jobs_for_a_rise_the_longer_walk_would_eat():
    town, a, near, far = two_jobs(106_000, "search_prob=1.0")
    employ(a, near)
    a.income_week, a.spend_week = a.wage, 0                   # not squeezed: they want a real rise to move
    labour_market(town)
    assert a.employer is near                                 # 6% more pay, but the walk costs more than that
    far.wage = 125_000
    labour_market(town)
    assert a.employer is far


def test_outside_worker_needs_a_home_within_reach_of_the_job():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    landlord.upkeep_level = 0.0
    block(town, landlord, 0, 0)                                 # free homes, but a long way off
    firm = premises(town, "food", 12, 12, customers=10)
    before = town.population
    labour_market(town)
    assert town.population == before and firm.housing_blocked
    assert town.far_arrivals >= 1
    near = block(town, landlord, 12, 11)
    labour_market(town)
    arrivals = town.agents[before:]
    assert arrivals and all(a.unit["housing"].spot is near and a.employer is firm for a in arrivals)


def test_shop_out_of_reach_cannot_be_subscribed():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    premises(town, "food", 12, 12)
    assert find_provider(town, a, "food") is None
    assert (a.id, "food") in town.stranded
    local = premises(town, "food", 1, 0, price=45_000)          # dearer, but they can get there
    assert find_provider(town, a, "food") is local


def test_nearer_shop_wins_when_prices_are_close():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    far = premises(town, "food", 6, 0, price=40_000)            # six blocks
    near = premises(town, "food", 1, 0, price=40_500)           # one block, $5 dearer
    assert find_provider(town, a, "food") is near               # 100 minutes a week is worth more than $5
    near.price = 46_000
    assert find_provider(town, a, "food") is far


def homes_near_and_far_from_food():
    """Two blocks with free homes: one beside the food shop, one a ride away and cheaper to rent."""
    town, landlord, middle, edge = rent_scene()
    a = town.add_agent(cash=5_000_000)
    assert unit_rent(edge.units[0]) < unit_rent(middle.units[0])
    return town, a, middle, edge


def test_home_search_counts_the_fare_a_home_far_from_food_would_need():
    town, a, middle, edge = homes_near_and_far_from_food()
    town.needs["transport"] = transport_spec(town)
    bus = premises(town, "transport", 6, 4)
    crew(town, bus)
    bus.price = 5_000                                         # $50: the far home is still cheaper all told
    assert find_home(town, a).spot is edge
    bus.price = 20_000                                        # $200: now the home by the shop costs less
    assert find_home(town, a).spot is middle


def test_home_with_no_way_to_get_food_is_a_last_resort():
    town, a, middle, edge = homes_near_and_far_from_food()   # no transport firm in town
    assert find_home(town, a).spot is middle                  # dearer, but they can eat
    for unit in middle.units:
        unit.occupant = object()
    middle.occupied = len(middle.units)
    assert find_home(town, a).spot is edge                    # nothing else is free


def test_living_far_from_food_counts_the_fare_when_weighing_a_move():
    town, a, middle, edge = homes_near_and_far_from_food()
    town.needs["transport"] = transport_spec(town)
    bus = premises(town, "transport", 6, 4)
    crew(town, bus)
    bus.price = 20_000
    assert home_cost(town, a, edge) == unit_rent(edge.units[0]) + 20_000
    assert home_cost(town, a, middle) == unit_rent(middle.units[0])


def only_edge_homes_free():
    """Someone housed and fed in the middle; every other home there is let; no transport in town."""
    town, landlord, middle, edge = rent_scene()
    a = tenant(town, middle, cash=5_000_000)
    subscribe(town, a, town.firms_for("food")[0])
    for unit in middle.units:
        if unit.occupant is None:
            tenant(town, middle)
    return town, a, middle, edge


def test_nobody_moves_out_of_reach_of_food_for_a_cheaper_rent():
    from engine.household import consider_moving
    town, a, middle, edge = only_edge_homes_free()
    assert unit_rent(edge.units[0]) < unit_rent(middle.units[0])
    consider_moving(town, a)
    assert home_spot(a) is middle and "food" in a.subs


def test_someone_living_out_of_reach_of_food_moves_within_reach_when_they_can():
    from engine.household import consider_moving
    town, landlord, middle, edge = rent_scene()               # no transport in town
    a = tenant(town, edge, cash=5_000_000)
    consider_moving(town, a)
    assert home_spot(a) is middle                             # dearer, but they can eat
    moved = [e for e in town.rec.events if e["kind"] == "moved_home"]
    assert moved[-1]["data"]["reason"] == "food"


def test_chief_executive_is_not_bound_by_the_walk_to_their_firm_when_looking_for_a_home():
    town, landlord, middle, edge = rent_scene()               # no transport in town
    shop = premises(town, "appliances", 0, 0)                 # twelve blocks from the nearest free home
    boss = town.add_agent(cash=5_000_000)
    shop.ceo, boss.employer, boss.role = boss, shop, "ceo"
    assert find_home(town, boss).spot is middle
    worker = town.add_agent(cash=5_000_000)
    employ(worker, shop)
    assert find_home(town, worker) is None                    # anyone else must be able to get to work


def test_agent_who_loses_reach_moves_closer_if_they_can():
    town = map_town("switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    near = block(town, landlord, 11, 12)
    firm = premises(town, "food", 12, 12)
    a.employer, a.role, a.wage = firm, "staff", firm.wage
    firm.staff.append(a)
    review_subscriptions(town)
    assert a.employer is firm and a.unit["housing"].spot is near
    assert [e["data"]["reason"] for e in town.rec.events if e["kind"] == "moved_home"] == ["reach"]


def test_agent_who_loses_reach_and_cannot_move_loses_the_job():
    town = map_town("switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    firm = premises(town, "food", 12, 12)
    a.employer, a.role, a.wage = firm, "staff", firm.wage
    firm.staff.append(a)
    review_subscriptions(town)
    assert a.role is None and firm.staff == []
    lost = [e for e in town.rec.events if e["kind"] == "layoff"]
    assert lost[0]["data"]["reason"] == "out_of_reach"
    assert a in town.agents


def two_food_shops(far_price):
    """Someone who buys food next door, with another food shop six blocks away."""
    town = map_town("switch_prob=1.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1), cash=5_000_000)
    near = premises(town, "food", 1, 0, price=40_000)
    far = premises(town, "food", 6, 0, price=far_price)
    subscribe(town, a, near)
    return town, a, near, far


def test_shopper_does_not_switch_to_a_cheaper_shop_that_costs_more_all_told():
    town, a, near, far = two_food_shops(37_600)               # 6% cheaper at the till, and $42 a week more on foot
    review_subscriptions(town)
    assert a.subs["food"] is near


def test_shopper_switches_to_a_far_shop_that_is_cheaper_all_told():
    town, a, near, far = two_food_shops(30_000)
    review_subscriptions(town)
    assert a.subs["food"] is far


def test_far_shop_costs_the_fare_too_unless_the_ride_is_needed_for_work():
    town, a, food, bus = far_from_food_scene()                # a works round the corner; the food shop is a ride away
    subscribe(town, a, bus)
    near = premises(town, "food", 0, 1, price=47_000)         # dearer at the till than the far shop
    assert find_provider(town, a, "food") is near             # but the far shop means the $71.50 fare as well
    b = tenant(town, home_spot(a), cash=1_000_000)
    employ(b, food)                                           # this one rides to work anyway
    subscribe(town, b, bus)
    assert find_provider(town, b, "food") is food


def test_shop_that_falls_out_of_reach_is_dropped():
    town = map_town("switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    food = premises(town, "food", 12, 12)
    subscribe(town, a, food)
    review_subscriptions(town)
    assert "food" not in a.subs
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert ends[0]["data"]["reason"] == "out_of_reach"


def test_hours_on_the_road_are_recorded():
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    firm = premises(town, "appliances", 3, 0)
    a.employer, a.role, a.wage = firm, "staff", firm.wage
    firm.staff.append(a)
    subscribe(town, a, premises(town, "food", 0, 2))
    update_agents(town)
    # five round trips of three blocks to work, two round trips of two blocks for food
    assert a.travel_hours == pytest.approx(5 * 2 * 3 * 5 / 60 + 2 * 2 * 2 * 5 / 60)


def test_transport_lets_an_agent_keep_a_far_job():
    town = map_town("switch_prob=0.0", "move_prob=0.0")
    landlord = premises(town, "housing", 6, 5)
    a = tenant(town, block(town, landlord, 0, 0, homes=1))
    firm = premises(town, "food", 12, 12)
    a.employer, a.role, a.wage = firm, "staff", firm.wage
    firm.staff.append(a)
    town.needs["transport"] = transport_spec(town)
    bus = premises(town, "transport", 6, 7)
    crew(town, bus)
    review_subscriptions(town)                                  # no home near work: they ride instead
    assert a.employer is firm and a.subs.get("transport") is bus
    assert a.unit["housing"].spot.x == 0


# --- location rents ---------------------------------------------------------------------------------
from engine.household import dues, pay_bills
from engine.places import refresh_access, unit_rent, update_popularity
from engine.subscriptions import price_paid


def rent_scene():
    """A landlord with three blocks: beside the shops and jobs, half way out, and far out."""
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    premises(town, "food", 6, 7)
    premises(town, "entertainment", 5, 6)
    middle = block(town, landlord, 6, 6)          # a walk from every job and shop
    edge = block(town, landlord, 12, 12)          # a walk from none of them
    refresh_access(town)
    return town, landlord, middle, edge


def test_best_placed_home_costs_a_quarter_more_than_the_worst_placed_is_below():
    town, landlord, middle, edge = rent_scene()
    assert middle.access == pytest.approx(1.0) and edge.access == pytest.approx(0.0)
    # equal numbers of homes, so the firm's price is the average of the two
    assert middle.rent_factor == pytest.approx(1.25)
    assert edge.rent_factor == pytest.approx(0.75)
    assert unit_rent(middle.units[0]) == round(33_000 * 1.25)
    assert unit_rent(edge.units[0]) == round(33_000 * 0.75)


def test_a_firms_price_is_the_average_rent_of_its_homes():
    town, landlord, middle, edge = rent_scene()
    block(town, landlord, 6, 4)                   # a second well-placed block: more good homes than bad
    refresh_access(town)
    rents = [unit_rent(u) for u in landlord.units]
    assert sum(rents) / len(rents) == pytest.approx(landlord.price, abs=1)
    assert unit_rent(middle.units[0]) > landlord.price > unit_rent(edge.units[0])


def test_compact_town_pays_the_plain_price():
    town = small_town()
    housing = town.firms_for("housing")[0]
    assert all(unit_rent(u) == housing.price for u in housing.units)     # every home equally well placed


def test_tenant_pays_their_own_homes_rent():
    town, landlord, middle, edge = rent_scene()
    central = tenant(town, middle)
    outer = tenant(town, edge)
    assert price_paid(central, "housing") == 41_250 and price_paid(outer, "housing") == 24_750
    assert [d[3] for d in dues(town, central) if d[2] == "housing"] == [41_250]
    pay_bills(town)
    assert landlord.w_revenue == 41_250 + 24_750


def test_fully_let_spot_grows_more_popular_and_an_emptier_one_less():
    town, landlord, middle, edge = rent_scene()
    for _ in range(8):
        tenant(town, middle)                      # the middle block is full; the edge block is empty
    for _ in range(13):
        update_popularity(town, quarter_end=False)
    update_popularity(town, quarter_end=True)
    assert middle.popularity == pytest.approx(1.02)
    assert edge.popularity == pytest.approx(0.98)
    refresh_access(town)
    assert middle.rent_factor > 1.25 and edge.rent_factor < 0.75


def test_home_search_weighs_rent_against_time():
    town = map_town()
    landlord = premises(town, "housing", 0, 0)
    premises(town, "food", 6, 8)                  # a walk from both blocks: neither needs a ride for food
    beside = block(town, landlord, 6, 6)          # one block from the job
    further = block(town, landlord, 6, 11)        # six blocks from it: five hours a week on foot
    beside.rent_factor, further.rent_factor = 1.1, 1.0        # $33 a week dearer beside the job
    a = town.add_agent()
    assert find_home(town, a, work=town.map.at(6, 5)).spot is beside      # the walk is weighed at about $104 more
    assert find_home(town, a).spot is further                 # with no job to get to, the cheaper rent wins


def test_popularity_stops_at_its_floor_and_its_ceiling():
    town, landlord, middle, edge = rent_scene()
    for _ in range(8):
        tenant(town, middle)                      # the middle block is full; the edge block is empty
    for _ in range(40):                           # ten years of quarters
        update_popularity(town, quarter_end=False)
        update_popularity(town, quarter_end=True)
    assert middle.popularity == pytest.approx(1.25)
    assert edge.popularity == pytest.approx(0.8)


def test_once_transport_runs_a_far_spot_is_worth_something():
    town, landlord, middle, edge = rent_scene()
    assert edge.access == 0.0                     # a walk from no job and no shop
    town.needs["transport"] = transport_spec(town)
    premises(town, "transport", 6, 4)
    refresh_access(town)
    assert edge.access == pytest.approx(0.5)      # it can be reached now


def test_nobody_moves_for_a_saving_too_small_to_bother():
    from engine.household import consider_moving
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    premises(town, "food", 6, 7)
    here = block(town, landlord, 6, 6)
    there = block(town, landlord, 5, 5)
    there.rent_factor = 0.97                      # 3% cheaper: less than the 5% it takes to move
    a = tenant(town, here)
    consider_moving(town, a)
    assert home_spot(a) is here
    there.rent_factor = 0.90
    consider_moving(town, a)
    assert home_spot(a) is there


# --- land -------------------------------------------------------------------------------------------
from engine.corporate import fail_firm, found_firm, wind_up
from engine.places import asking_price, pay_ground_rents, refresh_land_values, take_spot


def full_map(*overrides):
    """A 3 by 3 town with every spot taken: two landlords' blocks and three service spots."""
    town = map_town("map_width=3", "map_height=3", *overrides)
    owner = town.add_agent(cash=50_000_000)
    dear = found_firm(town, owner, 1_000_000, town.needs["housing"])       # premises at the middle
    other = town.add_agent(cash=50_000_000)
    cheap = found_firm(town, other, 1_000_000, town.needs["housing"])
    spots = [s for s in town.map.spots if s.kind is None]
    let = block(town, dear, spots[0].x, spots[0].y, homes=8)
    for _ in range(3):
        tenant(town, let)
    for spot in spots[2:]:
        spot.kind = "service"
    refresh_access(town)
    bare = take_spot(town, cheap, "homes")                                 # the last free spot: land is now scarce
    assert bare is spots[1]
    return town, dear, cheap, let, bare


def test_land_is_free_while_spots_remain():
    town = map_town()
    founder = town.add_agent(cash=20_000_000)
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])
    taken = [e for e in town.rec.events if e["kind"] == "spot_taken"]
    assert taken[0]["data"]["price"] == 0
    assert "land_sale" not in town.ledger.week_internal
    assert not town.map.scarce


def test_land_is_scarce_from_the_week_the_map_fills_and_stays_so():
    town, dear, cheap, let, bare = full_map()
    assert town.map.full and town.map.scarce
    assert [e["kind"] for e in town.rec.events].count("land_scarce") == 1
    bare.kind = bare.owner = bare.user = None                              # a spot comes free again
    assert not town.map.full and town.map.scarce


def test_owner_asks_the_floor_for_a_bare_lot():
    town, dear, cheap, let, bare = full_map()
    assert asking_price(town, bare) == 2_500_000                           # the $20,000 floor plus a quarter


def test_owner_asks_at_least_what_the_standing_homes_are_worth():
    town, dear, cheap, let, bare = full_map()
    homes = 8 * 7_000_000                                                  # eight new homes at $70,000
    rent_roll = 3 * unit_rent(let.units[0]) * 52 * 6
    assert homes > rent_roll
    assert asking_price(town, let) == int(homes * 1.25)                    # not the price of a bare lot


def test_owner_of_old_let_homes_asks_six_years_of_their_rent():
    town, dear, cheap, let, bare = full_map()
    for unit in let.units:
        unit.age = 45 * 52                                                 # worth a fifth of new as buildings
    rent_roll = 3 * unit_rent(let.units[0]) * 52 * 6
    assert rent_roll > 8 * 1_400_000
    assert asking_price(town, let) == int(rent_roll * 1.25)


def test_buyer_pays_the_cheapest_owner():
    town, dear, cheap, let, bare = full_map()
    founder = town.add_agent(cash=20_000_000)
    before = cheap.cash
    town.ledger.start_week()
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])
    assert firm.spot is bare and bare.kind == "premises"
    assert bare.owner is firm and bare.user is firm and bare.ground_rent == 0
    assert town.ledger.week_internal["land_sale"] == 2_500_000
    assert cheap.cash == before + 2_500_000 and bare not in cheap.lots
    assert cheap.w_revenue == 0                                            # selling land is not revenue
    assert town.map.land_price == 2_500_000
    assert [e["kind"] for e in town.rec.events].count("spot_sold") == 1


def test_buyer_who_cannot_pay_leases_and_pays_ground_rent():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    founder = town.add_agent(cash=2_000_000)
    firm = found_firm(town, founder, 1_000_000, town.needs["food"])        # $10,000 will not buy a $25,000 spot
    assert firm.spot is bare and bare.user is firm and bare.owner is cheap
    assert bare.ground_rent == int(2_500_000 * 0.10 / 52)
    assert [e["kind"] for e in town.rec.events].count("lease_started") == 1
    assert town.map.land_price == 0                                        # nothing was sold: no price of land yet
    town.ledger.start_week()
    before = cheap.cash
    assert pay_ground_rents(town) == []
    assert cheap.cash == before + bare.ground_rent
    assert town.ledger.week_internal["ground_rent"] == bare.ground_rent
    assert cheap.w_revenue == bare.ground_rent and firm.w_goods == bare.ground_rent


def test_homes_pulled_down_for_premises_put_the_tenants_out_first():
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"                                                  # only the let block can be had
    tenants = [u.occupant for u in let.units if u.occupant is not None]
    homes_before = len(dear.units)
    founder = town.add_agent(cash=90_000_000)
    firm = found_firm(town, founder, 80_000_000, town.needs["food"])
    assert firm.spot is let and let.kind == "premises" and let.units == [] and let.occupied == 0
    assert len(dear.units) == homes_before - 8
    for a in tenants:
        assert "housing" not in a.subs and "housing" not in a.unit and a in town.agents
    kinds = [e["kind"] for e in town.rec.events]
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert [e["data"]["reason"] for e in ends] == ["redeveloped"] * 3
    assert kinds.index("homes_pulled_down") > max(i for i, k in enumerate(kinds) if k == "sub_end")


def founder_under_the_cheapest_roof():
    """The cheapest block in a full town is two old homes, and a founder-to-be lives in one."""
    town, dear, cheap, let, bare = full_map()
    for _ in range(2):
        unit = town.new_unit(cheap)
        unit.age = 45 * 52
        bare.units.append(unit)
        unit.spot = bare
    founder = tenant(town, bare, cash=90_000_000)
    assert asking_price(town, bare) < asking_price(town, let)
    return town, let, bare, founder


def test_firm_does_not_pull_down_its_own_founders_home_while_another_block_can_be_had():
    town, let, bare, founder = founder_under_the_cheapest_roof()
    firm = found_firm(town, founder, 80_000_000, town.needs["food"])
    assert firm.spot is let                                                # dearer, but not their own roof
    assert home_spot(founder) is bare


def test_firm_takes_its_founders_block_when_it_is_the_only_one_to_be_had():
    town, let, bare, founder = founder_under_the_cheapest_roof()
    let.reserved = 1                                                       # being built on: not for sale
    firm = found_firm(town, founder, 80_000_000, town.needs["food"])
    assert firm.spot is bare and "housing" not in founder.subs


def test_housing_firm_that_buys_homes_keeps_the_tenants():
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"
    let.units.pop()                                                        # seven homes: room for one more
    dear.units.pop()
    tenants = [u.occupant for u in let.units if u.occupant is not None]
    banker = town.add_agent(cash=90_000_000)
    town.ledger.pay(banker, cheap, 80_000_000, "founding")
    assert take_spot(town, cheap, "homes") is let
    assert let.user is cheap and let.owner is cheap and let in cheap.lots and let not in dear.lots
    assert all(u.firm is cheap and u in cheap.units and u not in dear.units for u in let.units)
    for a in tenants:
        assert a.subs["housing"] is cheap and cheap.subs[a.id] is a and a.id not in dear.subs
        assert a.unit["housing"].spot is let


def test_rebuild_of_a_home_stops_when_its_block_is_pulled_down():
    from engine.entities import Project
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"                                                  # only the let block can be had
    dear.projects.append(Project(dear.spec, let.units[0]))                 # a home on it is being rebuilt
    founder = town.add_agent(cash=90_000_000)
    found_firm(town, founder, 80_000_000, town.needs["food"])              # buys the block and pulls it down
    assert let.kind == "premises" and dear.projects == []                  # nobody rebuilds a home that is gone


def test_rebuild_of_a_home_goes_with_it_to_the_landlord_who_buys_the_block():
    from engine.entities import Project
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"
    let.units.pop()                                                        # seven homes: room for one more
    dear.units.pop()
    rebuild = Project(dear.spec, let.units[0])
    dear.projects.append(rebuild)
    banker = town.add_agent(cash=90_000_000)
    town.ledger.pay(banker, cheap, 80_000_000, "founding")
    assert take_spot(town, cheap, "homes") is let and let.owner is cheap
    assert dear.projects == [] and cheap.projects == [rebuild]


def test_firm_that_cannot_buy_a_block_of_homes_cannot_lease_it_to_pull_it_down():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    bare.kind = "service"                                                  # only the let block is left
    founder = town.add_agent(cash=20_000_000)                              # $150,000 will not buy a $700,000 block
    assert found_firm(town, founder, 15_000_000, town.needs["food"]) is None
    assert let.kind == "homes" and len(let.units) == 8 and let.user is dear
    assert founder.cash == 20_000_000
    assert not any(e["kind"] in ("lease_started", "homes_pulled_down") for e in town.rec.events)


def leased_block():
    """A landlord with little money takes another landlord's part-built block on lease."""
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    bare.kind = "service"
    let.units.pop()                                                        # seven homes: room for one more
    dear.units.pop()
    tenants = [u.occupant for u in let.units if u.occupant is not None]
    assert take_spot(town, cheap, "homes") is let
    assert let.owner is dear and let.user is cheap and let.ground_rent > 0
    return town, dear, cheap, let, tenants


def test_leased_block_goes_back_as_it_stands_when_the_landlord_leasing_it_closes():
    town, dear, cheap, let, tenants = leased_block()
    wind_up(town, cheap, "idle")
    assert let.owner is dear and let.user is dear and let.ground_rent == 0 and let in dear.lots
    assert len(let.units) == 7 and all(u.firm is dear and u in dear.units and u.spot is let for u in let.units)
    for a in tenants:
        assert a.subs["housing"] is dear and dear.subs[a.id] is a          # they never lost the home
    assert not any(e["kind"] in ("sub_end", "units_scrapped") for e in town.rec.events)


def test_lessee_absorbed_by_its_own_landlord_ends_the_lease():
    town, dear, cheap, let, tenants = leased_block()
    fail_firm(town, cheap, "payroll")                                      # the only rival is its landlord
    assert not cheap.alive and let.owner is dear and let.user is dear
    assert let.ground_rent == 0                                            # nobody pays themselves ground rent


def test_landlord_absorbed_by_a_rival_passes_on_the_land_it_leased_out():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    poor = town.add_agent(cash=2_000_000)
    shop = found_firm(town, poor, 1_000_000, town.needs["food"])           # leases the bare lot from the cheap landlord
    assert bare.owner is cheap and bare.user is shop
    rent = bare.ground_rent
    spare = next(s for s in town.map.spots if s.kind == "service")
    tenant(town, block(town, cheap, spare.x, spare.y, homes=2))            # a tenant, so the landlord is sold and not shut
    fail_firm(town, cheap, "payroll")
    assert not cheap.alive
    assert [e["data"]["buyer"] for e in town.rec.events if e["kind"] == "takeover"] == ["rival"]
    assert bare.owner is dear and bare.user is shop and bare.ground_rent == rent     # the rival is the shop's landlord now


def test_firm_that_misses_one_of_two_ground_rents_is_late():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    spare = next(s for s in town.map.spots if s.kind == "service")
    spare.kind, spare.owner, spare.user = "homes", dear, cheap             # the cheap landlord leases two lots
    cheap.lots.append(spare)
    bare.owner = dear
    spare.ground_rent = bare.ground_rent = 300_000
    cheap.cash = 400_000                                                   # enough for one of them
    for week in range(1, 5):
        late = pay_ground_rents(town)
        cheap.cash = 400_000
        assert late == ([cheap] if week == 4 else [])                      # four weeks short: now it is late


def test_firm_that_cannot_carry_eight_weeks_of_ground_rent_gets_no_spot():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    founder = town.add_agent(cash=40_000)
    assert found_firm(town, founder, 30_000, town.needs["food"]) is None   # $300; eight weeks' ground rent is $384
    assert founder.cash == 40_000 and bare.user is cheap


def test_closed_firms_spot_is_free_again_before_land_is_scarce():
    town = map_town()
    founder = town.add_agent(cash=20_000_000)
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])
    spot = firm.spot
    wind_up(town, firm, "idle")
    assert spot.kind is None and spot.owner is None and spot.user is None and firm.spot is None


def test_closed_firms_spot_is_sold_to_a_landlord_once_land_is_scarce():
    town, dear, cheap, let, bare = full_map()
    founder = town.add_agent(cash=20_000_000)
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])       # buys the bare lot
    spot = firm.spot
    richer = max((dear, cheap), key=lambda f: f.cash)
    paid = founder.cash
    wind_up(town, firm, "idle")
    assert spot.kind == "homes" and spot.owner is richer and spot.user is richer and spot.units == []
    assert spot in richer.lots
    assert founder.cash > paid + 2_000_000 - 1                             # the sale money reached the shareholder
    sold = [e for e in town.rec.events if e["kind"] == "spot_sold"]
    assert sold[-1]["amount"] == 2_000_000


def test_lease_ends_when_the_firm_using_the_land_closes():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    founder = town.add_agent(cash=2_000_000)
    firm = found_firm(town, founder, 1_000_000, town.needs["food"])
    wind_up(town, firm, "idle")
    assert bare.kind == "homes" and bare.owner is cheap and bare.user is cheap
    assert bare.ground_rent == 0 and bare in cheap.lots


def test_owned_land_is_security_and_leased_land_is_not():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    rich = town.add_agent(cash=20_000_000)
    owner_firm = found_firm(town, rich, 15_000_000, town.needs["food"])    # buys the bare lot for $25,000
    refresh_land_values(town)
    assert town.map.land_price == 2_500_000                                # what a spot last sold for
    assert owner_firm.land_value == 2_000_000                              # security is the floor price, no more
    assert town.bank.firm_credit(owner_firm) == int(0.6 * 2_000_000)
    let.units, let.occupied = [], 0                                        # a second lot comes up, taken on lease
    dear.units = []
    poor = town.add_agent(cash=2_000_000)
    tenant_firm = found_firm(town, poor, 1_000_000, town.needs["entertainment"])
    refresh_land_values(town)
    assert tenant_firm.spot.owner is dear and tenant_firm.land_value == 0
    assert town.bank.firm_credit(tenant_firm) == 0


def test_absorbed_landlords_blocks_go_to_the_rival():
    town = map_town()
    rival_owner = town.add_agent(cash=90_000_000)
    rival = found_firm(town, rival_owner, 80_000_000, town.needs["housing"])
    owner = town.add_agent(cash=2_000_000)
    failing = found_firm(town, owner, 1_000_000, town.needs["housing"])
    spot = block(town, failing, 0, 0, homes=4)
    people = [tenant(town, spot) for _ in range(2)]
    old_premises = failing.spot
    fail_firm(town, failing, "payroll")
    assert not failing.alive
    assert spot.user is rival and spot.owner is rival and spot in rival.lots
    assert all(a.subs["housing"] is rival and a.unit["housing"].spot is spot for a in people)
    assert old_premises.kind is None                                       # its office is given up
    assert all(s.owner is not failing and s.user is not failing for s in town.map.spots)


# --- transport --------------------------------------------------------------------------------------
from engine.corporate import choose_venture
from engine.household import plan_bills
from engine.labour import desired_staff
from engine.production import operate
from engine.subscriptions import has_room


def crew(town, bus, staff=7):
    """Give a transport firm its crew of six and one more, so it can carry riders."""
    for _ in range(staff):
        employ(town.add_agent(), bus)


def far_job_scene(*overrides, staffed=True):
    """A home at one corner, a job at the other, and a transport firm in the middle."""
    town = map_town("switch_prob=0.0", "move_prob=0.0", "sell_review_prob=0.0", "invest_prob=0.0",
                    *overrides)
    landlord = premises(town, "housing", 6, 5)
    home = block(town, landlord, 0, 0, homes=2)
    firm = premises(town, "food", 12, 12)
    town.needs["transport"] = transport_spec(town)
    bus = premises(town, "transport", 6, 7)
    if staffed:
        crew(town, bus)
    return town, landlord, home, firm, bus


def employ(agent, firm):
    agent.employer, agent.role, agent.wage = firm, "staff", firm.wage
    firm.staff.append(agent)


def test_someone_turned_away_by_distance_is_recorded_once_a_quarter_for_each_thing():
    from engine.places import note_stranded, tally_stranded
    town = map_town()
    a = town.add_agent()
    for _ in range(3):
        note_stranded(town, a, "food")
    note_stranded(town, a, "job")
    events = [e for e in town.rec.events if e["kind"] == "too_far"]
    assert [(e["agent"], e["data"]["what"]) for e in events] == [(a.id, "food"), (a.id, "job")]
    tally_stranded(town)                                      # a new quarter: it is news again
    note_stranded(town, a, "food")
    assert len([e for e in town.rec.events if e["kind"] == "too_far"]) == 3


def test_town_counts_what_distance_kept_people_from():
    from engine.places import note_stranded, tally_stranded
    town = map_town()
    settled_market(town)
    a, b, c = (town.add_agent() for _ in range(3))
    note_stranded(town, a, "job")
    note_stranded(town, a, "food")
    note_stranded(town, b, "food")
    note_stranded(town, b, "food")                            # the same person twice is one person
    note_stranded(town, c, "entertainment")
    town.far_arrivals = 2                                     # two outside workers who found no home in reach
    tally_stranded(town)
    assert town.reach_blocked_by == {"job": 3, "food": 2, "other": 1}
    assert town.reach_blocked_last == 5                       # three residents and the two who never came
    assert town.stranded == {} and town.far_arrivals == 0


def test_workers_turned_away_because_no_home_can_be_built_within_reach_count_towards_transport():
    from engine.production import plan_building
    town = map_town()
    landlord = premises(town, "housing", 6, 5)
    firm = premises(town, "food", 6, 7, customers=30)         # customers and no staff: it has vacancies
    near = block(town, landlord, 6, 6, homes=8)
    for _ in range(8):
        tenant(town, near).klass = "owner"                    # the one block near the job is full
    for s in town.map.spots:                                  # and every other spot within a walk is taken
        if s.kind is None and min(dist(s, f.spot) for f in town.alive_firms) <= town.cfg.walk_range:
            s.kind = "service"
    refresh_access(town)
    landlord.cash = 500_000_000
    landlord.unmet_demand = 5.0
    plan_building(town, landlord)
    assert landlord.projects == []                            # it will not build where nobody could walk from
    town.week += 1
    labour_market(town)
    blocked = [e for e in town.rec.events if e["kind"] == "arrival_blocked"]
    assert blocked and {e["data"]["reason"] for e in blocked} == {"no home within reach"}
    assert town.far_arrivals == len(blocked)


def test_nobody_has_transport_at_the_start():
    town = small_town()
    assert "transport" not in town.needs
    assert town.firms_for("transport") == []
    assert not any("transport" in a.subs for a in town.agents)


def settled_market(town):
    """The four base needs each have a seller making too little to tempt anyone else in."""
    for i, need in enumerate(("housing", "food", "appliances", "entertainment")):
        firm = premises(town, need, 4 + i, 5)
        firm.profit_hist, firm.rev_hist = [50, 50], [1_000, 1_000]


def test_enough_people_turned_away_brings_a_transport_firm():
    town = map_town("invent_prob=0.0")
    settled_market(town)
    town.reach_blocked_last = 5
    assert choose_venture(town, 20_000_000) is None           # a few turned away: not enough
    town.reach_blocked_last = 25
    spec, price = choose_venture(town, 20_000_000)
    assert spec.name == "transport" and town.needs["transport"] is spec
    assert spec.fixed_labour == 6.0 and spec.trips_per_week == 0
    assert price == round((6 / 150 + 0.01) * 100_000 * 1.1 * 1.3)
    premises(town, "transport", 6, 7)                         # once one is running, nobody starts another for this
    assert choose_venture(town, 20_000_000) is None


def transport_worth_entering(fare):
    """A town where the only thing worth starting is a second transport firm."""
    town = map_town("invent_prob=0.0")
    settled_market(town)
    town.needs["transport"] = transport_spec(town)
    bus = premises(town, "transport", 6, 7, price=fare)
    bus.profit_hist, bus.rev_hist = [300, 300], [1_000, 1_000]       # a fat margin
    return town


def test_newcomer_to_transport_undercuts_the_fare():
    town = transport_worth_entering(7_150)
    spec, price = choose_venture(town, 20_000_000)
    assert spec.name == "transport" and price == int(7_150 * 0.92)


def test_newcomer_to_transport_reckons_the_crew_in_its_costs():
    # Six crew spread over the 150 riders a firm reckons on, and the labour per rider: $55 a
    # rider a week at a $1,000 wage with overhead. It will not sell below that plus 5%.
    town = transport_worth_entering(6_000)
    spec, price = choose_venture(town, 20_000_000)
    assert spec.name == "transport" and price == 5_775
    town = transport_worth_entering(5_700)
    assert choose_venture(town, 20_000_000) is None           # no room to undercut: it stays out


def test_transport_needs_capital_like_any_firm():
    town = map_town("invent_prob=0.0")
    town.reach_blocked_last = 25
    assert choose_venture(town, 1_000_000) is None


def test_transport_runs_only_with_its_fixed_crew():
    town, landlord, home, firm, bus = far_job_scene(staffed=False)
    riders = [town.add_agent(cash=1_000_000) for _ in range(50)]
    for a in riders:
        subscribe(town, a, bus)
    for _ in range(3):
        bus.staff.append(town.add_agent())
    operate(town)
    assert len(bus.unserved) == 50                            # three is not a crew: nothing runs
    assert desired_staff(bus, town.cfg, town.week) == 7       # six for the crew, and half a worker for fifty riders
    for _ in range(4):
        bus.staff.append(town.add_agent())
    operate(town)
    assert bus.unserved == {}
    assert has_room(town, bus)


def test_worker_sleeping_rough_who_rents_a_ride_from_work_takes_the_ride():
    town, landlord, home, firm, bus = far_job_scene()         # the only free homes are a ride from the job
    a = town.add_agent(cash=1_000_000)
    employ(a, firm)
    review_subscriptions(town)
    assert home_spot(a) is home and a.employer is firm
    assert a.subs.get("transport") is bus
    start = next(e for e in town.rec.events if e["kind"] == "sub_start" and e["data"]["need"] == "transport")
    assert start["data"]["reason"] == "needed"                # taken with the home, not left to chance


def test_worker_sleeping_rough_does_not_rent_a_home_they_could_not_get_to_work_from():
    town, landlord, home, firm, bus = far_job_scene()
    a = town.add_agent(cash=80_000)                           # after food: enough for the rent, not the rent and the fare
    employ(a, firm)
    review_subscriptions(town)
    assert "food" in a.subs and home_spot(a) is None          # they stay as they are and keep the job
    assert a.employer is firm and "transport" not in a.subs


def test_transport_firm_takes_no_riders_until_it_can_carry_them():
    town, landlord, home, firm, bus = far_job_scene(staffed=False)
    assert desired_staff(bus, town.cfg, town.week) == 7       # it staffs up for its first riders before any come
    assert not has_room(town, bus)                            # nobody to run it
    crew(town, bus, 6)
    assert not has_room(town, bus)                            # the crew alone carries nobody
    crew(town, bus, 1)
    assert has_room(town, bus)
    assert transport_fare(town) == bus.price


def test_firm_still_short_of_the_crew_it_cannot_run_without_is_not_idle():
    from engine.firmops import idle_this_week
    town, landlord, home, food, bus = far_job_scene(staffed=False)
    assert not idle_this_week(bus)                            # it cannot open yet: hiring, not idle
    crew(town, bus, 6)
    assert not idle_this_week(bus)                            # the crew alone carries nobody
    crew(town, bus, 1)
    assert idle_this_week(bus)                                # open for business, and nobody rode
    bus.w_revenue = 5_000
    assert not idle_this_week(bus)
    assert idle_this_week(food)                               # an ordinary firm that earned nothing is idle


def test_rider_not_carried_for_four_weeks_running_gives_the_ride_up():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home)
    subscribe(town, a, bus)
    for _ in range(4):
        assert "transport" in a.subs                          # a bad week or three does not cost the ride
        bus.unserved = {a.id: True}
        pay_bills(town)
    assert "transport" not in a.subs
    ends = [e for e in town.rec.events if e["kind"] == "sub_end" and e["agent"] == a.id]
    assert [e["data"]["reason"] for e in ends] == ["unserved"]


def test_rider_carried_again_starts_the_count_afresh():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home)
    subscribe(town, a, bus)
    for carried in (False, False, False, True, False, False, False):
        bus.unserved = {} if carried else {a.id: True}
        pay_bills(town)
    assert "transport" in a.subs


def test_rider_who_gave_the_ride_up_and_took_it_again_starts_the_count_afresh():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home)
    subscribe(town, a, bus)
    for _ in range(3):
        bus.unserved = {a.id: True}
        pay_bills(town)
    unsubscribe(town, a, "transport", "budget")
    pay_bills(town)
    subscribe(town, a, bus)
    for _ in range(3):
        bus.unserved = {a.id: True}
        pay_bills(town)
    assert "transport" in a.subs


def test_jobless_resident_rides_to_a_far_job():
    town, landlord, home, firm, bus = far_job_scene()
    employ(town.add_agent(), landlord)                        # the landlord has the hand it needs: one job on offer
    a = tenant(town, home)
    for _ in range(10):                                       # customers, so the firm has vacancies
        c = town.add_agent()
        c.klass = "owner"
        subscribe(town, c, firm)
    labour_market(town)
    assert a.employer is firm and a.subs.get("transport") is bus
    assert a.unit["housing"].spot is home                     # no home was free near the job, so they ride


def test_agent_who_needs_transport_for_work_does_not_drop_it_to_save_money():
    town, landlord, home, firm, bus = far_job_scene()
    fun = premises(town, "entertainment", 1, 0)
    a = tenant(town, home, cash=100_000, horizon=200.0, security=0.7)      # calm
    employ(a, firm)
    a.wage = 40_000                                           # income will not cover rent, the fare and the rest
    subscribe(town, a, bus)
    subscribe(town, a, fun)
    plan_bills(town)
    assert "transport" in a.subs                              # it is how they get to work
    assert "entertainment" not in a.subs


def far_from_food_scene():
    """Someone who works round the corner from home but lives a ride away from the only food shop."""
    town, landlord, home, food, bus = far_job_scene()
    near = premises(town, "appliances", 1, 0)
    a = tenant(town, home, cash=100_000, horizon=200.0, security=0.7)      # calm
    employ(a, near)
    return town, a, food, bus


def test_agent_who_needs_transport_to_reach_food_does_not_drop_it_to_save_money():
    town, a, food, bus = far_from_food_scene()
    fun = premises(town, "entertainment", 0, 1)
    a.wage = 40_000                                           # income will not cover rent, food, the fare and the rest
    subscribe(town, a, bus)
    subscribe(town, a, food)
    subscribe(town, a, fun)
    plan_bills(town)
    assert "transport" in a.subs and "food" in a.subs         # it is how they get to the food
    assert "entertainment" not in a.subs


def test_agent_far_from_food_takes_the_ride_and_the_food_in_the_same_week():
    town, a, food, bus = far_from_food_scene()
    a.wage = 200_000
    update_agents(town)
    review_subscriptions(town)
    assert a.subs.get("transport") is bus
    assert a.subs.get("food") is food                         # not a week later


def test_agent_with_food_round_the_corner_has_no_need_of_a_ride():
    town, a, food, bus = far_from_food_scene()
    assert needs_ride(town, a)
    premises(town, "food", 0, 1)
    assert not needs_ride(town, a)


def test_ride_to_the_food_shop_in_use_is_kept_though_a_dearer_shop_is_within_a_walk():
    town, a, food, bus = far_from_food_scene()
    premises(town, "food", 0, 1, price=55_400)                # a walk away, and dearer than the far shop and the fare
    fun = premises(town, "entertainment", 1, 1)
    a.wage = 40_000
    subscribe(town, a, bus)
    subscribe(town, a, food)
    subscribe(town, a, fun)
    assert needs_ride(town, a)                                # their food comes from beyond a walk
    plan_bills(town)
    assert "transport" in a.subs and a.subs["food"] is food   # dropping the ride would have cost them the food
    assert "entertainment" not in a.subs


def test_rider_cut_off_for_unpaid_fares_does_not_ride_again_until_they_can_pay():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home, cash=0)
    employ(a, firm)
    subscribe(town, a, bus)
    for week in range(1, 5):
        town.week = week
        a.cash = 0                                            # never has the fare
        a.arrears["housing"] = 0                              # the rent is not what this test is about
        pay_bills(town)
    assert "transport" not in a.subs                          # four fares missed: cut off
    a.arrears["housing"] = 0
    review_subscriptions(town)
    assert "transport" not in a.subs                          # no fare, no ride
    assert a.employer is None                                 # and no free home near the job: it goes
    assert bus.w_revenue == 0


def test_rider_cut_off_rides_again_when_they_have_the_fare():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home, cash=1_000_000)
    employ(a, firm)
    review_subscriptions(town)                                # the job is a ride away and they can pay
    assert a.subs.get("transport") is bus and a.employer is firm


def test_fare_is_paid_after_food_and_rent_and_before_the_rest():
    town, a, food, bus = far_from_food_scene()
    fun = premises(town, "entertainment", 0, 1)
    for firm in (fun, bus, food):
        subscribe(town, a, firm)
    assert [name for _, _, name, _ in dues(town, a)] == ["food", "housing", "transport", "entertainment"]


def test_someone_lately_kept_from_a_shop_by_distance_wants_the_ride():
    from engine.places import note_stranded, wants_transport
    town, landlord, home, firm, bus = far_job_scene()
    premises(town, "food", 0, 1)                              # food round the corner: no need of a ride for that
    a = tenant(town, home)
    assert not wants_transport(town, a, bus.price)
    note_stranded(town, a, "entertainment")
    assert wants_transport(town, a, bus.price)
    town.week += 14                                           # more than a quarter ago
    assert not wants_transport(town, a, bus.price)


def test_outside_worker_housed_a_ride_from_the_job_arrives_with_the_ride():
    from engine.labour import new_worker
    town, landlord, home, firm, bus = far_job_scene()
    a = new_worker(town, firm)
    assert a is not None and home_spot(a) is home and a.subs.get("transport") is bus


def test_chief_executive_keeps_the_job_however_far_they_live():
    town, landlord, home, firm, bus = far_job_scene()         # the home is twenty-four blocks from the firm
    boss = tenant(town, home)
    firm.ceo, boss.employer, boss.role = boss, firm, "ceo"
    wind_up(town, bus, "idle")                                # and now there is no ride to be had
    review_subscriptions(town)
    assert boss.employer is firm and boss.role == "ceo"


def test_agent_with_no_use_for_transport_does_not_take_it():
    town, landlord, home, firm, bus = far_job_scene()
    near = premises(town, "appliances", 1, 0)
    premises(town, "food", 0, 1)                              # a food shop round the corner
    a = tenant(town, home, cash=5_000_000)
    employ(a, near)
    a.wage = 200_000                                          # plenty to spare, and nowhere far to go
    update_agents(town)
    review_subscriptions(town)
    assert "transport" not in a.subs


def test_agent_takes_transport_when_the_time_saved_is_worth_the_fare():
    town, landlord, home, firm, bus = far_job_scene()
    work = premises(town, "appliances", 6, 0)                 # six blocks: five hours a week on foot
    a = tenant(town, home, cash=5_000_000)
    employ(a, work)
    a.wage = 200_000
    update_agents(town)
    assert a.travel_hours == pytest.approx(5.0)
    review_subscriptions(town)                                # 3.75 hours saved is worth more than the fare
    assert a.subs.get("transport") is bus


def test_transport_closing_strands_its_riders():
    town, landlord, home, firm, bus = far_job_scene()
    a = tenant(town, home)
    employ(a, firm)
    subscribe(town, a, bus)
    review_subscriptions(town)
    assert a.employer is firm                                 # riding, they keep the job
    wind_up(town, bus, "idle")
    assert "transport" not in a.subs
    review_subscriptions(town)
    assert a.role is None                                     # no ride and no home near work: the job goes
    lost = [e for e in town.rec.events if e["kind"] == "layoff" and e["agent"] == a.id]
    assert lost[0]["data"]["reason"] == "out_of_reach"


def test_land_is_worth_nothing_as_security_while_it_is_free():
    town = map_town()
    founder = town.add_agent(cash=20_000_000)
    firm = found_firm(town, founder, 15_000_000, town.needs["food"])
    refresh_land_values(town)
    assert firm.land_value == 0 and town.bank.firm_credit(firm) == 0


def test_one_dear_sale_does_not_revalue_every_landlords_land():
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"
    founder = town.add_agent(cash=90_000_000)
    found_firm(town, founder, 80_000_000, town.needs["food"])              # pays $700,000 for the let block
    refresh_land_values(town)
    assert town.map.land_price == 70_000_000
    assert cheap.land_value == 2 * 2_000_000                               # its office and its lot, each at the floor


def twice_failed_bus(*overrides):
    """A transport firm with a rider that fails, is sold, and fails again inside the year."""
    town, landlord, home, firm, bus = far_job_scene(*overrides)
    owner = town.add_agent(cash=1_000_000)
    town.issue_shares(bus, owner, 100)
    rider = tenant(town, home)
    subscribe(town, rider, bus)
    town.add_agent(cash=50_000_000)
    fail_firm(town, bus, "payroll")
    town.week += 20
    town.add_agent(cash=80_000_000)
    fail_firm(town, bus, "payroll")
    return town, bus, rider


def test_transport_firm_that_fails_twice_in_a_year_closes_like_any_other_firm():
    town, bus, rider = twice_failed_bus("transport_can_close=true")   # the rule before 16/11
    assert not bus.alive and "transport" not in rider.subs                 # its riders are on foot again
    assert [e["kind"] for e in town.rec.events].count("takeover") == 1


def test_transport_firm_with_riders_is_always_sold_on_when_it_may_not_close():
    town, bus, rider = twice_failed_bus("transport_can_close=false")
    assert bus.alive and "transport" in rider.subs
    assert [e["kind"] for e in town.rec.events].count("takeover") == 2


def test_selling_a_block_repays_what_the_seller_then_owes_above_its_security():
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"                                                  # only the let block can be had
    town.bank.lend_firm(dear, town.bank.firm_credit(dear))                 # borrowed to the limit on its eight homes
    owed = dear.loan
    assert owed == int(0.6 * 8 * 7_000_000)
    founder = town.add_agent(cash=90_000_000)
    town.ledger.start_week()
    found_firm(town, founder, 80_000_000, town.needs["food"])              # buys the block and pulls the homes down
    limit = int(0.6 * dear.collateral(town.cfg))                           # only the land under its office is left
    assert dear.units == [] and limit == int(0.6 * 2_000_000)
    assert dear.loan == limit                                              # the bank is paid out of the price
    assert town.ledger.week_out["loan_principal"] == owed - limit


def test_seller_with_security_to_spare_keeps_the_whole_price():
    town, dear, cheap, let, bare = full_map()
    bare.kind = "service"
    founder = town.add_agent(cash=90_000_000)
    before = dear.cash
    town.ledger.start_week()
    found_firm(town, founder, 80_000_000, town.needs["food"])
    assert dear.loan == 0 and dear.cash == before + 70_000_000
    assert "loan_principal" not in town.ledger.week_out


def test_homes_on_leased_land_secure_no_loan():
    town, dear, cheap, let, bare = full_map("premises_cost=0")
    bare.kind = "service"
    let.units.pop()                                                        # seven homes: room for one more
    dear.units.pop()
    assert take_spot(town, cheap, "homes") is let                          # $10,000 will not buy it: leased
    assert let.owner is dear and let.user is cheap and let.ground_rent > 0
    refresh_land_values(town)
    assert len(cheap.units) == 7
    assert cheap.collateral(town.cfg) == cheap.land_value                  # the homes are not its to pledge
    assert dear.collateral(town.cfg) == dear.land_value                    # the owner has the ground rent instead
