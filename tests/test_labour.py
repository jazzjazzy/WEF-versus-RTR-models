import pytest

from engine.labour import demote, hire, promote, separate


def test_hire_sets_role_wage_and_logs(town):
    firm = town.add_firm("food")
    a = town.add_agent()
    a.security = 0.5
    hire(town, firm, a)
    assert a.employer is firm and a.role == "staff" and a.wage == firm.wage
    assert firm.staff == [a]
    assert a.security == pytest.approx(0.6)
    assert [e["kind"] for e in town.rec.events] == ["hire"]


def test_job_loss_drops_security_more_for_the_loss_averse(town):
    firm = town.add_firm("food")
    mild = town.add_agent(loss_aversion=1.0)
    sharp = town.add_agent(loss_aversion=4.0)
    for a in (mild, sharp):
        a.security = 0.8
        hire(town, firm, a)
        a.security = 0.8
        separate(town, a, "laid_off")
    assert mild.security == pytest.approx(0.8 - 0.20 * 1.0 / 2.0)
    assert sharp.security == pytest.approx(0.8 - 0.20 * 4.0 / 2.0)
    assert mild.role is None and mild.employer is None and firm.staff == []
    assert mild.last_wage == firm.wage


def test_layoff_calls_the_loan(town):
    firm = town.add_firm("food")
    a = town.add_agent()
    hire(town, firm, a)
    town.bank.lend_person(a, 300_000)
    separate(town, a, "laid_off")
    assert a.loan_called
    kinds = [e["kind"] for e in town.rec.events]
    assert kinds.count("layoff") == 1 and kinds.count("loan_called") == 1


def test_moving_jobs_does_not_call_the_loan(town):
    old, new = town.add_firm("food"), town.add_firm("food")
    a = town.add_agent()
    hire(town, old, a)
    town.bank.lend_person(a, 300_000)
    separate(town, a, "moved")
    hire(town, new, a)
    assert not a.loan_called and a.employer is new
    assert [e["kind"] for e in town.rec.events].count("quit") == 1


def test_rehired_within_grace_puts_loan_back_on_instalments(town):
    firm = town.add_firm("food")
    a = town.add_agent()
    hire(town, firm, a)
    town.bank.lend_person(a, 300_000)
    separate(town, a, "laid_off")
    hire(town, firm, a)
    assert not a.loan_called and a.loan == 300_000


def test_promotion_and_demotion_change_role_and_pay(town):
    firm = town.add_firm("food")
    a = town.add_agent()
    hire(town, firm, a)
    promote(town, firm, a)
    assert a.role == "exec" and a.wage == int(firm.wage * 2.5)
    assert firm.execs == [a] and firm.staff == []
    demote(town, firm, a)
    assert a.role == "staff" and a.wage == firm.wage and firm.staff == [a] and firm.execs == []
    kinds = [e["kind"] for e in town.rec.events]
    assert kinds.count("promotion") == 1 and kinds.count("demotion") == 1


# --- the weekly labour market ------------------------------------------------------------------
from engine.labour import adjust_executives, desired_staff, labour_market, new_worker
from engine.subscriptions import subscribe
from conftest import empty_town


def busy_firm(town, need="food", customers=10):
    """A firm with customers who are not looking for work, so its vacancies stay open."""
    firm = town.add_firm(need)
    firm.founded = -100                       # not a start-up
    for _ in range(customers):
        a = town.add_agent()
        a.klass = "owner"
        subscribe(town, a, firm)
    return firm


def landlord(town, homes):
    firm = town.add_firm("housing")
    firm.founded = -100
    firm.upkeep_level = 0.0                   # no upkeep, so it wants no staff of its own
    for _ in range(homes):
        town.new_unit(firm)
    return firm


def test_staff_needed_follows_the_work(town):
    firm = busy_firm(town, customers=10)
    # 10 customers plus 3% growth: 1.854 workers serving and 1.442 making their goods
    assert desired_staff(firm, town.cfg) == 4
    firm.make_mode = "import"
    assert desired_staff(firm, town.cfg) == 2
    firm.export_target = 100.0                # 100 units a week for export is 14 more workers
    assert desired_staff(firm, town.cfg) == 16


def test_outside_worker_needs_a_vacant_home(town):
    firm = busy_firm(town)
    housing = landlord(town, homes=2)
    before = town.population
    labour_market(town)
    arrivals = town.agents[before:]
    assert len(arrivals) == 2                 # three wanted this week; only two homes
    assert all(a.origin == "worker" and a.employer is firm and a.subs["housing"] is housing
               for a in arrivals)
    assert firm.housing_blocked is True
    assert housing.unmet_demand == 1.0
    assert [e["kind"] for e in town.rec.events].count("arrival_blocked") == 1


def test_outside_worker_needs_the_outside_wage(town):
    firm = busy_firm(town)
    landlord(town, homes=5)
    firm.wage = town.cfg.outside_wage - 1
    before = town.population
    labour_market(town)
    assert town.population == before


def test_cap_stops_arrivals():
    town = empty_town("population_cap=10")
    busy_firm(town)                           # ten residents: the town is full
    landlord(town, homes=5)
    labour_market(town)
    assert town.population == 10
    assert new_worker(town) is None


def test_unfilled_vacancy_raises_wage_after_two_weeks():
    town = empty_town("population_cap=10")
    firm = busy_firm(town)
    labour_market(town)
    assert firm.wage == 100_000
    labour_market(town)
    assert firm.wage == 102_000
    assert [e["kind"] for e in town.rec.events].count("wage_change") == 1


def test_no_wage_rise_when_the_block_is_housing(town):
    firm = busy_firm(town)                    # under the cap, but no home is free
    for _ in range(4):
        labour_market(town)
    assert firm.wage == 100_000


def test_layoff_is_last_hired_first(town):
    firm = town.add_firm("food")
    firm.founded = -100
    staff = [town.add_agent() for _ in range(10)]
    for a in staff:
        hire(town, firm, a)
    labour_market(town)                       # no customers, no work
    assert staff[-1].role is None and staff[-1].last_trigger == "laid_off"
    assert len(firm.staff) == 9 and firm.staff == staff[:9]


def test_executives_promoted_by_skill_one_per_25_staff(town):
    firm = town.add_firm("food")
    staff = [town.add_agent(skill=i / 100) for i in range(52)]
    for a in staff:
        hire(town, firm, a)
    adjust_executives(town, firm)
    assert firm.execs == [staff[51], staff[50]]     # 52 people: two executives, the most skilled
    assert len(firm.staff) == 50
    for a in list(firm.staff[:30]):
        separate(town, a, "laid_off")
    adjust_executives(town, firm)                   # 22 people left: none
    assert firm.execs == [] and len(firm.staff) == 22


def test_secure_jobless_agent_holds_out_and_stressed_one_takes_the_job(town):
    firm = busy_firm(town)
    firm.wage = 80_000
    secure = town.add_agent()
    secure.last_wage, secure.security = 100_000, 0.9
    stressed = town.add_agent()
    stressed.last_wage, stressed.security = 100_000, 0.2
    labour_market(town)
    assert secure.role is None and stressed.employer is firm
    refused = [e for e in town.rec.events if e["kind"] == "offer_refused"]
    assert len(refused) == 1 and refused[0]["agent"] == secure.id


def test_reservation_wage_falls_with_weeks_out_of_work(town):
    firm = busy_firm(town)
    firm.wage = 80_000
    a = town.add_agent()
    a.last_wage, a.security, a.weeks_out = 100_000, 0.9, 4      # 0.9 x (1 - 4 x 0.05) = 72%
    labour_market(town)
    assert a.employer is firm


def test_squeezed_worker_moves_for_any_rise():
    town = empty_town("search_prob=1.0", "search_prob_squeezed=1.0", "population_cap=30")
    old = busy_firm(town)
    new = busy_firm(town)
    new.wage = 101_000
    content, squeezed = town.add_agent(), town.add_agent()
    for a in (content, squeezed):
        hire(town, old, a)
    squeezed.income_week, squeezed.spend_week = 100_000, 120_000
    labour_market(town)
    assert content.employer is old            # 1% is not worth the move
    assert squeezed.employer is new           # unless the bills are not being met
