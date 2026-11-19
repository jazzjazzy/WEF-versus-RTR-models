"""Shared test helpers. An "empty town" has the rules but no founders, so a test
can place exactly the agents and firms it needs."""

import pytest

from engine.config import load_config
from engine.town import Town


# Until 18 November 2026 the RTR world's bank lent four fifths of a home's price and the buyer found
# the other fifth in cash. Jason ruled "Lend the whole price". The dial is still there, and the tests
# written for the fifth still hold it: one marked `fifth_in_cash` gets its hand-built towns with the
# dial at 0.8. (A town a test builds from `load_config` itself says so in its own settings.)
FIFTH_IN_CASH = ["mortgage_ltv=0.8"]
# Until 19 November 2026 a firm had one rate for all its staff, and the line that let it cut that
# rate was everyone with no job. Jason ruled that staff already there keep their pay and that only
# those who would take the job are in the line. Whole towns whose seeds were picked before that
# hold these dials.
BEFORE_THE_LINE = ["staff_keep_pay=false", "line_is_who_would_take=false", "unhappy_makers_apply=false"]
# The RTR world as stage 2 was merged, before any of Jason's rulings of 18 and 19 November: for whole
# towns whose seeds were picked then. Towns as the world now ships are run in test_rtr_rulings.py.
BEFORE_THE_RULINGS = FIFTH_IN_CASH + ["newcomers_buy=false", "owners_pay_any_price=false", "makers_weigh_jobs=false",
                                      "makers_buy_in_town=false"] + BEFORE_THE_LINE
_OLD_LOAN: list[str] = []


@pytest.fixture(autouse=True)
def _the_loan_a_test_was_written_for(request):
    _OLD_LOAN[:] = FIFTH_IN_CASH if request.node.get_closest_marker("fifth_in_cash") else []
    yield
    _OLD_LOAN[:] = []


def empty_town(*overrides: str) -> Town:
    """Rules but no founders and, unless a test asks for one, no map: stage 1 tests place
    things by hand and do not care where they are."""
    return Town(load_config(None, ["map_width=0"] + _OLD_LOAN + list(overrides)), setup=False)


def wef_main(argv) -> int:
    """The command line as a town of the WEF world is run (the world's own folder is not used,
    so a test's runs land where the test says)."""
    from engine.__main__ import main
    return main(argv, world="wef")


def map_town(*overrides: str) -> Town:
    """An empty town with the default map, for tests about places."""
    return Town(load_config(None, _OLD_LOAN + list(overrides)), setup=False)


def small_town(*overrides: str) -> Town:
    """A full town with founders, capped small so tests run in seconds."""
    base = ["population_cap=120", "years=8"]
    return Town(load_config(None, base + list(overrides)))


@pytest.fixture
def town() -> Town:
    return empty_town()


def what_happened(town) -> tuple[str, int]:
    """Everything a town recorded, as one number: the record's own fingerprint (every
    event with all its detail, and every weekly measure), and how many events there were."""
    return town.rec.fingerprint()[:16], town.rec.event_count


# The batch tests check the batch, not the model: their towns keep the rules they were chosen under.
from engine.config import OLD_RULES  # noqa: E402
MIXED = OLD_RULES + ["population_cap=40", "years=4", "failure_unhappy_share=0.35"]


@pytest.fixture(scope="session")
def mixed_batch(tmp_path_factory):
    """Sixteen small towns, shared by the tests of the batch table and of its page. Under
    the base some towns fail and some are still standing after four years. Under the
    stricter failure rule every town fails, several of them inside their first year.
    Returns the batch's folder and its plan. Tests must not change the towns."""
    from engine import batch
    root = tmp_path_factory.mktemp("mixed")
    plan = batch.make_plan("mixed", list(range(1, 9)), base=MIXED, vary=["failure_unhappy_share=0.25"])
    return batch.run_batch(plan, out_root=root, jobs=4, quiet=True), plan
