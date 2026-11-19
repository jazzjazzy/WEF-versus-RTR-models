# WEF versus RTR models

One town economy, run as two worlds.

**The question** (Jason, 12 November 2026): if companies keep moving toward
"you will own nothing", does that world hold together, or does it collapse in on
itself, and why? And what happens in the opposite world, where people may own,
repair and build?

| World | Folder | In a sentence |
|---|---|---|
| **WEF** | [wef/](wef/README.md) | A town where nobody owns anything: everything is rented or on subscription, as in the 2016 World Economic Forum essay. Only housing firms own homes. |
| **RTR** (Right to Repair) | [rtr/](rtr/README.md) | The same town, except that people may also rent or buy, build a home or an appliance of their own, keep it up themselves, and let homes to others. |

Each world has a folder of its own, and **you run a world from its folder**.
Nobody chooses a world by setting a dial: the folder you are in is the world.
Each folder holds that world's page, its settings, its scripts, and what its
runs leave behind.

> **Untuned.** The build so far proves the machinery: the accounts balance, the
> places hold together, runs repeat exactly, and every week is recorded. The
> starting values have not been tested, and the RTR world is only part built.
> Nothing here is a finding yet.

## Run a world

Python 3.12, nothing to install.

```bash
cd wef
python run.py --seed 1          # one town of the WEF world
python batch.py first --seeds 1-30
```

```bash
cd rtr
python run.py --seed 1          # one town of the RTR world
python batch.py first --seeds 1-30
```

Every run says which world it is: on its first line, in its `summary.json`, and
at the top of its dashboard and its town view. A world's folder will not run
the other world.

The rest (what a run leaves behind, the pages, many towns at once, the rules,
and what the towns have done so far) is on each world's page:
[wef/README.md](wef/README.md) and [rtr/README.md](rtr/README.md).

To read what a run left, or build its pages again, from this top folder:

```bash
python -m engine info wef/runs/<folder>
python -m engine dashboard wef/runs/<folder>
python -m engine town rtr/runs/<folder>
python -m engine batch-report wef/batches/<name>
python -m pytest
```

## How the two are joined

Both worlds run on one engine. The WEF world is the engine with nothing added.
The RTR world is the engine plus two files of rules,
[engine/rtr_owning.py](engine/rtr_owning.py) (owning) and
[engine/rtr_makers.py](engine/rtr_makers.py) (makers), which run only in
an RTR town. A WEF town gives the same record, event for event, whether or not
those files exist, and the tests hold it to that: WEF towns recorded before the RTR world
was begun are run again and must match.

## Layout

| Path | What it is |
|---|---|
| `wef/` | **The WEF world.** `README.md` (its rules, Jason's rulings, what its towns did), `settings.json` (every dial), `run.py` (one town), `batch.py` (many towns), `runs/` and `batches/` (what they leave; not kept in git), `before-16-november.json` and `sloped-exports.json` (other settings), `experiments/` (diagnostics that are not part of the model) |
| `rtr/` | **The RTR world.** `README.md`, `settings.json`, `run.py`, `batch.py`, `runs/` and `batches/` |
| `engine/` | The code both worlds share |
| `engine/config.py` | Every dial, and the names of the two worlds |
| `engine/town.py` | The town and the week in order |
| `engine/places.py` | The map: spots, distance, reach, rent by location, land, finding a home |
| `engine/household.py` | Bills, coping, share orders, security, wellbeing, class |
| `engine/corporate.py` | Quarterly review, prices, dividends, new firms, failure, takeover |
| `engine/labour.py` | Hiring, layoffs, promotions, arrivals, wages |
| `engine/production.py` | The working week: service, upkeep, decay, building, making, trade |
| `engine/bank.py`, `broker.py`, `ledger.py` | The bank, the share market, and the one function all money moves through |
| `engine/rtr_owning.py` | **RTR only.** Spare time, a set and a home of one's own, their upkeep, buying from a landlord, letting, foreclosure and the sale for the debt |
| `engine/rtr_makers.py` | **RTR only.** Makers: a person selling their own spare time as food, entertainment, something thought up, repairs or building; their prices, customers and till; ideas; the bank's loan on profit, staff, and becoming a company |
| `engine/recorder.py`, `metrics.py` | The record and the weekly measures |
| `engine/dashboard.py`, `runner.py` | The dashboard and one run end to end |
| `engine/townview.py`, `townpage.py` | The town view: what it reads from the record, and the page itself |
| `engine/batch.py`, `batchpage.py` | Many towns: planning and running a batch, the table of all its towns, and the page built from that table |
| `engine/__main__.py` | The command line the world folders' scripts call |
| `tests/` | 1,156 tests. The ones that matter most run a whole town and check the accounts and the places every week. `test_rtr*.py` are the RTR world's; `test_worlds.py` holds the two apart. |
| `docs/` | How each part was designed and built: design notes, plans, and a ledger of every call made while building. They were written as the work was done and are kept as written; see [docs/README.md](docs/README.md) for names that have since changed. |

## How this was made

The rules were set by Jason in conversation. The model, the tests and this text
were written by Claude (an AI) under his direction.
[docs/how-this-was-built.md](docs/how-this-was-built.md) says who did what, the
method, what was built when, and what went wrong along the way.

## Licence

MIT: see [LICENSE](LICENSE). Anyone may use, copy, change and share this, for any
purpose, so long as the notice in that file stays with it. It comes with no warranty.
