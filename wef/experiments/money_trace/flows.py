"""Inside the town, year by year: who pays whom, and how concentrated the owners' cash is."""
import sys, collections
from engine.config import load_config, OLD_RULES
from engine.town import Town
from engine.recorder import NullRecorder
path, old = sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "old"
cfg = load_config(path, OLD_RULES if old else None)
town = Town(cfg, NullRecorder(keep_events=False))
year = collections.Counter()
M = 1e8
kinds_seen = set()
print("yr | inside town ($M a year): wages dividends subscription(all spending) founding share_trade liquidation other | owners: n, cash $M, top 5 share, spend $M, income $M | staff: n, wage $")
while town.failed_week is None and town.week < cfg.weeks:
    town.step()
    for k, v in town.ledger.week_internal.items():
        year[k] += v
        kinds_seen.add(k)
    spend = collections.Counter(); income = collections.Counter()
    for a in town.agents:
        spend[a.klass] += a.spend_week; income[a.klass] += a.income_week + a.div_week
    year["owner_spend"] += spend["owner"]; year["owner_income"] += income["owner"]
    if town.week % 52:
        continue
    owners = sorted((a.cash for a in town.agents if a.klass == "owner"), reverse=True)
    staff = [a for a in town.agents if a.role == "staff"]
    known = ("wage", "dividend", "subscription", "founding", "share_trade", "liquidation")
    other = sum(v for k, v in year.items() if k not in known and k not in ("owner_spend", "owner_income"))
    print(f"{town.week // 52:2d} |", " ".join(f"{year[k] / M:6.1f}" for k in known), f"{other / M:6.1f} |",
          len(owners), f"{sum(owners) / M:6.1f}", f"{sum(owners[:5]) / max(1, sum(owners)):.0%}",
          f"{year['owner_spend'] / M:5.1f}", f"{year['owner_income'] / M:5.1f} |",
          len(staff), round(sum(a.wage for a in staff) / max(1, len(staff)) / 100))
    year = collections.Counter()
print("internal kinds:", sorted(kinds_seen))
