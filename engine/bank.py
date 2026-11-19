"""The bank. Backed by a federal government outside the town, it never fails
(Jason, 12/11/2026). Loans bring money in; interest and repayments leave town.

Firms borrow against physical assets only. Individuals own no assets, so they
borrow against income only, and the loan is called when the job goes.
"""

from __future__ import annotations

from .ledger import OUTSIDE


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


class Bank:
    def __init__(self, town) -> None:
        self.town = town
        self.writeoffs_week = 0
        self.writeoffs_total = 0

    def start_week(self) -> None:
        self.writeoffs_week = 0

    def _write_off(self, amount: int) -> None:
        """Lost money was already spent in town, so a write-off moves nothing."""
        self.writeoffs_week += amount
        self.writeoffs_total += amount

    # --- firms ---------------------------------------------------------------------
    def firm_credit(self, firm) -> int:
        cfg = self.town.cfg
        return max(0, int(cfg.ltv * firm.collateral(cfg)) - firm.loan)

    def lend_firm(self, firm, amount: int) -> int:
        amount = min(int(amount), self.firm_credit(firm))
        if amount <= 0:
            return 0
        town = self.town
        town.ledger.pay(OUTSIDE, firm, amount, "loan")
        firm.loan += amount
        firm.loan_pay = _ceil_div(firm.loan, town.cfg.firm_term_weeks)
        town.event("loan", firm=firm, amount=amount, balance=firm.loan)
        return amount

    def repay_excess(self, firm) -> int:
        """A firm that has sold what secured its loan pays the bank, from the money it
        has, whatever it now owes above what the rest secures."""
        town, cfg = self.town, self.town.cfg
        excess = firm.loan - int(cfg.ltv * firm.collateral(cfg))
        paid = max(0, min(excess, firm.cash))
        if paid > 0:
            town.ledger.pay(firm, OUTSIDE, paid, "loan_principal")
            firm.loan -= paid
            town.event("sale_repaid", firm=firm, amount=paid, balance=firm.loan)
        return paid

    def service_firm(self, firm) -> bool:
        """Weekly interest and principal. True if paid in full."""
        if firm.loan <= 0:
            firm.loan_missed = 0
            return True
        town, cfg = self.town, self.town.cfg
        interest = round(firm.loan * cfg.firm_rate / cfg.weeks_per_year)
        principal = min(firm.loan, firm.loan_pay)
        if firm.cash >= interest + principal:
            town.ledger.pay(firm, OUTSIDE, interest, "loan_interest")
            town.ledger.pay(firm, OUTSIDE, principal, "loan_principal")
            firm.loan -= principal
            firm.w_interest += interest
            firm.loan_missed = 0
            return True
        paid = min(firm.cash, interest)
        town.ledger.pay(firm, OUTSIDE, paid, "loan_interest")
        firm.w_interest += paid
        firm.loan += interest - paid          # unpaid interest is added to the loan
        firm.loan_missed += 1
        town.event("loan_missed", firm=firm, amount=interest + principal, missed=firm.loan_missed)
        return False

    def recover(self, firm, proceeds_holder, amount: int) -> int:
        """Take sale proceeds from a failed firm's buyer against its debt; write off the rest."""
        take = min(amount, firm.loan)
        self.town.ledger.pay(proceeds_holder, OUTSIDE, take, "loan_recovery")
        firm.loan -= take
        return take

    def write_down(self, firm, to_amount: int) -> int:
        """Cut a failed firm's debt to what its units can secure. The rest is the bank's loss."""
        lost = firm.loan - max(0, to_amount)
        if lost <= 0:
            return 0
        firm.loan -= lost
        self._write_off(lost)
        self.town.event("writeoff", firm=firm, amount=lost)
        return lost

    def write_off_firm(self, firm) -> int:
        lost = firm.loan
        if lost > 0:
            self._write_off(lost)
            self.town.event("writeoff", firm=firm, amount=lost)
            firm.loan = 0
        return lost

    # --- individuals -------------------------------------------------------------------
    def person_credit(self, agent) -> int:
        town, cfg = self.town, self.town.cfg
        if agent.role is None or agent.loan_called or town.week < agent.credit_block_until:
            return 0
        return max(0, int(cfg.personal_limit_weeks * agent.wage) - agent.loan)

    def lend_person(self, agent, amount: int) -> int:
        amount = min(int(amount), self.person_credit(agent))
        if amount <= 0:
            return 0
        town = self.town
        town.ledger.pay(OUTSIDE, agent, amount, "loan")
        agent.loan += amount
        agent.loan_pay = _ceil_div(agent.loan, town.cfg.personal_term_weeks)
        town.event("loan", agent=agent, amount=amount, balance=agent.loan)
        return amount

    def service_person(self, agent) -> bool:
        """The weekly instalment on a loan that has not been called."""
        if agent.loan <= 0:
            agent.loan_missed = 0
            return True
        town, cfg = self.town, self.town.cfg
        interest = round(agent.loan * cfg.personal_rate / cfg.weeks_per_year)
        principal = min(agent.loan, agent.loan_pay)
        if agent.cash >= interest + principal:
            town.ledger.pay(agent, OUTSIDE, interest, "loan_interest")
            town.ledger.pay(agent, OUTSIDE, principal, "loan_principal")
            agent.loan -= principal
            agent.loan_missed = 0
            return True
        paid = min(agent.cash, interest)
        town.ledger.pay(agent, OUTSIDE, paid, "loan_interest")
        agent.loan += interest - paid
        agent.loan_missed += 1
        town.event("loan_missed", agent=agent, amount=interest + principal, missed=agent.loan_missed)
        if agent.loan_missed >= cfg.call_grace_weeks:
            self.call(agent)
        return False

    # --- homes (the Right to Repair world, 16/11/2026) -------------------------------------------
    def home_first_payment(self, amount: int) -> int:
        """The first week's payment on a loan against a home: the instalment and a week's interest."""
        cfg = self.town.cfg
        return _ceil_div(amount, cfg.mortgage_weeks) + round(amount * cfg.firm_rate / cfg.weeks_per_year)

    def home_credit(self, agent, price: int, owned: int = 0) -> int:
        """What the bank will still lend this person against a home of this price: up to
        `mortgage_ltv` of it (all of it since 18/11/2026), less what they owe, and no more than their income allows
        (Jason: the payment must fit their income; no income, no loan). `owned` is the value
        of the homes they already own: the loan is one loan on all their homes."""
        most = int(self.town.cfg.mortgage_ltv * (price + owned))
        return max(0, min(most, self.home_cap(agent)) - agent.home_loan)

    def home_cap(self, agent) -> int:
        """The most this person's income lets them owe against a home: the largest loan whose
        first payment is within `mortgage_income_share` of their income. Nothing while the
        bank refuses them credit, or with no income."""
        if self.town.week < agent.credit_block_until:
            return 0
        return self.home_cap_income(agent.income_estimate())

    def home_cap_income(self, income: int) -> int:
        """`home_cap` for an income of this much a week (a newcomer's is the wage of the job they
        come for)."""
        cfg = self.town.cfg
        afford = cfg.mortgage_income_share * income
        if afford <= 0:
            return 0
        per_cent = 1.0 / cfg.mortgage_weeks + cfg.firm_rate / cfg.weeks_per_year
        low, high = 0, int(afford / per_cent) + 1        # the payment never falls as the loan grows
        while low < high:
            mid = (low + high + 1) // 2
            if self.home_first_payment(mid) <= afford:
                low = mid
            else:
                high = mid - 1
        return low

    def lend_home(self, agent, amount: int, price: int, log: bool = True, owned: int = 0) -> int:
        """Lend against a home. `log=False` for the weekly draws of a build: the home's
        `home_built` event carries the loan. `owned`: the value of homes they already own."""
        amount = min(int(amount), self.home_credit(agent, price, owned))
        if amount <= 0:
            return 0
        town = self.town
        town.ledger.pay(OUTSIDE, agent, amount, "loan")
        agent.home_loan += amount
        agent.home_pay = _ceil_div(agent.home_loan, town.cfg.mortgage_weeks)
        if log:
            town.event("home_loan", agent=agent, amount=amount, balance=agent.home_loan)
        return amount

    def service_home(self, agent) -> bool:
        """The week's interest and instalment on a loan against a home. True if paid in full.
        A missed week adds the unpaid interest to the loan and is a blow, as a missed rent is."""
        if agent.home_loan <= 0:
            agent.home_missed = 0
            return True
        town, cfg = self.town, self.town.cfg
        interest = round(agent.home_loan * cfg.firm_rate / cfg.weeks_per_year)
        principal = min(agent.home_loan, agent.home_pay)
        if agent.cash >= interest + principal:
            town.ledger.pay(agent, OUTSIDE, interest, "loan_interest")
            town.ledger.pay(agent, OUTSIDE, principal, "loan_principal")
            agent.home_loan -= principal
            agent.home_missed = 0
            return True
        paid = min(agent.cash, interest)
        town.ledger.pay(agent, OUTSIDE, paid, "loan_interest")
        agent.home_loan += interest - paid
        agent.home_missed += 1
        town.event("home_loan_missed", agent=agent, amount=interest + principal, missed=agent.home_missed)
        agent.shock(cfg, cfg.shock_missed)
        return False

    # --- side hustles (the Right to Repair world, stage 2) -------------------------------------------
    def lend_hustle(self, hustle, amount: int) -> int:
        """Lend on a side hustle's profit (Jason: "loans is to make it a business ... if the bank
        thinks it's profitable"). Unsecured, to its owner, over `hustle_loan_term_weeks`."""
        amount = int(amount)
        if amount <= 0:
            return 0
        town = self.town
        town.ledger.pay(OUTSIDE, hustle, amount, "loan")             # into the business, not its owner's pocket
        hustle.reserve += amount
        hustle.loan += amount
        hustle.loan_pay = _ceil_div(hustle.loan, town.cfg.hustle_loan_term_weeks)
        town.event("hustle_loan", agent=hustle.owner, amount=amount, balance=hustle.loan)
        return amount

    def service_hustle(self, hustle) -> bool:
        """The week's interest (at the rate firms pay) and instalment: out of what the bank
        lent the business while any is left, then from its owner's cash. True if paid in
        full. A missed week adds the unpaid interest to the loan."""
        if hustle.loan <= 0:
            hustle.loan_missed = 0
            return True
        town, cfg, owner = self.town, self.town.cfg, hustle.owner
        interest = round(hustle.loan * cfg.firm_rate / cfg.weeks_per_year)
        principal = min(hustle.loan, hustle.loan_pay)
        if hustle.cash + owner.cash >= interest + principal:
            self._fund(hustle, interest + principal)
            town.ledger.pay(hustle, OUTSIDE, interest, "loan_interest")
            town.ledger.pay(hustle, OUTSIDE, principal, "loan_principal")
            hustle.reserve = min(hustle.reserve, hustle.cash)
            hustle.loan -= principal
            hustle.loan_missed = 0
            return True
        self._fund(hustle, interest)                 # what there is goes to the interest, and no more of the owner's
        paid = min(hustle.cash, interest)
        town.ledger.pay(hustle, OUTSIDE, paid, "loan_interest")
        hustle.reserve = min(hustle.reserve, hustle.cash)
        hustle.loan += interest - paid
        hustle.loan_missed += 1
        town.event("hustle_loan_missed", agent=owner, amount=interest + principal, missed=hustle.loan_missed)
        owner.shock(cfg, cfg.shock_missed)
        return False

    def _fund(self, hustle, amount: int) -> None:
        """Bring what is in the business up to `amount` out of its owner's cash, as far as that goes."""
        short = amount - hustle.cash
        if short > 0:
            self.town.ledger.pay(hustle.owner, hustle, min(short, hustle.owner.cash), "maker_capital")

    def settle_hustle(self, hustle) -> int:
        """A side hustle stops while it owes: its owner pays what cash they have toward the
        loan, the rest is written off, and they are refused credit as after a personal
        default. Returns what was written off."""
        town, cfg, owner = self.town, self.town.cfg, hustle.owner
        self._fund(hustle, hustle.loan)
        pay = min(hustle.cash, hustle.loan)
        town.ledger.pay(hustle, OUTSIDE, pay, "loan_principal")
        lost = hustle.loan - pay
        hustle.loan = hustle.loan_pay = hustle.loan_missed = 0
        hustle.reserve = 0                           # whatever is left in the business is its owner's now
        if lost > 0:
            self._write_off(lost)
            owner.credit_block_until = town.week + cfg.default_block_weeks
            owner.shock(cfg, cfg.shock_default)
            town.event("default", agent=owner, amount=lost, what="side hustle")
        return lost

    def call(self, agent) -> bool:
        """The job has gone (or instalments stopped): the whole loan falls due."""
        if agent.loan <= 0 or agent.loan_called:
            return False
        agent.loan_called = True
        agent.called_weeks = 0
        self.town.event("loan_called", agent=agent, amount=agent.loan)
        return True

    def reinstate(self, agent) -> None:
        """Back in work before the grace ran out: the loan returns to instalments."""
        if agent.loan_called:
            agent.loan_called = False
            agent.called_weeks = 0
            agent.loan_missed = 0
            agent.loan_pay = _ceil_div(agent.loan, self.town.cfg.personal_term_weeks)

    def weekly_called(self, agent):
        """A called loan takes whatever cash the agent has. Unpaid after the grace, it is
        written off and the agent is refused credit. Returns 'repaid', 'default' or None."""
        if not agent.loan_called:
            return None
        town, cfg = self.town, self.town.cfg
        interest = round(agent.loan * cfg.personal_rate / cfg.weeks_per_year)
        agent.loan += interest
        pay = min(agent.cash, agent.loan)
        interest_part = min(pay, interest)
        town.ledger.pay(agent, OUTSIDE, interest_part, "loan_interest")
        town.ledger.pay(agent, OUTSIDE, pay - interest_part, "loan_principal")
        agent.loan -= pay
        if agent.loan <= 0:
            agent.loan = 0
            agent.loan_called = False
            agent.called_weeks = 0
            town.event("loan_repaid", agent=agent, amount=pay)
            return "repaid"
        agent.called_weeks += 1
        if agent.called_weeks >= cfg.call_grace_weeks:
            lost = agent.loan
            self._write_off(lost)
            agent.loan = 0
            agent.loan_called = False
            agent.called_weeks = 0
            agent.credit_block_until = town.week + cfg.default_block_weeks
            town.event("default", agent=agent, amount=lost)
            return "default"
        return None
