"""Every movement of money goes through Ledger.pay.

Money crosses the town boundary in exactly five ways (Jason, 12/11/2026):
in as arrivals' capital, bank loans and exports; out as loan repayments
(principal, interest, recoveries from failed firms) and imports.
"""

from __future__ import annotations


class _Outside:
    __slots__ = ()

    def __repr__(self) -> str:
        return "OUTSIDE"


OUTSIDE = _Outside()

IN_KINDS = frozenset({"arrival", "loan", "export"})
OUT_KINDS = frozenset({"loan_principal", "loan_interest", "loan_recovery", "import"})


class InsufficientFunds(Exception):
    pass


class Ledger:
    def __init__(self) -> None:
        self.week_in: dict[str, int] = {}
        self.week_out: dict[str, int] = {}
        self.week_internal: dict[str, int] = {}
        self.total_in: dict[str, int] = {}
        self.total_out: dict[str, int] = {}

    def start_week(self) -> None:
        self.week_in = {}
        self.week_out = {}
        self.week_internal = {}

    def net_week(self) -> int:
        """Money that entered town this week minus money that left."""
        return sum(self.week_in.values()) - sum(self.week_out.values())

    def pay(self, src, dst, amount: int, kind: str) -> None:
        if type(amount) is not int:
            raise TypeError(f"money must be whole cents, got {amount!r}")
        if amount < 0:
            raise ValueError(f"negative payment: {amount}")
        if src is OUTSIDE and dst is OUTSIDE:
            raise ValueError("payment from outside to outside")
        if src is OUTSIDE:
            if kind not in IN_KINDS:
                raise ValueError(f"money cannot enter town as {kind!r}")
        elif dst is OUTSIDE:
            if kind not in OUT_KINDS:
                raise ValueError(f"money cannot leave town as {kind!r}")
        elif kind in IN_KINDS or kind in OUT_KINDS:
            raise ValueError(f"{kind!r} is a boundary kind, not a payment inside town")
        if amount == 0:
            return
        if src is OUTSIDE:
            dst.cash += amount
            self.week_in[kind] = self.week_in.get(kind, 0) + amount
            self.total_in[kind] = self.total_in.get(kind, 0) + amount
            return
        if src.cash < amount:
            raise InsufficientFunds(f"{kind}: needs {amount}, has {src.cash}")
        src.cash -= amount
        if dst is OUTSIDE:
            self.week_out[kind] = self.week_out.get(kind, 0) + amount
            self.total_out[kind] = self.total_out.get(kind, 0) + amount
        else:
            dst.cash += amount
            self.week_internal[kind] = self.week_internal.get(kind, 0) + amount
