"""Set a sane exposure baseline on the sendoff volume.

EV100 12.0 was a diagnostic probe to prove whether the volume applies at all, not a
proposed value. Settle it at 3.0 (about one and a half stops above the project default
min of 0.03, rounded to a usable figure) and leave the rest for a real render.

IMPORTANT: this is unverified. A provably-active unbound volume at EV100 2.0, 5.0 and
12.0 produced pixel-identical viewport captures, and every CineCameraActor reports
exposure_method = ENABLED, which overrides world volumes. So exposure must be checked in
an MRQ render, not a viewport screenshot.
"""
import sys

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if not world or len(actors) < 50:
    print("no map open")
    raise SystemExit(0)

by_label = {a.get_actor_label(): a for a in actors}
ppv = by_label["Film_Sendoff_Exposure"]

ppv.set_editor_property("unbound", True)
ppv.set_editor_property("enabled", True)
ppv.set_editor_property("priority", 500.0)
ppv.set_editor_property("blend_weight", 1.0)

s = ppv.get_editor_property("settings")
s.set_editor_property("override_auto_exposure_method", True)
s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
s.set_editor_property("override_auto_exposure_min_brightness", True)
s.set_editor_property("auto_exposure_min_brightness", 3.0)
s.set_editor_property("override_auto_exposure_max_brightness", True)
s.set_editor_property("auto_exposure_max_brightness", 3.0)
s.set_editor_property("override_auto_exposure_bias", True)
s.set_editor_property("auto_exposure_bias", 0.0)
s.set_editor_property("weighted_blendables", unreal.WeightedBlendables(array=[]))
ppv.set_editor_property("settings", s)
ppv.modify()

print("Film_Sendoff_Exposure: unbound, weight 1.0, priority 500, AEM_MANUAL EV100 3.0")
print("readback min/max:", s.get_editor_property("auto_exposure_min_brightness"),
      s.get_editor_property("auto_exposure_max_brightness"))
print("\nNOTE: level NOT saved.")