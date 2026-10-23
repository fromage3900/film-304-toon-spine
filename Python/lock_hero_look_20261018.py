"""Lock the four hero cameras, one-key light rig and a deliberate exposure.

Saves the level at the end (the dirty set was empty when this pass began).

Camera grammar (see Docs/HERO_LOOK_LOCK_20261018.md):
  HERO01 wide 24mm / 130cm   - establishing, depth through the desks to the windows
  HERO02 medium 35mm / 115cm - David foreground, Dana midground
  HERO03 close 75mm / 105cm  - 3/4 portrait, window as rim
  HERO04 macro 100mm / 68cm  - spider on David's desk

Framing is position + look-at target, so the intent survives a later nudge.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)

FOLDER = "Film304/HeroCameras_20261018"
SHOTS = [
    {"id": "HERO01_Wide_Establishing", "mm": 24.0, "f": 4.0,
     "loc": (60.0, -430.0, 135.0), "target": (-90.0, 40.0, 90.0), "focus": 520.0,
     "intent": "wide, layer foreground desks / cast / window wall"},
    {"id": "HERO02_Medium_TwoShot", "mm": 35.0, "f": 2.8,
     "loc": (-180.0, -250.0, 112.0), "target": (-50.0, -5.0, 85.0), "focus": 270.0,
     "intent": "David foreground-left, Dana midground-right"},
    {"id": "HERO03_Close_Portrait", "mm": 75.0, "f": 2.0,
     "loc": (-55.0, -35.0, 102.0), "target": (11.0, 29.0, 96.0), "focus": 95.0,
     "intent": "Dana 3/4 portrait, window behind for rim"},
    {"id": "HERO04_Macro_Insert", "mm": 100.0, "f": 2.8,
     "loc": (-120.0, -150.0, 68.0), "target": (-160.0, -100.0, 54.0), "focus": 68.0,
     "intent": "spider on David's desk, desk surface as ground"},
]

# One key, minimal fill, one character spot. Values in the unit each light uses.
LIGHTS = {
    "Cast_RimKicker_Light": {"intensity": 5.0, "forward_shading_priority": 1},
    "Light_Cinematic_SunBeam": {"intensity": 1.2,
                                "volumetric_scattering_intensity": 0.8,
                                "forward_shading_priority": 0},
    "EST_Fill_E1": {"intensity": 0.15, "forward_shading_priority": -1},
    "Film_Troffer_1_Light": {"intensity": 3.5},
    "Film_Troffer_2_Light": {"intensity": 3.5},
    "Film_Troffer_3_Light": {"intensity": 3.5},
    "Film_Troffer_4_Light": {"intensity": 3.5},
    "Film_Troffer_5_Light": {"intensity": 3.5},
    "Film_Troffer_6_Light": {"intensity": 3.5},
    "Light_Workstation_Row_Troffer": {"intensity": 8.0},
    "Light_Hero_CharacterFill": {"intensity": 4.0},
}

ACTIVE_PPV = "PPV_ToonOutlineClean"
PPV_SETTINGS = {
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_HISTOGRAM,
    "override_auto_exposure_min_brightness": True,
    "auto_exposure_min_brightness": 0.8,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_max_brightness": 1.2,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.0,
    "override_bloom_intensity": True,
    "bloom_intensity": 0.25,
    "override_vignette_intensity": True,
    "vignette_intensity": 0.12,
}

report = {"shots": [], "lights": [], "ppv": {}, "dirty_before": [], "saved": False,
          "dirty_after": [], "errors": []}

LEVEL = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office"


def ensure_level():
    """Never operate on whatever map the editor happened to open."""
    world = safe(lambda: unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world(), None)
    if world is not None and "L_Film_Office" in world.get_path_name():
        return world.get_path_name()
    safe(lambda: unreal.EditorLoadingAndSavingUtils.load_map(LEVEL))
    world = safe(lambda: unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world(), None)
    return world.get_path_name() if world else None


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:180])
        return default


def prop(o, n, d=None):
    return safe(lambda: o.get_editor_property(n), d)


def by_label():
    out = {}
    for a in EAS.get_all_level_actors():
        out[safe(lambda: a.get_actor_label(), "")] = a
    return out


def set_focus(comp, distance_cm):
    """Manual focus lives inside the FocusSettings struct, not on the component."""
    fs = safe(lambda: comp.get_editor_property("focus_settings"), None)
    if fs is None:
        return None
    safe(lambda: fs.set_editor_property("manual_focus_distance", float(distance_cm)))
    safe(lambda: fs.set_editor_property("focus_method", unreal.CameraFocusMethod.MANUAL))
    safe(lambda: comp.set_editor_property("focus_settings", fs))
    got = safe(lambda: comp.get_editor_property("focus_settings"), None)
    return safe(lambda: float(got.get_editor_property("manual_focus_distance")), None)

label_map = by_label()
report["world"] = ensure_level()
if report["world"] is None or "L_Film_Office" not in report["world"]:
    raise RuntimeError("wrong level loaded: " + str(report["world"]))
label_map = by_label()

for shot in SHOTS:
    loc = unreal.Vector(*shot["loc"])
    target = unreal.Vector(*shot["target"])
    rot = unreal.MathLibrary.find_look_at_rotation(loc, target)
    actor = label_map.get(shot["id"])
    state = "updated"
    if actor is None:
        actor = EL.spawn_actor_from_class(unreal.CineCameraActor, loc, rot)
        if actor is None:
            report["errors"].append("spawn failed: " + shot["id"])
            continue
        actor.set_actor_label(shot["id"])
        state = "created"
    actor.set_actor_location(loc, False, False)
    actor.set_actor_rotation(rot, False)
    actor.set_folder_path(FOLDER)
    actor.tags = ["HeroLock20261018"]
    comp = (safe(lambda: actor.get_cine_camera_component(), None)
            or safe(lambda: actor.get_component_by_class(unreal.CineCameraComponent), None))
    if comp is not None:
        safe(lambda: comp.set_editor_property("current_focal_length", shot["mm"]))
        safe(lambda: comp.set_editor_property("current_aperture", shot["f"]))
        focus_readback = set_focus(comp, shot["focus"])
    else:
        focus_readback = None
    report["shots"].append({
        "id": shot["id"], "state": state, "intent": shot["intent"],
        "loc": list(shot["loc"]), "target": list(shot["target"]),
        "rotation": [round(rot.pitch, 2), round(rot.yaw, 2), round(rot.roll, 2)],
        "mm": prop(comp, "current_focal_length"), "f": prop(comp, "current_aperture"),
        "focus_cm": focus_readback,
        "label_ok": safe(lambda: actor.get_actor_label(), None) == shot["id"],
        "folder": safe(lambda: str(actor.get_folder_path()), None),
    })

for label, values in LIGHTS.items():
    actor = label_map.get(label)
    if actor is None:
        report["errors"].append("light missing: " + label)
        continue
    comp = safe(lambda: actor.get_component_by_class(unreal.LightComponent), None)
    if comp is None:
        report["errors"].append("no LightComponent: " + label)
        continue
    row = {"label": label, "before": {}, "after": {}}
    for key, value in values.items():
        row["before"][key] = prop(comp, key)
        safe(lambda key=key, value=value: comp.set_editor_property(key, value))
        row["after"][key] = prop(comp, key)
    report["lights"].append(row)

ppv = label_map.get(ACTIVE_PPV)
if ppv is None:
    report["errors"].append("PPV missing: " + ACTIVE_PPV)
else:
    settings = prop(ppv, "settings")
    row = {"label": ACTIVE_PPV, "before": {}, "after": {}}
    for key, value in PPV_SETTINGS.items():
        row["before"][key] = str(prop(settings, key))
        safe(lambda key=key, value=value: settings.set_editor_property(key, value))
        row["after"][key] = str(prop(settings, key))
    ppv.set_editor_property("settings", settings)
    report["ppv"] = row

report["dirty_before"] = sorted(safe(lambda: [p.get_name() for p in
    unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])
report["saved"] = bool(safe(lambda: unreal.EditorLoadingAndSavingUtils.save_current_level(), False))
report["dirty_after"] = sorted(safe(lambda: [p.get_name() for p in
    unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])
report["ok"] = report["saved"] and not report["errors"] and len(report["shots"]) == 4
(OUT / "hero_lock.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("hero lock ok=" + str(report["ok"]), "saved=" + str(report["saved"]),
      "dirty_after=" + str(report["dirty_after"]))
for s in report["shots"]:
    print(" ", s["state"], s["id"], "mm=", s["mm"], "rot=", s["rotation"],
          "folder=", s["folder"])
for l in report["lights"]:
    print("  light", l["label"], l["before"], "->", l["after"])
print("  ppv", json.dumps(report["ppv"]))
for e in report["errors"]:
    print("  ERROR", e)

