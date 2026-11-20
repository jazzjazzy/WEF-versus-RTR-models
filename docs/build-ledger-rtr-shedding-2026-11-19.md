# Build ledger: a firm that is losing money lets its longest-serving staff go (RTR world, 19 November 2026, afternoon)

Branch `feature/rtr-loss-sheds-staff`, cut from `develop` at `934abc8` in the public repository. Nothing committed: that waits for Jason's word.

No plan document: one rule from one answer, built test first. This ledger is the record.

Format of a ruling of mine: `Ruling: what ; why ; cost if wrong`.

## Where this came from

The morning's ruling ("Old staff members still stay on the same pay rate") left one thing uncured, traced in that day's first ledger: where wages have been bid up past what the work brings, a firm cannot bring its wage bill down, and may fail. Two questions were put to Jason, with figures from the town traced there (staff on $1,127 a week while the firm offered $1,058; the head counts were mine): may a firm let go staff on the old rate to take on newcomers on the new one, and when some must go, do the newest or the dearest go first?

He answered with a rule of his own. His words:

> "Okay. let me get this straight so if we have five staff members in a business and we have debts of Say $2,000, we will sack the oldest staff member until the value of the total wages is less than the debt. Before we hire new staff"

Handed back to him with his numbers (my reading, said to him: the $2,000 is what the firm loses each week, and "oldest" is longest-serving): five staff on $1,127 is $5,635 a week; the work brings in $3,635; as the model stood it keeps all five and loses $2,000 a week until it fails. Swapping one for a newcomer at $1,058 saves $69 a week, all five $345, and does not save that firm. His version: let the longest-serving go until the wages fit what the work brings in (two go: $3,381 against $3,635), and hire nobody new until then. Told him the catch, untested: with fewer staff a firm can do less work, so what it takes in may fall too.

Asked: "Is that the rule you want: a firm losing money sheds its longest-serving staff until wages fit?" His answer: "Yes, that rule" (the wording is my button's).

## As it stood

A firm let nobody go for losing money. It let people go for want of work (`labour.labour_market`, step 1) or when it could not pay them that week (`corporate._shed_unpaid`), the last hired first in both. A small business did the same (`rtr_makers.hire_staff`, `pay_staff`).

## Built

(as it stands after the counts and the review below) the quarterly review notes a week's share of the loss of a firm in debt (`Firm.loss_to_cover`); `labour.let_go_for_loss`, the first thing in the next week's hiring; `labour.first_to_go`, used wherever a firm or a small business lets someone go; a firm event `staff_shed` (how many, their pay a week, the week's share of the loss); the dials `loss_sheds_staff` and `longest_serving_first`, both the RTR world's own; `rtr/settings.json` made again (two lines added; `wef/settings.json` untouched).

Ruling, AS FIRST BUILT AND WRONG (overturned by the count and by his ruling, below): "losing money" is a loss over the quarter just ended, whoever the firm ; his word was "debts" and I read it as a loss ; "one that misses by a dollar lets one person go". (A loss turned out to be the ordinary quarter: see "The review".)

Ruling, as it stands (his: "No, only if in debt"): a firm lets people go for a loss only if it made a loss over the quarter AND owes the bank. The loss is the quarter's (the profit the review already works out, below nothing); "in debt" is owing the bank anything at all (`firm.loan` above nothing) on the day of the review ; that is what I told him the answer would mean ("it lost money and also owes the bank") ; a firm with a small loan and plenty of cash still sheds, and a firm with no loan that is running out of cash does not (the rule for a firm that cannot pay its wages catches it later).

Ruling: it is not "short of what the shareholders expect" ; a firm growing more slowly than its owners want is not losing money ; a firm squeezed by its shareholders keeps everyone, where he may have meant it to shed.

Ruling: the firm lets go until what those let go were paid a week covers a week's share of the loss (the quarter's loss over its thirteen weeks, rounded up) ; his example: $2,000 a week lost, two go on $1,127 ($2,254) ; "less than" is read as "covers": at exactly the loss it stops.

Ruling: the longest-serving is the first in the firm's list of staff, which is kept in order of hiring, whatever they are paid ; "the oldest staff member" ; under the morning's rule they are usually the dearest, and not always (a rise lifts everyone under the new rate to it).

Ruling: never the last of its staff ; a firm with nobody cannot work, and a start-up already keeps one worker while it finds customers ; a firm whose loss is bigger than its wage bill sheds down to one and goes on losing.

Ruling: executives and the person in charge are not let go by this rule, and their pay is not counted toward the loss covered ; "staff members" ; a firm in trouble keeps its bosses. (Their number already follows the staff: one for every 25.)

Ruling, AS FIRST BUILT AND WRONG (kept as the record; overturned by the count below): "Before we hire new staff" is a hold on hiring. From the day it sheds, the pay of its staff between them may not pass what it is that day; it takes on only whom that leaves room for; the hold is lifted at the first quarterly review without a loss ; without a hold the labour market fills the same jobs the next week ; a firm that cut too deep cannot grow back for at least a quarter. (It could not grow back at all: see "The hold on hiring, counted and taken out".)

Ruling, as it stands: "Before we hire new staff" is an order, not a hold. The letting go comes first, at the quarter's review; from the next week the firm takes people on again as it needs them, at its rate for new hires ; that is what his words say, and eighty small towns fare as well or better with it than before the rule, where the hold doubled the share with no job ; the firm may take on again, at its rate for new hires, the very people it let go (they lose the rate they kept), and where its rate is no lower than theirs the letting go saves it nothing. FOR JASON if he sees the same people let go and taken back.

Ruling: a firm that has never had a customer lets nobody go for a loss ; nothing else at the review acts on such a firm either ; none.

Ruling, AS FIRST BUILT (overturned by the review): the letting go is done at the review, in the quarter's last week.

Ruling, as it stands: the review only notes what is to be covered; the letting go is the first thing in the next week's hiring, before the firm counts the jobs it has going ; "Before we hire new staff", and done in the quarter's last week it put everyone let go into that week's record as out of work (the reviewer measured the share with no job 7 points of the town higher on a quarter's last week than on the weeks either side) and in front of the quarter's other decisions as jobless, though half were back in days ; someone let go may be taken on again by the same firm in the same hour, at its rate for new hires.

Ruling: **whoever an employer has to let go, the longest-serving goes first**: for want of work and when it cannot pay as well, at firms and at small businesses (`longest_serving_first`) ; I told him that his rule answered my second question too, who goes first ; if he meant it only of a firm losing money, every layoff in this world now takes the old hands first. FOR JASON, one line.

Ruling: a small business does not shed for a loss ; it has no quarterly review like a firm's, and it already lets go whom its till cannot pay ; none seen.

Ruling: those let go are recorded as laid off, with one event for the firm ; no new kind of leaving for the pages to learn ; a reader of one person's record cannot tell this layoff from one for want of work without the firm's event.

Ruling: both rules are the RTR world's alone ; as with the morning's ; whether the WEF world's employers should follow is his.

Tests (`tests/test_rtr_rulings.py`): eighteen. Seventeen failed before the rule existed; one is a guard (`test_a_firm_that_has_never_had_a_customer_sheds_nobody`), to be proved by breaking the rule.

## What the change did to older tests

- The whole towns of the stages before, and the two pinned records of an RTR town with stage 2 off, are run as the world was when their seeds were picked: the two new dials are off for them (`conftest.BEFORE_THE_LINE`).
- Two tests of 18 November asserted that a small business lets the last hired go. They now say they are the rule with the new dial off; the ruling's own tests hold it on.
- `test_the_review_that_cuts_the_rate_leaves_the_staff_on_theirs` gave its firm a loss, and under this rule the review now lets one of its three staff go. Its firm is now short of its target without a loss, which is what the test was about.

## The hold on hiring, counted and taken out

The first build held a firm from hiring after it shed. Eighty small towns (seeds 1 to 40 on a 7 by 7 map and with no map, 200 people, fourteen years, no weekly checks; `outcome_small.py`), each line the same eighty seeds:

| | Mean share with no job, map | no map | Reached the 90% line, map | no map |
|---|---|---|---|---|
| Before this rule (develop, `934abc8`) | 8.6% | 12.3% | 0 of 40 | 2 of 40 |
| The rule as first built, with the hold | 20.1% | 23.6% | 1 of 40 | 2 of 40 |
| Only the shedding and the hold (`longest_serving_first` off) | 19.8% | 21.6% | 1 of 40 | 2 of 40 |
| Only who goes first (`loss_sheds_staff` off) | 9.1% | 12.4% | 0 of 40 | 0 of 40 |
| The shedding without the hold (a scratch copy; now the code) | 8.6% | 8.7% | 0 of 40 | 0 of 40 |

With the hold, more people were out of work in 72 of the eighty towns than before the rule, and fewer in 7. One town was traced (seed 38 on the map; `trace_shed.py`): four firms shed six people in their first year; from then some firm was held and wanting staff in 40 weeks of the first year and every week after; the jobs wanted and not opened were 43, 62, 150 and 255 at the ends of years 1 to 4, with 90% of the town out of work by year 4. A firm held from hiring serves fewer customers, takes in less, loses money again, and is held again: it never has the quarter without a loss that would free it.

Told to Jason as found, with the table, before anything was changed: the fault was in my reading of "before we hire new staff", not in his rule. The hold was then taken out test first (`test_after_shedding_for_a_loss_it_takes_people_on_again_as_it_needs_them_at_its_rate_for_new_hires` RED then GREEN) and `Firm.bill_cap` with it.

No weekly check was added for this rule: there is no standing state for one to hold. The rule is held by its tests and by the count of how towns fare.

## Checks on the second build (any firm with a loss, no hold): superseded, kept as the record

- The two new dials off: four small towns (seeds 3 and 17 on the map, 10 and 16 with no map, ten years) give the records `develop` gave before the change, event for event.
- The WEF world's old town: `08251209eb136522`, 180,377 events, as before.
- The code as it stands gives the same town as the scratch copy the "without the hold" row of the table was run on (seed 3 on the map, ten years: `193757b771a85969`, 30,647 events from both).
- Sixty small towns (seeds 1 to 30 on a 7 by 7 map and with no map, 200 people, fourteen years) under the weekly checks: **no problem in any.** A firm that lost money let its longest-serving staff go in all sixty: 3,134 times on the map and 3,572 with no map, about once a quarter in each town.
- The whole-town test's seeds were picked again from those sixty: 4 and 22 on the map, 8 and 15 with no map. Between them they reach every rule of the stages before, of 18 November, of that morning and this one (with no map, all but a block made into plots), and none has more than half its people out of work for more than 87 of its 728 weeks.
- A town test of stage 1b that places homes by hand in one particular town is now run in the town it was written for (the new dials off): under the rule that town had no free plot for its hand-placed home.
- Heat, for the record: these runs were made three and four at a time on a desktop that reached 91°C doing it.
- Broken on purpose in a scratch copy: **217 breaks, all caught** (196 from before this rule, 14 for the shedding and 8 for who goes first, less one that turned out not to be a break: a firm that exactly breaks even has a loss of nothing, which lets nobody go whether or not the check for it is there). Three slipped through first and each got a test: the week's share of the loss rounded down, not up; the pay counted being the firm's rate for new hires, not what those let go were on; and a small business that can pay one of two still letting the last hired go. Seven breaks written for the hold on hiring went out with it.

## The review, 19 November 2026, afternoon

A reviewer with no part in the build, held to two processes because of the heat. Nothing Critical; the books, the WEF world and the dials-off path sound. Four Important, five Minor. Its scripts and outputs are in the kept-scratch folder (`review_shed/`). Its two main claims were checked with my own count (`verify_shed.py`, seeds 3 and 5 on the map, fourteen years) before anything was changed.

- Final: Ruling by Jason, then fixed (Important): **the rule as first built was a revolving door.** A loss over the quarter is the ordinary quarter in this model. My count, two towns, any firm with a loss: a loss at 62% of reviews; a shedding at 55%; 208 of 283 losses by a firm owing nothing and 232 by a firm holding cash for a year of that loss; 1,027 people let go, 52% of them back at the same firm within four weeks (245 on less pay, 292 on the same or more). The reviewer's twelve towns: 18,951 layoffs with the rule against 12,985 without; loans called on those laid off 1,441 against 922; the lower wage bill covered a middle 2.3% of the weekly loss; how the towns fared not clearly moved. The firm still wants the same number of people, so it lets them go and takes them back. Put to Jason with the counts: "A firm with cash and no debts loses a little in a quarter. Does it let anyone go?" His answer: **"No, only if in debt"** (the wording is the button's; his own word for it from the start was "debts"). The ruling "as it stands" above. The same two towns after: a loss at 42% of reviews; a shedding after 9%; 307 people let go, 36% back within four weeks (70 on less, 41 on the same or more).
- Final: fixed (Important): **an executive put back on the staff was added at the end of the list, and so treated as the newest**; the longest-serving hand in the firm was passed over. In the reviewer's twelve towns 49% of the choices of who goes were not the longest-serving, by a middle 91 weeks. `labour.demote` now puts them back by when they joined (RTR with the dial on; the WEF world's order is untouched, and a test holds it). `test_an_executive_put_back_on_the_staff_takes_their_place_by_when_they_joined` RED then GREEN.
- Final: fixed (Important): **the letting go landed in the quarter's last week** (the ruling above). `test_the_letting_go_is_the_first_thing_in_the_next_weeks_hiring_and_then_it_takes_people_on` RED then GREEN.
- Final: fixed (Minor): tests for three breaks the reviewer planted and the tests missed (the bosses' pay worked out again after people go; who goes for a loss not following the other dial; the order of the cut and the letting go, since settled by moving the letting go to the next week). A town test of stage 1b given only the two new dials off, not the morning's as well. Two docstrings that still said the last hired goes.
- Final: minor (deferred): pay held back for shares. Someone let go is paid what was held back in cash and misses that quarter's shares, as anyone leaving does.
- Final: minor (deferred): no town run reaches a firm or small business that cannot pay its wages, so the longest-serving going first there is held by its tests alone.
- Final: Ruling: start-ups shed ; a firm with a first customer is a firm, and under "only if in debt" it sheds only once it owes the bank ; a young firm that borrowed to start lets people go in its first loss.
- Final: Ruling: executives are not let go by this rule, staff taken over count as the buyer's newest, and the longest-serving go first for want of work and at small businesses too: as above, and each his to change. The reviewer declined to judge them.

## How eighty small towns fare, all versions

Seeds 1 to 40 on a 7 by 7 map and with no map, 200 people, fourteen years, no weekly checks (`outcome_small.py`).

| | Mean share with no job, map | no map | Reached the 90% line, map | no map |
|---|---|---|---|---|
| Before this rule (develop, `934abc8`) | 8.6% | 12.3% | 0 of 40 | 2 of 40 |
| Any firm with a loss, with the hold on hiring | 20.1% | 23.6% | 1 of 40 | 2 of 40 |
| Any firm with a loss, no hold (the revolving door) | 8.6% | 8.7% | 0 of 40 | 0 of 40 |
| **Only a firm in debt, let go at the next hiring (as it stands)** | 9.5% | 12.4% | 0 of 40 | 1 of 40 |

As it stands the rule leaves small towns about where they were before it. The revolving door had fewer people out of work in towns with no map, and no town at the line: letting everyone go each quarter and taking them back at the rate for new hires works as a pay cut for the old hands, at the price of half as many layoffs again and loans called on people who were back at work in days. That is said to Jason, not hidden; his ruling stands.

## Checks on the rule as it stands

- Tests: **1,156 pass** (full run, 5 minutes 15 seconds), 26 of them for this rule.
- The two new dials off: four small towns give `develop`'s records, event for event (run again after the last change).
- The WEF world's old town: `08251209eb136522`, 180,377 events (run again after the last change).
- Sixty small towns (seeds 1 to 30 of each kind, fourteen years) under the weekly checks: **no problem in any.** A firm in debt let its longest-serving staff go for a loss in all sixty: 1,007 times on the map and 605 with no map (3,134 and 3,572 under the first build).
- The whole-town test's seeds picked again from those sixty: 16 and 30 on the map, 2 and 29 with no map. Between them they reach every rule asked of them (with no map, all but a block made into plots), and none has more than half its people out of work for more than 73 of its 728 weeks.
- Broken on purpose in a scratch copy: **228 breaks, all caught** (196 from before this rule; 20 for the letting go, 8 for who goes first, 4 for the place of someone put back on the staff). One slipped through on the last pass and got an assertion: a firm in debt noting something to cover in a quarter it made money.

## Full towns on the rule as it stands (19 and 20 November)

Committed on Jason's word ("Yes, publish it") as `7d7788f`, merged into `develop` as `644c166`. Run from that commit on his second machine, which has 32 processors; his word on the load there: "Can you do more than one processor? You've got 32 and 128 gigs of RAM". The tests pass there too: 1,156 in 3 minutes 8 seconds, on Python 3.13.

**Forty full towns** (seeds 1 to 40, the world as it ships, no cap on people, sixty years, thirty at a time, no weekly checks; `python3 batch.py debt1911 --seeds 1-40 --jobs 30 --quiet`): none crashed. 4 reached the 90% line, all late: seed 23 in year 52.0, seeds 24 and 5 in year 59.3, seed 27 in year 59.6. 36 never did. Those 36 at year 60:

| | lowest | middle town | highest |
|---|---|---|---|
| staff paid a week, on average (`wage`) | $390 | $715 | $928 |
| the rate offered to someone new (`wage_offer`) | $111 | $552 | $907 |
| share with no job | 0% | 0% | 23% |
| share unhappy | 32% | 75% | 88% |

Beside the runs before:

| | reached the 90% line | ended on a working wage |
|---|---|---|
| the home loan ruling (18 November, evening), forty towns | 28 of 40 | none |
| the morning's rulings, stopped at twenty-seven towns | 1 of 27 | 26 of 27 |
| the morning's rulings and this rule, forty towns | 4 of 40 | 36 of 40 |

Towns followed since 18 November, at year 60: town 4, $30 a week the evening of 18 November, now $553 paid, 0% with no job, 68% unhappy; town 9, $50, now $672, 13%, 77%; town 15, $24, now $773, 0%, 75%; town 31, failed in year 53, now $928, 0%, 87%.

Town 9 was run again in full to look at on the town view. Its first jump in people with no job, 0% to 19% in year 4, was traced in its record: the map's last empty spot went in week 200; with nothing left to build, the landlord firms went from 277 staff in week 196 to 118 in week 220 (137 builders let go in weeks 204 to 222); jobs open fell from over 300 to none by week 204; no newcomer came after week 203; 1,074 missed payments, 331 missed home loan payments and 79 homes taken back followed in those eighteen weeks. The rule of this ledger let nobody go in those weeks. It is the end of the building boom, not this rule.

**Three full towns under the weekly checks** (seeds 1, 2 and 3, sixty years, the same settings): every check clean, all 3,120 weeks, in all three. Each is the same town as in the forty: the same people, pay, share with no job and outcome. None reached the line. At year 60:

| | seed 1 | seed 2 | seed 3 |
|---|---|---|---|
| people | 919 | 924 | 900 |
| staff paid, on average | $755 | $685 | $787 |
| the rate offered to someone new | $500 | $438 | $594 |
| with no job | 7% | 21% | 0% |
| unhappy | 85% | 86% | 70% |
| the morning's rulings, before this rule | $622; 0%; 66% | $740; 0%; 62% | $720; 0%; 72% |

Three towns are too few to lay the change on this rule. Nothing here is traced, nothing is tuned, and "never reached the line" is not "works": in the middle town of the forty, three in four are unhappy at year 60, and the gap between what staff are paid and what a newcomer is offered is wide (town 9: $672 against $242).

- Ruling: the weekly checks of a full town skip only "population above the cap" when the cap is 0 ; 0 means no cap, Jason's rule of 16 November, and that check (`tests/test_town_invariants.py::check_week`) assumes a cap: on the first try it called every week a fault and the script stopped at week 51 ; if wrong, a town over a cap would pass, but these towns have none. Every other check was made. The suite's own check never meets a town with no cap, since every test town has one. Teaching it that 0 means no cap is a change to a test, left for Jason's word.

## Still to do

For Jason, when he chooses: whether the longest-serving should go first for want of work and at small businesses too, or only at a firm in debt; whether "in debt" should be owing the bank anything, as built, or owing more than the firm has in cash; the count above that the second build, the revolving door, left fewer people out of work in towns with no map than his rule as it stands; and the weekly check that assumes a cap.

For Jason, when he chooses: whether the longest-serving should go first for want of work and at small businesses too, or only at a firm in debt; whether "in debt" should be owing the bank anything, as built, or owing more than the firm has in cash; and the count above that the second build, the revolving door, left fewer people out of work in towns with no map than his rule as it stands.

