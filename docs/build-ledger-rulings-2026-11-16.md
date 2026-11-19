# Build ledger: Jason's rulings of 16 November 2026

Spec: `docs/superpowers/specs/2026-11-16-wef-world-rulings-design.md`. Branch
`feature/decisions-2026-11-16`, cut from `develop` at `6115ebe`.

Records before any change, on the code at `6115ebe` (10 years, `what_happened`):
- map, `population_cap=120 stop_on_failure=false seed=1`: `8695200c6089e105`, 33,859 events
- map, `population_cap=160 stop_on_failure=false seed=4 founder_arrival_rate=0.25 resident_founder_rate=0.2 invent_prob=0.1`: `4037d21bbcc64ec2`, 24,416 events
- the 13 November batch, seed 74 (60 years, `snapshot_every=13`): `08251209eb136522`, 180,377 events

With `config.OLD_RULES` the model must give these again, and the stage one records.

## Task 1: decisions 2, 5 and 10 (defaults)

- `habit_weeks` 52, `needs.housing.initial_units` 60, `transport_can_close` false; `config.OLD_RULES` gives the old three. `tests/test_rulings.py`: the defaults, and both map records above given again under `OLD_RULES` (RED on import, then GREEN).
- Ruling: the stage one pins (`test_town_invariants.py`) now run under `OLD_RULES`; they are records of the old rules; cost if wrong: none; a separate accounts check under the new rules is added with the later tasks.
- Ruling: tests tied to 120 homes or to the old transport rule now say which rule they test: 60 homes in the start-up checks; `transport_can_close=true` named in the twice-failed bus test and in `ROUGH_MAP` (whose purpose includes a transport firm closing); cost if wrong: none.
- Ruling: under the new rules small test towns are frailer (60 homes: a jobs dip in weeks 14 to 26 lifts unhappiness to 33% where 120 homes gave 17%, seed 2 of `population_cap=40`). `MIXED` moves from failure share 0.35 to 0.4 so the shared batch is still mixed (2 of 8 stand; under 0.25 all fail, most inside the first year); cost if wrong: the batch tests check machinery, not the model.
- Ruling: `ROUGH_MAP` seeds 8 and 22 became 8 and 28: with only the three new defaults of task 1, of thirty seeds only 20, 27 and 28 reached a rival takeover; cost if wrong: coverage only. (Checked again once every ruling was built, seeds 1 to 10 of `ROUGH_MAP`, 16 years: takeovers by a rival 0 under `OLD_RULES`, 11 under the rulings, 3 under the rulings without `shops_near_unserved`. So "rarer" held only part way through the build; with shops opening near the unserved there are more rivals to buy a failing shop.)
- Ruling: three tests were right only by luck and are corrected: the dashboard's first "Share unhappy" value is weighted by head count (the test took a plain mean); the places record of week 39 was compared with the map of week 40 (a home was built in week 40); the town view's money is rounded half up as the page does (the test used Python's round, which goes to even: $1,258.50).
- Ruling: three checks of a test town's shape loosened to what they guard: "each seed a town of its own" instead of six different towns (base and `price_rule=search` now give the same towns in a year of 30 people); at least 500 and 100 values checked instead of 1,000 and 150; towns drop out over the years instead of all 8 standing at year 1. A firm that changed between weeks 100 and 160 is picked for the pointing test. The 450-person town now fills in year 7, not 6.

## Task 2: decision 13 (the fare before the rent when the ride is for work)

- `fare_first_for_work` (default true; `OLD_RULES` false). `places.ride_for_work`; in `household.dues` the fare of a ride to work sorts at 0.5, between food (0) and rent (1). Five tests in `tests/test_rulings.py` (three RED before the change, then GREEN).
- Ruling: a missed rent is checked by the arrears count, not by `met`: the model counts a home as met during its grace weeks even when the rent is missed (as written in stage 1); cost if wrong: none.

## Task 3: decision 12 (a shop opens where people are unserved)

- `shops_near_unserved` (default true; `OLD_RULES` false), `unserved_entry_min` 20. `corporate.unserved_gap`; `choose_venture` tries it after the transport gap and before inventing a need; it returns four values (spec, price, the home spot aimed for, how many unserved) and `start_venture` takes `near` and `unserved` and records `unserved_entry`. Seven tests (RED: missing function and wrong venture; then GREEN).
- Ruling: a need with no seller at all is left to the old rule (score 1.0 for an unserved need, premises near the middle); the new rule is about distance only; cost if wrong: a new need's first shop still opens in the middle.
- Ruling: the gap is checked only when the founder has the capital for a flow firm (`flow_entry_capital`), as every shop entry is; cost if wrong: none.

## Task 4: decision 8 (the well-off spend more: a bigger plan and a better home)

- Put to Jason first as three designs; he chose "Bigger plan and better home". Dials `well_off_income` 1.5 (0 switches it off; `OLD_RULES`), `well_off_drop` 1.2, `bigger_plan` 2, `better_home` 1.5.
- Built: `Agent.plan`, `Agent.well_off`, `Agent.wants_better`; `Firm.extra` and `Firm.load()` (a bigger plan counts as that many customers for room, staffing, service and goods; unserved customers are the newest, plan by plan); `Unit.scale` and `Project(scale=)` (a better home's building, upkeep, wear, collateral and rent); `Spot.better` and `Spot.better_let` so the home search stays one step per spot; `find_home(better=)`, `home_cost(scale=)`, `unit_rent(standard=)`, `standard_price`, `set_plan`, `free_better_home`; `household.review_spending`, `look_for_better_home`, `standard_bills`; the units table has a scale column. Fourteen tests, RED then GREEN, and weekly checks that bigger plans and better-home counts add up (`test_town_invariants.py`).
- Ruling: the basket (and with it security and the cushion) is measured at standard size, as luxuries already are; the bills that are actually due, and the test for destitution, use what is really paid; cost if wrong: a well-off resident's security reads a little high.
- Ruling: a rival that takes over a firm takes its bigger plans with its customers; cost if wrong: none.
- Ruling, changed after the first full towns: better homes were first built from the number of times the well-off looked and found none (as unmet demand is counted). Seed 1 built 178 for a peak of 44 well-off, 47 of them in years 10 to 11, and from year 11 over 100 stood empty. Now the biggest landlord builds for the well-off still waiting, less the better homes free or being built anywhere in town, so none are built while better homes stand empty. Seed 1 after the change: 2 to 7 waiting at each year end, 170 better homes, nothing built after year 11 while 68 to 116 stood empty; cost if wrong: better homes come a little later.
- Found, not a fault: better homes outnumber the well-off (seed 1: 170 for at most 43) because a resident who stops being well-off stays until a cheaper home is free, and while the town grows there are almost none (0 to 4 empty homes until year 10). They pay the better rent meanwhile.
- Ruling: a better home is let to anyone when it is their cheapest choice; on arrival with no map a standard home is taken first; cost if wrong: none seen.

## Task 5: decision 14 (class as the dot's shape)

- Owner a square, working class a circle, out of work a triangle, about the same area, centred on the person; the colour as before. The followed person is drawn in their shape. The key shows the shapes in both colourings. Two tests, RED then GREEN.
- Ruling: a rider was a square while travelling (stage 3); a square is now the owner class, so a rider on the road gets a dark outline instead. The canvas stub of the page tests learns triangles; tests that took every circle to be a person now take every person; cost if wrong: none.

## Checks against whole towns (16/11)

- `OLD_RULES` on the 13 November batch's seed 74 (60 years, `snapshot_every=13`): `08251209eb136522`, 180,377 events, failed year 13.25. The same town as the batch, after every change.
- Under the rulings, seeds 1, 2 and 3 (60 years each, the map as built): failed in years 19.27, 18.75 and 21.0. The same seeds in the 13 November batch, as written: 16.75, 16.5 and 16.23 (`batch.sqlite`). Each reached every new rule: bigger plans taken (858, 1,379, 2,647) and given back (136, 365, 602), better homes built (170, 173, 200) and moved into (65, 79, 144), shops opened for the unserved (19, 15, 20). Transport firms that closed had no riders left or were absorbed by a rival. Three towns are not a finding; the next step is the batch.
- `configs/before-16-november.json` gives the same settings as `OLD_RULES` (tested).

## Test changes forced by the new rules (beyond task 1)

- Ruling: the shared batch of the batch tests (`MIXED`) now runs under `OLD_RULES`: every model change moved which small towns fail, and those tests check the batch tool, not the model. It is back to 0.35, as first written; cost if wrong: none.
- Ruling: the 450-person town fills in year 8; the test of transport following distance now checks that people were kept out by distance (the `too_far` events the trigger counts) before transport started, where it checked arrivals turned away for want of a home (under the rulings transport came 6 weeks before the first of those); the drawing test wants over 40 people on the map at the end, not 60 (53 under the rulings); cost if wrong: none.
- Ruling: one test wrote "1 were still standing"; the page says "1 was", which is right.

## Final review (a fresh reviewer, 16/11) and the fix pass

The reviewer could not break the new counts (`Firm.extra`, `Spot.better`, `Spot.better_let`): every path read, and 21 more towns run under the weekly checks, among them 8 `ROUGH` towns with no map under the new rules, which the suite does not cover. The faults were in behaviour.

- Final: fixed (Important) a well-off resident short of cash dropped a whole need while keeping a bigger plan; now `plan_bills` steps bigger plans back to standard first, least needed first, only as far as needed. `test_well_off_and_short_of_cash_they_go_back_to_the_standard_plan_before_dropping_anything` RED to GREEN.
- Final: fixed (Important) empty better homes switched off standard building (`plan_building` counted every home); now standard building counts standard homes only, and better homes are planned after it, on top, as the spec says. `test_empty_better_homes_do_not_stop_the_usual_building` RED to GREEN.
- Final: fixed (Important) a resident no longer well-off could not move to a cheaper standard home on their own block (`unit.spot is home` returned first). `test_no_longer_well_off_they_can_move_to_a_cheaper_home_on_their_own_block` RED to GREEN.
- Final: fixed (Important) with no map a waiting resident never got the better home built for them, and a well-off newcomer took a standard home first; now someone waiting looks each week, and sign-up takes a free better home first. `test_with_no_map_someone_waiting_takes_the_better_home_when_one_comes_free`, `test_with_no_map_a_well_off_newcomer_signs_up_for_a_better_home_first_or_waits` RED to GREEN; the old no-map test no longer sets `well_off` by hand.
- Final: fixed (Important) the well-off test used the bills a resident held, so losing a home made someone well-off; now it uses the standard basket of the four base needs, held or not (the same basket the cushion uses), plus the luxuries and ride they hold and the loan payment. `test_losing_a_bill_does_not_make_anyone_well_off` RED to GREEN.
- Final: fixed (graded Minor by the reviewer, re-graded Important by effect: the spec says a well-off newcomer with no better home free waits) a well-off newcomer on the map who found only a standard home was not counted as waiting. `test_on_the_map_a_well_off_newcomer_who_finds_only_a_standard_home_waits_for_a_better_one` RED to GREEN.
- Final: fixed with the move fix above (same lines, reviewer's Minor 9) a well-off resident in a standard home could not make the ordinary moves (cheaper, or to food) and a better home could be taken out of reach of work.
- Final: fixed, found while fixing (Important by effect): stepping down only as far as needed was undone by the next weekly review, so a plan would flip every week. Now a bigger plan, and a better home, are taken only while income stays at least `well_off_drop` (1.2) times the bills with it. `test_a_bigger_plan_is_taken_only_while_income_stays_well_over_the_bills_with_it` RED to GREEN, and the step-down test checks the plan is not put back.
- Final: fixed, found in the whole-town check after the fixes (Important by effect): people counted as waiting for a better home they could not pay for, so better homes were built in a burst when the town filled and 25 to 32 stood empty (seed 1). Now only someone who could pay for one at the cheapest landlord's price waits. `test_only_someone_who_could_pay_for_a_better_home_waits_for_one` RED (check switched off) to GREEN.
- Final: restored the four test checks the reviewer showed had been loosened (six different towns; more than 1,000 and 150 values checked; all 8 towns standing at year 1). They pass in their first form now that `MIXED` runs under `OLD_RULES`.
- Final: minor (deferred): switching seller drops a bigger plan without a `plan_change` event; it comes back the next week, and `plan_change` counts are not a balance.
- Final: minor (deferred): a shop opened for the unserved can land beyond a walk of where it aimed when land is short (rough small map, seed 5: three entries for one gap); not seen in towns of 450.
- Final: minor (deferred): with no map, `rent_home` checks the landlord's price against what they can pay, but `subscribe` hands over a better home at 1.5 times when no standard one is free.
- Final: not judged by the reviewer: the town view script beyond reading, the documents, whether the builder's numbers are sensible, towns of 1,000.

Suite after the fix pass: 705 passed. `OLD_RULES` seed 74 of the 13 November batch: `08251209eb136522`, 180,377 events, unchanged. Under the rulings, seeds 1, 2 and 3 (60 years): failed in years 16.5, 18.25 and 19.25 (as written: 16.75, 16.5, 16.23); better homes 36, 12 and 44; bigger plans taken up 864, 714 and 1,014 times; shops opened for the unserved 14, 12 and 18. Seed 1: nobody waiting for a better home after year 10; 5 to 11 standing empty. Better homes come late: while the town grows the landlords spend on standard homes first (6 better homes from year 3 to year 8, with 7 to 16 waiting).

## Task 6: no cap on people (Jason, 16/11, after the second batch)

- His words: "let's not make it a limit of 1,000 people", then "Yes, drop the cap but keep needing a home". `population_cap` 0 (none); `Config.at_cap`; `OLD_RULES` and `configs/before-16-november.json` add 1,000. Six tests in `tests/test_rulings.py` and one in `tests/test_dashboard.py`, RED then GREEN. Suite 712 passed. `OLD_RULES` seed 74: `08251209eb136522`, 180,377 events, unchanged.
- Ruling: with no cap, "town full" is the first week a newcomer is turned away for want of a home while no block of land is empty (`Town.no_home_week`, set where a worker or a founder is turned away); cost if wrong: the mark falls a little early or late on the charts; nothing in the model reads it.
- Ruling: founders keep arriving while a home is free (`founder_arrival_rate` 0.04 a week), since they are people too and his only limit is homes; cost if wrong: some outside money keeps coming in after the town is full (seed 32: 19 more people over 8 years).
- Found, not new: homeless residents beside empty homes. Under the cap (second batch, middle town) 113 to 232 homeless from year 12 while 232 to 348 homes stood empty; with no cap the same.
