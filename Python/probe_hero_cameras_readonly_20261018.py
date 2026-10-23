"""READ-ONLY verification of the four L_Film_Office hero cameras.

L_Film_Office.umap was written at 22:20, AFTER hero_lock.json recorded the camera
transforms (~03:27-03:53). This confirms whether the cameras still hold those
transforms, and discovers the correct UDS time-of-day property name.

SAFETY: never calls save. Aborts if any map package is dirty rather than risk
discarding unsaved work by loading a different map.

Run:  python Tools/run_ue_file.py Python/probe_hero_cameras_readonly_20261018.py
"""
import json
import os

import unreal

OUT = r"G:/film-304-toon-spine/Saved/Audit/HeroLock20261018/hero_camera_verify.json"
LOCK = r"G:/film-304-toon-spine/Saved/Audit/HeroLock20261018/hero_lock.json"
MAP_PATH = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office"
MAP_NAME = "L_Film_Office"

TOL_LOC = 0.5
TOL_ROT = 0.05

report = {
    "read_only": True,
    "saved_anything": False,
    "errors": [],
    "cameras": [],
    "uds_property_discovery": {},
    "lights": [],
    "ppv": {},
}


def note(msg):
    report["errors"].append(msg)
    unreal.log_warning("[hero_probe] " + str(msg))


def prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return None


# ---------------------------------------------------------------- world check
eds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = eds.get_editor_world()
world_name = world.get_name() if world else None
report["current_world"] = world_name

dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
report["dirty_map_packages"] = [p.get_name() for p in (dirty or [])]

if world_name != MAP_NAME:
    if report["dirty_map_packages"]:
        note(
            "ABORTED: current world is %s and %d map package(s) are dirty. "
            "Refusing to load %s to avoid discarding unsaved work."
            % (world_name, len(report["dirty_map_packages"]), MAP_NAME)
        )
        report["ok"] = False
    else:
        unreal.log("[hero_probe] loading %s (read-only, will not save)" % MAP_PATH)
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        world = eds.get_editor_world()
        report["current_world"] = world.get_name() if world else None
        report["loaded_map"] = True

if report.get("current_world") != MAP_NAME:
    note("could not resolve world %s" % MAP_NAME)
    report["ok"] = False
else:
    report["ok"] = True

# ------------------------------------------------------------ expected values
expected = {}
try:
    with open(LOCK) as fh:
        for shot in json.load(fh).get("shots", []):
            expected[shot["id"]] = shot
except Exception as exc:
    note("could not read hero_lock.json: %r" % (exc,))

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
report["actor_count"] = len(actors)

by_label = {}
for a in actors:
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        continue

# ------------------------------------------------------------------ cameras
for label, exp in expected.items():
    entry = {"label": label, "found": False}
    a = by_label.get(label)
    if a is None:
        entry["error"] = "actor with this label not present in live level"
        report["cameras"].append(entry)
        continue

    entry["found"] = True
    entry["class"] = a.get_class().get_name()
    try:
        entry["folder"] = str(a.get_folder_path())
    except Exception:
        entry["folder"] = None

    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    entry["loc"] = [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)]
    entry["rotation"] = [round(rot.pitch, 3), round(rot.yaw, 3), round(rot.roll, 3)]

    cc = None
    try:
        cc = a.get_cine_camera_component()
    except Exception:
        note("%s: get_cine_camera_component failed" % label)
    if cc is not None:
        # NOTE: CineCameraComponent exposes `current_focal_length`; plain
        # `focal_length` and `lens_settings.focal_length` both raise. Verified
        # 2026-10-18 in lens_and_uds_members.json.
        entry["mm"] = round(float(prop(cc, "current_focal_length") or 0.0), 3)
        entry["f"] = round(float(prop(cc, "current_aperture") or 0.0), 3)
        fs = prop(cc, "focus_settings")
        if fs is not None:
            entry["focus_cm"] = round(float(prop(fs, "manual_focus_distance") or 0.0), 3)
            entry["focus_method"] = str(prop(fs, "focus_method"))

    # ---- compare against hero_lock
    drift = {}
    if "loc" in exp:
        for i, axis in enumerate(("x", "y", "z")):
            d = abs(entry["loc"][i] - float(exp["loc"][i]))
            if d > TOL_LOC:
                drift["loc_" + axis] = round(d, 3)
    if "rotation" in exp:
        for i, axis in enumerate(("pitch", "yaw", "roll")):
            d = abs(entry["rotation"][i] - float(exp["rotation"][i]))
            if d > TOL_ROT:
                drift["rot_" + axis] = round(d, 3)
    for key in ("mm", "f", "focus_cm"):
        if key in entry and exp.get(key) is not None:
            d = abs(entry[key] - float(exp[key]))
            if d > 0.01:
                drift[key] = round(d, 3)

    entry["drift_from_hero_lock"] = drift
    entry["matches_hero_lock"] = not drift
    entry["folder_matches"] = entry.get("folder") == exp.get("folder")
    report["cameras"].append(entry)

# ------------------------------------------------- UDS property discovery
uds = by_label.get("Film_UDS_Daylight")
if uds is None:
    note("UDS actor Film_UDS_Daylight not found by label")
else:
    report["uds_actor_class"] = uds.get_class().get_name()
    candidates = [
        "time_of_day", "TimeOfDay", "time_of_day_24", "time_of_day_24h",
        "time_of_day_24_hours", "time", "hour", "sun_time_of_day",
        "blueprint_time_of_day", "time_of_day_override", "day_time",
    ]
    found = {}
    for name in candidates:
        v = prop(uds, name)
        if v is not None:
            found[name] = str(v)
    report["uds_property_discovery"] = {
        "candidates_that_resolve": found,
        "resolved_any": bool(found),
    }
    if not found:
        note("no time_of_day variant resolved on %s" % report["uds_actor_class"])

# --------------------------------------------------------------- lights
try:
    with open(LOCK) as fh:
        lock_lights = json.load(fh).get("lights", [])
except Exception:
    lock_lights = []

for spec in lock_lights:
    label = spec.get("label")
    entry = {"label": label, "found": False}
    a = by_label.get(label)
    if a is None:
        entry["error"] = "not present in live level"
        report["lights"].append(entry)
        continue
    entry["found"] = True
    comps = []
    try:
        comps = a.get_components_by_class(unreal.LightComponentBase)
    except Exception:
        note("%s: get_components_by_class failed" % label)
    if comps:
        c = comps[0]
        entry["intensity"] = round(float(prop(c, "intensity") or 0.0), 4)
        vsi = prop(c, "volumetric_scattering_intensity")
        if vsi is not None:
            entry["volumetric_scattering_intensity"] = round(float(vsi), 4)
        exp_after = spec.get("after") or {}
        drift = {}
        if "intensity" in exp_after:
            d = abs(entry["intensity"] - float(exp_after["intensity"]))
            if d > 0.001:
                drift["intensity"] = round(d, 4)
        if "volumetric_scattering_intensity" in exp_after and "volumetric_scattering_intensity" in entry:
            d = abs(entry["volumetric_scattering_intensity"] - float(exp_after["volumetric_scattering_intensity"]))
            if d > 0.001:
                drift["volumetric_scattering_intensity"] = round(d, 4)
        entry["drift_from_hero_lock"] = drift
        entry["matches_hero_lock"] = not drift
    report["lights"].append(entry)

# ------------------------------------------------------------------- PPV
ppv = by_label.get("PPV_ToonOutlineClean")
if ppv is None:
    note("PPV_ToonOutlineClean not found by label")
else:
    report["ppv"]["found"] = True
    report["ppv"]["class"] = ppv.get_class().get_name()
    settings = prop(ppv, "settings")
    if settings is None:
        note("PPV settings unresolved")
    else:
        names = [
            "auto_exposure_method", "auto_exposure_min_brightness",
            "auto_exposure_max_brightness", "auto_exposure_bias",
            "bloom_intensity", "vignette_intensity",
        ]
        live = {}
        for n in names:
            v = prop(settings, n)
            live[n] = str(v) if v is not None else None
            ov = prop(settings, "override_" + n)
            live["override_" + n] = str(ov) if ov is not None else None
        report["ppv"]["live"] = live

report["saved_anything"] = False
unreal.log("[hero_probe] read-only complete; nothing saved")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fh:
    json.dump(report, fh, indent=2)
unreal.log("[hero_probe] WROTE " + OUT)

cam_ok = [c for c in report["cameras"] if c.get("matches_hero_lock")]
print("HERO_PROBE cameras_matching_lock=%d/%d" % (len(cam_ok), len(report["cameras"])))
print("HERO_PROBE uds_resolved=%s" % report["uds_property_discovery"].get("resolved_any"))
print("HERO_PROBE errors=%d" % len(report["errors"]))
