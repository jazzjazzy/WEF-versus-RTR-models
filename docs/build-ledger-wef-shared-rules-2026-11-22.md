# Build ledger: six rules of the RTR world hold in the WEF world too, and the floor needs money coming in (22 November 2026)

Branch `feature/wef-shared-rules`, off `develop` at `65a5a3b`.

## His words

Asked whether there was enough to write the paper, Claude said no: several fixes of the last days repaired
faults both worlds share but went into the RTR world only. He said: "Okay, WEF World, the rule is that you
cannot own anything. Everything has to be rented. ... So the world is rent only. ... Give me a list of the
stuff in the RTR world, point by point, that could be transposable to the WEF world."

Put to him as six rules: the least someone out of work will take never falls below their basics
(`reservation_covers_basket`, Claude's of 21 November); the line that lets a firm cut its wage is those who
would take the job (`line_is_who_would_take`, his of 19 November); a cut is for those hired after it
(`staff_keep_pay`, his); a firm in debt that lost money lets staff go (`loss_sheds_staff`, his); the
longest-serving goes first (`longest_serving_first`, his); going without counts at the lowest price asked
(`going_without_at_lowest_price`, his of 21 November). His words: "From RTR world, all six of these issues
should be the same on both." Then "yes, build it now".

The fresh review then found WEF towns with nine in ten out of work under the six, and traced it to the floor.
Put to him as Sam, a year out of work with no income, basics $1,494 a week, offered a job at $1,445. His words:
"Oh, it's a yes? He has no other income coming in, if that's correct, then his expenses would never get paid."
"So we'd have to take the job there. Even though it's lower than his expenses, he can pay off most of his
expenses." Asked whether Sam would take $100 a week: "If there is no money coming in, he will take any offer that
is put forward to him. Because you can't pay anything if he doesn't have money coming in."

The second review found that a few dollars of dividends brought the whole floor back. Put to him: Sam's shares pay
him $5 a week; "he takes any offer unless the money he already has coming in pays his basics on its own";
someone whose rents bring in $1,600 a week could still hold out. His words: "Yes, that's right".

## What was built

- The six dials leave `RTR_ONLY`, are on in `wef/settings.json`, and are read in both worlds: the `cfg.rtr and`
  gates removed in `labour.py` (`first_to_go`, `demote`, `reservation_wage`), `corporate.py` (`line_share`,
  the loss noted at the review), `subscriptions.py` (`cheapest_prices`) and `town.py` (`own_rates`).
- Inside those blocks the RTR world's own parts keep their gate: what a business would still bring in
  (`floor_counts_kept_business`) and appliances at what owning costs (`going_without_appliances_at_owning`).
- `config.BEFORE_SHARED_RULES`, the six set off; `OLD_RULES` and `wef/before-16-november.json` carry them, so
  the old rules still give the old records.
- A new dial `floor_needs_money_coming_in` (J), on in both worlds: the floor holds only while what someone out of
  work has coming in (`Agent.income_estimate`) pays their basics on its own. Otherwise the least they would take
  is what it was before the floor.
- In the WEF world the most owed on each loan is kept each week when the floor is on
  (`rtr_makers.remember_loans`), so a loan mostly paid off is not counted as large.
- The record keeps `wage_offer` (the rate for someone taken on now) beside `wage` (what staff are paid) in both
  worlds, and the WEF dashboard shows the chart with the town's charts.

## Rulings

- Ruling: `going_without_at_lowest_price` in the WEF world counts the cheapest firm's price, which is what the
  WEF world already did ; it has no neighbours or makers who sell ; cost if wrong: none. With only it off, WEF
  seeds 5 and 11 give the same towns as with it on, event for event. It is opened for one rule in both worlds.
- Ruling: someone with a large loan still has no floor in the WEF world ("take[s] the first job offered", his of
  19 November) ; it is part of the floor as built ; cost if wrong: a few with personal loans take any job.
- Ruling: "money coming in" is `Agent.income_estimate`: a year's dividends spread over the week, the rents of
  let homes with tenants, a side hustle's takings a week over the last quarter ; the model's own reckoning of
  what someone expects to receive ; cost if wrong: a side hustle in its first quarter counts as nothing.
- Ruling: with too little coming in, the least they would take is the formula before the floor (what they last
  earned, less for feeling insecure, less 5% a week out of work), not nothing from the first week ; that formula is
  the WEF world's own from 12 November and was not put to him again ; cost if wrong: for up to twenty weeks after
  losing a job, someone with nothing coming in holds out for a share of their old pay.
- Ruling: Mia's rule (a job beside her business) is unchanged, but under the new dial someone whose business does
  not pay their basics takes any offer, so it reaches only those whose business does ; his later words decide ;
  cost if wrong: none found. Its tests hold the new dial off to test its own reckoning.
- Ruling (C): the record's `wage_offer` and its chart in both worlds ; with staff keeping their pay, what staff are
  paid and what a newcomer is offered differ in the WEF world too ; cost if wrong: none, a measure only. With the
  rule off the WEF record is unchanged.
- Ruling: the whole-town tests that pin records of the WEF world as it was (`test_rtr.py` WEF_PINS,
  `test_wef_pages_unchanged.py`, `OLD_RULES`) hold the six off ; they are records of that world ; cost if wrong:
  none. The WEF world as it now ships runs under the weekly checks in `test_wef_shared_rules.py` and in
  `test_town_invariants.py`, whose towns now run the six and pass.
- Ruling: the weekly checker reads `staff_keep_pay` in both worlds ; it is the rule's own check ; cost if wrong: none.
- Ruling: the RTR towns as shipped in `test_rtr_rulings.py` picked again, as before: thirty of each kind, all sixty
  clean under the weekly checks; on the map seeds 6 and 9, with no map 9 and 12, the pairs that reach every rule
  with the fewest weeks of more than half out of work (0 and 32) ; the new dial changes every RTR town and the
  seeds of the morning no longer reached one rule ; cost if wrong: none; the test asks the same of them.

## Checks

- Tests first: `tests/test_wef_shared_rules.py` (14 of the first 22 failed before the code; the six "as before"
  and rule 6 passed, as expected); `tests/test_floor_needs_money_coming_in.py` (6 failed before the code). The
  threshold was changed after his last answer and its tests rewritten; the break "money coming in is anything
  above nothing" fails them.
- Older tests failed and were dealt with as ruled above; tests that said a rule was not read in the WEF world
  now say what is true.
- Deliberate breaks, each in its own copy: 20, all failed a test.
- With the new dials off, 15-year towns of 200 match `develop` event for event: WEF seeds 5 (106,514 events) and
  11 (77,012) with the six off; RTR seeds 5 (44,541) and 11 (50,996) with `floor_needs_money_coming_in` off.
  With them on, every town changes.
- Full tests: 1,308 passed; the Ctrl-C batch test, which is flaky on this machine, left out.
- The WEF world's reference town (seed 74) cannot be run on this machine; its settings file
  (`wef/before-16-november.json`) carries the six off.

## How the towns fared while building (towns of 500, 15 years, out of work at year 14)

| | WEF seed 2 | WEF seed 3 |
|---|---|---|
| the six on, floor as it was | 94% | 94% |
| the six on, floor off | 4% | 4% |
| the six off (the WEF world as it was) | 18% | 25% |
| the floor holding for any money coming in | 18% | 32% |
| the floor holding only while what comes in pays the basics (as built) | 4% | 13% |

## Review

Two fresh reviewers, no part in the build.

- Final: Ruling (Critical, how the towns fare): with the six on, WEF towns of 500 had 89% to 94% out of work by
  year 14, every check passing ; the floor: basics in a rented world rise past every wage ; put to him; his rule
  built (`floor_needs_money_coming_in`).
- Final: fixed (Important) in the WEF world nobody kept the most owed on a loan, so any loan at all was large
  and took the floor away ; `remember_loans` runs in the WEF world when the floor is on ;
  `test_in_the_wef_world_the_most_owed_on_a_loan_is_kept_so_a_loan_mostly_paid_is_not_large`, RED then GREEN.
- Final: fixed (Minor) the jobseekers' prices were worked out again for each one in the WEF world: worked out once.
- Final: minor (deferred) a firm taken over puts the failed firm's staff at the end of its list though they keep
  their hiring week, so with the longest-serving first they are let go last. It was so in the RTR world already.
- Final: minor (deferred) old saved WEF run settings of 19 to 21 November hold four of the six as true, saved
  then though nothing read them; one loaded now stops on the two missing dials.
- Second review, Final: Ruling (Critical) a few dollars of dividends brought the whole floor back (WEF seed 3,
  300 people, year 9: 130 of 172 out of work had income, the middle of them about $5 a week) ; put to him; his
  rule built: the floor holds only while what comes in pays the basics.
- Second review, Final: fixed (Important) an unchanged test of Mia's rule failed: it holds the new dial off.
- Second review, Final: fixed (Minor) the docstring of `reservation_wage`; tests added for a side hustle and for
  small and large rents.
- Second review, Final: minor (deferred) rents and dividends coming in are not taken off the floor as a
  business's takings are (his open question: do rents and dividends count beside a job).

## The towns

A hundred towns of each world, 60 years: `wef/batches/shared-wef` against `wef/batches/stage3-wef`, and
`rtr/batches/shared-rtr` against `rtr/batches/arrivals-rtr`. The compare page is
`rtr/batches/shared-rtr/compare.html`. Figures are the middle town of the hundred.

The WEF world:

| | before (`stage3-wef`) | now (`shared-wef`) |
|---|---|---|
| towns that reached the failure line | 100 | 100 |
| year it was reached (middle town; first and last quarter) | 17.8 (17.0, 19.2) | 19.0 (18.2, 20.0) |
| out of work, year 15 | 25.7% | 24.7% |
| unhappy, year 15 | 44.1% | 46.1% |
| destitute, year 15 | 247 | 207 |
| wage staff are paid, year 15 | $853 | $967 |
| wage a newcomer is offered, year 15 | not recorded | $830 |
| basics, year 15 | $1,194 | $1,237 |

Every WEF town still reaches the failure line. 73 reach it later than before, 23 sooner, 4 in the same week;
the middle town a little over a year later. Unhappiness at year 15 went up in 50 towns and down in 48.
Staff keep their pay, so what they are paid falls more slowly, while newcomers are offered less.

The RTR world:

| | before (`arrivals-rtr`) | now (`shared-rtr`) |
|---|---|---|
| towns that survived | 100 | 100 |
| out of work, year 10 | 1.3% | 2.2% |
| out of work, year 60 | 0.1% | 0.0% |
| unhappy, year 60 | 20.5% | 20.3% |
| wage, year 60 | $848 | $832 |

All 100 RTR towns survived. Unhappiness at year 60 went up in 53 towns and down in 47; no town had more than half
out of work in any year, before or after.
