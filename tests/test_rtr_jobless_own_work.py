"""The RTR world: someone who works for themselves is not counted as jobless (21 November 2026).

His words, on more towns having more people with no job after the floor on what someone out of work will
take: "trace why those towns have fewer jobs and Implement the fix."

The trace (27 towns with the floor and without it, year 60): the share counted with no job was 8.2% against
4.3%, but the share with no work at all was 0.4% against 0.2%. The rest ran a small business of their own (6.8%
against 3.5%) or a side hustle (0.9% against 0.4%). The jobless rate counted everyone with no employer. Claude's
call (C): in the RTR world it counts only those with no job and no work of their own; the old figure is kept
beside it. It is a measure only: nothing a firm or a person does reads it."""

import pytest
from test_rtr_2 import jobless, maker, quiet_town, worker

from engine.config import RTR_ONLY, load_config
from engine.corporate import line_share
from engine.metrics import weekly_series
from engine.town import Town

DIAL = "jobless_leaves_out_own_work"


def _rows(town):
    return {m: v for s, m, v in weekly_series(town) if s == "town"}


def _four(*overrides):
    """Four people: one with a job, one with no work, one with a side hustle, one with a small business."""
    town = quiet_town(*overrides)
    worker(town)
    jobless(town)
    maker(town, "entertainment")
    _, shop = maker(town, "food")
    shop.business = True
    return town


def test_the_dial_is_on_in_the_rtr_world_and_is_the_rtr_worlds_own():
    assert load_config(None, ["world=rtr"]).jobless_leaves_out_own_work is True
    assert load_config("rtr/settings.json").jobless_leaves_out_own_work is True
    assert DIAL in RTR_ONLY


def test_only_someone_with_no_job_and_no_work_of_their_own_is_jobless():
    rows = _rows(_four())
    assert rows["jobless"] == 1
    assert rows["jobless_rate"] == pytest.approx(1 / 4)


def test_the_old_figure_and_those_working_for_themselves_are_kept_beside_it():
    rows = _rows(_four())
    assert rows["no_employer_rate"] == pytest.approx(3 / 4)            # what the jobless rate counted before
    assert rows["own_business_rate"] == pytest.approx(1 / 4)
    assert rows["own_hustle_rate"] == pytest.approx(1 / 4)


def test_someone_with_a_job_and_a_side_hustle_too_is_counted_once_as_working():
    town = quiet_town()
    a = worker(town)
    maker(town, "entertainment", agent=a)
    rows = _rows(town)
    assert (rows["jobless_rate"], rows["no_employer_rate"], rows["own_hustle_rate"]) == (0, 0, 0)


def test_with_the_dial_off_the_jobless_rate_is_everyone_with_no_employer():
    town = _four(f"{DIAL}=false")
    rows = _rows(town)
    assert rows["jobless"] == 3
    assert rows["jobless_rate"] == pytest.approx(3 / 4) == town.jobless_share()


def test_a_wef_town_counts_as_before_and_keeps_no_new_measures():
    town = Town(load_config("wef/settings.json", ["population_cap=30", "years=1"]))
    for _ in range(10):
        town.step()
    rows = _rows(town)
    assert rows["jobless_rate"] == town.jobless_share()
    assert rows["jobless"] == sum(1 for a in town.agents if a.role is None)
    for name in ("no_employer_rate", "own_business_rate", "own_hustle_rate"):
        assert name not in rows


def test_the_queue_a_firm_reads_does_not_change_with_the_dial():
    on, off = _four(), _four(f"{DIAL}=false")
    for wage in (10_000, 60_000, 100_000):
        assert line_share(on, wage) == line_share(off, wage)
    on.cfg.line_is_who_would_take = off.cfg.line_is_who_would_take = False
    assert line_share(on, 60_000) == line_share(off, 60_000) == pytest.approx(3 / 4)


def test_a_batch_keeps_the_new_measures_for_each_year():
    from engine.batch import RTR_MEASURES
    for name in ("no_employer_rate", "own_business_rate", "own_hustle_rate"):
        assert ("town", name) in RTR_MEASURES
