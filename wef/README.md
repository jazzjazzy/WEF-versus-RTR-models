# The WEF world

**This folder is the WEF world, and you run it from here.** It is one of two worlds in this
repository. The other, where people may also own, is the RTR world in [../rtr](../rtr/README.md).
Both run on the same engine ([../engine](../engine)); nothing in this world lets anyone buy,
sell or own a home.

A town where nobody owns anything. Everything an agent needs is rented or on
subscription, as in the 2016 World Economic Forum essay. Agents work, pay
their bills, hold shares if they can, and get by or do not.

**The question** (Jason, 12 November 2026): if companies keep moving toward
"you will own nothing", does that world hold together, or does it collapse in on
itself, and why? The second world, where things may be owned, is in
[../rtr](../rtr/README.md) and is measured the same way.

This is **stage 3: the town you can watch.** Stage 1 built the economy: agents,
firms, jobs, prices, shares, a bank, a share broker, decay, trade with the
outside, a full record of every run, and a dashboard. Stage 2 put that town on
a map of 169 spots. Homes, workplaces and shops have places. People walk, so
distance limits the jobs and shops they can reach. Rent depends on where a home
is. Land is free until the map fills and is then sold or leased. Transport is
one more subscription, and nobody starts with it. Stage 3 adds a page that
replays any recorded run: the map, every person moving through it, and one
person's life on demand. It changes nothing in the model or the record.

`--set map_width=0` switches the map off. That gives the stage 1 economy back,
event for event, so the two can be compared.

> **Untuned.** The build so far proves the machinery: the accounts balance, the
> places hold together, runs repeat exactly, and every week is recorded. The
> starting values have not been tested. Nothing here is a finding yet.

## Run it

Python 3.12, nothing to install.

From this folder:

```bash
python run.py --seed 1
```

That runs up to 60 years, prints one line a year (the first line says "The WEF
world"), and writes a folder under `runs/` here. Other things you can do from
this folder:

```bash
python run.py --seed 2 --years 40 --label mytest
python run.py --set price_rule=search --set population_cap=500
python run.py --config sloped-exports.json
python run.py --seed 1 --set map_width=0 --label no-map
python run.py --seed 1 --set map_width=9 --set map_height=9 --label small-map
python batch.py first --seeds 1-30
python batch.py dials --seeds 1-30 --vary price_rule=ratchet,search --vary habit_weeks=0,52
```

**The settings** of this world are in [settings.json](settings.json): every dial,
as the engine has it. `--set` changes one dial for one run. A mistyped dial
stops the run with an error naming it. `--config` takes a settings file of your
own in place of `settings.json`. Whatever you give it, a town run from this
folder is a WEF town: asking for the other world here is refused. A full
settings file saved before a dial existed (an older run's `config.json`) is
refused too, with the missing dials named: give each with `--set` to say which
town you mean.

To read what a run left, or build its pages again, from the top folder:

```bash
python -m engine info wef/runs/<folder>
python -m engine dashboard wef/runs/<folder>
python -m engine town wef/runs/<folder>
python -m engine batch-report wef/batches/first
python -m pytest
```

## What a run leaves behind

| File | What it is |
|---|---|
| `run.sqlite` | The record. Everything else is built from it. |
| `dashboard.html` | The charts. Opens offline in any browser. |
| `town.html` | The town view: the map with people moving, week by week. Only for a run on a map. Opens offline. |
| `config.json` | Every dial as it was set for this run. |
| `summary.json` | The state of the town when the run ended. |

Inside `run.sqlite`:

| Table | Holds |
|---|---|
| `run` | Seed, settings, code fingerprint, starting stock, outcome, record fingerprint |
| `events` | Every hire, layoff, price change, subscription change, missed payment, eviction, loan, default, share trade, dividend, firm founded, failed or sold, class change. On the map: every spot taken, sold or leased, homes pulled down, a move of home, and anyone turned away or cut off by distance. Numbered in the order they happened. Each agent event carries that agent's security and planning horizon at that moment. |
| `agent_snap` | Every agent, every week: cash, job, class, pay, debt, shares, security, wellbeing, needs met, which home and appliance set they have and its condition. On the map: the spot of their home, the spot of their work, hours on the road that week, and the transport firm they ride with if any |
| `firm_snap` | Every firm, every week: price, wage, customers, staff, cash, debt, revenue, costs, shares, upkeep, units. On the map: its spot, how many blocks it holds and what its land secures |
| `spots`, `places` | Every spot and where it is. Each quarter, what stands on it, who owns the land, who uses it, how many homes and how many are let, the rent factor and any ground rent |
| `series` | Every weekly measure for everyone, the owner class, the working class, the out of work, and the town |
| `holdings`, `units` | The share register and every home and appliance set, each quarter. Each home carries its spot |
| `orders` | Every share order and how much of it was filled |
| `agent_static`, `firm_static`, `needs` | What does not change: temperaments, founders, what each need takes to supply |

The same settings and the same seed give the same record, bit for bit. The
`fingerprint` in the `run` table proves it.

## Watch the town

`town.html` replays the run. Press Play, or drag the slider to any week.

- **The map.** Homes are pale blocks. A firm's premises is a darker block, sized
  by its staff, with what it sells written above it. The bank and the broker are
  outlined. The dashed strip under the map holds the people with no home.
- **The people.** One mark each. Colour them by wellbeing (two reds below the
  unhappy line, two blues above it) or by class. The shape is always the class:
  an owner is a square, the working class a circle, someone out of work a
  triangle. A dark outline is someone riding.
- **A person's card.** Point at a dot. The card gives their class, and under it
  their cash and their pay for the week shown, then their job, home and
  wellbeing. Cash is what they hold at the end of that week, after pay and
  bills. Pay is what their job pays a week; dividends are not in it. Leave the
  pointer on someone and the card keeps up as the weeks go by. At Walk and Slow
  people move out from under the pointer, so pause, or use Fast, to hold one.
- **Beside the map.** The date, and for everyone, the owner class, the working
  class and the out of work: how many, and the share unhappy. Then the people
  with no home, the share paying for a ride, the jobless rate, the staff wage
  and the basket.
- **Under the map.** The share of everyone who is unhappy over the whole run,
  with the 90% line and the moments that matter: the first transport firm, the
  town full, land running out, the town failing.
- **One person.** Click a dot, or type a person's number. You get where they are
  now, their cash, pay, debt, shares, wellbeing and security over the years, and
  what happened to them in order. Click any line of that list to go to its week.
  The lines have one point a quarter. The number beside each line is its latest
  point, and the page says which week that is.
- **A firm.** Point at the building, or at the name above it, to see its staff,
  customers and price that week.

Four speeds. At the two slow ones people make their round. At the two fast ones
each person is shown where they spend the day.

**What is recorded and what is drawn.** Where each person lives, works and
shops, their class, their wellbeing, their cash and their pay are recorded every
week and shown as recorded. The journeys are drawn. The model works in whole weeks and has no
days, so the page draws each week as one round: home, work, the food shop, the
entertainment firm, home. A person who pays for a ride moves four times as fast
as a walker, as in the model. What stands on a spot is recorded once a quarter;
between those records the page shows a firm from the week it has its spot and
homes from the week someone lives there. `--set register_every=1` records every
spot every week.

The page is built for every new run on a map. For a run made before stage 3:

```bash
python -m engine town wef/runs/<folder>
python -m engine dashboard wef/runs/<folder>
```

(from the top folder)

The second line rebuilds the dashboard so that it links to the town view.

## Many towns

One run is one town's luck. A batch runs many towns under the same rules and
shows the spread.

- **Settings.** The first setting is the base: the model as written, plus any
  `--set`. Each `--vary dial=a,b,c` adds one setting for each value, changing
  that one dial from the base. Every setting is run on every seed. Dials are
  varied one at a time; what two do together is not shown.
- **Each town is an ordinary run** in `batches/<name>/towns/<setting>/seed-0007/`
  (the base's towns are in `towns/base/`), with the same record fingerprint as
  the same seed and dials run alone. To save time and space a batch town records
  every person and firm once a quarter, not every week. Every event and every
  weekly measure is still there. `--full` keeps the weekly record. No dashboard
  or town view is built for a batch town; build either one later with
  `python -m engine dashboard <folder>` or `python -m engine town <folder>` (from the top folder).
- **Stopping and starting.** Ctrl-C stops a batch: no new town is started, the
  towns already running are let finish, and the table and the page are built
  for what is there. Ctrl-C again drops the towns in flight. Run the same
  command again and it finishes what is left. More seeds and more varied values
  can be added to a batch at any time. `--jobs` sets how many towns run at
  once; the default leaves two processor cores free.
- **One model to a batch.** A batch is stamped with a fingerprint of the model's
  own files. It cannot be carried on once a rule of the model has changed, with
  another base, or with another record of each town: give that one another
  name. A change to a page or to the batch tools does not count, so a batch can
  be carried on and its page rebuilt after one. A town is never run while the
  model's files differ from the batch's stamp.
- **A town stops when it fails.** `stop_on_failure=false` is not taken in a
  batch, because the page reads a town's last week as the week it failed.
- **What it leaves** in `batches/<name>/`: `batch.json` (the plan), `towns/`,
  `batch.sqlite` (one table of every town, built only from the towns' records)
  and `batch.html`.
- **The page** opens offline. The year each town failed, one dot a town. The
  share of towns still standing. Each measure year by year: the middle town as a
  line, the middle half of towns as a band, every town as a paler band, and how
  many towns the figure rests on. The towns' last week. What each varied dial
  did. Every town, with its record fingerprint and its folder.

How to read its numbers:

- A figure for a year covers only the towns still standing at the end of that
  year, so the late years rest on few towns. The page says how many each time.
  A town that fails in the last week of a year is not in that year's figure.
- The year of failure is given two ways. "The middle of the towns that failed"
  says nothing of the towns that never did. "Half of all the towns had failed
  by" counts them, and is the one to compare settings by.
- "The need whose price had risen most" counts needs within a tenth of a percent
  of the highest as level with it.

## The rules

The rules are written out in two documents: the economy in
[docs/superpowers/specs/2026-11-12-wef-world-stage1-design.md](../docs/superpowers/specs/2026-11-12-wef-world-stage1-design.md)
and the map in
[docs/superpowers/specs/2026-11-12-wef-world-stage2-design.md](../docs/superpowers/specs/2026-11-12-wef-world-stage2-design.md).
The town view adds no rules. What it shows, and what it draws that the record
does not hold, is in
[docs/superpowers/specs/2026-11-12-wef-world-stage3-design.md](../docs/superpowers/specs/2026-11-12-wef-world-stage3-design.md).
Each rule is marked **(J)** where Jason decided it and **(C)** where Claude chose
it as the builder. The conversation the rules came from is in
[docs/design-chat-2026-11-12.md](../docs/design-chat-2026-11-12.md). Both
predictions, written down before the first run, are in
[docs/predictions.md](../docs/predictions.md).

Every dial, its starting value and the reason for it is in
[engine/config.py](../engine/config.py). Every call Claude made while building,
with what it costs if it is wrong, is in
[docs/build-ledger-2026-11-12.md](../docs/build-ledger-2026-11-12.md),
[docs/build-ledger-stage2-2026-11-12.md](../docs/build-ledger-stage2-2026-11-12.md) and
[docs/build-ledger-stage3-2026-11-12.md](../docs/build-ledger-stage3-2026-11-12.md).

Five dials matter more than the rest and none is settled. Three belong to the
economy:

- `price_rule`. `ratchet` (the default) is the rule as Jason gave it: a firm's
  price rises whenever profit falls short of what its shareholders expect, and
  never falls. `search` lets a firm back off a rise that lost it money.
- `export_price_drop`. `0` (the default) means the outside pays one price for
  the whole export quota, so exporting is all or nothing. Above `0` the outside
  pays less for each further unit, so exports shrink smoothly as wages rise.
  `sloped-exports.json` sets it to 0.2 with outside prices to match.
- `habit_weeks`. `0` (the default) means a luxury an agent once had is missed
  for ever while someone still sells it. Set to 52, they stop missing it a year
  after they last had it.

Two belong to the map:

- `transport_can_close`. `true` (the default) means a transport firm fails like
  any other firm: sold once, and wound up if it fails again inside a year, which
  leaves its riders on foot. `false` means a transport firm with riders is
  always sold on.
- `map_width` and `map_height`. 13 by 13 by default, 169 spots, about what a
  town of 1,000 needs. In the first runs the map filled a year or two before the
  town failed, so land running out had little time to act. A smaller map makes
  land scarce sooner. `map_width=0` switches the map off.

The other map dials are the walking range, what an hour on the road is worth,
how much location moves rent, the three land prices, and the transport firm's
crew and trigger. All are in `engine/config.py` with their reasons.

## First runs without the map, 12 November 2026

These nine were made in stage 1, before the map existed. `--set map_width=0`
gives the same towns today, byte for byte.

All nine failed inside 60 years. Each row is one run, so the years below are
one town's luck, not a rate.

| Settings | Seed | Failed in year | Basket, town full to end | Staff wage at the end | Shares held by the owner class |
|---|---|---|---|---|---|
| As written | 1 | 18.5 | $785 to $1,382 | $1,018 | 85% |
| As written | 2 | 17.0 | $874 to $1,405 | $1,130 | 99% |
| As written | 3 | 22.5 | $903 to $1,601 | $1,014 | 86% |
| Firms back off a rise that lost money | 1 | 25.8 | $854 to $1,355 | $1,048 | 80% |
| Sloped outside demand | 1 | 18.8 | $904 to $1,540 | $1,124 | 87% |
| Lapsed luxuries fade after a year | 1 | 20.5 | $785 to $1,485 | $1,049 | 85% |
| All three changes | 1 | 30.0 | $867 to $1,421 | $992 | 80% |
| All three changes | 2 | 47.8 | $771 to $1,478 | $914 | 96% |
| All three changes | 3 | 31.3 | $798 to $1,491 | $1,023 | 85% |

The staff wage was $1,000 when each town filled, between year 6.3 and 7.4.

What the nine records have in common: after the town filled, the cost of the
basket rose by between 59% and 92%, while the staff wage moved between 9% down
and 13% up. Prices outran wages in every run. The owner class ended with 80% to
99% of all shares.

Why these are not findings yet:

- Few seeds. Three seeds of two settings, one seed of the rest.
- Jobs collapse in some runs. In seed 2 as written, wages were bid up a quarter,
  exports stopped, firms switched from making goods to importing them, and four
  in five residents were out of work at the end. How fast wages are bid up and
  how suddenly a firm switches are the builder's choices. So some of these
  failures are a squeeze and some are a jobs crash, and the crash is at least
  partly the model's own machinery.
- There are jobs for only about nine in ten residents once the town is full.
  That comes from the builder's starting values for labour per resident and for
  exports, not from anything Jason decided.
- Rich and poor consume the same things, so money that reaches the owners has
  few ways back to the workers. That may be the world, or it may be the model.
- Found in stage 4: after the town is full, landlords go on building. These nine
  runs built 1,099 to 2,283 homes after filling and had up to 1,749 standing
  empty at once, for 1,000 people. That building is what kept the wage level.
  See "Why the wage falls on the map" below.

These are the first things to test in stage 4.

Runs made before the code reviews are in `runs/superseded-before-review/` and
`runs/superseded-stage2-drafts/`. They were made by code with known faults and
can be deleted.

## First runs on the map, 12 November 2026

Six runs: seeds 1 to 3 on the map as written, 13 by 13, and the same three seeds
on a 12 by 13 map. All six failed between year 16.0 and year 17.2. Without the
map the same three seeds failed in years 18.5, 17.0 and 22.5.

| Map | Seed | Failed in year | Town full in year | First riders in year | Most who rode at once | Map full | Homes pulled down | Jobs lost to distance | Basket, town full to end | Staff wage at the end | Shares held by the owner class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 13 by 13 | 1 | 16.8 | 7.5 | 2.5 | 97% | year 15.5 | 16 | 222 | $869 to $1,256 | $861 | 90% |
| 13 by 13 | 2 | 16.5 | 6.8 | 3.3 | 99% | not before the end | 0 | 159 | $887 to $1,334 | $865 | 98% |
| 13 by 13 | 3 | 16.2 | 6.9 | 2.7 | 99% | year 15.3 | 8 | 123 | $884 to $1,273 | $877 | 89% |
| 12 by 13 | 1 | 16.0 | 7.4 | 2.5 | 99% | year 8.5 | 48 | 137 | $878 to $1,400 | $862 | 91% |
| 12 by 13 | 2 | 17.2 | 6.8 | 3.3 | 100% | year 6.9 | 24 | 104 | $881 to $1,328 | $844 | 96% |
| 12 by 13 | 3 | 16.0 | 6.8 | 2.7 | 98% | year 6.9 | 75 | 128 | $894 to $1,230 | $828 | 88% |

What the six records show. These are things seen in six towns, not findings.

- **Before transport, people walk.** Each person spent 4.2 to 4.6 hours a week
  on the road. The first transport firm with riders came between year 2.5 and
  year 3.3, and by year 10 the time on the road was about an hour and a half.
- **Nearly everyone rides.** The fare ran between $52 and $80 a week. At the
  peak 97% to 100% of residents held transport. By the end 57% to 82% did.
- **Transport firms come and go.** Each run founded 13 to 20 of them and closed
  10 to 19. Up to six ran at once. Only two of the six runs had any week with
  no transport firm after the first opened, two weeks each.
- **Distance keeps people from shops, not from jobs.** In most quarters between
  a dozen and a few hundred people could not get to a shop other than food, up
  to about 150 could not get to food, and almost nobody was kept from a job.
- **Jobs are lost to distance in two ways.** When the town fills and firms bid
  for staff, the transport firm loses crew and cannot carry everyone: 20 to 71
  jobs in five of the six runs. Later, riders who cannot pay the fare are cut
  off: 67 to 146 jobs a run, most after year 11.
- **Land.** On the 13 by 13 map land ran out in year 15 in two runs and never in
  the third, so the rule that land is then sold or leased hardly acted. On the
  12 by 13 map it ran out between year 6.9 and year 8.5. After that 18 to 33
  spots were sold, 24 to 75 homes were pulled down for premises, 2 to 15 tenants
  were put out, and 12 to 21 founders could not get a spot at all.
- **The wage falls.** On the map the staff wage ended 12% to 17% below the
  $1,000 it stood at when the town filled. Without the map the same three seeds
  ended 1% to 13% above it. Traced on 13 November: see "Why the wage falls on
  the map" below.
- **Prices rise less.** The basket rose 38% to 60% after the town filled, against
  61% to 77% for the same seeds without the map. The basket leaves out the fare,
  which most people also pay.
- **Protecting the transport firm changed nothing.** With
  `transport_can_close=false` all three seeds gave the same record as before,
  byte for byte. Those runs are in `runs/` with the label `map-transport-kept`.

Why these are not findings yet, on top of the reasons above:

- Six runs, three seeds.
- The fall in the wage is the largest difference between the map and no map.
  Most of it is now traced (below). Two to seven points of it are not.
- Nearly everyone rides because of two untested values: what an hour on the road
  is worth, and where the food shops are. Every firm opens as near the middle as
  it can, so most homes are beyond a walk of food.
- How fast a transport firm wins back a crew it has lost depends on the stage 1
  wage rules.
- Someone with no home is not limited by distance, so losing a home never costs
  a job.

## Why the wage falls on the map, 13 November 2026

The first job of stage 4. The full account, the tests and how to repeat them are
in `docs/stage4-wage-trace-2026-11-13.md`.

The map does not push the wage down. Without the map something holds it up.
After the town is full, newer landlords undercut the first one, tenants move, and
each newer landlord builds a home for every tenant it gains, on borrowed money.
The first landlord's rent never comes down, so its homes stand empty. A home
takes about 70 worker-weeks to build. That work keeps the town short of workers,
and a firm that cannot fill a job raises its wage.

On the 13 by 13 map there is room for about 1,150 homes and the town has about
1,005 when it fills, so a second set of homes cannot be built. Firms had
unfilled jobs in 4% to 8% of weeks after the town filled, against 39% to 53%
without the map. The wage was raised a fifth to a third as often and cut about
as often.

| | No map, seeds 1 to 3 | Map, seeds 1 to 3 |
|---|---|---|
| Homes built after the town filled | 1,205, 1,099, 1,763 | 156, 124, 173 |
| Most homes empty at once | 1,514, 1,421, 1,286 | 372, 411, 407 |
| Weeks with unfilled jobs | 41%, 39%, 53% | 8%, 4%, 8% |
| Wage rises | 253, 368, 308 | 89, 67, 114 |
| Wage cuts | 319, 338, 353 | 363, 421, 308 |
| Staff wage at the end | $1,018, $1,130, $1,014 | $861, $865, $877 |

Tested from both sides on the same three seeds. With the building stopped from
the week the town fills, the wage without the map ended 12.2%, 10.3% and 5.0%
down instead of 1.8%, 13.0% and 1.4% up. Those three runs are kept in
`runs/20261113-stage4-seed{1,2,3}-no-map-building-stopped-when-full`. Switching
off the map's distance rules, one at a time and all together, did not bring
building or the wage back: the newer landlords then filled their homes and were
refused land.

Not explained: the 2 to 7 points between the map and the town without a map
once its building is stopped, and why firms selling extras have about half the
customers on the map. Three seeds, so this is a mechanism seen and tested, not
a finding.

Runs without the map should not be used as the yardstick for what the map does.

## The first batch: 100 towns as written, 13 November 2026

`batches/20261113-as-written`: the model as written on the 13 by 13 map, seeds 1
to 100. Made with `python batch.py 20261113-as-written --seeds 1-100`.
Seeds 1, 2 and 3 have the same record fingerprints as the single runs of 12
November.

**All 100 towns failed.** The middle town failed in year 16.50 and the middle
half between years 15.50 and 17.25. The first failed in year 13.25 (week 689)
and the last in year 20.96 (week 1,090). They were given 60 years.

93 of the 100 failed in the last week of a quarter, 21 of those in the last
week of a year. Prices and wages move at each firm's quarterly review, so the
90% line is crossed then. That is the model's calendar, not a fact about towns.

Every town filled (the middle town in year 7.2) and every town got a transport
firm (year 2.5). Land ran out in 82 of the 100 (year 12.8).

Each figure below is the middle town of those still standing at the end of that
year.

| End of year | Towns still standing | Unhappy | Staff wage | Weekly basket | Basket against the wage | Jobless | Cash of the middle working person | Homes empty |
|---|---|---|---|---|---|---|---|---|
| 5 | 100 | 0.2% | $1,000 | $894 | 89% | 0% | $9,988 | 3 |
| 8 | 100 | 12.8% | $1,038 | $959 | 92% | 11.5% | $9,262 | 152.5 |
| 10 | 100 | 19.2% | $989 | $1,042 | 105% | 14.0% | $10,912 | 212 |
| 12 | 100 | 32.2% | $939 | $1,134 | 120% | 15.0% | $11,857 | 238 |
| 14 | 98 | 57.5% | $901 | $1,213 | 134% | 13.5% | $8,470 | 265 |
| 15 | 86 | 70.6% | $881 | $1,251 | 142% | 13.9% | $4,083 | 297.5 |
| 16 | 58 | 80.4% | $864 | $1,286 | 149% | 13.5% | $865 | 317 |
| 17 | 28 | 85.1% | $841 | $1,381 | 166% | 12.4% | $624 | 316.5 |

(As first written on 13 November this table counted, in each year, the towns
that failed in that year's very last week: 67 towns at year 16 where 58 were
still standing. The reviewer found it and the page and this table were
corrected the same morning. The failure years above were never affected.)

In the towns' last week the top tenth of people held 96.7% of all shares (the
middle town). 6% of the owner class were unhappy, 94.7% of the working class,
and everyone out of work. The base need whose price had risen most was
appliances in 85 towns, food in 10, entertainment in 5, and housing in none.

**Against the two predictions** (`docs/predictions.md`). Jason's: this world "is
not sustainable" and "will eventually collapse in on itself". Claude's: it does
not collapse by itself. As written, 100 of 100 collapsed, the path was the same
in every town, and luck moved the year by about eight years from first to last.
That runs with Jason's prediction and against Claude's. Of Claude's other
expectations, the town did look healthy while it was growing and showed its
character once it was full. Ownership did not drift toward the top: the top
tenth held nearly all shares from the first year.

Why this is still not a finding:

- Nothing is tuned. This is how the rules as written behave with the builder's
  starting values.
- Under the price rule a price never falls (decision 1, kept by Jason on 16
  November), and a firm cuts its wage when there is a queue for work. A basket that only rises against
  a wage that is cut will cross any line in time. So "they all fail" may say
  more about those two rules than about a world where everything is rented. The
  next batches vary the price rule and the four other dials named under "The
  rules".
- The model still builds homes while homes stand empty (decision 17, ruled a
  fault). On this map land limits it.
- The other open points under "First runs without the map" still stand: jobs for
  about nine in ten once the town is full, and rich and poor buying the same
  things.

## Decisions

Each had a starting value in the model. Jason ruled on decision 17 on 13
November 2026, on decisions 1 to 16 on 16 November 2026, four at a time, and on
decision 18 the same day.
Where he wrote his own answer it is quoted; otherwise he chose one of the
answers offered. **Changes the model** marks a ruling that differs from what was
built. All of them were built on 16 November 2026 (see "Jason's rulings, built"
below). Every run made before then, the first batch among them, follows the old
rules.

The economy:

1. Can a price ever fall? As built, never (`price_rule=ratchet`).
   **(J), 16 November 2026: no, as built.** His words: "I'm inclined to believe
   that it won't go down based on current rules in a real economic environment.
   Even though it should. as this would affect making the shareholders happy
   rule."
2. Is a luxury someone has lost missed for ever? As built, yes (`habit_weeks=0`).
   **(J), 16 November 2026: no, it fades after a year (`habit_weeks=52`).
   Changes the model; built.** In the first runs (seed 1, no map) this alone
   moved failure from year 18.5 to year 20.5.
3. Can the bank make a jobless borrower sell their shares? As built, no
   (`bank_can_force_share_sale=false`). **(J), 16 November 2026: no, as built.**
4. Can a resident ever buy a home? As built, no. **(J), 16 November 2026: no,
   everyone rents.** This town stays the "own nothing" world. It therefore has
   nothing inside it to compare against; ownership belongs to world two.
5. The town starts with 120 homes and 120 appliance sets already standing.
   **(J), 16 November 2026: 60 homes. Changes the model.** His words: "Let's just
   make it 60 homes". Built. Appliance sets stay at 120: the builder's reading,
   since he named homes only.
6. A personal loan is called in when the job goes, and loan interest leaves
   town. **(J), 16 November 2026: the loan is called in, as built.** Interest
   leaving town was already his rule (the federal bank).
7. Once the town is full there are jobs for about nine in ten residents.
   **(J), 16 November 2026: that is the world he means; the starting values
   stay.**
8. Rich and poor buy the same things. Should the well-off be able to buy more?
   **(J), 16 November 2026: yes, the well-off spend more. Changes the model.**
   Of three designs put to him he chose "Bigger plan and better home". Built:
   see below.

The map:

9. How big is the map? As built, 13 by 13, which fills late or never. 12 by 13
   fills as the town does. **(J), 16 November 2026: 13 by 13, as built.**
10. Can the town's only transport firm close? As built, yes
    (`transport_can_close=true`). **(J), 16 November 2026: no, a transport firm
    with riders is always sold on (`transport_can_close=false`). Changes the
    model; built.** In the first map runs it made no difference.
11. Is someone with no home limited by distance? As built, no. **(J), 16
    November 2026: no, as built.**
12. Should a shop open where people are unserved? Not built: every firm opens as
    near the middle as it can. **(J), 16 November 2026: yes. A founder opens near
    people who cannot reach a seller, so a shop can hold its own patch of town.
    Changes the model; built.**
13. Who pays the fare before the rent? As built, food, then rent, then the fare,
    for everyone. **(J), 16 November 2026: someone who needs the ride for work
    pays the fare before the rent. Changes the model; built.**

The town view (these change the picture, not the model):

14. What colours a person? As built, wellbeing, the number the 90% rule reads,
    with class as the other choice. The first design said security.
    **(J), 16 November 2026: wellbeing stays the colour and class becomes the
    dot's shape.** His words: "Can we keep the color of the well-being. but change
    shapes for the classes." Built.
15. Where are people with no home drawn? As built, in a strip under the map.
    **(J), 16 November 2026: the strip under the map, as built.**
16. Should the model have days? As built it has none; the page draws each
    person's round from where they live, work and shop. **(J), 16 November 2026:
    no, weeks, as built.**

Found in stage 4:

17. Should a landlord build while homes elsewhere in town stand empty? As
    built, yes: each keeps 6% of its own homes spare and builds when it has
    fewer. Without the map this built 1,099 to 2,283 homes after the town was
    full. On the 13 by 13 map land stops it.
    **(J), 13 November 2026: a fault in the model, not the world he means.** His
    words: "Most likely your fault. I don't remember actually saying 2,000
    houses." He never did. No rule says how many homes a town has; the number
    came out of the builder's starting values. The rule that replaces it is not
    designed yet, so the model still builds this way.

18. What do the rich do with money they do not spend? As built, it sits: no
    interest, the bank does not lend it on, and a resident founds a firm only
    now and then. Put to Jason on 16 November 2026 with the money trace.
    **(J), 16 November 2026: it sits, as built.** His words: "No, this seems to be correct. So What the rich usually do with their money is
    they tie it up in shares or they put them in blind trusts or charity trusts and
    never use the money.So I think we're fine with that."

19. Should the town stop at 1,000 people? As built on 12 November, yes (J).
    **(J), 16 November 2026: no cap; the homes that can be built are the limit,
    and a newcomer still needs a free home to move in.** His words: "So let's make the limitation the amount of homes we can build, and let's not make it a limit of 1,000 people, we can have more than that." Then, of two ways to do it: "Yes, drop the cap but keep needing a home".
    Built. With no cap the town counts as full (the "Town full" mark) the first
    week a newcomer is turned away for want of a home after the land has run out
    (the builder's call). Founders keep arriving, two a year on average, while a
    home is free. Four towns (seeds 1, 2, 3 and 32, 60 years): the land ran out
    and the town was full in years 8.9 to 9.9 at about 1,150 people; they grew to
    1,160 to 1,183 people and failed in years 17.0, 18.0, 20.0 and 18.27 (with the
    cap: 16.5, 18.25, 19.25 and 18.75). From year 10 or 11 a few hundred residents
    were homeless while homes stood empty, as under the cap: people put out for
    rent they could not pay, beside homes whose rent never falls.

## Jason's rulings, built, 16 November 2026

Each ruling is a dial whose default is his ruling. The settings in
`before-16-november.json` give the model as it was before, and with them
a town is the same town as before, event for event: seed 74 of the first batch
was made again and its record is identical.

```bash
python run.py --seed 74 --config before-16-november.json
```

| Decision | The dial | Now | Before |
|---|---|---|---|
| 2. A lost luxury fades | `habit_weeks` | 52 | 0 |
| 5. Homes at the start | `needs.housing.initial_units` | 60 | 120 |
| 8. The well-off spend more | `well_off_income` | 1.5 | 0 (off) |
| 10. Transport always sold on | `transport_can_close` | false | true |
| 12. Shops near the unserved | `shops_near_unserved` | true | false |
| 13. The fare before the rent, for work | `fare_first_for_work` | true | false |
| 19. No cap on people; a newcomer needs a home | `population_cap` | 0 (none) | 1000 |

How decision 8 works (the builder's calls, marked in the design note): someone
is well-off when their income is at least 1.5 times their week's bills at
standard size and their savings cushion is full, and stops being so below 1.2
times or with cash under half the cushion. The well-off buy a double plan of
food, entertainment and luxuries (not the ride) at double the price, and the
firm needs double the staff and goods for them, but only while their income
stays at least 1.2 times the bills with it. Short of cash, they go back to the
standard plan before giving anything up. A better home costs one and a half
times as much to build, keep up and rent. A well-off resident who could pay for
one looks for one and, if none is free, waits; the biggest landlord builds for
those waiting, less the better homes free or being built, on top of its usual
building, so none are built while better homes stand empty.

Decision 12: when at least 20 residents cannot reach any seller of something
they travel for (food, entertainment, a luxury), the next founder opens that
shop as near them as they can, at the going price.

Decision 14 is in the town view (see "Watch the town").

**Three towns under the rulings, not a finding.** Seeds 1, 2 and 3 on the map,
60 years each: all three failed, in years 16.5, 18.25 and 19.25. The same seeds
as first written failed in years 16.75, 16.5 and 16.23. Each town reached every
new rule: bigger plans (714 to 1,014 taken up), better homes (12 to 44 built),
shops opened for the unserved (12 to 18). Better homes come late: while the
town grows, landlords spend on standard homes first. The next step is a batch
under the rulings.

The design note is
[docs/superpowers/specs/2026-11-16-wef-world-rulings-design.md](../docs/superpowers/specs/2026-11-16-wef-world-rulings-design.md);
every call made while building it is in
[docs/build-ledger-rulings-2026-11-16.md](../docs/build-ledger-rulings-2026-11-16.md).

## The second batch: the same 100 towns under Jason's rulings, 16 November 2026

`batches/20261116-rulings`: seeds 1 to 100 on the 13 by 13 map, made with
`python batch.py 20261116-rulings --seeds 1-100` on commit `6ffd717`.
On its page the setting is called "as written": that means the model's
defaults on the day, which are now Jason's rulings.

**All 100 towns still failed, about two and a half years later.** The middle
town failed in year 18.75 (first batch: 16.50), the middle half between years
17.75 and 20.00 (15.50 and 17.25). The first failed in year 15.00 (13.25), the
last in year 24.75 (20.96). Seed by seed, 95 towns failed later, 4 earlier and
1 in the same week; the middle change was 2.38 years later, from 1.96 years
earlier (seed 75) to 9.75 years later (seed 49).

Each figure is the middle town of those still standing at the end of that year,
the first batch's figure first. Years 18 to 20 of the first batch rest on 8, 2
and 1 towns.

| End of year | Towns still standing | Unhappy | Staff wage | Weekly basket | Cash of the middle working person |
|---|---|---|---|---|---|
| 10 | 100 / 100 | 19.2% / 11.5% | $989 / $1,050 | $1,042 / $975 | $10,912 / $9,786 |
| 12 | 100 / 100 | 32.2% / 19.1% | $939 / $1,007 | $1,134 / $1,084 | $11,857 / $10,922 |
| 14 | 98 / 100 | 57.5% / 26.6% | $901 / $955 | $1,213 / $1,179 | $8,470 / $12,032 |
| 15 | 86 / 99 | 70.6% / 33.5% | $881 / $930 | $1,251 / $1,235 | $4,084 / $11,585 |
| 16 | 58 / 97 | 80.4% / 44.6% | $864 / $904 | $1,286 / $1,280 | $865 / $9,235 |
| 17 | 28 / 90 | 85.1% / 57.6% | $841 / $880 | $1,381 / $1,357 | $624 / $4,544 |
| 18 | 8 / 68 | 82.0% / 68.7% | $799 / $858 | $1,599 / $1,410 | $1,110 / $1,323 |
| 19 | 2 / 41 | 84.1% / 75.6% | $851 / $833 | $1,324 / $1,481 | $576 / $823 |
| 20 | 1 / 23 | 86.0% / 79.9% | $741 / $752 | $1,562 / $1,746 | $542 / $1,100 |

The path is the same, slower: the basket rises, the wage falls, the working
class's cash holds and then runs out, unhappiness climbs to the 90% line. Money
in town still rises all the way (the middle town: $45.6 million at year 10,
$131.6 million at year 17), so the towns do not run out of money; it does not
reach the workers. The owner class holds less cash than in the first batch (the
middle owner: $77,338 at year 10, against $222,835), since the well-off now
spend it, but the top tenth still held 94% to 98% of all shares in the middle
town up to year 18, and 96.9% in the last week. Out of work ran a little higher
(16% to 17% from year 14, against 12% to 15%). Between 274 and 364 homes stood
empty from year 14 (decision 17 is not yet replaced). In the last week the base need whose price
had risen most was appliances in 52 towns, entertainment in 27, food in 18,
housing in 2 (one town level between appliances and housing).

Checked against the towns' own records, not the table alone: every failure
year from each town's summary, and five of the yearly figures above from each
town's weekly record. All agree.

**Against the two predictions**, the same as the first batch: 100 of 100
collapsed, which runs with Jason's prediction and against Claude's. And the same
reasons it is not yet a finding: nothing is tuned, a price can never fall (now
Jason's ruling, decision 1), the empty homes of decision 17, and every town
rents, so there is nothing yet to compare it with.

## Where the money goes, 16 November 2026

The money in town rises to the end in both batches while the workers' cash runs
out. Traced in [docs/stage4-money-trace-2026-11-16.md](../docs/stage4-money-trace-2026-11-16.md).
It sits with the founders. Export money comes in ($18.8 million a year once the
town is full, in the middle town of the second batch), the firms pay it out as
dividends, and a handful of founders who own their firms outright take it,
spend a quarter to two fifths and keep the rest. Across the 100 towns under the
rulings, at year 15 the owner class held 63% of the town's money in the middle
town and the five richest people 54%; the working class held 11%. Nothing in the
model gives saved money a way back to the workers: it earns nothing, the bank
does not lend it, and new firms are started only now and then. The accounts are
right. Jason ruled that it is the world he means (decision 18: it sits).

## Six rules shared with the RTR world, 22 November 2026

Six rules about jobs, pay and basics had been built for the RTR world only,
though none needs anyone to own anything. Jason: "From RTR world, all six of
these issues should be the same on both." (J) They now hold here too: the
least someone out of work will take covers their basics; the line that lets a
firm cut its wage is those who would take the job; a cut is for those hired
after it; a firm in debt that lost money lets staff go; the longest-serving
goes first; going without counts at the cheapest firm's price.

With the six alone, nine in ten were out of work by year 14 in two test towns:
basics rose past every wage and everyone turned every offer down. Jason, of a
man with no income and basics of $1,494 offered $1,445: "If there is no money
coming in, he will take any offer that is put forward to him." And, of a few
dollars of dividends, that he takes any offer unless what he has coming in pays
his basics on its own: "Yes, that's right" (J, dial
`floor_needs_money_coming_in`, in both worlds).

The hundred WEF towns (`wef/batches/shared-wef`, against `stage3-wef`): all 100
still reach the failure line, the middle town at year 19.0 against 17.8; 73
later, 23 sooner. At year 15 the middle town has 24.7% out of work against
25.7% and is 46.1% unhappy against 44.1%; staff are paid $967 against $853, a
newcomer is offered $830. Details in
[the ledger](../docs/build-ledger-wef-shared-rules-2026-11-22.md).

## What is still to come

Stage 4, tuning and checking the starting values, was begun and then set aside
on 13 November: one check is done ("Why the wage falls on the map" above), the
fault of decision 17 is still in the model, and nothing is tuned.

Stage 5 has started with the batch runs: many towns per setting ("Many towns"
above) and the first batch of 100. Next are batches that vary one dial at a
time. The paper is not started; it should not rest on an untuned model. The
second world is being built beside this one, in [../rtr](../rtr/README.md).

Known simplifications are listed at the end of each rules document.

## Size and speed

A run takes one to three minutes. A run folder is 150 to 600 MB,
because every agent is recorded every week. `--set snapshot_every=4` records
agents and firms every fourth week and cuts that to about a quarter. `runs/` is
not kept in git. The town view takes about three seconds to build and is about
7 MB for a town that fails around year 16. For a town run the full 60 years it
is about 32 MB and takes about sixteen seconds; it opens in under a second and
plays. About half of the page is every person's cash for every week, which the
card needs. (Measured 13 November on seed 1 kept running after it failed: that
run folder was about 900 MB.)

A batch town, recorded once a quarter, takes about 40 seconds alone and about
60 MB. The first batch, 100 towns run 14 at a time on a 16-core machine, took
ten minutes and 6.7 GB. Its table is 1.8 MB and its page 0.3 MB. `batches/` is
not kept in git.
