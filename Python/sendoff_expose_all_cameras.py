"""Extend DO_NOT_OVERRIDE to every CineCameraActor in the level.

Exposure is a whole-film decision. Leaving 38 cameras on ENABLED means each shot meters
itself independently, which is the shot-to-shot inconsistency that made the renders read
as unfinished. With all cameras deferring to Film_Sendoff_Exposure, every shot lands on
the same brightness.

Skips the beacons the project already hides, and reports anything it could not change.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if not world or len(actors) < 50:
    print("no map open")
    raise SystemExit(0)

TARGET = unreal.CameraExposureMethod.DO_NOT_OVERRIDE
SKIP = {"Light_AviationBeacon_HeroSpire"}

changed, skipped, failed = [], [], []
for a in actors:
    if not isinstance(a, unreal.CineCameraActor):
        continue
    label = a.get_actor_label()
    if label in SKIP:
        skipped.append({"camera": label, "reason": "in skip list"})
        continue
    cine = a.get_component_by_class(unreal.CineCameraComponent)
    if cine is None:
        failed.append({"camera": label, "reason": "no CineCameraComponent"})
        continue
    before = cine.get_editor_property("exposure_method")
    if before == TARGET:
        continue
    try:
        cine.set_editor_property("exposure_method", TARGET)
        after = cine.get_editor_property("exposure_method")
        a.modify()
        if after == TARGET:
            changed.append({"camera": label, "from": str(before), "to": str(after)})
        else:
            failed.append({"camera": label, "reason": f"readback {after}"})
    except Exception as exc:
        failed.append({"camera": label, "reason": str(exc)})

total = sum(1 for a in actors if isinstance(a, unreal.CineCameraActor))
still_enabled = [
    a.get_actor_label() for a in actors
    if isinstance(a, unreal.CineCameraActor)
    and a.get_component_by_class(unreal.CineCameraComponent) is not None
    and a.get_component_by_class(unreal.CineCameraComponent).get_editor_property(
        "exposure_method") == unreal.CameraExposureMethod.ENABLED
]

print(f"CineCameraActors in level : {total}")
print(f"changed to DO_NOT_OVERRIDE : {len(changed)}")
print(f"skipped                    : {len(skipped)} {skipped}")
print(f"failed                     : {len(failed)} {failed}")
print(f"still on ENABLED           : {len(still_enabled)} {still_enabled}")

ppv = next((a for a in actors if a.get_actor_label() == "Film_Sendoff_Exposure"), None)
print("\n=== exposure volume (now governs every camera) ===")
if ppv is None:
    print("  MISSING Film_Sendoff_Exposure")
else:
    s = ppv.get_editor_property("settings")
    print(f"  unbound  = {ppv.get_editor_property('unbound')}")
    print(f"  enabled  = {ppv.get_editor_property('enabled')}")
    print(f"  weight   = {ppv.get_editor_property('blend_weight')}")
    print(f"  priority = {ppv.get_editor_property('priority')}")
    print(f"  method   = {s.get_editor_property('auto_exposure_method')}")
    print(f"  EV100    = {s.get_editor_property('auto_exposure_min_brightness')}")

out = Path("G:/film-304-toon-spine/Saved/Audit/Sendoff_Render_20261019")
out.mkdir(parents=True, exist_ok=True)
(out / "camera_exposure_change.json").write_text(
    json.dumps(
        {
            "map": world.get_path_name(),
            "total_cinecameras": total,
            "changed": changed,
            "skipped": skipped,
            "failed": failed,
            "still_enabled": still_enabled,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(f"\nreport: {out / 'camera_exposure_change.json'}")
print("NOTE: level NOT saved.")