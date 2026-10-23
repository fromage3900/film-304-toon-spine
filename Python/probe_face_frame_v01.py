"""Probe: what drives the FACE, and what are the real framing numbers?

Owner feedback 2026-10-17 (on STYLE_TOON_OFFICEMEDIUM_v06.png):
    "lights are over exposed, scene needs better compose, and eyes and afcial
     features didnt follow pose"

Three questions, all read-only:

 1. FACE. The pose table keys 21 bones and not one of them is a face bone
    (POSES["IDLE_A"] in universal_film_style_session_20261016.py). This probe
    lists every bone whose name looks facial (eye/pupil/iris/lid/lash/brow/
    jaw/mouth/lip/teeth/gum/tongue/cheek/nose) on both sides of the rig's
    control/deform split, so the next pose can key the real ones. It also
    reports each facial bone's WORLD position, which is what tells us whether
    the eyes sit on the skull or off it, and where to put a close-up camera.

 2. FRAMING. Subject bounds + camera transform + lens, so the next camera
    position can be computed from the numbers instead of guessed. The v06
    still has the subject at roughly a third of frame height in a mostly empty
    wall, which is a framing problem, not a lighting problem.

 3. LEVEL. Every non-session light in the level with its intensity and units.
    build_light_rig() notes the authored set totals ~12 lux; that claim gets
    re-checked here against the live actors, because the exposure fix depends
    on the ratio between the local rig and the set it is lighting.

Writes Saved/Audit/UniversalFilm_20261016/face_frame_probe.json. Mutates
nothing: reads only, spawns nothing, saves nothing.
"""
import json
import math
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved" / "Audit" / "UniversalFilm_20261016"
OUT = ROOT / "Saved" / "Renders" / "universal_film_styles"

FACE_WORDS = ("eye", "pupil", "iris", "lid", "lash", "brow", "jaw", "mouth",
              "lip", "teeth", "tooth", "gum", "tongue", "cheek", "nose",
              "head", "neck", "face", "chin", "ear")
CONTROL_PREFIXES = ("fk", "sdk", "ik", "motion", "x", "fkparent", "pole",
                    "curve", "grp", "group", "nurb", "locator", "loc",
                    "blend", "offset", "scal")

doc = {"probe": "face_frame_v01", "mutates": False}


def actors():
    return unreal.EditorLevelLibrary.get_all_level_actors()


doc["level"] = unreal.EditorLevelLibrary.get_editor_world().get_name()

# ---------------------------------------------------------------------------
# 1. face bones
# ---------------------------------------------------------------------------
subject = None
for a in actors():
    if a.get_actor_label().startswith("Film_Subject_Dana"):
        subject = a
        break
if subject is None:
    for a in actors():
        if a.get_actor_label().startswith("Film_Subject_"):
            subject = a
            break
doc["subject_actor"] = None if subject is None else subject.get_actor_label()

if subject is not None:
    comp = subject.get_component_by_class(unreal.SkeletalMeshComponent)
    if comp is None:
        doc["face_error"] = "no SkeletalMeshComponent on subject"
    else:
        mesh = comp.get_skeletal_mesh_asset()
        doc["mesh"] = mesh.get_path_name() if mesh else None
        n = comp.get_num_bones()
        doc["num_bones"] = n

        # bone whose world transform we resolve, so the close-up camera has a
        # target that is measured rather than assumed
        want = {}
        for i in range(n):
            nm = str(comp.get_bone_name(i))
            low = nm.lower()
            if not any(w in low for w in FACE_WORDS):
                continue
            side = ("control" if low.startswith(CONTROL_PREFIXES) else "deform")
            try:
                xf = comp.get_bone_transform(nm, unreal.BoneSpaces.WORLD)
                loc = [round(v, 2) for v in
                       (xf.translation.x, xf.translation.y, xf.translation.z)]
            except Exception as exc:                               # noqa: BLE001
                loc = "ERR: %s" % exc
            want.setdefault(side, []).append({"i": i, "bone": nm, "world": loc})

        for side in sorted(want):
            doc.setdefault("face_bones", {})[side] = want[side]

        # the whole head chain, so upstream/downstream is visible
        chain = []
        for nm in ("Head_M", "Neck_M", "Chest_M", "Spine2_M", "Spine1_M"):
            try:
                idx = comp.get_bone_index(nm)
            except Exception:                                      # noqa: BLE001
                idx = None
            row = {"bone": nm, "index": idx}
            if idx is not None and idx >= 0:
                try:
                    pidx = comp.get_parent_bone(idx)
                    row["parent"] = (str(comp.get_bone_name(pidx))
                                     if pidx is not None and pidx >= 0 else None)
                except Exception as exc:                           # noqa: BLE001
                    row["parent"] = "ERR: %s" % exc
                try:
                    xf = comp.get_bone_transform(nm, unreal.BoneSpaces.WORLD)
                    row["world"] = [round(v, 2) for v in
                                    (xf.translation.x, xf.translation.y,
                                     xf.translation.z)]
                except Exception as exc:                           # noqa: BLE001
                    row["world"] = "ERR: %s" % exc
            chain.append(row)
        doc["spine_chain"] = chain

        # eye-facing material assignment, live off the component
        slots = []
        for idx in range(comp.get_num_materials()):
            mat = comp.get_material(idx)
            slots.append({"index": idx,
                          "material": mat.get_path_name() if mat else None})
        doc["component_materials"] = slots

        origin, extent = subject.get_actor_bounds(False)
        doc["subject"] = {
            "location": [round(v, 2) for v in
                         (subject.get_actor_location().x,
                          subject.get_actor_location().y,
                          subject.get_actor_location().z)],
            "rotation": [round(v, 2) for v in
                         (subject.get_actor_rotation().roll,
                          subject.get_actor_rotation().pitch,
                          subject.get_actor_rotation().yaw)],
            "scale": [round(v, 6) for v in
                      (subject.get_actor_scale3d().x,
                       subject.get_actor_scale3d().y,
                       subject.get_actor_scale3d().z)],
            "bounds_origin": [round(v, 2) for v in (origin.x, origin.y, origin.z)],
            "bounds_extent": [round(v, 2) for v in (extent.x, extent.y, extent.z)],
            "world_height_cm": round(2 * extent.z, 2),
        }

# ---------------------------------------------------------------------------
# 2. cameras + framing
# ---------------------------------------------------------------------------
cams = []
for a in actors():
    lbl = a.get_actor_label()
    if not lbl.startswith("Film_Cam_"):
        continue
    row = {"label": lbl, "class": a.get_class().get_name(),
           "location": [round(v, 2) for v in
                        (a.get_actor_location().x, a.get_actor_location().y,
                         a.get_actor_location().z)],
           "rotation": [round(v, 2) for v in
                        (a.get_actor_rotation().roll, a.get_actor_rotation().pitch,
                         a.get_actor_rotation().yaw)]}
    cc = a.get_component_by_class(unreal.CineCameraComponent)
    if cc is not None:
        row["focal_mm"] = round(float(cc.get_editor_property("current_focal_length")), 3)
        fb = cc.get_editor_property("filmback")
        row["sensor_width_mm"] = round(float(fb.get_editor_property("sensor_width")), 3)
        row["sensor_height_mm"] = round(float(fb.get_editor_property("sensor_height")), 3)
        row["sensor_aspect"] = round(float(fb.get_editor_property("sensor_aspect_ratio")), 4)
        try:
            row["constrain_aspect"] = str(cc.get_editor_property("constrain_aspect_ratio"))
        except Exception:                                          # noqa: BLE001
            pass
        pp = cc.get_editor_property("post_process_settings")
        expo = {}
        for key in ("override_auto_exposure_method", "auto_exposure_method",
                    "override_auto_exposure_bias", "auto_exposure_bias",
                    "override_auto_exposure_min_brightness",
                    "auto_exposure_min_brightness",
                    "override_auto_exposure_max_brightness",
                    "auto_exposure_max_brightness",
                    "override_auto_exposure_apply_physical_camera_exposure",
                    "auto_exposure_apply_physical_camera_exposure",
                    "override_auto_exposure_highlights_contrast",
                    "auto_exposure_highlights_contrast"):
            try:
                v = pp.get_editor_property(key)
                expo[key] = float(v) if isinstance(v, (int, float)) else str(v)
            except Exception as exc:                               # noqa: BLE001
                expo[key] = "ERR: %s" % exc
        for key in ("camera_iso", "camera_shutter_speed", "camera_aperture",
                    "camera_fstop", "manual_ev100", "auto_exposure_manual_ev100"):
            try:
                expo[key] = float(pp.get_editor_property(key))
            except Exception:                                      # noqa: BLE001
                pass
        try:
            expo["override_color_grading"] = str(
                pp.get_editor_property("override_color_grading"))
        except Exception:                                          # noqa: BLE001
            pass
        row["post_process"] = expo
    cams.append(row)
doc["cameras"] = cams

# ---------------------------------------------------------------------------
# 3. the authored set lights (excluding this session's own rig)
# ---------------------------------------------------------------------------
lights = []
for a in actors():
    lbl = a.get_actor_label()
    if lbl.startswith("SESSION_"):
        continue
    lc = a.get_component_by_class(unreal.LightComponent)
    if lc is None:
        continue
    row = {"label": lbl, "class": a.get_class().get_name()}
    for key in ("intensity", "intensity_units", "use_temperature",
                "temperature", "attenuation_radius", "mobility"):
        try:
            v = lc.get_editor_property(key)
            row[key] = float(v) if isinstance(v, (int, float)) else str(v)
        except Exception as exc:                                   # noqa: BLE001
            row[key] = "ERR: %s" % exc
    try:
        row["loc"] = [round(v, 1) for v in
                      (a.get_actor_location().x, a.get_actor_location().y,
                       a.get_actor_location().z)]
    except Exception:                                              # noqa: BLE001
        pass
    lights.append(row)
doc["set_lights"] = lights

# session scaffolding currently alive, so teardown is judged from evidence
doc["session_actors"] = sorted(a.get_actor_label() for a in actors()
                               if a.get_actor_label().startswith("SESSION_"))

AUDIT.mkdir(parents=True, exist_ok=True)
(AUDIT / "face_frame_probe.json").write_text(json.dumps(doc, indent=2),
                                             encoding="utf-8")
unreal.log("[FaceFrameProbe] wrote " + str(AUDIT / "face_frame_probe.json"))
print("FACE_FRAME_PROBE_OK")
