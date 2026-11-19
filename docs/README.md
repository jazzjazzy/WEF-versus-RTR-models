# The build records

**Start with [how-this-was-built.md](how-this-was-built.md):** who did what, the method, what
was built when, and what went wrong along the way. The rest of this folder is the detail
behind it.

These are the design notes, plans and ledgers written while the two worlds were built. They
are kept as they were written, so they are a true record of what was decided and when.

Some names in them have since changed (17 November 2026), when the two worlds were given a
folder each:

| In these records | Now |
|---|---|
| the code folder `wefworld/` | `engine/` |
| `wefworld/owning.py` | `engine/rtr_owning.py` |
| `python -m wefworld run` | `python run.py`, from `wef/` or `rtr/` |
| `python -m wefworld run --set world=rtr` | `python run.py`, from `rtr/` |
| `python -m wefworld batch` | `python batch.py`, from `wef/` or `rtr/` |
| `configs/before-16-november.json`, `configs/sloped-exports.json` | the same files in `wef/` |
| `configs/rtr.json` | `rtr/settings.json` |
| `runs/`, `batches/` | `wef/runs/`, `wef/batches/` (and `rtr/runs/`, `rtr/batches/`) |
| `experiments/` | `wef/experiments/` |

Files with `rtr` in their name are about the RTR world. The rest are about the WEF world or
the engine both share.

Two small changes were made to these records on 19 November 2026, before the repository was
made public: the notes' own name for Claude was changed to "Claude" in three files, and one
sentence that named an unrelated folder was reworded. Nothing else in them was altered.

These records quote commit IDs (seven letters and digits, such as `4039ae9`) and branch names.
They are those of the private working repository in which the model was built. This public
repository starts from a single snapshot taken on 19 November 2026, so those IDs and branches
are not in its history. The records also name scratch scripts that were never part of the
repository.
