"""Where the town's money sits at each year end, and what crossed the boundary that year."""
import sys, collections
from engine.config import load_config, OLD_RULES
from engine.town import Town
from engine.recorder import NullRecorder
path, old = sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "old"
cfg = load_config(path, OLD_RULES if old else None)
town = Town(cfg, NullRecorder(keep_events=False))
M = 1e8   # cents to $ millions
prev_in, prev_out = {}, {}
print("yr  money | agents: owner working out | firms alive: housing food appl ent transport other | dead firms | loans firms people | in: arrival loan export | out: principal interest recovery import")
while town.failed_week is None and town.week < cfg.weeks:
    town.step()
    if town.week % 52:
        continue
    by_class = collections.Counter()
    for a in town.agents:
        by_class[a.klass] += a.cash
    by_need = collections.Counter()
    dead = 0
    for f in town.firms:
        if f.alive:
            by_need[f.need if f.need in ("housing", "food", "appliances", "entertainment", "transport") else "other"] += f.cash
        else:
            dead += f.cash
    lf = sum(f.loan for f in town.firms if f.alive)
    lp = sum(a.loan for a in town.agents)
    tin, tout = town.ledger.total_in, town.ledger.total_out
    yin = {k: tin.get(k, 0) - prev_in.get(k, 0) for k in ("arrival", "loan", "export")}
    yout = {k: tout.get(k, 0) - prev_out.get(k, 0) for k in ("loan_principal", "loan_interest", "loan_recovery", "import")}
    prev_in, prev_out = dict(tin), dict(tout)
    f = lambda x: f"{x / M:6.1f}"
    print(f"{town.week // 52:2d} {f(town.money_in_town())} |", " ".join(f(by_class[k]) for k in ("owner", "working", "out")), "|",
          " ".join(f(by_need[k]) for k in ("housing", "food", "appliances", "entertainment", "transport", "other")), "|", f(dead), "|",
          f(lf), f(lp), "|", " ".join(f(yin[k]) for k in yin), "|", " ".join(f(yout[k]) for k in yout))
print("failed week", town.failed_week)
