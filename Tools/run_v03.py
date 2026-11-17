"""Run the v03 polish pass headlessly."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")
runpy.run_path("G:/film-304-toon-spine/Tools/build_layout_v03_polish.py", run_name="__main__")
maya.standalone.uninitialize()
print("V03_PIPELINE_DONE")
