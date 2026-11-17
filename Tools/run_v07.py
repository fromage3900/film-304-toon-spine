"""Run v07 board-match fixes."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")
runpy.run_path("G:/film-304-toon-spine/Tools/build_layout_v07_match.py", run_name="__main__")
maya.standalone.uninitialize()
print("V07_PIPELINE_DONE")
