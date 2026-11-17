"""Run v08 handoff fixes."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")
runpy.run_path("G:/film-304-toon-spine/Tools/build_layout_v08_handoff.py", run_name="__main__")
maya.standalone.uninitialize()
print("V08_PIPELINE_DONE")
