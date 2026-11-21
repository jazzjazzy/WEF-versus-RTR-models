# Build ledger: the RTR world, who counts as jobless (21 November 2026)

Branch `feature/rtr-fewer-jobs`, off `develop` at `c910743`.

## His words

After the floor on what someone out of work will take (`docs/build-ledger-rtr-reservation-floor-2026-11-21.md`),
the middle RTR town at year 60 had 8.1% with no job against 3.4% before, and 16 towns over 15% against 2. He said:
"trace why those towns have fewer jobs and Implement the fix."

## The trace

Scratch probes, the world's own settings, the floor on and off.

1. Seeds 91 and 89, every ten years. At year 60 the firms employed about the same with the floor as without it
   (seed 91: 502 against 495; seed 89: 529 against 563). Small businesses employed far fewer (104 against 340;
   120 against 353). Of the 294 in seed 91 counted with no job, 155 ran a small business of their own and 92 a
   side hustle; 47 had no work at all.
2. The first guess was wrong: that a small business, paying the going wage (about $610 a week in seed 91), could
   not hire people whose floor was above it. Counted: the small businesses had nearly every worker they wanted
   (107 wanted, 104 had, at year 60). They wanted fewer because more of their owners did the work themselves.
3. 27 towns (seeds 1 to 27) with the floor and without it, year 60, as a share of the town:

| | With the floor | Without |
|---|---|---|
| counted with no job (no employer) | 8.2% | 4.3% |
| of whom no work at all | 0.4% | 0.2% |
| of whom running a small business | 6.8% | 3.5% |
| of whom running a side hustle | 0.9% | 0.4% |
| working for a firm | 57.3% | 56.5% |
| working for a small business | 34.5% | 39.2% |

So nobody lost work. The jobless rate counted everyone with no employer, and someone running a business of their
own has none. With the floor more people run a business than work for one. The fault is in the measure.

Also seen, not traced: those running a small business are more often unhappy with the floor than without it
(14% against 4% at year 60), and those on a side hustle (52% against 26%).

## What was built

- A dial `jobless_leaves_out_own_work` (C), on, in `RTR_ONLY` and `rtr/settings.json`.
- `metrics.weekly_series`: in the RTR world, `jobless` and `jobless_rate` count those with no employer and no side
  hustle or small business of their own. Three measures beside it, RTR only: `no_employer_rate` (the old figure),
  `own_business_rate`, `own_hustle_rate`. All three are kept for each year in a batch, and the first two are
  charts on the batch page.
- Nothing a firm or a person does reads it. A firm's queue for work in the RTR world is those who would take the
  job (his ruling of 19 November), and `town.jobless_share()`, which a firm reads where that dial is off, is not
  changed.

## Rulings

- Ruling: someone running a side hustle or a small business of their own, with no job, is not jobless ; it is
  work, and under his rulings it is weighed against a job ("take it" only if the job pays more) ; cost if wrong:
  a maker who earns little is counted as working. `own_hustle_rate` shows how many.
- Ruling: a measure only, so no fresh reviewer ; nothing a firm or a person reckons with is changed, and a
  15-year town makes the same 45,442 events with the dial on and off ; cost if wrong: none to the towns; a wrong
  count on the pages, which the tests pin.
- Ruling: the three checked full towns are not run again ; the events are the same with the dial on and off, and
  the weekly checks read the accounts and the places, not this measure ; cost if wrong: none found.
- Ruling: the owner class (who live on their shares) stays counted as it was ; it is the WEF world's count too,
  and changing it would be a second change ; cost if wrong: small: seeds 91 and 89 had at most one at any count (the 27 towns were not counted for it).
- Ruling: the WEF world is not changed ; nobody there works for themselves, so the count is the same ; cost if
  wrong: none.

## Checks

- Tests first: 8 in `tests/test_rtr_jobless_own_work.py`; 7 failed before the code (the WEF one passes by
  design).
- Deliberate breaks, each put back: the dial ignored; the WEF world given the new measures; side hustles still
  counted jobless; the old figure wrong; business and side hustle mixed. All 5 fail a test.
- The same events with the dial on and off: seed 5, 200 people, 15 years, 45,442 events, the same hash.
- `tests/test_worlds.py` keeps its own list of the RTR world's dials; the new one added.
- A hundred RTR towns run again (`rtr/batches/ownwork-rtr`): all 100 made the same number of events as
  `rtr/batches/floor-rtr`, town for town; wage, basket, population and firms the same in all 24,000 town-years; the
  new `no_employer_rate` equals the old batch's `jobless_rate` in all 6,000.
- The middle town: jobless 0.1% at years 20, 40 and 60; no employer 6.2%, 8.8%, 8.1%; running a small business
  4.1%, 6.9%, 7.0%; on a side hustle 1.9%, 1.0%, 0.6%. At year 60 the highest jobless is 9.9% (seed 55); 3 towns
  over 5%. The comparison page made again: `rtr/batches/ownwork-rtr/compare.html`.
