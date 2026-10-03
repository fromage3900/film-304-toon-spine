"""Self-test fixture for check_param_wiring.py - NOT a real builder.

Contains one wired parameter and one deliberately dead one. The checker must
report exactly 2 declared, 1 live, 1 dead and exit 1. If this file ever reports
"0 dead", the checker has stopped detecting dead parameters and its green run
against build_gouache_material.py means nothing.
"""
import spine_lib as lib


def build():
    mat = None
    good = lib.scalar(mat, "GoodParam", "G", 1.0)
    dead = lib.scalar(mat, "DeadParam", "G", 1.0)
    lib.binary(good, good, good)
    return good