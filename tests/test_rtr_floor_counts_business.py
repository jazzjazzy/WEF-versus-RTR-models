"""The RTR world: someone out of work who runs a small business or side hustle of their own takes a job when
the job's pay and what the business would still bring in cover their basics (22 November 2026).

The trace (27 towns at year 60, the floor on and off): of those with no job running a business of their own,
241 of 1,663 were unhappy with the floor against 39 of 850 without it. Of the unhappy with the floor, 74% had a
least-they-would-take above the going wage ($1,535 in the middle, against $793), and they had been out of work a
median 454 weeks. The floor set the job's pay alone against their whole basics, though taking a job does not
close a business. Put to him as Mia (basics $900, a business bringing in $620, a job at $790, and the business on
the hours left after the job bringing in perhaps $200): "Yes, that makes a lot more logical sense." (J)

What the business would still bring in is Claude's reckoning (C): what it brought in a week over the last
quarter, in proportion to the hours it would have with the owner in a job (theirs less a job's 40, and its
staff's), against what it used last quarter."""

import pytest
from test_rtr_2 import maker, quiet_town as _quiet_town

from engine.config import RTR_ONLY, load_config
from engine.household import basket_cost
from engine.labour import in_the_line, reservation_wage
from engine.rtr_makers import kept_with_a_job

DIAL = "floor_counts_kept_business"


def quiet_town(*overrides):
    return _quiet_town("reservation_covers_basket=true", f"{DIAL}=true", *overrides)


def mia(town, gross=62_000, used=60.0, staff_wages=(), own_hours=None):
    """Out of work a long time, unhappy, running a side hustle of her own: last quarter it took in `gross`
    a week less goods, on `used` hours a week; `staff_wages` are what its staff are paid."""
    a, hustle = maker(town, "entertainment")
    a.role, a.last_wage, a.weeks_out, a.security, a.happy = None, 100_000, 500, 0.5, False
    a.travel_hours = 0.0
    hustle.gross_week, hustle.used_week = gross, used
    hustle.profit_week = gross - sum(staff_wages)
    hustle.staff = []
    for w in staff_wages:
        s = town.add_agent(cash=0)
        s.wage = w
        hustle.staff.append(s)
    hustle.own_hours = town.cfg.free_hours if own_hours is None else own_hours
    hustle.hours = hustle.own_hours + town.cfg.job_hours * len(hustle.staff)
    return a, hustle


def test_working_it_alone_she_keeps_the_share_of_hours_a_job_leaves_her():
    town = quiet_town()
    _, hustle = mia(town, gross=60_000, used=60.0)
    assert kept_with_a_job(town, hustle) == 20_000                         # 20 of the 60 hours she used


def test_with_staff_the_takings_follow_the_hours_and_the_wages_do_not():
    town = quiet_town()
    _, hustle = mia(town, gross=200_000, used=100.0, staff_wages=[100_000])
    assert kept_with_a_job(town, hustle) == 20_000                         # 60 of 100 hours: 120,000 less 100,000 of wages


def test_a_business_that_used_few_hours_keeps_all_it_took_in():
    town = quiet_town()
    _, hustle = mia(town, gross=60_000, used=15.0)                         # 20 hours are left beside a job
    assert kept_with_a_job(town, hustle) == 60_000


def test_with_no_hours_left_after_a_job_it_keeps_nothing():
    town = quiet_town(f"free_hours=35")
    _, hustle = mia(town, gross=60_000, used=35.0)
    assert kept_with_a_job(town, hustle) == 0


def test_staff_dearer_than_the_takings_beside_a_job_leave_nothing_not_less():
    town = quiet_town()
    _, hustle = mia(town, gross=100_000, used=100.0, staff_wages=[90_000])
    assert kept_with_a_job(town, hustle) == 0                              # 60,000 less 90,000: nothing


def test_just_let_go_her_hours_beside_a_job_are_reckoned_from_now_not_from_her_old_week():
    town = quiet_town()
    _, hustle = mia(town, gross=30_000, used=20.0, own_hours=20.0)         # last quarter, with her old job: 20 hours
    assert kept_with_a_job(town, hustle) == 30_000                          # a new job leaves her those same 20


def test_a_shorter_working_week_leaves_more_hours():
    town = quiet_town("job_hours=30")
    _, hustle = mia(town, gross=60_000, used=60.0)
    assert kept_with_a_job(town, hustle) == 30_000


def test_the_road_and_her_own_upkeep_come_out_of_the_hours_first():
    town = quiet_town()
    a, hustle = mia(town, gross=60_000, used=60.0)
    a.travel_hours = 5.0
    assert kept_with_a_job(town, hustle) == 15_000


def test_her_floor_is_her_basics_less_what_the_business_would_still_bring_in():
    town = quiet_town()
    a, hustle = mia(town)
    assert 0 < kept_with_a_job(town, hustle) < basket_cost(town, a, loan=False)
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a, loan=False) - kept_with_a_job(town, hustle)


def test_newly_out_of_work_the_business_does_not_lower_what_they_held_out_for_before():
    town = quiet_town()
    a, _ = mia(town, gross=60_000)
    a.weeks_out, a.last_wage, a.security = 1, 300_000, 0.9
    alone = int(a.last_wage * a.security * (1.0 - town.cfg.reservation_decay * a.weeks_out))
    assert alone > basket_cost(town, a, loan=False)
    assert reservation_wage(town.cfg, a, town) == alone


def test_mia_takes_a_job_that_with_the_business_covers_her_basics():
    town = quiet_town()
    a, hustle = mia(town, gross=60_000, used=60.0)
    basics = basket_cost(town, a, loan=False)
    assert basics > 20_000
    job = basics - 20_000                                                  # below her basics on its own
    assert in_the_line(town, job) == 1
    assert in_the_line(town, job - 1) == 0
    town.cfg.floor_counts_kept_business = False
    assert in_the_line(town, job) == 0                                     # before: the job alone against her basics


def test_her_floor_never_goes_below_nothing():
    town = quiet_town()
    a, _ = mia(town, gross=10_000_000, used=60.0)
    assert reservation_wage(town.cfg, a, town) == 0


def test_someone_with_no_business_is_held_to_their_basics_as_before():
    from engine.labour import reservation_wage as rw
    town = quiet_town()
    a = town.add_agent(cash=0)
    a.role, a.last_wage, a.weeks_out, a.security = None, 100_000, 500, 0.5
    assert rw(town.cfg, a, town) == basket_cost(town, a, loan=False)


def test_with_the_dial_off_the_business_is_not_counted():
    town = quiet_town(f"{DIAL}=false")
    a, _ = mia(town)
    assert reservation_wage(town.cfg, a, town) == basket_cost(town, a, loan=False)


def test_a_happy_maker_still_wants_more_than_the_business_brings_in():
    from engine.rtr_makers import least_wage
    town = quiet_town()
    a, hustle = mia(town, gross=60_000)
    a.happy = True
    assert least_wage(town, a, reservation_wage(town.cfg, a, town)) >= 60_001   # his "Yes, take it", unchanged


def test_the_quarter_records_what_a_business_took_in_less_goods_and_the_hours_it_used():
    from engine.rtr_makers import hours_per_customer, quarter
    town = quiet_town()
    _, hustle = mia(town)
    hustle.started = -1000
    q = town.cfg.quarter_weeks
    hustle.q_revenue, hustle.q_goods, hustle.q_wages = 130_000 * q, 30_000 * q, 40_000 * q
    hustle.q_sold, hustle.q_could = 30.0, 120.0                            # plans served, and could have
    quarter(town)
    assert hustle.alive
    assert hustle.profit_week == 60_000
    assert hustle.gross_week == 100_000
    assert hustle.used_week == pytest.approx(30.0 * hours_per_customer(town.cfg, hustle.spec) / q)


def test_for_a_trade_that_sells_hours_the_hours_used_are_the_hours_sold():
    from engine.rtr_makers import quarter
    town = quiet_town()
    _, hustle = maker(town, "repair")
    hustle.started = -1000
    q = town.cfg.quarter_weeks
    hustle.q_revenue, hustle.q_sold, hustle.q_could = 50_000 * q, 26.0 * q, 40.0 * q
    quarter(town)
    assert hustle.used_week == pytest.approx(26.0)
