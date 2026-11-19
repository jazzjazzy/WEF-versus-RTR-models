# WEF World, stage 3 design: the town you can watch

Date: 12 November 2026. Jason said "commit the code, do the housekeeping, then start on stage three" after stage 2 was built and reviewed. Decisions marked **(J)** are his, from the conversation of 12/11 recorded in `docs/design-chat-2026-11-12.md`. Choices marked **(C)** are Claude's calls as the builder. Each is listed so he can overrule it.

## 1. Intent and why

Jason's picture (J): "the town itself with people moving through it." He said the town view is the primary view; the dashboard and the single-life view sit beside it. He also said (J): "I need to be able to visualise what's actually going on, and record it."

The dashboard answers "how much". The town view answers "where, and who". It lets him watch a town fill, spread, and go wrong, and then follow one person through it.

The rule from stage 1 still holds (J): record first. The view is a replay of the record. It never runs the model.

## 2. Goals, non-goals, anti-goals

Goals
- One page per run, `town.html`, in the run folder. Built only from `run.sqlite`. One file, nothing fetched, opens offline.
- The town at any recorded week: what stands on every spot; where each person lives, works and shops.
- People move. Each week is drawn as one round: home, work, shops, home.
- People are coloured by wellbeing, or by class (J: "colour or mark agents by class as an option").
- The four coverages beside the map at every week: everyone, owner class, working class, out of work (J).
- Replay: play, pause, four speeds, step a week, drag to any week. The moments that matter are marked on the time line.
- The single-life view (J: "one agent from arrival onward") is in the same page. Pick a person and their life opens beside the map.
- It works on the runs already made. Nothing in the model or the record changes.

Non-goals for stage 3
- No town view for a run with the map switched off. There is no town to draw.
- No film export. A screen recording does that.
- No two runs side by side (stage 5). No tuning (stage 4). No second world.

Anti-goals
- A picture that claims more than the record holds. The journeys are drawn, not recorded, and the page says so.
- A page that needs the internet, a server or an install.
- A number on the page that disagrees with the record or the dashboard.

## 3. What is recorded and what is drawn

Recorded every week, and shown as recorded:
- For each person: the spot they live on, their employer and role, their class, their wellbeing and whether they are happy, whether they pay for transport, which food firm and which entertainment firm they pay.
- For each firm: its spot, staff, customers and price.
- For the town: head counts and the share unhappy for the four coverages, people with no home, riders, the jobless rate, the staff wage, the basket.

Recorded once a quarter:
- What stands on each spot (homes, premises, a town service, or nothing), who uses it, how many homes.

Drawn, not recorded (C):
- **The journeys.** The model works in whole weeks. It has no days. The page draws each week as one round so there is movement to watch: home, then work if the person has a job, then the food shop and the entertainment firm they pay, then home.
- **Speed.** Journeys are drawn slower than they would be, so they can be seen. Walkers and riders keep their true ratio: a ride is `transport_speed` times faster (4 by default), read from the run's own settings.
- **Where a dot sits inside a block.** A block holds many people. Each dot gets its own fixed place in the block.
- **People with no home.** The model gives them no place on the map (stage 2 design, section 9). The page draws them in a strip under the map, marked "No home". Their round starts and ends there. This does not prejudge open decision 8 (whether a person with no home should be limited by distance).

Between the quarterly records (C): the page shows a firm's premises from the week the firm has the spot, and homes on a spot from the week someone lives there. Both come from the weekly snapshots. A premises whose firm no longer has the spot is drawn empty until the next quarterly record says what stands there. A run made with `--set register_every=1` records every spot every week and needs none of this.

## 4. The page

Top to bottom:
1. **Header.** The run, the seed, how it ended, and a link to the dashboard. The same "Untuned" notice as the dashboard.
2. **The map and the side panel**, side by side on a wide screen, stacked on a narrow one.
3. **The controls.** Play or pause, step back and forward one week, four speeds.
4. **The time line.** The share of everyone who is unhappy, week by week, with the 90% failure line. Marks for: town full, the first transport firm, land runs out, the town fails. A slider under it. Click the chart or drag the slider to go to any week.
5. **How to read this.** What is recorded and what is drawn, in plain words.

The map
- Spots are blocks with streets between them. Buildings are grey so the people carry the colour.
- Homes: a pale block. Premises: a darker block, sized by staff (design chat: "firms sized by staff"), with the need written on it. Bank and broker: outlined and named. Empty land: a faint outline.
- People are dots. A person paying for transport is a square while travelling and moves four times faster.
  **Changed 16/11/2026 (J):** class is the shape (owner a square, working class a circle, out of work a triangle); a rider on the road has a dark outline (decision 14).
- Point at a person's dot, at a block, or at the name above a firm to see who or what it is. Click to select. A person is picked only when the pointer is on their dot, so a firm full of people can still be pointed at, through the gaps or by its name.
- A person's card (J, 13 November, section 11): their class, and under it their cash and their pay for the week shown, then job, home, wellbeing, ride or walk.

The side panel
- The date: year, quarter, week.
- The four coverages: how many, and the share unhappy, each with a bar. The 90% line is marked on the bar for everyone.
- Town facts for the week: no home, destitute, riders, jobless rate, staff wage, basket, firms.
- "Colour people by": Wellbeing or Class, with the legend, and a key to what the blocks on the map are.
- The selection: a block (what it is, whose, staff, customers, price, homes and how many are let), or a person (the life view).

The life view (one person)
- Who they are: arrived when and how, what they came with.
- Now, at the week shown: class, job and role, home, wellbeing, ride or walk.
- Lines over their time in town, quarter by quarter: cash, weekly pay, debt, shares, wellbeing against the unhappy cutoff, and security. The number beside each line is its latest quarterly point. A dot marks that point and the page says which week it is, because the week shown is usually not a quarter end.
- What happened to them, in order, in plain words. Something that happened several times in one quarter is told once, with how many times. Click a line to go to that week.
- The person is ringed on the map and their round for the week is drawn as a line along the streets.
- A person can also be picked by number, or at random.

Speeds (C): a week in eight seconds, a week in two seconds, six weeks a second, half a year a second. At the two fast speeds the round is not drawn; each person is shown where they spend the day: at work if they have a job, otherwise at home.

Colours (C)
- Wellbeing: four steps, two red below the unhappy cutoff and two blue above it. The recorded happy flag decides the side; the wellbeing number decides the depth. This is the blue and red pair from the chart colour reference.
- Class: the dashboard's three class colours, so a class is the same colour on both pages.
- The design chat said "coloured by security". Wellbeing is used because it is the number the failure rule reads; security is half of it. Each person's security is in their life view.

## 5. The data in the page

All of it is worked out in Python from `run.sqlite` and embedded as JSON.

- `weeks`: the recorded weeks, in order. With `snapshot_every` above 1 these are the snapshot weeks.
- A **change list** is `[week, value, week, value, ...]`: a value holds from its week until the next entry. `-1` means none. Before the first entry the thing does not exist yet.
- `people`: id, arrival week, and change lists for home spot, employer, role, class, wellbeing step (0 to 3), rides, food firm, entertainment firm. For the card (section 11): weekly pay as a change list, `w`, and cash, `c`, as one number for each recorded week from the person's first, which is recorded week number `c0`. Both in whole dollars. Cash is not a change list because it changes nearly every week for nearly everyone, and a change list would be longer. Then the life data: quarterly cash, pay, debt, shares, wellbeing and security from arrival, and the list of life events.
- `firms`: id, name, need, founding week, and change lists for spot, staff, customers and price. A firm that has closed carries `end`, the first recorded week it is gone.
- `spots`: x, y, the service label if any, and change lists for kind, user firm and homes, worked out by the rule in section 3.
- `series`: the town numbers for the side panel, one for each recorded week.
- `line`: the share of everyone who is unhappy, for every week the run measured. The weekly measures are complete in the record however often people were recorded, so the time line is weekly even when the page moves four weeks at a time.
- `run`: the run's own seed, outcome, unhappy cutoff, failure share, ride speed, year and quarter lengths, and how often it recorded people and spots. The page words itself from these.
- `marks`: the weeks of the four key moments.

Life events kept (C): arrival, hired, laid off, quit, employer changed, promoted, demoted, made chief executive, founded a firm, founding blocked, takeover, class change, moved home, subscription started or ended, missed payments, loan called, loan repaid, default, shares bought or sold, cash call, job offer refused, a job or food too far to reach. Left out: credit refused, share grants, dividends. Events that can come week after week (missed payments, share trades, subscriptions started and ended, loan calls) are told once a quarter, with a count and a total.

Size, measured at the end of stage 3: about 3.5 MB for a town that fails around year 16, built in two or three seconds. A town run for the full 60 years is about 19 MB and takes about twelve seconds to build; it opens and plays. The first draft of this design said under 10 MB for any run. That does not hold for 60 years and the page is not cut down to make it hold. Since 13 November the page also carries every person's cash and pay and is about twice that size (section 11).

## 6. Commands

- `python -m wefworld town <run folder>` builds or rebuilds `town.html` and prints its path. For a run with no map it says so and writes nothing.
- `python -m wefworld run ...` writes `town.html` beside `dashboard.html` when the run has a map.
- The dashboard links to the town view when the run has a map, and the town view links back.

## 7. Tests

Python, on a small recorded run and on hand-made rows:
- The page builds from `run.sqlite` alone and fetches nothing.
- Every person's change lists, read back at every recorded week, equal the agent snapshot. The same for firms.
- The wellbeing step is on the unhappy side exactly when the record says unhappy.
- Spot change lists equal the `places` table at each quarterly record, and follow the between-quarters rule on hand-made rows.
- Series and marks equal the record.
- Life events are the person's own, in order, with the right weeks.
- A run with no map, an unfinished run, and a run with `snapshot_every=4` each behave as section 5 and 6 say.

JavaScript, run under Node when it is installed (skipped when it is not):
- Reading a change list.
- A route between two blocks runs along the streets, starts and ends in the right blocks.
- The round: the order of stops; no work stop without a job; a rider covers a leg in a quarter of a walker's time; at the start and end of the week the person is at home.

The whole page, loaded under Node with a stand-in for the browser (skipped without Node): the script runs; the panel equals the record at every week; every person is drawn where the record puts them; colours follow the wellbeing step and the class; play, the slider, the step buttons and the keys work; pointing and following a person work; a run that recorded every fourth week says so.

By eye, in the browser: the page on a full run, light and dark, wide and narrow; playing, dragging, selecting; no errors in the console.

## 8. Left to the builder

Layout, sizes, timings of the round, wording of the life events, code layout.

## 9. Known simplifications in stage 3

- The round is the same every week and the same for everyone with the same stops. Nobody visits the bank, the broker, or any firm other than their employer, their food firm and their entertainment firm.
- Journeys bend once along the streets. Nothing gets crowded and nobody waits.
- What stands on a spot is exact once a quarter and inferred between (section 3).
- The life lines are quarterly. Of a person's weekly numbers only cash and pay are in the page, for the card (section 11). The rest are in the record.

## 10. Checked and changed during the build

- Built as designed, with these changes: the speeds (first drafted faster; a six-block walk then took a quarter of a second and could not be watched); the followed person's round drawn as a route, not as straight lines to each stop.
- Measured on two full runs: 3.3 and 3.5 MB a page, built in about 2.5 seconds. The number of people with no home on the page equals the record's own count at every week.
- Checked by eye in the browser on both map sizes: light and dark, 375, 634 and 1400 pixels wide, all four speeds, the slider, stepping, the keys, pointing at people and places, following a person, both colour choices. No errors in the console.
- Colours checked with the chart colour checker. The three class colours pass for every pair in light and dark. Each side of the wellbeing scale passes as a two-step ramp in both. The four wellbeing steps pass the colour-blind and normal-vision tests in both.
- Not reached: a run with more than one town service of the same kind; a map so small that names never fit (below 30 pixels a block the names are left to the hover text).
- A fresh reviewer read the whole change and ran it against six more runs of its own. It found what the page draws equal to the record at every week it could check, and the model untouched. It found one critical fault (the numbers beside a person's lines read as this week's but were the last quarter's), nine important ones and fifteen minor ones. All are fixed, each with a test that failed first, except four minor ones listed in the ledger.
- The between-quarters rule was measured by the reviewer against a run that recorded every spot every week: 0.42% of spot-weeks differ, all of one kind (a block of homes drawn as empty land before anyone lives there).
- The page's own script is now loaded and driven by tests. 61 deliberate faults were put into a scratch copy one at a time, among them the 24 the first set of tests had missed. Each is now caught by a test.
- A page for a 60-year run (19 MB) was played through every week and every life in a headless browser with no errors.

## 11. Changed after the build

**13 November 2026: money on a person's card (J).** Jason was watching the town and asked how people are paid and where their money shows. The builder offered to show a person's cash and pay next to the map on a click. His answer: "No, put it on their card when you roll over them under the class."

- The card of a person now reads: Person N; their class; Cash; Pay; then job, home, wellbeing, ride or walk; "Click to follow".
- Cash is the record's figure for the week shown: what they hold at the end of that week, after pay and bills. Whole dollars.
- Pay is the record's `pay` for that week: what their job pays a week (the firm's wage for staff, an executive's or a chief executive's pay for them). Someone with no job reads "No pay". Dividends are not pay and are not on the card.
- The card keeps up with the week under a pointer that has not moved, as a firm's card already did.

Builder's calls (C):
- The numbers are this week's, not the latest quarter's. He was watching week by week to see pay arrive, and a number that stood still for thirteen weeks would have misled. This is why the page now carries every person's cash for every recorded week.
- The "Now" line beside a followed person is left as it was. The lines under it give the latest quarter's cash, and this week's cash on the line above would read as a second answer to the same question. The footer says the two can differ and why.
- Debt, shares and dividends are not on the card. They are beside a followed person, one point a quarter.
- A week with no record of someone keeps their cash as it was, so the list cannot slip a week. It cannot happen in a run, where everyone in town is recorded together.

Checked:
- 14 tests, written first and seen to fail for want of the feature. The suite is 512.
- Every person-week of cash and pay in the rebuilt page for seed 1 on the map (663,870 of them) equals the record.
- 43 cards read from the real page in the browser, at weeks 300 and 871, equal the record. One person held under the pointer for three weeks changed as the record does. The card stays inside a window 634 pixels wide.
- The model is untouched: seed 1 on the map, run again with this code, gives the record fingerprint recorded on 12 November (`8a9ccdf346c84b2d`).

Size, measured after the change: about 7 MB for a town that fails around year 16 (the nine recorded map runs: 6.7 to 7.2 MB, were 3.3 to 3.8), built in a little over three seconds. Seed 1 kept running for the full 60 years: 31.7 MB, built in 16 seconds. That page opened in the browser in about a third of a second, played at half a year a second with nothing in the console, and 12 cards read from it at the last week equal its record. One number a week was chosen over storing only the weekly change, which would have saved about a third of the added size, because it needs no working out in the page.
