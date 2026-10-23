"""Set the showcase cameras to inherit the world exposure volume.

Every CineCameraActor reports exposure_method = ENABLED, i.e. per-camera auto exposure.
That overrides the unbound world volume, which is why Film_Sendoff_Exposure appeared to
do nothing. MRQ honours both: the camera the sequence cuts to supplies its own exposure
settings, and unbound world volumes are applied in full during a render.

So flipping the camera is what lets the volume take effect. Scope is the showcase
cameras; extending to every CineCameraActor in the level is the same call on a wider
list.

Read the enum rather than guessing at a value.
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

print("=== CameraExposureMethod enum values ===")
enum = unreal.CameraExposureMethod
members = [m for m in dir(enum) if m.isupper()]
for m in members:
    try:
        print(f"  {m:16s} = {getattr(enum, m)}")
    except Exception:
        pass

# The enum has only two members in this build. DO_NOT_OVERRIDE means "this camera does
# not supply its own exposure", so the unbound world volume governs. That is the value
# we want. An earlier version of this script fell through to ENABLED, which is the
# value already set, and so silently changed nothing.
if "DO_NOT_OVERRIDE" not in members:
    print(f"CameraExposureMethod has no DO_NOT_OVERRIDE; members={members}")
    raise SystemExit(1)
TARGET = getattr(enum, "DO_NOT_OVERRIDE")
print(f"\nchose DO_NOT_OVERRIDE = {TARGET}")

SHOWCASE = [
    "Film_Cam_Showcase_Ensemble_v02",
    "Film_Cam_Showcase_DanaPortrait_v02",
    "Film_Cam_Showcase_LowAngleRake_v02",
    "Film_Cam_Closeout_DuskHero_v02",
]

print("\n=== applying to showcase cameras ===")
for label in SHOWCASE:
    cam = by_label.get(label)
    if cam is None:
        print(f"  {label:36s} NOT FOUND")
        continue
    cine = cam.get_component_by_class(unreal.CineCameraComponent)
    if cine is None:
        print(f"  {label:36s} no CineCameraComponent")
        continue
    before = cine.get_editor_property("exposure_method")
    cine.set_editor_property("exposure_method", TARGET)
    after = cine.get_editor_property("exposure_method")
    cam.modify()
    print(f"  {label:36s} {before} -> {after}")

print("\n=== world volume state ===")
ppv = by_label.get("Film_Sendoff_Exposure")
if ppv:
    s = ppv.get_editor_property("settings")
    print("  unbound  =", ppv.get_editor_property("unbound"))
    print("  enabled  =", ppv.get_editor_property("enabled"))
    print("  weight   =", ppv.get_editor_property("blend_weight"))
    print("  priority =", ppv.get_editor_property("priority"))
    print("  method   =", s.get_editor_property("auto_exposure_method"))
    print("  EV100    =", s.get_editor_property("auto_exposure_min_brightness"))

n_cams = sum(1 for a in actors if isinstance(a, unreal.CineCameraActor))
still_enabled = [
    a.get_actor_label() for a in actors
    if isinstance(a, unreal.CineCameraActor)
    and a.get_component_by_class(unreal.CineCameraComponent) is not None
    and a.get_component_by_class(unreal.CineCameraComponent).get_editor_property(
        "exposure_method") == enum.ENABLED
]
print(f"\n{n_cams} CineCameraActors in the level; {len(still_enabled)} still on ENABLED")
print("NOTE: level NOT saved.")