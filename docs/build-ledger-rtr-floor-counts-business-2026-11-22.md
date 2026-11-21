# Build ledger: the RTR world, a job beside a business of their own (22 November 2026)

Branch `feature/rtr-floor-counts-business`, off `develop` at `fc9c6be`.

## His words

After the floor on what someone out of work will take (`docs/build-ledger-rtr-reservation-floor-2026-11-21.md`),
those running a business of their own with no job were more often unhappy. He said: "yes, go ahead with the trace".

The trace was put to him as Mia: her basics cost $900 a week, her business brings in $620, the only job pays $790,
so under the floor she will not take it. He asked: "if she takes the job, is there a potential her wage could
actually rise. More than if her business brings in more money." Then: "So what you're saying is here, expenses is
$900. She currently makes $620 out of her small business, but she won't take a job because the job pays less than
her expenses, the problem is. Is it just stated to me that she'd still keep her small business? So there be an
income in there plus what should get as a wage? So by that combination, it would be better for her to take the
job. Because it would be more than combined would be more than the expenses."

Put back to him: take the job when the job's pay plus what her business would still bring in covers her basics
($790 and about $200 is $990, over $900). He said: "Yes, that makes a lot more logical sense. And he's more
realistic."

## The trace

Scratch probes, the world's own settings, 27 towns (seeds 1 to 27), the floor on and off.

| People with no job, at year 60 | Floor | No floor |
|---|---|---|
| running a small business | 1,663 | 850 |
| of whom unhappy | 241 (14%) | 39 (5%) |
| on a side hustle | 230 | 98 |
| of whom unhappy | 160 (70%) | 36 (37%) |

Of the 241 unhappy business owners with the floor: 80% took in less than their basics; 74% had a least they would
take above the going wage (in the middle $1,535 against $793); the middle one had been out of work 454 weeks.
Without the floor the middle unhappy one had been out of work 7 weeks.

With the floor, 99 of the 241 unhappy business owners had no home, against 114 of the 1,422 happy ones; on a side
hustle 89 of 160 unhappy against 4 of 70 happy. Someone who rents or has no home has basics above the going wage
(rent about $355 to $894 a week, food about $430), so the floor shut them out of a typical job.

Read in the code: taking a job does not close a business (`labour.hire` leaves it; it stops only for no hours or
too few customers over a quarter). A job takes 40 of a person's 60 free hours, so the business goes on in what is
left. The floor set the job's pay alone against the whole basket.

Also seen, not traced: for someone going without appliances, the lowest price on record was $5,214 to $33,568 a
week in 22 of the 27 towns, and for a home $112,140 a week in seed 21 and $26,038 in seed 24. Such a person's
floor is far above any job. It touches 19 of the 241 unhappy business owners.

The counts above are everyone in the 27 towns together. The figures given earlier (14% against 4% for business
owners, 52% against 26% on a side hustle) were the average of the 27 towns' shares; both come from the same towns.

## What was built

- A dial `floor_counts_kept_business` (J), on, in `RTR_ONLY` and `rtr/settings.json`.
- `labour.reservation_wage`: the floor is their basket (without the home loan payment) less what a business of
  their own would still bring in beside a job, never below nothing. What they held out for before, from their last
  wage, is not lowered by it. Someone with a large loan still has no floor at all (his rule).
- `rtr_makers.kept_with_a_job(town, hustle)` (C): its takings less goods a week over the last quarter, in
  proportion to the hours it would have beside a job against the hours a week it used then (never more than all of
  it), less what its staff are paid now. The hours beside a job are the owner's week less the job, their road and
  the upkeep of their own things, and the staff's hours.
- The quarter records `gross_week` (takings less goods a week) and `used_week` (hours a week used; for a need,
  plans served times the hours a plan takes).
- A happy maker still takes a job only if it pays more than the business brings in (his "Yes, take it", unchanged).

## Rulings

- Ruling: what the business would still bring in follows the hours it would have, against the hours it used last
  quarter ; takings follow the time put in, and a business that used few of its hours loses nothing to a job ;
  cost if wrong: a business whose customers would not wait for fewer hours is counted at more than it keeps.
- Ruling: the staff's wages are taken off whole ; they are paid the same whatever the owner's hours (the review's
  finding) ; cost if wrong: none found.
- Ruling: the road to the job itself is left out ; it depends on which job, and the floor is reckoned once for
  all the jobs on offer ; cost if wrong: a little more is counted as kept than is, for a long commute.
- Ruling: only the business is counted, not rents of homes they let or dividends ; his words were about the
  business ; cost if wrong: someone with rents coming in is still held to their whole basics. A question for him.
- Ruling: a business with no quarter behind it counts for nothing ; nothing is known of it yet ; cost if wrong:
  for a quarter, a new maker is held to their whole basics, as before this change.
- Ruling: the hundred towns and the review stand in for the three checked full towns ; the weekly checks read the
  accounts and the places, and this changes only who takes a job ; cost if wrong: a fault in the books from people
  taking jobs differently would not be seen. The whole-town tests in the suite run under the weekly checks.

## Checks

- Tests first: 17 in `tests/test_rtr_floor_counts_business.py`. The first version's tests failed before the code
  (the import was missing); after the review the rewritten tests failed (11 of 17) before the corrected code.
- Deliberate breaks, each put back: 16, all failed a test. The dial ignored; the business not counted; taken off
  what they held out for from their last wage too; a large loan given the floor; the staff's hours left out; the
  wages scaled with the hours; the wages left out; below nothing; the job's hours not taken off; the job's hours
  fixed at 40; the road left out; the old week's hours used; no cap at what it used; the quarter's takings with the
  wages off; plans not turned into hours; hours trades turned into plans.
- With the dial off, 15-year towns of 200 match `develop` event for event: RTR seeds 5 (45,442 events) and 11
  (67,639); WEF seeds 5 (106,514) and 11 (77,012). The reviewer matched RTR seeds 3 and 8 too. With it on, RTR seed
  5 makes 37,089 events and seed 11 58,907.
- The WEF world's reference town (seed 74, `08251209eb136522`) cannot be run on this machine: its settings file is
  on the desktop only. Its fixed pages and pinned towns are in the suite.

## Review

A fresh reviewer, no part in the build, read the change.

- Final: fixed (Important) the staff's wages were scaled down with the hours, though `profit_week` is after wages:
  a business with one worker on $1,000, taking $2,000 over 100 hours, was counted as keeping $600 beside a job
  instead of $200. Now its takings less goods follow the hours and the wages come off whole.
  `test_with_staff_the_takings_follow_the_hours_and_the_wages_do_not`, RED then GREEN.
- Final: fixed (Important) this week's hours were set against last quarter's share used: someone just let go was
  reckoned on their old week's hours (nothing kept the first week, a third for the rest of the quarter). Now the
  hours beside a job come from the owner's week as it is, against the hours a week it used.
  `test_just_let_go_her_hours_beside_a_job_are_reckoned_from_now_not_from_her_old_week`, RED then GREEN.
- Final: fixed (the reviewer's untested cases) the business taken off what they held out for from their last wage,
  and the job's hours fixed at 40: tests added, and both are now deliberate breaks that fail.
- Final: minor (deferred) the road to the job is left out (a ruling above).
- Final: minor (deferred) a side hustle started part way through a quarter has its takings spread over the whole
  quarter, as before this change.
- Final: minor (deferred) no whole-town test shows the dial reaching small-business hiring and the line a firm
  reads; the towns above, with the dial on and off, differ.

## The towns

A hundred RTR towns, 60 years, `rtr/batches/floorbiz-rtr`, against `rtr/batches/ownwork-rtr` (develop). All 100
survived in both; none reached the failure line. The middle town:

| | Year 20 before | after | Year 60 before | after |
|---|---|---|---|---|
| unhappy | 6.3% | 5.1% | 19.9% | 18.6% |
| no employer | 6.5% | 5.2% | 8.1% | 6.2% |
| running a small business | 4.1% | 3.2% | 7.1% | 5.5% |
| on a side hustle | 1.9% | 1.4% | 0.6% | 0.4% |
| jobless (no work at all) | 0.1% | 0.1% | 0.1% | 0.1% |
| staff wage a week | $922 | $909 | $858 | $840 |
| rate offered someone new | $806 | $780 | $810 | $758 |

The worst town at year 60: 48.2% unhappy before, 49.8% after; the lowest rate offered someone new $598 before,
$559 after. More people now stand in the line for a job, and a firm may cut its rate for newcomers when the line
is long (his rule), so the rate offered fell a little.

The 27 towns of the trace again, with the new rule, at year 60:

| People with no job | Before | After |
|---|---|---|
| running a small business | 1,663 | 1,335 |
| of whom unhappy | 241 (14%) | 208 (16%) |
| on a side hustle | 230 | 184 |
| of whom unhappy | 160 (70%) | 132 (72%) |
| unhappy business owners: middle weeks out of work | 454 | 287 |

Fewer people are out of work running a business, and they are out of work for less long. But the share of them
unhappy did not fall. Of the 208 unhappy business owners, 144 still have a least-they-will-take above the going
wage, and for all but 14 of those the business is counted. Their basics are the cause: in the middle $2,297 a
week, against $709 for a happy business owner; 113 of the 144 have basics more than twice the going wage. That
points at the prices seen in the trace (appliances at $5,214 to $33,568 a week for someone going without; a home
at $26,038 and $112,140 a week in two towns). Not traced yet.

The comparison page made again: `rtr/batches/floorbiz-rtr/compare.html`.

## Before the commit

- Full tests: 1,242 passed (7 minutes 10 seconds, alongside the hundred towns).
