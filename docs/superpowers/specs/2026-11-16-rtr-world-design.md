# The Right to Repair world (RTR): design

16 November 2026. The second world, to set beside the WEF world this model already
runs. **(J)** marks what Jason decided, with his words where he gave them; **(C)**
marks the builder's calls, each with a number or rule he can change. Nothing here is
built yet.

## 1. What it is, and why

Jason's question, 12 November: does a world where "you own nothing, everything is
rented or subscribed" hold together, and what would the opposite world do? The WEF
world is built and has been run (two batches of 100 towns; all failed). This is the
opposite world.

His brief, 16 November: "this one runs pretty much the same rules as a WEF, but this
one allows people the decision to either rent or buy. They can buy their own
appliances. They can repair their own appliances. All products and manufacturing can
be open-sourced ... So it covers things like ownership, rights to repair, and open
source designs and software. In other words, giving people freedom to do whatever
they want.. We'll call this one right to repair or RTR".

On record since 12 November, before any run (`docs/predictions.md`): Jason expects
open source to be "more constructive for society, but if it is too open it may
collapse as well". Claude expects neither world to collapse by itself. The failure
rule is the same in both worlds: the first week 90% of everyone is unhappy.

## 2. Goals, and what it must not become

- **Goal.** The same town, the same seeds, the same measures, with the RTR rules
  switched on, so the two worlds can be set side by side town for town.
- **Goal.** Every RTR rule can be switched on its own, so a result can be traced to
  the rule that caused it.
- **Not a goal.** A better or kinder economy by design. The rules below give people
  more they may do; whether the town does better is what the runs are for.
- **Would make it a failure even if it runs:** the WEF world changing in any way
  (its towns must stay the same towns, record for record); an RTR rule that hands
  people money or goods from nowhere (every dollar still moves through the five
  flows); numbers of the builder's passed off as Jason's.

## 3. One model, two worlds

One dial, `world`, `wef` (the default) or `rtr`. With `wef` nothing in this document
runs and every existing town is the same town. With `rtr` the rules of sections 5 to
11 apply. Each rule also has its own dials (below) so it can be weakened or switched
off inside an RTR town. `configs/rtr.json` holds `{"world": "rtr"}`. A batch can then
run `--vary world=rtr` and put both worlds on one page. (C)

Everything not named here is as the WEF world is today, with Jason's rulings of 16
November (no cap on people, 60 starting homes, the fare before the rent for work, the
well-off spend more, shops open near the unserved, a lost luxury fades in a year,
transport always sold on, unspent money sits, no tax and no welfare). (C: his words
were "pretty much the same rules"; put to him as an assumption and not objected to.)

## 4. What Jason decided (16 November)

1. **Everything is open, always.** "Let's go for the most purest form, so if anyone
   creates anything, it's always open source ... Their modifications are open source
   and so on and so on."
2. **New things come from people, for the fun of it.** "If companies are only making
   things to make money, then what's the point? Why don't I just leave it up to the
   people who are actually going to create things for fun?"
3. **Anyone creates, even while struggling.** "It gives them the opportunity to get
   out of the struggling."
4. **Time, then money, then a loan.** "Time, I think, is the main thing to come up
   with an idea. Money is the way to expand it, and loans is to make it a business."
   What it costs to start depends on the thing: software on a computer they already
   have costs nothing, chairs need "table saws, drills, tools"; "you could get a
   loan. if the bank thinks it's profitable."
5. **Anyone can make an open design**, "build it themselves or build it for other
   people who don't want to build it themselves. and so they can make a profit".
6. **Rent or buy**, homes as well as appliances. "landlords can opt to rent or sell
   to a person ... if their income allows for it, they will get a loan and buy. If
   they can't do that, then they'll rent. until their wages increase enough".
   A landlord sells when the price it can get is worth more than the rent it would
   collect, or when it needs the cash (put to him; "That is right").
7. **People can build homes with a bank loan**, to live in or to rent out. "landlords
   can build and also rent people looking for housing can build as well".
8. **A home can be borrowed against and foreclosed.** A foreclosed home is sold for
   the debt owed, offered first to a renter who can pay or borrow for it, then to a
   resident who already owns a home (who lets it), then to a landlord firm ("That's
   an actual good order"). The person foreclosed on rents if they have the money and
   is otherwise homeless.
9. **Repair your own** with your time and parts at cost, or pay someone who repairs
   as a side hustle ("Yes, that is correct").
10. **Prices.** A company's price still never falls (his decision 1). A person making
    for others charges what it costs them plus a little and can undercut ("Yes, that
    is potentially true": tentative).

## 5. Time (C)

The WEF world has no hours except travel. RTR needs them, because creating,
repairing, building and making all take time.

- Everyone has `free_hours` (60) a week beyond sleep and keeping themselves. A job
  takes `job_hours` (40). Hours on the road come off (already counted each week).
  What is left is **spare time**: about 20 hours for someone in work, 60 for someone
  out of work.
- Spare time is spent in this order: keeping up what they own; their side hustle;
  building for themselves. Whatever is left counts toward ideas (section 9).
- One worker-week in the model's costs is 40 hours.
- **What an hour is worth.** When someone weighs doing a thing themselves against
  paying for it, an hour of their own spare time counts at what the model already
  says an hour on the road is worth (a fortieth of the weekly staff wage, $25 at the
  start). So building or repairing for yourself is not free: it is parts plus hours.
  Someone short of hours, or whose hours a maker can do for less, pays a maker.
  (C, after the builder check: without this nobody would ever pay a repairer or a
  builder.)

## 6. Owning and repairing appliances

- A person may own their appliance set instead of renting one (J).
- **Getting one.** They build it from the open design (J: "build it themselves"):
  the parts the WEF firm uses for a set, bought from outside at the outside price
  (40 units at $135, $5,400 at the starting prices), and 20 hours of their spare
  time. Or they buy one from a maker (section 8). (C: the parts and hours are the
  WEF firm's own figures; buying parts from outside is the simplest "at cost".)
- **Keeping it.** Each week it needs the parts and time the firm's upkeep needs (at
  first about $4 of parts and 24 minutes, more as it ages). Their own time, or a
  repair maker's. Without the parts or the time it wears, as a neglected unit does
  in the WEF world. When it is past keeping they build or buy another. (J for the
  rule; C for using the WEF upkeep figures.)
- **When.** Someone with no set at all builds one if they can pay for the parts (C,
  after the review of stage 1a: otherwise a town whose appliance firm has gone could
  never have sets again). Someone renting a set gets their own when owning costs clearly less a
  week than their rent (parts spread over its ten-year life, plus upkeep, against
  rent, with the usual 5% reluctance to change) and they have the money and the
  hours. A personal loan may pay for the parts, by the WEF rule (up to eight weeks
  of wages). (C)
- A firm that rents sets keeps renting them, and sells one by the landlord's rule in
  section 7. (C: his rule for landlords, applied to every firm that rents things.)
- An owned appliance set cannot be taken for a debt and is not sold second-hand. (C)

## 7. Owning homes

**Three ways to own a home** (J): buy one a landlord offers; buy a foreclosed one;
build one.

- **The loan.** (Changed 18 November: Jason ruled "Lend the whole price", so `mortgage_ltv`
  is now 100% and nobody needs a fifth in cash. The 80% below was the builder's number.)
  The bank lends against the home: up to `mortgage_ltv` (80%) of its
  price, over `mortgage_weeks` (1,040, twenty years), at the rate firms pay (6% a
  year). The borrower pays the rest from their own cash. "If their income allows"
  (J) means the weekly payment is no more than `mortgage_income_share` (30%) of their
  income. (C: the three numbers.) Interest leaves town, as all the bank's interest
  does (J, 12 November).
- **Buying from a landlord** (J). Each quarter a landlord offers a home for sale when
  either (a) it is short of cash (it could not meet a wage or loan payment that
  quarter, or its cash is under its usual reserve), at the home's value as it stands
  (the cost of building it less wear); or (b) a buyer will pay more than the rent it
  would collect on that home, net of upkeep, over ten years (the longest any
  shareholder in the model looks ahead). That ten years of net rent is the asking
  price of a let home: the landlord sells to whoever can pay it. (C: how "worth more
  than the rent" and "needs the cash" are measured, and that the asking price is
  the floor.)
- **An empty home** (J, 16 November, of two answers offered: "Sells it cheap"). A
  home that has stood empty for a year is offered at its value as it stands (the
  cost of building it less wear), to renters first. (C: a year is 52 weeks.)
- **Who may buy a let home.** Its sitting tenant first; otherwise only someone who
  will go on letting it (a resident owner or a landlord firm), and the tenant stays.
  A renter other than the tenant buys only empty homes. So no sale puts a tenant
  out. (C, after the builder check.)
- **The land.** A buyer owns the home and its plot. A block with a privately owned
  home on it cannot be sold whole or pulled down for premises. (C)
- **Building** (J). A person builds on a plot. Blocks hold eight homes; an empty
  block may be taken as a block of plots, free while land is not scarce, as a firm
  takes one, and each builder owns their plot; once no block is empty a builder
  needs a free plot on such a block. The plot must be within reach of their work:
  nobody builds where they could not get to their job from (C, after the review of
  stage 1a). The materials are the landlord's (500 units,
  $54,000 at the outside price) and the work is 1,200 hours, their own spare time or
  a building maker's. The loan is drawn as the materials are bought: four
  fifths of each week's materials, the rest from their cash, of which they keep four
  weeks of bills in hand. They go on renting until it is finished. (C: plots; the WEF
  build figures; the four weeks.)
- **Building to let** (J). The same, by a resident who already has a home and
  "believes that they can rent" it out. They believe it when someone was turned away
  for want of a home in the last quarter, and the going rent would cover the loan
  payment and upkeep with `maker_margin` (10%) to spare. One home at a time. They let
  it at the going rent for its place. They are a small landlord: a person, not a
  firm. (C: the test. It asks for a sign that a home is wanted, so it does not copy
  the building while homes stand empty that decision 17 is about.)
- **Keeping it.** Upkeep is the landlord's upkeep (at first about $43 of parts and
  1.6 hours a week, more with age), by their own time or a repair maker's. (C)
- **Buy, build or rent.** Each quarter a renter who passes the bank's test takes the
  cheapest of the three by weekly cost (loan payment and upkeep against rent),
  if it is clearly cheaper than their rent. Otherwise they rent "until their wages
  increase enough" (J). (C: cheapest by weekly cost.)
- **Borrowing against a home** (J). An owner may borrow against their home, up to
  the same 80% of its value less what is owed on it, for a side hustle or a business
  (section 8) or to build. The bank lends only when the repayments fit their income,
  by the same 30% test (J, 16 November, of two answers offered: "No, they need
  income"). So someone with no income cannot borrow against their home to pay their
  bills.
- **Foreclosure** (J). After `grace_weeks` (4) missed payments in a row the bank
  takes the home and sells it for the debt owed, in his order: a renter who passes
  the bank's test (for a let home that is its sitting tenant; other renters may take
  an empty one); then a resident who owns a home, who lets it; then a landlord firm.
  A tenant stays through the sale. Until someone takes it, it stands empty
  on offer, and the asking price falls 5% each quarter. The former owner keeps
  nothing from the sale: it sold for the debt. They rent if they can pay, otherwise
  they are homeless, by the rule the model already has (J).
- **Simplifications** (C). An owner does not sell or move by choice; a job out of
  reach means a ride or the job is lost, as for anyone. A small landlord's tenant who
  misses the rent is put out after the same four weeks as any tenant.

## 8. Makers: side hustles and small businesses

A **maker** is one person supplying others with their own time (J: "side hustles or
actual small businesses").

- **What.** Any need people go to a seller for: food, entertainment, anything
  invented (section 9); and two trades that only exist in RTR: repairing what people
  own, and building appliance sets and homes for people who "don't want to build it
  themselves" (J). Not the ride. (C: the list.)
- **Starting** (J: their own money first). A one-off cost for tools by kind:
  entertainment and software $0 (his example: the computer they already have),
  invented things $500, food $2,000, repair $1,000, building appliance sets $5,000
  (his chairs), building homes $10,000. From their cash, a personal loan, or a loan
  against their home. (C: the amounts.)
- **Who starts one.** Each week, someone with ten or more spare hours and no side
  hustle may start one: with chance `hustle_rate_struggling` (10%) if they are out
  of work or their income does not cover their basket (J: a way out of struggling),
  otherwise `hustle_rate` (1%) times their appetite for risk. They pick the trade
  where their price most undercuts the cheapest seller within reach of them. (C)
- **Price** (J, tentative): cost plus `maker_margin` (10%). Cost is the goods at the
  outside price and their hours at what an hour of theirs is worth: their wage, or
  for someone out of work the wage they would now accept, which in the model falls
  the longer they are out, but never less than `maker_hour_floor` (half the going
  hourly staff wage). So the struggling undercut most and still earn. Set again each
  quarter; it can fall. (C: valuing their hours; the floor after the builder check,
  since the wage someone would accept reaches nothing after twenty weeks out of
  work.)
- **Repairers and builders.** These two trades sell hours: the price is the parts
  at the outside price plus the maker's hours at their hourly worth, plus the 10%.
  Someone uses one when that comes to less than doing it themselves (section 5), or
  when they do not have the hours: a home takes 1,200 hours, sixty weeks of an
  employed person's spare time. (C)
- **How many they serve.** Their spare hours divided by the hours one customer
  takes (the firm's own service figure). A maker works from home: customers reach
  them as they reach a shop. Customers choose between firms and makers on the same
  reckoning of cost. (C)
- **Stopping.** A maker with fewer than a fifth of the customers they could serve
  for a quarter gives it up; the tools are gone. (C)
- **Becoming a business** (J: "loans is to make it a business ... if the bank thinks
  it's profitable"). A maker full for a quarter may ask the bank. It lends up to
  `hustle_loan_weeks` (26) weeks of the side hustle's weekly profit over that
  quarter, over five years at the firms' rate. With it they become a **small
  business**: still working from home, they take on staff at the going wage, as many
  as their customers need, and serve more people. It has no premises, no executives
  and no shareholders, and still prices at cost plus a little. (C: the numbers and
  the shape; a loan on profit is new, the WEF bank lends only on wages and on what a
  firm owns.)
- **Becoming a company.** A maker or small business owner who has saved the capital
  any resident needs to found a firm ($150,000 for a service) may found one by the
  WEF rule, with premises and shares, and bring their customers. From then it is a
  company, and its price never falls (J). (C: after the builder check; a firm of the
  WEF kind cannot live on a side hustle's customers.)
- **Making for yourself.** Covered by sections 6 and 7 (appliance sets and homes).
  Food, entertainment and services are bought, from a firm or a maker, as now. (C)

## 9. Ideas: where new things come from

- In the WEF world a new need appears when a founder with capital starts a firm for
  it. In RTR founders of firms do not invent (J: not companies for money).
- Each week each person has a chance of an idea: `idea_rate` (0.00002) for every 20
  spare hours they have that week. That is about one new thing a year in a town of
  1,000 where most have jobs, and more when many are out of work. (For scale: the
  middle WEF town under the rulings had invented 6 needs by year 15.) (C)
- An idea is a new need exactly as the WEF world makes one: a service some people
  want. It is open (J): the creator may start it as a side hustle at once, at the
  start-up cost for invented things, and so may anyone else, from the next week.
- Nobody is paid for the idea itself. (C, from J: for the fun of it.)

## 10. The bank in RTR

As in the WEF world (federal, never fails, interest leaves town, a personal loan up
to eight weeks of wages, called in when the job goes), plus the three new loans
above: against a home (section 7), on a side hustle's profit (section 8), and for
building (section 7). The bank still cannot make anyone sell shares.

## 11. Classes, wellbeing and failure

- Classes stay as they are (owner, working, out of work), so the two worlds compare.
  A maker with no job counts as working when their side hustle brought in at least
  half their basket over the last quarter; otherwise out of work. Owning a home or
  being a small landlord is recorded, and is not a class. (C)
- Wellbeing is measured as in the WEF world, with four things said for owners (C,
  after the builder check; half of wellbeing rests on them):
  - **The basket does not shrink when someone owns.** An owner's basket counts a
    home and an appliance set at the going rent, as it does for anyone going
    without one. Their real bills are lower, and what they save shows up as cash.
  - **A loan against a home is not counted as debt while it is paid on time.** It is
    secured on the home. A missed payment is a blow, as a missed rent is, and
    foreclosure is a blow as eviction is.
  - **What the bank would still lend an owner against their home counts toward their
    cushion**, with their cash. Otherwise paying a deposit would make every buyer
    feel poorer the day they bought. With no income, or while the bank refuses them,
    that is nothing (J: no income, no loan).
  - **A maker has a position** (as someone with a job has) when their side hustle
    brought in at least half their basket over the last quarter.
- Income from a side hustle or from letting a home counts as income. An owned home
  or appliance set counts by its condition, as a rented one does. The failure rule
  is unchanged (J).

## 12. The record and the pages

- Everything recorded now is still recorded, so every WEF measure exists for RTR.
- New events: a home or appliance set bought, built, foreclosed and sold on; a loan
  against a home; a side hustle started and given up; an idea; a maker becoming a
  firm. New weekly measures: who owns the homes (lived in by their owner, let by a
  small landlord, held by a landlord firm, foreclosed and empty); appliance sets
  owned; makers and their customers; loans against homes; foreclosures.
- The town view marks homes lived in by their owner and people with a side hustle;
  the dashboard and the batch page gain charts of the new measures. (C)

## 13. Things to know before reading the results

- **The WEF model has no patents.** In it any company with the capital can already
  sell any product; what keeps people out is the capital a firm needs ($150,000 for
  a service, $600,000 for homes or appliances) and the rule that an entrant needs a
  clear margin. So "open" in RTR shows up as people making and repairing with
  nothing but their time and a few tools, not as broken monopolies.
- **Money leaves town in new ways.** Parts for building and repair are bought from
  outside, and loans against homes pay interest to the federal bank.
- **Sold for the debt** means a foreclosed owner loses what they had paid off.
- **Nothing is tuned.** Every number marked (C) is a starting value.

## 14. How it will be built

Three stages, each with its rules written first, tests before code, whole towns run,
and a fresh reviewer, as every stage so far.

1. **Owning.** Time; owning and repairing appliances; owning homes (buying,
   building, loans, foreclosure, small landlords). The `world` dial and the proof
   that WEF towns are unchanged.
2. **Making.** Makers, ideas, side hustles becoming firms.
3. **Seeing.** The new measures on the pages; then the WEF and RTR batches on the
   same 100 seeds, side by side. The WEF batch must be made again first: the one of
   16 November was made before the cap on people was dropped.

**Built so far.** Stage 1 was split in two when it was planned, and both parts are
built (17 November). **1a, building and owning your own**: spare time, an appliance set
of one's own, a home built on a plot, the loan against a home, foreclosure and the sale
for the debt to a renter, the record. **1b, buying, selling and letting**: buying from a
landlord, the cheap sale of homes that have stood empty, small landlords (building to
let, one loan on all their homes, rent as income), let homes sold only to those who go
on letting them with the tenant staying, and the whole foreclosure order (a renter, then
a resident who owns, then a landlord firm). Two calls made while building 1b add to what
section 7 says, and both are in the ledger (`docs/build-ledger-rtr-stage1b-2026-11-17.md`):
an *empty* home is bought to let, by a person or by a landlord firm, only when a newcomer
was turned away for want of a home in the last quarter, the sign already asked of someone
building to let; and when the bank forecloses on someone still building a second home,
the unfinished build goes first and what was lent on it is written off. A fresh review
of 1b found one crash and five faults in how the rules behaved (among them that "the
cheapest of the three" had not been built); all were fixed, and the ledger has each.

**Stage 2, making, is built (18 November)**, in two parts; the plan is
`docs/superpowers/plans/2026-11-18-rtr-stage2-makers.md` and the ledger
`docs/build-ledger-rtr-stage2-2026-11-18.md`. **Part A, side hustles**: a maker selling a need
or hours from home, what their hour is worth, their price, starting and stopping, repairers
and builders, a maker's income, class and position. **Part B**: ideas from spare time; the
bank's loan on a side hustle's profit and staff; a side hustle becoming a company. Calls
made while building that add to or change what sections 8 to 11 say (each is in the ledger
with its reason and what it costs if wrong):

- A side hustle has a till for the week: customers pay into it, the goods and then any staff
  are paid out of it, and what is left is its owner's at the week's end. So a maker buys the
  week's goods out of the week's takings, and someone with no money can start.
- The cost of living is the cheapest price someone could buy at: the firms' cheapest, or a
  maker's who has room that week if that is less.
- Someone with no home can run a side hustle (they sell where they are found). One with no
  hours for customers for a whole quarter is given up.
- A repairer or home builder charges their hour and that hour's parts plus the margin; the bank
  still lends its four fifths of a home's materials to the owner. Someone building works their
  own hours first. A repairer or builder starts only with enough work in sight to keep them
  past their first quarter, and never becomes a small business.
- A small business prices its hour at the going wage from the day it borrows. It takes on a
  worker for a full week's paying work, with a week of their wage in hand, and keeps them
  while they pay half their wage. A maker borrows only when there is a worker's worth of
  customers they cannot serve who would buy at the business's price, and counts as waiting
  only those who would have bought.
- The loan on profit stays in the business and is unsecured: unpaid, what is in the business
  and then what cash its owner has go to the bank, the rest is written off, and they are
  refused credit as after a personal default. Their home is not at risk for it.
- A small business hires residents only. Only a maker of a need becomes a company.
- Founders of firms stop inventing only while people have ideas (`idea_rate` above 0), so
  that stage 2 can be switched off whole.

One thing in section 5 was for Jason to keep or change once towns had been run with it:
because everyone's own spare hour counts at the going wage, people with idle hours pay a
repairer who charges less than that (the ledger has the reviewer's figures).

**Jason's rulings of 18 November** on that and five other calls of mine (ledger:
`docs/build-ledger-rtr-rulings-2026-11-18.md`; his words are in it and at the head of
`tests/test_rtr_rulings.py`):

- Idle people paying a cheaper repairer: kept. Added, and built: someone of the owner class
  has repairs done by anyone at any price ("needs more time than money"). `owners_pay_any_price`.
- A small business keeping its rate after its staff have gone: kept.
- A landlord firm buying a tenanted home from another only at a tenth over the price: kept.
- New, and built: a newcomer who finds nothing to rent may buy an empty home the bank holds,
  if their cash and the wage of the job they come for allow it by the terms of section 7.
  `newcomers_buy`. In the towns run so far it is never used: workers come only in a town's
  first seven years and the bank holds no home until after that.
- Changed, and built, from what that count showed: **the bank lends the whole price of a home
  where the income allows** ("Lend the whole price"). The four fifths of section 7, and the
  fifth a buyer or builder had to find in cash, were the builder's numbers; his words for the
  loan were "if their income allows". `mortgage_ltv` is 1.0. One dial, so it holds wherever
  section 7 said 80%: buying, building, a home to let, and borrowing against a home already
  owned (which was not put to him in so many words).
- Changed, and built: someone out of work with a side hustle takes a job only if it pays more
  than the side hustle brought in a week over the last quarter, or, with a loan less than half
  paid off, the first job offered as anyone does ("Yes, take it", of $600 against $200).
  `makers_weigh_jobs`. The loan against their home is not such a loan ("No, stay", of a $600
  job against a side hustle bringing in $700 and a new home loan; the evening of 18 November):
  a personal loan or the bank's loan on the side hustle is. `home_loan_presses`, off.
- Changed, and built: a maker buys their goods in town first, from a firm in their own line
  that makes them, when its price is no more than a tenth over the outside price (his examples:
  $200 against $189 yes, $298 no; the tenth is the builder's). The firm makes them to last
  week's order with staff it has to spare, at its cost and a tenth, never under what the
  outside pays it. `makers_buy_in_town`, `town_goods_premium`.

**Jason's rulings of 19 November 2026** change one rule this world took from the WEF world
(a firm short of profit, with no job going, cuts its wage when there is a line for work).
They are in the ledger with his words (`docs/build-ledger-rtr-rulings-2026-11-19.md`). The
WEF world keeps the rule as it was.

- Built: **the line is those out of work who would take the job** at the lower wage, not
  everyone with no job ("I would assume they wouldn't even apply for the job").
  `line_is_who_would_take`. "Long" is still more than a twentieth of the town (the builder's).
- Built: **someone unhappy on a side hustle takes a job as anyone out of work does** ("Unless
  they're unhappy. and wanted to get out of this hard hustle"). `unhappy_makers_apply`.
- Built: **a cut is for those hired after it** ("Old staff members still stay on the same pay
  rate"). A firm's wage is the rate for those it takes on; each person on its staff keeps
  theirs; a rise lifts anyone under the new rate. What a firm pays follows each person's
  rate; what it reckons ahead (one more unit made or built, selling outside, the going wage)
  is at the rate it offers. `staff_keep_pay`. The first build reckoned ahead at what the
  staff keep, and a fresh review showed that stopped small towns: the ledger has the count.
- Built, the same afternoon (`docs/build-ledger-rtr-shedding-2026-11-19.md`): **a firm in debt
  that lost money over the quarter lets its longest-serving staff go** until what they were paid
  a week covers a week's share of the loss, never the last of them ("we will sack the oldest
  staff member until the value of the total wages is less than the debt. Before we hire new
  staff"; and of a firm with cash and no debts: "No, only if in debt"). It is the first thing in
  the next week's hiring; then the firm takes people on as it needs them, at its rate for new
  hires. `loss_sheds_staff`. And **whoever an employer has to let go, the longest-serving goes
  first**, for want of work or of cash as well, at firms and small businesses (the builder's
  reading of how far his rule reaches). `longest_serving_first`. Two earlier builds were
  overturned by counts the same day (a hold on hiring; any firm with a loss): the ledger has
  them.

Stage 3 is not built.

Left to the builder: every name in the code, the order of steps within a week, and
how the new measures are drawn.
