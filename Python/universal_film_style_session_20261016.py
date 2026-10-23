"""Universal-film style session: cast + pose + local lighting + measured stills.

Owner asks, 2026-10-16 evening:
    "make a full updated bounded plan and render session with various instance
     renders (eg toon vs realistic vs painterly, etc.) and prep other characters
     in the scene as well."
    "Make sure to play with local loighting intensely and pose the meshes"

WHAT THIS IS
    A bounded, idempotent, re-runnable session executed in the ALREADY-OPEN
    L_Film_Office editor through Monolith (`editor_query run_python`,
    mode=execute_file). Modes:

      styles      ensure the style MI shelf (children of MI_Film_*; Toon is the
                  shelf itself so the control can never drift)
      lights      build/refresh a LOCAL LIGHT RIG around the subject from a
                  preset table (SESSION_LIGHT_* actors; session-only)
      poseframes  compute per-bone parent-relative transforms for a named pose
                  from the rig's bind pose and write frames JSON for
                  `animation.build_sequence_from_poses`
      fire        cast (+ optional David) -> apply pose + lighting -> fire ONE
                  latent still; caller polls (render_prototypes.py convention)
      report      aggregate the audit JSON from decoded pixels + readbacks

WHY THE POSE MATH LOOKS LIKE THIS
    The rig is an Advanced-Skeleton-style Maya rig: skinning follows the clean
    deform bones (Shoulder_R/Elbow_R/Wrist_R, Hip_R/Knee_R/Ankle_R, Spine*, ...)
    while the FK*/SDK*/Twist* subtrees are control/twist helpers. For a bone
    with bind local rotation L and bind component rotation C, asking for a
    WORLD-space rotation W gives the new local rotation

        L' = L * (C^-1 * W * C)

    (identical to the classic (P^-1 W P) L form, but needs no parent lookup).
    Bind data: +Z up, nose = local +Y, right arm extends along -X.

WHAT THIS IS NOT
    Not a rig gate, not a retarget, not a final render. Sam/Spider have no
    meshes in Unreal and get a contract record, not an import. NO LEVEL IS
    SAVED. No commit, no push, no master-material edit.
"""
from __future__ import annotations

import json
import math
import struct
import time
import zlib
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved" / "Renders" / "universal_film_styles"
AUDIT = ROOT / "Saved" / "Audit" / "UniversalFilm_20261016"
REQUEST = OUT / "_request.json"
LANE = "style-lookdev"
LEASE = ROOT / "Saved" / "Coord" / "editor_lease.json"

SHELF = "/Game/Materials/Instances/UniversalFilm_20261016"
STYLES_DIR = SHELF + "/Styles"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
HIDDEN_MAT = "/Game/Materials/Masters/UniversalFilm_20261016/M_ImportHelpersHidden"
POSE_DIR = "/Game/Staging/DanaFilmRuntime_20261016/Poses"
# A film still wants one pose held, not a loop: every key frame of an authored
# pose sequence is identical, and playback is frozen at frame 0.
HOLD_FRAMES = 3

DANA_MESH = "/Game/Staging/DanaFilmRuntime_20261016/Dana_CleanSkin_v08"
DAVID_MESH = "/Game/Meshes/Office/Props/C_DavidRenderTest_OSC"
TEX_DANA_SKIN = "/Game/Materials/Textures/OneDriveRigs_20261016/T_Dana_Skin_D_1001_20261016"
TEX_DANA_SHOES = "/Game/Materials/Textures/OneDriveRigs_20261016/T_Dana_Shoes_D_20261016"

DANA_SLOTS = {
    "danaskin_mat": "Skin", "danahair_mat": "Hair", "danaeye_mat": "EyeWhite",
    "danacornea_mat": "Hidden", "danaeyeint_mat": "EyeInterior",
    "danapants_mat": "Skirt", "danashirt_mat": "Shirt",
    "danashoes_mat": "Shoes", "danagum_mat": "Gum", "danatongue_mat": "Tongue",
}
DAVID_SLOTS = {
    "davidskin_mat": "Skin", "davidhair_mat": "Hair", "davideye_mat": "EyeWhite",
    "davidcornea_mat": "Hidden", "davideyeint_mat": "EyeInterior",
    "davidiris_mat": "Iris", "davidpants_mat": "Skirt",
    "davidshirt_mat": "Shirt", "davidshoes_mat": "Shoes",
}

STYLES = {
    "Toon": {},
    "Painterly": {
        "switches": {"bImpasto_Active": True},
        "scalars": {"ImpastoStrength": 0.7, "ImpastoHeight": 0.06,
                    "ImpastoCoverage": 1.0, "ImpastoRoughness": 0.5,
                    "OilPaintMix": 0.6, "InkDensity": 0.3, "StrokeMask": 0.5,
                    "RampSharpness": 0.55, "ShadowSoftness": 1.1},
        "vectors": {"InkColor": (0.06, 0.04, 0.07, 1.0)},
    },
    "Realistic": {
        "switches": {"bToonRampEnabled": False, "bToonRampActive": False},
        "scalars": {"ToonRampStrength": 0.0, "PaletteRampStrength": 0.0,
                    "NormalStrength": 1.0},
        "per_part": {
            "Skin": {"scalars": {"TextureWeight": 1.0, "Roughness": 0.72,
                                 "SkinSSS_Strength": 0.4},
                     "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
                     "textures": {"Albedo": TEX_DANA_SKIN}},
            "Shoes": {"scalars": {"TextureWeight": 1.0, "Roughness": 0.6},
                      "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
                      "textures": {"Albedo": TEX_DANA_SHOES}},
            "Hair": {"scalars": {"Roughness": 0.45}},
            "Shirt": {"scalars": {"Roughness": 0.85}},
            "Skirt": {"scalars": {"Roughness": 0.85}},
            "EyeWhite": {"scalars": {"Roughness": 0.35}},
            "EyeInterior": {"scalars": {"Roughness": 0.55}},
        },
    },
}

# ---------------------------------------------------------------------------
# POSES — component-axis rotations in degrees.
# axis letter -> UE rotator component: X = roll, Y = pitch, Z = yaw.
# Bind facts (measured on Dana_CleanSkin_v08 by quaternion probe 2026-10-17):
#   +Z up, nose = local +Y, upper arm along -X (right) / +X (left).
#   Rotator(pitch=-72).quaternion().rotate_vector(-X) = (-0.309, 0, +0.951)
#     => "Y" NEGATIVE *raises* the RIGHT arm. Lowering is therefore
#        ("Y", +) on the right and ("Y", -) on the left. The first version of
#        this table had those signs inverted, which would have raised both arms.
#   Yaw: +X rotates toward +Y (nose) for positive "Z", so -X (right arm) goes
#        forward on NEGATIVE "Z". Ops apply right-to-left: w = first * second,
#        so ("Y", 74), ("Z", -10) swings the flat arm forward, then drops it.
#   The bind legs already point straight down, so leg ops stay subtle.
# ---------------------------------------------------------------------------
POSES = {
    "IDLE_A": {
        "Shoulder_R": [("Y", 74), ("Z", -10)], "Elbow_R": [("Y", 14), ("X", 8)],
        "Wrist_R": [("X", 8)],
        "Shoulder_L": [("Y", -74), ("Z", 10)], "Elbow_L": [("Y", -14), ("X", 8)],
        "Wrist_L": [("X", 6)],
        # relaxed stance: hip/knee/ankle only, legs are vertical in bind
        "Hip_R": [("X", 4), ("Z", -3)], "Knee_R": [("X", -8)], "Ankle_R": [("X", 5)],
        "Hip_L": [("X", -3), ("Z", 3)], "Knee_L": [("X", -5)], "Ankle_L": [("X", 3)],
        # weight shift and head turn -- small, so it reads as alive not posed
        "Spine1_M": [("Y", 3), ("Z", -2)], "Spine2_M": [("Y", 3), ("Z", -2)],
        "Chest_M": [("Z", -5)], "Neck_M": [("Z", 7)], "Head_M": [("Z", 8), ("X", -3)],
        "MiddleFinger1_R": [("X", 24)], "IndexFinger1_R": [("X", 16)],
        "MiddleFinger1_L": [("X", 22)], "IndexFinger1_L": [("X", 14)],
    },
    "GESTURE_B": {
        # right forearm raised into a talking gesture, left arm relaxed
        "Shoulder_R": [("Y", 58), ("Z", -18)],
        "Elbow_R": [("Y", 26), ("X", 34)], "Wrist_R": [("X", 18)],
        "Shoulder_L": [("Y", -78), ("Z", 6)], "Elbow_L": [("Y", -10)],
        "Wrist_L": [("X", 6)],
        "Hip_R": [("X", 3), ("Z", -2)], "Knee_R": [("X", -7)], "Ankle_R": [("X", 2)],
        "Hip_L": [("X", -3), ("Z", 2)], "Knee_L": [("X", -4)], "Ankle_L": [("X", 3)],
        "Spine1_M": [("Y", 3)], "Spine2_M": [("Y", 3), ("Z", -4)],
        "Chest_M": [("Z", -8)], "Neck_M": [("Z", -9)],
        "Head_M": [("Z", -13), ("X", -5)],
        "MiddleFinger1_R": [("X", 32)], "IndexFinger1_R": [("X", 38)],
        "ThumbFinger1_R": [("X", 20)],
    },
}

# The deform chain the pose table drives. Used to accumulate the effective
# rotation for the prediction report, and to see whether a bone is upstream or
# downstream of another. Not shipped anywhere.
POSE_PARENT = {
    "Elbow_R": "Shoulder_R", "Wrist_R": "Elbow_R",
    "Elbow_L": "Shoulder_L", "Wrist_L": "Elbow_L",
    "Knee_R": "Hip_R", "Ankle_R": "Knee_R",
    "Knee_L": "Hip_L", "Ankle_L": "Knee_L",
    "Head_M": "Neck_M", "Neck_M": "Chest_M",
    "Chest_M": "Spine2_M", "Spine2_M": "Spine1_M",
    "IndexFinger1_R": "Wrist_R", "MiddleFinger1_R": "Wrist_R",
    "ThumbFinger1_R": "Wrist_R",
    "IndexFinger1_L": "Wrist_L", "MiddleFinger1_L": "Wrist_L",
}
POSE_CHILD = {}
for _child, _parent in POSE_PARENT.items():
    POSE_CHILD.setdefault(_parent, []).append(_child)
del _child, _parent

# ---------------------------------------------------------------------------
# LOCAL LIGHT RIG presets. Angles are bearings around the subject measured from
# the active camera ("front"), elevation from the floor, distance in cm.
# Session-only actors, named SESSION_LIGHT_<PRESET>_<NAME>.
#
# THE UNIT IS LUX-ON-THE-SUBJECT, NOT LUMENS. That distinction is the whole
# exposure fix. Lumens are a property of the lamp; lux is what lands on the
# actor, which is the number a look is judged on and the only one that can be
# reasoned about against the set it is lighting. Measured 2026-10-17, the
# office's own lights total ~10.6 lux and all of it is directional:
#
#     Film_Key 0.60   Film_Fill 2.0   Film_Rim 0.0   Film_UDS_Daylight 8.0
#
# The first version of this table was authored in raw lumens (26000 for the
# key) and nothing checked it against that 10.6 lux. At 320 cm a 26000 lm / 42
# deg spot delivers ~6000 lux, i.e. the local rig was ~600x the set it stood
# in, and exposure then sat wherever the frame average happened to land. The
# result was STYLE_TOON_OFFICEMEDIUM_v06.png: mean luma 212, median 223, and
# NOT ONE PIXEL below luma 12 in the entire frame. Ratio is what makes a rig
# read as local; level is what makes it expose, and the level was never set.
# ---------------------------------------------------------------------------
def cone_omega(cone_deg):
    """Solid angle of a cone, in steradians."""
    return 2.0 * math.pi * (1.0 - math.cos(math.radians(cone_deg) / 2.0))


def lumens_for_lux(lux, dist_cm, kind, cone_deg=None):
    """The lumens a UE light needs to put `lux` on a subject `dist_cm` away.

    Valid only for the distance the preset places the light at -- and that is
    the point: the preset states the intent ("90 lux on the actor"), and this
    turns it into whatever the engine's inverse-square attenuation demands.
    """
    d = max(0.01, float(dist_cm) / 100.0)
    if kind == "spot":
        omega = cone_omega(float(cone_deg or 45.0))
    elif kind == "rect":
        omega = math.pi
    else:
        omega = 4.0 * math.pi
    return float(lux) * d * d * omega


LIGHT_PRESETS = {
    # name, kind, bearing_off, elev_deg, dist_cm, z_cm, LUX, kelvin, extras
    # One hot key, a rim that separates the silhouette, a small warm practical,
    # and a deliberately weak fill: the fill flood is what flattened the first
    # studio frame. Key 90 vs fill 18 is a 5:1 ratio, so the shadow side keeps
    # its shape instead of being argued away.
    "studio": [
        ("KEY", "spot", -38, 32, 320, 10, 90, 4300, {"cone": 42}),
        ("FILL", "rect", 46, 12, 380, 30, 18, 5600, {"w": 200, "h": 160}),
        ("RIM", "spot", 168, 38, 300, 60, 130, 8000, {"cone": 34}),
        ("PRACTICAL", "point", 74, 6, 210, 78, 8, 3000, {"radius": 380}),
    ],
    "dusk": [
        ("KEY", "spot", -58, 18, 360, -10, 55, 2700, {"cone": 36}),
        ("RIM", "spot", 150, 30, 260, 40, 150, 9000, {"cone": 30}),
        ("MAGENTA", "spot", 62, 22, 300, -20, 40, 6500, {"cone": 44}),
        ("PRACTICAL", "point", 86, 4, 170, 70, 14, 2900, {"radius": 420}),
    ],
    "highkey": [
        ("KEY", "rect", -30, 30, 340, 30, 120, 5600, {"w": 260, "h": 200}),
        ("FILL", "rect", 40, 16, 360, 20, 85, 5600, {"w": 280, "h": 220}),
        ("RIM", "spot", 172, 34, 300, 50, 70, 6500, {"cone": 38}),
        ("BOUNCE", "point", 0, -10, 280, -80, 10, 5600, {"radius": 800}),
    ],
}

PLACEMENT = {"dana": (0.0, -45.0), "david": (0.0, 55.0)}
STAGE_HEIGHT_CM = 170.0

E = unreal.EditorAssetLibrary
M = unreal.MaterialEditingLibrary
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log("[StyleSession] " + str(m))


def save(asset):
    if not E.save_loaded_asset(asset, False):
        raise RuntimeError("cannot save " + asset.get_path_name())


# ---------------------------------------------------------------------------
# actors
# ---------------------------------------------------------------------------
def level_actors():
    return unreal.EditorLevelLibrary.get_all_level_actors()


def find_actor(prefix):
    for a in level_actors():
        try:
            if a.get_actor_label().startswith(prefix):
                return a
        except Exception:                                          # noqa: BLE001
            continue
    return None


def find_camera(label):
    for a in level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:                                          # noqa: BLE001
            continue
    return None


# ---------------------------------------------------------------------------
# styles
# ---------------------------------------------------------------------------
def ensure_base_mi(part, color):
    path = SHELF + "/MI_Film_" + part
    if E.does_asset_exist(path):
        return E.load_asset(path)
    obj = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MI_Film_" + part, SHELF, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
    M.set_material_instance_parent(obj, unreal.load_asset(MASTER))
    for key, value in {"TextureWeight": 0., "Metallic": 0., "Roughness": .85,
                       "ToonRampStrength": 1., "TemporalStrength": 0.,
                       "BoilIntensity": 0., "SmearStrength": 0.}.items():
        M.set_material_instance_scalar_parameter_value(obj, key, value)
    for key in ("BaseTint", "PaletteRampMid", "PaletteRampHigh"):
        M.set_material_instance_vector_parameter_value(
            obj, key, unreal.LinearColor(*color))
    M.update_material_instance(obj)
    save(obj)
    return obj


def apply_overrides(mi, spec):
    for name, value in (spec.get("scalars") or {}).items():
        M.set_material_instance_scalar_parameter_value(mi, name, float(value))
    for name, value in (spec.get("switches") or {}).items():
        M.set_material_instance_static_switch_parameter_value(mi, name, bool(value))
    for name, value in (spec.get("vectors") or {}).items():
        M.set_material_instance_vector_parameter_value(
            mi, name, unreal.LinearColor(*value))
    for name, path in (spec.get("textures") or {}).items():
        tex = unreal.load_asset(path)
        if tex is None:
            raise RuntimeError("style texture missing: " + path)
        M.set_material_instance_texture_parameter_value(mi, name, tex)


def style_mi(style, part):
    if style == "Toon":
        return SHELF + "/MI_Film_" + part
    path = "%s/%s/MI_Film_%s_%s" % (STYLES_DIR, style, part, style)
    base = SHELF + "/MI_Film_" + part
    if E.does_asset_exist(path):
        obj = E.load_asset(path)
    else:
        if not E.does_asset_exist(base):
            raise RuntimeError("shelf instance missing: " + base)
        obj = E.duplicate_asset(base, path)
        if obj is None:
            raise RuntimeError("duplicate failed: " + path)
    spec = STYLES[style]
    merged = {"scalars": dict(spec.get("scalars") or {}),
              "switches": dict(spec.get("switches") or {}),
              "vectors": dict(spec.get("vectors") or {}),
              "textures": dict(spec.get("textures") or {})}
    part_spec = (spec.get("per_part") or {}).get(part) or {}
    for key in ("scalars", "switches", "vectors", "textures"):
        merged[key].update(part_spec.get(key) or {})
    apply_overrides(obj, merged)
    M.update_material_instance(obj)
    save(obj)
    return path


def build_styles():
    record = {"styles": {}, "created_base": []}
    for part, color in (("Gum", (.24, .09, .10, 1)), ("Tongue", (.20, .06, .07, 1))):
        if not E.does_asset_exist(SHELF + "/MI_Film_" + part):
            ensure_base_mi(part, color)
            record["created_base"].append(part)
    parts = sorted({v for v in DANA_SLOTS.values()} |
                   {v for v in DAVID_SLOTS.values()})
    for style, spec in STYLES.items():
        entry = {"mi": {}, "note": "control: shelf as-is"}
        for part in parts:
            if part == "Hidden":
                entry["mi"][part] = HIDDEN_MAT
                continue
            entry["mi"][part] = style_mi(style, part)
        if style != "Toon":
            entry["note"] = "child instances of the shelf"
            entry["overrides_requested"] = spec
        record["styles"][style] = entry
    record["styles_dir"] = STYLES_DIR
    (OUT / "_styles.json").write_text(json.dumps(record, indent=2),
                                      encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# local lighting
# ---------------------------------------------------------------------------
def clear_light_rig():
    """Remove every session-only actor: lights and scene captures alike.

    Scene captures are cleaned here too because a capture left alive keeps
    rendering into its render target every frame -- it would cost the next lane
    performance and, worse, its render target would be a stale copy of a frame
    the owner never approved.
    """
    removed = []
    for a in level_actors():
        try:
            lbl = a.get_actor_label()
        except Exception:                                          # noqa: BLE001
            continue
        if lbl.startswith("SESSION_LIGHT_") or lbl.startswith("SESSION_CAPTURE_"):
            removed.append(lbl)
            A.destroy_actor(a)
    return removed


def bearing_vector(bearing_deg, elev_deg, dist_cm):
    b, e = math.radians(bearing_deg), math.radians(elev_deg)
    d = dist_cm * math.cos(e)
    return unreal.Vector(d * math.cos(b), d * math.sin(b), dist_cm * math.sin(e))


def build_light_rig(preset, subject_loc, camera_loc, scale=1.0, camera=None,
                    exposure_ev=None):
    """Local lights placed around the subject, front = direction to camera.

    `scale` multiplies every preset luminance so a lighting idea can be swept
    without editing its shape. `exposure_ev` stops the active camera up or down
    via auto_exposure_bias -- session memory only (this session never saves a
    map, and the original value is recorded for the handoff). Measured
    2026-10-17: these cameras are AEM_MANUAL with bias 0 and the authored set
    lights total ~12 lux, so the local rig is 60x hotter than the set it is
    lighting unless it is stopped down.
    """
    cam_bearing = math.degrees(math.atan2(camera_loc.y - subject_loc.y,
                                          camera_loc.x - subject_loc.x))
    removed = clear_light_rig()
    spec_list = LIGHT_PRESETS[preset]
    spawn = {"point": unreal.PointLight, "spot": unreal.SpotLight,
             "rect": unreal.RectLight}
    placed = []
    for name, kind, bearing_off, elev, dist, z_off, lux, kelvin, extra in spec_list:
        bearing = cam_bearing + bearing_off
        base = subject_loc + unreal.Vector(0, 0, 100 + z_off)
        offset = bearing_vector(bearing, elev, dist)
        loc = unreal.Vector(base.x + offset.x, base.y + offset.y, base.z + offset.z)
        target = unreal.Vector(subject_loc.x, subject_loc.y, subject_loc.z + 105)
        to_target = target - loc
        rot = unreal.MathLibrary.find_look_at_rotation(loc, target)
        actor = A.spawn_actor_from_class(spawn[kind], loc, rot)
        if actor is None:
            raise RuntimeError("failed to spawn light " + name)
        actor.set_actor_label("SESSION_LIGHT_%s_%s" % (preset.upper(), name))
        comp = actor.get_component_by_class(unreal.LightComponent)
        try:
            actor.set_mobility(unreal.ComponentMobility.MOVABLE)
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:                                          # noqa: BLE001
            pass
        # the preset states lux-on-the-subject; the light needs lumens
        lumens = lumens_for_lux(lux, dist, kind,
                                extra.get("cone") if kind == "spot" else None)
        comp.set_editor_property("intensity", float(lumens) * float(scale))
        units_note = "default"
        try:
            comp.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            units_note = str(comp.get_editor_property("intensity_units"))
        except Exception as exc:                                   # noqa: BLE001
            units_note = "LUMENS not settable: %s" % exc
        comp.set_editor_property("use_temperature", True)
        comp.set_editor_property("temperature", float(kelvin))
        if kind in ("point", "spot"):
            comp.set_editor_property("attenuation_radius",
                                     float(extra.get("radius", 900)))
        if kind == "spot":
            comp.set_editor_property("outer_cone_angle", float(extra["cone"]))
            comp.set_editor_property("inner_cone_angle",
                                     float(extra["cone"]) * 0.35)
        if kind == "rect":
            comp.set_editor_property("source_width", float(extra["w"]))
            comp.set_editor_property("source_height", float(extra["h"]))
        comp.set_editor_property("cast_shadows", kind in ("spot", "rect"))
        placed.append({"label": actor.get_actor_label(), "kind": kind,
                       "lux_on_subject": round(float(lux) * float(scale), 2),
                       "intensity": round(float(lumens) * float(scale), 1),
                       "intensity_units": units_note,
                       "kelvin": kelvin,
                       "location": [round(v, 1) for v in (loc.x, loc.y, loc.z)],
                       "bearing_off_deg": bearing_off, "elev_deg": elev,
                       "dist_cm": dist})
    exposure_note = None
    if camera is not None and exposure_ev is not None:
        try:
            ccomp = camera.get_component_by_class(unreal.CineCameraComponent)
            pp = ccomp.get_editor_property("post_process_settings")
            before = pp.get_editor_property("auto_exposure_bias")
            pp.set_editor_property("auto_exposure_bias", float(exposure_ev))
            ccomp.set_editor_property("post_process_settings", pp)
            after = ccomp.get_editor_property(
                "post_process_settings").get_editor_property("auto_exposure_bias")
            exposure_note = {"camera": camera.get_actor_label(), "before": before,
                             "requested": float(exposure_ev), "readback": after,
                             "persisted": False}
        except Exception as exc:                                   # noqa: BLE001
            exposure_note = {"camera": camera.get_actor_label(),
                             "error": str(exc), "persisted": False}
    record = {"preset": preset, "camera_bearing_deg": round(cam_bearing, 2),
              "intensity_scale": float(scale), "exposure": exposure_note,
              "removed_previous": removed, "lights": placed}
    (OUT / "_lights.json").write_text(json.dumps(record, indent=2),
                                      encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# pose authoring
# ---------------------------------------------------------------------------
def axis_quat(axis, degrees):
    # UE: roll = about X, pitch = about Y, yaw = about Z
    if axis == "X":
        return unreal.Rotator(roll=float(degrees)).quaternion()
    if axis == "Y":
        return unreal.Rotator(pitch=float(degrees)).quaternion()
    return unreal.Rotator(yaw=float(degrees)).quaternion()


# unreal.Quat() default-constructs to (0,0,0,0) -- a ZERO quaternion, not
# identity. Multiplying by it collapses every pose to "no rotation", which is
# exactly what the first IDLE_A report showed (predicted child dir == bind
# child dir for all 20 bones). Take identity from a zero rotator instead.
IDENTITY_QUAT = unreal.Rotator().quaternion()


def pose_world_quat(ops):
    w = IDENTITY_QUAT
    for axis, degrees in ops:
        w = w * axis_quat(axis, degrees)
    return w


# ---------------------------------------------------------------------------
# THE FACE DOES NOT FOLLOW THE HEAD -- and that is a rig-topology fact, not a
# tuning problem. Measured 2026-10-17 (probe_face_follow_v03.py, evidence in
# Saved/Audit/UniversalFilm_20261016/face_follow_probe.json):
#
#   Dana_CleanSkin_v08 carries a 345-bone deform-side face rig. It is NOT a
#   child of Head_M. The skeleton root `Group` has two children: `Main` (the
#   body, 88 bones incl. Head_M) and `FaceGroup` (the face, 316 bones). Every
#   face bone -- Eye_R/L, Pupil_*, Iris_*, Jaw_M, lips, lids, brows, teeth,
#   tongue -- descends from FaceGroup instead.
#
#   In Maya the face was pinned to the head by a CONSTRAINT, authored at
#   `FaceDeformationFollowHead` / `FaceMotionFollowHead` / `faceHeadJoint`,
#   whose bind translator is byte-identical to Head_M's ([0, -1.442, 65.454]).
#   A constraint does not survive FBX into a UE skeleton: UE evaluates the
#   skeletal hierarchy and nothing else. So the pose rotates the head while the
#   face skin stays welded to the actor root, and the face slides across the
#   skull.
#
#   Measured with A_DanaFilm_Pose_IDLE_A applied: Head_M moved 2.345 cm,
#   HeadEnd_M 3.452 cm, and the maximum movement of ANY face bone was
#   0.0000 cm. That offset is ~25% of head width, which is precisely the
#   shattered face in STYLE_TOON_OFFICEMEDIUM_v06.png (one eye parked on the
#   cheek, a smear across the mid-face).
#
# The fix is to carry the head's rigid motion onto the three authored follow
# bones. It is measured, not derived: apply the body-only pose, read how the
# head actually moved, then give the face exactly that motion. Both subtrees
# that carry skinned face geometry hang under these roots, so three keys close
# the whole face.
# ---------------------------------------------------------------------------
FACE_ANCHOR = "Head_M"
FACE_FOLLOW = ("FaceDeformationFollowHead", "FaceMotionFollowHead",
               "faceHeadJoint")


def rigid_mul(a, b):
    """`a` after `b`. A rigid is (quat, translation-of-origin)."""
    return (a[0] * b[0], a[1] + a[0].rotate_vector(b[1]))


def rigid_inv(a):
    qi = a[0].inversed()
    return (qi, -qi.rotate_vector(a[1]))


def rigid_apply(a, v):
    return a[1] + a[0].rotate_vector(v)


def vec_delta_cm(a, b):
    """Component-wise (b - a) as a plain list, plus its length.

    unreal.Vector is not subscriptable, so every distance in this file goes
    through here rather than indexing the vector directly.
    """
    d = b - a
    return [d.x, d.y, d.z], math.sqrt(d.x ** 2 + d.y ** 2 + d.z ** 2)


def rigid_from_transform(xf):
    return (xf.rotation, xf.translation)


def read_rigid(comp, bone):
    return rigid_from_transform(
        comp.get_bone_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT))


def subject_comp():
    actor = find_actor("Film_Subject_Dana") or find_actor("Film_Subject_")
    if actor is None:
        raise RuntimeError("no Film_Subject actor in the open level")
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    if comp is None:
        raise RuntimeError("subject has no SkeletalMeshComponent")
    return actor, comp


def clear_subject_animation(comp):
    """Return the subject to its bind pose so a bind read is really a bind read.

    AnimationMode has no ANIMATION_NONE in this build; set_animation(None) plus
    override_animation_data(None, True) is what actually clears it (probe
    2026-10-17). Both are reported so a future reader can see which one worked.
    """
    steps = {}
    for label, call in (
            ("set_animation", lambda: comp.set_animation(None)),
            ("override_animation_data",
             lambda: comp.override_animation_data(None, True))):
        try:
            call()
            steps[label] = "ok"
        except Exception as exc:                                   # noqa: BLE001
            steps[label] = "ERR: %s" % str(exc)[:80]
    return steps


def face_follow_targets(comp):
    """The face-subtree roots present on this skeleton, with their parents.

    Discovered, not hardcoded: a root is a bone whose parent is one of the face
    system nodes. If the rig changes, the census changes with it instead of
    silently keying bones that no longer exist.
    """
    rows = []
    for name in FACE_FOLLOW:
        try:
            if int(comp.get_bone_index(name)) < 0:
                continue
            parent = str(comp.get_parent_bone(name))
        except Exception:                                          # noqa: BLE001
            continue
        rows.append({"bone": name, "parent": parent})
    return rows


def build_pose_frames(pose_name, mesh_path):
    mesh = E.load_asset(mesh_path)
    actor = find_actor("Film_Subject_Dana")
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    table = POSES[pose_name]
    frames, report_bones = [], []

    def bone_index(name):
        try:
            return int(comp.get_bone_index(name))
        except Exception:                                          # noqa: BLE001
            return -1

    w_cache = {}

    def chain_quat(bone):
        """Effective component-axis rotation with posed ancestors accumulated.

        A bone's authored ops are expressed against its BIND parent, so on
        playback the parent's rotation carries them along. The chain product is
        what the limb actually ends up pointing at, and is the number worth
        checking before a render is spent.
        """
        if bone in w_cache:
            return w_cache[bone]
        own = pose_world_quat(table[bone]) if bone in table else IDENTITY_QUAT
        parent = POSE_PARENT.get(bone)
        eff = (chain_quat(parent) * own) if parent in table else own
        w_cache[bone] = eff
        return eff

    def child_of(bone):
        """The bone's downstream deform bone, when it has one on the skeleton."""
        for cand in POSE_CHILD.get(bone, []):
            if bone_index(cand) >= 0:
                return cand
        stem, _, side = bone.partition("_")
        digits = stem[len(stem.rstrip("0123456789")):]
        if side and digits:
            nxt = "%s%d_%s" % (stem[: -len(digits)], int(digits) + 1, side)
            if bone_index(nxt) >= 0:
                return nxt
        return None

    for bone, ops in table.items():
        index = bone_index(bone)
        if index < 0:
            raise RuntimeError("pose bone not on skeleton: " + bone)
        l_bind = comp.get_ref_pose_transform(index)              # local bind
        c_bind = comp.get_bone_transform(
            bone, unreal.RelativeTransformSpace.RTS_COMPONENT)   # component bind
        w_own = pose_world_quat(ops)
        delta = c_bind.rotation.inversed() * w_own * c_bind.rotation
        l_new = l_bind.rotation * delta
        frames.append({
            "name": bone,
            "location": [l_bind.translation.x, l_bind.translation.y,
                         l_bind.translation.z],
            "rotation": [l_new.x, l_new.y, l_new.z, l_new.w],
            "scale": [1.0, 1.0, 1.0],
        })
        # Predicted child direction: how the sign conventions get verified
        # BEFORE a render is spent. Values are unit directions in component
        # space (+Z up, +Y nose). `predicted_chain` is the one to trust.
        child = child_of(bone)
        predicted_own, predicted_chain, bind_dir = None, None, None
        if child:
            c_child = comp.get_bone_transform(
                child, unreal.RelativeTransformSpace.RTS_COMPONENT)
            offs = c_child.translation - c_bind.translation
            norm = max(1e-6, math.sqrt(offs.x ** 2 + offs.y ** 2 + offs.z ** 2))
            bind_dir = [round(v / norm, 3) for v in (offs.x, offs.y, offs.z)]
            unit = unreal.Vector(bind_dir[0], bind_dir[1], bind_dir[2])
            d_own = w_own.rotate_vector(unit)
            d_chain = chain_quat(bone).rotate_vector(unit)
            predicted_own = [round(v, 2) for v in (d_own.x, d_own.y, d_own.z)]
            predicted_chain = [round(v, 2) for v in (d_chain.x, d_chain.y, d_chain.z)]
        report_bones.append({"bone": bone, "ops": ops, "child": child,
                             "bind_child_dir": bind_dir,
                             "predicted_own": predicted_own,
                             "predicted_chain": predicted_chain})
    try:
        skel = mesh.get_editor_property("skeleton")
        skel_path = skel.get_path_name() if skel else "UNKNOWN"
    except Exception as exc:                                       # noqa: BLE001
        skel_path = "UNREADABLE: %s" % exc
    frames_doc = {"pose": pose_name, "mesh": mesh_path, "skeleton": skel_path,
                  "bone_count": len(frames), "bones": report_bones}
    # build_sequence_from_poses wants frames = [ {bones:[...]}, ... ].
    # The first version wrote a list of LISTS, which is not a frame object.
    static_frame = {"bones": frames}
    (OUT / ("_poseframes_%s.json" % pose_name)).write_text(
        json.dumps({"frames": [static_frame, static_frame, static_frame]},
                   indent=2),
        encoding="utf-8")
    (OUT / ("_posereport_%s.json" % pose_name)).write_text(
        json.dumps(frames_doc, indent=2), encoding="utf-8")
    return {"pose": pose_name, "bones": len(frames),
            "frames_file": str(OUT / ("_poseframes_%s.json" % pose_name)),
            "skeleton": frames_doc["skeleton"]}


def write_pose_sequence(pose_name, mesh_path, bones):
    """Create/refresh the AnimSequence that holds an authored pose.

    Python-native on purpose: `unreal.AnimSequence.controller` is an
    AnimDataController, so the pose never has to be shipped through an MCP
    payload. The sequence is a static hold -- every key frame is identical.

    `bones` is the full track list. It is passed in rather than read from the
    frames file because the pose is built in two phases: the body first, then
    the face follow derived from how the body actually moved the head.
    """
    mesh = E.load_asset(mesh_path)
    skeleton = mesh.get_editor_property("skeleton") if mesh else None
    asset_name = "A_DanaFilm_Pose_%s" % pose_name
    full = "%s/%s" % (POSE_DIR, asset_name)
    seq = E.load_asset(full)
    created = False
    if seq is not None:
        # An earlier attempt created this asset before the factory had a
        # skeleton, which leaves it permanently unable to initialize its rig
        # hierarchy. It is this session's own artifact, so it is safe to
        # remove and rebuild -- never do this to an asset someone else made.
        try:
            if seq.get_editor_property("skeleton") is None:
                E.delete_asset(full)
                seq = None
        except Exception:                                          # noqa: BLE001
            pass
    if seq is None:
        # The skeleton has to be on the FACTORY: creating an AnimSequence
        # without one produces an asset whose rig hierarchy never initializes
        # ("Unable to retrieve target USkeleton for Animation Asset").
        factory = unreal.AnimSequenceFactory()
        try:
            factory.set_editor_property("target_skeleton", skeleton)
        except Exception as exc:                                   # noqa: BLE001
            log("factory target_skeleton failed: %s" % exc)
        try:
            factory.set_editor_property("preview_skeletal_mesh", mesh)
        except Exception:                                          # noqa: BLE001
            pass
        seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name, POSE_DIR, unreal.AnimSequence, factory)
        created = True
    if seq is None:
        raise RuntimeError("could not create animation sequence: " + full)
    steps = {}
    try:
        seq.set_editor_property("skeleton", skeleton)
        steps["skeleton"] = "ok"
    except Exception as exc:                                       # noqa: BLE001
        steps["skeleton"] = "ERR: %s" % exc
    ctrl = seq.get_editor_property("controller")
    if ctrl is None:
        raise RuntimeError("AnimSequence has no controller: " + full)
    for label, call in (("frame_rate", lambda: ctrl.set_frame_rate(
            unreal.FrameRate(numerator=30, denominator=1), False)),
                        ("number_of_frames", lambda: ctrl.set_number_of_frames(
                            HOLD_FRAMES, False))):
        try:
            call()
            steps[label] = "ok"
        except Exception as exc:                                   # noqa: BLE001
            steps[label] = "ERR: %s" % exc
    keyed, failed = [], []
    try:
        ctrl.open_bracket("author film pose", False)
    except Exception:                                              # noqa: BLE001
        pass
    for bone in bones:
        name = bone["name"]
        try:
            ctrl.add_bone_track(name, False)
        except Exception:                                          # noqa: BLE001
            pass                       # already exists on an updated sequence
        try:
            pos = [unreal.Vector(bone["location"][0], bone["location"][1],
                                 bone["location"][2])] * HOLD_FRAMES
            rot = [unreal.Quat(bone["rotation"][0], bone["rotation"][1],
                               bone["rotation"][2], bone["rotation"][3])] * HOLD_FRAMES
            scl = [unreal.Vector(1.0, 1.0, 1.0)] * HOLD_FRAMES
            if ctrl.set_bone_track_keys(name, pos, rot, scl, False):
                keyed.append(name)
            else:
                failed.append(name)
        except Exception as exc:                                   # noqa: BLE001
            failed.append("%s: %s" % (name, exc))
    try:
        ctrl.close_bracket(False)
    except Exception:                                              # noqa: BLE001
        pass
    saved = False
    try:
        saved = bool(E.save_loaded_asset(seq))
    except Exception as exc:                                       # noqa: BLE001
        steps["save"] = "ERR: %s" % exc
    record = {"pose": pose_name, "asset": full, "created": created,
              "hold_frames": HOLD_FRAMES, "bones_keyed": len(keyed),
              "bones_requested": len(bones), "bones_failed": failed,
              "steps": steps, "saved": saved,
              "play_length": round(seq.get_play_length(), 4)}
    (OUT / ("_buildpose_%s.json" % pose_name)).write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    return record


def build_face_follow(pose_name, mesh_path, sequence_path):
    """Derive the face-follow keys from how the body-only pose moved the head.

    Phase 1 of `build_pose_sequence` writes and applies a body-only sequence.
    This reads the head's actual rigid motion out of that live pose,

        A = C_head_posed . C_head_bind^-1

    and hands every face-subtree root exactly that motion, so the whole face
    rides the head the way the Maya constraint used to. Measuring instead of
    re-deriving the FK chain is deliberate: the head's motion is the product of
    five keyed spine/neck bones about five different pivots, and a closed-form
    accumulation is easy to get subtly wrong with nothing to check it against.
    Here the ground truth is the engine's own evaluation.

    Returns the extra bone rows plus the numbers, so the caller can publish the
    offsets it corrected rather than just claiming the face follows.
    """
    _, comp = subject_comp()
    bind_clear = clear_subject_animation(comp)
    head_bind = read_rigid(comp, FACE_ANCHOR)
    targets = []
    for row in face_follow_targets(comp):
        targets.append({
            "bone": row["bone"], "parent": row["parent"],
            "c_bind": read_rigid(comp, row["bone"]),
            "p_bind": read_rigid(comp, row["parent"]),
        })
    if not targets:
        return {"bones": [], "note": "no face-follow roots on this skeleton",
                "bind_clear": bind_clear}

    # phase 1: body only, then read what it did to the head
    apply_pose(sequence_path)
    head_posed = read_rigid(comp, FACE_ANCHOR)
    motion = rigid_mul(head_posed, rigid_inv(head_bind))

    bones, rows = [], []
    for t in targets:
        c_new = rigid_mul(motion, t["c_bind"])          # where the face must go
        l_new = rigid_mul(rigid_inv(t["p_bind"]), c_new)  # in its parent's frame
        bones.append({"name": t["bone"],
                      "location": [l_new[1].x, l_new[1].y, l_new[1].z],
                      "rotation": [l_new[0].x, l_new[0].y, l_new[0].z, l_new[0].w],
                      "scale": [1.0, 1.0, 1.0]})
        before = rigid_apply(t["c_bind"], unreal.Vector(0, 0, 0))
        after = rigid_apply(c_new, unreal.Vector(0, 0, 0))
        rows.append({
            "bone": t["bone"], "parent": t["parent"],
            "delta_cm": [round(v, 4) for v in
                         (after.x - before.x, after.y - before.y,
                          after.z - before.z)]})

    head_move, _ = vec_delta_cm(head_bind[1], head_posed[1])
    return {
        "bones": bones, "rows": rows, "bind_clear": bind_clear,
        "head_bind": [round(v, 4) for v in
                      (head_bind[1].x, head_bind[1].y, head_bind[1].z)],
        "head_posed": [round(v, 4) for v in
                       (head_posed[1].x, head_posed[1].y, head_posed[1].z)],
        "head_motion_translation_cm": [round(v, 4) for v in head_move],
        "note": ("the face is a SIBLING of the body under the skeleton root; "
                 "these keys replace the Maya head-follow constraint that a UE "
                 "skeleton cannot carry"),
    }


def build_pose_sequence(pose_name, mesh_path):
    """Build the authored pose asset: body first, then the face follow."""
    frame_path = OUT / ("_poseframes_%s.json" % pose_name)
    build_pose_frames(pose_name, mesh_path)          # writes frames + report
    body = json.loads(frame_path.read_text(encoding="utf-8"))["frames"][0]["bones"]
    full = "%s/A_DanaFilm_Pose_%s" % (POSE_DIR, pose_name)

    first = write_pose_sequence(pose_name, mesh_path, body)
    follow = build_face_follow(pose_name, mesh_path, full)
    record = {"pose": pose_name, "phase1_body_only": first, "face_follow": follow}
    if follow["bones"]:
        record["phase2"] = write_pose_sequence(pose_name, mesh_path,
                                               body + follow["bones"])
    record["bones_total"] = (first.get("bones_keyed", 0)
                             + (record.get("phase2", {}).get("bones_keyed", 0)
                                if follow["bones"] else 0))
    record["saved"] = record.get("phase2", first).get("saved")
    (OUT / ("_buildpose_%s.json" % pose_name)).write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    return record


def verify_face_follow(pose_name):
    """Does the face actually ride the head once the pose is applied?

    This is the regression for the defect that produced v06. It re-reads the
    LIVE component: with the pose applied, the face roots must sit on the head
    they were authored onto (bind offset ~0) and the face bones must have
    moved. Both halves matter -- a face that "moved" but not with the head is
    still a shattered face.
    """
    _, comp = subject_comp()
    clear_subject_animation(comp)
    anchor_bind = read_rigid(comp, FACE_ANCHOR)
    roots = face_follow_targets(comp)
    bind = {r["bone"]: read_rigid(comp, r["bone"]) for r in roots}
    watch = ["Eye_R", "Eye_L", "Jaw_M", "FaceUpper_M", "Lips_M",
             "browInnerJoint_R", "upperLidMain0_R"]
    watch_bind = {}
    for name in watch:
        try:
            if int(comp.get_bone_index(name)) >= 0:
                watch_bind[name] = read_rigid(comp, name)
        except Exception:                                          # noqa: BLE001
            pass

    apply_pose("%s/A_DanaFilm_Pose_%s" % (POSE_DIR, pose_name))
    anchor_posed = read_rigid(comp, FACE_ANCHOR)

    rows, worst = [], 0.0
    motion = rigid_mul(anchor_posed, rigid_inv(anchor_bind))
    for r in roots:
        posed = read_rigid(comp, r["bone"])
        # where the face root must be (head's own motion applied to its bind)
        want = rigid_apply(rigid_mul(motion, bind[r["bone"]]),
                           unreal.Vector(0, 0, 0))
        got = rigid_apply(posed, unreal.Vector(0, 0, 0))
        _, err = vec_delta_cm(want, got)
        worst = max(worst, err)
        rows.append({"bone": r["bone"], "offset_from_head_cm": round(err, 4)})

    moved = []
    for name, b in watch_bind.items():
        p = read_rigid(comp, name)
        _, d = vec_delta_cm(rigid_apply(b, unreal.Vector(0, 0, 0)),
                            rigid_apply(p, unreal.Vector(0, 0, 0)))
        moved.append({"bone": name, "moved_cm": round(d, 4)})

    min_face_move = min([m["moved_cm"] for m in moved], default=0.0)
    return {
        "pose": pose_name,
        "roots": rows,
        "worst_face_offset_from_head_cm": round(worst, 4),
        "face_movement": moved,
        "min_face_movement_cm": min_face_move,
        "verdict": ("face follows the head"
                    if worst < 0.25 and min_face_move > 0.25
                    else "FACE STILL DOES NOT FOLLOW THE HEAD"),
    }


def verify_pose_directions(pose_name):
    """Assert the played pose actually moved the deform chain.

    The bind pose is a T-pose, so "the pose silently did not apply" is a real
    and previously-shipped failure mode. This compares the live component-space
    bone directions against the directions predicted when the pose was
    authored, and reports the angle error per bone.
    """
    actor = find_actor("Film_Subject_Dana")
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    report_path = OUT / ("_posereport_%s.json" % pose_name)
    if not report_path.exists():
        return {"checked": 0, "note": "no pose report for " + pose_name}
    rows = json.loads(report_path.read_text(encoding="utf-8"))["bones"]
    checked, worst, detail = 0, 0.0, []
    for row in rows:
        pred, child = row.get("predicted_chain"), row.get("child")
        if not pred or not child:
            continue
        try:
            p = comp.get_bone_transform(row["bone"],
                                        unreal.RelativeTransformSpace.RTS_COMPONENT)
            c = comp.get_bone_transform(child,
                                        unreal.RelativeTransformSpace.RTS_COMPONENT)
        except Exception:                                          # noqa: BLE001
            continue
        d = c.translation - p.translation
        norm = math.sqrt(d.x ** 2 + d.y ** 2 + d.z ** 2)
        if norm < 1e-6:
            continue
        actual = (d.x / norm, d.y / norm, d.z / norm)
        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(actual, pred))))
        angle = math.degrees(math.acos(dot))
        checked += 1
        worst = max(worst, angle)
        detail.append({"bone": row["bone"],
                       "actual": [round(v, 2) for v in actual],
                       "predicted": [round(v, 2) for v in pred],
                       "angle_deg": round(angle, 1)})
    return {"checked": checked, "worst_angle_deg": round(worst, 1),
            "verdict": ("pose applied" if worst < 25.0 else
                        "POSE DID NOT APPLY AS AUTHORED"),
            "detail": detail}


def apply_pose(sequence_path):
    """Play an authored pose sequence on the subject and HOLD frame 0.

    Held, not looped: a film still wants one deliberate pose, and a loop would
    smear the capture across frames the owner never asked to see.
    """
    actor = find_actor("Film_Subject_Dana")
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    seq = E.load_asset(sequence_path)
    if seq is None:
        raise RuntimeError("pose sequence missing: " + sequence_path)
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    comp.set_animation(seq)
    comp.play(True)
    try:
        comp.set_play_rate(0.0)
    except Exception as exc:                                       # noqa: BLE001
        log("set_play_rate failed: %s" % exc)
    try:
        comp.set_position(0.0, False)
    except Exception as exc:                                       # noqa: BLE001
        log("set_position failed: %s" % exc)
    # Single-node playback alone does NOT drive this mesh. The editor world
    # leaves the actor's tick disabled, so the pose never evaluates and the
    # still silently renders the bind T-pose (measured: every bone 74-91 deg
    # off the authored direction, arms straight out). `override_animation_data`
    # is the editor's own preview-animation path, and it DOES evaluate on the
    # game thread immediately (measured: worst bone 10.2 deg off prediction,
    # all 18 within 25 deg). It is what makes an authored pose real here.
    override_note = "ok"
    try:
        comp.override_animation_data(seq, True)
    except Exception as exc:                                       # noqa: BLE001
        override_note = "ERR: %s" % exc
    readback = {}
    for getter in ("get_animation_mode", "get_animation", "is_playing"):
        fn = getattr(comp, getter, None)
        try:
            readback[getter] = str(fn()) if fn else "UNAVAILABLE"
        except Exception as exc:                                   # noqa: BLE001
            readback[getter] = "ERR: %s" % exc
    # "the pose is playing" has to be evidence, not an assumption: the stills
    # this lane shipped defective were silent bind-pose renders.
    inst = comp.get_anim_instance()
    readback["anim_instance"] = "none" if inst is None else str(inst.get_class().get_name())
    if inst is not None:
        for prop in ("current_asset", "play_rate", "current_time", "b_playing"):
            try:
                readback["inst." + prop] = str(inst.get_editor_property(prop))
            except Exception as exc:                               # noqa: BLE001
                readback["inst." + prop] = "ERR: %s" % str(exc)[:70]
    pose_name = str(sequence_path).rstrip("/").rsplit("/", 1)[-1]
    pose_name = pose_name.replace("A_DanaFilm_Pose_", "")
    verification = verify_pose_directions(pose_name)
    return {"sequence": sequence_path, "readback": readback,
            "held_frame": 0, "verification": verification,
            "override_animation_data": override_note,
            "note": "play_rate 0 -> the pose is held, not looped"}


# ---------------------------------------------------------------------------
# teardown -- hand the level back clean
# ---------------------------------------------------------------------------
def teardown():
    """Remove every session artefact from the open level.

    Why this exists: nothing in this session saves a map, but another lane may
    want to save one. A handoff must leave nothing behind that would either be
    baked into an authored map or silently change the next lane's frames.
    """
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_name = world.get_name() if world else "NONE"
    removed = clear_light_rig()
    record = {"mode": "teardown", "level": world_name,
              "removed_session_actors": removed,
              "removed_count": len(removed), "subject": None}
    subject = find_actor("Film_Subject_Dana") or find_actor("Film_Subject_")
    if subject is not None:
        comp = subject.get_component_by_class(unreal.SkeletalMeshComponent)
        stop = getattr(comp, "stop", None)
        if stop:
            try:
                stop()
            except Exception as exc:                               # noqa: BLE001
                log("comp.stop failed: %s" % exc)
        try:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_NONE)
            mode_note = "ANIMATION_NONE"
        except Exception as exc:                                   # noqa: BLE001
            mode_note = "animation mode reset failed: %s" % exc
        mesh = comp.get_skeletal_mesh_asset()
        record["subject"] = {
            "label": subject.get_actor_label(),
            "mesh_left_on_actor": mesh.get_path_name() if mesh else None,
            "animation_reset": mode_note,
            "materials_left": [str(m.get_path_name()) if m else None
                               for m in comp.get_materials()],
        }
    record["note"] = ("session scaffolding removed. The cast is in-memory only, so a "
                      "level reload WITHOUT saving returns the map to its authored "
                      "state; a save while overrides are live would bake them in, so "
                      "do not save before this teardown has run.")
    (OUT / "_teardown.json").write_text(json.dumps(record, indent=2),
                                        encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# casting
# ---------------------------------------------------------------------------
def normalize_and_ground(actor, offset):
    """Height-normalise to STAGE_HEIGHT_CM and ground min-Z, idempotently.

    Bounds are read AFTER each scale write and the loop re-derives the factor
    from the measured world height, so re-running on an already-scaled actor
    converges instead of dividing the scale away.
    """
    for _ in range(4):
        origin, extent = actor.get_actor_bounds(False)
        height = 2 * extent.z
        if height <= 0:
            raise RuntimeError("zero-height bounds while normalising")
        if abs(height - STAGE_HEIGHT_CM) / STAGE_HEIGHT_CM <= 0.002:
            break
        cur = actor.get_actor_scale3d()
        factor = STAGE_HEIGHT_CM / height
        actor.set_actor_scale3d(unreal.Vector(cur.x * factor, cur.y * factor,
                                              cur.z * factor))
    origin, extent = actor.get_actor_bounds(False)
    actor.set_actor_location(
        unreal.Vector(offset[0] - origin.x, offset[1] - origin.y,
                      actor.get_actor_location().z - (origin.z - extent.z)),
        False, False)
    origin, extent = actor.get_actor_bounds(False)
    return origin, extent


def cast_one(actor, mesh_path, slots, style, camera_label, offset, yaw_offset,
             strict):
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    if comp is None:
        raise RuntimeError("no skeletal component on " + actor.get_actor_label())
    mesh = E.load_asset(mesh_path)
    if mesh is None:
        raise RuntimeError("cast mesh missing: " + mesh_path)
    comp.set_skeletal_mesh_asset(mesh)
    for method, value in (("set_actor_hidden", False),
                          ("set_actor_hidden_in_game", False)):
        try:
            getattr(actor, method)(value)
        except Exception:                                          # noqa: BLE001
            pass

    origin, extent = normalize_and_ground(actor, offset)
    cam = find_camera(camera_label)
    if cam is None:
        raise RuntimeError("camera not in level: " + camera_label)
    cam_loc = cam.get_actor_location()
    yaw = math.degrees(math.atan2(cam_loc.y - origin.y,
                                  cam_loc.x - origin.x)) + yaw_offset
    actor.set_actor_rotation(unreal.Rotator(yaw=yaw), False)

    assign = {}
    unmapped = []
    for index in range(len(mesh.materials)):
        name = str(mesh.materials[index].material_slot_name).lower()
        part = slots.get(name)
        if part is None:
            if strict:
                raise RuntimeError("unmapped cast slot: " + name)
            unmapped.append(name)
            part = "Hidden"
        path = HIDDEN_MAT if part == "Hidden" else style_mi(style, part)
        mat = E.load_asset(path)
        if mat is None:
            raise RuntimeError("style material missing: " + path)
        comp.set_material(index, mat)
        assign[name] = {"part": part, "material": path}
    origin, extent = actor.get_actor_bounds(False)
    return {
        "actor": actor.get_actor_label(), "mesh": mesh_path,
        "sections": len(mesh.materials),
        "display_scale": [round(v, 6) for v in
                          (actor.get_actor_scale3d().x, actor.get_actor_scale3d().y,
                           actor.get_actor_scale3d().z)],
        "world_height_cm": round(2 * extent.z, 3),
        "floor_min_z_cm": round(origin.z - extent.z, 4),
        "yaw_degrees": round(yaw, 2),
        "slots": assign, "unmapped_slots": unmapped, "style": style,
    }


def cast_all(style, cast_spec, camera_label):
    record = {"style": style, "camera": camera_label,
              "level": "not saved (component-only casting)", "subjects": []}
    if cast_spec.get("dana", True):
        actor = find_actor("Film_Subject_Dana") or find_actor("Film_Subject_")
        if actor is None:
            raise RuntimeError("no Film_Subject actor in the level")
        record["dana_original_label"] = actor.get_actor_label()
        actor.set_actor_label("Film_Subject_Dana_v08_CleanSkin")
        record["subjects"].append(cast_one(
            actor, DANA_MESH, DANA_SLOTS, style, camera_label,
            PLACEMENT["dana"], float(cast_spec.get("yaw_offset", -90.0)), True))
    if cast_spec.get("david", False):
        actor = find_actor("Film_Subject_David")
        if actor is None:
            actor = A.spawn_actor_from_class(
                unreal.SkeletalMeshActor, unreal.Vector(),
                unreal.Rotator(yaw=-90.0))
            actor.set_actor_label("Film_Subject_David_ReferenceGrade")
        record["subjects"].append(cast_one(
            actor, DAVID_MESH, DAVID_SLOTS, style, camera_label,
            PLACEMENT["david"], float(cast_spec.get("yaw_offset", -90.0)), False))
    record["note"] = ("Dana v08 = validated transport mesh; David = existing "
                      "reference-grade render test mesh; neither is rig-action "
                      "validated and the level is not saved")
    (OUT / "_cast.json").write_text(json.dumps(record, indent=2),
                                    encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# fire
# ---------------------------------------------------------------------------
def capture_still(camera_label, stem, res=(1280, 720),
                  method="scene_capture", exposure_bias=0.0):
    """Render one still of the film camera, deterministically.

    The engine's take_high_res_screenshot route borrows the *first active level
    viewport* and asks that viewport to take the shot a few frames later
    (Engine/Source/Developer/FunctionalTesting/Private/
    AutomationBlueprintFunctionLibrary.cpp:1234 and :1266). When that viewport
    is not drawing -- which is what happens the moment another editor tab takes
    focus, e.g. the animation editor that opens when a pose sequence is created
    -- the request dies silently: no file, no error, no log line. This lane
    produced good stills and then a run of silent no-ops for exactly that
    reason, so the default is now a camera-matched SceneCapture2D writing into
    a render target, which does not care which tab is focused.

    Two-phase on purpose: a render target only fills on the next rendered
    frame, so this spawns the capture and leaves it alive (capture_every_frame)
    and `export_capture` writes the PNG once a frame has passed.
    """
    cam = find_camera(camera_label)
    if cam is None:
        raise RuntimeError("no camera labelled " + str(camera_label))
    info = {"camera": camera_label, "method": method,
            "resolution": [int(res[0]), int(res[1])]}
    if method == "viewport":
        # The engine asks the *first active level viewport* to take the shot a
        # few frames later (AutomationBlueprintFunctionLibrary.cpp:1234/1266).
        # If that viewport is not drawing, the request just sits in
        # FScreenshotRequest until it next draws: this lane had one land ~4
        # minutes late and several produce nothing at all, with no error -- an
        # editor tab taking focus is enough to stop the draw. So wake the
        # viewport first, and stamp the request time so a stale capture can
        # never be mistaken for this one.
        try:
            les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            les.editor_set_viewport_realtime(True)
            les.editor_invalidate_viewports()
            info["viewport_nudged"] = True
        except Exception as exc:                                   # noqa: BLE001
            info["viewport_nudged"] = "ERR: %s" % exc
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=int(res[0]), res_y=int(res[1]), filename=str(OUT / stem),
            camera=cam, mask_enabled=False, capture_hdr=False,
            force_game_view=True)
        info["task_type"] = type(task).__name__ if task is not None else None
        info["requested_epoch"] = time.time()
        info["expected_png"] = str(OUT / (stem + ".png"))
        return info

    world = unreal.EditorLevelLibrary.get_editor_world()
    # RGBA8, deliberately. ExportRenderTarget writes EXR (not PNG) whenever the
    # render target is a float format, and the extension is only appended by
    # the caller -- so a float target plus a bare stem silently produces an
    # extension-less EXR that no other tool in this lane can read. Final-colour
    # LDR is what a still wants anyway.
    rt = None
    try:
        rt = unreal.RenderingLibrary.create_render_target2d(
            world, int(res[0]), int(res[1]),
            format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
        info["rt_format"] = str(rt.get_editor_property("render_target_format"))
    except Exception as exc:                                       # noqa: BLE001
        info["rt_format_note"] = "RGBA8 request failed (%s); using default" % exc
        rt = unreal.RenderingLibrary.create_render_target2d(world, int(res[0]),
                                                            int(res[1]))
    if rt is None:
        raise RuntimeError("could not create a render target")
    cap = A.spawn_actor_from_class(unreal.SceneCapture2D,
                                   cam.get_actor_location(),
                                   cam.get_actor_rotation())
    if cap is None:
        raise RuntimeError("could not spawn a SceneCapture2D")
    cap.set_actor_label("SESSION_CAPTURE_%s" % stem)
    comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("capture_source",
                             unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    comp.set_editor_property("capture_every_frame", True)
    info["capture_actor"] = cap.get_actor_label()
    ccomp = cam.get_component_by_class(unreal.CineCameraComponent)
    if ccomp is not None:
        focal = float(ccomp.get_editor_property("current_focal_length"))
        filmback = ccomp.get_editor_property("filmback")
        sensor = float(filmback.get_editor_property("sensor_width"))
        fov = math.degrees(2.0 * math.atan(sensor / (2.0 * focal)))
        comp.set_editor_property("fov_angle", fov)
        # Deliberate capture PP. Do NOT copy the shot camera's post process
        # object wholesale: the Film_Cam_* cameras are authored for the editor
        # viewport with AEM_MANUAL plus a physical-camera exposure block
        # (camera_iso / camera_shutter_speed), and copying that object onto a
        # SceneCaptureComponent2D is what produced the black v08 still -- the
        # capture honoured the physical exposure path and wrote essentially
        # zero. The capture gets its own explicit manual exposure instead, so
        # the number on the PNG is the number this script set.
        pp = comp.get_editor_property("post_process_settings")
        bias = float(exposure_bias)
        try:
            pp.set_editor_property("auto_exposure_method",
                                   unreal.AutoExposureMethod.AEM_MANUAL)
            pp.set_editor_property("auto_exposure_bias", bias)
            pp.set_editor_property(
                "override_auto_exposure_apply_physical_camera_exposure", True)
            pp.set_editor_property(
                "auto_exposure_apply_physical_camera_exposure", False)
            comp.set_editor_property("post_process_settings", pp)
            comp.set_editor_property("post_process_blend_weight", 1.0)
            info["pp_note"] = "explicit manual exposure (physical camera path off)"
        except Exception as exc:                                   # noqa: BLE001
            info["pp_note"] = "explicit pp failed: %s" % exc
        loc = cam.get_actor_location()
        info.update({"focal_mm": round(focal, 2),
                     "sensor_width_mm": round(sensor, 2),
                     "fov_deg": round(fov, 3),
                     "exposure_bias": bias,
                     "camera_location": [round(loc.x, 2), round(loc.y, 2),
                                         round(loc.z, 2)]})
    comp.capture_scene()
    info["expected_png"] = str(OUT / (stem + ".png"))
    info["needs_export"] = True
    (OUT / ("_capture_%s.json" % stem)).write_text(json.dumps(info, indent=2),
                                                   encoding="utf-8")
    return info


def export_capture(stem):
    """Write the PNG for a capture spawned by `capture_still`.

    `export_render_target` returns void and writes the file asynchronously, so
    the capture actor must NOT be destroyed in the same call: releasing the
    render target before the write lands is why this lane's first attempt
    reported a successful export with no PNG on disk. Call this twice -- the
    second call sees the file and cleans the actor up.
    """
    label = "SESSION_CAPTURE_%s" % stem
    cap = find_actor(label)
    if cap is None:
        raise RuntimeError("no pending capture actor labelled " + label)
    world = unreal.EditorLevelLibrary.get_editor_world()
    comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
    rt = comp.get_editor_property("texture_target")
    comp.capture_scene()                     # refresh with the newest frame
    # the extension has to be on FileName: ExportRenderTarget never adds one
    unreal.RenderingLibrary.export_render_target(world, rt, str(OUT),
                                                 stem + ".png")
    png = OUT / (stem + ".png")
    record = {"stem": stem, "capture_actor": label,
              "expected_png": str(png), "exists": png.exists(),
              "bytes": png.stat().st_size if png.exists() else 0,
              "destroyed": False}
    if png.exists():
        A.destroy_actor(cap)
        record["destroyed"] = True
    else:
        record["note"] = ("export is async; actor kept alive -- call export "
                          "again to confirm the file and clean up")
    (OUT / ("_export_%s.json" % stem)).write_text(json.dumps(record, indent=2),
                                                  encoding="utf-8")
    return record


def fire(style, camera_label, stem, cast_spec, res=(1280, 720),
         light_preset=None, pose_sequence=None, intensity_scale=1.0,
         exposure_ev=None, capture_method="scene_capture"):
    cast_record = cast_all(style, cast_spec, camera_label)
    subject_loc = None
    for a in level_actors():
        if a.get_actor_label().startswith("Film_Subject_Dana"):
            subject_loc = a.get_actor_location()
            break
    lighting, posing = None, None
    cam = find_camera(camera_label)
    if light_preset:
        lighting = build_light_rig(light_preset, subject_loc,
                                   cam.get_actor_location(),
                                   scale=float(intensity_scale),
                                   camera=cam, exposure_ev=exposure_ev)
    if pose_sequence:
        posing = apply_pose(pose_sequence)
    t0 = time.time()
    capture = capture_still(camera_label, stem, res, method=capture_method,
                            exposure_bias=(float(exposure_ev)
                                           if exposure_ev is not None else 0.0))
    blocked = round(time.time() - t0, 2)
    rec = {"mode": "fire", "style": style, "camera": camera_label, "stem": stem,
           "expected_png": capture["expected_png"],
           "requested_resolution": [int(res[0]), int(res[1])],
           "call_started_epoch": t0,
           "call_started_local": time.strftime("%Y-%m-%d %H:%M:%S",
                                               time.localtime(t0)),
           "call_blocked_seconds": blocked,
           "task_type": capture.get("task_type"),
           "capture": capture,
           "light_preset": light_preset, "lighting": lighting,
           "intensity_scale": float(intensity_scale), "exposure_ev": exposure_ev,
           "pose": posing, "pose_requested": pose_sequence,
           "cast": cast_record["subjects"],
           "note": "call blocks then the capture finishes latently; caller polls"}
    (OUT / ("_pending_%s.json" % stem)).write_text(json.dumps(rec, indent=2),
                                                   encoding="utf-8")
    return {"stem": stem, "blocked_seconds": blocked,
            "world_height_cm": [s["world_height_cm"] for s in rec["cast"]],
            "yaw": [s["yaw_degrees"] for s in rec["cast"]],
            "lights": len(lighting["lights"]) if lighting else 0,
            "pose": posing}


# ---------------------------------------------------------------------------
# still measurement (same pure-stdlib decode rules as render_headless_driver)
# ---------------------------------------------------------------------------
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def decode_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != PNG_SIG:
        return None
    pos, idat, ihdr = 8, bytearray(), None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body[:13])
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if ihdr is None or not idat:
        return None
    w, h, depth, ctype, _c, _f, interlace = ihdr
    if depth != 8 or interlace != 0 or ctype not in (2, 6):
        return None
    ch = 3 if ctype == 2 else 4
    stride = w * ch
    try:
        raw = zlib.decompress(bytes(idat))
    except Exception:                                              # noqa: BLE001
        return None
    if len(raw) != (stride + 1) * h:
        return None
    out = bytearray(stride * h)
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                c = prev[i - ch] if i >= ch else 0
                b = prev[i]
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def measure(path):
    dec = decode_png(path)
    if dec is None:
        return None
    w, h, ch, px = dec
    sx, sy = max(1, w // 320), max(1, h // 180)
    n = luma_sum = luma_sq = sat_sum = 0.0
    dark = bright = 0
    for y in range(sy // 2, h, sy):
        for x in range(sx // 2, w, sx):
            i = (y * w + x) * ch
            r, g, b = px[i], px[i + 1], px[i + 2]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            luma_sum += luma
            luma_sq += luma * luma
            sat_sum += max(r, g, b) - min(r, g, b)
            n += 1
            if luma < 24:
                dark += 1
            if luma > 200:
                bright += 1
    if n == 0:
        return None
    mean = luma_sum / n
    var = max(0.0, luma_sq / n - mean * mean)
    return {"width": w, "height": h, "channels": ch,
            "mean_luma": round(mean, 2), "luma_stddev": round(var ** 0.5, 2),
            "mean_saturation": round(sat_sum / n, 2),
            "dark_frac": round(dark / n, 4), "bright_frac": round(bright / n, 4)}


def build_report():
    stills = []
    for pend in sorted(OUT.glob("_pending_*.json")):
        rec = json.loads(pend.read_text(encoding="utf-8-sig"))
        stem = rec["stem"]
        hits = sorted(OUT.glob(stem + "*.png"))
        row = {k: rec.get(k) for k in
               ("style", "camera", "stem", "requested_resolution",
                "call_started_local", "call_blocked_seconds", "light_preset",
                "pose_requested")}
        row["exists"] = bool(hits)
        if hits:
            png = hits[0]
            row["path"] = str(png)
            row["bytes"] = png.stat().st_size
            row["measured"] = measure(png)
            row["resolution_matches_request"] = (
                row["measured"] is not None and
                [row["measured"]["width"], row["measured"]["height"]]
                == rec["requested_resolution"])
            row["total_seconds"] = round(
                png.stat().st_mtime - float(rec["call_started_epoch"]), 2)
        stills.append(row)
    report = {
        "session": "universal_film_style_session_20261016",
        "plan": "Docs/UNIVERSAL_FILM_STYLE_SESSION_PLAN_20261016.md",
        "script": "Python/universal_film_style_session_20261016.py",
        "level": "L_Film_Office (never saved by this session)",
        "stills": stills, "stills_count": len(stills),
        "stills_with_png": sum(1 for s in stills if s["exists"]),
        "evidence_level": ("stills measured from decoded pixels + reflected "
                           "material/slot/pose readback; deformation quality, "
                           "retarget and the other rigs are NOT proven"),
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "style_session.json").write_text(json.dumps(report, indent=2),
                                              encoding="utf-8")
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    request = (json.loads(REQUEST.read_text(encoding="utf-8-sig"))
               if REQUEST.exists() else {"mode": "styles"})
    mode = request.get("mode", "styles")
    log("mode=%s" % mode)

    # ---- level guard -------------------------------------------------------
    # This session spawns SESSION_* actors and casts meshes into the OPEN level.
    # It must never do that inside a level another writer owns: that writer's
    # own save would bake session scaffolding into an authored map. So the
    # mutating modes refuse to run unless the open level is explicitly allowed.
    if mode in ("lights", "poseframes", "posecheck", "fire", "teardown",
                "buildpose", "facecheck"):
        allow = request.get("allowed_levels") or ["L_Film_Office"]
        world = unreal.EditorLevelLibrary.get_editor_world()
        world_name = world.get_name() if world else "NONE"
        if world_name not in allow:
            print(json.dumps({
                "refused": True, "mode": mode, "open_level": world_name,
                "allowed_levels": allow,
                "reason": ("session-only actors would be baked into the open "
                           "level by any other writer's save; this session never "
                           "mutates a level outside its allowlist")},
                indent=2))
            print("STYLE_SESSION_REFUSED")
            return
        # The other half of the guard: another agent shares this one editor.
        # Mutual exclusion lives in Saved/Coord/editor_lease.json, and this
        # script refuses to mutate while a foreign, unexpired lease is held.
        lease, lease_state = {}, "absent"
        try:
            lease = json.loads(LEASE.read_text(encoding="utf-8-sig"))
            lease_state = "readable"
        except Exception as exc:                                   # noqa: BLE001
            lease_state = "unreadable: %s" % exc
        owner = lease.get("owner")
        expires = float(lease.get("expires_epoch") or 0)
        if owner not in (None, "", LANE) and expires > time.time():
            print(json.dumps({
                "refused": True, "mode": mode, "lease_state": lease_state,
                "lease_owner": owner, "lease_intent": lease.get("intent"),
                "lease_expires_local": lease.get("expires_local"),
                "expires_in_seconds": round(expires - time.time()),
                "reason": ("another lane holds the editor lease; mutating while it "
                           "does risks colliding on the one open level")},
                indent=2))
            print("STYLE_SESSION_REFUSED")
            return
        log("lease ok (state=%s owner=%r)" % (lease_state, owner))

    if mode == "level":
        # Deliberate, guarded level switch. Refuses when any map is dirty, since
        # a load with unsaved map changes raises a save modal that blocks the
        # game thread and would stall every other lane sharing this editor.
        want = request["level"]
        world = unreal.EditorLevelLibrary.get_editor_world()
        current = world.get_name() if world else None
        dirty_maps = None
        try:
            dirty_maps = sorted(p.get_name() for p in
                                unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
        except Exception as exc:                                   # noqa: BLE001
            log("dirty-map probe unavailable: %s" % exc)
        if current == want:
            print(json.dumps({"mode": "level", "level": current,
                              "action": "already-open", "dirty_maps": dirty_maps},
                             indent=2))
        elif dirty_maps:
            print(json.dumps({"mode": "level", "level": current,
                              "action": "refused-dirty-maps",
                              "dirty_maps": dirty_maps,
                              "reason": ("loading away from a level with unsaved "
                                         "changes raises a blocking save modal; "
                                         "save or discard them first")}, indent=2))
            print("STYLE_SESSION_REFUSED")
            return
        else:
            loaded = None
            try:
                loaded = unreal.LevelEditorSubsystem().load_level(want)
                how = "LevelEditorSubsystem"
            except Exception as exc:                               # noqa: BLE001
                log("LevelEditorSubsystem.load_level failed (%s); trying EditorLevelLibrary" % exc)
                loaded = unreal.EditorLevelLibrary.load_level(want)
                how = "EditorLevelLibrary"
            world = unreal.EditorLevelLibrary.get_editor_world()
            after = world.get_name() if world else None
            record = {"mode": "level", "requested": want, "was": current,
                      "now": after, "via": how, "ok": after == want,
                      "load_returned": str(loaded), "saved": False}
            subjects = [a.get_actor_label() for a in level_actors()
                        if a.get_actor_label().startswith("Film_Subject_")]
            cams = [a.get_actor_label() for a in level_actors()
                    if a.get_actor_label().startswith("Film_Cam_")]
            record["subjects"] = subjects
            record["cameras"] = cams
            print(json.dumps(record, indent=2))
            (OUT / "_level.json").write_text(json.dumps(record, indent=2),
                                            encoding="utf-8")
        print("STYLE_SESSION_OK")
        return

    if mode == "styles":
        print(json.dumps(build_styles()["styles"], indent=2)[:1200])
    elif mode == "lights":
        subject = find_actor("Film_Subject_Dana")
        cam = find_camera(request.get("camera", "Film_Cam_OfficeMedium"))
        rec = build_light_rig(request.get("preset", "studio"),
                              subject.get_actor_location(),
                              cam.get_actor_location(),
                              scale=float(request.get("intensity_scale", 1.0)),
                              camera=cam,
                              exposure_ev=request.get("exposure_ev"))
        print(json.dumps(rec, indent=2)[:2000])
    elif mode == "poseframes":
        print(json.dumps(build_pose_frames(request["pose"], DANA_MESH),
                         indent=2)[:1500])
    elif mode == "buildpose":
        print(json.dumps(build_pose_sequence(request["pose"], DANA_MESH),
                         indent=2)[:2600])
    elif mode == "facecheck":
        print(json.dumps(verify_face_follow(request["pose"]), indent=2))
    elif mode == "verifypose":
        print(json.dumps(verify_pose_directions(request["pose"]),
                         indent=2)[:1800])
    elif mode == "posecheck":
        print(json.dumps(apply_pose(request["pose_sequence"]), indent=2))
    elif mode == "teardown":
        print(json.dumps(teardown(), indent=2)[:2000])
    elif mode == "fire":
        print(json.dumps(fire(request.get("style", "Toon"),
                              request.get("camera", "Film_Cam_OfficeMedium"),
                              request["stem"],
                              request.get("cast") or {"dana": True},
                              tuple(request.get("resolution") or (1280, 720)),
                              request.get("light_preset"),
                              request.get("pose_sequence"),
                              float(request.get("intensity_scale", 1.0)),
                              request.get("exposure_ev"),
                              request.get("capture_method", "scene_capture")),
                    indent=2)[:2000])
    elif mode == "export":
        print(json.dumps(export_capture(request["stem"]), indent=2)[:800])
    elif mode == "report":
        print(json.dumps(build_report(), indent=2)[:4000])
    else:
        raise RuntimeError("unknown mode: " + mode)
    print("STYLE_SESSION_OK")


if __name__ == "__main__":
    main()
