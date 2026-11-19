"""The share broker: a weekly auction per firm. Its service is free (Jason, 12/11/2026)."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from itertools import accumulate


def clearing_price(bids, asks, ref: int):
    """The single positive price that trades the most shares.

    bids and asks are lists of (limit price, quantity). A bid trades at any price
    at or below its limit, an ask at any price at or above its limit. Ties go to
    the price nearest the last trade `ref`, then to the lower price.
    Returns (price, volume) or None when nothing can trade.
    """
    if not bids or not asks:
        return None
    bid_sorted = sorted(bids)
    ask_sorted = sorted(asks)
    bid_limits = [p for p, _ in bid_sorted]
    ask_limits = [p for p, _ in ask_sorted]
    bid_cum = [0] + list(accumulate(q for _, q in bid_sorted))
    ask_cum = [0] + list(accumulate(q for _, q in ask_sorted))
    total_bid = bid_cum[-1]
    candidates = {p for p in bid_limits if p > 0} | {p for p in ask_limits if p > 0}
    if ref > 0:
        candidates.add(ref)
    best = None
    for p in sorted(candidates):
        demand = total_bid - bid_cum[bisect_left(bid_limits, p)]
        supply = ask_cum[bisect_right(ask_limits, p)]
        volume = min(demand, supply)
        if volume <= 0:
            continue
        key = (volume, -abs(p - ref), -p)
        if best is None or key > best[0]:
            best = (key, p, volume)
    if best is None:
        return None
    return best[1], best[2]


class Order:
    __slots__ = ("agent", "firm", "limit", "qty", "reason", "placed", "filled", "price")

    def __init__(self, agent, firm, limit: int, qty: int, reason: str) -> None:
        self.agent = agent            # None for a firm's own new issue
        self.firm = firm
        self.limit = limit
        self.qty = qty                # what is still to trade
        self.reason = reason
        self.placed = qty             # what was asked for
        self.filled = 0
        self.price = None             # the price it traded at, if it traded


class Broker:
    def __init__(self, town) -> None:
        self.town = town
        self.bids: dict[int, list[Order]] = {}
        self.asks: dict[int, list[Order]] = {}
        self.issues: dict[int, list] = {}     # firm id -> [limit, quantity left, week it lapses]

    # --- placing orders ----------------------------------------------------------------
    def bid(self, agent, firm, limit: int, qty: int) -> None:
        if limit <= 0:
            return
        committed = sum(o.limit * o.qty for book in self.bids.values() for o in book if o.agent is agent)
        qty = min(qty, max(0, agent.cash - committed) // limit)
        if qty <= 0:
            return
        self.bids.setdefault(firm.id, []).append(Order(agent, firm, limit, qty, "buy"))

    def ask(self, agent, firm, limit: int, qty: int, reason: str) -> None:
        held = agent.shares.get(firm.id, 0)
        offered = sum(o.qty for o in self.asks.get(firm.id, []) if o.agent is agent)
        qty = min(qty, held - offered)
        if qty <= 0:
            return
        self.asks.setdefault(firm.id, []).append(Order(agent, firm, max(0, limit), qty, reason))

    def issue(self, firm, limit: int, qty: int) -> None:
        """A firm offers new shares. The offer stands for a quarter."""
        if qty <= 0 or limit <= 0:
            return
        self.issues[firm.id] = [limit, qty, self.town.week + self.town.cfg.issue_weeks]

    def pending_issue(self, firm) -> int:
        entry = self.issues.get(firm.id)
        return entry[1] if entry else 0

    # --- the auction -------------------------------------------------------------------
    def clear_all(self) -> None:
        town = self.town
        offered = []                  # this week's new-issue offers, for the record
        for firm_id in sorted(self.bids):
            firm = town.firm(firm_id)
            if not firm.alive:
                continue
            bids = self.bids[firm_id]
            asks = list(self.asks.get(firm_id, []))
            entry = self.issues.get(firm_id)
            if entry and entry[1] > 0:
                asks.append(Order(None, firm, entry[0], entry[1], "issue"))
                offered.append(asks[-1])
            if not asks:
                continue
            ref = firm.share_price or town.cfg.share_par
            result = clearing_price([(o.limit, o.qty) for o in bids],
                                    [(o.limit, o.qty) for o in asks], ref)
            if result is None:
                continue
            price, _ = result
            self._trade(firm, price, bids, asks)
        rows = []
        for side, books in (("bid", self.bids), ("ask", self.asks)):
            for firm_id in sorted(books):
                for o in books[firm_id]:
                    rows.append((firm_id, o.agent.id, side, o.limit, o.placed, o.filled, o.price,
                                 o.reason))
        for o in offered:
            rows.append((o.firm.id, None, "issue", o.limit, o.placed, o.filled, o.price, o.reason))
        if rows:
            town.rec.orders(town.week, rows)
        self.bids = {}
        self.asks = {}
        for firm_id in [f for f, e in self.issues.items()
                        if e[1] <= 0 or e[2] <= town.week or not town.firm(f).alive]:
            del self.issues[firm_id]

    def _trade(self, firm, price: int, bids, asks) -> None:
        town = self.town
        # Highest bidders first; the most willing sellers first. Python's sort is
        # stable, so equal limits keep the order in which they were placed.
        buyers = sorted((o for o in bids if o.limit >= price), key=lambda o: -o.limit)
        sellers = sorted((o for o in asks if o.limit <= price), key=lambda o: o.limit)
        traded = False
        si = 0
        for buy in buyers:
            want = min(buy.qty, buy.agent.cash // price)
            while want > 0 and si < len(sellers):
                sell = sellers[si]
                if sell.agent is buy.agent:
                    si += 1
                    continue
                q = min(want, sell.qty)
                if q <= 0:
                    si += 1
                    continue
                if sell.agent is None:
                    town.ledger.pay(buy.agent, firm, q * price, "share_issue")
                    town.issue_shares(firm, buy.agent, q)
                    self.issues[firm.id][1] -= q
                    town.event("share_issue", agent=buy.agent, firm=firm, amount=price, qty=q)
                else:
                    town.ledger.pay(buy.agent, sell.agent, q * price, "share_trade")
                    town.move_shares(firm, sell.agent, buy.agent, q)
                    town.event("share_trade", agent=buy.agent, firm=firm, amount=price, qty=q,
                               seller=sell.agent.id, reason=sell.reason)
                traded = True
                want -= q
                sell.qty -= q
                buy.filled += q
                sell.filled += q
                buy.price = sell.price = price
                if sell.qty <= 0:
                    si += 1
        if traded:
            firm.share_price = price
