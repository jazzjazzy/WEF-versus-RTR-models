# WEF World, stage 1 design: the economy without the map

Date: 12 November 2026. Decisions marked **(J)** are Jason's, made in conversation on 12/11 and recorded in `docs/design-chat-2026-11-12.md`. Choices marked **(C)** are Claude's calls as the builder. Every (C) is an adjustable dial or a stated simplification, never something Jason agreed to in detail. He approved stage 1 on the understanding that undecided rules start as dials with stated values.

## 1. Intent and why

Jason's question: if companies keep moving toward "you will own nothing, everything is rented or subscribed", does that world hold together, or does it collapse in on itself, and why? He believes it is not sustainable. He wants the question answered by a model instead of by belief: a town of agents who live ordinary working lives in the world of the 2016 World Economic Forum essay, later compared with a second world where things are owned and open source.

The end product is a white paper or thesis on the outcomes of both worlds, written by Claude from the recorded data. So the record must carry the argument: every figure traceable to a run, every run reproducible.

Stage 1 is the economy with no map: agents, firms, jobs, pricing, shares, bank, broker, decay, trade, full recording, and a dashboard that shows every measure for everyone, for the owner class and for the working class.

## 2. Goals, non-goals, anti-goals

Goals
- A town that runs week by week under the rules below and can be re-run exactly from its settings and seed.
- A complete record of each run: events, weekly snapshots of every agent and firm, town series, run record.
- A dashboard built only from the record, with three coverages plus the out of work.
- Tests that prove the accounting: money is conserved, shares are conserved, nobody leaves.

Non-goals for stage 1
- No map, distance, walking, land, location rents or transport (stage 2).
- No town view with people moving (stage 3). No single-life view yet.
- No tuning toward a sensible or a dramatic outcome (stage 4). No batch runs or sweeps (stage 5).
- No second world yet. The record is designed so the second world can use the same measures.

Anti-goals (these would make it a failure even if it runs)
- A model tuned until it says what either of us already believes. Both predictions are in `docs/predictions.md`, dated before the first run.
- Numbers in a paper that cannot be traced to a run and reproduced.
- Hidden rules. Every rule that shapes the outcome is written here and every dial is in one settings file.
- Agents quietly leaving town, or money appearing or vanishing outside the five named flows.

## 3. Constraints

- Python 3.12, standard library only. No third-party packages (numpy is not installed; none is needed). (C)
- Storage is one SQLite file per run. (C) Earlier idea was Parquet or DuckDB; SQLite needs nothing installed and the later viewers can read it directly.
- Money is whole cents (integers), so conservation can be tested exactly. (C)
- One random generator per run, seeded. Same settings plus same seed must give the same run, bit for bit.
- Nothing is committed to git without Jason's approval.

## 4. What Jason decided (as decided)

Agents
- Arrive two ways: hired by an existing firm, or bringing money to found a firm. Each agent starts with a sum of money.
- Live a normal working life: employable, willing or forced to change jobs for affordability.
- Need housing, food, appliances and entertainment. All rented or subscribed. They own nothing except cash and shares. Rent only, no home purchases (Claude's default, he did not object).
- Some work for the subscription firms. Some hold shares in them.
- Each has an emotional state that decides how they handle situations, for example on losing a job: sell the shares, or keep them and live on dividends.
- No one leaves town. The destitute stay and count.

Firms
- Day one: four founding companies (housing, food, appliances, entertainment), each owned by its founder. The town starts with no other agents.
- Later founders may compete or invent a fifth need. No limit.
- Prices move for the shareholders: the price rises whenever profit falls short of what shareholders expect. Each shareholder has their own expectation of growing returns, randomised. The firm's target is the holding-weighted average.
- Firms can fail and new ones can start. The number of firms per need is not fixed.
- Shares reach others three ways: the founder sells to raise expansion money, part of wages paid in shares, an open market. The founder chooses by temperament. Unhappy shareholders sell.
- Homes and appliances decay and cost more to keep as they age. The owning firm decides whether to repair, replace or neglect. Condition feeds the renter's happiness.
- The housing agent is the housing firm's shop front. The housing firm receives the rent. Its costs are upkeep and building new homes as the population grows.
- Make or import: whichever is more cost effective for shareholders. Firms export when it is profitable for shareholders.
- Firms have a hierarchy: founder, CEO, executives, staff.

Town services and the outside
- A bank that lends to firms and individuals. It is backstopped by a federal government outside the town and never fails. It is the channel that brings money in. Government does nothing else: no tax, no welfare.
- A share broker. Its service is free.
- Population grows by hiring and founding until it reaches 1,000. Then arrivals stop and the run continues.
  **Changed 16/11/2026 (J):** no cap on people (`population_cap = 0`); a newcomer still needs a free home, so the homes that can be built are the limit. `configs/before-16-november.json` gives the cap of 1,000.

Measures
- Failure: 90% of all agents unhappy.
- Class is by role. Owner class: founders, owners of a company, the CEO, the executives, and agents living on dividends alone. Working class: anyone employed by a company and drawing a wage, with or without shares. Out of work: a third group.
- Dashboard: everything shown for everyone, the owner class and the working class.
- Record as much as possible. Recording comes first; every view reads the record.

## 5. The rules as built in stage 1

### 5.1 Time and money
- One step is one week. 52 weeks to a year, 13 to a quarter. (C)
- All money is integer cents. Every movement of money goes through one ledger function that names its kind.
- Money enters the town three ways: arrivals' capital, bank loans, exports. It leaves two ways: loan repayments (principal, interest and recoveries) and imports. (J) Nothing else crosses the boundary. Loans the bank writes off are not a flow: that money simply stays in town.

### 5.2 The outside world (all C, all dials)
- Outside wage: a worker moves to town only for a job paying at least this, and only if a home is vacant. (J: every arrival must rent a home.)
- Each good has a fixed import price and a lower fixed export price, and the outside buys only so much of each good per week (a quota shared between the firms that make it).
- Starting stock. The housing firm and the appliance firm begin with homes and appliance sets already standing (120 each by default), so the founders and the first workers have somewhere to live. This stock is wealth the town starts with; it is not one of the five money flows. It is written into the run record, its founder holds shares for it at $10 each, and the bank will lend against it from the first week.
  **Changed 16/11/2026 (J):** 60 homes, appliance sets still 120 (decision 5). `configs/before-16-november.json` gives 120.
- Why exports matter. It takes well under one worker to supply one resident's four needs. A town that only served itself would stop hiring at a few dozen people. Outside buyers are what make "hiring pulls people in" work, exactly as in a real town. The default quota lets exports employ about 30% of a full town at the starting wage. Invented needs are services used in town and have no export quota.
- A calibration that matters. Labour per resident (about 0.57 of a worker), the export share (0.30) and executives together set how many jobs exist when the town is full, near 90 to 95% of residents. These are the builder's starting values, not a finding, and they are first in line for testing in stage 5.

### 5.3 Agents
Fixed at birth, randomised (C for the distributions):
- loss aversion (median about 2, the commonly cited figure from Kahneman and Tversky; to be checked against the source for the paper),
- natural time horizon in weeks,
- expected growth in returns as a shareholder (J: randomised per shareholder),
- skill, appetite for risk, taste.

Moving state:
- Security, between 0 and 1. Each week it moves toward a target built from income against the cost of the four base needs, weeks of savings, having a job or living on dividends, and debt. It falls fast and recovers slowly; the fall is scaled by loss aversion. Shocks hit at once: job loss, a price rise, a missed payment, eviction, a called loan, a default.
- Effective horizon = natural horizon, shortened as security falls (scarcity shortens the horizon; Mullainathan and Shafir, to be checked for the paper). At zero security a tenth of the natural horizon is left.

How the horizon decides (C):
- Calm agents (effective horizon of half a year or more) cut discretionary subscriptions when income will not cover them, hold their shares, and borrow or sell only for food and housing.
- Stressed or impatient agents keep consuming, run down cash, sell shares at whatever the market gives, and borrow to their limit.
- A share is worth more to an agent with a long horizon (expected dividends over the horizon, plus half of book value). So shares drift from the stressed to the calm.
- Out of work, a secure agent holds out for something near the old wage; the reservation wage falls with insecurity and with each week unemployed.
- Savings target: between 4 and 52 weeks of their subscriptions, longer for longer horizons. Cash above it is offered for shares, or for a new firm.

### 5.4 Needs and subscriptions
- Four base needs. Food and housing are essential. Payment order each week: food, housing, bank loan, appliances, entertainment, then invented needs.
- An agent subscribes to one firm per need and switches to a cheaper one now and then (5% friction). For homes and appliances the firm must have a free unit.
- A missed payment is logged. Food and entertainment stop that week. A home or an appliance set is kept through three missed payments in a row; on the fourth the agent is evicted or the set is taken back. A missed payment is forgiven, not owed later. An evicted agent stays in town homeless and re-rents as soon as they can pay.
- Invented needs are discretionary. An agent takes one up when they have the spare income or a large cushion, and only if it suits their taste. Once an agent has had one, going without it counts against them for as long as someone still sells it (`habit_weeks = 0`, the default). With `habit_weeks` set, they stop missing it that many weeks after they last had it. (C; the reviewer showed this rule moves the failure date, so it is one of Jason's open calls.)
  **Changed 16/11/2026 (J):** a lost luxury stops being missed a year after it was last held, `habit_weeks = 52` (decision 2).
- A service firm signs up only about as many customers as its staff can serve (a tenth more, and five to get a new firm started). Someone turned away is counted, and the firm staffs up for them the next week. A customer the firm could not serve in a week moves to any other seller with room. (C)

### 5.5 Firms: work, goods, decay
- Each firm sells one need at one weekly price and pays one staff wage. Executives (one per 25 staff) and the CEO are overhead and are paid multiples of the staff wage.
- Work needed each week: service per customer; upkeep per unit, rising with the unit's age; building; making goods; making goods for export. Staff are assigned in that order when short.
- Every need uses a tradable good: food goods, building materials, appliance parts, content. Each quarter the firm compares the cost of making a unit in town (wage times labour per unit) with the import price and takes the cheaper. (J) If it is short of staff it imports the gap.
- If making a unit costs less than the export price, the firm makes extra and sells it outside, up to its share of the quota. (J)
- Homes and appliance sets are units with an age and a condition. Upkeep needed grows with age. (J) The best condition a unit can reach falls with age. Condition climbs when upkeep is done in full and falls when it is skimped.
- Upkeep level is the firm's policy: it is cut in a quarter where profit falls short, faster when the shareholders' horizons are short, and restored slowly otherwise. (C)
- Replacement: a unit whose best achievable condition has fallen below a threshold is rebuilt, unless the firm is in a shortfall quarter or cannot fund it. So neglect is what a pressed firm does. (J in spirit, C in detail)
- The housing firm builds ahead: it keeps a small buffer of vacant homes and adds to it when people were turned away. Building needs labour, materials and funding.

### 5.6 Prices and shareholders
- Every quarter the firm compares profit per share with its target. Target: the same quarter a year ago (or last quarter for a young firm), grown by the holding-weighted average of its shareholders' expected growth. A loss always counts as a shortfall. (J)
- On a shortfall the price rises by one step (3%). With no shortfall the price is left alone. This is the rule as Jason gave it and it is the default (`price_rule = ratchet`): an incumbent's price never falls. Prices come down only when a cheaper firm enters or a dearer one fails. (J)
- A second setting exists for comparison (`price_rule = search`): the first move is up, but if a move was followed by lower profit the next move goes the other way, so the firm hunts for the price that yields the most profit. (C) The two settings may well give opposite headline results, so neither is treated as neutral: the first results show both, and which one is the main case is Jason's call.
- Profit, for the target and for dividends, is: customer revenue plus exports, less wages, imported goods and interest, less wear on its units (each unit's building cost spread over its life). Money spent building or rebuilding units is not a cost of the quarter; it becomes units. So a quarter of heavy building does not by itself look like a shortfall. (C)
- Dividends each quarter come out of profit only: never more than the profit the firm has made and not yet paid out, and never from borrowed money or money raised by selling shares. They are paid from cash above a reserve of eight weeks of costs plus the cost of building already started. A firm with homes still to build keeps part back; how much depends on its shareholders' horizons. (C)
- Wages: a firm that cannot fill a vacancy for two weeks raises its wage 2%. In a shortfall quarter with a queue of unemployed in town, it cuts 2%. (J: bidding for scarce workers, cutting when there is a queue; C: the numbers)

### 5.7 Shares and the broker
- A firm starts with shares at $10 each, all held by its founder.
- New shares: issued through the broker when the firm needs money to expand and the founder prefers selling shares to borrowing, or has no credit left. (J)
- Some firms (30% by default) pay 5% of staff wages in new shares each quarter. (J for the route, C for the numbers)
- "Unhappy shareholder" means this: the firm's profit per share has grown more slowly than that holder expects. Such a holder values the share less, and when their value falls a tenth below the market price they offer a tenth of their holding. A holder is not counted unhappy with a firm younger than two years. (J for the idea, C for the numbers)
- The broker runs a weekly auction per firm: one clearing price that trades the most shares, closest to the last price. Sellers in distress accept any price. The price is the last trade. The broker charges nothing. (J)
- An agent who holds half or more of a firm's shares controls it and counts as an owner. If the controller is not the CEO and is free to take the job, they take it.

### 5.8 The bank
- Firms borrow against physical assets only, up to 60% of their value, at 6% a year over ten years. A firm with no homes or appliances cannot borrow. (J: assets as collateral; C: numbers)
- A unit's value as security is its current building cost, falling in a straight line with age to a floor of 20%. The 60% limit is checked when a firm borrows; a loan already made is not called if the value later falls.
- Individuals borrow against income only: up to eight weeks of wages, at 12% a year over one year. The loan is called when the job goes. (C, proposed in chat and not objected to) A called loan takes the agent's cash after food and housing each week. Unpaid after eight weeks it is written off and the agent is refused credit for three years.
- The bank cannot touch an agent's shares (`bank_can_force_share_sale = false`). The loan was made against income, and Jason's rule is that the agent's emotional state decides whether shares are sold or kept. So a jobless shareholder can default and keep the shares. The opposite setting exists as a dial because ownership concentration may turn on it. (J for the principle, C for the dial)
- Interest and repayments leave town. The bank never fails. (J)

### 5.9 Labour market
- Each week firms post vacancies, highest wage first. Unemployed residents apply and accept if the wage meets their reservation wage. Employed staff look around now and then, more when squeezed, and move for a 5% rise (any rise if squeezed).
- Vacancies still open are filled from outside while the town is under 1,000, the wage is at least the outside wage and a home is vacant. (J) A firm brings in at most three people from outside in a week, or a tenth of its staff if that is more; residents are hired as fast as it wants them. Firms paying the same wage are taken in a fresh random order each week. (C)
- Layoffs when a firm has more staff than work, last hired first.
- Executives are promoted from staff by skill and demoted when the firm shrinks. Both are logged.

### 5.10 New firms, failure, takeover
- While the town is under 1,000, a founder arrives now and then with capital. (J) Residents with enough cash and appetite found firms at any time, before and after the town is full. A founder either invents a new need or enters the existing need that looks most profitable or least served. An entrant undercuts the cheapest rival by 8% but never below cost plus 5%.
- A firm fails when it cannot pay its wages after borrowing and after asking its largest shareholder for cash, or when it misses four loan payments.
- The largest shareholder may put in rescue cash and receives new shares for it at the last share price.
- A failed firm that still has customers is sold as a going concern, the same week. A rival in the same need buys it if it can pay half the value of the units; otherwise the richest resident buys it for what they can pay, up to that price, and becomes its owner. Homes and appliance sets that people are living with are always sold on this way, so occupied homes never vanish. A service firm is sold to a resident at most once a year: if it fails again inside that year it is wound up, so nobody is made to keep a loss-maker alive. (C; this is "cheap firms get bought" from the chat)
- Where the money goes in a sale. The bank first writes the firm's debt down to what its units can secure (60% of their value) and records the rest as a loss. The buyer takes the units with that remaining debt. The price paid goes to the bank against the debt; anything above the debt, and any cash left in the firm when a rival absorbs it, goes to the old shareholders. Their shares are then cancelled. A resident buyer also puts in working capital of up to eight weeks of the firm's costs and holds new shares at $10 for the price and the working capital together. Because the debt stays on the units, a failure never frees them to be borrowed against a second time.
- Staff keep their jobs through a sale. The executives and CEO lose theirs. A firm that has just been sold cannot fail again for a quarter: if it still cannot meet its wages it lets go the staff it cannot pay, and its owner goes unpaid.
- A failed firm with no customers is wound up: staff laid off, debt repaid from any cash, the rest to shareholders, empty units scrapped.
- A firm with no revenue and no exports for half a year is wound up the same way and any remaining customers are released.

### 5.11 Class (J)
Recalculated every week:
- Owner: CEO or executive; founder of a live firm who still holds shares in it; controller of a live firm; or no job and dividends over the last year at least equal to a year of the four base needs (living on dividends alone).
- Working: staff drawing a wage, with or without shares.
- Out of work: everyone else.
Every move between classes is logged with what triggered it.

### 5.12 Happiness and failure
- Wellbeing = 0.5 x security + 0.3 x provision + 0.2 x condition. (C) Provision is the weighted share of needs met this week. Condition is the state of their home and appliances (zero if they have none).
- Happy means wellbeing of 0.5 or more. (C; the cut-off is a dial)
- Destitute: no job, not living on dividends, no shares, and less cash than one week of food and housing.
- The run fails the first week 90% of all agents are unhappy. (J) A guard ignores the rule while fewer than 20 agents are in town. (C) At failure the record notes how long it took, how concentrated the shares were and how far each need's price had risen.

### 5.13 The week, in order
1. A founder may arrive.
2. Firms plan staff; layoffs, promotions, vacancies; hiring from residents, then from outside.
3. Firms work: service, upkeep, building, making, importing, exporting. Units age.
4. Wages are paid. A firm that cannot pay fails here.
5. Agents plan the week's bills, cut subscriptions or place share orders.
6. The broker clears.
7. Agents pay their bills in order, borrowing if they choose and can. Missed payments, evictions.
8. Loans are serviced.
9. Each quarter: firm reviews (target, price, upkeep, make or import, exports, wages, dividends, share grants, raising money), control changes, wind-ups, residents founding firms.
10. Agents review subscriptions; security, wellbeing and class are updated.
11. The week is recorded and the failure rule is checked.

## 6. The record (one SQLite file per run)
- `run`: seed, full settings, code fingerprint, start and end, outcome, summary.
- `events`: every hire, layoff, quit, promotion, demotion, wage change, price change, subscription started, cancelled or switched, missed payment, eviction, loan, loan called, default, share issue, share trade, dividend, firm founded, firm failed, takeover, class change. Each with the week, who, which firm, the amount, and for an agent's own decisions their security and effective horizon at that moment.
- `agent_static` and `agent_snap`: every agent every week: cash, job, role, class, wage, debt, shares held and their value, subscriptions, security, effective horizon, wellbeing, happy, destitute, income, spending.
- `firm_static` and `firm_snap`: every firm every week: price, wage, customers, staff, executives, cash, debt, revenue, costs, profit, shares, share price, target growth, upkeep level, units, condition, vacancies, imports, exports.
- `holdings`: the share register, every quarter. `units`: every home and appliance set, every quarter.
- `series`: every measure every week for each scope: all, owner, working, out of work, and town.
- Also recorded, for the later life view and town replay: which home and which appliance set each agent has each week and its condition; units built and rebuilt; arrivals turned away for want of a home; job offers refused; credit refused; every share order with how much of it was filled; and each agent's provision, condition, wage income, dividend income and spending every week. Events are numbered in the order they happened, so the order within a week is kept.
- Routine weekly payments (wages, subscription payments, loan instalments) are not single events; they are in the snapshots and the weekly flow totals.

## 7. The dashboard
- One HTML file per run, built only from the record, readable offline.
- Header: run, seed, outcome in plain words, the warning that stage 1 is untuned.
- Charts with one line per coverage (everyone, owner class, working class, out of work): share unhappy with the 90% line, security, wellbeing, provision, condition, weekly income, cash, share of all shares held, head count.
- Town charts: prices against wages, cost of the basket against the staff wage, firms per need, unemployment and destitution, ownership concentration, money in town and the five flows, bank lending, moves between classes.

## 8. Dials
All dials and their starting values are in `wefworld/config.py`, with the reason for each. A run stores the full set it used. Any dial can be overridden from the command line or a settings file.

## 9. Left to the builder
Code layout, the SQLite column details, chart drawing, test design, and any starting value not fixed above.

## 10. Known simplifications in stage 1
- One staff wage per firm; skill only decides who is promoted.
- Rich and poor consume the same needs; spare money goes to shares, new firms and invented needs.
  **Changed 16/11/2026 (J):** the well-off spend more: a bigger plan of food, entertainment and luxuries, and a better home (decision 8). See `2026-11-16-wef-world-rulings-design.md`, section 7.
- Goods are not stored. A firm makes or buys what it needs each week.
- No firm sells goods to another firm; each makes or imports its own.
- Outside prices and quotas do not move.
- No interest on savings.
- One home per agent, no households, no births, deaths or ageing of people.
- The order in which a short-of-cash agent drops subscriptions is fixed by how essential they are.

## 11. What changed while it was built (12/11/2026)

Each of these was found by a test or by reading the record of a run, and each is in the build ledger.

- **The yardstick is the four base needs.** An agent's cushion, their security and whether they count as living on dividends are all measured against a week of the four base needs. Invented needs are left out, because counting them made well-off agents cancel and rejoin luxuries every week. (C)
- **Signing up counts the same bills as cutting back.** The loan instalment is in both. Before, agents with a loan cancelled a subscription and rejoined it every week. (C, a bug)
- **The export decision follows every wage change.** In the first full run the three exporting firms bid wages up 15% in twelve weeks to hire staff for export work that had stopped paying, noticed only at the next quarterly review, and all stopped exporting in the same week. Jason's rule is export when it is profitable for shareholders, so the decision is now re-made whenever a firm's wage moves. (J, a bug in how it was built)
- **`export_price_drop` dial.** With one outside price for the whole quota, exporting is all or nothing and jobs swing. The dial lets the outside pay less for each further unit. The default stays at 0, as written in 5.2, because changing a default after seeing a run would lean the result toward one of the two predictions. First results are shown both ways. (C)
- **A firm that has never had a customer does not move its price, its upkeep or its wage.** Otherwise an entrant still building would raise its price before it opened. (C)
- **After a sale the buyer is the firm's founder of record and its profit history starts again.** The ousted founder is no longer an owner. (C)
- **A new service firm keeps one worker for its first half year** while it finds customers. (C)
- **Lines on the dashboard end on the final week itself**, so a failed run's line reaches the failure level. (C)

### After the independent review

- **Two faults in the record were fixed.** Weekly income left dividends out, and a mistyped price rule ran the default while the dashboard said otherwise. Any setting that is not a real choice is now refused.
- **Service firms no longer sign up customers they cannot serve**, and residents are hired as fast as a firm wants them (see 5.4 and 5.9). In one run an entrant had taken 790 food customers with staff for 263.
- **A lapsed luxury that nobody sells no longer counts against needs met.** Whether one that is still sold is missed for ever is the `habit_weeks` dial (see 5.4).
- **The richest resident is no longer made to buy every failed service firm** (see 5.10). In one run two residents had been made to buy failed firms 144 times.
- **Week 0 is recorded**, so the founders' capital is in the weekly flows and the five flows add up to the money in town.
- **A base need that nobody sells keeps its last price** in the basket and the price index.
- **Class lines on the dashboard are averaged over the people in the class** and break where the class was empty. A strip under the chart marks those quarters, the legend says what it means, and the hover readout and the table say "nobody" there. (Asked for by Jason, 12/11, after the breaks read as missing data.)
- **A run can be repeated from the `config.json` in its own folder.**
- Left for later, by choice: a price rise is felt in proportion to income even when income is nil; the dashboard assumes 13-week quarters and 52-week years.
