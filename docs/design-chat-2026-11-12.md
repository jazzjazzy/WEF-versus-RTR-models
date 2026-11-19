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
