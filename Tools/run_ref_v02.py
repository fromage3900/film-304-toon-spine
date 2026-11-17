"""Run the referenced v02 layout build, material pass, and post pass headlessly."""
from __future__ import annotations

import runpy

import maya.standalone

maya.standalone.initialize(name="python")

ROOT = "G:/film-304-toon-spine/Tools/"
runpy.run_path(ROOT + "build_layout_62_66_ref_v02.py", run_name="__main__")
runpy.run_path(ROOT + "fix_layout_materials.py", run_name="__main__")
runpy.run_path(ROOT + "post_layout_ref_v02.py", run_name="__main__")

maya.standalone.uninitialize()
print("V02_PIPELINE_DONE")
