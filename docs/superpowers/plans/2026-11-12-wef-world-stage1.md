# WEF World Stage 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A week-by-week town economy (agents, firms, jobs, prices, shares, bank, broker, decay, trade) that records everything to one SQLite file per run and builds a three-coverage dashboard from that record.

**Architecture:** One `Town` object holds all state and one seeded random generator. Each phase of the week is a function in its own module that takes the town. All money moves through `Ledger.pay`, which names the kind of every payment and tallies the five flows across the town boundary. A `Recorder` writes events, snapshots and series; the dashboard reads only the SQLite file.

**Tech Stack:** Python 3.12 standard library only (`dataclasses`, `random`, `sqlite3`, `json`, `argparse`, `hashlib`). Tests with pytest 9.

**Spec:** `docs/superpowers/specs/2026-11-12-wef-world-stage1-design.md`. Background: `docs/design-chat-2026-11-12.md`, `docs/predictions.md`.

## Global Constraints

- Standard library only. No third-party imports anywhere in `wefworld/`.
- Money is `int` cents everywhere. `Ledger.pay` rejects floats and negatives.
- One `random.Random(cfg.seed)` per town, reached as `town.rng`. No other source of randomness, no wall-clock time inside the model, no iteration over sets of objects.
- Same settings plus same seed gives an identical record.
- No one leaves town: agents are only ever appended to `town.agents`.
- Money crosses the town boundary only as kinds `arrival`, `loan`, `export` (in) and `loan_principal`, `loan_interest`, `loan_recovery`, `import` (out).
- No git commits. Jason's standing rule is no commit without his approval; work stays in the working tree.
- Plain language in anything Jason reads (README, dashboard). No em dashes.

## Review Focus

1. A firm failing mid-week while agents still point at it. Expected: after every step no agent's employer or subscription is a dead firm, and every occupied unit's occupant subscribes to the unit's firm. Pinned in Task 9 (`test_no_reference_to_a_dead_firm`).
2. No vacant home when a firm wants to hire from outside. Expected: no arrival, the housing firm sees the unmet demand and builds, the town keeps growing. Pinned in Task 9 (`test_arrivals_are_always_housed`, `test_town_grows_past_its_first_homes`).
3. Empty or all-zero inputs to the measures (no shares traded, one agent, a run that ends in its first year). Expected: 0.0, never a division error; the dashboard still builds. Pinned in Task 10 (`test_gini_known_values`) and Task 11 (`test_dashboard_handles_a_short_failed_run`).
4. A mistyped dial on the command line. Expected: a clear error naming the key, not a silent default run. Pinned in Task 1 (`test_unknown_dial_raises`).
5. A run stopped part way. Expected: the SQLite file is still readable and `info` reports it as unfinished. Pinned in Task 10 (`test_unfinished_run_is_readable`).

---

## File structure

| File | Responsibility |
|---|---|
| `wefworld/config.py` | `NeedSpec`, `Config`, every dial with its starting value and reason, load and override |
| `wefworld/ledger.py` | `OUTSIDE`, `Ledger.pay`, per-week and running flow tallies |
| `wefworld/entities.py` | `Agent`, `Firm`, `Unit`, `Project`: state and small derived values |
| `wefworld/broker.py` | order book, `clearing_price`, weekly auctions, new issues |
| `wefworld/bank.py` | lending limits, loans, servicing, calling, defaults |
| `wefworld/production.py` | weekly work: service, upkeep, decay, building, making, import, export |
| `wefworld/corporate.py` | quarterly review, price search, dividends, share grants, raising money, founding, failure, takeover, wind-up |
| `wefworld/labour.py` | staff planning, layoffs, promotions, hiring, arrivals, wage moves |
| `wefworld/household.py` | bills, coping, share orders, subscription reviews, security, wellbeing, class |
| `wefworld/town.py` | `Town`: set-up, the week in order, failure rule |
| `wefworld/metrics.py` | Gini, top share, weekly series for each coverage |
| `wefworld/recorder.py` | SQLite schema and writers, `NullRecorder`, fingerprints |
| `wefworld/runner.py` | one run end to end: run folder, record, summary, dashboard |
| `wefworld/dashboard.py` | the HTML dashboard from a run folder |
| `wefworld/__main__.py` | command line: `run`, `dashboard`, `info` |
| `tests/conftest.py` | `small_cfg(**kw)`, `small_town(**kw)`, helpers to place agents and firms |

---

### Task 1: Skeleton and settings

**Files:** Create `pyproject.toml`, `.gitignore`, `wefworld/__init__.py`, `wefworld/config.py`, `tests/conftest.py`, `tests/test_config.py`.

**Interfaces (produces):**
- `NeedSpec` dataclass: `name, kind ('flow'|'asset'), weight, essential, priority, service_labour, goods_per_sub, make_labour, import_price, export_price, export_quota, initial_price, build_labour, build_goods, upkeep_labour, upkeep_goods, upkeep_growth, aging_rate, life_years, initial_units, appeal, invented`.
- `Config` dataclass with every dial; `Config.need(name) -> NeedSpec`; `Config.to_dict()`; `Config.from_dict(d)`.
- `load_config(path: str | None, overrides: list[str]) -> Config`. Overrides are `key=value`; need dials are `needs.<name>.<field>=value`.
- Starting values exactly as in the spec section 5 and the dial table in `config.py`: basket food 40000, housing 33000, appliances 5500, entertainment 9500; outside wage 100000; cap 1000.

- [ ] Tests: `test_default_basket_is_880_dollars` (sum of `initial_price` == 88000); `test_override_dotted_need_key`; `test_unknown_dial_raises` (`KeyError` naming the key); `test_round_trip` (`Config.from_dict(cfg.to_dict()) == cfg`).
- [ ] Run `python -m pytest tests/test_config.py -q`: fails on import.
- [ ] Implement. Run again: 4 passed.

### Task 2: Ledger

**Files:** Create `wefworld/ledger.py`, `tests/test_ledger.py`.

**Interfaces (produces):**
- `OUTSIDE` sentinel; `InsufficientFunds(Exception)`.
- `Ledger.pay(src, dst, amount: int, kind: str) -> None`: `src` and `dst` are any object with an int `cash`, or `OUTSIDE`.
- `Ledger.start_week()`; `Ledger.week_in`, `Ledger.week_out`, `Ledger.week_internal` (dict kind -> cents); `Ledger.total_in`, `Ledger.total_out`.

- [ ] Tests: `test_internal_payment_conserves_money`; `test_outside_flows_are_tallied`; `test_cannot_overdraw` (raises, balances unchanged); `test_rejects_negative_and_float`; `test_unknown_boundary_kind_rejected` (an inflow kind outside `arrival, loan, export` raises `ValueError`, likewise outflows).
- [ ] Run: fails. Implement. Run: passes.

### Task 3: Entities and broker

**Files:** Create `wefworld/entities.py`, `wefworld/broker.py`, `tests/test_broker.py`.

**Interfaces (produces):**
- `Agent`, `Firm`, `Unit`, `Project` with the fields named in the spec sections 5.3 to 5.8. `Agent.h_eff(cfg) -> float`; `Firm.collateral(cfg) -> int`; `Firm.book_per_share(cfg) -> int`; `Firm.weighted(town, fn) -> float` (holding-weighted mean).
- `clearing_price(bids: list[tuple[int, int]], asks: list[tuple[int, int]], ref: int) -> tuple[int, int] | None`: the positive price that trades the most shares; ties go to the price nearest `ref`.
- `Broker(town)`: `.bid(agent, firm, limit, qty)`, `.ask(agent, firm, limit, qty, reason)`, `.issue(firm, limit, qty)`, `.clear_all()`.

- [ ] Tests: `test_fire_sale_price_set_by_depth_of_buyers` (bids `[(800,50),(600,30),(300,40)]`, asks `[(0,100)]`, ref 1000 -> `(300, 100)`); `test_no_cross_no_trade` -> `None`; `test_tie_goes_to_price_nearest_last_trade` (bid `(1000,10)`, ask `(600,10)`, ref 900 -> `(900, 10)`); `test_trades_conserve_cash_and_shares`; `test_new_issue_raises_cash_and_adds_shares`; `test_seller_cannot_sell_more_than_held`.
- [ ] Run: fails. Implement. Run: passes.

### Task 4: Bank

**Files:** Create `wefworld/bank.py`, `tests/test_bank.py`.

**Interfaces (produces):** `Bank(town)`: `.firm_credit(firm) -> int`, `.lend_firm(firm, amount) -> int`, `.person_credit(agent) -> int`, `.lend_person(agent, amount) -> int`, `.service_firm(firm) -> bool`, `.service_person(agent) -> bool`, `.call(agent)`, `.weekly_called(agent)`, `.writeoffs_week: int`.

- [ ] Tests: `test_firm_borrows_up_to_60pct_of_asset_value`; `test_firm_without_assets_cannot_borrow`; `test_person_borrows_up_to_eight_weeks_wages`; `test_unemployed_person_cannot_borrow`; `test_interest_and_principal_leave_town` (ledger outflows `loan_interest`, `loan_principal` rise; money in town falls by the same); `test_called_loan_written_off_after_grace_and_credit_blocked` (after 8 weeks unpaid: `agent.loan == 0`, a `default` event, no credit for 156 weeks, no money left town for the written-off part).
- [ ] Run: fails. Implement. Run: passes.

### Task 5: Production and decay

**Files:** Create `wefworld/production.py`, `tests/test_production.py`.

**Interfaces (produces):** `upkeep_need(spec, unit) -> tuple[float, float]` (labour, goods); `best_condition(spec, unit) -> float`; `update_condition(cfg, spec, unit, done: float)`; `make_cost(firm) -> int`; `operate(town)`.

- [ ] Tests: `test_upkeep_rises_with_age` (at 10 years, housing labour == `0.04 * (1 + 0.04 * 10)`); `test_best_condition_falls_with_age`; `test_condition_falls_when_skimped_and_recovers_slowly`; `test_units_age_one_week_per_step`; `test_firm_makes_when_cheaper_and_imports_when_dearer` (flip by setting the firm wage above and below `import_price / make_labour`; import outflow appears only when dearer or short of staff); `test_exports_only_when_profitable_and_within_quota`.
- [ ] Run: fails. Implement. Run: passes.

### Task 6: Corporate rules

**Files:** Create `wefworld/corporate.py`, `tests/test_pricing.py`, `tests/test_corporate.py`.

**Interfaces (produces):** `target_growth(town, firm) -> float`; `review_firm(town, firm)`; `pay_dividends(town, firm)`; `quarterly(town)`; `found_firm(town, founder, capital, spec, in_kind_units=0) -> Firm`; `maybe_arrive_founder(town)`; `invent_need(town) -> NeedSpec`; `fail_firm(town, firm, reason)`; `wind_up(town, firm, reason)`.

- [ ] Tests (pricing): `test_target_growth_is_holding_weighted_average` (75% at 0.02 and 25% at 0.10 -> 0.04); `test_shortfall_raises_price_one_step` (price x 1.03); `test_no_shortfall_leaves_price_alone`; `test_price_reverses_after_a_move_that_lowered_profit`; `test_loss_always_counts_as_shortfall`; `test_upkeep_level_cut_on_shortfall_and_restored_after`.
- [ ] Tests (corporate): `test_founding_moves_capital_and_issues_shares_at_ten_dollars`; `test_dividends_split_by_holding_and_leave_reserve`; `test_failed_firm_with_customers_is_sold_and_staff_keep_jobs`; `test_failed_firm_without_customers_is_wound_up`; `test_old_shares_cancelled_on_failure`; `test_invented_need_is_discretionary_and_not_transport`.
- [ ] Run: fails. Implement. Run: passes.

### Task 7: Labour market

**Files:** Create `wefworld/labour.py`, `tests/test_labour.py`.

**Interfaces (produces):** `desired_staff(firm, cfg) -> int`; `hire(town, firm, agent)`; `separate(town, agent, reason)`; `new_worker(town) -> Agent | None` (None when no home is vacant or the cap is reached); `labour_market(town)`.

- [ ] Tests: `test_outside_worker_needs_wage_and_vacant_home`; `test_cap_stops_arrivals`; `test_unfilled_vacancy_raises_wage_after_two_weeks`; `test_layoff_is_last_hired_first_and_calls_loan`; `test_executives_promoted_by_skill_one_per_25_staff`; `test_squeezed_worker_moves_for_any_rise`.
- [ ] Run: fails. Implement. Run: passes.

### Task 8: Households

**Files:** Create `wefworld/household.py`, `tests/test_household.py`, `tests/test_classes.py`.

**Interfaces (produces):** `basket_cost(town, agent) -> int`; `valuation(town, agent, firm) -> int`; `plan_bills(town)`; `pay_bills(town)`; `review_subscriptions(town)`; `classify(town, agent) -> str` (`'owner'|'working'|'out'`); `update_agents(town)`.

- [ ] Tests (household): `test_bills_paid_in_order_food_housing_loan_appliances_entertainment`; `test_calm_agent_cuts_entertainment_and_keeps_shares`; `test_stressed_agent_sells_shares_at_market`; `test_four_missed_rents_evicts_but_agent_stays_in_town`; `test_job_loss_drops_security_more_for_the_loss_averse`; `test_low_security_shortens_horizon`; `test_longer_horizon_values_a_share_more`.
- [ ] Tests (classes): `test_ceo_and_executive_are_owner_class`; `test_staff_with_shares_is_working_class`; `test_jobless_living_on_dividends_is_owner_class`; `test_jobless_without_dividend_cover_is_out_of_work`; `test_controller_of_live_firm_is_owner`; `test_wellbeing_formula_and_cutoff` (0.5, 0.3, 0.2; happy at >= 0.5); `test_destitute_definition`.
- [ ] Run: fails. Implement. Run: passes.

### Task 9: The town

**Files:** Create `wefworld/town.py`, `tests/test_town_invariants.py`, `tests/test_determinism.py`, `tests/test_failure_rule.py`.

**Interfaces (produces):** `Town(cfg, recorder=None)`; `.step()`; `.run(weeks) -> str` (`'failed'|'survived'`); `.event(kind, agent=None, firm=None, amount=None, qty=None, **data)`; `.population`; `.alive_firms`; `.firms_for(need_name)`; `.money_in_town() -> int`; `.failed_week`; `.cap_week`.

- [ ] Tests (invariants, one module-scoped run of a 120-agent town for 8 years, checked after every step): `test_money_only_moves_through_the_five_flows`; `test_shares_always_add_up`; `test_no_negative_cash_or_debt`; `test_nobody_leaves_and_cap_is_never_exceeded`; `test_classes_partition_population`; `test_no_reference_to_a_dead_firm`; `test_arrivals_are_always_housed`; `test_town_grows_past_its_first_homes` (with `needs.housing.initial_units=10`, population later exceeds 10).
- [ ] Tests (determinism): `test_same_seed_same_run`; `test_different_seed_different_run`.
- [ ] Tests (failure): `test_run_fails_when_ninety_percent_unhappy` (`happy_cutoff=1.01`, guard 4 -> `'failed'`, `failed_week` set); `test_guard_ignores_rule_below_minimum_population`; `test_run_survives_when_everyone_counts_as_happy` (`happy_cutoff=0`).
- [ ] Run: fails. Implement. Run: passes.

### Task 10: Record, measures, runner, command line

**Files:** Create `wefworld/metrics.py`, `wefworld/recorder.py`, `wefworld/runner.py`, `wefworld/__main__.py`, `tests/test_metrics.py`, `tests/test_recorder.py`.

**Interfaces (produces):** `gini(values) -> float`; `top_share(values, frac=0.10) -> float`; `weekly_series(town) -> list[tuple[str, str, float]]` (scope, metric, value; scopes `all, owner, working, out, town`); `Recorder(path, cfg)` with `.event`, `.agent_static`, `.firm_static`, `.snapshot(town)`, `.series(week, rows)`, `.finish(outcome, summary)`, `.fingerprint()`; `NullRecorder`; `code_fingerprint() -> str`; `runner.run(cfg, out_root='runs', quiet=False) -> Path`.

- [ ] Tests (metrics): `test_gini_known_values` (`[1,1,1,1]` -> 0; `[0,0,0,1]` -> 0.75; `[]` -> 0; all zero -> 0); `test_top_share` (nine 1s and one 91 -> 0.91).
- [ ] Tests (recorder): `test_run_record_holds_seed_settings_and_fingerprint`; `test_series_has_four_coverages_and_town`; `test_agent_events_carry_security_and_horizon`; `test_snapshot_rows_match_population_each_week`; `test_unfinished_run_is_readable`; `test_recorded_run_matches_unrecorded_run` (recording does not change the simulation).
- [ ] Run: fails. Implement. Run: passes.

### Task 11: Dashboard

**Files:** Create `wefworld/dashboard.py`, `tests/test_dashboard.py`.

**Interfaces (produces):** `build_dashboard(run_dir: Path) -> Path` (writes `dashboard.html`, self-contained, no network).

- [ ] Tests: `test_dashboard_builds_from_record_alone` (contains `Everyone`, `Owner class`, `Working class`, `Out of work`, the seed, no `http://` or `https://` script or style links); `test_dashboard_handles_a_short_failed_run`; `test_every_class_chart_has_all_four_coverages`.
- [ ] Run: fails. Implement. Run: passes.

### Task 12: First run and write-up

**Files:** Create `README.md`. Modify the spec if any rule was built differently.

- [ ] `python -m pytest -q`: all pass.
- [ ] `python -m wefworld run --seed 1`: finishes, prints the run folder and the outcome.
- [ ] Open the dashboard and read it. Check the first run for obvious nonsense (nobody hired, everyone bankrupt in the first year, money exploding) and fix causes that are bugs. Do not tune toward an outcome.
- [ ] README: what it is, how to run, where the record is, the dials, what stage 1 leaves out, the warning that results are untuned.
