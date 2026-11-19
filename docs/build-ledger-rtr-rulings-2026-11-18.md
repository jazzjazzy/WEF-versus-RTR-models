# Build ledger: Jason's rulings of 18 November 2026 (RTR world)

Branch `feature/rtr-his-rulings`, cut from develop `46c7ca5`. Nothing committed: that waits for Jason's word.

Six questions were put to him after stage 2. His rulings, in his words, are in `HANDOFF.md` of the notes folder and at the head of `tests/test_rtr_rulings.py`. In short:

1. People with idle hours pay a repairer who is cheaper than their own hour: KEEP, and ADD: someone of the owner class pays for repair work at any price ("needs more time than money").
2. Makers with no job take the first job offered: CHANGE. Only with a large loan, less than half paid off.
3. Makers buy all their goods from outside: CHANGE. Outside only if they cannot get it in town at a reasonable price first.
4. A small business keeps the rate it is at after its staff have gone: KEEP.
5. A newcomer may rent anything vacant or buy anything available, if their income is good enough: NEW RULE.
6. One landlord firm buys a tenanted home from another only at a tenth over the price: KEEP.

No plan document: each ruling is one rule, built test first. This ledger is the record.

Format of a ruling of mine: `Ruling: what ; why ; cost if wrong`.

## Ruling 5: a newcomer may buy on arriving

His words: "If a newcomer is coming into the town, they have an opportunity to rent anything that's vacant or buy anything that's available as long as they have enough cash. Oh, good Enough income." And to my question "Should a newcomer with good enough income be able to buy a home on arriving?": "Yes, they can buy" (the wording of that answer is my button's).

As it stood: a newcomer came only if a home was free to rent within reach of the job (`labour.new_worker`, `corporate.maybe_arrive_founder`, both through `subscriptions.home_available`), and only someone already living in town with a job could buy a home the bank held (`rtr_owning._buyers`).

Built: `rtr_owning.newcomer_keeps`, `home_for_newcomer`, `arrive_as_owner`; `bank.home_cap_income` (the income test of `home_cap`, for an income given); `subscriptions.sign_up_for_the_rest` (the second half of `settle_arrival`); the two arrivals; the dial `newcomers_buy`; `rtr/settings.json` made again (one line added; `wef/settings.json` untouched). Tests: `tests/test_rtr_rulings.py`, sixteen, each seen to fail first where it could (ten failed before the rule existed; six are guards that pass with no rule and were proved by breaking the rule, below).

Ruling: a newcomer rents if a home is free to rent within reach, and buys only when none is ; a renter with a job already buys from the bank the same week if owning costs them clearly less (stage 1a), so weighing the two at the door would be a second copy of that rule ; a newcomer who would rather own pays one week's rent first.

Ruling: what is "available to buy" is an empty home the bank holds ; nothing else stands for sale when nothing is free to rent: a landlord's empty home is free to rent, a let home is only its tenant's to buy, and nobody in the model sells the home they live in ; if he means more (a home built for them, a home bought from its owner), the rule is narrower than he meant. FOR JASON, see "What the towns did".

Ruling: "good enough income" is the test anyone in town passes to buy from the bank (`_terms`): their cash beyond what they hold back, the rest borrowed within the bank's four fifths of the price and within a payment of three tenths of their income, and the income is the wage of the job they come for ; one rule for every buyer ; the four fifths and the three tenths are my numbers from stage 1 (marked C in `config.py`), and the usual newcomer brings about $3,000, so they have their fifth only for a home under about $15,000 less what they hold back. FOR JASON: whether a newcomer needs the fifth in cash at all (he corrected "enough cash" to "good enough income" himself). (RULED the same day: "Lend the whole price". See "The deposit" below; the tests of the fifth now run with the dial at 0.8.)

Ruling: a newcomer holds back four weeks of the base needs other than a home at the cheapest prices on offer (`newcomer_keeps`) ; a resident holds back four weeks of their bills, and a newcomer has none yet ; a few dollars either way on who can buy.

Ruling: the home must be a walk from the job, or a ride where a ride is on offer, and then the ride comes with it ; that is the rule for a home rented on arriving ; a resident buyer is held to where they can get today, so a newcomer may buy a home a resident on foot could not.

Ruling: a newcomer does not weigh buying against building ; a resident who could build for less a week builds instead, but a newcomer has nowhere to live while they build ; none seen.

Ruling: of the homes they could buy, the one the bank asks least for, the older home first at the same price ; the least debt ; none seen.

Ruling: a founder buys only if the cash they keep back from the venture (a tenth of their capital) covers the whole price, and the venture still gets its nine tenths ; they have no income yet, and his rule is "no income, no loan" ; a founder with a good venture and a dear home is turned away.

Ruling: the sign that a home is wanted (`town.no_home_week`) is set as before, when a newcomer is turned away, which now means they could neither rent nor buy ; I told him so before he ruled ; fewer homes bought or built to let.

Ruling: a dial, `newcomers_buy`, RTR only, on by default ; so the rule can be switched off whole and towns compared with and without it ; one more dial.

Ruling: the arrival is recorded with `bought`, the home's number, beside `who` ; so the pages can count it ; a field only on those arrivals.

Ruling: where nothing is free to rent and the bank holds a home, the newcomer's cash is rolled before it is known whether they come ; the price they can pay depends on it ; from that week the town's dice differ from a town without the rule. Never in the WEF world (`test_in_the_wef_world_the_dial_is_not_read`).

Test slips of mine, all in the tests: the first helper took its first setting for the asking price; a transport firm needs its need added to the town first; my stand-in for the dice answered for a person's temperament as well as their cash (it now answers only for the cash, and counts the rolls).

Checked: 1,028 tests passed on this rule alone (the 1,012 of stage 2 and these sixteen), and 1,032 with ruling 1 built, each run fresh; old-rules seed 74 of the 13 November batch still `08251209eb136522`, 180,377 events; the pinned RTR towns of stages 1 and 2 are the towns they were (no newcomer buys in any of them); the rule broken on purpose 38 ways in a scratch copy, 35 caught at once, three showed gaps in my tests and each got a test (invented needs held back, the cash rolled twice, a founder's arrival not saying what they bought), and all 38 are caught now; one more is a doubled guard that stood before today (`if afford <= 0` in `bank.home_cap_income`).

### What the towns did: the rule is never used

Counted before and after building, not tuned.

- Three full RTR towns (seeds 1, 2, 3) run without the rule and watched at the door: 1,163, 904 and 1,012 workers turned away, and in no week of those did the bank hold an empty home, in reach or out of it.
- Forty small towns of 200 (seeds 1 to 20, on a map and with none) run WITH the rule for fourteen years under the weekly checks: every check clean; 20,789 turned away, 3,658 homes taken by the bank, and not one newcomer bought.
- Why, counted year by year in the three full towns: workers arrive, and are turned away, only in years 0 to 6. The town is full by year 6.25 to 6.85 (the land has run out and a newcomer finds no home). After that no worker comes and nobody is turned away, to the end. Traced in seed 1: through year 6 nobody is out of work and thousands of vacancies go unfilled at firms that all pay the outside wage; in year 7, 352 are out of work and from then on not one vacancy is left unfilled at the week's end, so no firm looks outside (and from year 9 no firm pays the outside wage, which it must to hire from outside). The bank takes its first home in year 6 to 8, and in the last year of each town holds up to 181, 247 and 366 empty homes (the towns fail in years 23.5, 27.25, 29.75).

So newcomers and the bank's homes never meet. The rule is right as he gave it and does nothing in a town as towns now run.

**Who the bank's homes could go to** (seeds 1 and 2, every second year; `scratchpad/newcomer_probe3.py`). At year 20 in seed 1: 1,095 people, 521 out of work, 437 with no home, 75 of those in work, none of the 437 with four weeks of the going rent in cash. Standing empty: 126 homes the bank holds (the cheapest asked $10,750), 205 homes people let, 6 landlords' homes. The going rent is $609 a week and the typical wage under $700. Seed 2 at year 22: 411 with no home (52 in work), 83 bank homes empty (cheapest $6,367), 281 lets empty, rent $737.

What that says about the rule he could not follow when I first put it ("an empty home is bought to let only when a newcomer was turned away for want of one"): after year 7 no newcomer is turned away, so by that rule nobody buys one of the bank's empty homes to let it. But that is not what keeps people out of them: two hundred and more homes already stand empty to let, and the people with no home cannot pay the rent. More homes to let would stand empty too. The rule stays.

What it says about "good enough income": someone in work at $700 a week pays $609 in rent or sleeps rough beside a home the bank would sell for $10,750. The loan on all of it would cost about $23 a week. They cannot buy it because the bank lends four fifths and they have not the other fifth in cash beyond four weeks of bills. The four fifths is MY number (the design, "The loan": "C: the three numbers"); his words for the loan were "if their income allows", and on 18/11 again "enough cash. Oh, good Enough income." FOR JASON: whether the bank should want the fifth in cash at all.

**A trial, to know what the question is worth before asking it** (`scratchpad/whole_price.py`; seeds 1 and 2; both rulings of today built; `mortgage_ltv=1.0` against the default 0.8; nothing else changed). The dial also covers building: the bank then lends all of a home's materials.

| | seed 1 as built | seed 1, whole price lent | seed 2 as built | seed 2, whole price lent |
|---|---|---|---|---|
| failed in year | 26.0 | 52.0 | 30.3 | 34.5 |
| people at the end | 1,093 | 887 | 1,056 | 874 |
| own their home at the end | 336 | 661 | 335 | 695 |
| no home at the end (of them in work) | 581 (131) | 221 (1) | 647 (212) | 179 (19) |
| bank's homes empty at the end | 261 | 179 | 207 | 98 |
| homes the bank took / sold to someone to live in | 553 / 279 | 1,424 / 1,100 | 531 / 308 | 1,356 / 1,116 |
| the bank wrote off | $148,307 | $159,617 | $167,860 | $182,677 |
| newcomers who bought | 0 | 0 | 0 | 0 |

Two towns. Not a finding. Not traced: why seed 1 runs to year 52 (by then the going rent is $15,476 a week and the typical wage $72, the old ratchet), or why the towns are smaller. It says only that the fifth is a big lever and that it is mine.

**Ruling 1's towns.** The "as built" columns have ruling 1 on. The same seeds this morning, before it, failed in years 23.52 and 27.25. Two towns: the rule or the dice, not traced.

## Ruling 1: the owner class pays for repair work at any price

His words: "Yes, unless they are an owner class, then they'll get anyone to do repair work for them at any price. as an owner class, needs more time than money."

So the rule of stage 2 stays for everyone else (someone pays a repairer who comes to less than their own hour, and beyond that for the hours they are short of), and someone whose class is `owner` (an executive, a founder or controller of a live firm, or living on dividends: `household.classify`) buys every hour of upkeep on what they own, and on the homes they let, from whoever will do it, the cheapest first, whatever the price.

Built: three lines in `rtr_owning._repairer`; the dial `owners_pay_any_price` (RTR only, on); four tests in `tests/test_rtr_rulings.py`, two seen to fail first.

Ruling: "any price" is paid from the purse everyone pays a repairer from, their cash beyond four weeks of bills ; nobody in the model spends money they do not have, and the four weeks is the rule for every purchase of this kind ; an owner with little cash does their own repairs. I had this down as a question for him; it is not worth one of his answers, and it is said here so he can overturn it.

Ruling: repair work only, not the building of a set or a home ; his words are "repair work" ; an owner who builds still works their own hours first.

Ruling: class is the class they were given at the last week's end (`agent.klass`) ; that is how the labour market reads it ; someone made an executive this week pays any price from next week.

Checked: the rule broken on purpose 8 ways, all caught. With ruling 5: 46 breaks, all caught.

## The deposit: the bank lends the whole price

Not one of the six. It came out of counting ruling 5's towns (above), was put to him with the two-town trial, and he ruled: "Lend the whole price" (the wording is my button's, under "Should the bank lend the whole price of a home, or still ask a fifth in cash?").

Built: `mortgage_ltv` is 1.0 (it was 0.80, marked C; now marked J); `rtr/settings.json`; the comments that said "four fifths". No line of logic changed: every place already read the dial, and the branch for a whole share in `_own_hours_on_home` was already there, never run by a test until today.

Ruling: one dial, so the whole value is lent wherever the design said 80%: buying, building with their own hours or a builder's, buying or building a home to let, and borrowing against a home already owned (the cushion, tools for a side hustle) ; section 7 uses one number for all of it ("the same 80%") and the trial he saw was run that way ; borrowing against the whole value of a home already owned was not put to him in so many words. FOR JASON.

Ruling: the 27 tests written for the fifth are kept as tests of the dial at 0.8 (marked `fifth_in_cash`; `tests/conftest.py` gives their hand-built towns the old dial), not rewritten ; the dial is still there and must still work, and 27 sets of figures redone by hand is where my slips come from ; the shipped setting is held by fewer hand-built tests than the old one was: nine new ones (the whole price lent to a buyer, a newcomer, a builder with their own hours and with a builder's, a home to let bought and built, building weighed against buying) and whole towns.

Ruling: the whole-town tests of stages 1b and 2 keep the towns their seeds were picked for, with the dial at 0.8, and towns exactly as the RTR world now ships are run under the same weekly checks in `tests/test_rtr_rulings.py` (seeds 10 and 2 on a map, 5 and 3 with none; fourteen years; they must reach a home bought with the whole price lent, a home being built with every part lent, and someone of the owner class having a repair done at any price) ; stage 2 did the same to stage 1b's towns ; four rules of the older stages are not reached at the shipped setting in the old seeds (a block made into plots, a foreclosed home to an owner who lets it, a let home sold to another landlord, a creator starting their idea), and I have not looked for seeds that reach them.

Found: with the dial at 0.8 the two pinned towns of stage 1 are still the towns they were, event for event. So the three changes of today switch off whole.

Test slips of mine: the first whole-town watch counted an owner-class person buying the hours they were short of, which the old rule allows too; the break-the-rules step showed it (the owner-class rule switched off went unnoticed) and the watch now counts only someone who had the hours and no repairer cheaper than their own hour.

Checked: 1,045 tests pass, run fresh on the final code and tests (only comments and documents changed after that run); old-rules seed 74 of the 13 November batch still `08251209eb136522`, 180,377 events; 56 rules broken on purpose across the three changes, every break caught by a hand-built test (three of the ten for the whole price showed gaps first: building weighed against buying, a home to let bought, a home to let built; each got a test), and three of them tried against the whole-town test alone, all caught after the fix above. Three full RTR towns exactly as shipped (seeds 1, 2, 3) under the weekly checks: every check clean; they failed in years 52.0, 34.5 and 34.79 (the same seeds as stage 2 was merged: 23.52, 27.25, 29.75). Three towns, nothing tuned, not a finding.

Not done for any of today's three changes: the fresh review and the forty full towns. They wait until rulings 2 and 3 are built.

## Ruling 2: someone out of work with a side hustle, and the jobs on offer

His words: "No, they will only take the first job offered if they have a large loan, So they've only paid off less than 50% of their loan They will take the job." Read word for word, someone with a side hustle and no loan never takes a job. Put to him with his own kind of example ("A side hustle brings in $200 a week, no loan: do they take a $600 a week job?"), he said "Yes, take it" (the wording is my button's).

So: someone out of work with a side hustle takes a job only if it pays more than the side hustle brings in; unless they owe a large loan, less than half paid off, when they take the first job offered as anyone does.

As it stood: someone out of work with a side hustle looked for work like anyone (the best offer, taken if it met their reservation wage), and in five full towns took a job 2,331 times, 1,256 of them at less than the side hustle was bringing in.

Built: `rtr_makers.least_wage`, `owes_a_large_loan`, `remember_loans` (called from `start_week`); `Agent.loan_top`, `Agent.home_loan_top`, `Hustle.loan_top`; the two places a resident out of work is offered a job (`labour.labour_market`, step 2, and `rtr_makers.hire_staff`); the dial `makers_weigh_jobs`. Tests: twelve in `tests/test_rtr_rulings.py` (ten, one of them run for each of the three loans), eight seen to fail before the rule existed and the rest proved by breaking it.

Ruling: "what the side hustle brings in" is what it brought in a week over the last quarter (`profit_week`, the figure the bank and their own income already use) ; one figure for a side hustle's income everywhere ; a side hustle in its first quarter has brought in nothing yet, so its owner takes any job they would have taken without it.

Ruling: "pays more" is the wage against that figure alone. The side hustle goes on in the hours the job leaves, so with the job they have both ; his example compares the two numbers ; someone gives up most of a side hustle's hours for a job that pays a dollar more than it did.

Ruling: the reservation wage still stands under both halves: nobody takes a job for less than they would work for with nothing else, loan or no loan ; "as anyone does" ; none seen.

Ruling: "a large loan" is any loan from the bank of which less than half is paid off: a personal loan, the loan against their home, the bank's loan on the side hustle. His "So" makes the half the test of large; no size is asked ; it is what he said ; someone with $300 left of a $500 loan for tools takes the first job offered. With the whole price lent, most home owners are in this state for the first ten years of a twenty-year loan. FOR JASON, said to him, not asked.

Ruling: "paid off" is measured against the most that was ever owed on that loan since it was last nil, noted once a week as the week starts (none of the three loans kept what was first borrowed) ; a missed week adds its interest, so the most owed can be more than was borrowed, and one sweep catches every way a loan grows ; a loan taken and part repaid inside one week is measured from where it stood at the week's start. A loan just taken counts at once.

Ruling: exactly half paid off is not "less than half": they stay ; his words ; a cent.

Ruling: a refusal for this reason is recorded as `offer_refused` with `why: "side hustle"` ; so it can be counted ; a field only on those.

Found by the break-the-rules step against the whole towns: a small business takes on residents out of work by its own route (`hire_staff`), which did not weigh the side hustle; with the loan test broken the whole-town test still passed, because makers were being taken on there. Test first (`test_a_small_business_takes_on_a_maker_out_of_work_only_by_the_same_rule`, failed: the wrong one of two was taken on), then one line.

Found: two seed-picked tests of stage 2 no longer found what they were picked for (a set builder starting; a business with staff and a loan in seed 2). The whole-town tests of stage 2 now run the world as it was merged (`BEFORE_THE_RULINGS` in `tests/conftest.py`), and towns as shipped are held in `tests/test_rtr_rulings.py`: they reach every rule the older whole-town tests ask for (on the map all but the rare one, a maker becoming a company, which the no-map towns reach), and the every-firm-closes test is repeated there on seed 10.

Checked, with stage 2 ON this time: three small towns (seeds 10 and 2 on a map, 5 with none; ten years) on `develop` and on this branch with today's four dials at their old values are the same towns, event for event (`8b51f152585e7ff9` 36,973; `591d61b19c99c7e7` 47,109; `94bb391736c2ca31` 23,709). So all of today switches off whole.

Checked on the final code: 1,059 tests pass, run fresh; old-rules seed 74 of the 13 November batch still `08251209eb136522`, 180,377 events; 80 rules broken on purpose across all four of today's changes (24 of them this ruling's), every break caught by a hand-built test, and this ruling's two main breaks tried against the whole-town test alone, both caught after the fix above. Three full RTR towns exactly as shipped (seeds 1, 2, 3) under the weekly checks: every check clean; they failed in years 40.75, 37.25 and 35.52 (with the whole price lent but before this ruling: 52.0, 34.5, 34.79; as stage 2 was merged: 23.52, 27.25, 29.75). Small businesses still take people on (364, 430 and 389 in the three towns). Three towns, nothing tuned, not a finding, and why is not traced.

Not done: the fresh review and the forty full towns, which wait for ruling 3.

## Ruling 3: a maker buys their goods in town first

His words: "No, they can only buy outside the town if they can't get it inside town at a reasonable price first." Asked what reasonable means with an example ("Ingredients cost $189 from outside. The town's food firm asks $200. Does the maker still buy in town?"): "I would say yes buys in town because it's only $11 difference and they get it sooner. where if it was $189 and in town it was $298 That would get it from out of town".

As it stood: a maker bought every unit from outside at the import price, and no firm sold goods to anyone in town. A firm makes its own goods or imports them, and with staff to spare makes more and sells it outside at the export price, up to a quota. In five full towns $591 million of food makers' $1,028 million of takings left town this way.

Built: `rtr_makers.reasonable`, `town_price`, `place_orders` (from `start_week`), `buy_goods`, `sell_leftovers` (from `after_bills`); `Firm.town_target`, `Firm.town_units`; `Town.goods_wanted`; step 5 of a firm's week (`production._work`) and its staffing (`labour.labour_need`); the parts a repairer or builder buys (`sell_hours`, with whose good they are passed down from `keep`, `_repairer`, `_home_builder`); the dials `makers_buy_in_town` and `town_goods_premium`. Tests: thirteen in `tests/test_rtr_rulings.py`, eight seen to fail before the rule existed, the rest written against it and proved by breaking it.

How it works. What the makers wanted of each good in a week is ordered the next week, in equal shares, of the town's firms in that line whose price is reasonable. A firm makes its order with the staff it has left after its own customers, before anything for export, and counts the order when it decides how many staff it wants. When a maker buys the week's goods they take what the town's firms made for them, the cheapest first, and the rest from outside. What nobody took is sold outside at the week's end.

Ruling: the line between his two examples is a tenth over the outside price (`town_goods_premium`): $200 against $189 is 6% over and is bought in town; $298 is 58% over and is not; the line falls at $207.90 ; he gave no line, the model's "a little" is a tenth everywhere else, and it is a dial ; someone who would pay a fifth more to have it sooner is sent outside. FOR JASON, said to him.

Ruling: the seller is a firm in the same line of business as the maker, because in the model the only makers of a good are the firms that sell that need: a food maker's ingredients come from the food firm they compete with ; there is nobody else in town who makes them ; a firm supplies its own competitor at a tenth over cost. FOR JASON, said to him.

Ruling: a firm asks a maker what a unit costs it to make, overhead and all, and a tenth on that (`maker_margin`), and never less than the outside pays it for the same unit ; cost plus a little, as a maker charges, and no firm sells for less than it can get ; at low wages the firm asks the export price though it makes for far less (food: $168, made for $102 at a wage of $600), so the saving on a unit is the firm's.

Ruling: a firm makes for the town's makers what they wanted LAST week ; a firm plans its week before the makers know what they sold ; the first week of any new demand comes from outside, and a week's order nobody then wants is sold outside.

Ruling: what a firm made for makers and nobody took is sold outside at the export price at the week's end, whatever the quota ; the goods exist ; a little more is exported than the quota allows.

Ruling: a firm's takings from makers are booked with its takings from customers, and what it sends outside at the week's end with its exports ; the two are only ever added together in the firm's reckoning, and "exports" should mean what left town ; the pages cannot yet tell goods sold to makers from customers' payments except by the ledger's own kind, `town_goods`.

Ruling: a maker's own price is still reckoned on the outside price of their goods ; the design prices a maker at cost plus a tenth and says nothing of where they buy ; cheaper goods in town are the maker's gain and dearer ones their loss, and their customers pay the same.

Ruling: a repairer's and a home builder's parts are bought the same way, from the town's landlords or appliance firms, and their customer pays what they paid before ; they are makers buying goods ; none seen.

Ruling: someone doing their own upkeep or building still buys their parts from outside ; his ruling is about makers ; an owner's parts are a larger sum than the makers' and all of it still leaves town. FOR JASON.

Test slips of mine, in the tests: a food maker's sixty hours serve eight customers, not the ten I gave them; the whole-town watch on repairs had the old signature.

Found: with this ruling on, the four small towns of the shipped test no longer reached four older rules (three about the bank taking a home, one about a block made into plots): in those seeds the bank took far fewer homes in fourteen years. Forty small towns exactly as shipped were then run under the weekly checks (seeds 1 to 20, map and none): every check clean; 2,577 homes taken by the bank between them, 815 jobs turned down for a side hustle, no newcomer buying. The shipped test now uses four of those forty (17 and 3 on a map, 16 and 10 with none), which reach every older rule but one (a landlord short of cash selling a let home to another landlord: not in these four, not looked for in the others).

Checked on the final code: 1,072 tests pass, run fresh; old-rules seed 74 of the 13 November batch still `08251209eb136522`, 180,377 events; 119 rules broken on purpose across all five of today's changes (39 of them this ruling's), every break caught by a hand-built test, and this ruling's two main breaks tried against the whole-town test alone, both caught; with all five dials at their old values the three small towns (makers on) are still the towns of `develop`, event for event. Three full RTR towns exactly as shipped (seeds 1, 2, 3) under the weekly checks: every check clean; they failed in years 45.0, 49.75 and 59.33 (before this ruling: 40.75, 37.25, 35.52; as stage 2 was merged: 23.52, 27.25, 29.75). Small businesses took on 664, 707 and 1,846 people in the three towns and let 91, 74 and 690 go unpaid (before this ruling: 364, 430, 389 taken on; 36, 29, 47 unpaid). Three towns, nothing tuned, not a finding, and why is not traced: not the longer lives, and not the 690.

## The forty full towns (the crash hunt), finished 18/11/2026 about 6pm

`python3 batch.py rulings1811 --seeds 1-40 --quiet` from `rtr/`, the RTR world as it now ships, 60 years, code `d1c14bfd84a40070`. Folder `rtr/batches/rulings1811` (not in git). These towns ran WITHOUT the weekly checks: this run hunts crashes, it does not prove the books.

- No crash. All forty ran to the end or to the failure rule.
- 29 failed (the rule is Jason's: 90% unhappy). Failed in year 34.75 at the earliest, 59.5 at the latest, middle 48.8.
- 11 never reached 90% unhappy in 60 years (towns 4, 5, 7, 9, 11, 15, 19, 22, 31, 35, 40). The record calls these "survived". READ THE NEXT TWO LINES BEFORE USING THAT WORD.
  - Seven of the eleven (5, 7, 11, 19, 22, 35, 40) end with 37 to 45% out of work, a wage of $32 to $64 a week, 190 to 264 people destitute, and 80 to 87% unhappy. They sit just under the line. That is not a town that works.
  - Four (4, 9, 15, 31) end with 2 to 11% out of work and a wage of $601 to $872. They are still 63 to 83% unhappy.
- Beside the same forty seeds at the stages before: stage 2 Part A, 40 of 40 failed, middle year 23.1; stage 2 Part B (as merged into develop), 39 of 40 failed, middle year 28.5.
- Towns 1, 2 and 3 failed in the same years here as under the weekly checks (45.0, 49.75, 59.33).

Not traced: why the towns last longer; which of the five changes does it; why seven towns settle just under the line instead of crossing it. Forty towns, nothing tuned. The difference from stage 2 is large and it is NOT explained, so it is a thing to look into, not a result.

## The fresh review, finished 18/11/2026 about 6:10pm

A reviewer with no part in the build, working in its own copy; the repository was not touched. It ran the suite forwards and backwards, 162 small towns under the weekly checks with odd needs, odd rates and every mix of today's switches, 24 towns where every firm of a need closes mid-week, two full towns under the checks to their ends, and 38 breaks of its own. Its scripts are in the scratchpad's `review_rulings/` (not kept).

**Nothing Critical.** No line from the weekly checks in any town. In seed 3's full town all 1,227,788 purchases of goods balanced. Six WEF towns are the same on `develop` and here.

Its findings, each graded again by what a person using the model gets, and what was done. One fix pass.

- Final: fixed (Important, stands): **a full settings file saved before today ran four of today's five rules without a word.** `load_config("rtr/batches/stage2b/base-settings.json")` gave the old loan (0.8) with the four new switches on: a town that never shipped. The batch page itself tells a reader to re-run a town from its saved `config.json`. Now `load_config` refuses a full file that leaves out a dial its world reads, names each one and today's value, and says the way out (add it to the file, or give it with `--set`). A WEF world file may still leave out what only the RTR world reads; a short file still means today's world with a few dials changed. `test_a_full_settings_file_saved_before_a_dial_existed_is_refused_and_the_dials_are_named`, `test_the_file_loads_once_every_missing_dial_is_given`, `test_a_wef_world_file_may_leave_out_only_what_the_rtr_world_alone_reads` RED then GREEN; `test_a_full_file_with_every_dial_and_a_short_file_load_as_they_did` held throughout. Tried on the real file: refused, five dials named; with the five given it loads as stage 2.
  - Final: Ruling: refuse, do not fill in the old values ; the model cannot know what a missing dial stood for in general (not every change has a dial), so guessing either way runs a town nobody asked for, and refusing is what `validate` already does for settings that "would run something other than what was asked for" ; if wrong, someone re-running an old town has to add up to five words to the command, which the message spells out.
- Final: fixed (the reviewer's Minor, graded up: it is a crash): **a need whose goods a firm asks nothing for stopped the run** (`ZeroDivisionError` in `buy_goods`; `needs.X.export_price=0` with almost no labour to make it). Not reachable with the shipped needs. Goods asked nothing for are now taken without being held to the till. `test_goods_a_firm_asks_nothing_for_are_taken_for_nothing_and_the_week_goes_on` RED then GREEN.
- Final: tests added, no code changed: **four breaks no hand-built test caught** (the two till limits in `buy_goods`, leftovers not counted as units exported, the home loan's high mark never cleared). `test_a_maker_short_of_cash_takes_from_the_towns_firm_only_what_the_till_will_pay_for`, `test_the_rest_from_outside_is_held_to_what_is_left_in_the_till`, `test_what_nobody_took_is_counted_with_the_units_the_firm_sent_outside`, `test_a_home_loan_paid_off_is_forgotten_and_the_next_is_measured_on_its_own`: each passes on the code and fails under its break.
- Final: corrected: `rtr/README.md` still gave the four fifths in the present tense in two places. Found by me while there: the same page said twenty-four dials are the RTR world's own; it is twenty-nine since today (counted from `RTR_ONLY`). Both worlds' pages now say an old full settings file is refused (`wef/README.md` changes by that one sentence; nothing else of the WEF world is touched).
- Final: minor (deferred): **a door for ruling 2.** A firm with no chief picks "the jobless first" to run it (`corporate.pick_manager`) and does not ask what their side hustle brings in. The reviewer counted 214 makers out of work made chief of someone else's firm in 173 small runs, a little over one a town in fourteen years. FOR JASON: is being put in charge of a firm "taking a job"?
- Final: minor (deferred): goods a firm made for the makers are lost if the firm closes that same week (`sell_leftovers` passes over closed firms): 3,345 units in 173 small runs. No money goes astray.
- Final: minor (deferred): three of the reviewer's five breaks failed the whole-town tests only at the exact list in `test_between_them_the_towns_as_shipped_reach_every_rule_of_the_stages_before`, which any harmless change to those towns would also fail.
- Final: minor (deferred): the `fifth_in_cash` marker does not reach a town built by a module-scoped fixture. No leak today: run backwards, all 27 marked tests built their towns at 0.8.

**What the reviewer declined to judge, and my ruling on each.** These are how the rules play out, not faults.

- Final: Ruling: **"a large loan" stands as built, and goes to Jason first** ; in two shipped small towns the loan clause sent a maker into a job paying no more than the side hustle 71 and 64 times (68 and 64 of them on the home loan), against 39 and 41 jobs turned down. Of the makers out of work who were hired, about four in five owed a loan less than half paid off, nearly always on their home. His words were "a large loan, So they've only paid off less than 50% of their loan", and a home loan in its first ten years is that; counting it is my reading ; if wrong, his rule that a maker keeps the side hustle unless the job pays more does nothing for most people who own a home. FOR JASON.
- Final: Ruling: the price floor stands ; a firm never asks a maker less than the outside pays it, and in seed 3's full town makers paid $39.2M under the outside price in all and $38,000 over, while their own prices did not move, so the gain is the maker's ; if wrong, makers' customers see none of the saving (said to Jason as my call at 5pm).
- Final: Ruling: the tenth stands ; an entertainment firm's price is over the line while its wage is above $818, so 7% of those goods were bought in town in the reviewer's small runs against 73% of food ; if wrong, his rule works for food and hardly at all for entertainment. FOR JASON (the line is my call between his $200 and his $298).
- Final: Ruling: what is still bought outside stands ; his ruling was about makers. In a shipped small town: makers' tools $237,500; parts for people's own sets $2.16M, also when a set builder does the hours; people's own upkeep and building about $18M, against $11.8M of makers' goods ; if wrong, most of the money that could stay in town still leaves. FOR JASON.
- Final: Ruling: "any price" stands, it is his ; it cost the owner class 9% more than the parts and their own hour ; nothing to pay if wrong, it is what he ruled.
- Final: Ruling: leftovers sold outside beyond a firm's quota stand ; 0.2% of exports ; a firm sells a little more outside than the outside was said to take.

**Why the towns last longer: the reviewer's answer, and my own count.** The reviewer ran seed 3's full town twice, changing only `makers_buy_in_town`: with the rule off the makers' goods money leaves town, with it on it goes to the town's firms and becomes wages. I ran the same pair myself for twenty years, with my own counter on every payment (`verify_why.py` in the scratchpad), no weekly checks:

| seed 3, twenty years | goods bought in town first | everything from outside |
|---|---|---|
| makers paid the town's firms for goods | $64.1M | $0 |
| makers paid outside for goods | $2.6M | $86.0M |
| firms paid in wages | $449.4M | $385.3M |
| out of work at year 20 | 12 of 799 | 285 of 820 |
| without a home at year 20 | 0 | 159 |
| unhappy at year 20 | 162 | 461 |

The reviewer's own figures at year 20 were 11 against 307 out of work, none against 189 without a home, 177 against 511 unhappy: the same direction and size, not the same to the digit (I have not chased the difference; a different week is the likely cause). ONE town, one switch. It says ruling 3 is most of the longer life in this town. It does not say the same of the other thirty-nine, and it does not say how much the whole price and the jobs rule add.

**The 690.** Seed 3's small businesses let 690 people go unpaid, against 47 before ruling 3. From the record of the forty-town run I count 44 of the 690 by year 35 (the town without the rule ended in year 35.5 with 47) and 646 after. It is the longer life, not a new fault: the reviewer found that in 97% of those weeks the owner had under one wage in hand, as the wage fell from $511 to $102.

**The newcomer rule does run** in one odd town the reviewer built (every good made with no labour, no map, seed 308): three workers bought in week 216, each lent the whole price, checks clean. In the towns as shipped it still never runs.

**Not got to by the reviewer:** other seeds' full towns to their ends; a full town with the bank's share under 1.0; the pages and the dashboard; `export_price_drop` above 0.

**Checked on the code after the fix pass (18/11/2026, 6:21pm):** 1,081 tests pass, run fresh (1,072 and the nine above; 69 are for today's changes). 128 rules broken on purpose (the 119 and nine for the fix pass), every break caught. Old-rules seed 74 of the 13 November batch is still `08251209eb136522`, 180,377 events. NOTE: that check loads the town's saved `config.json` of 13/11, which the new refusal stopped at once: the file was saved before `better_home`, `bigger_plan`, `unserved_entry_min`, `well_off_drop` and `world` existed. The check now names the five (under the old rules none of the four dials is read) and the record is the same. That is the cost the ruling above said it would have, met the same hour. The four settings files kept in the repository all load. Three small towns as shipped (seeds 3 and 17 on the map, 16 with none) give the same record before and after the fix pass, event for event; with the five dials at their old values the same three are the towns of `develop`. One full town as shipped (seed 14) run again on the fixed code: failed in year 35.52 with 628,342 events and 835 people, exactly as in the forty-town run. So the forty towns and the three checked towns above stand for the code as it now is. Not run again after the fix pass: the other thirty-nine full towns, and the three full towns under the weekly checks.

## Committed and merged, 18/11/2026

On Jason's word ("Yes, model repo", 6:57pm): commit `5986a9d` on `feature/rtr-his-rulings`. On his word ("Yes, merge", 7:04pm): merged into `develop` as `9d56400`; 1,081 tests and the old WEF town checked again on `develop`. `main` untouched.

## The home loan ruling, 18/11/2026, evening (branch `feature/rtr-home-loan-not-large`)

**Where it came from.** The fresh review's count against my reading of ruling 2 (above): counting the loan against a home as "a large loan" sent makers into a job paying no more than the side hustle 71 and 64 times in two small towns, against 39 and 41 jobs turned down. Put to Jason as a person in a situation: "A side hustle brings in $700 a week and they have a new home loan: do they take a $600 job?" **His answer: "No, stay"** (the button; the wording is mine).

- Ruling (J): **the loan against a home is not the "large loan"** ; his answer ; nothing to pay if wrong, it is what he ruled.
- Ruling: what still counts is a personal loan or the bank's loan on the side hustle, less than half paid off ; he was asked only about the home loan, and these two are the rest of his words "less than 50% of their loan" ; if wrong, a maker with a small personal loan still takes the first job offered whatever the side hustle brings in. FOR JASON.
- Ruling: a dial, `home_loan_presses`, off as shipped, one of the RTR world's own ; with it on the towns are the towns merged at `9d56400`, so today's earlier results can be made again ; one more dial to keep.

**Built.** `rtr_makers.owes_a_large_loan(agent, home_counts=False)`; `least_wage` passes the dial. Both doors a job comes through (the labour market, a small business taking on staff) go through `least_wage`. Nothing else changed.

**Tests, each seen to fail first:** `test_the_dial_for_the_home_loan_is_off_and_is_one_of_the_rtr_worlds_own`, `test_with_a_new_home_loan_they_stay_when_the_job_pays_no_more_than_the_side_hustle`, `test_with_that_dial_on_a_home_loan_less_than_half_paid_off_sends_them_to_the_first_job_as_it_did`, `test_a_small_business_weighs_a_home_loan_by_the_same_rule` (both ways). Two more hold what did not change and fail under their breaks: `test_with_a_home_loan_they_take_a_job_that_pays_more_as_anyone_with_a_side_hustle_does`, `test_a_personal_loan_still_sends_someone_with_a_home_loan_to_the_first_job_offered`. The older test of the three loans now runs the personal and the business loan only.

**Whole small towns.** Forty towns of 200 exactly as now shipped (seeds 1 to 20, map and none), fourteen years under the weekly checks: every one clean. Job offers turned down for a side hustle: 23,609 across the forty (815 before this ruling). That is offers, not people: a maker whose side hustle pays more turns down the same sort of offer week after week. 2,633 homes taken by the bank (2,577 before). No newcomer bought. The whole-town tests now run seeds 17 and 18 on the map and 10 and 18 with none (the old pairs no longer reached "a maker became a company" on the map); between them they reach every rule of the stages before, the one that was missed until now as well, and every rule of today including this one ("owing most of a home loan, a maker turned down a job that paid no more than the side hustle").

**Checked:** 1,087 tests pass, run fresh. 134 rules broken on purpose (eight of them this ruling's), every break caught. Old-rules seed 74 still `08251209eb136522`, 180,377 events. With `home_loan_presses=true` three small towns (seeds 3 and 17 on the map, 16 with none) are the towns merged at `9d56400`, event for event; with the five dials of the afternoon at their old values the same three are still the towns of `develop` before today.

**Three full towns as shipped, under the weekly checks: every check clean.** Seeds 1 and 2 never reached the failure line in 60 years (this afternoon they failed in years 45.0 and 49.75). Seed 3 failed in year 50.25 (this afternoon 59.33).

**Forty full towns, 60 years, no weekly checks (batch `rtr/batches/homeloan1811`, code `43e8ed096cbab489`): none crashed.** 28 failed, in year 36.0 at the earliest and 56.27 at the latest, middle 44.9 (this afternoon: 29 failed, 34.75 to 59.5, middle 48.8). 12 never reached the line (this afternoon 11). Town by town: 18 lasted longer than this afternoon, 16 not as long, 6 the same.

**What the ruling cost. This is the finding of the evening and it is not good news.** This afternoon four of the forty (towns 4, 9, 15, 31) ended sixty years with nearly everyone in work and a wage of $601 to $872: the only towns so far in which the RTR world looked as if it worked. With this ruling none of the forty does. The same four towns, wage and share with no job, afternoon then evening:

| | year 10 | year 20 | year 30 | year 40 | year 50 | year 60 |
|---|---|---|---|---|---|---|
| town 4, afternoon | $879, 6% | $760, 5% | $767, 2% | $779, 3% | $801, 3% | $801, 4% |
| town 4, evening | $812, 4% | $521, 8% | $304, 22% | $141, 37% | $66, 39% | $30, 27% |
| town 9, afternoon | $818, 3% | $821, 1% | $821, 1% | $821, 1% | $821, 3% | $834, 2% |
| town 9, evening | $842, 1% | $648, 17% | $403, 10% | $213, 25% | $104, 37% | $50, 41% |
| town 15, afternoon | $915, 0% | $911, 1% | $921, 1% | $919, 1% | $918, 1% | $872, 5% |
| town 15, evening | $749, 14% | $444, 18% | $241, 17% | $115, 21% | $55, 26% | $24, 22% |
| town 31, afternoon | $846, 10% | $836, 1% | $837, 1% | $838, 1% | $808, 9% | $601, 11% |
| town 31, evening | $938, 0% | $830, 12% | $560, 15% | $331, 33% | $175, 45% | failed, year 53.25 |

"No job" counts everyone without a job, those living on a side hustle among them. Of the twelve towns that never reached the line this evening, the best wages at the end are $190 (town 35, 37% with no job) and $97 (town 37, 13%); the other ten end at $24 to $72.

The middle town of the forty is nearly what it was this afternoon: wage $842 and $842 at year 10, $635 and $620 at year 20, $390 and $370 at year 30, $217 and $205 at year 40. The ruling changed the best towns, not the usual one.

**Why: not known.** One rule read in the code looked as if it could be the cause: a firm short of customers, with no vacancy, cuts its wage by 2% whenever more than 5% of the town has no job (`corporate.py`, "cutting when there is a queue"), and that 5% counts makers who are living on a side hustle and turning jobs down. Tried in a scratch copy, NOT in the repository: count as the queue only those who would take the firm's wage. The four towns again, 60 years, no weekly checks, wage and share with no job:

| scratch trial | year 10 | year 20 | year 30 | year 40 | year 50 | year 60 |
|---|---|---|---|---|---|---|
| town 4 | $823, 4% | $837, 2% | $862, 3% | $880, 2% | $880, 3% | $881, 3% |
| town 9 | $842, 1% | $613, 14% | $552, 11% | $560, 11% | $563, 8% | $567, 8% |
| town 15 | $749, 14% | $444, 18% | $263, 20% | $282, 14% | $239, 27% | $114, 41% |
| town 31 | $938, 0% | $902, 14% | $818, 10% | $821, 12% | $820, 16% | $769, 24% |

In towns 4 and 31 the wage holds; in town 9 it falls to about $560 by year 30 and holds there; in town 15 the slide is slower but does not stop. So the wage cut "when there is a queue", reading makers who would turn the job down as part of the queue, is most of the slide in three of these four towns and not all of it in any but two. (I first read town 15 alone and nearly wrote that the rule explains nothing: the other three came in ten minutes later.) In all four the share unhappy still climbs, to 61% to 87% at year 60: the wage holding is not the town working. A SCRATCH TRIAL: four towns, no tests, no weekly checks, not run on the other thirty-six, nothing of it in the repository. It is a question for Jason, not a fix: does someone living on a side hustle, who would turn the job down, count in the queue that lets a firm cut its wage? FOR JASON, next.

**Not done for this ruling:** a fresh review. The change is one test in one function, behind a dial; the review of the afternoon covered the function and both doors.

## Still to do

The home loan ruling is built and checked, not committed. Waiting on Jason: the commit; then the question of who is in the queue when a firm cuts its wage.
