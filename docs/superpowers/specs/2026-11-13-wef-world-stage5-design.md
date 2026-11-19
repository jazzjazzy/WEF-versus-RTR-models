# WEF World, stage 5 design, part 1: many towns

Date: 13 November 2026. Decisions marked **(J)** are Jason's. Choices marked **(C)** are Claude's calls as the builder: each is a dial, a default or a stated simplification, and each is his to overrule.

## 1. Intent and why

Jason, 13 November: "move on to stage 5". The plan given to him on 12 November reads: "Batch runs, then the paper. World two after that reuses most of the machinery."

What he asked of batch runs, from the notes of the 12 November design chat (`docs/design-chat-2026-11-12.md`):
- "Many runs per setting (one run is one town's luck). Results reported as distributions. Sweep the dials to see which ones matter." (J)
- "Log at failure: time to failure, share concentration, which need's price broke first." (J)
- The paper is written from the record, so "every figure in the paper traceable to a run". (J)

So far every result rests on three towns. This part builds the machine that runs many towns under the same rules, gathers what happened to each into one table, and shows the spread on one page. The paper is not started here (section 10).

**Where stage 4 stands, because stage 5 rests on it.** Stage 4 was "checking and tuning so behaviour is sane", given to him as the longest stage. One check is done (why the wage falls on the map). Not done: the fault he ruled on in decision 17 (a landlord builds while homes elsewhere stand empty) is still in the model; sixteen decisions are open; no starting value has been tuned. He chose to move on. So every batch made now is of the untuned model and says so on its page. Many towns per setting is also the tool the remaining checks need, so nothing built here is wasted whichever comes next.

## 2. Goals, non-goals, anti-goals

Goals
- One command runs every setting on every seed, several towns at a time, and can be stopped and started again without redoing finished towns.
- Each town is an ordinary run: its own folder, its own record, the same result as running it alone.
- One table for the batch, built only from the towns' records.
- One page, built only from that table: how the towns ended, how they went year by year, what stood at the end, and, when dials were varied, what each dial did.
- Every number on the page can be traced to a town and that town re-made from its seed and settings.

Non-goals
- The paper. The second world. Any change to a rule of the model.
- Tuning. No default changes because of what a batch shows.
- Every combination of several dials at once. Dials are varied one at a time from the base (section 3).
- Statistical tests. The page shows every town and the spread, with the number of towns beside every figure.

Anti-goals
- An average that hides the towns that have already failed. Every figure by year says how many towns were still standing.
- A page that reads as a finding. It carries the same "Untuned" notice as the other pages.
- A batch whose towns were made by different versions of the code.

## 3. A batch

- A batch has a name, a list of seeds, and one or more **settings**. The first setting is the base: the model as written, plus any dials given with `--set`. Each `--vary dial=a,b,c` adds one setting for each value, changing that one dial from the base. A value equal to the base's own is the base and is not run twice. (C)
- Every setting is run on the same seeds. (C)
- A town is run exactly as `python -m wefworld run` runs it, and stops when it fails. A batch does not take `stop_on_failure=false` (C, after the review): the page reads a town's last week as the week it failed, and for a town run on past its failure that would be false.
- **A lighter record by default (C).** A batch town records every person and firm once a quarter (`snapshot_every=13`), not every week. Every event and every weekly measure is still recorded. Checked before building: seed 2 on the map run this way gives the same events, the same weekly measures and the same record fingerprint as the full record of 12 November, in 37 seconds and 60 MB against about 180 MB. `--full` keeps the weekly record of every person.
- No dashboard or town view is built for a batch town (C). Either can be built later for any town with the commands that already exist.
- Towns are run several at a time, each in its own process. The default leaves two processor cores free. The result does not depend on how many run at once.
- **Stopping and starting.** A town whose folder holds a finished record is not run again. A folder left unfinished is emptied and that town run again. Ctrl-C stops a batch: no new town is started, the towns in flight are let finish, and the table and page are built for what is there; Ctrl-C again drops the towns in flight. (C)
- **One version of the model.** A batch is stamped with a fingerprint of the model's own files: the package without the pages and the tools that only read records (`batch.py`, `batchpage.py`, `dashboard.py`, `townview.py`, `townpage.py`, `__main__.py`). Carrying a batch on with another model is refused, with both stamps in the message, and no town is run while the files on disk differ from the stamp. A fix to a page does not stop a batch being carried on. (C, after the review; the first draft held a batch to the whole code fingerprint, so any page fix orphaned every batch.)
- **The same base, by what it comes to.** A batch is carried on only with the same base and the same record of each town. Settings are compared by the full settings they come to, not by how they are spelt or what their file is called. (C)
- A mistyped dial stops the batch before any town runs.

On disk, under `batches/` (not kept in git, like `runs/`):

```
batches/<name>/
  batch.json                 the plan: seeds, settings, code fingerprint
  towns/<setting>/seed-0007/ one ordinary run folder for each town (the base's are in towns/base/)
  batch.sqlite               the table
  batch.html                 the page
```

## 4. The table (`batch.sqlite`)

Built only from the towns' records and `batch.json`. It can be rebuilt at any time.

- `batch`: the plan and the code fingerprint.
- `settings`: number, name, the dials it changes, and the value it has each varied dial at, read from a town's own record of its settings.
- `towns`: one row for each town: setting, seed, folder, outcome, weeks run, the week it failed, the week it filled, the weeks in its year, the years it was given, record fingerprint, code fingerprint, events, and the run's own summary.
- `moments`: the weeks of the four moments the town view marks: the first transport firm, town full, land runs out, town fails.
- `yearly`: for each town and each completed year, the value of each measure in the last week of that year. The measures (C): for everyone, the owner class, the working class and the out of work: how many, the share unhappy, the middle person's cash. For the town: people, staff wage, basket, basket against wage, jobless rate, destitute, people with no home, firms, needs invented, the share of all shares held by the top tenth, the same for cash, both Gini numbers, homes standing, homes empty, money in town, loans to firms, loans to people.

"Which need's price broke first" (J) is recorded as it has been since stage 1: the base need whose price had risen most, against its starting price, when the run ended (C). The page says it in those words, and counts needs within a tenth of a percent of the highest as level with it.

## 5. The page (`batch.html`)

One file, opens offline, built only from `batch.sqlite`. Charts are drawn by Python as SVG; a few lines of script show the numbers under the pointer.

Top to bottom:
1. **Header.** The batch, how many settings and towns, the code fingerprint, the "Untuned" notice.
2. **How the towns ended.** For each setting: how many towns, how many failed, how many were still standing at the end. The year of failure as one dot for each town on a line of years, with the middle of the towns that failed and their middle half marked. Below it, the share of towns still standing, year by year, over the whole of the years the towns were given.
3. **The towns year by year.** For the base setting, one small chart for each measure: the middle town as a line, the middle half of towns as a band, the full range as a paler band. Pointing at a year gives the numbers and how many towns were still standing. Each chart has its table. Other settings are folded away below, one group each.
4. **When the towns ended.** For each setting: the year of failure two ways (the middle of the towns that failed; the year by which half of all the towns had failed), the top tenth's share of all shares, the Gini number for shares, the share unhappy in each class, and how many towns ended with each need's price risen most.
5. **What each dial did** (only when dials were varied). For each varied dial, its values side by side: towns failed, and the year of failure as the middle town with the middle half.
6. **Every town.** Setting, seed, how it ended and when, when it filled, its record fingerprint and its folder.
7. **How to read this**, and the command that re-makes any one town in full.

Numbers (C): the middle is the median. The middle half runs from the first to the third quartile, by straight-line interpolation between towns. A figure for a year is over the towns still standing at the end of that year, and that number is always shown. A week is recorded before the failure rule is read, so a town that fails in the last week of a year has a record for that year; it is not still standing and is left out of that year's figure.

Colours (C): the same palette as the dashboard and the town view. A band is one hue in two strengths. Settings side by side take the palette's colours in a fixed order, and never more than four on one chart: more are drawn as rows.

## 6. Commands

- `python -m wefworld batch NAME --seeds 1-30 [--set DIAL=VALUE ...] [--vary DIAL=A,B,C ...] [--config FILE] [--jobs N] [--out batches] [--full]` runs the batch, then builds the table and the page. Run again with the same name, it finishes what is left and can add seeds or settings.
- `python -m wefworld batch-report DIR` rebuilds the table and the page from the towns already there.

## 7. Tests

On batches of small towns (tens of people, a year or two):
- A town made by a batch has the same record fingerprint as the same town run alone.
- The same batch run one town at a time and several at a time gives the same table.
- A finished town is not run again; an unfinished folder is; a batch from other code is refused; a mistyped dial stops it before any town runs; a varied value equal to the base's is not run twice.
- The table equals the towns' records: outcomes, moments, and the yearly value of every measure.
- The page: one dot for each failed town, at its year; the share still standing; the middle, the middle half and the range for each year equal the same numbers worked out in the test from the records; every town is listed with its fingerprint; nothing is fetched; the "Untuned" notice is there; the colours are the dashboard's.

By eye, in the browser, on the first real batch: light and dark, wide and narrow, the numbers under the pointer, no errors in the console.

## 8. Left to the builder

Layout, the look of each chart, code layout, the order of the measures on the page.

## 9. Known simplifications

- Dials are varied one at a time. What two dials do together is not shown.
- A year's figure covers only the towns still standing, so late years rest on few towns. The page says how many.
- The same seed under two settings is not the same town. A changed dial changes what happens next, so towns are compared as groups, not seed by seed.
- "The need whose price broke first" is the need whose price had risen most by the end (section 4).
- No test of whether a difference between two settings is more than luck. With the towns shown one by one, the reader can see how far the two groups overlap.

## 10. What comes after this part

- The first batches: the model as written on the map, then the five dials the README names as mattering most, one at a time.
- The paper (J: "Claude writes it; he will not rewrite it"). It is not started on an untuned model with a fault he has ruled on. That is the builder's call (C) and his to overrule.
- The second world, after the paper, as planned.

## 11. Checked and changed during the build

- Built as designed, with one change: the page is written from `batch.sqlite` alone and does not gather the table first. The two commands gather the table and then write the page. The first draft had the page-writer gather too, which could not be squared with "built only from the table".
- Added while building: a batch keeps its own copy of the settings file it was started with and runs every town from that copy; a town the model cannot run is reported at the end and does not stop the others; a class with nobody in it has no figure that year, and the count beside the figure is the towns that had someone in it.
- The first real batch, `batches/20261113-as-written`: 100 towns of the model as written on the 13 by 13 map, 14 at a time, ten minutes, 6.7 GB. Seeds 1, 2 and 3 have the record fingerprints of the single runs of 12 November.
- The page of that batch was checked two ways. By eye in the browser: 634 and 1,400 pixels wide, light and dark, the numbers under the pointer, the tables, nothing in the console. And by number: 80 of its year figures (four measures, twenty years) were worked out again straight from the 100 towns' own records, without the table and without the page's code, and all agree; each of the 100 dots is at its town's own week of failure.
- Changed after seeing it in a narrow window: the two wide charts are drawn 640 units wide so their labels can be read at 634 pixels; the table of the towns' last week runs its measures down the page when there are three settings or fewer.

## 12. The review, and what it changed

A fresh reviewer read the whole change, worked 2,495 of the page's figures out again by its own routine and put 29 deliberate faults into copies of the code. The arithmetic was right. What it found, and what was done:

- **Critical: a year's figure counted towns that had failed in that year's last week.** 21 of the first batch's 100 towns fail in the last week of a year, so the year charts counted 91, 67, 33, 9 and 2 towns where 86, 58, 28, 8 and 1 were still standing, with those towns' failing-week numbers in the figures. Fixed: a town is left out of a year once it has failed by the end of it, and a test holds each year's count to the count of towns still standing. The year-by-year table already in the README was wrong and was re-made. The failure years were never affected.
- **Ctrl-C did not stop a batch.** Fixed as section 3 now says. Towns are handed to a process one at a time as one comes free, so stopping waits only for the towns in flight.
- **Towns run on after failing made "the last week" not the failing week.** A batch no longer takes `stop_on_failure=false`.
- **"The middle town failed in year X" was the middle of the towns that failed.** Every such figure now says so, and the page adds the year by which half of all the towns had failed.
- **Ties for "the need whose price had risen most" went to one need.** They are now counted as level.
- **Each setting's dial values were worked out by today's code.** They are now read from a town's own record.
- **The tests missed 18 of the 29 faults**, nearly all in what the page shows. 46 tests were added: every table cell is read back against made-up numbers that all differ, every chart is checked for which way up it is and where its marks sit, and one batch counts its years in 48 weeks. The 18, and 17 more for the faults fixed in this pass, were planted again one at a time: all 35 are caught.
- Also fixed: a `#`, `?` or `%` in the path (finished towns were being deleted and run again); a town's process dying (it is reported and the rest can be carried on); the whole-code gate (above); a base with many dials (its folder is now `base`); the labels of the step chart piling up (the lines now differ by dash as well as colour and are named in a key, with the share still standing at the end); the missing command that re-makes a town in full; charts for the nine measures that had none (29 of the 30: the people in town are not drawn twice); a part-finished batch now says it leans toward early failure; years are written to two places, because 93 of the 100 towns fail on a quarter end.
- The line of dots is drawn round the years in which towns failed when they all fail late (years 12 to 22 for the first batch), and the step chart under it runs the whole 60 years the towns were given. The first fix ran the dots over all 60 years, which piled 100 dots into a column.
- Left for later, and listed in the ledger: two `batch` commands on one name at once are not kept apart; `batch.py` reads the town view's own rule for the four moments through a private name.
