# Build ledger: the RTR world, the least someone out of work will take (21 November 2026)

Branch `feature/rtr-reservation-floor`, off `develop` at `224fee9`.

## His words

After the batch under his rulings of 20 and 21 November (`rtr/batches/lowest-rtr`), the unhappiest RTR towns were
poor ones: seed 15, 51% unhappy and staff paid $230 a week at year 60; seed 49, 61% and $462. He said: "trace how
the, why the pay fell so low. and fix the issue. Then commit that change and notify me when complete".

## The trace

Seeds 15 and 49 run again with a count every five years (a scratch probe, the world's own settings):

- The share with no job stayed between 10% and 26% for decades in seed 15. The rate a firm offered someone new fell
  the whole time: $945 at year 5, $694 at 10, $501 at 20, $386 at 30, $219 at 40, $125 at 50, $110 at 60.
- Nearly everyone out of work would take any pay: the least they would take was nothing for 145 of 153 at year 5,
  103 of 107 at year 10, 215 of 222 at year 30. Their middle spell out of work ran from 42 weeks to over 14 years.
- So the line (those out of work who would take the job at the lower rate) stayed over 5% of the town, and every
  firm short of profit cut its rate 2% each quarter it did. The seven firms' rates fell from $922 to $980 at year 5
  to $93 to $138 at year 60.
- What their basics cost those out of work (their basket, under his rulings) was $416 to $681 a week.
- No firm had a job it could not fill at any of the counts. Lower pay made no more work: a firm hires for the work
  its customers bring.
- Seed 49 the same, more slowly: rates $922 to $1,000 at year 5, $171 to $248 at year 60.

Whose rules: cutting when there is a queue is his ("cutting when there is a queue", 12 November, and on
19 November only those who would take the job are in the line). The numbers are Claude's: 2% a cut, the line at 5%
of the town, and the least someone will take falling 5% a week (`reservation_decay`), with no floor, so nothing
after twenty weeks.

## What was built

- A dial `reservation_covers_basket` (C), on, in `RTR_ONLY` and `rtr/settings.json`.
- `labour.reservation_wage(cfg, agent, town=None)`: given the town, in the RTR world, never less than
  `basket_cost(town, agent)`. Its three callers pass the town: the line (`in_the_line`), the weekly labour market,
  and a small business taking staff on (`rtr_makers`).

## Rulings

- Ruling: the floor is their own basket ; under his rulings it is what their basics actually cost them, so a job
  below it does not keep them ; cost if wrong: someone with nothing at all turns down a job that would have been
  better than nothing, and stays out of work.
- Ruling: Claude's call, not his, made at his "fix the issue" ; the fault was in Claude's numbers, and his rule of
  cutting when there is a queue is untouched ; cost if wrong: he may want a different floor, or none. The dial
  turns it off.
- Ruling: the WEF world is not changed ; it must not change, and his word was about the RTR towns ; cost if wrong:
  the WEF world keeps the same spiral (its towns fail by year 22, before it shows).
- Ruling: hand-built test towns (`quiet_town` in `tests/test_rtr_2.py`) hold the floor off ; their jobs pay what
  each test sets, often less than an empty town's basket of $880, to test other rules one at a time ; cost if
  wrong: none; the floor's own tests turn it on.

## Checks

- Tests first: 7 in `tests/test_rtr_reservation_floor.py`, which failed before the code (one, someone offered a
  job below their basics turns it down, was added after a break passed every test).
- Deliberate breaks, each put back: no floor; the WEF world not shut out; the dial ignored; the line ignoring the
  floor; the labour market ignoring it. All 5 fail a test.
- Under the floor 19 older tests failed: hand-built towns whose jobs pay less than an empty town's basket. Held off
  as the ruling above says.
- Full tests: 1,213 passed.
- Started at 3:32pm: `rtr/batches/floor-rtr` and three checked full towns, and a fresh reviewer. Stopped when the
  review came back (below), the workers killed by process number, the output deleted.

## Review

A fresh reviewer, with no part in the build. Its two main claims were checked in the code before anything changed.

- Final: fixed (Important) the floor overrode his rule that someone owing a large loan "take[s] the first job offered"
  (`rtr_makers.least_wage` returned the floored figure) ; no floor for someone who owes a large loan (as
  `owes_a_large_loan` reckons it, with `home_loan_presses`) ; `test_someone_who_owes_a_large_loan_still_takes_the_first_job_offered`
  RED then GREEN.
- Final: fixed (Important) the floor counted the home loan payment, so a homeowner with a loan could have a floor
  above every wage in town (the reviewer's town, seed 1 at year 14: 32 out of work above every wage, 30 with a home
  loan, all with a side hustle, some out 300 weeks) ; the floor leaves the home loan payment out (`basket_cost(...,
  loan=False)`) ; `test_the_floor_leaves_out_the_home_loan_payment` RED then GREEN.
- Final: fixed (the reviewer's Minor, a slow spot) each floor rebuilt the town's prices ; the prices are worked out
  once in the line, the labour market and a small business's hiring.
- Final: fixed (the reviewer's Minor, a wrong change that passed) a small business's hiring without the floor ;
  `test_a_small_business_taking_someone_on_asks_the_floor_too` (it failed with that change); and
  `test_a_floor_applies_part_way_through_a_spell_too`.
- Final: minor (deferred) `rtr_makers.hour_worth` writes the old formula out by itself: someone out of work with a
  side hustle prices their hour on what they would take with no floor. It sets prices only, not who would take a job.

- Ruling: someone with a large loan has no floor at all ; his rule is "take the first job offered" ; cost if wrong:
  they may take a job far below their basics.
- Ruling: the home loan payment is left out of the floor ; a job need not pay off their home for them to take it ;
  cost if wrong: an owner with a large home loan takes a job that does not cover what they pay.

After the fixes the towns as shipped no longer reached one rule; picked again the same way (all sixty clean): 1 and
23 on the map, 1 and 27 with no map. Full tests: 1,216 passed and that one, then all of `test_rtr_rulings.py` (144).

Running again from 3:46pm: `rtr/batches/floor-rtr` (100 towns) and three checked full towns.

## The towns

Three checked full towns (seeds 1 to 3, sixty years): 3,120 weeks each, no problem found.

A hundred RTR towns, the same seeds as before (`rtr/batches/floor-rtr`, against `rtr/batches/lowest-rtr`), all
reached sixty years without the failure line. The middle town at year 60:

| | Before the floor | With the floor |
|---|---|---|
| unhappy | 23.7% (2% to 61%) | 19.9% (4% to 48%) |
| towns over 30% unhappy | 27 | 13 |
| with no job | 3.4% | 8.1% |
| towns over 15% with no job | 2 | 16 |
| the rate a firm offers someone new | $698 | $810 |
| the lowest such rate in any town | $110 | $598 |
| staff paid | $827 ($230 to $1,015) | $858 ($677 to $1,018) |
| towns with staff paid under $500 | 3 | 0 |
| basket against the staff wage | 128% | 118% |

The two towns traced:

| | Seed 15 before | Seed 15 after | Seed 49 before | Seed 49 after |
|---|---|---|---|---|
| unhappy at year 60 | 51% | 25% | 61% | 22% |
| staff paid | $230 | $720 | $462 | $842 |
| rate offered someone new | $110 | $665 | $217 | $822 |
| with no job | 12.8% | 5.5% | 8.4% | 5.9% |

The cost: more people out of work. The average share with no job, year 20 to 60, was about 5% before and about
9% after; 16 towns end over 15%, the worst 33% (seed 91). The middle town's unhappiness is a little higher at
years 20 to 40 (6.3% against 5.0% at year 20, 15.4% against 14.1% at year 40), the same at 50 (20%), and lower at 60.
Nearly all of those out of work are unhappy: in the middle town, 70% at year 20 and all of them at year 60.

Why more are out of work, traced in the two worst towns (seeds 91 and 89, a count every five years, the same
scratch probe as above):

- No firm had a job it could not fill at 22 of the 24 counts (6 open jobs in seed 91 at year 10, 2 in seed 89 at
  year 15). So the floor is not what keeps them out: there was no job for them to turn down.
- The jobs did not grow with the town. Seed 91: 633 jobs for 783 people at year 5, 582 for 900 at year 60, with
  294 out of work. Seed 89: 610 for 785, then 621 for 904, with 255 out.
- The firms' rates no longer fall to nothing: seed 91 from $922 to $980 at year 5 to $590 to $627 at year 60; seed
  89 to $618 to $654. Those out of work count their basics at about $624 and $640 a week.
- By year 60, 134 of those out of work in seed 91 (60 in seed 89) have a floor above every firm's rate. They would
  turn down a firm's job if one came up.

Not traced: why these towns have fewer jobs than they had under the old rule. A firm hires for the work its
customers bring, so it is a question of what people buy, not of pay.

## Before the commit

Full tests on the tree committed: 1,216 of 1,217 passed. The one failure was
`test_batch.py::test_ctrl_c_at_the_keyboard_stops_a_batch_running_several_towns`, which depends on timing (one
town running instead of two when Ctrl-C landed) and fails on `develop` too; run again alone, it passed.
