# Build ledger: RTR stage 1a, building and owning your own

Plan: `docs/superpowers/plans/2026-11-16-rtr-stage1a-owning-your-own.md`. Spec: `docs/superpowers/specs/2026-11-16-rtr-world-design.md`. Branch `feature/rtr-world`, cut from `develop` at `958d19f`; design and plan committed as `7f44744`.

WEF towns before any change (six years, `what_happened`), pinned in `tests/test_rtr.py`:
- `seed=1 stop_on_failure=false`: `889a87a96629fed5`, 14,113 events
- `seed=5 stop_on_failure=false founder_arrival_rate=0.25 resident_founder_rate=0.2`: `f92ac66689bf0bc5`, 25,843 events

Pre-flight: the tasks share `owning.py` in order (2 to 8); each consumes only what an earlier one produces. No conflict found on reading the plan against the spec.

Task 1: complete (world dial, RTR dials, configs/rtr.json; tests RED then GREEN; suite 716 passed; both WEF pins hold)
Task 2: complete (`owning.spare_hours`, `start_week`; two tests RED then GREEN)
Task 3: complete (Unit.owner, Agent RTR slots, OwnBuild, Spot.private_units and plots_reserved, `take_plot`, `place_own_unit`, `Town.new_own_unit`, `owns`, `housed`, homeless by `housed`; weekly checks for plots and for owned units; suite 723 passed)
Task 3: Ruling: `take_plot` notes land as scarce when it finds no land, as `take_spot` does ; so the map's scarcity does not depend on who asked last ; none.
Task 4: complete (`parts_price`, `own_cost_week`, `consider_own_set`, `work`, `keep`, replacement of a worn set; `owning.after_bills` and `owning.quarter` in the week; owned needs are met, not billed, not shopped for; six tests RED then GREEN; suite 729 passed)
Task 4: Ruling: someone starting a set keeps four weeks of their bills in hand, as the plan has for a home ; so nobody spends their last dollar on parts and then misses the rent ; fewer sets built by the very poor.
Task 4: Ruling: upkeep (`keep`) runs before building (`work`) each week and both draw on the same spare hours ; the spec's order ; none.
Task 4: Ruling: a home past keeping is not rebuilt in 1a (a home's best condition reaches the line in year 41) ; no run has reached it ; owned homes in a very long run would wear on.
Task 4, seen: a small RTR town (150 people, seed 1, six years, weekly checks clean): all 150 built their own set and the appliance firm was left with no customers.
Task 5: complete (`Bank.home_first_payment`, `home_credit`, `lend_home`, `service_home`; the loan is a bill of kind home_loan at the rent's place, borrowed for like rent; three tests RED then GREEN)
Task 6: complete (`build_cost`, `consider_building`, the home's hours in `work`, `_finish_home`; an owner is not moved by `check_reach`, `consider_moving` or `reach_job`; seven tests RED then GREEN; suite 739 passed)
Task 6: Ruling: each hour's materials are paid four fifths by the loan and a fifth from cash (the spec's "up to 80% ... the rest from their own cash", "drawn as the materials are bought"), where the plan first said cash first ; the plan was corrected before the build ; none.
Task 6: fixed, found by the first whole town (not by a unit test): a well-off owner was sent looking for a better rented home and the rent of a home with no landlord was asked for. `test_a_well_off_owner_is_not_sent_looking_for_a_better_rented_home` RED then GREEN.
Task 6, seen: a town of 200 on a 7 by 7 map, seed 1, ten years, weekly checks clean: 88 own the home they built, 112 rent, the first landlord has 96 of 208 homes empty, no loan payment missed, 1% unhappy.
Task 7: complete (`home_value`, `borrowable`; the cushion counts what an owner could still borrow; a home loan is not in the debt term; four tests, two RED then GREEN, two already true; suite 744 passed)
Task 7: Ruling: what an owner must find each week (`essentials_cost`) is food and the loan payment, not a rent ; the plan said an owned need costs nothing and left the loan out ; without it a calm owner would not sell shares to keep the home.
Task 7: Ruling: the weekly draws of a build do not each log a `home_loan` event (a small town logged 6,346); `home_built` carries the loan ; the flows are in the weekly measures either way ; none.
Task 8: complete (`foreclose`, `foreclosures`, `sell_foreclosed`; seven tests RED then GREEN; weekly checks for foreclosed homes, for loans without a home, and for reserved plots; suite 751 passed)
Task 8: Ruling: someone foreclosed on is refused credit for `default_block_weeks`, as after any default ; the spec is silent and the WEF bank does this for a personal default ; without it they could borrow the same week to buy the home back.
Task 8: Ruling: a buyer is taken in order of arrival, has a job, is not mid-build, and keeps four weeks of bills ; the plan's rule ; who buys first is the builder's order, not a market.
Task 8, seen: six towns of 200 on a 7 by 7 map, seeds 1 to 6, fourteen years, weekly checks clean in all; foreclosures 1 to 44 a town, sold on 0 to 30.
Task 9: complete (RTR-only weekly measures homes_owned, homes_foreclosed, homes_building, sets_owned, home_loans, spare_hours; homes and sets counts include what people own; units snapshot has own units and an owner column; a block of plots is written as a block of homes labelled "owned"; summary has `world` and the RTR figures; two tests RED then GREEN; suite 753 passed). The town view of a small RTR run opened in the browser with no errors.
Task 10: whole-town tests added (every rule reached with the weekly checks clean on seeds 2 and 3; a town with no map; the same town twice gives the same record).
Task 10, seen before the review: `OLD_RULES` seed 74 of the 13 November batch still `08251209eb136522`, 180,377 events. Three full RTR towns (seeds 1, 2, 3) failed in years 25.25, 23.5 and 22.9. They took 173 to 363 seconds each, against about 50 for a WEF town: a profile of two late years put 6% of the time in `owning` and most of it in the weekly shopping review that the WEF world already has (a large, poor town with about 19 needs on sale).

## Final review (a fresh reviewer, 17/11) and the fix pass

The first reviewer (16/11) stopped part way: the account ran out of usage credits. Run again on 17/11 at Jason's word. No Critical finding. It ran 21 more RTR towns under the weekly checks (80 to 402 people, 10 to 30 years, maps from 3 by 5 to 13 by 13 and none, other loan settings), checked the home-loan sums every week in six, fuzzed 177,165 weeks of building, and ran 7 more WEF towns against the code before the change: no fault in the money, the bookkeeping or a WEF town.

- Final: fixed (Important) someone short of credit for the parts of a set was lent what credit they had, got no parts, and was lent again each week (one town: 1,030 such loans, a person at their limit for 254 weeks). Now nothing is borrowed unless it buys the parts. `test_short_of_credit_for_the_parts_nothing_is_borrowed_and_no_set_is_started` RED then GREEN.
- Final: fixed (Important) a builder was given the best-placed plot with no look at their job and moved in whatever the distance (3 to 13% of finished homes cost the builder their job that week). Now a plot is taken only within reach of their work. `test_a_plot_is_taken_within_reach_of_their_work_or_not_at_all` RED then GREEN.
- Final: fixed (Important; the reviewer's own what-if showed no clear gain, adopted so the rule is the same everywhere) a builder put all their cash into materials week by week. Now they keep four weeks of bills in hand while building, as when starting and as for a set. `test_a_builder_keeps_four_weeks_of_bills_in_hand_while_building` RED then GREEN.
- Final: fixed (Important) an owner's cushion counted four fifths of the home's value whatever their income, though the bank lends nothing without income (Jason's answer of 16/11) and refuses anyone it has foreclosed on. Now the cushion counts what the bank would lend them (`Bank.home_credit`). `test_what_an_owner_could_borrow_counts_only_if_the_bank_would_lend_it` RED then GREEN.
- Final: fixed (graded Minor by the reviewer as "a gap for Jason"; re-graded Important by effect: with no appliance firm in town nobody could ever get a set) someone with no set at all now builds one if they can pay. `test_someone_with_no_set_at_all_builds_one_if_they_can_pay` RED then GREEN.
- Final: fixed (Minor by the reviewer; a crash on a setting is not minor to the person who sets it) `mortgage_weeks=0` divided by zero and `mortgage_ltv=1.5` lent more than the home's price; the RTR dials are now checked. `test_the_rtr_dials_are_refused_when_they_cannot_work` RED then GREEN.
- Final: fixed (Minor, with its test) a home the bank holds now ages and wears like any empty home. `test_a_home_the_bank_holds_ages_and_wears_like_any_empty_home` RED then GREEN.
- Final: fixed (speed) the most a person's income lets them owe is found by halving, not a cent at a time (`Bank.home_cap`), and possible buyers of foreclosed homes are worked out once a week, not once for each home. `test_the_most_the_bank_lends_on_income_is_found_at_once_and_is_the_most`.
- Final: tests made to bite. The reviewer broke rules one at a time and 13 breaks passed all 44 tests. Nine tests added or sharpened (no job no build even with cash; the fifth and the four weeks each needed; nobody builds or buys when rent is as cheap; a buyer must reach their work; upkeep needs the hours and the parts each; upkeep before building; hours counted in the weekly cost of owning; the home loan paid where the rent is and borrowed for; an owner not counted homeless). Eight breaks tried again in a scratch copy on 17/11: all eight caught.
- Final: added the debt on bank-held homes as a weekly measure (`homes_foreclosed_debt`); the record's schema version is 3.
- Final: minor (deferred to stage 3, the pages): the dashboard's map calls a block of owned homes "Firm None".
- Final: minor (deferred): the weekly `spare_hours` measure is what is left after upkeep and building, not what the week began with; blocks of plots are in none of the `spots_*` counts.
- Final: minor (deferred): with no spare hours someone could buy the parts for a set and never build it; cannot happen at the settings as they are (anyone has at least 20 hours less the road).
- Final: Ruling weighed by the reviewer and kept, with its cost restated: buyers of foreclosed homes are renters with a job only, and someone foreclosed on is refused credit for three years, so the bank's homes can pile up unsold (a reviewer's town, year 20: 45 held, the oldest 12 years, the cheapest asking $3,073 on a $30,907 debt, with 82 people homeless, nearly all in work and none able to buy). Stage 1b brings the rest of Jason's order (owners who let, then landlord firms). Until then this is how 1a behaves, and results from 1a alone should be read with it in mind.
- Final: not judged by the reviewer: stages 1b, 2 and 3; whether the builder's numbers are sensible; the pages beyond a smoke run; towns of 1,000 or 60 years.

Suite after the fix pass: 773 passed.

After the fix pass (17/11): `OLD_RULES` seed 74 of the 13 November batch is still `08251209eb136522`, 180,377 events. Three full RTR towns (seeds 1, 2, 3; 60 years allowed; no cap): failed in years 23.0, 22.25 and 22.02 (the same seeds in the WEF world under the rulings with no cap: 17.0, 18.0, 20.0). Most who owned their home at once: 336, 257, 302. Foreclosures: 308, 235, 219. At year 22: homeless 941, 824, 580; landlords' homes empty 724, 664, 442; homes held unsold by the bank 155, 70, 28; staff wage $643, $704, $507. At the end the owner class held $221.8M of $273.0M, $200.6M of $242.6M, $142.2M of $231.2M. Each town now takes 77 to 89 seconds (173 to 363 before the buyers were looked up once a week). Three towns of half a stage: not a finding.

Deferred minors, all in one place: the dashboard's "Firm None" on a block of owned homes (stage 3); the `spare_hours` measure is after upkeep and building; blocks of plots are in no `spots_*` count; parts bought for a set by someone with no hours at all.
