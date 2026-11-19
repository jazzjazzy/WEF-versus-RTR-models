"""Small operations on a firm that several parts of the model share."""

from __future__ import annotations

from .production import export_target


def idle_this_week(firm) -> bool:
    """Did the firm earn nothing and build nothing this week, though it was able to trade?
    A firm still short of the crew it cannot run without is hiring, not idle."""
    if firm.w_revenue != 0 or firm.w_export != 0 or firm.projects:
        return False
    fixed = firm.spec.fixed_labour
    return not (fixed > 0 and len(firm.staff) <= fixed)


def set_price(town, firm, new: int, reason: str) -> None:
    """Change the weekly price. A rise is a blow to every customer's security."""
    old = firm.price
    new = max(1, int(new))
    if new == old:
        return
    firm.price = new
    town.event("price_change", firm=firm, amount=new, old=old, reason=reason)
    if new > old:
        cfg = town.cfg
        for agent in firm.subs.values():
            income = max(1, agent.income_estimate())
            agent.shock(cfg, cfg.shock_price_scale * (new - old) / income)


def sync_pay(town, firm) -> None:
    """Bring everyone's pay into line with the firm's wage and size. Where its staff keep
    rates of their own (RTR; Jason, 19/11/2026: "Old staff members still stay on the same pay
    rate"), a rise lifts those under the new rate and a cut touches nobody already there."""
    cfg = town.cfg
    for a in firm.staff:
        if not firm.own_rates or a.wage < firm.wage:
            a.wage = firm.wage
    exec_pay = firm.exec_pay(cfg)
    for a in firm.execs:
        a.wage = exec_pay
    if firm.ceo is not None:
        firm.ceo.wage = firm.ceo_pay(cfg)


def set_wage(town, firm, new: int, reason: str) -> None:
    old = firm.wage
    new = max(1, int(new))
    if new == old:
        return
    firm.wage = new
    sync_pay(town, firm)
    # Exporting has to pay at the firm's wage (what those it would take on to make the goods are
    # paid), so the decision follows every change of it.
    firm.export_target = export_target(town.cfg, firm, len(town.firms_for(firm.need)))
    town.event("wage_change", firm=firm, amount=new, old=old, reason=reason)


def appoint_ceo(town, firm, agent) -> None:
    agent.employer = firm
    agent.role = "ceo"
    agent.wage = firm.ceo_pay(town.cfg)
    agent.weeks_out = 0
    agent.hired_week = town.week
    firm.ceo = agent
    town.bank.reinstate(agent)
    agent.last_trigger = "became_ceo"
    town.event("ceo_appointed", agent=agent, firm=firm, amount=agent.wage)
