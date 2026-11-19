# WEF World Stage 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A page per run, `town.html`, that replays the recorded town: the map, people moving through it, the four coverages at every week, and one person's life on demand.

**Architecture:** One new module, `wefworld/townview.py`. Python reads `run.sqlite` and turns it into compact change lists, embedded as JSON in a single HTML file. A small block of pure JavaScript (`CORE_JS`: reading change lists, routes, the round) is kept apart from the drawing code so it can be tested under Node. Nothing in the model or the recorder changes.

**Tech Stack:** Python 3.12 standard library only. pytest. Plain JavaScript in the page, no libraries. Node only to test `CORE_JS`, skipped when absent.

**Spec:** `docs/superpowers/specs/2026-11-12-wef-world-stage3-design.md`. Stage 1 and stage 2 specs still bind everything they cover.

## Global Constraints

- The page is built only from `run.sqlite`. It fetches nothing: no `<script src`, `<link`, `@import` or `url(`.
- No change to any model file or to `recorder.py`. Allowed outside `townview.py`: the `town` command in `__main__.py`, the hook in `runner.py`, a link in `dashboard.py`.
- Every number on the page equals the record. Class names and colours match the dashboard: Everyone, Owner class, Working class, Out of work.
- What is drawn but not recorded (the journeys, the strip for people with no home) is said on the page.
- No git commit without Jason's approval. Stage 3 work stays in the working tree on `feature/stage-3-town-view`.
- Plain language in anything Jason reads. No em dashes.

## Review Focus

1. A run with no map, or made before stage 2 (no `spots` table). Expected: no page, a plain message, no crash.
2. A run stopped part way (no outcome in the record). Expected: the page builds from what is there.
3. `snapshot_every` above 1. Expected: the weeks on the page are the snapshot weeks; nothing reads a week that was not recorded.
4. A firm that closes, and a spot that changes hands between quarterly records. Expected: no person is drawn walking to a firm that is gone; no premises is drawn for a closed firm.
5. A person with no home, no job, or no shops. Expected: a round with only the stops they have; nobody is drawn at spot `-1`.

---

### Task 1: Change lists and the people

**Files:** Create `wefworld/townview.py`, `tests/test_townview.py`.

**Interfaces (produces):**
- `encode(pairs) -> list[int]`: `[(week, value), ...]` in week order to `[week, value, ...]`, keeping only changes; `None` becomes `-1`.
- `mood_step(happy, wellbeing, cutoff) -> int`: 0 very unhappy, 1 unhappy, 2 content, 3 well; the happy flag decides the side, the halfway point of each side decides the depth.
- `KLASS = {"owner": 0, "working": 1, "out": 2}`, `ROLE = {None: 0, "staff": 1, "exec": 2, "ceo": 3}`.
- `_people(con, cutoff) -> list[dict]` with keys `id, arrived, origin, cash0, h, j, o, k, m, r, f, e`.
- Test helper `at(track, week)`: the value in force that week, `None` before the first entry.

- [ ] Tests first: `encode` drops repeats and maps `None`; `mood_step` at the edges; on a recorded small map run, every person's eight tracks read back at every recorded week equal `agent_snap`; a step below 2 exactly when `happy = 0`.
- [ ] Run them: fail (no module). Implement. Run: pass.

### Task 2: Firms and spots

**Interfaces (produces):**
- `_firms(con, weeks) -> list[dict]` with keys `id, name, need, founded, end, s, n, c, p`; `end` is the first recorded week after a firm's last snapshot, or None. (First drafted as a `-1` at the end of the `s` track; changed in Task 2 so that a live firm with no spot is not mistaken for a closed one.)
- `KIND = {None: 0, "homes": 1, "premises": 2, "service": 3}`.
- `spot_tracks(weeks, n_spots, places, premises, homes) -> list[dict]` with keys `k, u, n`. `places` is `{week: {spot: (kind, user, homes)}}` (quarterly); `premises` is `{week: {spot: firm}}`; `homes` is `{week: {spot: (firm, people)}}`. Rule: start from the latest quarterly record at or before the week. A firm that has the spot that week makes it premises. A premises whose firm no longer has the spot is empty. A spot someone lives on is homes, with at least as many homes as people living there.

- [ ] Tests first: firm tracks equal `firm_snap` at every week and end when the firm does; spot tracks equal `places` at each quarterly record; four hand-made cases for the between-quarters rule (firm arrives mid quarter; firm goes mid quarter; someone lives on a spot the last record called empty; homes pulled down for premises).
- [ ] Fail, implement, pass.

### Task 3: Series, marks and lives

**Interfaces (produces):**
- `_series(con, weeks) -> dict`: `n` and `unhappy` for the four scopes, and `homeless, riders, jobless, wage, basket, firms, destitute`, one value per recorded week.
- `_marks(con) -> list[dict]`: `{"week", "kind", "label"}` for `full`, `transport`, `land`, `failed`, in week order, only those that happened.
- `_lives(con, people, quarter) -> None`: adds `life = {"q0", "cash", "pay", "loan", "shares", "well", "sec", "events"}` to each person; `events` is `[[week, kind_code, firm, amount, text_code], ...]` in order; `LIFE_KINDS` lists the kinds kept.
- `town_data(con) -> dict | None`: everything above plus `run` and `map`; `None` when the run has no map.

- [ ] Tests first: series equal the `series` table; marks equal the first event of each kind; a person's life events are theirs, in week order, and include their hires and home moves; a seller appears in their own life for a share trade; quarterly lines start at arrival.
- [ ] Fail, implement, pass.

### Task 4: The page

**Files:** Modify `wefworld/townview.py`, `wefworld/__main__.py`, `wefworld/runner.py`, `wefworld/dashboard.py`. Create `tests/test_townview_js.py`.

**Interfaces (produces):**
- `CORE_JS`: a string defining `TownCore` with `at(track, week)`, `spotPoint(...)`, `route(a, b, lane)`, `length(pts)`, `along(pts, f)`, `plan(stops, pace, split)`, `where(plan, phase)`, `rnd(id, salt)`. No DOM.
- `build_town_view(run_dir) -> pathlib.Path | None`: writes `town.html`; `None` and nothing written when there is no map.
- CLI: `python -m wefworld town <run_dir>`.

- [ ] Node tests first (skipped without Node): `at` against the Python helper on random tracks; route ends, axis-aligned legs, length at least the grid distance; the round's order of stops, no work stop without a job, rider four times faster on a leg, home at phase 0 and phase 1.
- [ ] Python tests first: builds from the record alone; fetches nothing; carries the four coverage names, both colour choices, the Untuned notice and the recorded-and-drawn note; embedded data equals `town_data`; no map gives `None`; unfinished run builds; `snapshot_every=4` weeks; the CLI; the runner writes it for a map run and not for a run without one; the dashboard links to it only when there is a map.
- [ ] Fail, implement, pass. Whole suite green.

### Task 5: By eye, and the documents

- [ ] Build `town.html` for a full run. In the browser: light, dark, wide, narrow; play at each speed; drag the slider; click the time line; select a block and a person; pick a person by number; no console errors. Fix what is wrong, with a test where the fault is in logic.
- [ ] README: stage 3 intro, the `town` command, layout table, test count, what is still to come. `pyproject.toml` description. File the ledger under `docs/`.
- [ ] Fresh review of the whole branch. One fix pass, each fix test first.
