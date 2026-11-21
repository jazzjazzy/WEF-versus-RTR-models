# Build ledger: the RTR world, an owner is judged on what they actually pay (20 November 2026)

Branch `feature/rtr-owner-pays`, off `develop` at `6acefd1`. Built by Claude on the second machine.

## His words

Claude put to him: in the RTR world the basket counts the asking prices of firms with no tenants, so it reads about
11,200% of the wage. Should the RTR world's basket use what people actually pay? He said:

> "yes, use what people actually pay"

Before building, Claude found the same thing inside each person's own yardstick and put that to him too, with the
figures below. He said:

> "Yes, it should be judged on what they actually pay because they own it. The reason they want to own it is
> because they don't want to know what the firms are being priced at or they don't want to care."

## What was found before building

- `basket_cost` (`engine/household.py`) is each person's yardstick: it measures how adequate their income is,
  sets their cushion and their buffer, tests "living on dividends", and says whether a maker makes a living. For a
  need they own, it counted the cheapest asking price, as for a need gone without.
- That was Claude's call in the design, not his: section 11 of the RTR design, "(C, after the builder check) ...
  The basket does not shrink when someone owns. An owner's basket counts a home and an appliance set at the going
  rent, as it does for anyone going without one."
- A 20-year RTR test town (seed 1, the world's settings), averages over people who own their home:

| Year | Their yardstick a week | Of it, asking prices of what they own | Their income | Owners unhappy (rough count: security below 0.5) |
|---|---|---|---|---|
| 5 | $942 | $437 | $1,441 | 12% |
| 10 | $1,139 | $637 | $1,180 | 11% |
| 15 | $1,393 | $899 | $1,198 | 19% |
| 20 | $1,651 | $1,203 | $1,152 | 22% |

- The 93 RTR towns of the stage 3 batch still standing at year 60 (`rtr/batches/stage3-rtr`): homes lived in by
  their owner 844 on average (702 to 910), let by a small landlord 391 (281 to 562), taken back by the bank 2,
  about 5 left to the landlord firms.

## What was built

- A dial, `owners_judge_by_what_they_pay` (J), on, in `RTR_ONLY` and in `rtr/settings.json`.
- `basket_cost`: in the RTR world with the dial on, a home or appliance set of their own counts at
  `own_cost_week(..., build=False)` (its upkeep: parts at the outside price and the hours at what an hour is worth),
  and a loan against a home adds the week's payment (interest and repayment, as their bills count it).
- The town's `basket` in the RTR world is the average of its people's own baskets. The cheapest asking price of
  each need is kept as `basket_asking` (RTR only). `price_index` stays on asking prices. `affordability` is the
  new basket against the staff wage.
- Pages: an RTR dashboard's "Basket against the staff wage" draws what people pay and the asking prices beside it.
  The batch page has a card "Asking basket" (RTR only). The comparison page says the basket is not the same measure
  in the two worlds when the RTR batch was run under the rule, and keeps the old warning for a batch made before
  it (it reads the dial from a town's own settings).

## Rulings

- Ruling: an owned unit counts at the upkeep it needs that week (`own_upkeep_week`: `upkeep_need` at its age, at a
  standard unit's size, parts at the outside price and the hours at what an hour is worth) ; it is what their own
  upkeep each week charges them, and a better home is left out as it is for a renter ; cost if wrong: hours they do
  themselves are counted as if paid. (First built on a new unit's upkeep; the review found it, below.)
- Ruling: the loan payment counts whether or not they live in the home the loan is on ; it is what they pay, and
  their bills already count it so ; cost if wrong: a small landlord's yardstick includes a payment their tenant's rent
  covers.
- Ruling: the town's basket is the average of its people's own baskets ; "what people actually pay" is a per-person
  figure ; cost if wrong: the town's basket mixes renters at their rent with owners at their upkeep, so it moves when
  the share who own moves.
- Ruling: `price_index` stays on asking prices ; it is a price index, the prices on offer against where they started
  ; cost if wrong: none to the measures; "Prices against wages" on the dashboard still reads asking prices, and says so.
- Ruling: the WEF world's basket is not changed ; his ruling was for the RTR world, and the WEF world must not
  change ; cost if wrong: the comparison page sets two different measures on one chart, which it now says.
- Ruling: whole-town tests of earlier stages hold the old rule (`BEFORE_OWNERS_PAY`, inside `BEFORE_THE_SHEDDING` in
  `tests/conftest.py`), as was done for each ruling of 18 and 19 November ; their seeds were picked for the rules of
  their day ; cost if wrong: none; the towns as the world ships are run under the new rule (below).
- Ruling: new seeds for the towns as shipped (`tests/test_rtr_rulings.py`): 3 and 23 on the map, 3 and 5 with no map,
  picked from thirty of each kind as on 19 November ; under the new rule the old seeds no longer reached "a firm short
  of profit kept its rate" and some rules of the stages before ; cost if wrong: none to the model; a test of whole
  towns that reach every rule.

## Checks

- Tests first: 11 new tests in `tests/test_rtr_owner_pays.py` (8 failed before the code; the 3 that passed are the
  dial-off and WEF cases, which hold the old behaviour). Page tests in `tests/test_compare.py` and
  `tests/test_dashboard.py` failed first, then passed.
- Under the new rule, 10 older tests failed: whole towns whose seeds were picked for the old rule. Fixed as the
  rulings above say. The old unit test `test_owning_does_not_shrink_the_basket...` is renamed `..._did_not_...` and
  holds the dial off for that line.
- The sixty candidate towns as shipped (seeds 1 to 30, each kind, 200 people, fourteen years, weekly checks): all
  sixty clean.
- Deliberate breaks, each in place and put back (`cmp` confirmed): an owned need at the asking price; the loan left
  out; the WEF world not shut out; the dial ignored; an owned need free; the town's basket left at asking prices; the
  price index on what people pay; the WEF world given the new measure. All 8 failed a test.
- The WEF world: its fixed pages (`tests/test_wef_pages_unchanged.py`) and the pinned WEF towns of `tests/test_rtr.py`
  are unchanged. The reference town (seed 74, `08251209eb136522`) cannot be run here: its settings file is on the
  desktop only. Not checked on this machine.
- Full tests: 1,195 passed (3 minutes 29 seconds).

## Review

A fresh reviewer, with no part in the build, on how a person now reckons. Its main claim was checked against the
code before anything was changed: `keep` (`engine/rtr_owning.py`) charges an owner `upkeep_need`, which grows with
the unit's age (4% a year for a home, 15% for a set), while the yardstick used a new unit's upkeep. The reviewer's
probe (seed 3, 200 people): home upkeep owed $144 a week at year 20 against $86 counted. The runs already started
were stopped, their workers killed by process number and their output deleted.

- Final: fixed (Important) owned units counted at a new unit's upkeep, not at their age ; `test_an_aged_home_counts_at_the_upkeep_it_needs_now_not_a_new_ones` RED then GREEN, with `test_a_bigger_home_of_their_own_counts_at_a_standard_homes_upkeep`.
- Final: fixed (the reviewer's Minor, a wrong change that passed every new test: dropping the loan for someone who owes on a home they do not live in) ; `test_someone_who_owes_on_a_home_they_do_not_live_in_counts_the_payment` added.
- Final: minor (deferred) the town basket test checks the town figure with `basket_cost` itself, so it cannot catch a fault inside `basket_cost` (the unit tests do).
- Final: minor (deferred) a personal loan taken for a set's parts is not in the yardstick, where a home loan is ; as before this change, and as `standard_bills` counts it.
- Final: minor (deferred) someone going without a need is still counted at the cheapest asking price, which in the RTR world may be an empty firm's ; his ruling was for what owners pay; for him.
- Final: minor (deferred) the batch page's "Weekly basket" card says "What the four base needs cost a week" in both worlds ; the card is shared with the WEF world's page, which must not change; the "Asking basket" card says which is which.
- Final: minor (deferred) the comparison page reads the dial from the first town's settings only ; a batch cannot vary it across towns of one setting.

After the fix the towns as shipped no longer reached one rare rule of the stages before ("foreclosed home to an owner
who lets it"). Seeds picked again the same way, from thirty of each (all sixty clean under the checks): 3 and 22 on
the map, 5 and 25 with no map.

Found by the full tests after the fix: the comparison page crashed on a measure that only one world had any of (the
small RTR test towns now had nobody out of work, so "Unhappy: out of work" had no RTR rows). An old fault of stage 3,
not of this rule. Fixed: `test_a_measure_only_one_world_has_any_of_is_drawn_for_that_world_alone` RED then GREEN.

Full tests after the review: 1,199 passed.

## The second rule: going without (21 November 2026, Canberra time)

The batch under the first rule (`rtr/batches/ownerpays-rtr`, after the review fix): RTR 0 of 100 failed (7 before);
year 60, middle town: unhappy 38.8% (74% before), no town at 80% or more, no job 2.7%. Three checked full towns,
seeds 1 to 3: clean, sixty years. But unhappy still rose from about 4% at year 20 to 39% at year 60. Probes of four
towns (scratch) found why: a need someone goes without was still counted at the cheapest price on offer this week,
and a neighbour's price counted only while they had room. Seed 1, year 60: owners paid $208 a week of home upkeep
and $27 for a set; 406 owners bought entertainment, at about $205 a week; 442 went without and were counted at the
entertainment firm's $5,905 a week (it started at $95 and rose 3% each quarter it fell short, his "ratchet" rule).
People with no home were counted at an asking rent of $12,649 (seed 3: $137,917).

He asked why the firm does not close. Read in the code: a firm closes after 26 weeks with no income at all, or when
it cannot pay its wages or loan. Any sale outside the town or one customer resets the first. Not traced for that
firm.

His words:

> "happiness can be affected by the fact that you can't purchase entertainment. But unhappiness shouldn't be
> affected by not paying a $5,905 bill that no one is paying for."

> "The price that they can't afford should always be the one that's the lowest out of the possible two.
> neighbours entertainment or firms Entertainment. It will be the one that they could actually achieve, not the
> one that's way out of scope."

Built: a dial `going_without_at_lowest_price` (J), on, RTR only. `cheapest_prices` now returns its prices with a
second set beside them, `lowest`: the lowest any firm or neighbour asks (a maker's price whether or not they have
room; for a home, a small landlord's rent too). `basket_cost` counts a need gone without at `lowest`. What people
shop with (`cheapest_prices` itself) is not changed.

- Ruling: a neighbour's price counts whether or not they have room this week ; his "the lowest out of the possible two"; counting only makers with room brought the firm's $5,905 back whenever they were full ; cost if wrong: someone counts a price they could not get this week. (This reverses Claude's stage 2 ruling that a full maker moves nobody's yardstick.)
- Ruling: for a home, a small landlord's rent counts beside the firms' (homes with a rent of their own, `unit.rent`) ; a neighbour's home is his "neighbours" for housing ; cost if wrong: let homes whose rent is the landlord firm's price are not counted, so the firm's rent may still be the lowest for someone with no home.
- Ruling: only the yardstick changes, not what people shop with ; his words were about unhappiness ; cost if wrong: none to what people buy.
- Ruling: `test_what_a_side_hustle_brings_in_is_income_and_half_a_basket_of_it_is_a_living` (stage 2) holds the dial off ; written for a full maker's price moving nobody's basket ; cost if wrong: none.
- Ruling: the towns as shipped picked again, the same way (all sixty clean): 1 and 22 on the map, 1 and 27 with no map.

Checks: 7 new tests (4 failed before the code). Deliberate breaks: the lowest set not used; the WEF world not shut
out (passed at first: a WEF town has no makers or lets; a test added, then it failed); the dial ignored; let rents
left out; makers left out. All failed a test. The flaky Ctrl-C test (`test_batch.py`) failed twice in full runs;
alone it passed 4 of 4 with the change and failed 1 of 3 on `develop` without it. Full tests: 1,206 passed.

Running from 12:15pm Canberra time: `rtr/batches/lowest-rtr` (100 towns, 27 at a time) and three checked full towns
(`rtr/batches/checked-lowest/`).
