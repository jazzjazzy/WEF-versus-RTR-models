# Build ledger: Jason's rulings of 19 November 2026 (RTR world)

Branch `feature/rtr-line-for-a-job`, cut from develop `1779244`. Nothing committed: that waits for Jason's word.

Two notes carried over from the ledger of 18 November: its last line ("not committed. Waiting on Jason") is out of date. The home loan ruling was committed on his word on 19 November (`910345c`) and merged into develop (`1779244`), with 1,087 tests passing on develop and the old WEF town unchanged.

No plan document: three rules from one answer, each built test first. This ledger is the record.

Format of a ruling of mine: `Ruling: what ; why ; cost if wrong`.

## Where this came from

With the home loan ruling ("No, stay") the four towns of forty that had ended on a working wage no longer did. One rule read in the code could cause it: the WEF world's rule that a firm short of profit, with no job going, cuts its wage by a fiftieth when more than a twentieth of the town has no job (`corporate.review_firm`). That count took in people living on a side hustle who would turn the job down. The rule is his, of 12 November ("cutting when there is a queue"); the fiftieth and the twentieth are mine.

Put to him first as "Are people who would turn the job down part of the queue that lets a firm cut its wage?". He sent it back: "Sorry, I don't understand the question... I'm not sure what you mean by Q. And if people turn down jobs, why would you cut their wages?" Put again as a shop paying its staff $800 that wants to pay $784, and sixty people in town with no job who all make more than that from side hustles.

His words, 19 November 2026:

> "Okay, so if people have a side hustle that pays more than a wage for a job, then why would they get into the queue? I'm confused at that. I would assume they wouldn't even apply for the job. Unless they're unhappy. and wanted to get out of this hard hustle. So If a side hustle person is Actually happy they will never apply for a job Until they become unhappy then they might want to do something different. That should reduce the number of people in the queue. If the queue is long, then the employer can ask for pay less wages to the newcomers. Old staff members still stay on the same pay rate. Just a question can someone who's employed by the firm actually get a pro pay increase. If not, then I don't think it's fair that employers can actually reduce wages."

His question, answered from the code before anything was built: yes. A firm that cannot fill a job for two weeks, and did not lose money last quarter, bids its wage up a fiftieth and everyone on its staff gets it (`labour.labour_market`, step 5; `firmops.sync_pay`). Staff look around (one week in ten; one in two if their bills are not met) and move to a firm paying a twentieth more, or any more if squeezed (step 3). Someone can be made an executive on two and a half times the staff wage. A cut, as it stood, was also everyone's.

Played back to him as three rules, with the gaps I had filled named. His answer: "Yes, build it" (the wording is my button's).

1. Someone happy on a side hustle that pays more than the job does not apply. They are not in the line.
2. Someone unhappy on a side hustle does apply. They are in the line. (My reading of "get out of this hard hustle", said to him: they take the job even if it pays a bit less; $700 from the side hustle, offered $600, they take it.)
3. When the line is long the firm can pay new hires less. Staff already there keep their pay. (Staff on $800; the next person hired starts on $784; everyone hired before stays on $800.)

Said to him as mine: "long" keeps my number, more than 5 in every 100 people in town; "unhappy" is the model's own measure; a later rise lifts anyone below the new rate and cuts nobody; the RTR world only, the WEF world left as it is.

## Rules 1 and 2: who is in the line

As it stood: `town.jobless_share()` counted everyone with no job, whoever they were.

Built: `labour.reservation_wage` (the one formula, which the labour market, the small businesses' hiring and the line now share; it was written out three times); `labour.in_the_line(town, wage)`; `corporate.line_share`; `review_firm` asks the line at the lower rate; `rtr_makers.least_wage` lets an unhappy maker through; the dials `line_is_who_would_take` and `unhappy_makers_apply`, both the RTR world's own.

Ruling: the line for a firm's job is everyone out of work who would take it, by the same test the labour market uses when a job is offered, not only people with side hustles ; his reason is "they wouldn't even apply for the job", and that is as true of someone holding out for more than the firm pays as of someone with a side hustle ; fewer cuts than he meant in a town where the jobless would rather wait than take less.

Ruling: the line is counted at the lower rate the firm would move to, not at what it pays today ; the cut is what new hires would be offered, so the line that matters is those who would come for it ; someone who would take $800 and not $784 is not counted, which makes each step down a little harder than the one before.

Ruling: "long" is still more than a twentieth of the town (`wage_cut_unemployment`, my number of 12 November), now counted over the line and not over everyone with no job ; said to him and not overruled ; the bar was set for a bigger count, so cuts are rarer than a bar chosen for this count might make them. FOR JASON if the towns show it matters.

Ruling: the owner class is never in the line ; in the labour market those living on dividends do not apply (stage 1) ; none.

Ruling: whether the job can be reached on the map is not asked ; someone out of reach may move for a job ; a few people counted who would not in the end come.

Ruling: a firm still cuts only with no job going, as before ; his words today do not touch it ; none.

Ruling: his "Yes, take it" of 18 November stands: someone happy on a side hustle still takes a job that pays more than it ; read alone, today's "If a side hustle person is Actually happy they will never apply for a job" would end that, but the rule played back to him carried "that pays more than the job" and he said yes to it ; happy makers leave for better paid jobs where he meant them to stay. FOR JASON, one line.

Ruling: unhappy is the model's own `agent.happy`, the measure his 90% failure line counts (wellbeing under a half: income against their costs, cash in hand, debt, needs met, the state of their things) ; said to him ; it measures being short, not the side hustle being hard, and the model has no measure of how hard a side hustle is.

Ruling: someone unhappy on a side hustle takes a job as anyone out of work does, at what they would work for with nothing else, and keeps the side hustle for their spare hours as anyone with a job and a side hustle does ; "wanted to get out of this hard hustle ... might want to do something different" ; if "get out of" means closing it, they keep something he meant them to drop.

Ruling: a small business hiring goes by the same rule as a firm ; both doors go through `least_wage` (18 November's whole-town finding) ; none.

Tests (`tests/test_rtr_rulings.py`): fifteen for these two rules. Fourteen failed before the rule existed; one is a guard (`test_an_unhappy_maker_still_turns_down_a_job_under_what_they_would_take_with_nothing_else`), to be proved by breaking the rule.

## Rule 3: "Old staff members still stay on the same pay rate"

As it stood: a firm had one wage. `firmops.sync_pay` set every staff member's pay to it on any change, pay day paid `firm.wage` to each, and everything a firm reckoned (its wage bill, what a unit costs it to make, what its bosses are paid) was reckoned from that one number.

Built (as it stands after the fresh review's fix pass, below): `firm.wage` is now the rate for those a firm hires; each person on its staff keeps their own (`agent.wage`, which was already there and already recorded each week). `Firm.own_rates` (set when a firm is made, from the dial); `Firm.staff_bill()` and `Firm.staff_pay()`; `sync_pay` lifts and never cuts; `corporate._pay_wages` pays each their own; `Firm.payroll`, `exec_pay`, `ceo_pay` and the building work booked in `production.operate` follow what is paid; `labour.promote` notes the rate someone was on as staff (`agent.staff_wage`) and `labour.demote` gives it back; `labour.hire` can take a rate of the person's own; `town.staff_pay()` and the RTR world's weekly measure `wage_offer`; the small businesses (`rtr_makers.hire_staff`, `wages_due`, `pay_staff`, `become_company`); the dial `staff_keep_pay`. `rtr/settings.json` made again (three lines added; `wef/settings.json` untouched). What a firm reckons ahead (`make_cost`, `unit_build_cost`, `production.project_cost`, `rtr_owning._firm_upkeep`, and through them selling outside, making or importing, the price it asks makers in town) and the going wage (`town.typical_wage`) are at the rate offered, as they were before today.

Ruling: a rise lifts anyone under the new rate to it and touches nobody else ; said to him ("anyone below the new rate is lifted to it. Nobody is cut") ; if he means a rise is everyone's, staff above the new rate miss a fiftieth each time.

Ruling, AS FIRST BUILT AND WRONG (kept here as the record; overturned by the fresh review, below): what its labour costs a firm is what it pays its staff, the average of their rates: for what a unit costs to make, what a unit costs to build, upkeep, and so the export decision and the price it asks makers in town ; reckoned at the rate it offers, a firm paying $800 would think its goods cost what a $600 worker makes them for, and sell under cost ; the next worker costs the offer, not the average, so at the margin a firm reckons a little high. ("A little" was wrong by the whole town: see the review.)

Ruling, as it stands: what a firm reckons AHEAD is at the rate it offers: one more unit made, a unit built, a home kept up, and so whether to sell outside, whether to make or import, and the price it asks makers in town. What it PAYS follows each person's own rate: the wage bill, pay day, the building work booked each week ; the next unit is made by whoever it would take on to make it, and his rule exists so that an employer with a long line can take people on for less: reckoned at what its staff keep, the cut changed nothing the firm decided ; a firm whose staff are all on more than the work brings goes on with them and loses money on that work until they leave or it fails, where in the WEF world a cut would have brought their pay down. FOR JASON, as a question about people: may a firm let go staff on the old rate to take on newcomers on the new one?

Ruling: an executive is paid two and a half times, and the person in charge their multiple of, what the staff are paid on average, not of the rate offered ; they are "old staff" too, and on the offer every cut for newcomers would have been a cut for bosses already there while the staff they manage kept theirs ; the bosses' pay drifts down as old staff leave, with nobody deciding it.

Ruling, AS FIRST BUILT AND WRONG (overturned by the fresh review): the going wage in town (`typical_wage`) is the average of what staff are paid, not of what firms offer.

Ruling, as it stands: the going wage in town (`typical_wage`) is what a job pays someone taken on now: the firms' rates, each counted once for every one of its staff, as before today. It is what a new firm starts on, what a small business pays someone new and prices its hour at, and what an hour of anyone's time is valued at. What staff are paid is a second number, `town.staff_pay()`, kept for the record ; "the employer can ask for pay less wages to the newcomers": a new employer is an employer, and paying newcomers the old hands' average turned his rule round (the review counted new firms opening at a middle 1.55 times what firms were offering in one small town) ; an hour of a person's own time is valued at what a new job pays, not at what people in work get.

Ruling, AS FIRST BUILT (overturned by the fresh review): an executive put back on the staff gets what its staff are paid on average ; a few dollars. (The review counted 189 such demotions in eight small towns: 11 came back on less than the staff rate they had kept, the worst by a fifth.)

Ruling, as it stands: an executive put back on the staff goes back on the staff rate they were on when promoted, or the firm's rate if that has since passed it ; "Old staff members still stay on the same pay rate" ; a rise the staff had while they were a boss reaches them only if it took the firm's rate past theirs.

Ruling: staff taken over with a failed firm start on the buyer's rate, as they did ; a new employer, and they were about to have no job ; a cut for people who did not choose to move.

Ruling: someone who leaves and is hired again starts on the rate for new hires ; they are a new hire ; none.

Ruling: a firm short of money still lets go the last hired first, who are now its cheapest ; unchanged, and the usual rule ; a firm in trouble sheds the staff who cost it least. FOR JASON if the towns show it matters.

Ruling: pay held back for shares is the same share of each person's own pay ; it was a share of the one wage ; none.

Ruling: a small business pays someone new the going wage, as before; its staff keep what they are on when the going wage falls and are lifted when it rises; if till and owner cannot pay what they keep, the last hired is let go (the rule it already had for a short till) ; a small business is an employer, and his rule is about employers ; a business that could have kept someone on at the lower going wage lets them go.

Ruling: when a small business becomes a company its staff keep their rate ; the same employer under a new name ; none.

Ruling: all three rules are the RTR world's alone ; said to him ; the rule being changed is the WEF world's own (12 November), and whether its employers should follow rule 3 is his to say. FOR JASON, later, as its own question.

Tests: twelve for the firms, six for the small businesses and the company (four failed first; two are the dial-off halves, guards). Seen to fail first: all twelve; four of six.

## What the change broke in older tests, and why

- Three tests of 18 November's ruling 3 set `firm.wage` by hand to say what a unit costs a firm to make, leaving its hand-made staff on another rate. Under rule 3 the cost follows what the staff are paid. The tests now set both (`pays_its_staff`); what they assert is unchanged.
- `rtr/settings.json` was refused by the loader for missing the three new dials, which is the refusal doing its job; made again.
- `test_a_town_as_shipped_where_every_firm_closes_still_balances`: its town no longer has a business with staff and a loan standing. A seed is picked again below.

## Weekly checks added (`tests/test_town_invariants.py::check_week`)

- No firm pays anyone on its staff under its rate (RTR, staff keep pay); where staff do not keep pay (the WEF world, or the dial off) every one is paid exactly its rate.
- Every firm knows whether its staff keep their pay (`own_rates` agrees with the dial).
- No small business pays anyone on its staff under the going wage it took as its rate.
- Nobody who stayed on the same staff since last week is paid less than they were. This is his rule stated directly, and it is asked of every person in every week of every town run under the checks.

## Eighty small towns, first build (before the review)

`scan_reach_line.py`, forty seeds on a 7 by 7 map and forty with no map, 200 people, fourteen years, under the weekly checks: no problem in any. Every new rule was reached. I reported that to Jason as "no problem in any of them". The books of those towns balanced. I had not looked at how the towns fared, and the weekly checks cannot see a town that has stopped. See the next section.

## The fresh review, 19 November 2026

A reviewer with no part in the build, given the diff, the ledger, the tests and a scratch copy. Nothing Critical for the world as it ships (no cap on people). Three Important, ten Minor. Its scripts and outputs are in the session's scratch folder (`review_line/`). I checked its first finding with my own count before acting on it; the rest are taken from its report and from what the tests show now.

- Final: fixed (Important; decisive in any town with a cap on people, which is every town the tests run): **a firm reckoned what a unit costs to make at what its staff keep, so a cut for newcomers brought no work.** After a boom in a capped town every firm has bid its rate up past the wage at which selling outside pays ($1,069.52 for food); it stops, and lets most of its staff go. On develop one cut puts everyone under that wage and it starts again in the quarter. As first built the few staff left kept their rate, the average did not move however far the rate for newcomers was cut, and the firm never took a newcomer on: the figure could fall only when someone cheap was hired, and someone cheap was hired only when the figure fell. The reviewer's trace of one town (seed 3 on the map): nine in ten with no job for four years while the one firm left cut its rate fourteen times. My own count, twenty towns of 200, fourteen years, no weekly checks (`outcome_small.py`, seeds 1 to 10 of each kind):

  | | Reached the 90% line, map | no map | Mean share with no job, map | no map |
  |---|---|---|---|---|
  | The three dials off (develop) | 0 of 10 | 0 of 10 | 7.8% | 6.6% |
  | As first built | 3 of 10 | 5 of 10 | 31.1% | 49.4% |
  | After the fix | 0 of 10 | 0 of 10 | 7.4% | 8.5% |

  The reviewer's figures for the first two rows were the same to the decimal. The fix is the ruling "as it stands" above: what a firm reckons ahead is at the rate it offers. `test_a_firm_that_cut_its_rate_sells_outside_again_though_its_staff_keep_theirs` (the reviewer's case), `test_what_one_more_unit_would_cost_a_firm_is_reckoned_at_the_rate_it_offers`, `test_building_ahead_is_reckoned_at_the_rate_offered_and_building_done_is_booked_at_what_was_paid` RED then GREEN.
- Final: fixed (Important): **"Staff wage" in every report had come to mean what the people still employed are paid, and the rate a job is offered at was recorded nowhere.** A town's wage could no longer fall when rates were cut, only when cheap people were hired, and it rose when the last hired were let go. Now the record's `wage` is `town.staff_pay()`, what staff are paid (in the WEF world, and wherever a firm pays one rate, the same number as before), and the RTR world records a second weekly measure, `wage_offer`, the going wage. `test_the_record_keeps_what_staff_are_paid_and_what_a_job_pays_someone_new` RED then GREEN. Not done: see the deferred minors.
- Final: fixed (Important): **a new firm, and a small business taking someone on, offered newcomers the old hands' average**, more than any existing firm was offering in most cases the reviewer counted. The going wage is again what a job pays someone new (the ruling above).
- Final: fixed (Minor): the record of a hire said the firm's rate for someone who kept a higher one when their business became a company. `labour.hire` takes the rate and records it.
- Final: fixed (Minor): an executive put back on the staff could lose a fifth (the ruling above). `test_an_executive_put_back_on_the_staff_is_paid_what_they_kept_as_staff`, `test_with_the_dial_off_an_executive_put_back_on_the_staff_gets_the_firms_rate`, `test_someone_who_left_as_an_executive_brings_no_old_rate_back`.
- Final: fixed (Minor): a home's value moved with whom its landlord had hired last week (by as much as 28.6% in a week in the reviewer's count): what a unit costs to build is at the rate offered again.
- Final: fixed (Minor): two older tests had been given the dial off to pass; with the going wage back at the rate offered they pass as the world ships, and the constant made for them is gone. One test's name said the opposite of half its body: renamed. A comment in `firmops.set_wage` was no longer true: rewritten.
- Final: fixed (Minor): the whole-town test's map towns reached "unhappy on a side hustle, a maker took a job" once in 28 town years. Seeds picked again from eighty (below): seven times on the map, fourteen with no map.
- Final: Ruling: **someone unhappy on a side hustle has no floor under what they will take** ; the rule as played back to him was "$700 against $600", and what was built is "as anyone out of work does", which after twenty weeks with no job is any wage at all ; it is the rule everyone else in the model lives by, and the reviewer counted it rarely (0 to 3 times in fourteen years of a small town) ; if he meant "a bit less" and not "anything", some people leave a side hustle for a wage he would have had them refuse.
- Final: minor (deferred): the pages (town page, batch page, dashboard) still show one figure, "Staff wage", and do not show the going wage; the record keeps both. The README says which is which.
- Final: minor (deferred): the line as a share of the town is recorded nowhere; `jobless_rate` still counts everyone with no job, and is no longer the number that lets a firm cut.
- Final: minor (deferred): `rtr_makers.hour_worth` still writes the reservation formula out in its own words (not behaviour).
- Final: minor (deferred): a firm's decision to sell outside is made at its quarterly review and at each change of rate; between them it can be a few weeks stale.

Declined to judge by the reviewer, ruled here:

- Final: Ruling: "long" stays more than a twentieth ; said to Jason ; in the reviewer's four towns the line kept a firm's rate 25 times against 370 cuts, because someone long out of work will take any wage and so is in the line at any rate: rule 1 seldom changes a decision. FOR JASON only if he asks why his rule 1 does so little.
- Final: Ruling: staff taken over with a failed firm start on the buyer's rate, a rise lifts only those under the new rate, the bosses' multiple is on the average (the reviewer measured it moving by at most 0.4% in a week from the staff mix alone), the last hired are let go first: all as above.
- Final: Ruling: whether the WEF world's employers should follow rule 3 is Jason's, later.

## What the fix did not cure, and why (for Jason)

After the fix, eighty small towns (seeds 1 to 40 of each kind, fourteen years, no checks): none of forty on the map reached the 90% line, and two of forty with no map did (seeds 17 and 29); with the three dials off, none of eighty. Mean share with no job: on the map 8.6% against 9.2% with the dials off; with no map 12.3% against 9.8%.

I traced seed 17 with no map three ways. In all three the firms bid their rates up from $1,000 to $1,148 in the second year (23 rises), and firms fail on their wages for years after. With the dials off, and with rule 3 alone off, a cut brings everyone's pay down, a firm or two survives, and new ones are founded. With rule 3 on, the staff keep what the boom gave them ($1,127 paid against $1,058 offered in year 6), the last three firms fail on their wages in year 7, and with nobody earning nobody founds another: no firm, 100% with no job, for the rest of the run.

That is not the fault the review found. It is what his rule does where wages have been bid up past what the work brings: a firm cannot bring its wage bill down except by letting people go, and it lets go the last hired, who are its cheapest. Two things would change it, and both are his to rule on: whether a firm may let go staff on the old rate to take on newcomers on the new one, and whether it lets go its dearest or its newest first. A town with no cap on people (the world as it ships) has outside workers to hire at $1,000, so its firms do not bid up as far; whether this bites there is what the full towns below are for.

## Checks after the fix pass

- Tests: **1,130 pass** (full run, 5 minutes 16 seconds). 43 are new today in `tests/test_rtr_rulings.py`.
- Broken on purpose in a scratch copy: **196 breaks, all caught** (134 from before today, less ten that the fix pass made meaningless, plus 53 for today's rules and 19 for the fix pass). Along the way four of today's slipped through and each got a test: exactly a twentieth counted as a long line; a firm cutting with a job going (a rule of 12 November that no test had ever held); a unit built at the wrong rate (the test asked it of a food firm, which builds nothing); and the line counted at today's rate, which my own tightening of another test had let go. One older break's text had gone stale and was refreshed. Four of today's breaks were also tried against the whole-town tests alone, and the weekly checks caught all four.
- With the three dials off, four small towns (seeds 3 and 17 on the map, 10 and 16 with no map, ten years) give the records develop gave this morning, event for event.
- The WEF world's old town: `08251209eb136522`, 180,377 events, as before.
- Eighty small towns after the fix (seeds 1 to 40 on a 7 by 7 map and with no map, 200 people, fourteen years) under the weekly checks: **no problem in any.** Reached, in towns of forty on the map and of forty with no map: a firm cut its rate and its staff kept theirs, 40 and 40 (2,323 and 2,133 times); a firm had staff on more than one rate, 40 and 40; a firm bid its rate up while some staff were on more, 40 and 38; a small business kept its staff on more than the going wage, 40 and 39; unhappy on a side hustle, a maker took a job that paid no more than it brought in, 26 and 29 (88 and 131 times); a firm short of profit kept its rate because those with no job would not take less, 11 and 11 (35 and 102 times).
- The whole-town test's seeds were picked again from those eighty: 38 and 40 on the map, 10 and 14 with no map. Between them they reach every rule of the stages before, of 18 November and of today (with no map, all but a block made into plots). The test of a town where every firm closes moved to seed 1.
- A loose check on how the test towns fare is now in the whole-town test: none may have more than half its people out of work for more than 156 of its 728 weeks (these four: 6, 9, 0 and 64).

**Three full towns as shipped (seeds 1, 2, 3; no cap on people; 60 years) under the weekly checks: every check clean, every week.** None reached the 90% line. At year 60:

| Seed | People | Unhappy | No job | Staff paid, average | Rate offered | Under the home loan ruling (18 November, evening) |
|---|---|---|---|---|---|---|
| 1 | 893 | 66% | 0% | $622 | $469 | never reached the line; ended on $67, 46% with no job, 89% unhappy |
| 2 | 940 | 62% | 0% | $740 | $593 | never reached the line; ended on $52, 47% with no job, 89% unhappy |
| 3 | 872 | 72% | 0% | $720 | $545 | failed in year 50.25 |

Three towns. Why they hold is not traced. The share unhappy still climbs through all sixty years in all three.

## Forty full towns: stopped at twenty-seven, to rest the machine

`python3 batch.py line1911b --seeds 1-40 --quiet` from `rtr/`, the world as it ships after the fix pass, 60 years, no weekly checks (a crash hunt). Jason's machine was running hot (the processor read 100°C, its critical limit, at 11:17am on 19 November), and the batch was stopped after 49 minutes on his word to finish up. **Twenty-seven towns had finished (seeds 1 to 26 and 28): none crashed.** The other thirteen (27, 29 to 40) did not finish and are not counted. Folder `rtr/batches/line1911b` (not in git; it has no batch page, because the batch never wrote one).

Of the twenty-seven: one reached the 90% line (seed 9, in year 56.8). Twenty-six never did. Those twenty-six at year 60: staff paid $670 to $964 a week on average (middle $796); share with no job 0% in the middle town and 11% at most; share unhappy 50% to 85% (middle 65%). Under the home loan ruling of the evening before, 28 of all forty had reached the line and none ended on a working wage.

Not known: why. Nothing here is traced, twenty-seven is not forty, and the share unhappy still climbs for sixty years in every town looked at. "Never reached the line" is not "works".

An earlier batch of the same name without the "b" (`rtr/batches/line1911`) is a stopped half-run of the first build, before the review's fix: ignore it.

The scratch scripts and outputs this ledger names (the break script, the scans, the outcome counts, the traces, the reviewer's scripts and outputs) were copied to `rtr/batches/kept-scratch-2026-11-19/` (not in git), because the machine was to be shut down and its temporary folder is cleared when it starts.

## Still to do

Nothing is committed. Waiting on Jason: the commit. Owed after the machine has rested: the forty full towns in full, run on fewer processors at a time; then the RTR README's section for 19 November (the README has today's dial count and one corrected line, and no account of the day yet). Two questions for him, one at a time: may a firm let go staff on the old rate to take on newcomers on the new one; and does it let go its dearest or its newest first.
