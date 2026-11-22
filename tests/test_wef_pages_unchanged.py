"""Stage 3 of the RTR world changes what the pages show, and must not change the WEF world's pages.
The expected pages in tests/expected/ were made by `develop` at 644c166 / e6343ee (20 November 2026),
before stage 3. Only the code's own fingerprint, printed in the small print, may differ. From 22 November 2026
six rules of the RTR world hold in the WEF world too (Jason); these towns hold them off, as they were made."""

import json
import pathlib
import sqlite3

from engine import batch
from engine.batchpage import build_batch_page
from engine.config import BEFORE_SHARED_RULES, load_config
from engine.recorder import code_fingerprint
from engine.runner import run_in

EXPECTED = pathlib.Path(__file__).parent / "expected"
CODE_THEN = "9054fe6e1714181a"          # the code fingerprint of develop when the expected pages were made


def same_but_the_code(now: str, then: str) -> bool:
    return now.replace(code_fingerprint(), "CODE") == then.replace(CODE_THEN, "CODE")


def test_a_wef_towns_dashboard_and_town_view_are_unchanged(tmp_path):
    run_dir = tmp_path / "wef-seed9"
    run_dir.mkdir()
    run_in(load_config(None, ["population_cap=40", "years=3", "seed=9"] + BEFORE_SHARED_RULES), run_dir, quiet=True)
    for name in ("dashboard.html", "town.html"):
        now = (run_dir / name).read_text(encoding="utf-8")
        then = (EXPECTED / f"wef-seed9-{name}").read_text(encoding="utf-8")
        assert same_but_the_code(now, then), name


def test_a_wef_batch_keeps_the_same_yearly_figures_and_its_page_is_unchanged(tmp_path):
    plan = batch.make_plan("wefpair", [1, 2], base=["population_cap=30", "years=2"] + BEFORE_SHARED_RULES)
    batch_dir = batch.run_batch(plan, out_root=tmp_path, jobs=1, quiet=True)
    batch.collect(batch_dir)
    page = build_batch_page(batch_dir).read_text(encoding="utf-8")
    page = page.replace(", " + ", ".join(BEFORE_SHARED_RULES), "")   # the page names the dials its towns were given
    assert same_but_the_code(page, (EXPECTED / "wef-pair-batch.html").read_text(encoding="utf-8"))
    con = sqlite3.connect(batch_dir / "batch.sqlite")
    rows = sorted(list(r) for r in con.execute("SELECT setting, seed, year, scope, metric, value FROM yearly"))
    con.close()
    assert rows == json.loads((EXPECTED / "wef-pair-yearly.json").read_text())
