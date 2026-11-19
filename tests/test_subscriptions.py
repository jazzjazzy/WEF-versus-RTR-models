from engine.subscriptions import find_provider, settle_arrival, subscribe, unsubscribe, wants


def test_subscribing_to_housing_takes_a_free_home(town):
    firm = town.add_firm("housing")
    home = town.new_unit(firm)
    a = town.add_agent()
    assert subscribe(town, a, firm) is True
    assert a.subs["housing"] is firm and a.unit["housing"] is home and home.occupant is a
    assert firm.subs[a.id] is a
    b = town.add_agent()
    assert subscribe(town, b, firm) is False        # no free home
    assert "housing" not in b.subs


def test_unsubscribing_frees_the_home_and_logs_why(town):
    firm = town.add_firm("housing")
    home = town.new_unit(firm)
    a = town.add_agent()
    subscribe(town, a, firm)
    unsubscribe(town, a, "housing", "evicted")
    assert home.occupant is None and a.subs == {} and a.unit == {} and firm.subs == {}
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert ends[0]["data"]["reason"] == "evicted"
    assert a in town.agents                         # evicted, still in town


def test_cheapest_provider_with_room_wins(town):
    dear = town.add_firm("food")
    cheap = town.add_firm("food")
    cheap.price = dear.price - 1000
    a = town.add_agent()
    assert find_provider(town, a, "food") is cheap
    assert find_provider(town, a, "food", exclude=cheap) is dear
    full = town.add_firm("housing")                 # a landlord with no homes cannot take anyone
    assert find_provider(town, a, "housing") is None


def test_arrival_needs_a_vacant_home(town):
    food = town.add_firm("food")
    a = town.add_agent()
    assert settle_arrival(town, a) is False
    assert a.subs == {}
    housing = town.add_firm("housing")
    town.new_unit(housing)
    assert settle_arrival(town, a) is True
    assert set(a.subs) == {"housing", "food"}       # the base needs that have a provider


def test_invented_need_suits_only_some_agents(town):
    from engine.corporate import invent_need
    spec = invent_need(town)
    agents = [town.add_agent() for _ in range(400)]
    share = sum(wants(a, spec) for a in agents) / len(agents)
    assert abs(share - spec.appeal) < 0.1
    assert wants(agents[0], town.needs["food"]) is True


# --- a service firm takes only the customers it can serve ------------------------------------
from engine.labour import desired_staff, hire, labour_market
from engine.household import review_subscriptions
from engine.subscriptions import has_room
from conftest import empty_town


def staffed(town, need, staff, price=None):
    firm = town.add_firm(need)
    firm.founded = -200
    if price is not None:
        firm.price = price
    for _ in range(staff):
        w = town.add_agent()
        w.klass = "owner"                      # not looking for other work in these tests
        firm.staff.append(w)
        w.employer, w.role, w.wage = firm, "staff", firm.wage
    return firm


def customers(town, firm, n):
    out = []
    for _ in range(n):
        a = town.add_agent(cash=1_000_000)
        a.klass = "owner"
        assert subscribe(town, a, firm)
        out.append(a)
    return out


def test_service_firm_takes_no_more_customers_than_it_can_serve(town):
    firm = staffed(town, "food", staff=2)      # two workers feed six; a tenth more and five to get started
    customers(town, firm, 11)
    assert has_room(town, firm) is True        # the twelfth still fits: 6.25 x 1.1 + 5 = 11.9
    customers(town, firm, 1)
    assert has_room(town, firm) is False
    late = town.add_agent(cash=1_000_000)
    assert find_provider(town, late, "food") is None
    assert firm.turned_away == {late.id: True}


def test_customers_turned_away_make_the_firm_hire(town):
    firm = staffed(town, "food", staff=2)
    customers(town, firm, 12)
    base = desired_staff(firm, town.cfg, town.week)
    firm.waiting = 50                          # fifty people wanted in last week and could not get in
    assert desired_staff(firm, town.cfg, town.week) > base + 14


def test_a_firm_with_room_takes_the_customer_a_full_one_turned_away(town):
    cheap = staffed(town, "food", staff=2, price=36_000)
    dear = staffed(town, "food", staff=20, price=40_000)
    customers(town, cheap, 12)                 # the cheap one is full
    a = town.add_agent(cash=1_000_000)
    assert find_provider(town, a, "food") is dear


def test_unserved_customer_moves_to_any_seller_with_room():
    town = empty_town("switch_prob=0.0")
    cheap = staffed(town, "food", staff=2, price=36_000)
    dear = staffed(town, "food", staff=20, price=40_000)
    fed, unfed = customers(town, cheap, 2)
    cheap.unserved = {unfed.id: True}
    review_subscriptions(town)
    assert unfed.subs["food"] is dear          # dearer, but it can feed them
    assert fed.subs["food"] is cheap
    ends = [e for e in town.rec.events if e["kind"] == "sub_end"]
    assert ends[0]["data"]["reason"] == "unserved"


def test_residents_are_hired_without_a_weekly_cap(town):
    firm = town.add_firm("food")
    firm.founded = -200
    firm.export_target = 200.0                 # 28 workers' worth of export work
    jobless = [town.add_agent() for _ in range(40)]
    labour_market(town)
    assert len(firm.staff) == 28
    assert all(a.employer is firm for a in firm.staff)


def test_equal_wages_share_outside_hires():
    town = empty_town("population_cap=500")
    first = town.add_firm("food")
    second = town.add_firm("food")
    for f in (first, second):
        f.founded = -200
        f.export_target = 500.0                # both want far more staff than there are homes
    landlord = town.add_firm("housing")
    landlord.founded = -200
    landlord.upkeep_level = 0.0
    for _ in range(40):
        town.new_unit(landlord)                # one home a week, forty weeks
        labour_market(town)
    assert town.population == 40                             # one arrival for each new home
    assert len(first.staff) + len(second.staff) >= 38        # the landlord takes one or two for its office
    assert min(len(first.staff), len(second.staff)) >= 8     # not all to the firm with the lower id
