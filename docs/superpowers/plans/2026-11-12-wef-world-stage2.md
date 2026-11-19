# WEF World Stage 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the stage 1 town on a fixed map so that distance limits and steers every choice of home, job and shop, land runs out, and transport becomes a subscription.

**Architecture:** A `TownMap` of `Spot`s lives on the `Town`. Homes (`Unit`) and firms carry a spot. All geography (distance, reach, access, rent factors, taking and buying land) is in one new module, `wefworld/places.py`, which the existing phase modules call. Entities with no spot are at distance zero from everything, so stage 1's unit tests and a town with `map_width = 0` behave as before.

**Tech Stack:** Python 3.12 standard library only. pytest.

**Spec:** `docs/superpowers/specs/2026-11-12-wef-world-stage2-design.md`. Stage 1 spec still binds everything it covers.

## Global Constraints

- Everything in the stage 1 plan's Global Constraints still holds: standard library only, integer cents, one seeded generator, no one leaves town, money crosses the boundary in the five named ways only.
- Land sales (`land_sale`) and ground rent (`ground_rent`) are payments inside town. Fitting out premises is an `import`.
- `map_width = 0` gives stage 1 behaviour: every existing test must pass unchanged in meaning.
- A home is never destroyed while it has a tenant without the tenant first being put out and the event logged.
- No git commit without Jason's approval. Stage 1 is committed; stage 2 work stays in the working tree on `feature/stage-2-map`.
- Plain language in anything Jason reads. No em dashes.

## Review Focus

1. Homes pulled down for premises. Expected: every tenant is put out first, logged with the reason, left with no home and no unit, and stays in town; no unit is left pointing at a spot it is not on.
2. The map is full and a founder cannot get a spot. Expected: the firm is not founded and the founder keeps their capital; nothing crashes.
3. The transport firm closes. Expected: riders who needed it move closer if they can or lose the job, with an event; nobody is left holding a job out of reach.
4. `map_width = 0`. Expected: no error anywhere a spot is read; results as in stage 1.
5. A firm with land fails, is sold or is absorbed. Expected: its spots follow the units and premises; no spot is left owned by a closed firm.

---

## File structure

| File | Change |
|---|---|
| `wefworld/places.py` | New. `Spot`, `TownMap`, distance, reach, travel time, access and rent factors, taking, buying and leasing land, finding a home |
| `wefworld/config.py` | Map dials; `trips_per_week` and `fixed_labour` on `NeedSpec` |
| `wefworld/entities.py` | `Unit.spot`; `Firm.spot`, `Firm.lots`; `Agent.work_spot`, `Agent.travel_hours` |
| `wefworld/town.py` | Builds the map; places day one; ground rent, quarterly refresh |
| `wefworld/subscriptions.py` | Reach and travel time in `find_provider`; `price_paid`; homes chosen by `find_home` |
| `wefworld/labour.py` | Jobs within reach; move for a job; arrivals need a home within reach of the job |
| `wefworld/household.py` | Bills at the home's own rent; moving; reach checks; transport; hours on the road |
| `wefworld/production.py` | New homes need room on a spot; land in collateral; fixed crew |
| `wefworld/corporate.py` | Premises for new firms; transport; unserved patches; land on sale, absorption and closing |
| `wefworld/recorder.py`, `metrics.py`, `dashboard.py` | Places in the record, measures of distance, the map picture and charts |
| `tests/test_places.py`, `tests/test_map_town.py` | New |

---

### Task 1: The map

**Interfaces (produces):** `Spot` (`id, x, y, kind, owner, user, units, ground_rent, access, popularity, rent_factor, label`); `TownMap(cfg)` with `.spots`, `.at(x, y)`, `.centre`, `.empty()`, `.full`; `dist(a, b) -> int` (0 if either is None); `town.map` (None when `map_width = 0`).

- [ ] Tests: `test_distance_is_blocks_along_the_grid`; `test_no_spot_means_no_distance`; `test_map_off_when_width_is_zero`; `test_default_map_is_169_spots`.

### Task 2: Places on day one

**Interfaces (produces):** `places.take_spot(town, firm, purpose, near=None) -> Spot | None`; `places.house(town, firm, unit) -> bool` (puts a new home on a spot with room); `Firm.spot` set by `found_firm`.

- [ ] Tests: `test_bank_and_broker_hold_the_middle`; `test_founding_firms_sit_next_to_the_middle`; `test_starting_homes_fill_the_best_placed_spots_eight_to_a_spot`; `test_early_town_is_within_walking_reach` (every starting home within 6 blocks of every founding premises); `test_new_firm_pays_to_fit_out_its_premises` (an `import` of `premises_cost`).

### Task 3: Reach and time

**Interfaces (produces):** `places.reach(town, agent) -> int`; `places.travel_hours(cfg, trips, blocks, fast) -> float`; `places.time_cost(town, hours) -> int`; `places.find_home(town, agent, work=None) -> Unit | None`; `subscriptions.find_provider` filters by reach and ranks by price plus time.

- [ ] Tests: `test_walking_reach_is_six_blocks_and_transport_makes_it_twenty_four`; `test_job_out_of_reach_is_refused`; `test_resident_moves_to_take_a_job_when_a_home_is_free_near_it`; `test_outside_worker_needs_a_home_within_reach_of_the_job`; `test_shop_out_of_reach_cannot_be_subscribed`; `test_nearer_shop_wins_when_prices_are_close`; `test_agent_who_loses_reach_moves_or_loses_the_job`; `test_hours_on_the_road_are_recorded`.

### Task 4: Location rents

**Interfaces (produces):** `places.refresh_access(town)`; `places.unit_rent(unit) -> int`; `subscriptions.price_paid(agent, need_name) -> int`.

- [ ] Tests: `test_best_placed_home_costs_a_quarter_more_and_the_worst_a_quarter_less`; `test_tenant_pays_their_own_homes_rent`; `test_fully_let_spot_grows_more_popular_and_an_emptier_one_less`; `test_home_search_weighs_rent_against_time`.

### Task 5: Land

**Interfaces (produces):** `places.take_spot` buys or leases once `town.map.scarce`; `places.give_up_spots(town, firm)`; `Firm.collateral` counts owned land at `town.land_price`.

- [ ] Tests: `test_land_is_free_while_spots_remain`; `test_land_is_scarce_from_the_week_the_map_fills`; `test_buyer_pays_the_cheapest_owner`; `test_buyer_who_cannot_pay_leases_and_pays_ground_rent`; `test_homes_pulled_down_for_premises_put_the_tenants_out_first`; `test_housing_firm_that_buys_homes_keeps_the_tenants`; `test_founder_who_cannot_get_a_spot_keeps_their_capital`; `test_closed_firms_spot_is_free_before_scarcity_and_sold_after`; `test_owned_land_is_security_and_leased_land_is_not`.

### Task 6: Transport

**Interfaces (produces):** `corporate.transport_spec(town) -> NeedSpec`; the trigger in `choose_venture`; `household` adoption; `NeedSpec.fixed_labour` honoured in `labour_need`, `has_room` and `_work`.

- [ ] Tests: `test_nobody_has_transport_at_the_start`; `test_enough_people_turned_away_brings_a_transport_firm`; `test_transport_runs_only_with_its_fixed_crew`; `test_agent_takes_transport_to_reach_a_job`; `test_agent_who_needs_transport_for_work_does_not_drop_it_to_save_money`; `test_transport_closing_strands_its_riders`.

### Task 7: Record, measures, dashboard

- [ ] Tests: `test_spots_and_places_are_recorded`; `test_agent_snapshot_has_home_work_and_hours`; `test_series_has_distance_measures_for_each_class`; `test_dashboard_has_the_map_and_the_distance_charts`; `test_dashboard_without_a_map_still_builds`.

### Task 8: Whole towns

- [ ] Tests: the stage 1 weekly checks with the map on, extended (`test_places_hold_together_every_week`: every home on a spot of its firm, no spot over 8 homes, every spot's user alive, no job or shop out of reach at week's end); `test_map_town_reaches_its_cap`; `test_same_seed_same_run_with_the_map`; `test_map_off_gives_a_town_with_no_places`.
- [ ] Run full towns, read the record, fix what is a bug. Do not tune toward an outcome.
- [ ] README and spec updated to what was built.
