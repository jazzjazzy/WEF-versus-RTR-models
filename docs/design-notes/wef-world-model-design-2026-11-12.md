# WEF World Model, design notes (spitballing, 12/11/2026)

Question: if companies keep moving to "you own nothing, everything is rented or subscribed", does that world hold together or collapse, and why? Second world (open source / ownership) parked for now.

## Agents
- Arrive two ways: hired by an existing firm, or bring capital and found a firm.
- Have a job, wages, savings, shares. Can change jobs, including for affordability.
- Need housing, food, appliances, entertainment; all rented or subscribed. Nothing owned except shares and cash.
- Temperament fixed at birth (randomised): loss aversion, natural time horizon, return expectation as a shareholder.
- State: security (falls with job loss, price rises, dwindling savings; recovers slowly). Security sets the effective horizon; horizon drives decisions (sell vs hold shares, take first job vs wait, which subscription to cancel first). Grounding: Kahneman & Tversky loss aversion; Mullainathan & Shafir scarcity.
- Happiness read from security. FAILURE = 90% of agents unhappy.

## Firms
- Four founders on day one: housing, food, appliances, entertainment; each owned by its founder.
- Later founders may compete or invent a fifth need. No limit.
- Price rule: price rises whenever profit falls short of shareholder expectation. Expectation = holding-weighted average of shareholders' own expectations.
- Firms can fail; new ones can start. Number of firms per need is not fixed.
- Share routes: founder sells to raise expansion money; part-wages in shares; open market. Founder chooses by temperament.
- Unhappy shareholders sell; price falls; cheap firms get bought.

## Bank (his addition)
- Lends to firms and individuals. Rules to set: collateral required, loan size vs income or assets, interest.
- Note: in this world individuals own no assets; only shares and income can secure a loan. Firms own the houses and ovens, so credit flows to firms more easily than to people.
- Bank is backstopped by a federal government outside the town. It NEVER fails. It is the channel that brings money into the town (credit).
- Open: who gets the interest (local shareholders, or it leaves town to the federal level); whether government taxes anything.

## Broker (his addition)
- Share market with price discovery; agents and firms buy and sell through it.

## Dynamics to watch
- Growth phase (arrivals bring outside money) vs closed phase after population reaches 1,000. Keep running well past closure.
- Log at failure: time to failure, share concentration, which need's price broke first.
- Expect drift toward monopoly and toward ownership concentration via distress selling; the model should show it rather than assume it.

## Open
- Collateral rules; interest; whether the bank can fail.
- Money supply: bank credit creates money inside the loop.
- Build approach: coded-rule ABM (Python, Mesa) first; LLM agents later for watching individual lives.

## Decisions (later in the chat)
- Government: guarantor of the bank only. No tax, no welfare. Interest leaves town (federal bank, no local shareholders) unless he says otherwise.
- No one leaves town. Destitute agents stay, count toward the 90%, and the model records how many are destitute.

## Recording and visualisation (his requirement, 12/11)
- Purpose: a white paper or thesis on the outcomes of both worlds. Claude writes it; he will not rewrite it (his words). So the record has to carry the argument: every figure in the paper traceable to a run.
- Record first; pictures are built on the record, never on the live model. Any run can then be replayed, slowed, filmed or re-examined later.
- Three layers of record:
  1. Event log: every hire, sacking, resignation, wage change, price change, subscription started or cancelled, missed payment, loan, repayment, default, share issue, share trade, dividend, firm founded, firm failed. Each with the tick, who, what, the amount, and for agent decisions the agent's security and horizon at that moment (the "why").
  2. Snapshot each tick: every agent (cash, wage, employer, shares, debt, subscriptions, security, happy or not, destitute or not) and every firm (price, customers, staff, revenue, profit, target return, share register, debt).
  3. Town series each tick: share unhappy, share destitute, ownership concentration (Gini and top-10% share), price index against wage index, firms per need, bank lending, interest leaving town, money in town.
- Run record: settings file, random seed, code version, outcome. Same settings plus same seed must reproduce the run exactly.
- Many runs per setting (one run is one town's luck). Results reported as distributions. Sweep the dials to see which ones matter.
- Same measures in both worlds, so the comparison is like for like. Design the record world-neutral now, even though world two is parked.
- Three views, all reading the record: (a) dashboard of the town series; (b) town view, agents as dots coloured by security, firms sized by staff, replayable; (c) single-life view, one agent from arrival onward.
- Volume, if the tick is a week: 1,000 agents x 52 weeks x 50 years = 2.6 million agent rows a run. Storage is not a constraint. Format not decided (Parquet or DuckDB per run is the idea).
- Paper states plainly how it was produced (model and text by AI under his direction), as his letters do.

## Predictions on record BEFORE any run (so the model cannot be tuned toward a belief)
- His (12/11): what companies are doing is not sustainable and, continued, would eventually collapse in on itself. Open source is the opposite and more constructive for society, but if too open it may collapse as well.
- Claude's (12/11): neither world collapses by itself. The WEF world's outcome turns on who holds the shares; expect drift toward monopoly and concentration through distress selling. Expect it to look healthy while arrivals bring money in and to show its character after the population reaches 1,000.
- Failure definition, fixed 12/11: 90% of agents unhappy.

## Visualisation decision (12/11)
- His picture: the town itself with people moving through it. The town view is the primary view; dashboard and single-life view sit beside it. Still a replay of the record.
- Consequence: the model needs places. Homes (rented), workplaces, shops or service points per firm, bank, broker. Agents need a daily routine so there is movement to watch.
- Open: is distance real (commute cost, shop choice by nearness) or is the map only a picture of the record?
- DECIDED 12/11: distance is real. Travel costs time and money; agents weigh nearness when choosing firms and jobs; location of rentals and shop fronts matters.
- Consequences: the housing firm owns location as well as shelter (rent by nearness to work); transport becomes a need, and in the WEF world a subscription (a likely fifth firm); local monopolies can form by distance even with several firms per need.
- Open: how agents travel (walk only, or a transport service); town layout (grid, size); who decides where new buildings go.
- DECIDED 12/11: everyone walks until a transport firm exists. Transport is not a founding firm; it must be founded by an arrival with capital.
- Consequences: the early town is compact (walking range limits who can work where and shop where); the first transport firm widens every agent's reach at once and is a natural monopoly; its price sets how far the town can spread.
- Open: town layout and size; who decides where new buildings go; walking range per day.
- DECIDED 12/11: land is free while empty spots remain (a firm picks any empty spot). Once every spot is filled, buildings and land change hands only by sale or lease.
- Consequences: a land rush early (first firms take the central spots for nothing); a fixed map means land becomes scarce and gains a price at the moment the town fills; late founders must buy or lease from incumbents; land is a firm asset the bank lends against.
- Note for the paper: individuals own nothing, so only firms can hold land. Confirm with him.
- Open: map size (number of spots) relative to 1,000 agents; whether a failed firm's land goes to the bank or back to empty.

## Town services (12/11): three, separate from the firms
- Bank (lending, federal backstop, never fails), share broker (share market), housing agent (handles sale and lease of land and buildings once the map is full; matches tenants to rentals).
- The housing agent is a marketplace, distinct from the housing FIRM (a founder-owned landlord that owns rentals).
- Open: do broker and housing agent charge fees, and where do the fees go; are they permanent like the bank; failed firm's land via bank and housing agent; who can hold land (assumed firms only).
- DECIDED 12/11: broker and housing agent services are free (no fees). Every new arrival must rent a home through the housing agent. Rent and house price depend on location: nearness to work, cafes and shops, and popularity of the area.
- He also said agents can BUY a house through the housing agent "if they want to own a property". CONFLICT with the WEF premise (own nothing). Put to him; unresolved.
- Unresolved: who receives the rent (the housing firm as landlord, the housing agent itself, or any firm that owns homes).
- DECIDED 12/11: the housing agent is the shop front of the housing FIRM (not a separate service). Agents go there to pay rent or find a home. The housing firm receives all rent. Agents can buy its shares. Its costs: ongoing maintenance of every rented home (always a cost) and construction of new homes as population grows.
- So town services are two (bank, broker); the housing agent is the housing firm's front office.
- Maintenance and construction are work: jobs at the housing firm or at a building firm someone founds.
- Home buying by agents: Claude's proposed default is NO (rent only; the way to own housing in this world is shares in the housing firm). Awaiting his yes or no.
- DECIDED 12/11: homes decay; maintenance cost rises with age. Rent only, no home purchases by agents (Claude's default, he did not object; confirm if it comes up).
- Consequences: the housing firm's costs rise over time even with a stable population; it must choose between raising rent, skimping on upkeep (worse homes, lower happiness for tenants), or demolishing and rebuilding. Condition of the home becomes an input to the tenant's security and happiness.
- Open: does the same decay apply to appliances (ovens, fridges) rented from the appliance firm; can a firm let homes run down.
- DECIDED 12/11: appliances decay too; upkeep cost rises with age. Condition of home and appliances feeds tenant happiness.
- General rule: every rented physical thing has age, condition, rising upkeep, and a replace-or-neglect decision made by the owning firm under shareholder pressure.
- Open: who makes replacement appliances and building materials (made in town by a firm, or imported, which sends money out of town).
- DECIDED 12/11: make or import is the firm's choice, whichever is more cost effective for its shareholders.
- Consequences: an outside world with an import price for goods and materials (a dial we set). Local makers exist only while they undercut it. If local wages rise, firms import, local jobs go and money leaves town; if wages fall, production comes back. Imports are a second drain beside bank interest.
- Open: is the import price fixed or does it move; can the town export anything (the only way money comes back besides arrivals and loans).
- DECIDED 12/11: firms can export when it is profitable for shareholders.
- Consequences: the town has a trade balance (exports in; imports and bank interest out). Outside prices for goods bought and sold are dials we set. Export income lands with exporting firms and their shareholders first, then wages.
- Money flows now complete: IN = arrivals' capital, bank loans, exports. OUT = loan repayments plus interest, imports. Record all five every tick.
- Open: outside price list (fixed or moving); what the town is good at making.

## Dashboard requirement (12/11): three coverages
- Every measure shown three ways: everyone, the owner class, the working class. He wants the town as a whole and the difference between the classes.
- Class needs a definition, because agents can be both (a worker holding shares). Claude's proposal: class by main source of income in the period. Owner = more than half of income from dividends and firm profits. Worker = more than half from wages. A third group, no income, shown separately so it does not hide inside the workers. Awaiting his call.
- Class is recalculated every tick; movements between classes are logged as events (who rose, who fell, and what triggered it).
- Town view: colour or mark agents by class as an option.
- DECIDED 12/11 (his definition, replaces Claude's income-based proposal): class is by ROLE. Owner class = founders, owners of a company, the CEO and the executive class; shareholding does not make someone an owner. Working class = anyone employed by a company and drawing a wage, whether or not they hold shares.
- Consequences: firms need a hierarchy (founder, CEO, executives, staff) and executive pay distinct from wages; promotion into and removal from the executive class are logged events; share ownership is reported as a separate measure inside each class.
- Open: agents with no job (unemployed, destitute) and agents living only on dividends with no role: which group. Proposed: "out of work" as a third coverage; dividend-only agents shown within it or as a fourth.
- DECIDED 12/11: dividend-only agents are owner class. Out of work shown as a third group.

## Build plan and estimate given to him (12/11, rough, nothing built yet)
1. Core economy without the map: agents, firms, jobs, pricing rule, shares, bank, broker, decay, trade, full recording, class dashboard. About one working day.
2. Space: map, real distance, walking, land rush, location rents, transport firm. About one more day.
3. Town viewer (replay of the record, people moving). One to two days.
4. Checking and tuning so behaviour is sane. The longest and least predictable stage: a week or more of back and forth.
5. Batch runs, then the paper. World two after that reuses most of the machinery.
- Undecided rules Claude will set as adjustable dials unless he objects: tick = one week; wages by firms bidding for scarce workers; map size; walking range; arrival rate and starting money; outside price list; the happiness cut-off; executive pay.
- Needed from him: where the project lives (proposed ~/Workspace/wef-world, its own git repo), and a go-ahead for stage 1.

## STAGE 1 BUILT (12/11/2026)
- Lives at `~/Workspace/wef-world` (its own git repo, branch feature/stage-1-economy, nothing committed). A copy of this note is in its `docs/`. From here on the rules of record are in that repo: `docs/superpowers/specs/2026-11-12-wef-world-stage1-design.md`, each marked (J) his or (C) Claude's.
- What exists: the weekly economy, the SQLite record of every run, the three-coverage dashboard, 172 tests (money conserved every week, shares conserved, nobody leaves, same seed same record).
- Decisions that surfaced while building, put to him 12/11: price rule (ratchet as recorded vs a firm backing off a rise that lost money); whether the bank can force a share sale; the starting stock of 120 homes and 120 appliance sets; exports as the thing that lets hiring pull people in.
- First runs on the final code (untuned): all nine failed inside 60 years, between year 17 and year 48. See the repo README for the table and the reasons they are not findings yet.
- An independent review found no accounting leak and no broken (J) rule; its ten findings were fixed with tests. 200 tests pass.
- Open calls for him: price can fall or not; bank forcing a share sale; dropped luxuries missed for ever or not; commit; stage 4 before stage 2.


## STAGE 2 BUILT (12/11/2026, same day)
- He said "commit this and start on stage two". Stage 1 committed (`a2289f9`). Stage 2 is on `feature/stage-2-map`, finished and reviewed, not committed.
- What exists now: a 13 by 13 map of spots; homes, firms' premises, the bank and the broker each on a spot; walking reach of six blocks; time on the road weighed in every choice of home, job and shop; rent by location; land free until the map fills, then sold or leased; transport as a subscription with a fixed crew, founded when enough people are turned away by distance. `map_width=0` switches it off and gives the stage 1 economy exactly.
- First six map runs, untuned: all failed between year 16.0 and 17.2. See the repo README for the table and why they are not findings.
- The largest thing the map changed, not yet understood: the staff wage fell 12 to 17% after the town filled.
- One rule in my first draft was never built and is struck: shops opening where people are unserved. Every firm opens as near the middle as it can.
- Thirteen decisions are open and listed in the repo README. He asked for the list on 12/11 evening.

## STAGE 3 BUILT (12/11/2026, same day, late)
- His words: "OK, commit the code, Do the housekeeping Then start on stage three." Stage 2 committed and merged into `develop`; `main` made at the stage 1 commit; old faulty runs deleted. Stage 3 is on `feature/stage-3-town-view`, not committed at that point (committed 13/11; see the last line of this section).
- What it is: `town.html` in each run folder, built only from `run.sqlite` by `python -m wefworld town <run folder>` and at the end of every run on a map. One file, opens offline. Sizes as measured after the review are further down this section.
- What it shows: the map (homes, premises sized by staff, bank, broker, empty land); every person as a dot; the four coverages (everyone, owner class, working class, out of work) with head counts and share unhappy at the week shown; people with no home, riders, jobless rate, staff wage, basket; a time line of the share unhappy with the 90% line and four marked moments; one person's life (cash, pay, debt, shares, wellbeing by quarter, and what happened to them in order).
- Recorded and shown as recorded: where each person lives, works and shops, class, wellbeing, ride or walk, each week; what stands on each spot, each quarter.
- Drawn, not recorded (my calls, said on the page): the journeys inside a week (the model has no days, so each week is drawn as one round: home, work, food shop, entertainment, home); where a dot sits in a block; the strip under the map for people with no home (the model gives them no place; this does not prejudge his open decision on whether a person with no home is limited by distance).
- Other calls of mine: people coloured by wellbeing by default (the design chat said security; wellbeing is what the 90% rule reads), class as the other choice; four speeds; the single-life view lives inside the town view.
- No change to the model or the record, so every map run already made can be watched.
- Design, plan and ledger: `docs/superpowers/specs/2026-11-12-wef-world-stage3-design.md`, `docs/superpowers/plans/2026-11-12-wef-world-stage3.md`, `docs/build-ledger-stage3-2026-11-12.md` in the wef-world repo.
- Reviewed the same night by a fresh agent. The data matched the record at every week. The page itself had 1 critical, 9 important and 15 minor faults; all fixed with tests except four minor ones (in the ledger). The critical one: the numbers beside a person's life lines were quarter-end values shown as if they were the week on screen. Now each number is the line's latest quarterly point and the page says which week that is.
- Also changed by the review: a rent is no longer quoted for a tenancy (the record holds the landlord's average, not the tenant's rent); "moved to a cheaper home" now says what the model compares (rent, fares and time on the road); a busy firm can be pointed at by its name; a Security line was added to the life view; things that repeat within a quarter are told once with a count.
- 484 tests. A page is about 3.5 MB for a town that fails around year 16, about 19 MB for a full 60 years.
- Three calls of mine are in the wef-world README as open decisions 14 to 16: wellbeing, not security, colours the dots; people with no home are drawn in a strip under the map; the model has no days, so the weekly round is drawn by the page.
- Committed Fri 13/11/2026 05:39 on his approval (the commit button, under my question "Commit stage 3?"): `6f5f8f7` on `feature/stage-3-town-view`, 13 files, 484 tests passing on the committed tree. Merged into `develop` at 05:47 the same morning on his word ("Yes, merge"): merge commit `f6cfc52`, 484 tests passing on `develop`. `main` still holds stage 1 only. The repo has no remote.

## STAGE 4 STARTED (13/11/2026)
- His words: "Start stage 4". The question put to him was "Start stage 4, tracing why wages fell on the map?". Branch `feature/stage-4-checking`. Nothing in the model changed; nothing committed.
- The wage fall is traced. Full account: `docs/stage4-wage-trace-2026-11-13.md` in the wef-world repo.
- What it found: the map does not push the wage down. Without the map, landlords go on building after the town is full (1,099 to 2,283 homes in the nine recorded runs, up to 1,749 empty at once), and that building keeps firms short of staff, which is what raises wages. The 13 by 13 map has room for about 1,150 homes, so it cannot happen there.
- How it was tested: seeds 1 to 3 re-run with the building stopped from the week the no-map town fills. The wage then fell 12.2%, 10.3% and 5.0% instead of rising 1.8%, 13.0% and 1.4%.
- Two of my own explanations for why the map has no boom were tested and were wrong (rents by block; the need for a ride). The third test showed land is the limit.
- Not explained: the last 2 to 7 points; why extras have half the customers on the map. Three seeds.
- Consequence for the paper: runs without the map are not a fair yardstick for what the map does.
- New decision 17, his to make: should a landlord build while homes elsewhere in town stand empty? Put to him 13/11 beside a chart of homes and wages.
- **Decision 17 answered 13/11 about 08:40 (J): a fault in the model, not the world he means.** His words: "Most likely your fault I don't remember actually saying 2,000 houses. Why do you ask that question?" He never said 2,000 homes. Nobody did: no rule says how many homes a town has, and the number came out of my starting values (a landlord keeps 6% of its own homes spare and does not look at empty homes elsewhere) meeting his rule that a price only rises. My question ("Is 2,000 homes for 1,000 people the world you mean, or a fault in my model?") read as if he had said it. Recorded in the wef-world README and `docs/stage4-wage-trace-2026-11-13.md`. **The rule that replaces it is not designed and not built. The model still builds this way.**
- **His first words about the town view, 13/11:** "what I'm trying to look at now is how do the agents actually get paid like I'm not seeing a price on how much money the agents actually have Is that in step five?" He was watching seed 1 on the map from its first weeks, at Slow.
- How people are paid, checked in the code on 13/11 (`corporate.py`: `payroll`, `_pay_wages`, `pay_dividends`, `grant_shares`; `town.py`: `step`): wages are step 4 of the 11 steps of a week; step 5 is people planning their bills. Staff get the firm's wage ($1,000 a week at the start). An executive gets 2.5 times it. A chief executive gets 1.5 times it plus 0.05 for each member of staff, up to 8 times, and goes short if the firm has not the cash. At about three firms in ten, 5% of the staff wage is held back and paid in the firm's shares each quarter. Dividends are paid each quarter. A firm that cannot pay its wages borrows, then calls on its largest shareholder, then fails. Nobody out of work is paid anything: the stage 1 design says "no tax, no welfare". A newcomer brings their own money, $3,000 for the middle one.
- Where the money shows, checked in the page on 13/11: the town view shows one person's cash, weekly pay, debt and shares under "Follow one person" (click a dot, or "Someone at random"). At his pane width (634 px) that panel starts about 1,880 px down the page, more than a screen under the map, which ends at 800 px, so a click on a dot shows nothing where he is looking. The week panel beside the map shows the staff wage and the basket but no money held. The dashboard has "Cash held" and "Weekly income" by class. **Offered 13/11, not built: put a person's money beside the map.**
- **13/11 about 09:00, his answer to the offer:** "No, put it on their card when you roll over them under the class." **Built 13/11 (not committed).** A person's card in the town view now gives, under their class, their cash and their pay for the week on screen. Cash is the record's end-of-week figure, after pay and bills. Pay is what the job pays a week; dividends are not in it; someone with none reads "No pay". The card keeps up as the weeks go by. To do it the page now carries every person's cash for every recorded week, so a page is about 7 MB (was 3.3 to 3.8), and 31.7 MB for a town run the full 60 years (was about 19; it still opens in a third of a second and plays). The model is unchanged: seed 1 on the map re-run gives record fingerprint `8a9ccdf346c84b2d`, as on 12/11. 512 tests pass (14 new, written first). All nine town pages in `runs/` rebuilt. Checked against the record in the browser (43 cards, weeks 300 and 871) and across the whole seed 1 page (663,870 person-weeks, none differ). My calls: this week's numbers, not the last quarter's; the "Now" line beside a followed person left as it was; debt and shares not on the card.
- **Committed 13/11 09:30 on his word** ("Ah yes, commit the changes to the code"): `9cbc04f` "Stage 4: trace why the wage falls on the map" and `0e9c858` "Town view: a person's cash and pay on their card", both on `feature/stage-4-checking`. 498 tests pass on the first alone, 512 on the second. Not merged into `develop`.
- **His housing question, 13/11 09:30:** "are we keeping track of what's actually happening with buildings as they are required? So keeping track of housing builds, how many houses are left, how many are vacant at any given time, that sort of thing. Or is that part of version stage five? Just answer yes or no for the moment". **Answered yes: recorded now, not stage 5.** What the record keeps (checked in the seed 1 map run): the town's homes standing and homes empty every week; each landlord's homes, empty homes and homes being built every week; everything built or rebuilt, homes pulled down and every refusal for want of land as events; every home's age, condition and tenant once a quarter. The dashboard charts homes standing and empty. He asked for no more than yes or no for now.
- Seen while checking, not looked into: at week 300 two working people on $1,000 a week held $0 and were spending about $1,160 a week on credit (persons 304 and 365, debts $7,912 and $3,681); at the last week a person with no home, no job and $46 was still recorded as paying for a ride (person 78). Both are the record, and both are things to look at in stage 4.
- Seed 1 on the map, the middle person's cash, from the record: working class $7,777 (year 1), $9,803 (year 7), $447 (the end, year 16.8); owner class $96,897, $91,983, $189,086; out of work at the end $51 (86 people).
- Kept for re-running: `experiments/wage_trace.py` (not part of the model) and its tests; three test runs in `runs/20261113-stage4-*`.

## STAGE 5 STARTED (13/11/2026): MANY TOWNS
- His words, 13/11 about 09:40: "OK, commit this. And move on to stage 5." The notes in this folder were committed (`298b2d1`).
- Stage 5 by the plan of 12/11 (above): "Batch runs, then the paper. World two after that reuses most of the machinery." I started with the batch runs only.
- Stage 4 was set aside by him, not finished: one check done (the wage on the map), decision 17's fault still in the model, sixteen decisions open, nothing tuned. Said to him once. The paper is not started on that footing (my call, his to overrule).
- Built on branch `feature/stage-5-batch-runs` (cut from `feature/stage-4-checking`, `0e9c858`; stage 4 is still not merged into `develop`). Not committed.
- What it does: `python -m wefworld batch NAME --seeds 1-30 [--set DIAL=VALUE] [--vary DIAL=A,B,C] [--jobs N]`. Every setting on every seed, several towns at a time, can be stopped and started. Each town is an ordinary run with the same record fingerprint as that seed run alone. A batch town records people once a quarter (checked: the identical town, 37 s and 60 MB against about 180 MB). One table (`batch.sqlite`) built only from the towns' records; one page (`batch.html`) built only from the table.
- Design `docs/superpowers/specs/2026-11-13-wef-world-stage5-design.md`, plan `docs/superpowers/plans/2026-11-13-wef-world-stage5.md`, ledger `docs/build-ledger-stage5-2026-11-13.md`.
- **The first batch, `batches/20261113-as-written`: the model as written on the 13 by 13 map, seeds 1 to 100. ALL 100 TOWNS FAILED.** Middle town year 16.50; middle half 15.50 to 17.25; first 13.25 (week 689); last 20.96 (week 1,090); given 60 years. 93 of 100 failed in the last week of a quarter. Every town filled (middle year 7.2); land ran out in 82. Middle town of those still standing at the end of the year: unhappy 0.2% (year 5), 12.8% (8), 19.2% (10), 32.2% (12), 57.5% (14, 98 towns), 70.6% (15, 86), 80.4% (16, 58), 85.1% (17, 28). Staff wage $1,000 (5), $1,038 (8), $989 (10), $939 (12), $901 (14), $881 (15), $864 (16), $841 (17). Basket $894, $959, $1,042, $1,134, $1,213, $1,251, $1,286, $1,381. Basket against wage 89%, 92%, 105%, 120%, 134%, 142%, 149%, 166%. Middle working person's cash $9,988, $9,262, $10,912, $11,857, $8,470, $4,083, $865, $624. In the last week: top tenth held 96.7% of shares; unhappy 6% of owners, 94.7% of workers, all of the out of work. Price risen most: appliances 85 towns, food 10, entertainment 5, housing 0.
- **CORRECTION, 13/11 about 11:00.** The year-by-year numbers first written here (at 10:40) were wrong from year 15 on: a year's figure counted towns that failed in that year's very last week (67 towns at year 16 where 58 were still standing; unhappy 81.9% where it is 80.4%; working cash $748 where it is $865). A fresh reviewer found it. The page, the README, the brief and this note were corrected the same morning. The failure years were never affected.
- The reviewer (108 tool calls, read-only) found the arithmetic right and the machinery sound, one critical fault (above), six important ones (Ctrl-C did not stop a batch; "the middle town" was the middle of the towns that failed only; ties for "price risen most" went to food; dial values came from today's code, not the records; run-on towns; the tests missed 18 of its 29 planted faults) and about twenty small ones. All fixed with tests first, except three small ones deferred in the ledger. 35 planted faults are now caught, the unchanged copy passes, 660 tests pass.
- **Against the two predictions: this runs with his and against mine.** Mine said it would not collapse by itself; 100 of 100 collapsed. Said so plainly in the README. Why it is still not a finding: untuned; a price never falls under the rule as written (decision 1) while wages are cut, so the basket must cross any line in time; decision 17's fault; jobs for nine in ten; rich and poor buy the same.
- Next: batches that vary one dial at a time (price_rule, export_price_drop, habit_weeks, transport_can_close, map size), on his word.

## DECISIONS RULED 16/11/2026: ALL SIXTEEN, FOUR AT A TIME
He asked to go through them in batches of four and answer them all. Full wording in the wef-world README, "Decisions" (branch `feature/decisions-2026-11-16`, not committed). (J) on each.
- Kept as built: 1 price never falls (his words: "I'm inclined to believe that it won't go down based on current rules in a real economic environment. Even though it should. as this would affect making the shareholders happy rule."); 3 bank cannot force a share sale; 4 everyone rents; 6 loan called in when the job goes; 7 jobs for about nine in ten; 9 map 13 by 13; 11 no home does not limit distance; 15 homeless drawn in the strip; 16 weeks, no days.
- **Changes the model, not built:** 2 a lost luxury fades after a year (`habit_weeks=52`); 5 start with 60 homes ("Let's just make it 60 homes"; appliance sets left at 120, my reading); 8 the well-off spend more (not designed: mine to propose); 10 transport with riders always sold on (`transport_can_close=false`); 12 founders open near the unserved (local patches); 13 fare before rent for someone who needs the ride for work; 14 town view: wellbeing colour, class as shape ("Can we keep the color of the well-being. but change shapes for the classes.").
- Still open: the rule replacing decision 17 (mine to propose).

## SECOND BATCH 16/11/2026: THE SAME 100 TOWNS UNDER HIS RULINGS
Commit `6ffd717`, `batches/20261116-rulings`. All 100 failed, about 2.4 years later than the 13/11 batch: middle town year 18.75 (was 16.50), middle half 17.75 to 20.00, first 15.00, last 24.75. 95 of 100 seeds later, 4 earlier, 1 the same. Same path, slower. Money in town still rises throughout; workers' cash still runs out. Checked against the towns' own records. Full table in the wef-world README, "The second batch".

## WHERE THE MONEY GOES, 16/11/2026 (his "Yes, trace it")
It sits with the founders who own their firms outright: export money comes in (the full quota, $18.8M a year once full), firms pay it out as dividends, the owners spend a quarter to two fifths and keep the rest; nothing gives saved money a way back to the workers. 100 towns at year 15 under the rulings: owners 63% of the money, the five richest 54%, workers 11%. Accounts right. Decision 18 open: what do the rich do with money they do not spend? Full note in wef-world `docs/stage4-money-trace-2026-11-16.md`.
- **Decision 18 (J), 16/11:** it sits, as built. His words: "What the rich usually do with their money is they tie it up in shares or they put them in blind trusts or charity trusts and never use the money.So I think we're fine with that."

## WHERE THE MODEL LIVES NOW, 18/11/2026
The folder `~/Workspace/wef-world` named in this note is now `~/Workspace/two-towns` (my working name; his to change). It holds two worlds, a folder each, over one shared `engine/` (the old `wefworld/` code folder): the WEF world is run from `wef/`, the RTR world from `rtr/`. Nothing in the WEF world's rules changed in the move: the old-rules seed 74 town of the 13/11 batch still gives `08251209eb136522`, 180,377 events. The WEF batches named here are now under `wef/batches/`. Commit `c64ea48` on `feature/two-worlds-layout`; merged into develop as `3d10127` on 18/11 (his "Yes, merge").

## WHERE THE MODEL LIVES NOW, 19/11/2026
Since 19 November 2026 the model is published as the repository `WEF-versus-RTR-models` (his name for it). The folder names above are those of the machine it was built on.
