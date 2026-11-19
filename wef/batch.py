"""Run many towns of the WEF world at once: every setting on every seed.

    python batch.py first --seeds 1-30
    python batch.py prices --seeds 1-100 --vary price_rule=ratchet,search
    python batch.py --help

The batch is written to a folder of its own under batches/ here, with one page for all its
towns. Its base settings are settings.json in this folder. Every town of a batch run from
this folder is a town of the WEF world."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                # the engine both worlds share is one folder up

from engine.__main__ import world_main              # noqa: E402

if __name__ == "__main__":
    sys.exit(world_main("wef", HERE, "batch", sys.argv[1:]))
