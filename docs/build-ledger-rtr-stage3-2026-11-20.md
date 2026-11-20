# Build ledger: the RTR world, stage 3 (seeing), 20 November 2026

Plan: `docs/superpowers/plans/2026-11-20-rtr-stage3-seeing.md`. Design: `docs/superpowers/specs/2026-11-16-rtr-world-design.md`, section 12 and the list of stages.

## Jason's words

- "how much more work have we got to do to get RTR finished? Currently we spent three days on this and I'm running out of fable"
- "Yes, write the plan for stage 3"
- To "Does it cover what you want?": "yes"

## What does not change

No rule of either world changes in this stage, nor any dial, nor any event. The WEF world's pages are kept as they were made by `develop` before this stage (`tests/expected/`, made on 20 November from the code of `develop` at `e6343ee`): a small WEF town's dashboard and town view, a small WEF batch's page and its yearly figures. `tests/test_wef_pages_unchanged.py` holds them byte for byte, save the code's own fingerprint in the small print, which changes with any change to the code.

## Task 1: the RTR world's charts on the town dashboard

A section of its own, "Owning, letting and side hustles", with five charts, and two tiles in the header. Drawn only for a run whose record has the RTR world's measures; a chart whose measure a record lacks is left out.

- Ruling: who holds the homes is drawn as lines (homes standing; lived in by their owner; let by a small landlord; taken back by the bank), not as a stack with landlord firms as the rest ; a stack needs the firms' part worked out by subtraction, and the record has a case where that would count a home twice (a home taken back with its tenant kept stands both with a landlord firm and among the homes people own) ; if wrong, the reader works out the firms' share by eye.
- Ruling: "lived in by their owner" is the homes people own (`homes_owned`) less those they let (`homes_let_private`) ; `homes_owned` counts every home a person owns, let or not: in a small town of 74 owned homes, 18 were let and 56 lived in by their owner, and 56 + 18 = 74 ; if wrong, a home owned and standing empty is counted as lived in.
- Ruling: the RTR section is put into the page only for a run that has it, by replacing two pieces of the page's text ; so the WEF world's page stays the page it was, byte for byte ; if wrong, a change to those two pieces would stop the page building, and the build says so.

Checks:
- Tests first, seen to fail (4 failed for the missing charts and tiles), then pass: 17 in `test_dashboard.py` and `test_wef_pages_unchanged.py`. One test of mine was wrong and was put right: it compared a line's last point with the last quarter's average, but every line on the dashboard ends on the final week's own value.
- Town 9 of the forty full towns (sixty years) rebuilt with the new section, on a copy: at year 60, 1,251 homes standing, 850 lived in by their owner, 389 let by small landlords, 12 held by the bank, so none held by landlord firms; staff paid $672.60 and the rate for someone taken on $242.73; 304 people with a side hustle, 151 of them grown into small businesses.

## Task 2: the RTR world's measures in a batch and on the batch page

A batch now also keeps, for each town at the end of each year, eight measures of the RTR world (`batch.RTR_MEASURES`), and the batch page draws a chart of each across the towns (`batchpage.RTR_CHARTS`): the rate for someone taken on now, homes lived in by their owner, homes let by a small landlord, homes taken back by the bank, appliance sets owned, loans against homes, people with a side hustle, small businesses.

- Ruling: the RTR world's measures are a list of their own beside the WEF world's, not added to it ; three older tests hold that a batch keeps exactly the thirty measures the design names, and for the WEF world that stays true ; if wrong, nothing is lost: both lists are read wherever a batch's measures are.
- Ruling: "homes lived in by their owner" is worked out when the batch reads each town (homes owned less homes let) and kept as a measure of its own ; the batch keeps a town's measures, not sums of them ; if wrong, it can be worked out again from the two it is made of.

Checks: three tests first, seen to fail, then pass (an RTR batch of two small towns keeps each measure every year and agrees with the towns' own records; its page draws each; a batch made before still builds, leaving out what it lacks). The batch tests and the WEF pages tests: 149 pass.

## Task 3: owners and side hustles on the town view

Each person in an RTR town's view now carries two change lists: `ow`, whether they live in a home they own, and `hu`, whether they have a side hustle. On the map someone who lives in a home they own has a short line under them, and someone with a side hustle a short tick above and to the right; both are said in the key, and on the person's card ("Lives in a home they own" in place of "Has a home"; "Runs a side hustle"). A WEF person carries neither, and a WEF town's page is byte for byte what it was.

- Ruling: the marks go on people, not on homes ; the design says "marks homes lived in by their owner", but the map draws a block of many homes as one, so a home on its own cannot be picked out, and the person living in it can ; if wrong, a block that is mostly owners does not look different from one that is mostly tenants.
- Ruling: someone lives in a home they own when their week's record has a home but no landlord (`home_firm` empty, `home_unit` set) ; the homes' own record (taken each quarter) agrees in every week it was taken, which a test holds ; if wrong, a tenant of a small landlord could be read as an owner, and the same test would fail.
- Ruling: a side hustle runs from the week of `hustle_started` to the week of `hustle_stopped` or of `maker_company` (when it becomes a firm) ; these are the only events that open and close one in the code ; if wrong, a hustle ended another way would stay marked.
- Ruling: the marks are lines in the text colour at widths no other stroke on the map has (1.5 and 1.1) ; a shape, not colour alone, and the page tests can tell them apart ; if wrong, a later stroke at the same width would be miscounted by the tests, not shown wrongly.

Checks: five tests first, seen to fail, then pass. One mistake of mine on the way: a helper I added to the page tests' stand-in browser (`T.frame()`) hid one already there (`T.frame`), and two older tests failed; it was taken out. Town view, page and WEF pages tests: 174 pass. Town 9 (sixty years) rebuilt with the marks, on a copy: built in 8 seconds, 26 MB.

## Task 4: both worlds side by side

`python3 -m engine compare <WEF batch> <RTR batch>` (`engine/comparepage.py`) writes `compare.html` beside the RTR batch, or in `--out`. It refuses, in plain words, unless the first batch is of the WEF world, the second of the RTR world, each has one setting and both finished the same seeds; a batch whose table is not yet made is collected first. The page: the answer first (how many towns reached the failure line in each world, when, and the four cases seed by seed); town for town, one row a seed; the measures both worlds keep, the two worlds on one chart each (the middle town as a line and the middle half as a band, the WEF world solid, the RTR world broken); what only the RTR world has; how to read it, starting with the towns that drop out of the yearly figures when they fail.

- Ruling: "lasted longer" counts a town that never reached the failure line as lasting longer than one that did, and two that failed in the same week as "the same" ; it is the plainest reading of "lasted" ; if wrong, a town that stood sixty years on nine in ten unhappy reads as the better one, and the page says so in "how to read this".
- Ruling: each world's chart shows the middle half of its towns, not the whole range ; two whole ranges on one chart hide each other ; if wrong, the reader misses the extreme towns, which the RTR world's own charts and each batch's page still show.
- Ruling: the page borrows the batch page's look, styles and tips ; one look for both kinds of page, and no new page code to test ; if wrong, nothing is lost.

Checks: nine tests first (collection failed with no `comparepage` to import), then pass: town for town matches each batch's own record of when each town failed; the four cases add up to the seeds; the longer-lasting town is named right; the page has every part in order, names both worlds, fetches nothing and has no em dash; the command writes the page and says where, and refuses the worlds the wrong way round; the wrong worlds, different seeds and more than one setting are refused; a batch with no table yet is collected first.

## Task 5: the two batches of a hundred towns

Run on Jason's second machine, thirty towns at a time (his word on load: "Can you do more than one processor? You've got 32 and 128 gigs of RAM"), from the code of this branch, each world as it ships (no cap on people, sixty years): `wef/batches/stage3-wef` (seeds 1 to 100, about 5 minutes) and `rtr/batches/stage3-rtr` (seeds 1 to 100, about 51 minutes). No town crashed. `python3 -m engine compare wef/batches/stage3-wef rtr/batches/stage3-rtr` wrote `rtr/batches/stage3-rtr/compare.html`.

**The answer, as counted by Claude (before the review):**

| | WEF world | RTR world |
|---|---|---|
| reached the 90% line | 100 of 100 | 7 of 100 |
| when | first in year 14.50, middle 17.76, last 22.21; half by year 17.75 | years 52.0 (seed 23), 57.8 (98), 58.0 (50), 58.3 (75), 59.3 (5), 59.3 (24), 59.6 (27) |
| seed by seed, lasted longer | 0 | 100 |

Both failed on 7 seeds (the RTR town later in all 7), only the WEF town on 93, only the RTR town on none. The four RTR seeds of the forty-town run that failed (5, 23, 24, 27) fail here too, in the same years.

At the end: the WEF towns when they failed had 15% to 49% with no job (middle 30%), staff paid $595 to $848 (middle $796), 1,106 to 1,220 people. The 93 RTR towns that stood, at year 60: 32% to 88% unhappy (middle 74%; 27 above 80%, 6 above 85%), 0% to 30% with no job (middle 0%), staff paid $356 to $968 (middle $725), the rate for someone taken on now $91 to $948 (middle $583). The RTR world's middle town year by year: unhappy 9% at year 10, 11% at 20, 22% at 30, 60% at 45, 74% at 60; staff paid $959, $881, $862, $830, $725.

The RTR world did not reach the line in ninety-three towns in sixty years, and its towns were still getting worse at year 60. Nothing here is traced: not why the WEF towns fail in years 14 to 22, nor what drags the RTR towns down.

**The basket in the RTR world misleads.** In the RTR world "Basket against the staff wage" climbs to a middle 11,200% at year 60. Traced in one town (seed 9): at year 60, 1,239 of 1,251 homes are owned by people, one landlord firm is left, and its asking rent is $96,733 a week; the basket is the cheapest asking price of each need, so that one firm's rent is the basket's housing. Food, which people buy, is $271 a week against staff pay of $673. A note says so on the comparison page (test first). The measure itself is the WEF world's, and is not changed: whether the RTR world should measure what people pay is Jason's to say.

**Under the weekly checks** (`rtr/batches/checked-stage3/run_checked_full.py`, not in git, the cap check left out as before): seeds 1, 2, 3 of each world, clean every week: the WEF towns through 884, 936 and 1,040 weeks to their failure in years 17, 18 and 20; the RTR towns all 3,120 weeks. Each is the same town as in its batch.

## Review

One fresh reviewer, with no part in the build, on the comparison page and its numbers (the first one sent was stopped before it reported; it was sent again). It recounted from the 200 towns' own records, not from the batch tables: every row of the town-for-town table, the four cases, the longer-lasting world, and the first, middle, last and half-failed years of both worlds, **0 mismatches**; seven measures' yearly tables, all sixty years, 0 mismatches, and its own rows fed through the chart code gave the page's charts byte for byte; no town counted in a year it had failed. Its main claim checked with Claude's own count before anything was changed: at year 60, landlord firms had no tenants in 92 of the 93 RTR towns standing and held no homes in 43; the middle town's basket was 71% the asking rent of homes and 14% that of appliance sets. Both counts agree.

- Final: fixed (Important): **the basket note blamed "a landlord firm with few tenants left", and only in the notes at the foot of the page.** The firms have no tenants at all in nearly every town, and the appliance firms' asking prices count too. The note now says so, and the two cards themselves ("Weekly basket", "Basket against the staff wage") say they are asking prices that in the RTR world may be those of firms with no tenants or customers. `test_the_basket_cards_themselves_say_they_are_asking_prices_nobody_may_be_paying` RED then GREEN.
- Final: fixed (Important): **"More than half never did" overstated the RTR world**, and the headline gave no horizon. The towns were stopped at sixty years and were getting worse: RTR towns at or above 80% unhappy were 0 at year 30, 3 at 40, 7 at 50 and 27 of 93 at 60 (the reviewer's count). The headline now says "Both in 60 years"; "never" is gone; the answer says, for each world, how many towns still standing at the end had 80% or more unhappy, and that a town under the line when stopped may be on its way to it. `test_the_answer_says_the_horizon_and_never_says_never` RED then GREEN. One slip of Claude's in the fix: this batch's own figures were first written into the page's fixed text, which would be wrong for any other pair of batches; taken out the same hour, and kept here instead.
- Final: minor (deferred): the comparison checks the worlds, one setting each and the seeds, but not that both batches ran the same years, weeks a year, shared settings and code. For these two the reviewer diffed them: they differ only in `world` and the RTR world's own dials; both sixty years, 52 weeks, the same code.
- Final: minor (deferred): an unfinished batch is not refused, and a batch table older than its towns is used as it is.
- Final: minor (deferred): "the middle one of those in year 17.76" is a middle worked out between two towns (17.75 and 17.77), set beside "half had failed by year 17.75".
- Final: minor (deferred): the WEF world's last points on the yearly charts rest on very few towns (4 in year 21, 1 in year 22); each chart's table shows how many.

## A test that fails now and then, from before this stage

`tests/test_batch.py::test_ctrl_c_at_the_keyboard_stops_a_batch_running_several_towns` failed in one of four full runs on this machine: it presses Ctrl-C on a batch running two towns at once and expects two in flight, and at that moment there was one (one town had just finished, the next not yet started). With this stage's changes set aside, on `develop`'s code, it failed once in eight runs of that test alone. So it is a race in the test, older than this stage, seen on a fast machine. Not fixed here: a change to a test, for Jason's word. The suite is run again until it passes whole before any commit, and this is said when it is.
