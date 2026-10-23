import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")

cloc = unreal.Vector(240.0, -220.0, 115.0)
crot = unreal.Rotator(pitch=-2.272323, yaw=142.523820, roll=0.0)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
res = claireon.slate_screenshot(target="level_viewport", filename="phase2_bay3_real_view.png", directory=str(OUT))
print("Screenshot result:", res)
