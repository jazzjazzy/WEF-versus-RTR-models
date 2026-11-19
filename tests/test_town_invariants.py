"""The whole town, run week by week, with the accounting checked after every step."""

import pytest

from conftest import small_town, what_happened

from engine.config import OLD_RULES

CLASSES = {"owner", "working", "out"}


def check_week(town, before_money, before_pop, seen_ids):
    """Returns a list of what went wrong this week (empty when all is well)."""
    bad = []
    week = town.week
    put_out = set()                      # tenants whose homes were pulled down for premises this week
    for e in reversed(town.rec.events):
        if e["week"] != week:
            break
        if e["kind"] == "sub_end" and e["data"].get("reason") == "redeveloped":
            put_out.add(e["agent"])
    for f in town.alive_firms:
        if f.extra != sum(a.plan.get(f.need, 1) - 1 for a in f.subs.values()):
            bad.append(f"week {week}: firm {f.id} miscounts its bigger plans")
    for u in town.foreclosed:
        tenanted = u.occupant is not None        # RTR 1b: a let home the bank took: its tenant stays and pays the bank
        if u.owner is not None or u.since is None or u.ask < 1 or u.ask > u.debt:
            bad.append(f"week {week}: foreclosed home {u.id} is owned or mispriced")
        if tenanted and (u.firm is not town.bank_lets or u.occupant.subs.get("housing") is not town.bank_lets):
            bad.append(f"week {week}: foreclosed home {u.id} is lived in by someone who is not the bank's tenant")
    if town.bank_lets is not None and town.bank_lets.cash != 0:
        bad.append(f"week {week}: the bank's letting is holding money")
    for u in town.own_units:
        let = u.rent > 0                     # RTR 1b: a home its owner lets to someone else
        if let and u in town.foreclosed:
            continue                         # the bank's: checked above
        if let and (u.owner is None or u.firm is not u.owner.lets or u not in u.firm.units):
            bad.append(f"week {week}: let home {u.id} is not in its owner's letting")
        if not let and (u.firm is not None or (u.owner is None and u not in town.foreclosed)):
            bad.append(f"week {week}: own unit {u.id} belongs to a firm or to nobody")
        if not let and u.owner is not None and (u.owner.unit.get(u.spec.name) is not u or u.occupant is not u.owner):
            bad.append(f"week {week}: own unit {u.id} is not the one its owner uses")
    for a in town.agents:
        if a.lets is None:
            continue
        for u in a.lets.units:               # every home in a person's letting is theirs, with a rent of its own
            if u.owner is not a or u.firm is not a.lets or u.rent <= 0 or u not in town.own_units:
                bad.append(f"week {week}: home {u.id} in agent {a.id}'s letting is not theirs to let")
        for t in a.lets.subs.values():
            if t.subs.get("housing") is not a.lets or t.unit.get("housing") not in a.lets.units:
                bad.append(f"week {week}: agent {a.id}'s letting lists agent {t.id} who is not its tenant")
    for h in town.hustles:                   # RTR 2: side hustles
        owner = h.owner
        if not h.alive:
            bad.append(f"week {week}: side hustle {h.id} is stopped and still listed")
        if owner.hustle is not h or town._agents.get(owner.id) is not owner:
            bad.append(f"week {week}: side hustle {h.id}'s owner does not know it")
        if h.extra != sum(a.plan.get(h.need, 1) - 1 for a in h.subs.values()):
            bad.append(f"week {week}: side hustle {h.id} miscounts its bigger plans")
        if h.spec is None and h.subs:
            bad.append(f"week {week}: side hustle {h.id} sells hours and has subscribers")
        if h.sold < -1e-9 or h.sold > h.hours + 1e-6:
            bad.append(f"week {week}: side hustle {h.id} sold more hours than it had")
        if not h.business and (h.staff or h.loan or h.reserve):
            bad.append(f"week {week}: side hustle {h.id} has staff, a loan or the bank's money and is not a business")
        if h.cash != h.reserve or h.reserve < 0:
            bad.append(f"week {week}: side hustle {h.id} has money left in its till at the week's end")
        if h.spec is None and h.business:
            bad.append(f"week {week}: side hustle {h.id} sells hours and is a business")
        if h.loan < 0 or h.loan_missed < 0:
            bad.append(f"week {week}: side hustle {h.id} has a negative loan")
        for w in h.staff:
            if w.employer is not h or w.role != "staff":
                bad.append(f"week {week}: side hustle {h.id} lists agent {w.id} who is not on its staff")
            if town.cfg.staff_keep_pay and w.wage < h.wage:
                bad.append(f"week {week}: side hustle {h.id} pays agent {w.id} under the going wage it took as its rate")
            if w is owner:
                bad.append(f"week {week}: agent {w.id} is on their own staff")
        for aid, a in h.subs.items():
            if a.subs.get(h.need) is not h:
                bad.append(f"week {week}: side hustle {h.id} lists agent {aid} who is not a customer")
            if a is owner:
                bad.append(f"week {week}: agent {aid} is their own customer")
    for a in town.agents:
        if a.hustle is not None and a.hustle not in town.hustles:
            bad.append(f"week {week}: agent {a.id}'s side hustle is not in the town's list")
    by_trade = sorted(h.id for makers in town.makers_of.values() for h in makers)
    if by_trade != sorted(h.id for h in town.hustles) or any(
            h.trade != trade for trade, makers in town.makers_of.items() for h in makers):
        bad.append(f"week {week}: the list of makers by trade is not the list of side hustles")
    loose = [u for a in town.agents if a.lets is not None for u in a.lets.units]
    loose += [u for f in town.alive_firms for u in f.units if u.rent > 0]
    if town.bank_lets is not None:
        loose += town.bank_lets.units
    if sorted(u.id for u in loose if u.occupant is None) != sorted(u.id for u in town.to_let):
        bad.append(f"week {week}: the list of loose homes to let is not the loose homes with no tenant")
    if town.cfg.rtr and week % town.cfg.quarter_weeks == 0:
        # RTR 1b: landlords sell homes after the quarter's review, so at a quarter's end the only
        # revenue a landlord has in its new quarter is the gain on the homes it has just sold
        gains = {}
        for e in reversed(town.rec.events):
            if e["week"] != week:
                break
            if e["kind"] == "home_bought" and e["firm"] is not None:
                gains[e["firm"]] = gains.get(e["firm"], 0) + max(0, e["amount"] - e["data"]["value"])
        for f in town.alive_firms:
            if f.need == "housing" and f.q_revenue != gains.get(f.id, 0):
                bad.append(f"week {week}: landlord {f.id} has not counted the gain on the homes it sold")
    money = town.money_in_town()
    if money != before_money + town.ledger.net_week():
        bad.append(f"week {week}: money moved outside the five flows "
                   f"({money - before_money} against net {town.ledger.net_week()})")
    for a in town.agents:
        if a.cash < 0 or a.loan < 0:
            bad.append(f"week {week}: agent {a.id} negative cash or debt")
        if a.klass not in CLASSES:
            bad.append(f"week {week}: agent {a.id} has class {a.klass!r}")
        if a.employer is not None:
            f = a.employer
            if not f.alive:
                bad.append(f"week {week}: agent {a.id} works for closed firm {f.id}")
            where = {"staff": f.staff, "exec": f.execs, "ceo": [f.ceo]}.get(a.role, [])
            if a not in where:
                bad.append(f"week {week}: agent {a.id} is {a.role} but not on firm {f.id}'s books")
        elif a.role is not None:
            bad.append(f"week {week}: agent {a.id} has role {a.role} and no employer")
        if a.home_loan > 0 and a.build is None and not (
                "housing" in a.unit and a.unit["housing"].owner is a):
            bad.append(f"week {week}: agent {a.id} owes on a home they neither own nor are building")
        if a.lets is not None and a.lets.units and not (
                "housing" in a.unit and a.unit["housing"].owner is a):
            bad.append(f"week {week}: agent {a.id} lets a home but does not own the one they live in")
        if a.home_loan < 0 or a.spare_hours < -1e-9:
            bad.append(f"week {week}: agent {a.id} has a negative home loan or negative hours")
        for need, u in a.unit.items():
            rented = need in a.subs and u.firm is a.subs[need]
            if not rented and u.owner is not a:
                bad.append(f"week {week}: agent {a.id} uses a {need} unit that is neither rented nor theirs")
            if u.occupant is not a:
                bad.append(f"week {week}: agent {a.id} uses a {need} unit that does not know it")
        if any(need not in a.subs or size < 2 for need, size in a.plan.items()):
            bad.append(f"week {week}: agent {a.id} has a bigger plan of something they do not hold")
        for need, f in a.subs.items():
            if not f.alive or f.need != need or f.subs.get(a.id) is not a:
                bad.append(f"week {week}: agent {a.id} subscription to {need} is broken")
            if f.spec.kind == "asset":
                u = a.unit.get(need)
                if u is None or u.occupant is not a or u.firm is not f or u not in f.units:
                    bad.append(f"week {week}: agent {a.id} has no proper {need} unit")
        for fid, n in a.shares.items():
            f = town.firm(fid)
            if not f.alive or n <= 0 or f.holders.get(a.id) != n:
                bad.append(f"week {week}: agent {a.id} holding in firm {fid} is broken")
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            owned_home = "housing" in a.unit and a.unit["housing"].owner is a    # RTR: they may buy it at once
            if a.arrived == week and "housing" not in a.subs and not owned_home and a.id not in put_out:
                bad.append(f"week {week}: agent {a.id} arrived without a home")
    for f in town.firms:
        if f.cash < 0 or f.loan < 0:
            bad.append(f"week {week}: firm {f.id} negative cash or debt")
        if f.alive:
            if sum(f.holders.values()) != f.shares_out or f.shares_out <= 0:
                bad.append(f"week {week}: firm {f.id} shares do not add up")
            keeps = town.cfg.rtr and town.cfg.staff_keep_pay     # (Jason, 19/11/2026) staff keep the rate they were hired on
            if f.own_rates != keeps:
                bad.append(f"week {week}: firm {f.id} does not know whether its staff keep their pay")
            for a in f.staff:
                if (a.wage < f.wage) if keeps else (a.wage != f.wage):
                    bad.append(f"week {week}: firm {f.id} pays agent {a.id} {'under' if keeps else 'other than'} its rate")
            for aid, a in f.subs.items():
                if a.subs.get(f.need) is not f:
                    bad.append(f"week {week}: firm {f.id} lists agent {aid} who is not a customer")
            for u in f.units:
                if u.occupant is not None and u.occupant.unit.get(f.need) is not u:
                    bad.append(f"week {week}: firm {f.id} unit {u.id} occupant mismatch")
        else:
            if f.cash != 0 or f.loan != 0 or f.shares_out != 0 or f.staff or f.execs or f.ceo or f.subs:
                bad.append(f"week {week}: closed firm {f.id} still holds something")
    if town.cfg.rtr and town.cfg.staff_keep_pay:
        # nobody who stayed on the same staff since last week is paid less than they were
        last = town.__dict__.setdefault("_pay_last_checked", {})
        now = {}
        for a in town.agents:
            if a.role == "staff":
                now[a.id] = (a.employer, a.hired_week, a.wage)
                was = last.get(a.id)
                if was is not None and was[0] is a.employer and was[1] == a.hired_week and a.wage < was[2]:
                    bad.append(f"week {week}: agent {a.id} stayed on the same staff and their pay was cut "
                               f"from {was[2]} to {a.wage}")
        last.clear()
        last.update(now)
    bad.extend(check_places(town))
    if town.population < before_pop:
        bad.append(f"week {week}: population fell")
    if town.population > town.cfg.population_cap:
        bad.append(f"week {week}: population above the cap")
    if [a.id for a in town.agents] != list(range(1, town.population + 1)):
        bad.append(f"week {week}: someone has left town")
    counts = {k: sum(1 for a in town.agents if a.klass == k) for k in CLASSES}
    if sum(counts.values()) != town.population:
        bad.append(f"week {week}: classes do not add up to the population")
    return bad


def check_places(town):
    """Where there is a map: every home stands on a spot of its firm, no spot is over full,
    no land belongs to a closed firm, and nobody ends the week holding a job or a shop
    they cannot get to."""
    from engine.places import dist, home_spot, reach
    m = town.map
    if m is None:
        return []
    bad, week, cap = [], town.week, town.cfg.homes_per_spot
    for spot in m.spots:
        where = f"week {week}: spot {spot.id}"
        if spot.kind is None:
            if spot.owner is not None or spot.user is not None or spot.units or spot.better or spot.better_let:
                bad.append(f"{where} is empty but still has an owner, a user or homes")
            continue
        if spot.kind == "service":
            continue
        if spot.kind == "plots":                 # RTR: a block of plots, each home its owner's
            if spot.owner is not None or spot.user is not None or spot.units:
                bad.append(f"{where} is a block of plots but has an owner, a user or a landlord's homes")
            if len(spot.private_units) + spot.plots_reserved > cap or spot.plots_reserved < 0:
                bad.append(f"{where} holds more plots than a block can")
            if spot.plots_reserved != sum(1 for a in town.agents if a.build is not None and a.build.spot is spot):
                bad.append(f"{where} keeps plots for builds that are not under way")
            for u in spot.private_units:
                if u.spot is not spot or (u.firm is not None and u.rent <= 0):
                    bad.append(f"{where} has a private home that belongs elsewhere")
            continue
        if spot.plots_reserved or (spot.private_units and spot.kind != "homes"):
            bad.append(f"{where} is not a block of plots but holds plots")
        for u in spot.private_units:             # RTR 1b: homes bought from the landlord stand where they stood
            if u.spot is not spot or (u.firm is not None and u.rent <= 0):
                bad.append(f"{where} has a private home that belongs elsewhere")
        if spot.owner is None or spot.user is None or not spot.owner.alive or not spot.user.alive:
            bad.append(f"{where} belongs to nobody or to a closed firm")
            continue
        if spot.kind == "premises":
            if spot.user.spot is not spot or spot.units or spot.better or spot.better_let:
                bad.append(f"{where} is premises but its firm is elsewhere, or it holds homes")
        else:
            if spot not in spot.user.lots:
                bad.append(f"{where} holds homes but is not among its firm's blocks")
            if len(spot.units) + len(spot.private_units) + spot.reserved > cap or spot.reserved < 0:
                bad.append(f"{where} holds more homes than a spot can")
            if spot.occupied != sum(1 for u in spot.units if u.occupant is not None):
                bad.append(f"{where} miscounts its let homes")
            better = [u for u in spot.units if u.scale > 1.0]
            if (spot.better, spot.better_let) != (len(better), sum(1 for u in better if u.occupant is not None)):
                bad.append(f"{where} miscounts its better homes")
            for u in spot.units:
                if u.firm is not spot.user or u.spot is not spot or u not in spot.user.units:
                    bad.append(f"{where} has a home that belongs elsewhere")
        if (spot.ground_rent > 0) != (spot.owner is not spot.user):
            bad.append(f"{where} ground rent does not match who owns and who uses it")
    for f in town.alive_firms:
        if f.spot is None or f.spot.user is not f:
            bad.append(f"week {week}: firm {f.id} has no premises")
        for lot in f.lots:
            if lot.user is not f or lot.kind != "homes":
                bad.append(f"week {week}: firm {f.id} lists a block it does not use")
        if f.need == "housing":
            for u in f.units:
                held = u.spot.private_units if u.rent > 0 and u.spot is not None else None   # RTR 1b: a single home
                if u.spot is None or u not in (u.spot.units if held is None else held):
                    bad.append(f"week {week}: home {u.id} of firm {f.id} stands nowhere")
                if u.rent > 0 and (u.owner is not None or u in town.own_units):
                    bad.append(f"week {week}: home {u.id} of firm {f.id} is also someone's own")
    for f in town.firms:
        if not f.alive and (f.spot is not None or f.lots):
            bad.append(f"week {week}: closed firm {f.id} still holds land")
    for a in town.agents:
        home = home_spot(a)
        if home is None:
            continue
        limit = reach(town, a)
        if a.role in ("staff", "exec") and dist(home, a.employer.spot) > limit:
            bad.append(f"week {week}: agent {a.id} holds a job {dist(home, a.employer.spot)} blocks away")
        for name, f in a.subs.items():
            if f.spec.trips_per_week > 0 and dist(home, f.spot) > limit:
                bad.append(f"week {week}: agent {a.id} buys {name} from out of reach")
    return bad


def run_checked(town, weeks):
    problems, seen = [], set()
    for _ in range(weeks):
        money, pop = town.money_in_town(), town.population
        town.step()
        problems.extend(check_week(town, money, pop, seen))
        if len(problems) > 20:
            break
    return problems


@pytest.fixture(scope="module")
def checked_run():
    town = small_town("stop_on_failure=false")
    problems = run_checked(town, 8 * 52)
    return town, problems


def test_the_accounts_hold_every_week(checked_run):
    town, problems = checked_run
    assert problems == []


def test_town_actually_lives(checked_run):
    town, _ = checked_run
    assert town.week == 8 * 52
    assert town.population > 40                         # people were hired and came
    assert any(a.role == "staff" for a in town.agents)
    assert sum(f.w_revenue for f in town.alive_firms) > 0
    kinds = {e["kind"] for e in town.rec.events}
    assert {"hire", "arrival", "sub_start", "firm_founded", "dividend", "class_change"} <= kinds


def test_four_founding_firms_owned_by_their_founders():
    town = small_town()
    assert [f.need for f in town.firms] == ["housing", "food", "appliances", "entertainment"]
    for f in town.firms:
        founder = town.agent(f.founder_id)
        assert f.holders == {founder.id: f.shares_out} and f.ceo is founder
        assert set(founder.subs) == {"housing", "food", "appliances", "entertainment"}
    assert town.population == 4
    assert len(town.firms[0].units) == 60 and len(town.firms[2].units) == 120   # (J) 16/11: 60 homes


def test_search_rule_also_keeps_the_accounts():
    town = small_town("price_rule=search", "stop_on_failure=false", "seed=3")
    assert run_checked(town, 6 * 52) == []


def test_forced_sale_dial_also_keeps_the_accounts():
    town = small_town("bank_can_force_share_sale=true", "stop_on_failure=false", "seed=5")
    assert run_checked(town, 6 * 52) == []


def test_town_grows_past_its_first_homes():
    town = small_town("needs.housing.initial_units=12", "needs.appliances.initial_units=12",
                      "population_cap=60", "stop_on_failure=false")
    problems = run_checked(town, 6 * 52)
    assert problems == []
    assert town.population > 12                         # homes were built and people came
    assert len(town.firms[0].units) > 12 or len(town.firms_for("housing")) > 1


# A rougher town: founders arrive often and with more money, so firms compete, fail, merge,
# sell shares and default. The accounts must hold through all of it.
ROUGH = ["population_cap=140", "stop_on_failure=false", "founder_arrival_rate=0.25", "invent_prob=0.1",
         "founder_capital_median=90000000", "resident_founder_rate=0.2",
         "map_width=0"]          # the economy on its own; towns on a map have their own checks


# What these towns did under the stage 1 code (commit a2289f9). A town with the map off is
# the stage 1 economy, so a later stage must leave these alone. If one changes, either
# something leaked into the economy by accident (stage 2 did that once: an arriving
# founder opened their firm before settling in), or a rule was changed on purpose, and
# then the new value goes here with the reason in the spec.
STAGE_ONE = {"small seed 1": ("a5d411a223f4616e", 15719),
             "rough seed 5": ("0a8838e38c704556", 14976),
             "rough seed 8": ("84042797a3dea7b1", 20480)}


def test_accounts_hold_through_failures_mergers_share_issues_and_write_offs():
    import collections
    from engine.config import load_config
    from engine.town import Town
    seen = collections.Counter()
    for seed in (5, 8):
        town = Town(load_config(None, OLD_RULES + ROUGH + [f"seed={seed}"]))   # the pinned records are of the old rules
        assert run_checked(town, 9 * 52) == []
        assert what_happened(town) == STAGE_ONE[f"rough seed {seed}"]
        for e in town.rec.events:
            seen[e["kind"]] += 1
            if e["kind"] == "takeover":
                seen["takeover by a " + e["data"]["buyer"]] += 1
            if e["kind"] == "sub_end":
                seen["sub_end: " + e["data"]["reason"]] += 1
    for kind in ("takeover by a rival", "takeover by a resident", "share_issue", "share_trade",
                 "share_grant", "writeoff", "cash_call", "default", "control_change", "firm_closed",
                 "sub_end: evicted", "sub_end: firm_closed", "sub_end: budget", "loan_called"):
        assert seen[kind] > 0, f"these runs never reached '{kind}': pick seeds that do"


# --- towns on the map ------------------------------------------------------------------------------
def test_map_off_town_runs_exactly_as_stage_one_did():
    from engine.config import load_config
    from engine.town import Town
    town = Town(load_config(None, OLD_RULES + ["population_cap=120", "stop_on_failure=false", "seed=1", "map_width=0"]))
    for _ in range(8 * 52):
        town.step()
    assert what_happened(town) == STAGE_ONE["small seed 1"]


def test_the_week_collects_ground_rent_counts_popularity_and_values_the_hour():
    town = small_town("stop_on_failure=false")
    first_blocks = town.map.homes()
    town.step()
    town.step()                                               # two weeks in: the firms have staff
    housing, food = town.firms[0], town.firms[1]
    food.spot.owner, food.spot.ground_rent = housing, 5_000   # the food firm leases its premises for $50 a week
    for f in town.firms:
        f.wage = 150_000
    hour = town.typical_wage() * town.cfg.time_value_share
    assert hour != town.hour_value                            # wages have moved since the hour was last valued
    town.step()
    assert town.ledger.week_internal.get("ground_rent") == 5_000
    assert town.hour_value == pytest.approx(hour)             # an hour on the road is valued from the wage
    assert all(s.weeks == 3 for s in first_blocks)            # every block counted each week


def test_firm_that_cannot_pay_its_ground_rent_for_four_weeks_fails():
    town = small_town("stop_on_failure=false")
    housing, food = town.firms[0], town.firms[1]
    food.spot.owner, food.spot.ground_rent = housing, 10**12  # a ground rent nobody could pay
    for _ in range(4):
        town.step()
    failed = [e for e in town.rec.events if e["kind"] == "firm_failed" and e["firm"] == food.id]
    assert [e["data"]["reason"] for e in failed] == ["ground_rent"]


def test_access_is_worked_out_afresh_each_quarter_and_land_is_valued_each_week():
    town = small_town("stop_on_failure=false")
    for _ in range(12):
        town.step()
    for spot in town.map.spots:
        spot.access = -1.0
    town.map.scarce = True                                    # suppose land had just run out
    town.step()                                               # week 13: the end of a quarter
    assert all(spot.access >= 0.0 for spot in town.map.spots)
    floor = town.cfg.land_floor
    for f in town.alive_firms:
        owned = sum(1 for s in town.map.spots if s.owner is f)
        assert f.land_value == owned * floor


def test_map_off_gives_a_town_with_no_places():
    town = small_town("map_width=0", "stop_on_failure=false")
    assert run_checked(town, 2 * 52) == []
    assert town.map is None
    assert all(f.spot is None and f.lots == [] for f in town.firms)
    assert all(a.travel_hours == 0.0 for a in town.agents)


def test_map_town_stalls_on_foot_then_grows_with_transport():
    town = small_town("population_cap=450", "stop_on_failure=false")
    assert run_checked(town, 8 * 52) == []      # six years until the rulings of 16/11
    assert town.population == 450
    events = town.rec.events
    blocked = [e["week"] for e in events if e["kind"] == "arrival_blocked"
               and e["data"].get("reason") == "no home within reach"]
    too_far = [e["week"] for e in events if e["kind"] == "too_far"]   # what the transport trigger counts
    started = [e["week"] for e in events if e["kind"] == "firm_founded" and e["data"]["need"] == "transport"]
    assert blocked and started and min(too_far) < min(started)       # kept out by distance first, then transport
    assert any("transport" in a.subs for a in town.agents)


# A rough town on a small map: land runs out early, blocks are sold, leased and pulled down,
# and transport firms come and go. The accounts and the places must hold through all of it.
# Sixteen years, because the late town is where people are put out, sleep rough and rent
# again: a fault in exactly that showed only after year twelve.
ROUGH_MAP = ["population_cap=200", "stop_on_failure=false", "founder_arrival_rate=0.25", "invent_prob=0.1",
             "founder_capital_median=90000000", "resident_founder_rate=0.2",
             "map_width=6", "map_height=6", "walk_range=3", "homes_per_spot=6", "transport_trigger=5",
             "transport_can_close=true"]          # so a transport firm can close (the rule before 16/11)


def test_places_hold_through_land_sales_leases_demolition_and_transport_closing():
    import collections
    from engine.config import load_config
    from engine.town import Town
    seen = collections.Counter()
    for seed in (8, 28):                                      # 22 until 16/11: since then a rival takeover is rarer
        town = Town(load_config(None, ROUGH_MAP + [f"seed={seed}"]))
        assert run_checked(town, 16 * 52) == []
        for e in town.rec.events:
            kind, data = e["kind"], e["data"]
            seen[kind] += 1
            if kind == "firm_founded" and data["need"] == "transport":
                seen["transport founded"] += 1
            if kind == "firm_closed" and town.firm(e["firm"]).need == "transport":
                seen["transport closed"] += 1
            if kind == "takeover":
                seen["takeover by a " + data["buyer"]] += 1
            if kind in ("sub_end", "layoff"):
                seen[f"{kind}: {data['reason']}"] += 1
    # Leases are rare now that a block of homes cannot be leased to pull it down, and so is a
    # seller repaying the bank; those have their own tests in test_places.py.
    for kind in ("land_scarce", "spot_sold", "homes_pulled_down", "no_land", "too_far",
                 "transport founded", "transport closed", "sub_end: redeveloped", "sub_end: out_of_reach",
                 "layoff: out_of_reach", "takeover by a rival", "takeover by a resident",
                 "sub_end: evicted"):
        assert seen[kind] > 0, f"these runs never reached '{kind}': pick seeds that do"


def test_same_seed_same_run_with_the_map():
    from engine.config import load_config
    from engine.town import Town
    first = Town(load_config(None, ROUGH_MAP + ["seed=2"]))
    second = Town(load_config(None, ROUGH_MAP + ["seed=2"]))
    for _ in range(5 * 52):
        first.step()
        second.step()
    assert what_happened(first) == what_happened(second)
    assert what_happened(first)[1] > 5_000
    assert any(e["kind"] == "spot_sold" for e in first.rec.events)      # far enough in to have traded land
