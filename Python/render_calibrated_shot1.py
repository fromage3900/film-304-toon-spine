import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")

cloc = unreal.Vector(250.0, -210.0, 108.0)
crot = unreal.Rotator(pitch=-0.2, yaw=130.5, roll=0.0)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
res = claireon.slate_screenshot(target="level_viewport", filename="showcase_calibrated_shot1.png", directory=str(OUT))
print("Screenshot result:", res)
