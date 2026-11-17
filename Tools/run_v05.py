"""Run the v05 board-match fix headlessly."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")
runpy.run_path("G:/film-304-toon-spine/Tools/build_layout_v05_match.py", run_name="__main__")
maya.standalone.uninitialize()
print("V05_PIPELINE_DONE")
