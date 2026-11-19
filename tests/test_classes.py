from engine.corporate import fail_firm, found_firm
from engine.household import classify, update_agents
from engine.labour import hire, promote
from engine.subscriptions import subscribe


def firm_and_founder(town, need="food"):
    founder = town.add_agent(cash=2_000_000)
    return found_firm(town, founder, 1_000_000, town.needs[need]), founder


def test_ceo_and_executive_are_owner_class(town):
    firm, founder = firm_and_founder(town)
    exec_ = town.add_agent()
    hire(town, firm, exec_)
    promote(town, firm, exec_)
    assert classify(town, founder) == "owner"
    assert classify(town, exec_) == "owner"


def test_staff_with_shares_is_working_class(town):
    firm, founder = firm_and_founder(town)
    worker = town.add_agent()
    hire(town, firm, worker)
    town.move_shares(firm, founder, worker, 100)             # a tenth of the firm
    assert classify(town, worker) == "working"


def test_controller_of_live_firm_is_owner(town):
    firm, founder = firm_and_founder(town)
    other, _ = firm_and_founder(town)
    worker = town.add_agent()
    hire(town, other, worker)
    town.move_shares(firm, founder, worker, 600)             # 60% of the first firm
    assert classify(town, worker) == "owner"


def test_jobless_living_on_dividends_is_owner_class(town):
    firm, _ = firm_and_founder(town)
    a = town.add_agent()
    a.div_quarters = [1_144_000] * 4                         # $45,760 a year: exactly a year of the $880 basket
    assert classify(town, a) == "owner"


def test_jobless_without_dividend_cover_is_out_of_work(town):
    firm, _ = firm_and_founder(town)
    a = town.add_agent()
    a.div_quarters = [100_000] * 4
    assert classify(town, a) == "out"
    assert classify(town, town.add_agent()) == "out"


def test_founder_who_lost_the_firm_is_out_of_work(town):
    firm, founder = firm_and_founder(town)
    customer = town.add_agent()
    subscribe(town, customer, firm)
    town.add_agent(cash=50_000_000)
    fail_firm(town, firm, "payroll")
    assert classify(town, founder) == "out"


def test_class_change_is_logged_with_its_trigger(town):
    firm, founder = firm_and_founder(town)
    worker = town.add_agent()
    hire(town, firm, worker)
    update_agents(town)
    changes = {e["agent"]: e["data"] for e in town.rec.events if e["kind"] == "class_change"}
    assert changes[worker.id]["new"] == "working" and changes[worker.id]["trigger"] == "hired"
    assert changes[founder.id]["new"] == "owner"
    assert {a.klass for a in town.agents} <= {"owner", "working", "out"}
