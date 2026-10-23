import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")

# Step back to see Sam fully
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(220.0, -180.0, 110.0), unreal.Rotator(pitch=-8.0, yaw=140.0, roll=0.0))
res = claireon.slate_screenshot(target="level_viewport", filename="test_sam_full_body.png", directory=str(OUT))
print("Screenshot result:", res)
