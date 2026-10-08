"""Probe #5: MovieSceneObjectBindingID construction for set_camera_binding_id.

Output: %TEMP%/ue_py_mrq_probe5.txt
"""
import os
import tempfile

import unreal

rows = []

rows.append("MovieSceneObjectBindingID: %s" % (
    [n for n in dir(unreal.MovieSceneObjectBindingID) if not n.startswith("_")]
    if hasattr(unreal, "MovieSceneObjectBindingID") else "MISSING"))

rows.append("set_camera_binding_id doc:\n%s" %
            getattr(unreal.MovieSceneCameraCutSection.set_camera_binding_id,
                    "__doc__", "NO DOC"))

# build a live sequence binding to learn the id types
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Sequences/ProtoDiag"):
    unreal.EditorAssetLibrary.make_directory("/Game/Sequences/ProtoDiag")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
seq = tools.create_asset("PROBE_SEQ", "/Game/Sequences/ProtoDiag", unreal.LevelSequence,
                         unreal.LevelSequenceFactoryNew())
if seq is None:
    raise RuntimeError("PROBE_SEQ could not be created")
cube = sub.spawn_actor_from_class(unreal.CineCameraActor,
                                  unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0))
binding = seq.add_possessable(cube)
rows.append("binding type: %s" % type(binding).__name__)
gid = binding.get_id()
rows.append("binding.get_id(): %r (%s)" % (gid, type(gid).__name__))

# ctor attempts
for attempt, form in enumerate([
    "unreal.MovieSceneObjectBindingID(gid)",
    "unreal.MovieSceneObjectBindingID()",
]):
    try:
        rows.append("%s -> %r" % (form, eval(form)))                # noqa: S307
    except Exception as exc:                                       # noqa: BLE001
        rows.append("%s -> FAILED: %s" % (form, str(exc)[:120]))

try:
    obj = unreal.MovieSceneObjectBindingID()
    rows.append("empty struct props: %s" % [n for n in dir(obj) if not n.startswith("_")])
    for prop in ("binding_guid", "guid", "sequence_guid", "object_binding_id"):
        try:
            obj.get_editor_property(prop)
            rows.append("HAS property %s" % prop)
        except Exception:                                          # noqa: BLE001
            pass
except Exception as exc:                                           # noqa: BLE001
    rows.append("empty struct probe FAILED: %s" % exc)

# cleanup
try:
    unreal.EditorAssetLibrary.delete_asset("/Game/Sequences/ProtoDiag/PROBE_SEQ")
    sub.destroy_actor(cube)
except Exception:                                                  # noqa: BLE001
    pass

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe5.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(str(r) for r in rows))
print("[mrq-probe5] wrote %s" % out)
