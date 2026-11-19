from conftest import small_town


def test_run_fails_when_ninety_percent_unhappy():
    town = small_town("happy_cutoff=1.01", "failure_min_population=4")   # nobody can count as happy
    assert town.run(52) == "failed"
    assert town.failed_week == 1
    assert [e["kind"] for e in town.rec.events].count("town_failed") == 1


def test_guard_ignores_rule_below_minimum_population():
    town = small_town("happy_cutoff=1.01", "failure_min_population=20", "founder_arrival_rate=0.0",
                      "needs.housing.initial_units=4")      # four founders and no room for anyone else
    assert town.run(26) == "survived"
    assert town.failed_week is None and town.population == 4


def test_run_survives_when_everyone_counts_as_happy():
    town = small_town("happy_cutoff=0.0")
    assert town.run(3 * 52) == "survived"
    assert town.failed_week is None and town.week == 3 * 52


def test_run_can_continue_past_failure():
    town = small_town("happy_cutoff=1.01", "failure_min_population=4", "stop_on_failure=false")
    assert town.run(10) == "failed"
    assert town.failed_week == 1 and town.week == 10


def test_ninety_percent_fails_and_just_under_does_not():
    import math
    town = small_town()
    town.run(40)
    n = town.population
    assert n >= 20 and town.failed_week is None

    def make_unhappy(count):
        for i, a in enumerate(town.agents):
            a.happy = i >= count

    at_ninety = math.ceil(0.9 * n)
    make_unhappy(at_ninety - 1)                    # one person short of 90%
    town._check_failure()
    assert town.failed_week is None
    make_unhappy(at_ninety)
    town._check_failure()
    assert town.failed_week == town.week


def test_twenty_agents_eighteen_unhappy_fails_seventeen_does_not():
    from conftest import empty_town
    town = empty_town()
    agents = [town.add_agent() for _ in range(20)]
    for i, a in enumerate(agents):
        a.happy = i >= 17                          # 17 of 20 is 85%
    town._check_failure()
    assert town.failed_week is None
    agents[17].happy = False                       # 18 of 20 is 90%
    town._check_failure()
    assert town.failed_week == town.week
