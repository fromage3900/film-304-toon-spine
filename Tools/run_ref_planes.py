"""Run the storyboard reference image-plane pass."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")
runpy.run_path("G:/film-304-toon-spine/Tools/build_ref_planes.py", run_name="__main__")
maya.standalone.uninitialize()
print("REFPLANES_PIPELINE_DONE")
