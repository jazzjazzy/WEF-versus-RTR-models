# How this model was built

This model was built in eight days, from 12 to 19 November 2026, by a person
and an AI working together. This page says who did what, the method that was
followed, what was built when, and what went wrong along the way. It is
written so that someone who downloads the model can judge how far to trust
it, and can check the work for themselves.

Everything said here can be traced to the records in this folder. Where a
figure is given, the record it comes from is named.

## Who did what

**Jason** asked the question, set the rules, and ruled on every design
decision that was put to him. His question, on 12 November 2026: if companies
keep moving toward "you will own nothing", does that world hold together, or
does it collapse in on itself? And what happens in the opposite world, where
people may own, repair and build? Nothing was committed, merged or published
without his word.

**Claude**, an AI model made by Anthropic and working as a coding agent,
designed the machinery under those rules, wrote all of the code, the tests
and the documents, ran the towns, and kept the record.

The two are kept apart everywhere. In the settings
([engine/config.py](../engine/config.py)) and in the designs, a rule that is
his is marked **(J)** and a number or a gap the builder filled is marked
**(C)**. His rulings are quoted in his own words in the ledgers. Most of the
starting numbers are the builder's, which is one reason nothing here is yet a
finding.

Before the first run, each wrote down what they expected to happen
([predictions.md](predictions.md)), so that neither could tune the model
toward what they already believed. Jason expected the rent-everything world
to collapse in on itself. Claude expected neither world to collapse by
itself.

## The method

The same steps were followed for every part of the model.

1. **Talk first.** Each world began as a conversation about how its people
   and firms behave. That became a written design
   ([superpowers/specs/](superpowers/specs/)), which Jason approved before
   anything was built. His briefs, in his words, are in
   [design-notes/](design-notes/).
2. **A plan**, task by task ([superpowers/plans/](superpowers/plans/)).
3. **Tests first.** A test was written for each rule and seen to fail before
   the rule was built to make it pass.
4. **A ledger.** Every decision the builder made alone was written down as it
   was made, with the reason and what it would cost if it was wrong (the
   `build-ledger-*.md` files here). The ledgers were kept as written.
5. **Whole towns under weekly checks.** Tests of single rules are not enough,
   so whole towns are run for years with a set of checks made every week: all
   money moves through one function and must add up, every person and firm
   must be where the record says, and so on.
6. **Runs must repeat exactly.** The same settings and seed give the same
   record, event for event. Towns of the WEF world recorded early on are run
   again by the tests and must still match, so work on one world cannot
   quietly change the other.
7. **Deliberate breaks.** Each rule was broken on purpose in a scratch copy,
   one break at a time. A break that no test caught meant a test was missing,
   and one was written.
8. **A fresh reviewer.** At the end of each stage a second instance of the AI,
   with no part in the build, was given the code and the records and asked to
   find faults. It ran its own towns. Its findings were graded by what a
   person using the model would get, fixed with a failing test first, and
   listed in the ledger, including the ones that were left.
9. **Many towns, not one.** One town can mislead. Results are read across
   batches of towns that differ only in their seed.
10. **Plain reporting.** A town that did not reach the failure line is not
    called a town that works. Good news was checked as hard as bad.

## What was built, and when

Test counts are the size of the test suite at the end of each stage.

| When | What | Tests | What checking found |
|---|---|---|---|
| 12 Nov | The design conversation, and both predictions | | |
| 12 Nov | Stage 1: the economy, no map. People, firms, a bank, a share market, renting everything | 201 | The reviewer ran 21 small towns through about 1,800 firm failures with no fault in the accounts. It found two critical faults (income wrongly recorded for each person, and a mistyped setting accepted without complaint) and several rules that misbehaved; fixed |
| 12 Nov | Stage 2: the map. Distance, land, rent by location, transport | 333 | Comparing records showed the new code, with the map switched off, no longer gave the stage 1 town. The cause was the order in which a founder settled and opened a firm; fixed. The review found one critical fault (a pulled-down home went on being rebuilt) |
| 12 to 13 Nov | Stage 3: the town view, a page that plays a run back week by week | 512 | The review found 1 critical, 9 important and 15 minor faults in the page, and that the page's own code had no tests. It is now tested by loading the built page and driving it |
| 13 Nov | Stage 5, first part: running many towns at once and comparing them | 660 | The first batch: all 100 WEF towns failed, the middle one in year 16.5. The review found the yearly charts were counting towns that had failed in a year's last week; fixed |
| 13 and 16 Nov | Stage 4: tracing. Why the wage falls on the map, and where the money goes | | Two written traces: [wage](stage4-wage-trace-2026-11-13.md), [money](stage4-money-trace-2026-11-16.md) |
| 16 Nov | Jason's rulings on the sixteen open decisions of the WEF world, and no cap on people | 712 | Seven rulings differed from what had been built, and were built. The second batch: all 100 towns still failed, the middle one in year 18.75 |
| 16 to 17 Nov | The RTR world, stage 1: owning, building, buying, selling and letting | 861 | The review found that the quarterly home sales crashed about one full town in ten; fixed |
| 17 Nov | The two worlds given a folder each over one shared engine | | |
| 18 Nov | The RTR world, stage 2: side hustles, ideas, small businesses, companies | 1,012 | Whole towns showed five things wrong with the builder's own design that every test had passed. The review then changed five more of the builder's rules, with figures for each |
| 18 Nov | Jason's rulings on six of the builder's calls in the RTR world | 1,087 | The review found that an old saved settings file would quietly run some of the new rules. Such a file is now refused |
| 19 Nov | Jason's rulings on who is in the line for a job, and on staff keeping their pay | 1,130 | The builder's first version stopped small towns. The review caught it. See below |
| 19 Nov | Jason's ruling that a firm in debt and losing money lets its longest-serving staff go | 1,156 | It took three builds. Counting how towns fare, and then a reviewer, overturned the builder's reading twice. See below |
| 20 Nov | The RTR world, stage 3: its measures on the pages, and both worlds on the same hundred seeds, side by side | 1,183 | No rule changed; the WEF world's pages held byte for byte. A reviewer recounted the comparison from the 200 towns' own records and found no wrong count, but found the page said more than the counts did: "never" for towns stopped at sixty years and getting worse, and a cost of living made of asking prices nobody was paying. Both fixed |
| 20 and 21 Nov | Jason's rulings that in the RTR world people are judged on what they actually pay: an owner on what owning costs them, and someone going without on the lowest price a firm or a neighbour asks | 1,206 | Two rules, each found by looking inside how towns fared: people were measuring themselves against the asking prices of firms nobody used. The review found the builder had counted an owner's upkeep as if every home were new. Fixed before the hundred towns were run. RTR towns reaching the failure line: 7 of 100 before, 0 after; unhappy in the middle town at year 60: 74% before, 24% after |
| 21 Nov | In the RTR world, someone out of work will not take a job that pays less than their basics cost them (the builder's rule, at Jason's word to trace why pay fell so low and fix it) | 1,217 | The trace found the builder's own numbers at fault: what someone out of work would take fell to nothing after twenty weeks, so firms cut pay for decades. The review found the first version overrode Jason's rule that someone with a large loan takes the first job offered, and could trap a homeowner with a loan out of work for years. Both fixed before the hundred towns. Lowest pay offered in any town at year 60: $110 before, $598 after. With no job in the middle town: 3.4% before, 8.1% after |
| 21 Nov | In the RTR world, someone running a small business or side hustle of their own is not counted as jobless (the builder's call, at Jason's word to trace why towns had fewer jobs and fix it) | 1,225 | The builder's first guess, that small businesses could not hire, was wrong when counted. Nobody had lost work: the jobless rate counted everyone with no employer, and the rise was people running businesses of their own. A measure only; the hundred towns made the same events. Jobless in the middle town at year 60: 8.1% as counted before, 0.1% now |
| 22 Nov | In the RTR world, someone out of work with a business of their own takes a job when its pay and what the business would still bring in cover their basics (Jason's rule, from a trace of why such people were unhappier) | 1,242 | The trace found the floor set the job's pay alone against their whole basics, though a job does not close a business. The review found the builder's first reckoning scaled staff wages down with the hours and used the wrong week's hours for someone just let go; both fixed before the hundred towns. In the middle town at year 60, no employer 8.1% before, 6.2% after; unhappy 19.9% before, 18.6% after. Business owners out of work were still as often unhappy: most have basics measured at prices that look wrong |
| 22 Nov | In the RTR world, someone going without appliances counts them at what owning a set costs (Jason's rule, from a trace of rents of thousands of dollars a week) | 1,251 | The appliance firm kept almost no customers and its rent rose 3% a quarter for decades, $76 to $9,417 a week in one town, against about $23 to own. The review found nothing wrong in the change and one older fault nearby (a newcomer buying a home holds back four weeks of that rent), not fixed. All 100 towns survived; the middle town's unhappiness at year 60 moved from 18.6% to 20.8%, with towns going both ways about evenly |
| 22 Nov | In the RTR world, a newcomer does not rent appliances that cost more than owning a set (Jason's rule: "Who would pay $9,000 if they could pay $23") | 1,265 | Every newcomer had signed up for the runaway appliance rent on arrival, and a buyer held back four weeks of it. The review found the builder's first version undone by the week's review, which rented newcomers a set anyway, some while building one; fixed. The towns as shipped in the tests were picked again. All 100 towns survived; the middle town barely moved, towns going both ways evenly |
| 22 Nov | Six rules on jobs, pay and basics hold in the WEF world too (Jason: "all six of these issues should be the same on both"), and in both worlds the floor on what someone out of work will take holds only while what they have coming in pays their basics (his rule) | 1,309 | With the six alone, WEF test towns had nine in ten out of work: basics rose past every wage and everyone turned every offer down. Put to him as a man with no income; his rule built. The second review found a few dollars of dividends brought the floor back; his threshold built. All 100 WEF towns still reach the failure line, the middle town at year 19.0 against 17.8; all 100 RTR towns survived, the middle town barely moved |

The engine is about 13,300 lines of Python and the tests about 16,900. All
three stages of the RTR world are built.

## What went wrong, and what it taught

These are kept on the record because they are the best guide to where the
model may still be wrong.

- **The first batch failed everywhere.** All 100 towns of the WEF world
  failed within 21 years. That is a result of the rules and the untested
  starting numbers together, and it has not been separated into which is
  which.
- **A rule that works in a test can do nothing in a town.** On 18 November a
  rule of Jason's (a newcomer may buy a home) was built and passed sixteen
  tests. Counting showed that no newcomer used it in any town that was run,
  because of when newcomers arrive and when the bank holds homes. The count,
  not the tests, showed this.
- **The accounts can balance in a town that has stopped.** On 19 November the
  builder made firms work out their costs from the average pay of their
  staff. Eighty small towns passed every weekly check. A reviewer then showed
  that 8 of 20 such towns reached the failure line, with a third to a half of
  their people out of work on average, and that with the new rules switched
  off none did. The weekly checks prove the books. They cannot see whether a town is working. The tests now also ask
  how their towns fare.
- **The builder reads more into a rule than it says.** The same afternoon
  Jason ruled that a firm losing money lets its longest-serving staff go
  "before we hire new staff". The builder turned that into a freeze on hiring
  until the firm had a quarter without a loss. Across eighty small towns the
  share of people with no job doubled. The freeze was taken out. A reviewer
  then showed the builder had also read "debts" as "any loss in a quarter",
  which in this model is more than half of all quarters: firms were letting
  people go and taking the same people back within days. Jason ruled "only
  if in debt". Each fault was found by counting what happened in towns, not
  by a test.
- **A reviewer finds what the builder cannot.** In every stage that was
  reviewed, the reviewer found at least one fault that mattered, in a place
  the builder had not looked. Each is in its ledger.
- **The builder's numbers are everywhere.** His rules often left a number
  open ("long", "reasonable", "a large loan"), and the builder chose one.
  Each choice is marked and listed for him to overrule. Several have already
  been overruled.

## Checking this for yourself

- Run the tests from the top folder: `python3 -m pytest`. They take about
  five minutes and need Python 3.12 or later and `pytest`, nothing else.
- Run a town: see the README in [wef/](../wef/README.md) or
  [rtr/](../rtr/README.md). The same seed and settings give the same town.
- Read a ledger beside the code it describes. Each ruling says what was
  decided, why, and what it costs if wrong.
- The ledgers quote commit IDs and branch names from the private working
  repository the model was built in. This public repository starts from one
  snapshot of 19 November 2026, so those IDs are not in its history. The
  recorded towns the figures come from are large and are not in the
  repository either. Running the same settings and seeds makes them again.

## What this is not

It is not tuned, and it is not finished. The starting numbers have not been
tested against anything. No result here is a finding yet. The report on what
the two worlds do, set against the two predictions, has not been written.
