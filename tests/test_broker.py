from engine.broker import clearing_price


def test_fire_sale_price_set_by_depth_of_buyers():
    bids = [(800, 50), (600, 30), (300, 40)]
    asks = [(0, 100)]                       # a seller in distress takes any price
    assert clearing_price(bids, asks, ref=1000) == (300, 100)


def test_no_cross_no_trade():
    assert clearing_price([(500, 10)], [(600, 10)], ref=550) is None
    assert clearing_price([], [(600, 10)], ref=550) is None
    assert clearing_price([(500, 10)], [], ref=550) is None


def test_tie_goes_to_price_nearest_last_trade():
    assert clearing_price([(1000, 10)], [(600, 10)], ref=900) == (900, 10)


def test_trades_conserve_cash_and_shares(town):
    seller = town.add_agent(cash=0)
    buyer = town.add_agent(cash=100_000)
    firm = town.add_firm("food")
    town.issue_shares(firm, seller, 100)
    firm.share_price = 1000
    town.broker.ask(seller, firm, 0, 40, "distress")
    town.broker.bid(buyer, firm, 900, 40)
    before = town.money_in_town()
    town.broker.clear_all()
    assert town.money_in_town() == before
    assert seller.shares[firm.id] == 60 and buyer.shares[firm.id] == 40
    assert sum(firm.holders.values()) == firm.shares_out == 100
    assert firm.share_price == 900
    assert (seller.cash, buyer.cash) == (36_000, 64_000)
    trades = [e for e in town.rec.events if e["kind"] == "share_trade"]
    assert len(trades) == 1 and trades[0]["qty"] == 40 and trades[0]["amount"] == 900


def test_new_issue_raises_cash_and_adds_shares(town):
    founder = town.add_agent(cash=0)
    buyer = town.add_agent(cash=100_000)
    firm = town.add_firm("food")
    town.issue_shares(firm, founder, 100)
    firm.share_price = 1000
    town.broker.issue(firm, 950, 50)
    town.broker.bid(buyer, firm, 1000, 20)
    town.broker.clear_all()
    assert firm.cash == 20_000
    assert firm.shares_out == 120 and buyer.shares[firm.id] == 20
    assert sum(firm.holders.values()) == firm.shares_out
    assert town.broker.pending_issue(firm) == 30


def test_seller_cannot_sell_more_than_held(town):
    seller = town.add_agent(cash=0)
    buyer = town.add_agent(cash=1_000_000)
    firm = town.add_firm("food")
    town.issue_shares(firm, seller, 10)
    firm.share_price = 1000
    town.broker.ask(seller, firm, 0, 25, "distress")
    town.broker.ask(seller, firm, 0, 25, "distress")
    town.broker.bid(buyer, firm, 1000, 50)
    town.broker.clear_all()
    assert buyer.shares[firm.id] == 10
    assert firm.id not in seller.shares
    assert sum(firm.holders.values()) == firm.shares_out == 10


def test_bid_is_capped_by_cash(town):
    seller = town.add_agent(cash=0)
    buyer = town.add_agent(cash=5_000)
    firm = town.add_firm("food")
    town.issue_shares(firm, seller, 100)
    firm.share_price = 1000
    town.broker.ask(seller, firm, 0, 100, "distress")
    town.broker.bid(buyer, firm, 1000, 10)
    town.broker.clear_all()
    assert buyer.shares[firm.id] == 5
    assert buyer.cash == 0


def test_orders_do_not_carry_over_to_next_week(town):
    seller = town.add_agent(cash=0)
    firm = town.add_firm("food")
    town.issue_shares(firm, seller, 10)
    town.broker.ask(seller, firm, 0, 10, "distress")
    town.broker.clear_all()
    buyer = town.add_agent(cash=100_000)
    town.broker.bid(buyer, firm, 1000, 10)
    town.broker.clear_all()
    assert firm.id not in buyer.shares
