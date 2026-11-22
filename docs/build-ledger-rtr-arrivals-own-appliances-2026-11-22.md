# Build ledger: the RTR world, a newcomer does not rent appliances that cost more than owning (22 November 2026)

Branch `feature/rtr-arrivals-own-appliances`, off `develop` at `5f88caf`.

## His words

After the fix to how someone going without appliances is measured
(`docs/build-ledger-rtr-appliances-at-owning-2026-11-22.md`), the review there found a newcomer buying a home held
back four weeks of the appliance firm's runaway rent. He said: "Okay, let's trace back the appliance issue. A
newcomer is only renting a house. A rented house can also buy appliances, not just rent them. Is that what's
happening? So a newcomer must rent before they can buy, but that only applies to the house, not appliances. Who
would pay $9,000 if they could pay $23."

Read in the code and put to him: on arrival every newcomer signed up for each base need at the cheapest firm,
whatever it charged (`subscriptions.sign_up_for_the_rest`), so they took on the appliance rent ($9,417 a week in
seed 1 at year 60); and a newcomer buying a home held back four weeks of base needs at those rents
(`rtr_owning.newcomer_keeps`), about $37,700. The fix put to him: on arrival, if renting appliances costs more
than owning a set, they build their own straight away if they can pay for the parts, or go without until they
can, as anyone in town does; the holdback counts appliances at what owning costs. He said: "yes, build it".

## What was built

- A dial `arrivals_own_appliances` (J), on, in `RTR_ONLY` and `rtr/settings.json`.
- `subscriptions.sign_up_for_the_rest`: a newcomer offered a set to rent for clearly more than owning one costs a
  week (owning below the rent less `switch_friction`, the test anyone in town uses) does not sign up for it on
  arrival; they start a set of their own if they can pay for the parts (`rtr_owning._start_set`).
- If they cannot, the week's review (`household._take_up`) rents them one only if they can afford it, by the
  test everyone in town uses: at $9,417 a week almost nobody can; at the opening $55 most can.
- `household._take_up`: someone building a set of their own does not take up a rental meanwhile.
- `rtr_owning.newcomer_keeps`: appliances count at no more than owning a set costs a week.

## Rulings

- Ruling (put to him before the commit; he asked whether they could not just buy a set, was told owning means buying the parts and building it or paying a set builder, as in the design of 16 November, and said "ok, commit, merge and push it"): "go without until they can" is not read literally ; the rent starts at
  $55 a week against about $25 to own, and most newcomers cannot pay $5,400 for the parts, so read literally most
  would have no set from the first week, though a $55 rent is one anyone in town would take ; the newcomer is
  treated as anyone in town is: they rent only what they can afford ; cost if wrong: if he meant newcomers to go
  without rather than rent at all, they now rent at the opening rent.
- Ruling: owning must be clearly cheaper, by the same `switch_friction` (5%) as someone in town switching from a
  rented set ; one rule for both ; cost if wrong: none found.
- Ruling: a newcomer who arrives with no job has no personal credit, so only their cash buys the parts ; that is
  the bank's rule for anyone with no job ; cost if wrong: fewer newcomers build at once; they build at a later
  quarter, as anyone in town does.
- Ruling: someone in town with no set may still rent at a runaway rent if they can afford it ; the review's
  affordability test, his rules, and the quarterly look at owning cover them ; cost if wrong: a rich resident pays
  a runaway rent for up to a quarter.
- Ruling: the whole-town tests of the stages before hold the new dial off (`BEFORE_OWNERS_PAY` in
  `tests/conftest.py`) ; their seeds were picked for the world as it was ; cost if wrong: none; the towns as the
  world now ships are run in `test_rtr_rulings.py`.
- Ruling: the towns as shipped in `test_rtr_rulings.py` were picked again, as on 21 November: thirty of each
  kind, all sixty clean under the weekly checks; on the map seeds 3 and 9, with no map seeds 21 and 27, the pairs
  that between them reach every rule with the fewest weeks of more than half out of work (4 and 0) ; the rule
  changes every RTR town from the first week, and the old seeds no longer reached every rule (on the map, one of the rulings of 19 November and seven rules of the stages before) ; cost if wrong:
  none; the test asks the same of them.
- Ruling: the page test's small RTR town (`tests/test_townview.py`) is seed 9, not 3 ; it needs side hustles
  that stop, and none stopped in seed 3 any more ; cost if wrong: none.
- Ruling: the holdback test of 18 November (`test_they_hold_back_four_weeks...`) now expects appliances at no more
  than owning costs ; that is the new rule ; cost if wrong: none.

## Checks

- Tests first: `tests/test_rtr_arrivals_own_appliances.py`, 15 tests. The first 10 failed before the code (the
  dial did not exist). After the review, the rewritten tests failed (4) before the revised code.
- Under the rule 10 older tests failed; dealt with as ruled above.
- Deliberate breaks, each put back, on the revised code: 12, all failed a test (the dial ignored; the WEF world
  not shut out; renting on arrival anyway; never building; no friction; skipping a cheap rent too; every need,
  not appliances; renting while building; the building guard ignoring the dial; the holdback at the rent; the
  holdback ignoring the dial; the holdback always at owning).
- With the dial off, 15-year towns of 200 match `develop` event for event: RTR seeds 5 (37,089 events) and 11
  (58,907); WEF seeds 5 (106,514) and 11 (77,012). The reviewer matched WEF and RTR seed 3. With it on, the towns
  change from the first year (RTR seed 5: 40,549 events; seed 11: 50,202 in the first version).
- Full tests: 1,265 passed.
- The WEF world's reference town (seed 74) cannot be run on this machine.

## Review

A fresh reviewer, no part in the build, read the first version.

- Final: fixed (Critical) the week's review rented the newcomer a set anyway, at the same rent, if they could
  afford it, even while they were building one: in a 15-year town 198 of 200 newcomers who declined on arrival
  rented in the same week, 23 of them having just paid $5,400 for parts. Now nobody rents while building, and the
  review's affordability test decides the rest. `test_a_newcomer_who_can_pay_for_the_parts_builds_a_set_and_does_not_rent_one_that_week`
  and `test_someone_in_town_building_a_set_does_not_take_up_a_rental_meanwhile`, RED then GREEN.
- Final: Ruling (Important, the rule reaches every RTR town from week 0) : kept, and said to him ; owning a set is
  cheaper than the opening rent, so newcomers who can pay for parts build from the start, as people in town
  already did at their first quarter ; cost if wrong: towns differ from the first year.
- Final: fixed (Minor) no friction against owning, unlike someone in town: added.
  `test_owning_must_be_clearly_cheaper_as_for_anyone_in_town`, RED then GREEN.
- Final: minor (deferred) the four weeks of bills held back before buying parts leave out entertainment, which a
  newcomer signs up for after appliances.
- Final: minor (deferred) a buyer's holdback counts appliances at about $100 for four weeks and not the $5,400 of
  parts; most buyers then rent or go without until a later quarter.
- Final: minor (deferred) no test runs a newcomer in through `new_worker`, a founder's arrival or the week-0
  founders; the whole towns do.

## The towns

A hundred RTR towns, 60 years, `rtr/batches/arrivals-rtr`, against `rtr/batches/appliances-rtr` (develop). All
100 survived in both. The middle town:

| | Year 20 before | after | Year 60 before | after |
|---|---|---|---|---|
| unhappy | 6.4% | 5.1% | 20.8% | 20.5% |
| no employer | 5.4% | 4.7% | 5.2% | 5.3% |
| staff wage a week | $915 | $928 | $851 | $848 |
| rate offered someone new | $792 | $811 | $776 | $755 |
| sets of their own | 818 | 820 | 895 | 900 |

On every one of these, town by town, about as many towns went up as down (unhappy at year 60: 50 up, 50 down).
Read as the towns going different ways, not as an effect of the rule: it touches only newcomers offered a rent
above what owning costs, and only those who could pay for parts at once or would have rented a set they could not
afford. How newcomers fared was not counted on its own.

The comparison page made again: `rtr/batches/arrivals-rtr/compare.html`.
