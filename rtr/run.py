"""Run one town of the RTR world: the Right to Repair town, where people may rent or own, build and let.

    python run.py --seed 1
    python run.py --seed 7 --years 30 --set failure_unhappy_share=0.8
    python run.py --help

The town is written to a folder of its own under runs/ here. Its settings are settings.json
in this folder. `--set` changes one of them for this run; `--config` takes a settings file of
your own in place of settings.json. Whatever you give it, a town run from this folder is a
town of the RTR world."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                # the engine both worlds share is one folder up

from engine.__main__ import world_main              # noqa: E402

if __name__ == "__main__":
    sys.exit(world_main("rtr", HERE, "run", sys.argv[1:]))
