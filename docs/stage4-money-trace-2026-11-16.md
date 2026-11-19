# Where the money goes, 16 November 2026

The question (Claude's, 16 November): in both batches the money in town rises all
the way to the end, while the working class's cash runs out. Where does it sit,
and is that the model working or a fault in it?

Short answer: it sits with the town's founders. Export money comes in, firms pay it
out as dividends, and a handful of founders who own their firms outright receive
it, spend about a quarter, and keep the rest as cash. Nothing in the model gives
that cash a way back to the workers. The accounts are right; this is how the rules
as built behave. Whether it is the world Jason means is a question for him
(decision 18 below).

## One town, year by year

Seed 32 of the second batch (`batches/20261116-rulings`, the rulings of 16
November), the middle town: it failed in week 975, year 18.75. Made again from its
own settings with every payment counted (`money.py` and `flows.py`, below). Money
is in $ millions.

| End of year | Money in town | Top five people | Other owners | Working class | Out of work | Firms |
|---|---|---|---|---|---|---|
| 10 | 47.9 | 19.2 | 4.4 | 11.5 | 3.8 | 9.1 |
| 12 | 62.6 | 32.7 | 5.9 | 12.3 | 1.4 | 10.4 |
| 15 | 101.2 | 66.3 | 6.9 | 11.4 | 0.6 | 16.1 |
| 18 | 142.4 | 110.0 | 7.5 | 3.8 | 0.0 | 21.1 |

(The top five are the five owners with the most cash; their share of the owner
class's cash was 81%, 85%, 91% and 94% in those years.) Closed firms held $0 in
every one of those years: a closed firm pays its cash to the bank and its
shareholders.

**What crosses the town's edge.** From year 12 to year 18 the outside bought $18.8
million of the town's goods each year, the full export quota. The town bought
almost nothing back ($0.1 to $0.3 million a year; before the town filled it had
bought $3.5 to $7 million a year, and why that fell is not traced). It paid the
bank $5.6 to $6.4 million a year in principal and interest. So the town's money
grew by $12.6 to $14.0 million a year: the trade surplus less the bank.

**Inside the town.** Over the same years:

| Year | Wages paid to staff | Dividends paid | Owner class: income | Owner class: spending | Staff wage |
|---|---|---|---|---|---|
| 10 | 54.9 | 5.5 | 11.7 | 4.9 | $1,073 |
| 12 | 48.5 | 10.4 | 15.7 | 5.2 | $1,008 |
| 15 | 44.7 | 14.7 | 20.1 | 6.2 | $943 |
| 18 | 42.0 | 19.2 | 24.2 | 6.4 | $869 |

"Wages paid" is every wage payment in the year, executives and chief executives
included; "income" is pay plus dividends. Dividends grew three and a half times
while the wage bill fell by nearly a quarter. The owner class spent between two
fifths (year 10) and a quarter (year 18) of what it took in. From year 15 its cash grew by about $15 million a year:
more than the town's whole surplus, so some came out of the workers' cash as well,
which fell from $11.4 million to $3.8 million.

**Who the five are**, at year 15: four of the town's day-one founders and the
founder of its transport firm, each still running their firm as chief executive.
The richest (person 2, the first food firm's founder) owned all of the food firm,
all of one landlord and 88% of another, held $31.3 million and took $6.9 million in
dividends that year.

## All 100 towns

From each town's own record (the agent and firm snapshots at the end of the year,
`pile.py`), the middle town of those still standing, with the middle half in
brackets:

| | Owner class's share of money | Top five people | Working class | Firms |
|---|---|---|---|---|
| Year 10, rulings (100 towns) | 46% (41 to 50) | 35% (30 to 40) | 24% (20 to 27) | 29% (23 to 33) |
| Year 10, first batch (100) | 60% (56 to 64) | 44% (40 to 49) | 16% (15 to 17) | 22% (18 to 26) |
| Year 15, rulings (99) | 63% (57 to 71) | 54% (47 to 64) | 11% (10 to 13) | 23% (17 to 30) |
| Year 15, first batch (86) | 73% (65 to 79) | 62% (52 to 68) | 6% (4 to 8) | 20% (14 to 26) |

The same in every town, less so under the rulings: in the first batch the rich did
not spend more and the money piled up faster ($139 million in the middle town at
year 15, against $104 million).

## Why it stays there: the rules that make it so

Each of these is a rule of the model as built. Marked (J) where Jason set it and (C)
where the builder did.

- **Owners keep what they do not spend, and it does nothing.** Cash earns no
  interest and the bank does not lend it on: the bank is federal and lends its own
  money (J: the bank is a federal backstop; C: savings are not lent). So money a
  founder saves is out of the town's circulation.
- **The rich have few things to spend on.** The four base needs, a bigger plan
  and a better home (J, 16 November), and luxuries. At year 15 person 2's bills
  came to $3,062 a week, with bigger plans, a better home and two luxuries,
  against $131,750 a week of dividends.
- **New firms are the only way saved money makes jobs, and they are rare.** A
  resident with cash founds a firm with a small chance each week (`resident_founder_rate`
  0.05, times their appetite for risk), and only into a need that is unserved or
  profitable enough (C). In seed 32 at year 15 a founder with $5 million would have
  started a childcare firm near people who could not reach one, so ventures were
  there to be had; the rate decides how often anyone takes them.
- **Shares change hands between residents.** Buying shares moves cash from one
  person to another; it does not reach the firm or its staff.
- **The outside buys a fixed quota at a fixed price, for ever** (C, stage 1).
  That is $18.8 million a year coming in whatever happens in town.
- **No tax, no welfare** (J).

What is not traced yet: how much of the founders' extra wealth comes from the
ratchet on prices (decision 1) and how much from exports alone. A batch with
`price_rule=search` would show it.

## The question for Jason: decision 18

What do the rich do with money they do not spend? As built, it sits. The other
answers would each give saved money a way back into the town:

- the bank lends savings on, to firms and residents in town;
- the rich put more of it into new firms (a higher founding rate);
- or it sits, as built, and that is the world he means.

**(J), 16 November 2026: it sits, as built.** His words: "No, this seems to be
correct. So What the rich usually do with their money is they tie it up in shares
or they put them in blind trusts or charity trusts and never use the money.So I
think we're fine with that." Nothing in the model changes.

## How this was made

`money.py` (who holds the money at each year end, and what crossed the town's
edge that year), `flows.py` (payments inside town by kind, owners' income and
spending, how concentrated owners' cash is) and `pile.py` (the same split across a
batch, from each town's snapshots) were run on 16 November 2026 against commit
`6ffd717`. They are kept with this note in `experiments/money_trace/`. They are records of
the trace, not part of the model, and have no tests of their own; every figure
above was also read a second way (the table of the town by a separate run, the
batch figures from each town's own snapshots).
