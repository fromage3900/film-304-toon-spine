"""Fast visual check: viewport stills from the Film 304 showcase cameras.

Viewport captures, not MRQ renders - seconds instead of minutes, and enough to judge
exposure, framing and whether anything is obviously broken. Read-only apart from
moving the viewport camera, which is restored.
"""
import sys
from pathlib import Path

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal
import claireon

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
el = unreal.EditorLevelLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

actors = eas.get_all_level_actors()
if not world or len(actors) < 50:
    print("no map open")
    raise SystemExit(0)

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Sendoff_Check_20261019")
OUT.mkdir(parents=True, exist_ok=True)

by_label = {}
for a in actors:
    by_label.setdefault(a.get_actor_label(), []).append(a)

# Prefer the finished-looking showcase/hero cameras.
wanted = [
    "Film_Cam_Showcase_Ensemble_v02",
    "Film_Cam_Showcase_DanaPortrait_v02",
    "Film_Cam_Closeout_DuskHero_v02",
    "Film_Cam_Showcase_LowAngleRake_v02",
    "Film_Cam_Skyline_BlueHour",
    "Cam_E1",
]
cams = [(w, by_label[w][0]) for w in wanted if w in by_label]
if not cams:
    # Fall back to any CineCameraActor with a sensible label.
    for a in actors:
        if isinstance(a, unreal.CineCameraActor) and "Cam" in a.get_actor_label():
            cams.append((a.get_actor_label(), a))
    cams = cams[:6]

print("cameras:", [c[0] for c in cams])

start_loc, start_rot = el.get_level_viewport_camera_info()
shots = []
try:
    eas.set_selected_level_actors([])
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
    for label, cam in cams:
        el.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
        try:
            res = claireon.slate_screenshot(
                target="level_viewport", filename=f"{label}.png", directory=str(OUT)
            )
            shots.append((label, "ok"))
            print(f"  {label}: ok")
        except Exception as exc:
            shots.append((label, f"FAILED {exc}"))
            print(f"  {label}: FAILED {exc}")
finally:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
    el.set_level_viewport_camera_info(start_loc, start_rot)

print(f"\nimages in {OUT}")
for label, status in shots:
    print(f"  {label:36s} {status}")