"""Build L_Gouache_Lookdev - the controlled fixture for judging M_PainterlyGouache.

WHY THIS LEVEL EXISTS
---------------------
The first lookdev pass at the gouache master produced no visual evidence at all.
`M_PainterlyGouache` had zero MI_* instances and was assigned to nothing; the
screenshots that prompted "they look a little meh" were captured at 23:08-23:13
on 10/02, while the gouache material was authored at 23:17 and saved at 02:36 on
10/03. Those stills show the stock toon master in `L_Brutalist_Layout`. So a
full review cycle was spent judging a material nobody had seen.

A material cannot be tuned from a still of the WRONG material, and it cannot be
tuned from a still of the RIGHT material in an uncontrolled scene either. This
level is the controlled scene: one deliberate light rig, a fixed camera, and a
form set chosen so each visual cue is separable.

WHAT THE FORMS ARE FOR
----------------------
Four cues have to be judged independently, because they fail differently:

  * SPHERE - pure curvature. The terminator crosses it continuously, so band
    placement and softness read without occlusion or creases confusing them.
    This is the reference form for "are the bands right".
  * CUBE - flat faces. Each face has ONE normal, so the wash inside a face must
    be perfectly flat. Any texture-driven banding shows up here immediately as a
    bug, and granulation is the only thing allowed to break the flatness.
  * CONE - sharp curvature change and a hard normal discontinuity at the
    silhouette. This is where a wet edge derived from the band gradient is
    proved or disproved: an edge that follows form draws a ring there, and a
    UV-stamped field does not.
  * PLANE - pure texture response, with no form-driven banding at all. Anything
    visible on it is granulation or blotch, which is the intent.
  * GREY BALL (18% linear) - the exposure anchor. CG Lounge's first rule for
    lookdev: you cannot judge "the shadow is too dark" against an unknown
    reference. 0.18 linear is the industry anchor and reads ~0.19 in ACEScg, so
    if this ball is not mid-grey the whole frame is mis-exposed and every colour
    judgement downstream is worthless.

STOCK VS GOUACHE
----------------
A parallel row carries the same meshes with the stock toon master. Comparing a
new look against nothing is how "meh" goes unmeasured: there has to be a
baseline in the same frame, under the same light, at the same camera.

LIGHTING
--------
ONE directional key at a declared angle, plus a weak SkyLight fill. Both are
NEUTRAL WHITE and there is no HDRI: a tinted key makes "is the wash too dark or
is the light too warm" unanswerable, which is the exact ambiguity that made the
first pass unreadable. CG Lounge's point stands - one setup is never enough.

NOTE ON THE KEY AND THE MATERIAL
--------------------------------
`M_PainterlyGouache` uses a FIXED `KeyLightDir` (currently (0,0,1)) and takes
NO light from the scene - a deliberate decision, documented at length in
build_gouache_material.py. Consequence for this fixture: the sun here does NOT
drive the wash bands. It drives cast shadow and the specular/roughness response
only. The bands come from the authored key vector against surface normals.

That means the sun's angle here does NOT have to match KeyLightDir for the bands
to read - which is the predictability that was traded for, and also exactly the
flaw (cast shadow and wash can disagree) that this fixture exists to make
visible.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/build_gouache_lookdev.py",
                             mode: execute_file}

Assert on the report FILE, not the log - `success: true` from the MCP layer only
means nothing threw.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

for _stale in ("build_gouache_material", "spine_lib"):
    sys.modules.pop(_stale, None)

import unreal

# The fixture builders are launched standalone (-ExecutePythonScript), so
# Python/ is NOT on sys.path the way it is inside build_spine.py - without
# this, `import spine_lib` dies with ModuleNotFoundError and the editor exits
# 0 with no level built (measured 2026-10-03, lookdev driver run 2).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spine_lib as lib  # noqa: E402
import lookdev_lib  # noqa: E402

LEVEL_NAME = "L_Gouache_Lookdev"
MAP_DIR = "/Game/Maps"

REPO = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get("TEMP", ".")) / "gouache_lookdev_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "gouache_lookdev_report.json"

GOUACHE_MASTER = "/Game/Materials/Masters/M_PainterlyGouache"
STOCK_MASTER = "/Game/Materials/Masters/M_Master_Toon_Universal"

ENGINE_SHAPES = {
    "sphere": "/Engine/BasicShapes/Sphere",
    "cube": "/Engine/BasicShapes/Cube",
    "cone": "/Engine/BasicShapes/Cone",
    "cylinder": "/Engine/BasicShapes/Cylinder",
    "plane": "/Engine/BasicShapes/Plane",
}

# (label, shape, location, scale, material_role)
FORMS = [
    ("REF_GreyBall18", "sphere", (-600.0, 0.0, 100.0), 1.0, "grey"),
    ("GUA_Sphere", "sphere", (-200.0, 0.0, 100.0), 1.0, "gouache"),
    ("GUA_Cube", "cube", (200.0, 0.0, 100.0), 1.0, "gouache"),
    ("GUA_Cone", "cone", (600.0, 0.0, 100.0), 1.0, "gouache"),
    ("GUA_Plane", "plane", (1000.0, 0.0, 100.0), 1.0, "gouache"),
]

COMPARE = [
    ("CMP_Stock_Sphere", "sphere", (-600.0, 600.0, 100.0), 1.0, "stock"),
    ("CMP_Gouache_Sphere", "sphere", (-200.0, 600.0, 100.0), 1.0, "gouache"),
    ("CMP_Stock_Cube", "cube", (200.0, 600.0, 100.0), 1.0, "stock"),
    ("CMP_Gouache_Cube", "cube", (600.0, 600.0, 100.0), 1.0, "gouache"),
]

# 18% reflectance, the CG Lounge / ACEScg mid-grey anchor. NOT black, NOT white:
# this ball exists so "too dark" becomes a measurable claim.
GREY_BALL_COLOR = (0.18, 0.18, 0.18, 1.0)

# Sun placement. Written (pitch, yaw, roll) to match the project spec's
# sun_rotation convention, and applied with KEYWORD args - see spawn_lights.
SUN_ROT = (-46.0, 35.0, 0.0)
SUN_INTENSITY = 4.0
SKY_INTENSITY = 0.6

CAM_LOC = (0.0, -900.0, 320.0)
CAM_LOOK_AT = (0.0, 300.0, 100.0)
CAM_FOCAL_MM = 50.0
GROUND_LABEL = "LDV_Ground"


def log(m):
    unreal.log("[GouacheLookdev] " + str(m))


def resolve_world_factory():
    """Find the level factory by probing, not by guessing the name.

    `unreal.WorldFactoryNew` does not exist on UE 5.8 - only `unreal.WorldFactory`
    does - so a hardcoded guess raises AttributeError the moment a fresh level is
    created. This is the same lesson as build_gouache_material's ENUM_SPECS: on
    this codebase a name that has not been measured must not be trusted, because
    the failure looks like a broken builder rather than a typo.
    """
    for nm in ("WorldFactory", "WorldFactoryNew", "WorldFactoryNewLevel"):
        cls = getattr(unreal, nm, None)
        if cls is not None:
            return cls
    return None


def ensure_level() -> str:
    """Open the fixture level via lookdev_lib (phantom purge, create, save,
    then load). The old local version is gone: it skipped creation when the
    asset registry claimed the package existed while the .umap was not on
    disk, which made load_level fatal (see lookdev_lib docstring)."""
    status = lookdev_lib.ensure_level(LEVEL_NAME)
    lib.log(f"level {LEVEL_NAME}: {' '.join(status['actions'])}")
    return status["asset_path"]


def resolve_materials() -> dict:
    """Load both masters and report which are real.

    The stock side is not optional: a baseline in the same frame is the only way
    "meh" becomes a specific, fixable claim instead of a vibe.
    """
    out = {}
    for key, path in (("gouache", GOUACHE_MASTER), ("stock", STOCK_MASTER)):
        asset = unreal.load_asset(path)
        out[key] = {"path": path, "loaded": asset is not None}
        if asset is None:
            log("WARN master missing: %s" % path)
    return out


def spawn_form(label, shape, location, scale, material):
    """One static mesh actor with a material chosen by ROLE.

    Probes the mesh first and returns (None, None) when absent, so a missing
    engine asset is recorded rather than raising and leaving the level
    half-built with no explanation in the report.
    """
    mesh_path = ENGINE_SHAPES.get(shape)
    if mesh_path is None:
        log("WARN %s: unknown shape role %r" % (label, shape))
        return None, None
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        log("WARN %s: engine mesh missing at %s" % (label, mesh_path))
        return None, None

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location), unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(label)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        log("WARN %s: no StaticMeshComponent" % label)
        return None, None

    # Movable for the swap, then STATIC: static mobility refuses a mesh change
    # mid-session. Same ordering as compose_shot_env_level.py.
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    if scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if material is not None:
        comp.set_material(0, material)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor, mesh


def spawn_ground(mat):
    """A floor to catch contact and give the bands something to cross.

    Plane is 100uu across at scale 1, hence the scale factor.
    """
    mesh = unreal.load_asset(ENGINE_SHAPES["plane"])
    if mesh is None:
        log("WARN ground mesh missing")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(GROUND_LABEL)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
def spawn_lights():
    """One key + a weak sky fill, both neutral white, no HDRI."""
    pitch, yaw, roll = SUN_ROT
    # Keyword args, NOT positional: unreal.Rotator is (roll, pitch, yaw) but
    # SUN_ROT is written (pitch, yaw, roll) to match the project spec. Getting
    # that order wrong put a 46-degree sun exactly ON the horizon once already -
    # see compose_shot_env_level.sun_rotator.
    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 4000.0),
        unreal.Rotator(roll=float(roll), pitch=float(pitch), yaw=float(yaw)))
    sun.set_actor_label("LDV_Sun")
    try:
        c = sun.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(SUN_INTENSITY)
        lib.try_set(c, "light_color", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        # Hard shadows on: a soft source blurs every band boundary, which is the
        # one thing this fixture must not do.
        lib.try_set(c, "cast_shadows", True)
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception as exc:                                       # noqa: BLE001
        log("WARN sun config: %s" % str(exc)[:100])

    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 1000.0))
    sky.set_actor_label("LDV_Sky")
    try:
        c = sky.get_component_by_class(unreal.SkyLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(SKY_INTENSITY)
        lib.try_set(c, "light_color", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception as exc:                                       # noqa: BLE001
        log("WARN sky config: %s" % str(exc)[:100])
    return sun, sky


def spawn_camera():
    """Fixed camera, so two renders are comparable pixel-for-pixel."""
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(*CAM_LOC),
        unreal.Rotator(0.0, 0.0, 0.0))
    cam.set_actor_label("LDV_Cam")
    try:
        comp = cam.get_component_by_class(unreal.CineCameraComponent)
        lib.try_set(comp, "current_focal_length", CAM_FOCAL_MM)
    except Exception as exc:                                       # noqa: BLE001
        log("WARN camera focal: %s" % str(exc)[:100])
    try:
        rot = unreal.KismetMathLibrary.find_look_at_rotation(
            unreal.Vector(*CAM_LOC), unreal.Vector(*CAM_LOOK_AT))
        cam.set_actor_rotation(rot)
    except Exception as exc:                                       # noqa: BLE001
        log("WARN camera aim: %s" % str(exc)[:100])
    return cam


def build() -> dict:
    report = {"level": LEVEL_NAME, "errors": [], "warnings": [],
              "forms": [], "missing_meshes": [], "materials": {}}

    report["materials"] = resolve_materials()
    if not report["materials"]["gouache"]["loaded"]:
        report["errors"].append(
            f"{GOUACHE_MASTER} not found - build the master before lookdev")

    mats = {
        "gouache": unreal.load_asset(GOUACHE_MASTER),
        "stock": unreal.load_asset(STOCK_MASTER),
        # The reference ball must show the LIGHT the scene gives it, so it gets
        # a plain grey material, NOT the gouache master. Putting the wash shader
        # on the exposure anchor would make it depend on the thing being measured.
        "grey": None,
    }

    path = ensure_level()
    report["level_asset"] = path

    spawn_ground(mats["stock"])

    for label, shape, loc, scale, role in FORMS + COMPARE:
        mat = None if role == "grey" else mats.get(role)
        if role != "grey" and mat is None:
            report["warnings"].append(
                f"{label}: no {role} material - renders with engine default")
        actor, _mesh = spawn_form(label, shape, loc, scale, mat)
        ok = actor is not None
        if not ok:
            report["missing_meshes"].append({"label": label, "shape": shape})
        report["forms"].append({
            "label": label, "shape": shape, "role": role,
            "location": list(loc), "spawned": ok,
            "mesh_asset": ENGINE_SHAPES.get(shape),
        })

    spawn_lights()
    spawn_camera()

    saved = lookdev_lib.save_current_level(report["level_asset"])
    report["level_saved"] = saved

    # Census from the LEVEL, not from what we intended to spawn. This is what
    # proves the actors are really in the level and persisted with it.
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors() or []
        labels = [a.get_actor_label() for a in actors]
        report["census"] = {
            "total": len(actors),
            "static_mesh": len([a for a in actors
                                if isinstance(a, unreal.StaticMeshActor)]),
            "directional": len([a for a in actors
                                if isinstance(a, unreal.DirectionalLight)]),
            "skylight": len([a for a in actors
                             if isinstance(a, unreal.SkyLight)]),
            "camera": len([a for a in actors
                           if isinstance(a, unreal.CineCameraActor)]),
            "all_forms_present": all(
                f["label"] in labels for f in report["forms"]),
        }
    except Exception as exc:                                       # noqa: BLE001
        report["census"] = {"error": str(exc)[:160]}

    report["notes"] = {
        "material_key_is_fixed": True,
        "material_key_dir": [0.0, 0.0, 1.0],
        "sun_does_not_drive_bands": (
            "M_PainterlyGouache derives its terminator from KeyLightDir, not "
            "from scene lights. The sun here drives cast shadow and specular "
            "only, so the bands and the shadow can disagree - that disagreement "
            "is the thing to inspect in this frame."),
        "grey_ball_linear": GREY_BALL_COLOR[0],
        "grey_ball_note": (
            "REF_GreyBall18 carries no project material, so it renders with the "
            "engine default. Treat its value as indicative and set an explicit "
            "0.18-linear material before trusting it as an exposure anchor."),
        "ddx_ddy_resolution_dependent": (
            "The wet edge is a screen-space derivative, so GouacheEdgeWidth and "
            "GouacheEdgeReference are resolution-dependent. Compare renders at "
            "one fixed resolution or the edge will not match."),
    }

    report["ok"] = (not report["errors"]) and saved
    return report


def verify(report):
    out = {}
    out["level_saved"] = bool(report.get("level_saved"))
    out["no_errors"] = not report["errors"]
    out["all_meshes_found"] = not report["missing_meshes"]
    out["all_forms_spawned"] = all(f["spawned"] for f in report["forms"])
    census = report.get("census", {})
    out["forms_in_level"] = bool(census.get("all_forms_present"))
    out["camera_present"] = census.get("camera", 0) >= 1
    out["key_light_present"] = census.get("directional", 0) >= 1
    out["grey_ball_present"] = any(
        f["role"] == "grey" and f["spawned"] for f in report["forms"])
    out["both_masters_loaded"] = all(
        report["materials"][k]["loaded"] for k in ("gouache", "stock"))
    out["ok"] = all(v for k, v in out.items() if k != "ok")
    return out


def main():
    report = build()
    report["verify"] = verify(report)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:                                              # noqa: BLE001
        pass
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["verify"]["ok"] else "FAIL"))
    for k, v in report["verify"].items():
        if k != "ok":
            log("  %-22s %s" % (k, v))
    return 0 if report["verify"]["ok"] else 1


if __name__ == "__main__":
    main()