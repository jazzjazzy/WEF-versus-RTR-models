"""The page for a batch: its numbers, checked against the table, and the page itself."""

import json
import sqlite3

import pytest

from engine import batch, batchpage
from engine.batchpage import quantile, report_data, spread

SMALL = ["population_cap=30", "years=1"]
CLASSES = ("all", "owner", "working", "out")


# --- the middle, the middle half and the range ----------------------------------------------------------
def test_quantile_goes_in_a_straight_line_between_the_sorted_values():
    values = [10, 20, 30, 40, 50]
    assert [quantile(values, q) for q in (0, 0.25, 0.5, 0.75, 1)] == [10, 20, 30, 40, 50]
    assert quantile([4, 1, 3, 2], 0.5) == 2.5                 # the order given does not matter
    assert quantile([1, 2, 3, 4], 0.25) == 1.75
    assert quantile([0, 10], 0.9) == 9


def test_quantile_of_one_value_is_that_value():
    assert [quantile([7], q) for q in (0, 0.25, 0.5, 0.75, 1)] == [7, 7, 7, 7, 7]


def test_spread_is_the_count_the_range_the_middle_and_the_middle_half():
    assert spread([3, 1, 2, 5, 4]) == {"n": 5, "min": 1, "q1": 2, "median": 3, "q3": 4, "max": 5}
    assert spread([8]) == {"n": 1, "min": 8, "q1": 8, "median": 8, "q3": 8, "max": 8}
    assert spread([]) is None


# --- the numbers of a batch -------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def numbers(mixed_batch):
    batch_dir, plan = mixed_batch
    con = sqlite3.connect(batch.collect(batch_dir))
    yield report_data(con), con, plan, batch_dir
    con.close()


def test_the_batch_is_described_as_the_table_has_it(numbers):
    data, con, plan, _ = numbers
    assert data["batch"] == {"name": "mixed", "code": plan["code"], "planned": 16, "finished": 16,
                             "seeds": plan["seeds"], "record": plan["record"], "world": "WEF world"}
    assert [(s["setting"], s["name"], s["overrides"]) for s in data["settings"]] == [
        (0, plan["settings"][0]["name"], []), (1, "failure_unhappy_share=0.25", ["failure_unhappy_share=0.25"])]
    json.dumps(data)                                         # everything in it can be written out


def test_each_town_is_listed_with_how_and_when_it_ended(numbers):
    data, con, _, _ = numbers
    for setting in data["settings"]:
        rows = con.execute("SELECT seed, folder, outcome, weeks, failed_week, full_week, fingerprint FROM towns "
                           "WHERE setting = ? ORDER BY seed", (setting["setting"],)).fetchall()
        assert setting["n"] == len(rows) == 8
        for town, (seed, folder, outcome, weeks, failed, full, fingerprint) in zip(setting["towns"], rows):
            assert (town["seed"], town["folder"], town["outcome"], town["fingerprint"]) == (seed, folder, outcome, fingerprint)
            assert town["years"] == weeks / 52
            assert town["failed_year"] == (failed / 52 if failed is not None else None)
            assert town["full_year"] == (full / 52 if full is not None else None)
        assert setting["failed"] == sorted(failed / 52 for _, _, _, _, failed, _, _ in rows if failed is not None)
        assert setting["survived"] == sum(1 for row in rows if row[2] == "survived")
        assert setting["survived"] + len(setting["failed"]) == 8


def test_the_share_still_standing_starts_whole_and_falls_only_when_a_town_fails(numbers):
    data, _, _, _ = numbers
    for setting in data["settings"]:
        steps = setting["standing"]
        assert steps[0] == [0, 1.0]
        years, shares = [year for year, _ in steps], [share for _, share in steps]
        assert years == sorted(years) and shares == sorted(shares, reverse=True)
        assert years[-1] == max(town["years"] for town in setting["towns"])
        assert shares[-1] == pytest.approx(setting["survived"] / 8)
        for year, share in steps[1:-1]:
            assert year in setting["failed"]
            assert share == pytest.approx(sum(1 for f in setting["failed"] if f > year) / 8 + setting["survived"] / 8)
    assert data["settings"][1]["standing"][-1][1] == 0       # under the stricter rule none is left


def standing_at(con, setting, year):
    """The seeds of the towns that had not failed by the end of that year, from the table."""
    return {seed for seed, failed, year_weeks in con.execute(
        "SELECT seed, failed_week, year_weeks FROM towns WHERE setting = ?", (setting,))
        if failed is None or failed > year * year_weeks}


def test_each_years_spread_is_over_the_towns_still_standing_at_the_end_of_that_year(numbers):
    data, con, _, _ = numbers
    checked = 0
    for setting in data["settings"]:
        for key, rows in setting["yearly"].items():
            scope, metric = key.split("/")
            for row in rows:
                alive = standing_at(con, setting["setting"], row["year"])
                values = {seed: value for seed, value in con.execute(
                    "SELECT seed, value FROM yearly WHERE setting = ? AND year = ? AND scope = ? AND metric = ?",
                    (setting["setting"], row["year"], scope, metric)) if seed in alive}
                if scope != "town" and metric != "n":         # a class with nobody in it has no number
                    sizes = dict(con.execute(
                        "SELECT seed, value FROM yearly WHERE setting = ? AND year = ? AND scope = ? AND metric = 'n'",
                        (setting["setting"], row["year"], scope)))
                    values = {seed: value for seed, value in values.items() if sizes[seed] > 0}
                assert {k: row[k] for k in ("n", "min", "q1", "median", "q3", "max")} == spread(values.values())
                checked += 1
            assert [row["year"] for row in rows] == sorted(row["year"] for row in rows)
        assert set(setting["yearly"]) <= {f"{scope}/{metric}" for scope, metric in batch.MEASURES}
    assert checked > 150
    base = data["settings"][0]["yearly"]["all/unhappy"]
    assert base[0]["year"] == 1 and base[0]["n"] == 8 and base[-1]["n"] < 8


def test_a_towns_failing_week_is_not_in_the_figure_for_the_year_it_ends(numbers):
    """A week is recorded before the failure rule is read, so a town that fails in the last
    week of a year has a record for that year. It is not still standing, and is left out."""
    data, con, _, _ = numbers
    at_year_end = con.execute("SELECT setting, seed, failed_week / year_weeks FROM towns "
                              "WHERE failed_week % year_weeks = 0").fetchall()
    assert at_year_end, "no test town fails in the last week of a year: pick other towns"
    for setting, seed, year in at_year_end:
        assert con.execute("SELECT COUNT(*) FROM yearly WHERE setting = ? AND seed = ? AND year = ?",
                           (setting, seed, year)).fetchone()[0] > 0          # the table keeps the record
        rows = [row for row in data["settings"][setting]["yearly"].get("town/wage", []) if row["year"] == year]
        assert (rows[0]["n"] if rows else 0) == len(standing_at(con, setting, year))


def test_the_count_beside_a_years_figure_is_the_share_still_standing_that_year(numbers):
    data, _, _, _ = numbers
    for setting in data["settings"]:
        for row in setting["yearly"].get("town/wage", []):
            share = [s for year, s in setting["standing"] if year <= row["year"]][-1]
            assert row["n"] == round(share * setting["n"])
        last_year = max((row["year"] for row in setting["yearly"].get("town/wage", [])), default=0)
        assert all(row["n"] > 0 for rows in setting["yearly"].values() for row in rows)
        assert last_year <= 4


def test_half_failed_is_the_year_by_which_half_the_towns_had_failed():
    from engine.batchpage import half_failed
    assert half_failed([1.0, 2.0, 3.0, 4.0], 8) == 4.0        # the fourth failure makes it half of eight
    assert half_failed([4.0, 1.0, 3.0, 2.0], 8) == 4.0
    assert half_failed([1.0, 2.0, 3.0, 4.0], 9) is None       # four of nine is not half
    assert half_failed([1.0, 2.0, 3.0, 4.0], 4) == 2.0
    assert half_failed([3.5], 1) == 3.5
    assert half_failed([], 5) is None and half_failed([], 0) is None


def test_the_need_whose_price_rose_most_is_level_when_two_are_level():
    from engine.batchpage import risen_most
    assert risen_most({"food": 1.2, "housing": 1.5, "appliances": 2.0, "entertainment": 1.9}) == "appliances"
    assert risen_most({"food": 1.2, "housing": 1.2, "appliances": 1.6045, "entertainment": 1.6044}) == (
        "level: appliances, entertainment")                  # a cent's rounding apart
    assert risen_most({"food": 1.0, "housing": 1.0, "appliances": 1.0, "entertainment": 1.0}) == (
        "level: appliances, entertainment, food, housing")
    assert risen_most({"food": 1.5, "housing": 1.502}) == "housing"
    assert risen_most({}) == "none"


def test_a_class_with_nobody_in_it_is_not_counted_as_a_town_with_a_number(numbers):
    data, con, _, _ = numbers
    empty = con.execute("SELECT setting, year, COUNT(*) FROM yearly WHERE scope = 'out' AND metric = 'n' AND value = 0 "
                        "GROUP BY setting, year").fetchall()
    assert empty, "the test towns always have someone out of work: pick others"
    for setting, year, towns_with_nobody in empty:
        all_towns = next(row["n"] for row in data["settings"][setting]["yearly"]["out/n"] if row["year"] == year)
        rows = [row for row in data["settings"][setting]["yearly"].get("out/unhappy", []) if row["year"] == year]
        assert (rows[0]["n"] if rows else 0) == all_towns - towns_with_nobody


def test_the_end_of_the_towns_is_spread_the_same_way(numbers):
    data, con, _, _ = numbers
    for setting in data["settings"]:
        summaries = [json.loads(text) for (text,) in con.execute(
            "SELECT summary FROM towns WHERE setting = ? ORDER BY seed", (setting["setting"],))]
        end = setting["end"]
        assert end["failed_year"] == spread(setting["failed"])
        assert end["top10_shares"] == spread([s["top10_shares"] for s in summaries])
        assert end["gini_shares"] == spread([s["gini_shares"] for s in summaries])
        for scope in CLASSES:
            assert end["unhappy"][scope] == spread([s["unhappy"][scope] for s in summaries if s["class_counts"][scope] > 0])
        counts = {}
        for s in summaries:
            top = max(s["price_ratio"].values())
            level = sorted(need for need, ratio in s["price_ratio"].items() if top - ratio <= 0.001)
            name = level[0] if len(level) == 1 else "level: " + ", ".join(level)
            counts[name] = counts.get(name, 0) + 1
        assert setting["needs"] == counts and sum(counts.values()) == 8
        failed = setting["failed"]
        assert setting["half_failed"] == (sorted(failed)[3] if len(failed) >= 4 else None)   # half of eight
        assert setting["planned"] == 4


def test_a_varied_dial_lists_the_base_and_each_value(numbers):
    data, _, _, _ = numbers
    assert data["varied"] == [{"dial": "failure_unhappy_share", "rows": [
        {"setting": 1, "value": 0.25, "base": False}, {"setting": 0, "value": 0.35, "base": True}]}]   # in order of value


def test_a_batch_in_which_no_town_fails(tmp_path):
    plan = batch.make_plan("calm", [1, 2, 3], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        data = report_data(con)
    finally:
        con.close()
    only = data["settings"][0]
    assert (only["failed"], only["survived"], only["n"]) == ([], 3, 3)
    assert only["standing"] == [[0, 1.0], [1.0, 1.0]]
    assert only["end"]["failed_year"] is None and only["half_failed"] is None and only["planned"] == 1
    assert data["varied"] == []


def test_a_batch_of_one_town(tmp_path):
    plan = batch.make_plan("one", [5], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        data = report_data(con)
    finally:
        con.close()
    row = data["settings"][0]["yearly"]["town/wage"][0]
    assert row["n"] == 1 and row["min"] == row["q1"] == row["median"] == row["q3"] == row["max"]


def test_a_batch_with_no_finished_town_at_all(tmp_path):
    import shutil
    plan = batch.make_plan("empty", [1], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    shutil.rmtree(batch_dir / "towns")
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        data = report_data(con)
    finally:
        con.close()
    assert (data["batch"]["planned"], data["batch"]["finished"]) == (1, 0)
    only = data["settings"][0]
    assert (only["n"], only["towns"], only["failed"], only["standing"], only["yearly"]) == (0, [], [], [], {})
    assert (only["half_failed"], only["planned"], only["needs"]) == (None, 0, {})


# --- the page ---------------------------------------------------------------------------------------------
import html as html_lib   # noqa: E402
import re                 # noqa: E402
import shutil             # noqa: E402

from engine.batchpage import build_batch_page   # noqa: E402


def tips(text):
    """Every text shown under the pointer, as written in the page."""
    return [html_lib.unescape(tip) for tip in re.findall(r'data-tip="([^"]*)"', text)]


def section(page, name):
    """One section of the page, by its id."""
    return re.search(rf'<section id="{name}".*?</section>', page, re.S).group(0)


def chart(page, setting, measure):
    """The year-by-year chart of one measure for one setting: its whole card."""
    found = re.search(rf'<figure class="card" data-setting="{setting}" data-measure="{re.escape(measure)}".*?</figure>',
                      page, re.S)
    return found.group(0) if found else None


def number(text):
    """The first number in a piece of text, whatever it is dressed in."""
    return float(re.search(r"-?[\d,]+(?:\.\d+)?", text.replace("$", "")).group(0).replace(",", ""))


@pytest.fixture(scope="module")
def page(numbers):
    data, _, _, batch_dir = numbers
    path = build_batch_page(batch_dir)
    return path.read_text(encoding="utf-8"), data, batch_dir


def test_the_page_is_written_beside_the_table_and_fetches_nothing(page):
    text, _, batch_dir = page
    assert (batch_dir / "batch.html").is_file()
    for forbidden in ("<script src", "<link", "@import", "url(", "fetch(", "XMLHttpRequest", "import("):
        assert forbidden not in text                         # it opens offline
    assert text.count("<script>") == 1
    assert "Untuned" in text and "not a finding" in text


def test_the_page_builds_from_the_table_alone(numbers, tmp_path):
    _, _, _, batch_dir = numbers
    alone = tmp_path / "alone"
    alone.mkdir()
    shutil.copy(batch_dir / "batch.sqlite", alone / "batch.sqlite")           # no plan file, no towns
    built = build_batch_page(alone).read_text(encoding="utf-8")
    assert built == (batch_dir / "batch.html").read_text(encoding="utf-8")
    assert sorted(p.name for p in alone.iterdir()) == ["batch.html", "batch.sqlite"]


def test_the_page_says_what_was_run(page):
    text, data, _ = page
    head = re.search(r"<header>.*?</header>", text, re.S).group(0)
    assert "Batch mixed" in head and "16 towns" in head and "2 settings" in head and "8 seeds" in head
    assert data["batch"]["code"] in head
    assert f"{len(data['settings'][0]['failed'])} of 8 towns failed" in head


def test_there_is_one_dot_for_each_town_that_failed_at_its_year(page):
    text, data, _ = page
    ended = section(text, "ended")
    for setting in data["settings"]:
        row = re.search(rf'<g class="row" data-setting="{setting["setting"]}".*?</g>', ended, re.S).group(0)
        dots = tips(row)
        dots = [tip for tip in dots if tip.startswith("Seed ")]
        assert len(dots) == len(setting["failed"])
        for town in setting["towns"]:
            if town["failed_year"] is not None:
                assert f"Seed {town['seed']}|failed in year {town['failed_year']:.2f} (week {town['failed_week']})" in dots
        assert row.count("<circle") == len(setting["failed"])


def test_the_dots_sit_at_their_year_along_the_line_of_years(page):
    text, data, _ = page
    ended = section(text, "ended")
    row = re.search(r'<g class="row" data-setting="1".*?</g>', ended, re.S).group(0)
    placed = sorted((float(x), tip) for x, tip in re.findall(r'<circle[^>]*cx="([\d.]+)"[^>]*data-tip="([^"]*)"', row))
    years = [number(tip.split("|")[1]) for _, tip in placed]
    assert years == sorted(years) and len(placed) == 8       # further right is later
    assert placed[0][0] < placed[-1][0]


def test_the_page_says_how_many_towns_failed_and_how_many_stand(page):
    text, data, _ = page
    ended = section(text, "ended")
    base, strict = data["settings"]
    assert f"{len(base['failed'])} of 8 failed" in ended and f"{base['survived']} still standing after 4 years" in ended
    assert "8 of 8 failed" in ended


def test_the_share_still_standing_is_drawn_step_by_step(page):
    text, data, _ = page
    ended = section(text, "ended")
    steps = [tip for tip in tips(ended) if "still standing" in tip and tip.startswith("Year ")]
    for setting in data["settings"]:
        for year, share in setting["standing"][1:]:
            left = round(share * setting["n"])
            assert f"Year {year:.2f}|{setting['name']}|{left} of {setting['n']} towns still standing" in steps


def test_each_years_numbers_under_the_pointer_are_the_tables(page):
    text, data, _ = page
    checked = 0
    for setting in data["settings"]:
        for measure in ("all/unhappy", "town/wage", "town/homes_vacant", "working/cash_median", "town/top10_shares"):
            rows = setting["yearly"].get(measure)
            card = chart(text, setting["setting"], measure)
            if not rows:
                assert card is None
                continue
            shown = [tip.split("|") for tip in tips(card)]
            assert len(shown) == len(rows)
            # shares are written as a percentage to one place, money in whole dollars, counts to one place
            scale, near = ((100, 0.051) if measure in ("all/unhappy", "town/top10_shares")
                           else (0.01, 0.51) if measure in ("town/wage", "working/cash_median") else (1, 0.051))
            for parts, row in zip(shown, rows):
                assert parts[0] == f"Year {row['year']}"
                assert number(parts[1]) == pytest.approx(row["median"] * scale, abs=near)
                low, high = parts[2].split(" to ")
                assert number(low) == pytest.approx(row["q1"] * scale, abs=near)
                assert number(high) == pytest.approx(row["q3"] * scale, abs=near)
                low, high = parts[3].split(" to ")
                assert number(low) == pytest.approx(row["min"] * scale, abs=near)
                assert number(high) == pytest.approx(row["max"] * scale, abs=near)
                assert parts[4] == (f"{row['n']} towns" if row["n"] != 1 else "1 town")
                checked += 1
    assert checked > 20


def test_each_chart_has_its_table_and_says_how_many_towns_it_rests_on(page):
    text, data, _ = page
    card = chart(text, 0, "all/unhappy")
    rows = data["settings"][0]["yearly"]["all/unhappy"]
    cells = re.findall(r"<tr><td>(\d+)</td><td>(\d+)</td>", card)
    assert [(int(year), int(n)) for year, n in cells] == [(row["year"], row["n"]) for row in rows]
    assert f"{rows[0]['n']} towns in year 1" in card and f"{rows[-1]['n']} in year 4" in card


def test_every_town_is_listed_with_its_fingerprint_and_its_folder(page):
    text, data, _ = page
    every = section(text, "towns")
    for setting in data["settings"]:
        for town in setting["towns"]:
            assert town["fingerprint"][:16] in every and town["folder"] in every
    assert every.count("<tr>") == 16 + 1                     # one row a town, and the heading


def test_the_end_of_the_towns_is_in_words_and_numbers(page):
    text, data, _ = page
    end = section(text, "end")
    for setting in data["settings"]:
        assert html_lib.escape(setting["name"]) in end
        middle = setting["end"]["failed_year"]["median"]
        assert f"{middle:.2f}" in end
        for need, count in setting["needs"].items():
            assert f"{need} {count}" in end


def test_what_each_dial_did_is_shown_only_when_a_dial_was_varied(page, tmp_path):
    text, data, _ = page
    dials = section(text, "dials")
    assert "failure_unhappy_share" in dials and ">0.25<" in dials and "0.35 (the base)" in dials
    plan = batch.make_plan("plain", [1, 2], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    batch.collect(batch_dir)
    plain = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert 'id="dials"' not in plain and "None of the 2 towns failed" in plain
    assert "still standing after 1 year" in plain
    for name in ("ended", "years", "end", "towns", "read"):
        assert f'<section id="{name}"' in plain


def test_the_page_says_when_towns_are_missing(tmp_path):
    plan = batch.make_plan("holes", [1, 2, 3], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    shutil.rmtree(batch.town_dir(batch_dir, plan["settings"][0], 1))
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "1 of 3 towns is missing or unfinished" in text
    shutil.rmtree(batch_dir / "towns")
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "3 of 3 towns are missing or unfinished" in text and "No town of this batch has finished" in text


def test_a_batch_of_one_town_still_draws(tmp_path):
    plan = batch.make_plan("one", [5], base=SMALL)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "1 town" in text and "NaN" not in text and "None" not in text.replace("None of the", "")
    assert chart(text, 0, "town/wage") is not None


def test_a_name_that_is_not_safe_as_html_is_escaped(tmp_path):
    odd = tmp_path / "odd<b>&.json"
    odd.write_text(json.dumps({"population_cap": 30, "years": 1}))
    plan = batch.make_plan("odd", [1], config=str(odd))
    batch_dir = batch.run_batch(plan, out_root=tmp_path / "batches", jobs=1, quiet=True)
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "odd&lt;b&gt;&amp;.json" in text and "odd<b>" not in text


def test_the_colours_are_the_dashboards(page):
    from engine import dashboard

    def colours(text):
        return re.findall(r"--series-1: (#\w+); --series-2: (#\w+); --series-3: (#\w+);", text)

    assert colours(batchpage.TEMPLATE) == colours(dashboard.TEMPLATE)
    assert len(colours(batchpage.TEMPLATE)) == 3              # light, dark by the system, dark by choice


def test_nothing_on_the_page_is_not_a_number(page):
    text, _, _ = page
    assert "NaN" not in text and "nan" not in re.sub(r"[A-Za-z]nan|nan[A-Za-z]", "", text)
    assert "None" not in text.replace("None of the", "")
    assert not re.search(r'="[^"]*\binf\b', text)


# --- what the review found the tests could not see ----------------------------------------------------------
def cells(table_html):
    """The rows of a table as lists of cell text."""
    return [[html_lib.unescape(re.sub(r"<[^>]+>", "", cell)) for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            for row in re.findall(r"<tr>(.*?)</tr>", table_html, re.S)]


def test_the_headline_gives_the_middle_of_the_towns_that_failed_and_says_so(page):
    text, data, _ = page
    base = data["settings"][0]
    found = base["end"]["failed_year"]
    sub = re.search(r'<div class="herosub">(.*?)</div>', text, re.S).group(1)
    assert f"Of the {len(base['failed'])} that failed, the middle one failed in year {found['median']:.2f}" in sub
    assert f"the first in year {found['min']:.2f} and the last in year {found['max']:.2f}" in sub
    assert f"Half of all 8 towns had failed by year {base['half_failed']:.2f}" in sub
    were = "was" if base["survived"] == 1 else "were"
    assert f"{base['survived']} {were} still standing after 4 years" in sub


def test_the_bar_under_the_dots_is_the_middle_half_of_the_towns_that_failed(page):
    text, data, _ = page
    ended = section(text, "ended")
    for setting in data["settings"]:
        row = re.search(rf'<g class="row" data-setting="{setting["setting"]}".*?</g>', ended, re.S).group(0)
        tip = [t for t in tips(row) if not t.startswith("Seed ")][0].split("|")
        found = setting["end"]["failed_year"]
        assert number(tip[1].split("failed in year")[1]) == pytest.approx(found["median"], abs=0.006)
        low, high = tip[2].split(" to ")
        assert number(low.replace("middle half", "")) == pytest.approx(found["q1"], abs=0.006)
        assert number(high) == pytest.approx(found["q3"], abs=0.006)
        assert f"first {found['min']:.2f}, last {found['max']:.2f}" in tip[3]
        if setting["survived"]:
            assert tip[1].startswith(f"of the {len(setting['failed'])} that failed")


def test_a_dot_sits_at_its_year_between_the_marks_of_the_years(page):
    text, data, _ = page
    ended = section(text, "ended")
    strip = re.search(r'<svg[^>]*aria-label="The year each town failed.*?</svg>', ended, re.S).group(0)
    marks = {int(label): float(x) for x, label in re.findall(r'<text x="([\d.]+)" y="[\d.]+" text-anchor="middle">(\d+)</text>', strip)}
    assert 0 in marks and 4 in marks and max(marks) == 4      # the line of years runs for as long as the towns were given
    line = [(float(a), float(b)) for a, b, c, d in re.findall(
        r'<line x1="([\d.]+)" x2="([\d.]+)" y1="([\d.]+)" y2="([\d.]+)" stroke="var\(--axis\)"/>', strip) if c == d and a != b]
    assert line == [(marks[0], marks[4])]                     # and the years fill the whole line, end to end
    width = float(re.search(r'viewBox="0 0 ([\d.]+) ', strip).group(1))
    assert marks[0] < 20 and marks[4] > width - 20
    per_year = (marks[4] - marks[0]) / 4
    seen = 0
    for cx, tip in re.findall(r'<circle cx="([\d.]+)"[^>]*data-tip="([^"]*)"', strip):
        year = number(tip.split("|")[1])
        assert float(cx) == pytest.approx(marks[0] + per_year * year, abs=per_year * 0.006 + 0.06)
        seen += 1
    assert seen == sum(len(s["failed"]) for s in data["settings"])


def test_towns_that_fail_in_the_same_week_are_not_drawn_on_top_of_each_other(page):
    text, data, _ = page
    ended = section(text, "ended")
    strict = data["settings"][1]
    weeks = [town["failed_week"] for town in strict["towns"]]
    assert len(weeks) - len(set(weeks)) >= 2, "no two test towns fail in the same week: pick other towns"
    row = re.search(r'<g class="row" data-setting="1".*?</g>', ended, re.S).group(0)
    places = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', row)
    assert len(places) == len(set(places)) == 8
    for i, (x1, y1) in enumerate(places):
        for x2, y2 in places[i + 1:]:
            assert abs(float(x1) - float(x2)) >= 9 or abs(float(y1) - float(y2)) >= 9   # a dot is 8 across


def test_the_share_still_standing_starts_at_the_top_and_only_goes_down(page):
    text, data, _ = page
    ended = section(text, "ended")
    chart_svg = re.search(r'<svg[^>]*aria-label="The share of towns still standing.*?</svg>', ended, re.S).group(0)
    top = float(re.search(r'<text x="[\d.]+" y="([\d.]+)" text-anchor="end">100%</text>', chart_svg).group(1))
    bottom = float(re.search(r'<text x="[\d.]+" y="([\d.]+)" text-anchor="end">0%</text>', chart_svg).group(1))
    assert top < bottom                                       # all the towns is the top of the chart
    paths = re.findall(r'<path class="series" d="([^"]+)"', chart_svg)
    assert len(paths) == 2
    for d, setting in zip(paths, data["settings"]):
        start_y = float(re.match(r"M[\d.]+,([\d.]+)", d).group(1))
        drops = [float(v) for v in re.findall(r"V([\d.]+)", d)]
        assert start_y == pytest.approx(top - 4, abs=0.6)       # the label sits four units under its line
        assert drops == sorted(drops) and drops[0] > start_y
        share = setting["standing"][-1][1]
        assert drops[-1] == pytest.approx(start_y + (bottom - top) * (1 - share), abs=0.6)
    assert 'stroke-dasharray' in chart_svg                    # the second line is not told apart by colour alone
    legend = re.search(r'<ul class="legend">.*?</ul>', ended, re.S).group(0)
    for setting in data["settings"]:
        assert f"{html_lib.escape(setting['name'])}: {100 * setting['standing'][-1][1]:.0f}% still standing at the end" in legend


def test_a_years_chart_puts_more_higher_and_later_further_right(page):
    text, data, _ = page
    rows = data["settings"][0]["yearly"]["town/wage"]
    card = chart(text, 0, "town/wage")
    points = [tuple(map(float, pair.split(","))) for pair in
              re.search(r'<polyline class="series" points="([^"]+)"', card).group(1).split()]
    assert len(points) == len(rows) >= 3
    assert [x for x, _ in points] == sorted(x for x, _ in points) and points[0][0] < points[-1][0]
    grid = {(float(a), float(b)) for a, b in re.findall(r'<line x1="([\d.]+)" x2="([\d.]+)" y1="[\d.]+" y2="[\d.]+" stroke="var\(--grid\)"/>', card)}
    assert grid == {(points[0][0], points[-1][0])}            # the years run from one side of the chart to the other
    moved = 0
    for (_, y1), (_, y2), a, b in zip(points, points[1:], rows, rows[1:]):
        if a["median"] != b["median"]:
            assert (y2 < y1) == (b["median"] > a["median"])   # up the page is more
            moved += 1
    assert moved >= 1
    zero = float(re.search(r'<text x="[\d.]+" y="([\d.]+)" text-anchor="end">\$0</text>', card).group(1))
    assert all(y < zero for _, y in points)


def test_each_charts_table_runs_from_lowest_to_highest(page):
    text, data, _ = page
    for measure, scale, near in (("all/unhappy", 100, 0.051), ("town/wage", 0.01, 0.51), ("town/homes", 1, 0.051)):
        rows = data["settings"][0]["yearly"][measure]
        table = cells(chart(text, 0, measure))
        assert table[0] == ["Year", "Towns", "Lowest", "First quarter", "Middle", "Third quarter", "Highest"]
        assert len(table) - 1 == len(rows)
        for line, row in zip(table[1:], rows):
            assert (int(line[0]), int(line[1])) == (row["year"], row["n"])
            for cell, key in zip(line[2:], ("min", "q1", "median", "q3", "max")):
                assert number(cell) == pytest.approx(row[key] * scale, abs=near)


def test_the_table_of_the_last_week_has_each_number_under_its_own_name(page):
    text, data, _ = page
    table = {row[0]: row[1:] for row in cells(section(text, "end"))}
    assert table["In the last week"] == [s["name"] for s in data["settings"]]
    for i, setting in enumerate(data["settings"]):
        end = setting["end"]
        assert int(table["Towns"][i]) == setting["n"]
        assert int(table["Failed"][i]) == len(setting["failed"])
        assert int(table["Still standing"][i]) == setting["survived"]
        assert number(table["Year of failure, of the towns that failed"][i]) == pytest.approx(end["failed_year"]["median"], abs=0.006)
        half = table["Half of all the towns had failed by year"][i]
        assert (number(half) == pytest.approx(setting["half_failed"], abs=0.006) if setting["half_failed"] is not None
                else half == "more than half never failed")
        assert number(table["Shares held by the top tenth"][i]) == pytest.approx(100 * end["top10_shares"]["median"], abs=0.051)
        assert number(table["Gini of shares"][i]) == pytest.approx(end["gini_shares"]["median"], abs=0.006)
        for label, scope in (("Unhappy: everyone", "all"), ("Unhappy: owner class", "owner"),
                             ("Unhappy: working class", "working"), ("Unhappy: out of work", "out")):
            found = end["unhappy"][scope]
            assert (number(table[label][i]) == pytest.approx(100 * found["median"], abs=0.051) if found
                    else table[label][i] == "none")


def made_up():
    """Two settings in which every number is different, so no two can be swapped unseen.
    The shared test towns cannot show that: their owners and their workers are equally content."""
    def around(value):
        return {"n": 5, "min": value - 0.02, "q1": value - 0.01, "median": value, "q3": value + 0.01, "max": value + 0.02}

    def setting(number, name, k):
        return {"setting": number, "name": name, "overrides": [] if number == 0 else [f"dial={k}"], "dials": {"dial": k},
                "towns": [], "n": 9 + number, "failed": [1.0 + k] * (4 + number), "survived": 2 + 3 * number,
                "planned": 60, "half_failed": 7.11 + k, "standing": [[0, 1.0], [60, 0.5]], "yearly": {},
                "end": {"failed_year": around(3.3 + k), "top10_shares": around(0.55 + k / 100),
                        "gini_shares": around(0.66 + k / 100),
                        "unhappy": {"all": around(0.44 + k / 100), "owner": around(0.11 + k / 100),
                                    "working": around(0.22 + k / 100), "out": around(0.33 + k / 100)}},
                "needs": {"food": 3 + number, "housing": 1}}

    return {"batch": {"name": "made-up", "code": "c", "planned": 19, "finished": 19, "seeds": [1], "record": []},
            "settings": [setting(0, "the base", 1), setting(1, "dial=2", 2)],
            "varied": [{"dial": "dial", "rows": [{"setting": 0, "value": 1, "base": True},
                                                 {"setting": 1, "value": 2, "base": False}]}]}


def test_every_cell_of_the_last_week_is_under_its_own_name():
    table = {row[0]: row[1:] for row in cells(batchpage._end_section(made_up()))}
    assert table == {
        "In the last week": ["the base", "dial=2"],
        "Towns": ["9", "10"],
        "Failed": ["4", "5"],
        "Still standing": ["2", "5"],
        "Year of failure, of the towns that failed": ["4.30 (4.29 to 4.31)", "5.30 (5.29 to 5.31)"],
        "Half of all the towns had failed by year": ["8.11", "9.11"],
        "Shares held by the top tenth": ["56.0% (55.0% to 57.0%)", "57.0% (56.0% to 58.0%)"],
        "Gini of shares": ["0.67", "0.68"],
        "Unhappy: everyone": ["45.0%", "46.0%"],
        "Unhappy: owner class": ["12.0%", "13.0%"],
        "Unhappy: working class": ["23.0%", "24.0%"],
        "Unhappy: out of work": ["34.0%", "35.0%"],
        "Need whose price had risen most, and in how many towns": ["food 3, housing 1", "food 4, housing 1"],
    }


def test_with_many_settings_the_last_week_is_turned_with_every_cell_still_under_its_name():
    data = made_up()
    data["settings"] = [dict(data["settings"][i % 2], setting=i, name=f"s{i}") for i in range(5)]
    table = cells(batchpage._end_section(data))
    assert table[0][:5] == ["Setting", "Towns", "Failed", "Still standing", "Year of failure, of the towns that failed"]
    assert table[0][9:12] == ["Unhappy: owner class", "Unhappy: working class", "Unhappy: out of work"]
    assert [row[0] for row in table[1:]] == ["s0", "s1", "s2", "s3", "s4"]
    assert table[2][1:4] == ["10", "5", "5"] and table[2][9:12] == ["13.0%", "24.0%", "35.0%"]


def test_every_cell_of_a_dials_table_is_under_its_own_name():
    table = cells(batchpage._dials_section(made_up()))
    assert table[0] == ["dial", "Towns", "Failed", "Still standing",
                        "Year of failure, of the towns that failed: middle (middle half)", "First to last",
                        "Half of all the towns had failed by year"]
    assert table[1:] == [["1 (the base)", "9", "4", "2", "4.30 (4.29 to 4.31)", "4.28 to 4.32", "8.11"],
                         ["2", "10", "5", "5", "5.30 (5.29 to 5.31)", "5.28 to 5.32", "9.11"]]


def test_the_table_of_a_dial_has_each_number_under_its_own_name(page):
    text, data, _ = page
    table = cells(section(text, "dials"))
    assert table[0] == ["failure_unhappy_share", "Towns", "Failed", "Still standing",
                        "Year of failure, of the towns that failed: middle (middle half)", "First to last",
                        "Half of all the towns had failed by year"]
    by_value = {row[0]: row[1:] for row in table[1:]}
    for label, setting in (("0.25", data["settings"][1]), ("0.35 (the base)", data["settings"][0])):
        got = by_value[label]
        assert [int(got[0]), int(got[1]), int(got[2])] == [setting["n"], len(setting["failed"]), setting["survived"]]
        assert number(got[3]) == pytest.approx(setting["end"]["failed_year"]["median"], abs=0.006)
        assert got[4] == f"{setting['end']['failed_year']['min']:.2f} to {setting['end']['failed_year']['max']:.2f}"
        assert number(got[5]) == pytest.approx(setting["half_failed"], abs=0.006)


def test_every_town_is_listed_with_the_year_it_failed_and_the_year_it_filled(page):
    text, data, _ = page
    rows = cells(section(text, "towns"))
    assert rows[0][:4] == ["Setting", "Seed", "How it ended", "Town full in year"]
    listed = {(row[0], int(row[1])): row for row in rows[1:]}
    differ = 0
    for setting in data["settings"]:
        for town in setting["towns"]:
            row = listed[(setting["name"], town["seed"])]
            ended = (f"failed in year {town['failed_year']:.2f}" if town["failed_year"] is not None
                     else "still standing after 4 years")
            full = f"{town['full_year']:.2f}" if town["full_year"] is not None else "never"
            assert (row[2], row[3]) == (ended, full)
            differ += town["failed_year"] is not None and town["full_year"] is not None and ended[-4:] != full[-4:]
    assert differ >= 3                                        # so the two years cannot be swapped unseen


def test_every_measure_in_the_table_has_its_chart_but_the_one_that_is_said_twice(page):
    text, data, _ = page
    for setting in data["settings"]:
        for key in setting["yearly"]:
            assert (chart(text, setting["setting"], key) is None) == (key == "all/n"), key   # people in town says it
    assert len(batchpage.CHARTS) == 29 and len({spec[0] for spec in batchpage.CHARTS}) == 29
    assert {spec[0] for spec in batchpage.CHARTS} == {f"{scope}/{metric}" for scope, metric in batch.MEASURES} - {"all/n"}


def test_no_chart_marks_its_side_with_the_same_number_twice(page):
    text, data, _ = page
    for card in re.findall(r'<figure class="card" data-setting="\d+" data-measure="[^"]+".*?</figure>', text, re.S):
        side = re.findall(r'text-anchor="end">([^<]*)</text>', card)
        assert len(side) == len(set(side)) >= 2, side


def test_round_numbers_for_the_side_and_the_foot_of_a_chart():
    from engine.batchpage import _ticks, _year_ticks
    assert _ticks(0.9, "pct") == [0, 0.25, 0.5, 0.75, 1.0]
    assert _ticks(0, "money") == [0, 100] and _ticks(0, "count") == [0, 1]   # nothing to show still has two marks
    assert _ticks(103_800, "money")[-1] >= 103_800
    for last in (4, 21, 60, 800, 5000, 123_456):
        marks = _year_ticks(0, last)
        assert 2 <= len(marks) <= 9 and marks[0] == 0 and marks[-1] <= last


def test_the_page_says_how_to_make_a_town_again_in_full(page):
    text, _, _ = page
    read = section(text, "read")
    assert "python run.py --config FOLDER/config.json --set snapshot_every=1" in read
    assert "level" in read                                    # what "risen most" does with a tie


def test_a_batch_that_counts_its_years_in_other_weeks(tmp_path):
    plan = batch.make_plan("weeks", [1, 2, 3, 4, 5, 6], base=["population_cap=40", "years=4", "failure_unhappy_share=0.25",
                                                             "weeks_per_year=48", "quarter_weeks=12"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=3, quiet=True)
    con = sqlite3.connect(batch.collect(batch_dir))
    try:
        data = report_data(con)
        rows = con.execute("SELECT seed, failed_week, weeks, year_weeks, folder FROM towns ORDER BY seed").fetchall()
        years = {seed: {year for (year,) in con.execute("SELECT DISTINCT year FROM yearly WHERE seed = ?", (seed,))}
                 for seed, *_ in rows}
        wage = {(seed, year): value for seed, year, value in con.execute(
            "SELECT seed, year, value FROM yearly WHERE scope = 'town' AND metric = 'wage'")}
    finally:
        con.close()
    assert {year_weeks for _, _, _, year_weeks, _ in rows} == {48}
    failed = [(seed, week) for seed, week, _, _, _ in rows if week is not None]
    assert len(failed) >= 3 and any(week % 48 for _, week in failed)
    assert data["settings"][0]["failed"] == sorted(week / 48 for _, week in failed)
    for seed, _, weeks, _, folder in rows:
        assert years[seed] == set(range(1, weeks // 48 + 1))          # a year is 48 weeks here
        town = sqlite3.connect(batch_dir / folder / "run.sqlite")
        try:
            for year in years[seed]:
                assert wage[(seed, year)] == town.execute(
                    "SELECT value FROM series WHERE week = ? AND scope = 'town' AND metric = 'wage'", (48 * year,)).fetchone()[0]
        finally:
            town.close()
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    for seed, week in failed:
        assert f"Seed {seed}|failed in year {week / 48:.2f} (week {week})" in tips(text)


def test_more_than_four_settings_are_never_drawn_on_one_chart(tmp_path):
    plan = batch.make_plan("five", [1, 2], base=SMALL, vary=["failure_unhappy_share=0.5,0.6,0.7,0.8", "habit_weeks=104"])
    assert len(plan["settings"]) == 6
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=3, quiet=True)
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    ended = section(text, "ended")
    charts = re.findall(r'<svg[^>]*aria-label="The share of towns still standing.*?</svg>', ended, re.S)
    assert len(charts) == 3                                   # the dial with four values takes two charts
    drawn = set()
    for one in charts:
        lines = re.findall(r'<path class="series"', one)
        assert 2 <= len(lines) <= 4
    legends = re.findall(r'<ul class="legend">(.*?)</ul>', ended, re.S)
    for legend in legends:
        names = re.findall(r"</svg>([^<:]+):", legend)
        assert names[0] == "population_cap=30, years=1" and len(names) <= 4    # the base is on every chart
        drawn |= set(names)
    assert drawn == {s["name"] for s in plan["settings"]}
    strip = re.search(r'<svg[^>]*aria-label="The year each town failed.*?</svg>', ended, re.S).group(0)
    assert len(re.findall(r'<g class="row"', strip)) == 6     # the dots have a row for every setting


def test_a_name_that_is_not_safe_is_escaped_wherever_it_is_written(tmp_path):
    odd = tmp_path / "odd<b>&.json"
    odd.write_text(json.dumps({"population_cap": 30, "years": 1}))
    plan = batch.make_plan("odd2", [1], config=str(odd), vary=["habit_weeks=104"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path / "batches", jobs=1, quiet=True)
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "odd<b>" not in text and "<b>&" not in text
    assert text.count("odd&lt;b&gt;&amp;.json") >= 6         # header, dots, legend, last week, the dial, every town
    assert "odd&lt;b&gt;&amp;.json" in re.search(r'<ul class="legend">.*?</ul>', text, re.S).group(0)
    assert "<summary>habit_weeks=104</summary>" in text       # the folded group of the other setting


def test_a_part_finished_batch_says_it_leans_toward_early_failure(tmp_path):
    plan = batch.make_plan("part", [1, 2, 3], base=SMALL, vary=["habit_weeks=104"])
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=2, quiet=True)
    shutil.rmtree(batch_dir / "towns" / "base")
    batch.collect(batch_dir)
    text = build_batch_page(batch_dir).read_text(encoding="utf-8")
    assert "3 of 6 towns are missing or unfinished" in text
    assert "towns that fail soonest finish first" in text
    assert "No town under the base has finished" in text and "No town of this batch has finished" not in text


def test_a_name_is_escaped_in_the_key_and_in_the_folded_groups():
    data = made_up()
    data["settings"][1]["name"] = "x<y>&z"
    for piece in (batchpage._years_section(data), batchpage._ended(data), batchpage._end_section(data),
                  batchpage._towns_section(data)):
        assert "x<y>" not in piece
    assert "<summary>x&lt;y&gt;&amp;z</summary>" in batchpage._years_section(data)
    assert "x&lt;y&gt;&amp;z: 50% still standing at the end" in batchpage._ended(data)


def test_the_line_of_dots_is_drawn_round_the_failures_when_they_all_come_late():
    from engine.batchpage import _dot_span
    late = [("a", {"failed": [13.25, 16.5, 20.96]}), ("b", {"failed": [15.0]})]
    assert _dot_span(late, 60) == (12, 22)                    # all 100 towns of the first batch failed in these years
    early = [("a", {"failed": [0.5, 3.75]}), ("b", {"failed": []})]
    assert _dot_span(early, 4) == (0, 4)                      # from nought, and never past the years given
    assert _dot_span([("a", {"failed": []})], 60) == (0, 60)
    assert _dot_span([("a", {"failed": [59.9]})], 60) == (58, 60)
    assert _dot_span([("a", {"failed": [0.2]})], 0.5) == (0, 1)


def test_the_step_chart_runs_the_whole_of_the_years_the_towns_were_given(page):
    text, data, _ = page
    chart_svg = re.search(r'<svg[^>]*aria-label="The share of towns still standing.*?</svg>', section(text, "ended"), re.S).group(0)
    years = [int(label) for label in re.findall(r'text-anchor="middle">(\d+)</text>', chart_svg)]
    assert years[0] == 0 and years[-1] == 4                   # the towns were given four years
    ends = [float(re.findall(r"H([\d.]+)", d)[-1]) for d in re.findall(r'<path class="series" d="([^"]+)"', chart_svg)]
    right_edge = max(float(x2) for x2 in re.findall(r'<line x1="[\d.]+" x2="([\d.]+)"', chart_svg))
    assert ends == [right_edge, right_edge]                   # each line is carried level to the last year given


# --- stage 3 of the RTR world: its measures across a batch (20 November 2026) ----------------

RTR_PAIR = ["world=rtr", "population_cap=60", "years=3"]
RTR_MEASURES = ("town/wage_offer", "town/homes_lived_in_by_owner", "town/homes_let_private",
                "town/homes_foreclosed", "town/sets_owned", "town/home_loans", "town/makers",
                "town/small_businesses")


@pytest.fixture(scope="module")
def rtr_pair(tmp_path_factory):
    plan = batch.make_plan("rtrpair", [3, 9], base=RTR_PAIR)
    batch_dir = batch.run_batch(plan, out_root=tmp_path_factory.mktemp("rtrbatch"), jobs=1, quiet=True)
    batch.collect(batch_dir)
    return batch_dir


def test_an_rtr_batch_keeps_its_own_measures_every_year(rtr_pair):
    con = sqlite3.connect(rtr_pair / "batch.sqlite")
    try:
        kept = {(seed, year, f"{scope}/{metric}"): value for seed, year, scope, metric, value in con.execute(
            "SELECT seed, year, scope, metric, value FROM yearly")}
        folders = dict(con.execute("SELECT seed, folder FROM towns"))
    finally:
        con.close()
    for seed in (3, 9):
        for year in (1, 2, 3):
            for measure in RTR_MEASURES:
                assert (seed, year, measure) in kept, (seed, year, measure)
        town = sqlite3.connect(rtr_pair / folders[seed] / "run.sqlite")
        week = {m: v for m, v in town.execute(
            "SELECT metric, value FROM series WHERE scope='town' AND week=104")}
        town.close()
        assert kept[(seed, 2, "town/homes_lived_in_by_owner")] == week["homes_owned"] - week["homes_let_private"]
        assert kept[(seed, 2, "town/wage_offer")] == week["wage_offer"]
        assert kept[(seed, 2, "town/makers")] == week["makers"]


def test_an_rtr_batch_page_draws_its_own_measures(rtr_pair):
    html = build_batch_page(rtr_pair).read_text(encoding="utf-8")
    for measure in RTR_MEASURES:
        assert chart(html, 0, measure), measure
    assert "Homes lived in by their owner" in chart(html, 0, "town/homes_lived_in_by_owner")


def test_an_rtr_batch_made_before_these_measures_still_builds(rtr_pair, tmp_path):
    old = tmp_path / "old"
    shutil.copytree(rtr_pair, old)
    con = sqlite3.connect(old / "batch.sqlite")
    con.execute("DELETE FROM yearly WHERE metric IN ('wage_offer', 'homes_lived_in_by_owner', 'makers')")
    con.commit()
    con.close()
    html = build_batch_page(old).read_text(encoding="utf-8")
    assert not chart(html, 0, "town/wage_offer") and chart(html, 0, "town/sets_owned")
