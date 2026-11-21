# Build ledger: the RTR world, going without appliances counted at what owning a set costs (22 November 2026)

Branch `feature/rtr-appliances-at-owning`, off `develop` at `f4665ec`.

## His words

The trace of a job beside a business of one's own (`docs/build-ledger-rtr-floor-counts-business-2026-11-22.md`)
found someone going without appliances counted as if renting a set cost thousands of dollars a week. He asked:
"How long will it take you to determine that or is it legitimate that it should cost thousand dollars a week?"
Then: "let's just do the fridge fix and let me know we'll see if it goes any further".

Put to him: should someone without a fridge count it at what owning one costs, about $23 a week, when renting
costs more? He said: "yes, go ahead with the fix".

## The trace

Six RTR towns, 60 years, the world's own settings (seeds 1, 4, 9, 14, 21, 24), every five years.

| Seed 1 | Year 5 | Year 20 | Year 40 | Year 60 |
|---|---|---|---|---|
| the appliance firm's rent a week | $76 | $448 | $2,642 | $9,417 |
| its customers | 1 | 1 | 2 | 0 |
| owning a set a week (`own_cost_week`) | $24 | $23 | $24 | $20 |
| people who own a set | 791 | 823 | 867 | 909 |
| people with no set | 0 | 0 | 1 | 6 |

The other five the same: the firm's rent at year 60 was $4,632 to $12,656 a week, with 0 or 1 customer; in seed
14 the firm closed at year 40 and its last rent, $2,279, stood. The rent starts at $55 (`initial_price`). The firm
falls short of its profit target every quarter and its price rises 3% each time; under his "ratchet" rule a price
only rises. 3% a quarter for 240 quarters is about 1,200 times.

The housing firms went the same way with no tenants ($50,000 to $155,000 a week at year 60), but someone with no
home is counted at the lowest rent a neighbour asks ($304 to $921 in these towns), so homes are mostly sound.

## What was built

- A dial `going_without_appliances_at_owning` (J), on, in `RTR_ONLY` and `rtr/settings.json`.
- `subscriptions.cheapest_prices`: in the RTR world, with his lowest-price rule on, the lowest price counted for
  appliances is what owning a set costs a week (`rtr_owning.own_cost_week`: the building spread over its life and
  its upkeep), when no firm or neighbour asks less. What is on offer to rent this week is not changed.
- Homes are left as they were.

## Rulings

- Ruling: appliances only, not homes ; owning a home takes a deposit and a loan that someone with no home
  mostly cannot get, so it is not a price they could actually achieve ; cost if wrong: in a town where no
  neighbour lets, someone with no home is still counted at a firm's runaway rent. Seen in two of 27 towns in the
  earlier trace.
- Ruling: owning counts at the full cost a week, building spread over ten years and upkeep, not upkeep alone ;
  someone without a set would have to build or buy one ; cost if wrong: small, about $10 a week.
- Ruling: the three tests of his lowest-price rule in `tests/test_rtr_owner_pays.py` now add up a person's other
  basics from the lowest prices (what a basket counts for a need they go without) rather than the prices on
  offer ; that is what the basket does, and the appliance part now differs between the two ; cost if wrong:
  none found; each test still pins its own need.
- Ruling: the firm's ratchet is not touched ; it is his rule, in both worlds ; cost if wrong: the firms' asking
  rents still climb; only what a person is measured against changes.

## Checks

- Tests first: 9 in `tests/test_rtr_appliances_at_owning.py`, all failed before the code (the dial did not exist).
- Under the rule 3 older tests failed (above); changed as ruled.
- Deliberate breaks, each put back: the dial ignored; owning always counted, even above a cheaper rent; homes
  counted at owning too; upkeep alone; what is on offer to rent changed too; the WEF world not shut out. All 6
  failed a test.
- With the dial off, 15-year towns of 200 match `develop` event for event: RTR seeds 5 (37,089 events) and 11
  (58,907); WEF seeds 5 (106,514) and 11 (77,012). With it on they match too: in the six long towns nobody went
  without a set until about year 40.
- The WEF world's reference town (seed 74) cannot be run on this machine; its fixed pages and pinned towns are in
  the suite.

## Review

A fresh reviewer, no part in the build, read the change. No Critical finding; the change writes only to the
lowest prices a basket counts for a need someone goes without, and nothing else reads them (confirmed by the
reviewer: what is on offer, `town.last_price`, `metrics.basket_asking`, `price_appliances`, the decision to build a
set and `essentials_cost` all still see the firm's rent). The town's `basket` and `affordability` measures move,
because they average `basket_cost`; that is intended.

- Final: Ruling: the rule holds from the first week, not only once the rent has climbed ; the rent starts at
  $55 a week against about $25 to own a set, and his words were "when renting costs more" ; cost if wrong: the
  few with no set early on are counted about $30 a week lighter than before.
- Final: minor (deferred) the rule sits inside his lowest-price rule (`going_without_at_lowest_price`); with that
  off, this is off too. Said in the dial's comment.
- Final: minor (deferred) with `owners_judge_by_what_they_pay` off (a dial study only), someone who owns a set is
  counted at what owning costs rather than the asking rent.
- Final: minor (deferred) untested: that the measures of what firms ask, and `town.last_price`, keep the rent.
- Found, not caused by this change, not fixed (Important by the reviewer's grade): `rtr_owning.newcomer_keeps`
  has a newcomer buying a home hold back four weeks of the base needs at the prices on offer, appliances at the
  firm's rent: about $37,700 at a rent of $9,417 a week. That may stop newcomers buying homes in old towns.
  Confirmed by reading the code; not traced in a town. Put to him.
- For him: "about $23 a week" spreads the cost of building a set ($5,400 of parts) over ten years; someone with
  no cash or credit may not be able to raise it.

## The towns

A hundred RTR towns, 60 years, `rtr/batches/appliances-rtr`, against `rtr/batches/floorbiz-rtr` (develop). The
first run of this batch was refused part way (27 of 100 run) because the builder edited a comment in the code
while it ran and the batch saw the code had changed; it was deleted and all 100 run again on the final code.

All 100 survived in both. Every town made different events. The middle town:

| | Year 40 before | after | Year 60 before | after |
|---|---|---|---|---|
| unhappy | 14.8% | 14.0% | 18.6% | 20.8% |
| no employer | 7.2% | 5.6% | 6.2% | 5.2% |
| running a small business | 5.8% | 4.6% | 5.5% | 4.8% |
| staff wage a week | $888 | $891 | $840 | $851 |
| rate offered someone new | $786 | $799 | $758 | $776 |
| basket a week | $892 | $894 | $1,050 | $945 |

Town by town at year 60, 53 towns were more unhappy (by more than half a point) and 42 less; at year 40, 33 more
and 42 less. That is close to even, and only 3 to 10 people a town go without a set, too few to move a town's
figure on their own: the change in the middle town is read as the towns going different ways once anything
changes, not as an effect of the rule. How those going without a set fared was not counted.

The comparison page made again: `rtr/batches/appliances-rtr/compare.html`.
