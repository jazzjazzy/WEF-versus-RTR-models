# The RTR world (Right to Repair)

**This folder is the RTR world, and you run it from here.** It is one of two worlds in this
repository. The other, where everything is rented and nobody owns a home, is the WEF world
in [../wef](../wef/README.md). Both run on the same engine ([../engine](../engine)).

The opposite world to WEF, designed with Jason on 16 November 2026
([docs/superpowers/specs/2026-11-16-rtr-world-design.md](../docs/superpowers/specs/2026-11-16-rtr-world-design.md)):
people may rent or buy, build and repair their own, everything created is open,
new things come from people, and a side hustle can grow into a business.

> **Untuned.** All three stages are built: owning (stage 1), side hustles, ideas
> and small businesses (stage 2), and the pages and the two worlds side by side
> (stage 3, 20 November). On 20 and 21 November Jason ruled that people are judged
> on what they actually pay (the last section). The starting values have not been
> tested. Nothing here is a finding yet.

## Run it

Python 3.12, nothing to install. From this folder:

```bash
python run.py --seed 1
python run.py --seed 2 --years 40 --label mytest
python batch.py first --seeds 1-30
```

A run prints one line a year (the first line says "The RTR world") and writes a
folder under `runs/` here, with the same record, dashboard and town view as a
WEF run; what each holds is described in [../wef/README.md](../wef/README.md).

**The settings** of this world are in [settings.json](settings.json): every dial
the WEF world has, at the same values, and thirty-five more that only this
world reads (spare hours, the loan against a home, foreclosure, letting,
seventeen for makers, six for Jason's rulings of 18 November 2026 and five
for those of 19 November). `--set` changes
one dial for one run; `--config` takes a settings file of your own. Whatever you
give it, a town run from this folder is an RTR town: asking for the other world
here is refused. A full settings file saved before a dial existed (an older
run's `config.json`) is refused too, with the missing dials named: give each
with `--set` to say which town you mean.

The rules that only this world has are in two files:
[../engine/rtr_owning.py](../engine/rtr_owning.py) (owning) and
[../engine/rtr_makers.py](../engine/rtr_makers.py) (side hustles, ideas, small
businesses). None of it runs in a WEF town.

## Stage 1, 17 November 2026

**Built so far: stage 1, owning.** It was built in two parts.

*Stage 1a, building and owning your own.* In an RTR town a person has spare
hours (60 a week, less 40 for a job, less the road). They can build an appliance
set of their own (parts from outside, 20 hours) and a home of their own on a
plot (materials from outside, 1,200 hours, a bank loan if their income allows:
the whole cost since 18 November 2026, four fifths before), keep both up with
their own hours and parts, and lose the home
to the bank after four missed payments.

*Stage 1b, buying, selling and letting.*

- **Buying from a landlord.** A tenant can buy the home they rent: ten years of
  its rent after upkeep, or its value as a building if the landlord is short of
  cash. A home a landlord has not let for a year is sold at its value to a renter
  with a job. A block with a privately owned home on it is never sold or pulled
  down; if its landlord closes it becomes a block of plots.
- **Buy, build or rent.** Someone who could buy takes whichever of buying and
  building would cost them less a week (the first loan payment and the upkeep),
  and only if it is clearly less than their rent. Empty homes are offered before
  tenants are offered the homes they rent, so the cheaper goes first.
- **Small landlords.** Someone in work who owns the home they live in builds a
  second home to let when a newcomer was turned away for want of a home in the
  last quarter and the going rent would cover the loan payment and upkeep with a
  tenth to spare. They are a person, not a firm: the rent is their income, they
  keep the home up with their own hours, and one bank loan stands against all
  the homes they own.
- **Who may buy a let home.** Its tenant first. If the tenant cannot, only
  someone who will go on letting it: a resident who owns their home, then
  another landlord firm. The tenant stays at the same rent. No sale puts a
  tenant out.
- **Foreclosure, in Jason's order.** The bank takes one thing at a time: an
  unfinished second home first (nothing stands to sell, so what it lent on it
  is written off), then the newest home they let (its tenant stays and pays the
  bank), and the home they live in last. Each home is then sold for the debt
  owed: to a renter who can pay or borrow for it (the sitting tenant of a let
  home), then to a resident who owns, who lets it, then to a landlord firm.
  Unsold, the price falls 5% a quarter.
- **Calls the builder made** (each is in the ledger with its reason and what it
  costs if wrong; the two that matter most): an *empty* home is bought to let,
  by a person or by a landlord firm, only when a newcomer was turned away for
  want of a home in the last quarter, the same sign as for building to let; and
  one landlord firm buys a let home from another only when it is worth the
  price with a tenth to spare, so homes do not pass back and forth between
  landlords at no gain.

**Not built when these figures were made.** Stage 2 (side hustles, ideas, small
businesses) and stage 3 (the new measures on the pages, and the two worlds side
by side on the same 100 seeds). So the towns in this section are WEF towns in
which people can also own, build, buy and let, and nothing more. The first part
of stage 2 has been built since: see the next section.

**The WEF world is unchanged.** Two WEF towns recorded before the build give
the same record after it, and seed 74 of the first batch under the old rules is
still the same town (checked again at the end of stage 1b).

**Three towns, not a finding.** Seeds 1, 2 and 3 on the map, no cap on people.
The year each failed:

| Seed | WEF | RTR, stage 1a alone | RTR, all of stage 1 |
|---|---|---|---|
| 1 | 17.0 | 23.0 | 19.0 |
| 2 | 18.0 | 22.25 | 24.25 |
| 3 | 20.0 | 22.02 | 20.25 |

(The WEF years are the same seeds under the rulings with no cap, from decision
19.) All three still failed: 2.0, 6.25 and 0.25 years later than in the WEF
world. Against stage 1a alone, one town lasted two years longer and the other
two failed about four and two years sooner.

What the same three towns looked like with all of stage 1. The last four
columns are for the last even year before each failed (years 18, 24 and 20):

| Seed | Most who owned the home they lived in | Most small landlords | Most homes let by one person | Foreclosures | Homeless | Homes the bank held unsold | Other empty homes | Staff wage |
|---|---|---|---|---|---|---|---|---|
| 1 | 280 | 112 | 100 | 425 | 630 | 146 | 239 | $746 |
| 2 | 410 | 133 | 87 | 601 | 788 | 382 | 442 | $636 |
| 3 | 530 | 164 | 60 | 595 | 602 | 358 | 308 | $524 |

- **A quarter to nearly half of the town came to own the home they lived in**
  at the most (each town had about 1,100 people). With stage 1a alone the
  figures were 336, 257 and 302: fewer now in one town, more in the other two.
- **Most homes that changed hands went to people who let them.** Landlord
  firms sold 494 to 581 homes to owners who let them (the tenant, where there
  was one, staying) and 76 to 279 to people who live in them. People built 186
  to 212 homes to live in and 60 to 122 to let.
- **A few people hold a great many homes.** At the end the largest small
  landlord let 60 to 100 homes. An owner may buy one let home from the
  landlords each quarter and bank-held homes as they come up, and the town's
  founders have the cash to do it every time. Nothing checks that they have the
  hours to keep that many homes up, so those homes wear.
- **The bank holds homes unsold again near the end** (146 to 382). An empty
  home is bought to let only when a newcomer has just been turned away for want
  of one, and late in these towns nobody is, because homes stand empty. Until a
  renter with a job can pay, the home waits and its price falls 5% a quarter.
- **Foreclosures rose in all three** (425, 601 and 595, against 308, 235 and
  219 with stage 1a), with more people owning and borrowing.
- **The squeeze is the same one.** The staff wage fell to between $524 and
  $746 while rents never fell, so near the end 600 to 790 people had no home
  beside 385 to 824 empty ones (the bank's included). At the end the owner
  class held $102 million to $228 million of the $192 million to $279 million in
  town.

**The fresh review of stage 1b** found one crash (about one full town in ten
died in the quarterly home sales) and five faults in how the rules behaved; the
figures above are after its fixes. The largest changes: the gain on a home a
landlord sells now reaches its profit; a renter who could build for less a week
no longer buys on a large loan; and landlord firms no longer buy every empty
home the bank holds. Before those fixes the same towns failed in years 22.56,
23.75 and 21.69.

How it was built, every call made, and the fresh reviews with their fixes are in
[docs/build-ledger-rtr-stage1a-2026-11-16.md](../docs/build-ledger-rtr-stage1a-2026-11-16.md)
and
[docs/build-ledger-rtr-stage1b-2026-11-17.md](../docs/build-ledger-rtr-stage1b-2026-11-17.md).

## Stage 2, part A: side hustles, 18 November 2026

**Built: makers.** A maker is one person selling their own spare time to others
(Jason, 16 November: "side hustles or actual small businesses"). The rules are in
[../engine/rtr_makers.py](../engine/rtr_makers.py); the plan is
[docs/superpowers/plans/2026-11-18-rtr-stage2-makers.md](../docs/superpowers/plans/2026-11-18-rtr-stage2-makers.md).

- **What they sell.** Food, entertainment, or anything someone has thought up, to
  customers who sign up as they would with a firm. Or hours: repairs to homes
  and appliance sets people own, building appliance sets, building homes. Not
  the ride, and not homes or sets to let.
- **What an hour of theirs is worth.** Their wage over the forty hours of a job.
  For someone out of work, the wage they would now accept, which falls the
  longer they are out, and never less than half the going hourly wage. So the
  struggling undercut most.
- **Their price** (Jason, tentative: cost plus a little). The goods at the
  outside price and their hours at that worth, plus 10%. Set again each
  quarter; it can fall. A firm's price still never falls.
- **How many they serve.** Their spare hours, after keeping up what they own,
  divided by the hours one customer takes (the firm's own figure). Someone out
  of work can serve about 30 people entertainment or 8 people food; someone
  with a job about 10 or 2.
- **Customers** choose between firms and makers on the same reckoning of cost.
  A maker works from home, and customers reach them as they reach a shop.
- **Starting one.** Each week someone with ten spare hours and no side hustle
  may start one: one chance in ten if they are out of work or their income does
  not cover their basket (Jason: "It gives them the opportunity to get out of
  the struggling"), otherwise one in a hundred times their appetite for risk.
  They take the trade where their price most undercuts the cheapest seller in
  reach, and pay for the tools: nothing for entertainment (Jason: the computer
  they already have), $2,000 for food, $1,000 for repairs, $5,000 for building
  sets (his chairs), $10,000 for building homes. From their cash, then a
  personal loan, then a loan against their home.
- **Stopping.** With fewer than a fifth of the customers they could serve for a
  whole quarter they give it up, and the tools are gone.
- **Repairers and builders.** An owner pays a repairer for the hours of upkeep
  they are short of that week, and for all of them when the repairer comes to
  less than doing it themselves (their own hour counts at a fortieth of the
  going wage). Someone building pays a builder on the same test, or while the
  job would take them more than a quarter of their spare time. The bank still
  lends its share of a home's materials to the owner (all of it since
  18 November 2026, four fifths before).
- **Class and income.** What a side hustle brings in is income. Someone with no
  job whose side hustle brings in at least half their basket counts as working
  and has a position, as someone with a job has.

**Calls the builder made** (all are in the ledger with the reason and what each
costs if wrong; the ones that matter most):

- A maker buys the week's goods after the customers have paid, out of what they
  paid. So someone with no money at all can start.
- A maker's price does not move the town's cost of living while a firm still
  sells the same thing. *(Changed after the fresh review: see part B.)*
- A side hustle needs a home to work from. Someone who loses their home loses
  the side hustle with it. *(Withdrawn after the fresh review: see part B.)*
- A maker with no hours left for customers for a whole quarter gives it up.
- Nobody is their own customer.

**Not built when these figures were made.** The second part of stage 2: ideas
(new things thought up in spare time), the bank's loan on a side hustle's profit
with staff taken on, and a side hustle becoming a company. It has been built
since: see the next section. So the towns in this section have side hustles
and nothing more of stage 2.

**It can be switched off whole.** With `hustle_rate`, `hustle_rate_struggling`
and `idea_rate` at 0, an RTR town is exactly the stage 1 town: three towns gave
the same record, event for event, on the code before this stage and on this
code with those three at 0.

**The WEF world is unchanged.** The two pinned WEF towns give the same record,
and seed 74 of the first batch under the old rules is still the same town
(`08251209eb136522`, 180,377 events), checked again on 18 November.

**Three towns, not a finding.** The same seeds as above, on the map, no cap on
people, under the weekly checks. The year each failed:

| Seed | WEF | RTR, all of stage 1 | RTR, with side hustles |
|---|---|---|---|
| 1 | 17.0 | 19.0 | 23.1 |
| 2 | 18.0 | 24.25 | 24.5 |
| 3 | 20.0 | 20.25 | 24.25 |

All three still failed. What they looked like at year 10, about two years after
each town filled and jobs ran short, and at the last even year before each
failed (years 22, 24 and 24):

| Seed | When | Side hustles | Of them selling hours | Makers with no job | Of those, making a living at it | Plans makers serve a week | Firms' customers of every kind | Hours sold a week | Out of work | Staff wage |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | year 10 | 72 | 4 | 51 | 46 | 1,180 | 1,477 | 212 | 38% | $932 |
| 1 | year 22 | 97 | 10 | 64 | 5 | 1,117 | 819 | 231 | 51% | $662 |
| 2 | year 10 | 72 | 8 | 53 | 48 | 1,068 | 1,241 | 224 | 39% | $913 |
| 2 | year 24 | 91 | 19 | 84 | 11 | 931 | 554 | 927 | 53% | $664 |
| 3 | year 10 | 107 | 9 | 69 | 55 | 1,418 | 1,474 | 226 | 39% | $858 |
| 3 | year 24 | 175 | 13 | 141 | 1 | 2,445 | 438 | 393 | 64% | $420 |

("Making a living" is the rule's own line: the side hustle brings in at least
half their basket. "Firms' customers of every kind" counts every subscription
to a firm, homes, appliance sets and rides included, so it is more than the
firms' share of what makers sell. Each town had about 1,100 people.)

- **Side hustles are few while there are jobs for everyone** (3 to 31 before
  each town filled, every one run beside a job) **and many once there are
  not.** By year 10, with about two in five out of work, there were 72 to 107.
- **At year 10 most makers with no job were making a living at it** (46 of 51,
  48 of 53, 55 of 69). **By the end almost none were** (5, 11 and 1), though
  there were more makers than ever. Why has not been traced. The rules allow
  at least two reasons: more makers sharing the customers, and a maker's price
  following the going wage down while the basket they are measured against
  never falls.
- **Makers came to serve more than the firms.** By year 10 makers served nearly
  as many plans a week as the firms had customers of every kind; by the end,
  more. How much of that makers took from firms, and how much the firms lost
  because people could no longer pay, these figures do not say.
- **Many lost the side hustle with their home.** Over each run 349 to 412 side
  hustles were started; 119 to 176 were given up for want of customers, 79 to
  101 because the maker lost their home, and 18 to 31 for want of hours.
- **The squeeze is still the same one.** The staff wage fell to between $420
  and $664 and half to two thirds were out of work at the end.

**How it was checked.** 957 tests. Small towns of 200 people run for fourteen
years under the weekly checks with every rule on, and reach every rule of this
part. Then 176 rules were broken on purpose, one at a time: 164 failed a test
at once, eleven showed gaps in the tests and each got a test, and one changes
nothing (a doubled guard). Last, forty full towns (seeds 1 to 40) were run from
this folder to hunt for crashes: all forty ran to their end with no error. All
forty failed by the town's own rule, the first in year 18.25, the middle one at
about year 23, the last in year 37; that is not a finding either. The ledger is
[docs/build-ledger-rtr-stage2-2026-11-18.md](../docs/build-ledger-rtr-stage2-2026-11-18.md).

## Stage 2, part B: ideas, small businesses and companies, 18 November 2026

**Built.** The rest of stage 2, in the same file
([../engine/rtr_makers.py](../engine/rtr_makers.py)). The figures in this
section are from the code as it stands after the fresh review.

- **Ideas** (Jason: new things come from people, for the fun of it, and time is
  the main thing). Each week a person has a small chance of an idea for every
  twenty spare hours they have left once their own things, their side hustle
  and their building have had theirs. An idea is a new need, made exactly as
  the WEF world makes one. It is open: its creator may start selling it as a
  side hustle at once ($500 of tools), anyone else from the next week, and
  nobody is paid for the idea. While people have ideas, founders of firms do
  not invent.
- **The till.** A side hustle has a till for the week. What customers pay goes
  into it; the goods are bought out of it, then any staff are paid out of it,
  and what is left is its owner's at the week's end.
- **A small business** (Jason: "loans is to make it a business ... if the bank
  thinks it's profitable"). A maker of a need who sold all they could for a
  whole quarter, and has a worker's worth of customers they cannot serve who
  would still buy at a business's price, borrows 26 weeks of their weekly
  profit from the bank over five years. The loan stays in the business. From
  then it prices its hour at the going wage, which is what it pays (since 19
  November 2026, what it pays someone new: its staff keep what they are on
  when the going wage falls), and takes on residents as staff: a worker for every whole week of hours its customers
  need beyond its owner's own, and one more only when that work would pay
  their wage and a week of the wage is in hand. It has no premises, no
  executives and no shareholders.
- **If it cannot pay.** Staff it cannot pay are let go, last hired first. Four
  loan payments missed in a row end the business: what is left in it goes to
  the bank, then what cash its owner has, the bank writes off the rest, and
  they are refused credit for three years. Their home is not at risk for it.
- **A company.** A maker of a need who has saved the capital any resident
  needs to found a firm ($150,000 after investing seven tenths of their cash)
  may found one by the WEF world's rule, with premises near their home and
  shares, and bring their customers and staff. From then its price never falls.

**Changed by the fresh review** (each was a rule of the builder's; the reasons
and the reviewer's figures are in the ledger):

- **No home is no bar.** Someone with no home can start a side hustle and
  sells where they are found; someone who loses their home goes on from where
  they were. The builder's rule that a side hustle needs a home is withdrawn:
  about three quarters of the jobless in a full town have no home, and Jason's
  decision was "anyone creates, even while struggling".
- **The cost of living counts a maker who has room.** The yardstick is the
  cheapest price someone could buy at: the firms' cheapest, or a maker's with
  room this week if that is less. In full towns almost nobody was paying the
  firms' prices the index had been built on.
- **Their own hours first.** Someone building a set or a home works their own
  hours first and pays a builder with what money is left. Before, the builder
  took the money and their own hours stood idle.
- **A repairer or builder never becomes a small business,** and starts only
  with enough work in sight to keep them past their first quarter. At the
  going wage nobody would buy their hour, and most had been losing the cost of
  their tools.
- **The map knows where food makers are.** A block beside a food maker with
  room is not far from food.

**Other calls the builder made** (in the ledger with reasons and costs):

- A maker counts as waiting only people it turned away who would have bought.
  It takes on staff, and goes to the bank, for those and nobody else.
- A worker a business already has for a part week is kept while their work
  pays half their wage, so that one customer more or less does not cost
  someone their job each week. The half is the builder's number.
- A small business hires only people already in town, and keeps the going-wage
  price even in weeks it has no staff.
- Only a maker of a need becomes a company: no firm in the model sells hours.

**For Jason to rule on.** Everyone's own spare hour counts at the going wage
when they weigh doing a thing themselves (section 5 of the design). So someone
out of work, with sixty idle hours, pays a repairer who charges less than that:
$69.52 for upkeep that would cost them $43.20 in parts. It is the design to
the letter, and it moves money between people for work they had the time to do.

**Five things whole towns showed that the tests had not.** None broke the
accounts. All were faults in the builder's own design of the small business,
found by running whole towns, traced before they were changed, and each now
held by a test:

1. A business lost money on every worker by construction: it paid the going
   wage and still charged its owner's cheap hour.
2. Nearly every side hustle borrowed and called itself a business without
   ever needing staff.
3. Businesses took on staff for people who asked the price but would never
   have bought. In the first full town they took on 30,244 workers in 24 years
   and let 21,061 go unpaid. Small towns of 200 had hidden this.
4. The takings went into the owner's pocket, and the owner's own rent and
   loans were paid before the worker's wage. That is why there is a till.
5. The loan went into the owner's pocket too, where it looked like savings.

After them, and after the review's fixes: 318 to 434 workers taken on by small
businesses in a full town's whole run, 225 to 296 let go for want of work and
28 to 52 let go unpaid, against 2,833 to 3,541 laid off by the firms in the
same towns.

**Three towns, not a finding.** The same seeds again, on the map, no cap on
people, under the weekly checks. The year each failed:

| Seed | WEF | RTR, all of stage 1 | RTR, with side hustles (as first built) | RTR, all of stage 2 |
|---|---|---|---|---|
| 1 | 17.0 | 19.0 | 23.1 | 23.5 |
| 2 | 18.0 | 24.25 | 24.5 | 27.25 |
| 3 | 20.0 | 20.25 | 24.25 | 29.75 |

All three still failed. At year 10 and at the last even year before each failed:

| Seed | When | Side hustles | Makers with no job | Of those, making a living at it | Small businesses | Their staff | Plans makers serve a week | Firms' customers of every kind | New things thought up so far | Out of work | Staff wage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | year 10 | 170 | 94 | 79 | 57 | 89 | 2,836 | 934 | 7 | 44% | $878 |
| 1 | year 22 | 396 | 204 | 83 | 135 | 63 | 5,278 | 815 | 27 | 51% | $585 |
| 2 | year 10 | 147 | 103 | 82 | 37 | 25 | 1,940 | 1,126 | 6 | 39% | $909 |
| 2 | year 26 | 365 | 192 | 17 | 100 | 50 | 4,585 | 561 | 30 | 50% | $551 |
| 3 | year 10 | 158 | 64 | 45 | 57 | 90 | 2,382 | 916 | 6 | 43% | $864 |
| 3 | year 28 | 376 | 205 | 8 | 106 | 67 | 4,972 | 173 | 25 | 58% | $389 |

- **People thought up 26 to 31 new things in each town**, about one a year. In
  the WEF world under the rulings the middle town had invented 6 by year 15.
- **Most side hustles came to sell something somebody thought up.** Of the 656
  to 809 side hustles started in each town, 457 to 555 were in an invented
  need. By the end about one person in three had one.
- **About a third of them were small businesses** near the end (100 to 135),
  with 50 to 67 staff between them: most have no staff at any one time.
- **The bank lent on profit 177 to 186 times in a town and wrote off 5 to 17
  of those loans** ($4,700 to $21,600 a town): the loan now stays in the
  business and mostly goes back to the bank.
- **Five to nine makers in each town became companies.**
- **Makers with no job who make a living at it** were 79, 82 and 45 at year 10
  and 83, 17 and 8 near the end. Why it falls in two towns and not the third
  has not been traced.
- **The squeeze is still the same one.** The staff wage fell to between $389
  and $585 and half or more of the town was out of work near the end.

**Forty towns.** Forty full towns (seeds 1 to 40) were run from this folder on
the final code to hunt for crashes: all forty ran to their end with no error.
Thirty-nine failed by the town's own rule: the first in year 21.5, the middle
one in year 28.5, the last in year 44. One (seed 17) was still standing at year
60, and it was looked at decade by decade before saying so: 859 people, nearly
all in work at a wage of $768, every home privately owned, 663 side hustles,
and 42% unhappy, up from 5% at year 30 and still rising a few points a decade.
It is one town in forty. With side hustles alone, as first built, the forty
failed between years 18.25 and 37, the middle one at about year 23. None of
this is a finding: nothing is tuned, and no WEF batch under the same rules
exists yet to set beside it.

**It can still be switched off whole.** With `hustle_rate`,
`hustle_rate_struggling` and `idea_rate` at 0 an RTR town is the stage 1 town,
event for event; two such towns are pinned in the tests.

**How it was checked.** 1,012 tests. Small towns of 200 run for fourteen years
under the weekly checks with every rule on, and between them reach every rule
of both parts but three that are now too rare for a small town and have tests
of their own; one small town has every firm closed in a single week and must
still balance. Rules were broken on purpose, one at a time: 342 breaks of the
code as it stands each fail a test, and one more is a doubled guard that
changes nothing. A fresh reviewer then ran 458 towns of its own and found no
crash and no broken account with any shipped settings, one crash with a
hand-made list of needs, and eight things that behaved wrongly; seven were
fixed in one pass, each with a test that failed first, and the eighth is the
one above for Jason. Three full towns under the weekly checks on the final code,
and the forty above.

## Jason's rulings of 18 November 2026

Six of the calls made while building stages 1 and 2 were put to Jason. He kept
three and changed three, and a fourth change came out of counting what the
towns did. All are built. The ledger is
[docs/build-ledger-rtr-rulings-2026-11-18.md](../docs/build-ledger-rtr-rulings-2026-11-18.md).

**Kept as built.** People with idle hours pay a repairer who comes to less than
their own hour. A small business keeps the rate it is at after its staff have
gone, "if they need to hire more staff moving forward". One landlord firm buys
a tenanted home from another only at a tenth over the price.

**A newcomer may buy** (built). His words: a newcomer has "an opportunity to
rent anything that's vacant or buy anything that's available as long as they
have ... good enough income". Someone who comes for a job and finds no home
free to rent may buy an empty home the bank holds, on the terms of anyone in
town: their cash beyond four weeks of the other base needs, and a loan for the
rest if the wage of that job allows it. The home must be a walk from the job,
or a ride where one is on offer. A founder buys only with the cash they keep
back from the venture, since they have no income yet. A newcomer is counted as
turned away only when they could neither rent nor buy. Dial: `newcomers_buy`.

**It is never used.** In three full towns 1,163, 904 and 1,012 workers were
turned away, and in no week of those did the bank hold an empty home. In forty
small towns run with the rule, 20,789 were turned away, the bank took 3,658
homes, and no newcomer bought one. Workers come only while the town is
growing, in its first seven years. The bank takes its first home in year 6 to
8, and by then there is someone in town out of work for every vacancy, so
nobody comes from outside again.

**What the count showed instead, and the ruling it led to.** By the end of
those towns the bank held 181 to 366 empty homes, hundreds more stood empty to
let, and four or five hundred people had no home. Most could not pay any rent.
But some were in work: in one town at year 20, 75 people in work had no home,
the rent was $609 a week on a wage of about $610, and the bank's cheapest
empty home was $10,750, about $23 a week on a loan for all of it. They could
not buy it, because the bank lent four fifths and they had not the other fifth
in cash. That four fifths was the builder's number. Jason's words for the loan
had been "if their income allows".

**The bank lends the whole price** (built). His ruling: "Lend the whole
price". Where the income allows the payments, the bank now lends all of a
home's price, all the materials of a home someone builds, and against the
whole value of a home already owned. Nobody needs a fifth in cash.
`mortgage_ltv` is 1.0; set it to 0.8 for the towns of before.

Two towns were run both ways before he was asked (seeds 1 and 2, nothing else
changed). With the fifth in cash they failed in years 26.0 and 30.3 with 581
and 647 people without a home at the end and 336 and 335 owning theirs. With
the whole price lent they failed in years 52.0 and 34.5, with 221 and 179
without a home and 661 and 695 owning theirs. The towns were smaller (about
880 people, not about 1,070), and still no newcomer bought. Two towns. Not a
finding. Why the first ran to year 52 is not traced.

**The owner class pays for repairs at any price** (built). His words: "as an
owner class, needs more time than money". An executive, a founder or
controller of a firm, or someone living on dividends has the upkeep of what
they own done by whoever will do it, the cheapest first, whatever the price,
from their cash beyond four weeks of bills. Everyone else still weighs the
price against their own hour. Dial: `owners_pay_any_price`.

**Someone out of work with a side hustle, and the jobs on offer** (built). His
words: "they will only take the first job offered if they have a large loan,
So they've only paid off less than 50% of their loan". Asked whether someone
whose side hustle brings in $200 a week, with no loan, takes a job at $600:
"Yes, take it". So they take a job only if it pays more than the side hustle
brought in a week over the last quarter; unless they owe a loan of which less
than half is paid off (a personal loan, or the bank's loan on the side
hustle), when they take the first job offered as anyone does.
The same holds when a small business takes someone on. Dial:
`makers_weigh_jobs`.

**The loan against a home is not that loan** (built, the evening of 18
November). The rule was first built with the home loan counted too. The fresh
review counted what that did: in two small towns it sent makers into a job
paying no more than their side hustle 71 and 64 times, against 39 and 41 jobs
turned down, because nearly everyone who owns a home owes more than half of
it for ten years. Asked "A side hustle brings in $700 a week and they have a
new home loan: do they take a $600 job?", Jason said "No, stay". Dial:
`home_loan_presses`, off; with it on, the towns are the towns as they were
that afternoon.

*What it did.* 1,087 tests; 134 deliberate breaks, all caught; forty small
towns under the weekly checks, all clean; three full towns under the weekly
checks, all clean (two never reached the failure line in 60 years, the third
failed in year 50.25). Forty full towns, none crashed: 28 failed (middle year
44.9; 29 and 48.8 that afternoon) and 12 never reached the line (11). The
middle town is much as it was. The best towns are not: that afternoon four of
the forty ended sixty years with nearly everyone in work on a wage of $601 to
$872, and with this ruling none does (the same four end at $30, $50 and $24 a
week, and one fails in year 53). In forty small towns, job offers turned down
for a side hustle went from 815 to 23,609.

*Why, as far as it is known.* A firm short of customers cuts its wage by 2%
whenever more than 5% of the town has no job, and that count takes in makers
living on a side hustle who would turn the job down. In a scratch trial, not
in this code, the count was held to those who would take the firm's wage: the
wage then held in two of the four towns ($881 and $769 at year 60), settled
near $560 in a third, and still slid in the fourth. Four towns, no tests
behind it. Whether a maker who would refuse the job is part of "the queue" is
Jason's to rule on. (He ruled on it the next day: see 19 November, below.)

**A maker buys their goods in town first** (built). His words: "they can only
buy outside the town if they can't get it inside town at a reasonable price
first." Of ingredients at $189 from outside and $200 in town: "yes buys in
town because it's only $11 difference and they get it sooner"; at $298 in
town, "from out of town". Before this a maker bought every unit from outside
and no firm sold goods to anyone in town.

What the makers wanted of each good in a week is ordered the next week of the
town's firms in that line whose price is reasonable: no more than a tenth
over the outside price (that line is the builder's, between his two
examples). A firm asks what a unit costs it to make and a tenth, and never
less than the outside pays it. It makes the order with the staff it has to
spare, before anything for export, and counts it when it decides how many
staff it wants. A maker takes what the town made, the cheapest first, and the
rest from outside; what nobody took is sold outside at the week's end. A
repairer's and a builder's parts are bought the same way. The seller is a
firm in the maker's own line (the food firm supplies the food makers),
because nobody else in the model makes those goods. Someone doing their own
repairs or building still buys parts from outside. Dials:
`makers_buy_in_town`, `town_goods_premium`.

**How it was checked.** 1,081 tests, 69 of them for these five changes, each
seen to fail first where it could. The five broken on purpose 128 ways, every
break caught (six showed gaps in the tests first, and each got a test; one
showed a second place a job is offered that the rule had missed). The 27
older tests written for the fifth in cash still run with the dial at 0.8, so
that setting still works. Forty small towns of 200 exactly as the world now
ships were run for fourteen years under the weekly checks, all clean; four of
them are in the tests, and between them reach all five changes but the
newcomer buying, and every rule the whole-town tests of the earlier stages
ask for but one. The old WEF town is the town it was. With the five dials
back where they were, three small towns are the towns of the merged stage 2,
event for event.

**Three full towns as shipped**, under the weekly checks: every check clean.

| | seed 1 | seed 2 | seed 3 |
|---|---|---|---|
| as stage 2 was merged, failed in year | 23.5 | 27.25 | 29.75 |
| with the whole price lent and the owner-class rule | 52.0 | 34.5 | 34.8 |
| with the rule on jobs as well | 40.75 | 37.25 | 35.5 |
| with goods bought in town first (as shipped) | 45.0 | 49.75 | 59.3 |

Three towns, nothing tuned, not a finding, and why is not traced.

**Forty full towns, 60 years, no weekly checks (a crash hunt):** none crashed.
29 failed, in year 34.75 at the earliest and 59.5 at the latest (middle 48.8).
11 never reached the failure line of 90% unhappy. Seven of those eleven end with
about four in ten out of work, a wage of $32 to $64 a week and 80 to 87% unhappy:
just under the line, not a town that works. Four end with most people in work,
a wage of $601 to $872, and 63 to 83% unhappy. On the same forty seeds before
these rulings, 39 of 40 failed and the middle year was 28.5. Why the towns last
longer is not traced, so it is a thing to look into, not a finding.

**The fresh review.** A reviewer with no part in the build went over all five
changes in a copy of its own: 162 small towns with odd needs and every mix of
the switches, 24 towns where firms close mid-week, two full towns under the
weekly checks. Nothing critical; no fault in the accounts. One finding
mattered and is fixed: a full settings file saved before today (a run folder's
`config.json`, a batch's `base-settings.json`) was loaded with today's values
for the dials it did not have, so it ran a town that never shipped. Such a
file is now refused, with the missing dials named and the way to give them
(`--set`). A crash with goods a firm asks nothing for is fixed too (not
reachable with the needs as shipped). Left as they are, and listed in the
ledger: a firm with no chief can still put a maker out of work in charge
without asking what their side hustle brings in; goods a firm made for the
makers are lost if it closes that same week.

**What the review counted, for Jason to rule on.** Counting a home loan as "a
large loan" sent makers into a job paying no more than their side hustle 71
and 64 times in two small towns, against 39 and 41 jobs turned down (he has
since ruled on this one: see "The loan against a home is not that loan"
above). An entertainment firm's price is over the tenth while its wage is above $818, so
7% of those goods were bought in town against 73% of food. People's own
upkeep and building still buy about $18M of parts outside against $11.8M of
makers' goods.

**Why one town lasts longer.** Seed 3, twenty years, changing only whether
makers buy in town first (the builder's own count, after the reviewer's):

| | goods bought in town first | everything from outside |
|---|---|---|
| makers paid the town's firms for goods | $64.1M | $0 |
| makers paid outside for goods | $2.6M | $86.0M |
| firms paid in wages | $449.4M | $385.3M |
| out of work at year 20 | 12 of 799 | 285 of 820 |
| without a home at year 20 | 0 | 159 |

One town and one switch. It is not yet known how far this holds in the other
thirty-nine, or what the whole price and the rule on jobs add.

## Jason's rulings of 19 November 2026

One rule this world took from the WEF world was put to Jason: a firm short of
profit, with no job going, cuts its wage by a fiftieth when more than a
twentieth of the town has no job. That count took in people living on a side
hustle who would turn the job down. The ledger is
[docs/build-ledger-rtr-rulings-2026-11-19.md](../docs/build-ledger-rtr-rulings-2026-11-19.md).

It was put to him as a shop paying its staff $800 a week that wants to pay
$784, in a town where sixty people have no job and all sixty make more than
that from side hustles. His words: "if people have a side hustle that pays
more than a wage for a job, then why would they get into the queue? ... I
would assume they wouldn't even apply for the job. Unless they're unhappy. and
wanted to get out of this hard hustle ... If the queue is long, then the
employer can ask for pay less wages to the newcomers. Old staff members still
stay on the same pay rate."

He asked first whether someone on a firm's staff can ever get a rise: "If not,
then I don't think it's fair that employers can actually reduce wages." They
can. A firm that cannot fill a job for two weeks bids its wage up a fiftieth
and its staff get it; staff move to a firm that pays a twentieth more; and
someone can be made an executive.

**Who is in the line** (built). The line that lets a firm cut is now the
people out of work who would take the job at the lower wage, by the same test
as when a job is offered. Someone happy on a side hustle that brings in as
much is not in it. Someone unhappy on a side hustle is: they take a job as
anyone out of work does, and keep the side hustle for their spare hours. Dials:
`line_is_who_would_take`, `unhappy_makers_apply`.

The builder's, not his: the line is counted at the lower wage the firm would
move to; it takes in anyone out of work who would take the job, not only
people with side hustles; "long" is still more than a twentieth of the town;
and "unhappy" is the model's own measure, the one the 90% failure line counts.
His ruling of the day before stands: someone happy on a side hustle still
takes a job that pays more than it.

**Staff keep their pay through a cut** (built). A firm's wage is now the rate
for those it takes on. Each person on its staff keeps the rate they were hired
on or last lifted to. A cut touches nobody already there. A rise lifts anyone
under the new rate to it. His example: staff on $800, the firm drops its rate,
the next person hired starts on $784, everyone hired before stays on $800.
Dial: `staff_keep_pay`.

What follows from it, each a call of the builder's and each in the ledger:

- What a firm pays follows each person's own rate: its wage bill, pay day, the
  building work it books. Its executives are paid their multiple of what its
  staff are paid on average.
- What a firm reckons ahead is at the rate it offers: what one more unit would
  cost to make or build, and so whether to sell outside, whether to make or
  import, and the price it asks makers in town. The going wage in town is also
  the rate on offer: it is what a new firm starts on and what a small business
  pays someone new.
- An executive put back on the staff goes back on the staff rate they had.
- A small business keeps its staff on what they are on when the going wage
  falls, and lifts them when it rises. When it becomes a company they keep
  their rate.
- Staff taken over with a failed firm start on the buyer's rate. Someone who
  leaves and comes back starts on the rate for new hires. A firm that must let
  people go still lets go the last hired first, who are now its cheapest.

All three rules are this world's alone. The WEF world keeps the rule as it
was.

**The first build was wrong, and a fresh review caught it.** As first built, a
firm reckoned what a unit costs it to make at the average of what its staff
keep. After a boom, with wages bid up past what selling outside pays, a firm
stops and lets most of its staff go. A cut for newcomers could not move the
average of the few who were left, so the firm never started again and never
took a newcomer on. The rule exists so that an employer can take people on for
less, and the costing cancelled it. Twenty towns of 200 people, fourteen
years, the builder's own count after the reviewer's:

| | reached the 90% line | mean share with no job |
|---|---|---|
| the three dials off | 0 of 20 | 7.8% on the map, 6.6% with no map |
| as first built | 8 of 20 | 31.1% and 49.4% |
| after the fix | 0 of 20 | 7.4% and 8.5% |

Eighty small towns of that first build had passed every weekly check. The
checks prove the accounts and the places. They cannot see a town that has
stopped. The whole-town test now also asks how its towns fare: none may have
more than half its people out of work for more than three of its fourteen
years.

**Two wages in the record.** Since staff keep their own rates, "the wage" of a
town is two numbers. The record's `wage`, shown on the pages as the staff
wage, is what staff are paid on average. A second weekly measure, `wage_offer`,
is the going wage: what a job pays someone taken on now. The pages show only
the first. In the WEF world the two are one number, as before.

**How it was checked.** 1,130 tests, 43 of them new, each seen to fail first
where it could. The rules broken on purpose, with every earlier ruling's
breaks run again: 196 breaks, all caught (four slipped through at first and
each got a test). Four checks were added to the weekly checks, one of them his
rule stated directly: nobody who stayed on the same staff since last week is
paid less than they were. With the three dials off, four small towns are the
towns of the day before, event for event. The old WEF town is the town it was.
Eighty small towns exactly as the world now ships were run for fourteen years
under the weekly checks, all clean; in all eighty a firm cut its rate and its
staff kept theirs.

**Three full towns as shipped**, 60 years, under the weekly checks: every
check clean. None reached the failure line. At year 60:

| | seed 1 | seed 2 | seed 3 |
|---|---|---|---|
| people | 893 | 940 | 872 |
| with no job | 0% | 0% | 0% |
| staff paid, on average | $622 | $740 | $720 |
| the rate offered to someone new | $469 | $593 | $545 |
| unhappy | 66% | 62% | 72% |
| the day before, with the home loan ruling | never reached the line; $67 a week, 46% with no job | never reached the line; $52, 47% | failed in year 50.25 |

Three towns, nothing tuned, not a finding, and why is not traced. The share
unhappy still climbs through all sixty years in all three.

**Forty full towns, stopped at twenty-seven.** The run was stopped part way to
rest the machine it was on. Twenty-seven towns had finished (seeds 1 to 26 and
28), with no weekly checks: none crashed. One reached the failure line (seed
9, in year 56.8). The other twenty-six ended sixty years with staff paid $670
to $964 a week on average (middle $796), 0% with no job in the middle town and
11% at most, and 50% to 85% unhappy (middle 65%). The day before, on all forty
seeds, 28 reached the line and none ended on a working wage. Twenty-seven is
not forty, nothing here is traced, and "never reached the line" is not "works".
The run is owed in full.

**What the fix did not cure, for Jason to rule on.** In small towns with a cap
on people, wages are bid up in the boom past what the work brings. Under his
rule a firm cannot bring its wage bill down except by letting people go, and
it lets go the last hired, who are its cheapest. Of eighty small towns after
the fix, two (both with no map) reached the failure line; with the three dials
off, none did. One was traced: in year 6 its staff were paid $1,127 against
$1,058 on offer, in year 7 its last three firms failed on their wages, and
with nobody earning nobody founded another. Two questions follow, both his:
may a firm let go staff on the old rate to take on newcomers on the new one,
and does it let go its dearest or its newest first? A town with no cap, as the
world ships, has outside workers to hire at $1,000 and does not bid up as far;
whether this bites there is what the forty towns are for.

Also his to rule on, when he chooses: whether "long" should stay at a
twentieth, now that the line is a smaller count (in four small towns the
reviewer counted the line keeping a firm's rate 25 times against 370 cuts,
because someone long out of work will take any wage); whether someone unhappy
on a side hustle should take any wage at all, as anyone out of work for twenty
weeks does, when the example put to him was $600 against $700; and whether the
WEF world's employers should follow the third rule.

**Left as they are**, and listed in the ledger: the pages do not show the
going wage; the line itself is recorded nowhere, and the share with no job
still counts everyone; a firm's decision to sell outside can be a few weeks
stale between its quarterly reviews.

**The same afternoon: a firm in debt that is losing money lets its
longest-serving staff go** (built). The ledger is
[docs/build-ledger-rtr-shedding-2026-11-19.md](../docs/build-ledger-rtr-shedding-2026-11-19.md).
What the morning's rule did not cure was put to Jason as two questions: may a
firm whose staff are on $1,127 let them go to take on people who would work
for $1,058, and when some must go, who goes first? He answered with a rule of
his own: "if we have five staff members in a business and we have debts of
Say $2,000, we will sack the oldest staff member until the value of the total
wages is less than the debt. Before we hire new staff". And later, asked
whether a firm with cash and no debts that loses a little lets anyone go: "No,
only if in debt".

So a firm that owes the bank and lost money over the quarter lets its
longest-serving staff go, one at a time, until what they were paid a week
covers a week's share of the loss. His example: five staff on $1,127, losing
$2,000 a week; two go. It never lets the last of its staff go, nor its
executives. The letting go is the first thing in the next week's hiring; then
it takes people on as it needs them, at its rate for new hires. Dial:
`loss_sheds_staff`.

And whoever an employer has to let go, the longest-serving goes first: for
want of work and when it cannot pay as well, at firms and at small
businesses. Before, the last hired went first. That reach is the builder's
reading of his rule, and his to narrow. Dial: `longest_serving_first`.

**It took three builds, and each fault was found by counting.** Eighty small
towns, fourteen years, the mean share of people with no job:

| | on the map | no map | reached the 90% line |
|---|---|---|---|
| before this rule | 8.6% | 12.3% | 2 of 80 |
| first build: any firm with a loss, and held from hiring until a quarter without one | 20.1% | 23.6% | 3 of 80 |
| second build: any firm with a loss, no hold | 8.6% | 8.7% | 0 of 80 |
| as it stands: only a firm in debt | 9.5% | 12.4% | 1 of 80 |

- The hold on hiring was the builder's reading of "before we hire new staff".
  A firm held from hiring serves fewer customers, loses money again and is
  held again. His words say the letting go comes first, not that hiring stops.
- Without the hold the towns did well, and a fresh reviewer showed why not to
  trust it. In this model a firm makes a small loss in more than half its
  quarters, usually with cash in hand and no loan. So firms let people go at
  more than half of all quarterly reviews, and half of those let go were back
  at the same firm within four weeks. In two towns: 1,027 people let go. It
  worked as a pay cut for the old hands, at the price of half as many layoffs
  again and loans called on people who were back at work in days.
- His word had been "debts". With only a firm in debt letting people go, the
  same two towns let go 307, and 36% were back within four weeks.

As it stands the rule leaves small towns about where they were before it.

**Forty full towns on the rule as it stands**, sixty years, no weekly checks:
none crashed. Four reached the failure line, all late (one in year 52, three
in year 59). The other thirty-six ended sixty years with staff paid $390 to
$928 a week on average (middle $715), a rate offered to newcomers of $111 to
$907 (middle $552), 0% with no job in the middle town and 23% at most, and 32%
to 88% unhappy (middle 75%).

| | reached the failure line | ended on a working wage |
|---|---|---|
| the home loan ruling, 18 November, forty towns | 28 of 40 | none |
| the morning's rulings, stopped at twenty-seven towns | 1 of 27 | 26 of 27 |
| the morning's rulings and this rule, forty towns | 4 of 40 | 36 of 40 |

**Three of them again under the weekly checks** (seeds 1, 2, 3): every check
clean in every one of 3,120 weeks, and each the same town as in the forty. At
year 60: staff paid $755, $685 and $787; offered to newcomers $500, $438 and
$594; with no job 7%, 21% and 0%; unhappy 85%, 86% and 70%.

The best this world has done, across all forty towns, and still not a working
town by any measure but the failure line: in the middle town three in four
are unhappy at year 60, and newcomers are offered far less than the staff
beside them are paid. Nothing here is traced. The figures and the one check
left out (a check that assumes a cap on people, which this world does not
have) are in the ledger.

The reviewer also found that an executive put back on the staff was being
treated as the firm's newest hand, so the true longest-serving was often
passed over. Fixed: they go back in their place by when they joined.

## Stage 3: the two worlds side by side, 20 November 2026

The last stage of the design: the RTR world's own measures on the pages, then
both worlds on the same hundred seeds. The ledger is
[docs/build-ledger-rtr-stage3-2026-11-20.md](../docs/build-ledger-rtr-stage3-2026-11-20.md).
No rule of either world changed.

**On the pages.** An RTR town's dashboard has a section "Owning, letting and
side hustles": who holds the homes, what staff are paid beside the rate for
someone taken on now, side hustles and the small businesses grown from them,
appliance sets owned and small landlords, and loans against homes. A batch
page draws the same across its towns. On the town view a line under someone
means they live in a home they own, and a tick above means they have a side
hustle. The WEF world's pages are exactly as they were.

**Side by side:** `python3 -m engine compare <WEF batch> <RTR batch>` writes
`compare.html`. Run from the top folder after:

```bash
cd wef && python3 batch.py stage3-wef --seeds 1-100 && cd ..
cd rtr && python3 batch.py stage3-rtr --seeds 1-100 && cd ..
python3 -m engine compare wef/batches/stage3-wef rtr/batches/stage3-rtr
```

**What a hundred towns of each world did**, each as it ships, sixty years:

| | WEF world | RTR world |
|---|---|---|
| reached the failure line | 100 of 100 | 7 of 100 |
| when | years 14.5 to 22.2; half by year 17.75 | years 52 to 59.6 |
| seed by seed, lasted longer | 0 | 100 |

The WEF towns, when they failed, had 30% of people with no job in the middle
town (15% to 49%). The 93 RTR towns that stood had, at year 60, 0% with no job
in the middle town (30% at most), staff paid $725 a week (from $1,000 at the
start) and newcomers offered $583, and 74% unhappy (32% to 88%). They were
getting worse when the run stopped: the middle town was 11% unhappy at year
20, 60% at year 45 and 74% at year 60, and 27 of the 93 were at 80% or more.
Under the line at sixty years is not a working town. Six towns of the two,
run again under the weekly checks, were clean in every week. A fresh reviewer
recounted the comparison from the towns' own records and found no wrong count.

**One measure misleads in the RTR world: the basket.** It is the cheapest
asking price of each of the four needs. At year 60, landlord firms had no
tenants at all in 92 of the 93 RTR towns standing, and kept raising the rent
they asked; the middle town's basket was 71% that asking rent and 14% the
asking price of appliance sets, which few rent either. So "Basket against the
staff wage" in the RTR world, a middle 11,200% at year 60, is asking prices
nobody is paying. The pages say so. Whether the RTR world should measure what
people do pay was Jason's to decide; he did, the next day (below).

Nothing here is traced: not why the WEF towns fall between years 14 and 22,
nor what pulls the RTR towns down slowly.

## Jason's rulings of 20 and 21 November 2026: judged on what people actually pay

The ledger is
[docs/build-ledger-rtr-owner-pays-2026-11-20.md](../docs/build-ledger-rtr-owner-pays-2026-11-20.md).

Each person measures how they are doing against a basket: what the four base
needs cost them a week. It decides how secure they feel, and so how happy. In
the RTR world that basket counted the asking prices of firms that hardly anyone
used. A landlord firm with no tenants, or an entertainment firm whose customers
had gone to their neighbours, falls short of profit every quarter and raises its
price 3% each time (Jason's price rule), so its price climbs for decades. By
year 60 in one town an owner's basket counted a rent of $12,649 a week for a
home they owned, and someone without entertainment counted it at $5,905 a week,
while their neighbours who bought it paid about $205.

His words: "it should be judged on what they actually pay because they own it.
The reason they want to own it is because they don't want to know what the firms
are being priced at or they don't want to care." And: "happiness can be affected
by the fact that you can't purchase entertainment. But unhappiness shouldn't be
affected by not paying a $5,905 bill that no one is paying for. ... It will be
the one that they could actually achieve, not the one that's way out of scope."

**The rules.** A home or appliance set of your own counts at the upkeep it needs
that week, at its age, plus the payment on a loan against a home. A need you go
without counts at the lowest price a firm or a neighbour asks: a neighbour's
side hustle, or a small landlord's rent. The town's basket is the average of its
people's. The firms' asking prices are kept as a measure of their own, "Asking
basket". What people shop with is not changed. The WEF world is not changed.

**A hundred RTR towns under each rule**, the same seeds, sixty years, the middle
town at year 60:

| | Before | Owners' rule | Both rules |
|---|---|---|---|
| reached the failure line | 7 of 100 | 0 | 0 |
| unhappy | 74% | 39% | 24% (15% to 61%) |
| with no job | 0% | 2.7% | 3.4% |
| staff paid | $725 | $821 | $827 |
| basket against the staff wage | 11,200% | 793% | 128% |

Three full towns under each rule, run again under the weekly checks, were clean
in every week. The WEF world's hundred towns (made on 20 November) all failed,
in years 14.5 to 22.2.

Under both rules the middle town is still getting worse: 5% unhappy at year 20,
14% at year 40, 24% at year 60. At year 60, 49% of those out of work are
unhappy, 24% of those with a job and 4% of those who live on their shares. The
unhappiest towns are poor ones: in seed 15, 51% unhappy and staff paid $230 a
week; in seed 49, 61% and $462. Traced below.

## The least someone out of work will take, 21 November 2026

The ledger is
[docs/build-ledger-rtr-reservation-floor-2026-11-21.md](../docs/build-ledger-rtr-reservation-floor-2026-11-21.md).

Jason asked why pay fell so low in those towns, and to fix it. The trace of
seeds 15 and 49: the least someone out of work would take fell 5% a week of
their spell, with nothing under it, so after twenty weeks it was nothing. Nearly
everyone out of work would take any pay (215 of 222 in seed 15 at year 30). So
the line for a job stayed over 5% of the town, and under Jason's rule of cutting
when there is a queue each firm short of profit cut its rate 2% a quarter, for
decades: in seed 15 from about $950 a week to about $110. The 5% a week, the 2%
and the 5% of the town are the builder's numbers (C), not his.

**The rule (C).** Someone out of work will not take a job that pays less than
their own basics cost them a week (their basket, as he ruled on 20 and 21
November), leaving out a payment on a home loan. Someone who owes a large loan
has no floor, as he ruled: they take the first job offered. A dial,
`reservation_covers_basket`, in the RTR world only. The WEF world is not
changed.

**A hundred RTR towns**, the same seeds, the middle town at year 60:

| | Before | With the floor |
|---|---|---|
| reached the failure line | 0 of 100 | 0 of 100 |
| unhappy | 24% | 20% |
| towns over 30% unhappy | 27 | 13 |
| with no job | 3.4% | 8.1% |
| towns over 15% with no job | 2 | 16 |
| the rate a firm offers someone new | $698 | $810 |
| the lowest such rate in any town | $110 | $598 |
| staff paid | $827 | $858 |
| towns with staff paid under $500 | 3 | 0 |

Seed 15: 51% unhappy and staff paid $230 before, 25% and $720 after. Seed 49:
61% and $462 before, 22% and $842 after.

The cost is more people out of work, and nearly all of them are unhappy. In the
two worst towns (seeds 91 and 89, 33% and 28% with no job) there was no job
going unfilled at 22 of 24 counts: the jobs did not grow with the town (seed 91,
633 jobs for 783 people at year 5, 582 for 900 at year 60). The floor stops the
pay falling; it does not make work. Why those towns have fewer jobs than under
the old rule is not traced.

*Corrected the same day, by the trace below:* they did not have fewer jobs. The
jobless rate counted everyone with no employer, and most of the rise was people
running a small business of their own.

## Who counts as jobless, 21 November 2026

The ledger is
[docs/build-ledger-rtr-jobless-own-work-2026-11-21.md](../docs/build-ledger-rtr-jobless-own-work-2026-11-21.md).

Jason asked why those towns had fewer jobs, and to fix it. Counted in 27 towns
with the floor and without it, at year 60, as a share of the town:

| | With the floor | Without |
|---|---|---|
| counted with no job (no employer) | 8.2% | 4.3% |
| of whom no work at all | 0.4% | 0.2% |
| of whom running a small business | 6.8% | 3.5% |
| of whom running a side hustle | 0.9% | 0.4% |
| working for a firm | 57.3% | 56.5% |
| working for a small business | 34.5% | 39.2% |

Nobody lost work. The jobless rate counted everyone who works for nobody else,
so someone running a business of their own was counted as having no job. With
the floor, more people run a business than work for one.

**The fix (the builder's call, C): a measure only.** In the RTR world the
jobless rate now counts those with no job and no small business or side hustle
of their own. The old figure is kept beside it as "No employer", with "Running a
small business" (both charts on the batch page) and the share on a side hustle.
Nothing a firm or a person does reads it, and the towns did the same: the
hundred towns run again made the same events as before, town for town. The WEF
world is not changed: nobody there works for themselves.

The hundred RTR towns (`rtr/batches/ownwork-rtr`), the middle town:

| | Year 20 | Year 40 | Year 60 |
|---|---|---|---|
| jobless (no work at all) | 0.1% | 0.1% | 0.1% |
| no employer (the old figure) | 6.2% | 8.8% | 8.1% |
| running a small business | 4.1% | 6.9% | 7.0% |
| on a side hustle | 1.9% | 1.0% | 0.6% |

At year 60 the highest is 9.9% (seed 55); 3 towns are over 5%.

Seen, not traced: with the floor, those running a small business are more
often unhappy (14% against 4% at year 60 in the 27 towns), and those on a side
hustle (52% against 26%).


## A job beside a business of their own, 22 November 2026

Traced in 27 towns at year 60: with the floor, someone out of work running a
small business of their own would not take a job that paid less than their
basics, though taking a job does not close the business. Of the 241 unhappy
business owners, 74% would take nothing below a figure above the going wage,
and the middle one had been out of work for 454 weeks.

Put to Jason as Mia (basics $900 a week, a business bringing in $620, a job at
$790, and the business perhaps $200 on the hours left beside the job): take the
job when its pay and what the business would still bring in cover her basics.
His words: "Yes, that makes a lot more logical sense." (J)

**What was built.** The least someone out of work will take is now their basics
less what a business of their own would still bring in beside a job (dial
`floor_counts_kept_business`). What it would still bring in is the builder's
reckoning (C): its takings less goods over the last quarter, in proportion to the
hours it would have beside a job (the owner's week less the job, the road and the
upkeep of their own things, and its staff's hours) against the hours it used,
less what its staff are paid. A fresh review found two faults in the first
version (staff wages scaled down with the hours; last week's hours used for
someone just let go); both were fixed before the towns were run.

The hundred RTR towns (`rtr/batches/floorbiz-rtr` against
`rtr/batches/ownwork-rtr`), the middle town:

| | Year 60 before | after |
|---|---|---|
| unhappy | 19.9% | 18.6% |
| no employer | 8.1% | 6.2% |
| running a small business | 7.1% | 5.5% |
| rate offered someone new | $810 | $758 |

All 100 towns survived, as before. The rate offered someone new fell a little:
more people now stand in the line for a job.

**Not fixed by it.** In the 27 towns the share of business owners out of work
who are unhappy did not fall (14% before, 16% after). Most of those left have
basics measured far above the going wage (in the middle $2,297 a week, against
$709 for a happy business owner). The prices behind that look wrong: for
someone going without appliances, the lowest price on record was $5,214 to
$33,568 a week in 22 of the 27 towns. Not traced yet.

## Going without appliances, 22 November 2026

The firm that rents out appliances loses nearly all its customers within ten
years, as people own their own sets, and by his rule its price only rises: 3%
every quarter it misses its profit target. In seed 1 its rent went from $76 a
week at year 5 to $9,417 at year 60, with no customer, while owning a set cost
about $20 to $24 a week. The few with no set (3 to 10 a town) were counted as if
their basics included that rent.

Put to Jason: should someone without a fridge count it at what owning one
costs, about $23 a week, when renting costs more? "yes, go ahead with the fix"
(J). Dial `going_without_appliances_at_owning`. Homes are not changed (the
builder's call, C): owning a home takes a deposit and a loan.

The hundred RTR towns (`rtr/batches/appliances-rtr`): all 100 survived. In the
middle town at year 60, 20.8% unhappy against 18.6%, with 53 towns a little more
unhappy and 42 a little less: about even, read as the towns going different ways
rather than as the rule's effect.

Found by the review, not fixed: a newcomer buying a home holds back four weeks
of basics at the rents on offer, appliances at the firm's rent (about $37,700 at
$9,417 a week). It may stop newcomers buying homes in old towns. Not traced.

## A newcomer and appliances, 22 November 2026

A newcomer signed up for every base need at the cheapest firm, whatever it
charged, so in an old town they took on the appliance firm's runaway rent; and
a newcomer buying a home held back four weeks of it (about $37,700). Jason:
"Who would pay $9,000 if they could pay $23." (J)

Now (dial `arrivals_own_appliances`): a newcomer for whom owning a set is
clearly cheaper than renting one builds their own on arrival if they can pay
for the parts. If not, the week's review rents them one only if they can
afford it, as for anyone in town. Nobody rents while building a set. A buyer
holds back appliances at no more than owning costs.

The review found the first version's newcomers rented anyway at the week's
review, some while building a set; fixed before the towns were run. The rule as
first put to Jason said they would "go without until they can"; read literally,
most newcomers would have had no set from the first week, though the opening
rent is $55, so they rent what they can afford instead (the builder's call, C,
put to him).

The hundred RTR towns (`rtr/batches/arrivals-rtr`): all 100 survived; the
middle town at year 60 is 20.5% unhappy against 20.8%, with 50 towns up and 50
down.
