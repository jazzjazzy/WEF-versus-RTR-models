# RTR world, stage 3: seeing. Build plan

**Goal:** show what the RTR world records on its pages, then run both worlds on the same
hundred seeds and set them side by side, town for town. This is the last stage of the RTR
world in the design.

**Design:** `docs/superpowers/specs/2026-11-16-rtr-world-design.md`, section 12 (the record
and the pages) and the list of stages: "3. **Seeing.** The new measures on the pages; then
the WEF and RTR batches on the same 100 seeds, side by side. The WEF batch must be made
again first: the one of 16 November was made before the cap on people was dropped."

**Written:** 20 November 2026, by Claude, at Jason's word: "Yes, write the plan for stage 3".

## What is there now (read in the code, 20 November)

- The RTR world already records its weekly measures (`engine/metrics.py`): `homes_owned`,
  `homes_let_private`, `small_landlords`, `homes_foreclosed`, `sets_owned`, `home_loans`,
  `makers`, `maker_customers`, `small_businesses`, `wage_offer`, and more. Each home in
  the record has an `owner` (`units` table).
- No page shows any of them. `engine/dashboard.py`, `engine/batchpage.py`,
  `engine/townview.py` and `engine/townpage.py` do not name one.
- A batch keeps 33 yearly measures (`engine/batch.py`, `MEASURES`). None is an RTR measure.
- Nothing puts two batches on one page. A batch can vary a dial, but not the world: the
  world is the folder a town is run from, and a batch refuses `world=`.

## Rules for this stage

- **The model does not change.** No rule of either world, no dial, no event. Only what is
  drawn from the record. So the parts of the process that are about rules (deliberate
  breaks of a rule, dials-off equal to `develop`, a reviewer for how a firm reckons) have
  nothing to bite on. What still holds: tests first, a ledger, the full tests before any
  commit, nothing committed, merged or pushed without Jason's word.
- **The WEF world's pages must not change.** A WEF run's dashboard and town view, and a
  WEF batch's page, come out byte for byte as they do today. Each task below has a test
  for that.
- **The WEF reference town** (`08251209eb136522`, 180,377 events) cannot change, since no
  rule changes. Its check needs a settings file that is on the desktop only
  (`wef/batches/20261113-as-written/towns/as_written/seed-0074/config.json`). Copy it
  across, or skip that one check and say so in the ledger.
- Plain words on every page. No em dashes. Say "WEF world" and "RTR world".

## Tasks

### Task 1. The RTR world's charts on the town dashboard

`engine/dashboard.py`, tests in `tests/test_dashboard.py`.

A new section of charts, drawn only when the run's `world` is `rtr`:

1. **Who holds the homes**, a stack by year: lived in by their owner (`homes_owned`), let by
   a small landlord (`homes_let_private`), taken back and empty (`homes_foreclosed`), and
   the rest, held by landlord firms (`homes` less the three).
2. **What staff are paid and what a newcomer is offered**, two lines: `wage` and
   `wage_offer`. This is the gap Jason's "old staff keep their pay" rule makes.
3. **Side hustles**: makers, their customers, and small businesses grown from them.
4. **Owning**: appliance sets owned, small landlords.
5. **Loans against homes** (`home_loans`).

Two header tiles for an RTR run: homes lived in by their owner at the end, and makers at
the end.

Tests, written and seen to fail first:
- an RTR small town's dashboard has each of the five charts, with the right series;
- the homes stack adds up to the homes standing, every year;
- a WEF small town's dashboard is byte for byte what `develop` makes (save the page from
  `develop` first, as the expected file);
- an RTR run recorded before a measure existed still builds its page, with the chart left
  out, not broken.

### Task 2. The RTR world's measures in a batch and on the batch page

`engine/batch.py` (`MEASURES`), `engine/batchpage.py` (`CHARTS`), tests in
`tests/test_batch.py` and `tests/test_batchpage.py`.

Add to the yearly measures: `wage_offer`, `homes_owned`, `homes_let_private`,
`homes_foreclosed`, `sets_owned`, `home_loans`, `makers`, `small_businesses`. A WEF town
records none of them, so a WEF batch keeps none.

Add a chart to the batch page for each, drawn only when the batch holds it.

Tests:
- an RTR batch of two small towns keeps each new measure for every year it stood;
- its page has the new charts;
- a WEF batch of two small towns keeps exactly the rows it keeps today, and its page is
  byte for byte what `develop` makes;
- `batch-report` on a batch made before this change still builds.

### Task 3. Owners and side hustles on the town view

`engine/townview.py` (the data), `engine/townpage.py` (the page), tests in
`tests/test_townview.py`, `tests/test_townpage_dom.py`, `tests/test_townview_js.py`.

The design: "The town view marks homes lived in by their owner and people with a side
hustle." Each week the view already knows which home each person is in. Add: whether that
home is lived in by its owner (from `units.owner`), and whether the person had a side
hustle. Draw both with a mark that is not colour alone, and a line in the key.

Tests:
- in an RTR small town, the view's data marks a home as lived in by its owner in the week
  the record says it was bought, and stops in the week it was sold or taken back;
- a person is marked in the weeks they ran a side hustle;
- the page draws the marks and the key (driven in the page tests the stage 3 review of
  13 November set up);
- a WEF run's town view is byte for byte what `develop` makes.

### Task 4. Both worlds side by side

A new command, `python3 -m engine compare <WEF batch> <RTR batch>`, and a new page,
`engine/comparepage.py`, tests in `tests/test_compare.py`.

It refuses, with a plain message, unless the first batch is of the WEF world, the second
of the RTR world, and both ran the same seeds with one setting each. It writes
`compare.html` beside the RTR batch (or to a folder given).

The page, in this order:
1. **The answer first:** how many towns reached the 90% line in each world, and by when
   half of them had (or that half never did).
2. **Town for town:** one row per seed. In the WEF world: failed in year N, or stood sixty
   years. The same in the RTR world. Then which world's town lasted longer. Counts of each
   case at the top: both failed, only the WEF town failed, only the RTR town failed,
   neither failed.
3. **The measures side by side:** for each measure both worlds keep (unhappy, wage, basket
   against the wage, with no job, people, cash of the middle person, shares held by the top
   tenth, homes empty, firms), the spread across the towns still standing each year, the
   two worlds on one chart. Reuse the batch page's charts.
4. **What only the RTR world has:** the new measures of task 2, for the RTR towns.
5. **How to read it:** towns that failed drop out of the yearly figures, so a world whose
   towns fail early can look better in later years than it is. Say so on the page.

Tests:
- two small batches, one per world, same seeds: the page has every part above and the
  counts add up to the number of seeds;
- the town-for-town table matches each batch's own record of when each town failed;
- the command refuses the wrong world, the two worlds the wrong way round, different
  seeds, and a batch with more than one setting.

### Task 5. The two batches of a hundred towns

On the second machine (32 processors; Jason's word on load: "Can you do more than one
processor? You've got 32 and 128 gigs of RAM"). Thirty towns at a time. No building.

1. From `wef/`: `python3 batch.py stage3-wef --seeds 1-100 --jobs 30 --quiet`. This is the
   WEF batch made again with no cap on people, as the design asks.
2. From `rtr/`: `python3 batch.py stage3-rtr --seeds 1-100 --jobs 30 --quiet`.
3. `python3 -m engine compare wef/batches/stage3-wef rtr/batches/stage3-rtr`.
4. Three of the RTR towns and three of the WEF towns again under the weekly checks
   (`rtr/batches/checked-debt1911/run_checked_full.py`, adapted for the WEF world).

Expected time: the RTR towns took 6 to 8 minutes each this week, so about half an hour for
a hundred at thirty at a time; the WEF towns fail sooner and should be quicker. Before
saying anything about the result, look at how the towns fared, not only the counts: open a
few of each world on the town view, including the ones that differ most.

### Task 6. The record

- A ledger, `docs/build-ledger-rtr-stage3-2026-11-20.md`: Jason's words, every ruling of
  Claude's (`Ruling: what ; why ; cost if wrong`), every check, and the two batches' results
  as they came.
- The design's "Built so far" says stage 3 is built, and what it shows.
- `rtr/README.md`: the top note no longer says stage 3 is not built; a section with the
  side-by-side result.
- `README.md` and `docs/how-this-was-built.md`: a row for stage 3 and the test count.

## Review

One fresh reviewer at the end, with no part in the build, on the comparison page and its
numbers (task 4). That page carries the answer to Jason's question, so it is the one place a
wrong count would mislead the report. It is asked to recount the town-for-town table from
the two batches' own records, and to check that the page says plainly what the yearly
figures leave out. Its main claim is checked with Claude's own count before anything is
changed.

## What this plan does not do

- It does not change any rule of either world.
- It does not answer the questions still open for Jason (who goes first outside a firm in
  debt; what "in debt" means; the revolving door count; the weekly check that assumes a
  cap). None of them blocks this stage.
- It does not write the report on what the two worlds do. That comes after.

## Size

Tasks 1 to 4: about a day of building. Task 5: about an hour or two of the machine, plus
looking at the towns. Task 6: an hour.
