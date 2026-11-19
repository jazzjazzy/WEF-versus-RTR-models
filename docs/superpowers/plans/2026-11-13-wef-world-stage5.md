# WEF World Stage 5 (part 1: many towns) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One command that runs many towns under one or more settings, gathers them into one table, and builds one page that shows the spread.

**Architecture:** `wefworld/batch.py` plans a batch (settings by seeds), runs each town as an ordinary run in its own process and folder, and collects the towns' records into `batch.sqlite`. `wefworld/batchpage.py` reads only that table and writes `batch.html`, with charts drawn by Python as SVG. `runner.py` gains `run_in`, the part of `run` that works in a folder it is given.

**Tech Stack:** Python 3.12 standard library only (`concurrent.futures`, `sqlite3`). pytest. No JavaScript beyond a few lines that show the text under the pointer.

**Spec:** `docs/superpowers/specs/2026-11-13-wef-world-stage5-design.md`. The stage 1 to 3 specs still bind everything they cover.

## Global Constraints

- No rule of the model changes. Outside the two new modules, only these may change: `runner.py` (the split), `__main__.py` (two commands), `.gitignore`, `README.md`, `docs/`.
- A town made by a batch has the same record fingerprint as the same town run alone.
- The table is built only from the towns' records and `batch.json`. The page is built only from the table. Every number on the page equals the table.
- The page fetches nothing: no `<script src`, `<link`, `@import`, `url(`, `fetch(`.
- The page carries the "Untuned" notice. A figure for a year says how many towns were still standing.
- Batch default record: `snapshot_every=13`. `--full` leaves the record as the settings say.
- No git commit without Jason's approval. Work stays in the working tree on `feature/stage-5-batch-runs`.
- Plain language in anything Jason reads. No em dashes.

## Review Focus

1. A batch in which no town fails. Expected: no dots, "none failed" in words, no crash and no division by nothing.
2. A batch of one town. Expected: the middle, the middle half and the range are all that town's number.
3. Towns that end inside their first year. Expected: no yearly rows for them, the page still builds and says how many towns each year rests on.
4. A batch stopped part way, with towns missing or unfinished. Expected: the table and the page are built from the finished towns and say how many are missing.
5. A dial or value that is not safe as a folder name or as HTML (`needs.food.initial_price=5000`, a value with a space or `<`). Expected: a safe folder, the text escaped on the page.

---

### Task 1: A run into a given folder

**Files:** Modify `wefworld/runner.py`. Test: `tests/test_runner.py`.

**Interfaces (produces):**
- `run_in(cfg, run_dir, quiet=True, pages=True) -> dict`: runs the town into `run_dir` (it must exist and hold no `run.sqlite`, else `FileExistsError`), writes `config.json`, `run.sqlite`, `summary.json`, builds the town view and dashboard when `pages`, and returns the summary. `run()` names the folder, calls it, and prints as before.

- [ ] Tests first: `run_in` into a made folder gives the same record fingerprint and the same files as `run()` with the same settings; `pages=False` leaves no `dashboard.html` or `town.html`; a folder that already holds a record raises and is left as it was.
- [ ] Run: fail (no `run_in`). Implement. Run the whole suite: pass.

### Task 2: The plan of a batch

**Files:** Create `wefworld/batch.py`, `tests/test_batch.py`.

**Interfaces (produces):**
- `class BatchError(ValueError)`.
- `parse_seeds(text) -> list[int]`: `"1-5,9"` gives `[1, 2, 3, 4, 5, 9]`, sorted, no repeats; bad text, an empty list or a seed below 0 raises `BatchError`.
- `LIGHT = ("snapshot_every=13",)`.
- `slug(name) -> str`: a folder name from a setting's name: every character outside `A-Za-z0-9._=-` becomes `_`; never empty.
- `make_plan(name, seeds, base=(), vary=(), config=None, full=False) -> dict` with keys `name, seeds, base, config, record, code, settings`. `settings` is a list of `{"name", "slug", "overrides"}`; the first is the base, named `as written` when `base` is empty, else the `base` items joined by `, `. Each item of `vary` is `"dial=a,b,c"` and adds a setting named `dial=value` for each value. A setting whose full settings equal an earlier one's is left out. A mistyped dial or value raises here. Two settings with the same slug raise.
- `town_overrides(plan, setting, seed) -> list[str]`: `record + base + setting overrides + ["seed=N"]`, the list handed to `load_config(plan["config"], ...)`.

- [ ] Tests first: seeds; slugs (Review Focus 5); the base's name; one setting per varied value; a varied value equal to the base's is not a second setting; `full=True` drops the lighter record; a mistyped dial raises `BatchError` naming it; the plan can be written as JSON.
- [ ] Fail, implement, pass.

### Task 3: Running a batch

**Files:** Modify `wefworld/batch.py`, `tests/test_batch.py`.

**Interfaces (consumes):** `run_in`, `make_plan`, `town_overrides`. **(produces):**
- `town_dir(batch_dir, setting, seed) -> Path`: `batch_dir / "towns" / slug / "seed-0007"`.
- `finished(run_dir) -> bool`: the record there has an outcome.
- `run_batch(plan, out_root="batches", jobs=None, quiet=False) -> Path`: writes or merges `batch.json`, runs every town not yet finished, several at a time, and returns the batch folder. Merging: the stored `base`, `config`, `record` and `code` must equal the new plan's, else `BatchError`; seeds and settings are joined. An unfinished town folder is emptied and run again. `jobs` defaults to the processor count less two, at least one.
- `run_town(args) -> dict`: the worker. One town; returns `{"setting", "seed", "outcome", "failed_year", "seconds"}`.

- [ ] Tests first, on towns of 30 people for one year: a batch town's record fingerprint equals the same town run alone with `run()`; one at a time and three at a time give the same fingerprints; a second call runs nothing (the folders' records are untouched) and a third with more seeds runs only the new ones; an unfinished folder is run again; a plan with another code fingerprint or another base is refused and nothing is run; `batch.json` holds the joined plan.
- [ ] Fail, implement, pass.

### Task 4: The table

**Files:** Modify `wefworld/batch.py`, `tests/test_batch.py`.

**Interfaces (produces):**
- `MEASURES`: the `(scope, metric)` pairs of the spec, section 4.
- `collect(batch_dir) -> Path`: writes `batch.sqlite` afresh (to a temporary file, then moved into place) with tables `batch(key, value)`, `settings(setting, name, slug, overrides)`, `towns(setting, seed, folder, outcome, weeks, failed_week, full_week, year_weeks, fingerprint, code, events, summary)`, `moments(setting, seed, name, week)`, `yearly(setting, seed, year, scope, metric, value)`. `batch` holds `plan`, `code`, `planned` and `finished` (how many towns the plan asks for and how many are in the table).

- [ ] Tests first: every town row equals its record's `run` table and summary; `moments` equal the first week of each moment in the town's events and `firm_static`; every `yearly` value equals the town's `series` at week `year * weeks_per_year`, and there is none for a year the town did not finish; a town missing or unfinished is left out and counted (Review Focus 4); collecting twice gives the same table.
- [ ] Fail, implement, pass.

### Task 5: The numbers for the page

**Files:** Create `wefworld/batchpage.py`, `tests/test_batchpage.py`.

**Interfaces (produces):**
- `quantile(values, q) -> float`: straight-line interpolation between sorted values; one value gives itself.
- `spread(values) -> dict | None`: `{"n", "min", "q1", "median", "q3", "max"}`; `None` for no values.
- `report_data(con) -> dict`: `{"batch": {...}, "settings": [{"setting", "name", "towns": [...], "failed": [years], "standing": [(year, share)], "yearly": {(scope, metric): [(year, spread)]}, "end": {...}, "needs": {need: count}}], "varied": {dial: [setting numbers]}}`.

- [ ] Tests first: `quantile` and `spread` against hand-worked lists, a list of one, an empty list (Review Focus 2); `report_data` on a small batch: failed years equal the table; the share standing falls only at a failure and never rises; each year's spread equals the spread of that year's values worked out in the test, and its `n` is the towns that finished that year (Review Focus 3); a batch in which nothing failed (Review Focus 1).
- [ ] Fail, implement, pass.

### Task 6: The page

**Files:** Modify `wefworld/batchpage.py`, `tests/test_batchpage.py`.

**Interfaces (consumes):** `report_data`, `collect`. **(produces):**
- `build_batch_report(batch_dir) -> Path`: collects, then writes `batch.html`.

- [ ] Tests first: the page builds from `batch.sqlite` alone (the towns' folders moved away); one dot for each failed town, its text naming the seed and the year; the words for a setting in which none failed; each year's text under the pointer carries the same middle, middle half, range and count as `report_data`; every town is in the table with its fingerprint and folder; a setting's name with `<` in it is escaped; nothing is fetched; "Untuned" is there; the palette is the dashboard's.
- [ ] Fail, implement, pass.

### Task 7: Commands, the first batch, and by eye

**Files:** Modify `wefworld/__main__.py`, `.gitignore`, `README.md`, `tests/test_batch.py`.

- [ ] Tests first: `python -m wefworld batch NAME --seeds 1-2 --set ... --vary ... --out DIR --jobs 2` makes the towns, the table and the page and prints where the page is; a mistyped dial exits 2 and makes nothing; `batch-report DIR` rebuilds the page; `batch-report` on a folder that is not a batch exits 2 with a plain message.
- [ ] Fail, implement, pass. Whole suite: pass.
- [ ] Run the first real batch: the model as written on the map, seeds 1 to 100. Check seed 1's fingerprint against the record of 12 November. Read the page in the browser, light and dark, wide and narrow, with nothing in the console.
- [ ] README: how to run a batch, what it leaves behind, what the first batch shows, and that it is untuned.
