import unreal
import sys
for p in ["g:/film-304-toon-spine/Python", "g:/film-304-toon-spine"]:
    if p not in sys.path:
        sys.path.insert(0, p)

import build_master_toon
print("Calling build_master_toon.build()...")
mat = build_master_toon.build(rebuild=True)
print("Build returned:", mat.get_name() if mat else "None")

res = build_master_toon.verify()
print("Verify returned:", res)
