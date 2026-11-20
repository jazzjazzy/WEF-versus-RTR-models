"""Stage 3 of the RTR world (20 November 2026): the WEF world and the RTR world on the same seeds, side
by side. Small batches with the failure line at 30%, so that some towns fail and some stand."""

import re
import shutil
import sqlite3

import pytest

from engine import batch
from engine.comparepage import CompareError, build_compare_page, compare_data
from engine.__main__ import main

SEEDS = [1, 2, 3, 4, 5, 6]
BASE = ["population_cap=40", "years=4", "failure_unhappy_share=0.3"]


def make(root, name, world, seeds=SEEDS, vary=()):
    plan = batch.make_plan(name, seeds, base=[f"world={world}", *BASE], vary=vary)
    batch_dir = batch.run_batch(plan, out_root=root, jobs=1, quiet=True)
    batch.collect(batch_dir)
    return batch_dir


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    root = tmp_path_factory.mktemp("compare")
    return make(root, "wefside", "wef"), make(root, "rtrside", "rtr")


def failed_years(batch_dir):
    con = sqlite3.connect(batch_dir / "batch.sqlite")
    try:
        return {seed: (None if failed is None else failed / weeks_a_year) for seed, failed, weeks_a_year in
                con.execute("SELECT seed, failed_week, year_weeks FROM towns")}
    finally:
        con.close()


def test_town_for_town_is_each_batchs_own_record(pair):
    wef, rtr = pair
    data = compare_data(wef, rtr)
    wef_failed, rtr_failed = failed_years(wef), failed_years(rtr)
    assert [row["seed"] for row in data["towns"]] == SEEDS
    for row in data["towns"]:
        assert row["wef"] == wef_failed[row["seed"]]
        assert row["rtr"] == rtr_failed[row["seed"]]
    assert any(row["wef"] is not None for row in data["towns"])        # these settings give a mix
    assert any(row["wef"] is None for row in data["towns"])


def test_the_four_cases_add_up_to_the_seeds(pair):
    data = compare_data(*pair)
    cases = data["cases"]
    assert set(cases) == {"both", "only_wef", "only_rtr", "neither"}
    assert sum(cases.values()) == len(SEEDS)
    wef_failed, rtr_failed = failed_years(pair[0]), failed_years(pair[1])
    assert cases["both"] == sum(1 for s in SEEDS if wef_failed[s] is not None and rtr_failed[s] is not None)
    assert cases["only_wef"] == sum(1 for s in SEEDS if wef_failed[s] is not None and rtr_failed[s] is None)
    assert cases["neither"] == sum(1 for s in SEEDS if wef_failed[s] is None and rtr_failed[s] is None)
    for world, failed in (("wef", wef_failed), ("rtr", rtr_failed)):
        assert data[world]["failed"] == sum(1 for v in failed.values() if v is not None)


def test_the_longer_lasting_town_is_named_in_each_row(pair):
    data = compare_data(*pair)
    for row in data["towns"]:
        wef, rtr = row["wef"], row["rtr"]
        if wef is None and rtr is None:
            assert row["longer"] == "neither failed"
        elif wef is None:
            assert row["longer"] == "WEF world"
        elif rtr is None:
            assert row["longer"] == "RTR world"
        else:
            assert row["longer"] == ("RTR world" if rtr > wef else "WEF world" if wef > rtr else "the same")


def test_the_page_has_every_part_in_order(pair, tmp_path):
    path = build_compare_page(*pair, out_dir=tmp_path)
    assert path == tmp_path / "compare.html"
    html = path.read_text(encoding="utf-8")
    order = [html.index(f'<section id="{name}"') for name in ("answer", "towns", "measures", "rtr-only", "read")]
    assert order == sorted(order)
    data = compare_data(*pair)
    answer = re.search(r'<section id="answer".*?</section>', html, re.S).group(0)
    assert f"{data['wef']['failed']} of 6" in answer and f"{data['rtr']['failed']} of 6" in answer
    towns = re.search(r'<section id="towns".*?</section>', html, re.S).group(0)
    assert len(re.findall(r"<tr data-seed=", towns)) == 6
    for chart in ("all/unhappy", "town/wage", "town/jobless_rate", "town/population"):
        assert f'data-measure="{chart}"' in html, chart
    assert "WEF world" in html and "RTR world" in html
    assert "drop out" in re.search(r'<section id="read".*?</section>', html, re.S).group(0)
    for forbidden in ("<script src", "<link", "@import", "url("):
        assert forbidden not in html
    assert "—" not in html                                       # no em dashes


def test_the_page_goes_beside_the_rtr_batch_by_default(pair):
    path = build_compare_page(*pair)
    assert path == pair[1] / "compare.html"


def test_it_refuses_the_wrong_worlds(pair, tmp_path):
    wef, rtr = pair
    with pytest.raises(CompareError, match="the first batch must be of the WEF world"):
        compare_data(rtr, wef)
    with pytest.raises(CompareError, match="the first batch must be of the WEF world"):
        compare_data(rtr, rtr)
    with pytest.raises(CompareError, match="the second batch must be of the RTR world"):
        compare_data(wef, wef)


def test_it_refuses_different_seeds_and_more_than_one_setting(pair, tmp_path):
    wef, _ = pair
    other = make(tmp_path, "fewer", "rtr", seeds=[1, 2])
    with pytest.raises(CompareError, match="the same seeds"):
        compare_data(wef, other)
    varied = make(tmp_path, "varied", "rtr", seeds=SEEDS, vary=["happy_cutoff=0.4"])
    with pytest.raises(CompareError, match="one setting"):
        compare_data(wef, varied)


def test_the_command_writes_the_page_and_says_where(pair, tmp_path, capsys):
    assert main(["compare", str(pair[0]), str(pair[1]), "--out", str(tmp_path)]) == 0
    assert (tmp_path / "compare.html").is_file()
    assert str(tmp_path / "compare.html") in capsys.readouterr().out
    assert main(["compare", str(pair[1]), str(pair[0]), "--out", str(tmp_path)]) == 2
    assert "the first batch must be of the WEF world" in capsys.readouterr().err


def test_a_batch_with_no_table_yet_is_collected_first(pair, tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(pair[1], copy)
    (copy / "batch.sqlite").unlink()
    assert len(compare_data(pair[0], copy)["towns"]) == 6


def test_the_page_warns_that_the_basket_is_posted_prices_not_what_owners_pay(pair, tmp_path):
    html = build_compare_page(*pair, out_dir=tmp_path).read_text(encoding="utf-8")
    read = re.search(r'<section id="read".*?</section>', html, re.S).group(0)
    assert "The basket is the cheapest price on offer" in read
    assert "people who own their home pay no rent" in read


# --- after the review (20 November 2026) -------------------------------------------------------------

def test_the_basket_cards_themselves_say_they_are_asking_prices_nobody_may_be_paying(pair, tmp_path):
    html = build_compare_page(*pair, out_dir=tmp_path).read_text(encoding="utf-8")
    for measure in ("town/basket", "town/affordability"):
        card = re.search(rf'<figure class="card" data-measure="{re.escape(measure)}".*?</figure>', html, re.S).group(0)
        assert "asking prices" in card and "no tenants or customers" in card, measure
    read = re.search(r'<section id="read".*?</section>', html, re.S).group(0)
    assert "no tenants" in read and "appliance" in read
    assert "few tenants left" not in read


def test_the_answer_says_the_horizon_and_never_says_never(pair, tmp_path):
    data = compare_data(*pair)
    html = build_compare_page(*pair, out_dir=tmp_path).read_text(encoding="utf-8")
    answer = re.search(r'<section id="answer".*?</section>', html, re.S).group(0)
    assert "never" not in answer.lower()
    assert f"in {data['wef']['planned']:g} years" in answer
    near = data["near_line"]["rtr"]
    assert set(near) == {"year", "standing", "at_80"}
    assert f"{near['at_80']} of the {near['standing']}" in answer
    con = sqlite3.connect(pair[1] / "batch.sqlite")
    ended = dict(con.execute("SELECT seed, failed_week FROM towns"))
    shares = [v for seed, v in con.execute(
        "SELECT seed, value FROM yearly WHERE scope='all' AND metric='unhappy' AND year=?", (near["year"],))
        if ended[seed] is None or ended[seed] > near["year"] * 52]
    con.close()
    assert near["standing"] == len(shares) and near["at_80"] == sum(1 for v in shares if v >= 0.8)
