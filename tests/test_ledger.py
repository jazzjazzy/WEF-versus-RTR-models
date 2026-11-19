import pytest

from engine.ledger import OUTSIDE, InsufficientFunds, Ledger


class Purse:
    def __init__(self, cash):
        self.cash = cash


def test_internal_payment_conserves_money():
    ledger, a, b = Ledger(), Purse(1000), Purse(0)
    ledger.pay(a, b, 300, "wage")
    assert (a.cash, b.cash) == (700, 300)
    assert ledger.net_week() == 0
    assert ledger.week_internal["wage"] == 300


def test_outside_flows_are_tallied():
    ledger, a = Ledger(), Purse(0)
    ledger.pay(OUTSIDE, a, 500, "loan")
    ledger.pay(a, OUTSIDE, 200, "import")
    assert a.cash == 300
    assert ledger.week_in["loan"] == 500
    assert ledger.week_out["import"] == 200
    assert ledger.net_week() == 300
    ledger.start_week()
    assert ledger.week_in == {} and ledger.week_out == {}
    assert ledger.total_in["loan"] == 500 and ledger.total_out["import"] == 200


def test_cannot_overdraw():
    ledger, a, b = Ledger(), Purse(100), Purse(0)
    with pytest.raises(InsufficientFunds):
        ledger.pay(a, b, 101, "wage")
    with pytest.raises(InsufficientFunds):
        ledger.pay(a, OUTSIDE, 101, "import")
    assert (a.cash, b.cash) == (100, 0)


def test_rejects_negative_and_float():
    ledger, a, b = Ledger(), Purse(100), Purse(0)
    with pytest.raises(ValueError):
        ledger.pay(a, b, -1, "wage")
    with pytest.raises(TypeError):
        ledger.pay(a, b, 1.5, "wage")
    with pytest.raises(TypeError):
        ledger.pay(a, b, True, "wage")


def test_unknown_boundary_kind_rejected():
    ledger, a, b = Ledger(), Purse(100), Purse(0)
    with pytest.raises(ValueError):
        ledger.pay(OUTSIDE, a, 10, "gift")
    with pytest.raises(ValueError):
        ledger.pay(a, OUTSIDE, 10, "tax")
    with pytest.raises(ValueError):
        ledger.pay(a, b, 10, "loan")          # a boundary kind cannot be used inside town
    assert (a.cash, b.cash) == (100, 0)


def test_zero_payment_is_a_no_op():
    ledger, a, b = Ledger(), Purse(100), Purse(0)
    ledger.pay(a, b, 0, "wage")
    assert ledger.week_internal == {}
