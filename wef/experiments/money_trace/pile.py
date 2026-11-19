"""Across a batch: at the end of a year, how much of the town's money the owner class and its top five hold,
and the year's exports (from the weekly town measures)."""
import sys, json, sqlite3, pathlib, statistics as st
from multiprocessing import Pool
batch, folder, year = sys.argv[1], sys.argv[2], int(sys.argv[3])
week = year * 52
def one(d):
    s = json.loads((d / "summary.json").read_text())
    if s["failed_week"] is not None and s["failed_week"] <= week:
        return None
    con = sqlite3.connect((d / "run.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    snap = con.execute("SELECT MAX(week) FROM agent_snap WHERE week <= ?", (week,)).fetchone()[0]
    rows = con.execute("SELECT klass, cash FROM agent_snap WHERE week = ?", (snap,)).fetchall()
    firms = con.execute("SELECT COALESCE(SUM(cash), 0) FROM firm_snap WHERE week = ?", (snap,)).fetchone()[0]
    con.close()
    agents = sum(c for _, c in rows)
    owners = sorted((c for k, c in rows if k == "owner"), reverse=True)
    money = agents + firms
    return (snap, sum(owners) / money, sum(owners[:5]) / money, sum(c for k, c in rows if k == "working") / money, firms / money, money / 1e8)
with Pool(12) as pool:
    got = [g for g in pool.map(one, sorted(pathlib.Path(batch, "towns", folder).iterdir())) if g is not None]
cols = list(zip(*got))
print(batch, "year", year, "towns", len(got), "snapshot weeks", sorted(set(cols[0])))
for i, name in ((1, "owner class share of money"), (2, "top five people's share"), (3, "working class share"), (4, "firms' share"), (5, "money $M")):
    v = sorted(cols[i])
    print(f"  {name:28s} middle {st.median(v):.3g}  middle half {v[len(v)//4]:.3g} to {v[3*len(v)//4]:.3g}  range {v[0]:.3g} to {v[-1]:.3g}")
