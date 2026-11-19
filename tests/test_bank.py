from engine.ledger import OUTSIDE


def housing_firm(town, homes):
    firm = town.add_firm("housing")
    for _ in range(homes):
        town.new_unit(firm)
    return firm


def worker(town, wage=100_000, cash=0):
    a = town.add_agent(cash=cash)
    a.role, a.wage = "staff", wage
    return a


def test_firm_borrows_up_to_60pct_of_asset_value(town):
    firm = housing_firm(town, 10)
    # a new home costs 30 worker-weeks at $1,000 plus 500 units of materials at $80 = $70,000
    assert firm.collateral(town.cfg) == 70_000_000
    assert town.bank.firm_credit(firm) == 42_000_000
    lent = town.bank.lend_firm(firm, 100_000_000)
    assert lent == 42_000_000
    assert (firm.loan, firm.cash) == (42_000_000, 42_000_000)
    assert town.ledger.week_in["loan"] == 42_000_000
    assert town.bank.firm_credit(firm) == 0


def test_firm_without_assets_cannot_borrow(town):
    firm = town.add_firm("food")
    assert town.bank.firm_credit(firm) == 0
    assert town.bank.lend_firm(firm, 1_000_000) == 0
    assert firm.loan == 0 and firm.cash == 0


def test_person_borrows_up_to_eight_weeks_wages(town):
    a = worker(town)
    assert town.bank.person_credit(a) == 800_000
    assert town.bank.lend_person(a, 1_000_000) == 800_000
    assert (a.loan, a.cash) == (800_000, 800_000)
    assert town.bank.person_credit(a) == 0


def test_unemployed_person_cannot_borrow(town):
    a = town.add_agent(cash=0)
    assert town.bank.person_credit(a) == 0
    assert town.bank.lend_person(a, 100_000) == 0


def test_interest_and_principal_leave_town(town):
    firm = housing_firm(town, 20)
    town.bank.lend_firm(firm, 52_000_000)
    before = town.money_in_town()
    assert town.bank.service_firm(firm) is True
    # 6% a year on $520,000 is $600 a week; a ten-year loan repays $1,000 a week
    assert town.ledger.week_out["loan_interest"] == 60_000
    assert town.ledger.week_out["loan_principal"] == 100_000
    assert firm.loan == 51_900_000
    assert town.money_in_town() == before - 160_000


def test_firm_that_cannot_pay_misses_and_interest_is_added_to_the_loan(town):
    firm = housing_firm(town, 20)
    town.bank.lend_firm(firm, 52_000_000)
    other = town.add_agent()
    town.ledger.pay(firm, other, firm.cash, "wage")
    assert town.bank.service_firm(firm) is False
    assert firm.loan_missed == 1
    assert firm.loan == 52_060_000


def test_called_loan_written_off_after_grace_and_credit_blocked(town):
    a = worker(town)
    town.bank.lend_person(a, 800_000)
    other = town.add_agent()
    town.ledger.pay(a, other, 800_000, "subscription")      # the money is spent in town
    a.role, a.wage = None, 0                                # the job goes
    town.bank.call(a)
    assert a.loan_called
    before = town.money_in_town()
    outcomes = []
    for _ in range(town.cfg.call_grace_weeks):
        town.week += 1
        outcomes.append(town.bank.weekly_called(a))
    assert outcomes[-1] == "default"
    assert a.loan == 0 and not a.loan_called
    assert a.credit_block_until == town.week + 156
    assert town.money_in_town() == before                   # a write-off moves no money
    assert town.bank.writeoffs_total >= 800_000
    assert [e["kind"] for e in town.rec.events].count("default") == 1
    a.role, a.wage = "staff", 100_000                       # back in work, still refused
    assert town.bank.person_credit(a) == 0


def test_called_loan_is_repaid_from_cash_and_closes(town):
    a = worker(town, cash=2_000_000)
    town.bank.lend_person(a, 500_000)
    a.role, a.wage = None, 0
    town.bank.call(a)
    assert town.bank.weekly_called(a) == "repaid"
    assert a.loan == 0 and not a.loan_called
    assert town.ledger.week_out["loan_principal"] == 500_000
