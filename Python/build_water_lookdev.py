"""Build L_Water_Lookdev - the controlled fixture for the water master.

WHAT THIS FIXTURE MUST SEPARATE
--------------------------------
The water master's failure modes are distinguishable only on distinct forms:
  * CANAL (large plane) - the scrolling ripple normal and the flowing band
    mask at their authored scales; a still frame proves band placement, and
    two stills at different times prove the flow actually moves.
  * PUDDLE (small plane) - the same graph at tight scale; if ripples alias
    into shimmer here, RippleScale1/2 are wrong for close-ups.
  * BANK (cube) - the fresnel edge ink where a form meets the surface at a
    grazing angle; an edge that follows form draws a line UP the bank, and
    a UV-stamped field does not.
One key light + weak sky, fixed camera - the same contract as
L_Gouache_Lookdev, so both fixtures read the same way.

The water planes use Engine BasicShape planes scaled up, matching the
gouache fixture's form-source precedent: lookdev fixtures measure MATERIALS,
and the basic shapes are the neutral geometry for that.
"""
from __future__ import annotations

import sys
from pathlib import Path

import unreal

# standalone launch: Python/ must be on sys.path or `import spine_lib` fails
# and the editor exits 0 having built nothing (measured 2026-10-03)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spine_lib as lib  # noqa: E402
import lookdev_lib  # noqa: E402

NAME = "L_Water_Lookdev"
MAP_DIR = "/Game/Maps"
ENGINE_SHAPES = {
    "plane": "/Engine/BasicShapes/Plane.Plane",
    "cube": "/Engine/BasicShapes/Cube.Cube",
}
INSTANCES = {
    "canal": "/Game/Materials/Instances/MI_Water_Canal",
    "puddle": "/Game/Materials/Instances/MI_Water_Puddle",
}
SUN_ROT = (-42.0, 195.0, 0.0)      # (pitch, yaw, roll) - gouache precedent
SUN_INTENSITY = 3.0
SKY_INTENSITY = 1.0
CAM_LOC = (520.0, -620.0, 340.0)
CAM_LOOK_AT = (0.0, 0.0, 0.0)


def resolve_world_factory():
    for nm in ("WorldFactory", "WorldFactoryNew", "WorldFactoryNewLevel"):
        cls = getattr(unreal, nm, None)
        if cls is not None:
            return cls
    return None


def ensure_level() -> str:
    """Open the fixture level via lookdev_lib (phantom purge, create, save,
    then load) - see lookdev_lib.ensure_level for why this is shared."""
    status = lookdev_lib.ensure_level(NAME)
    lib.log(f"level {NAME}: {' '.join(status['actions'])}")
    return status["asset_path"]


def spawn_mesh(label, mesh_path, location, scale, material, yaw=0.0):
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        lib.log(f"WARN {label}: mesh missing {mesh_path}")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=float(yaw)))
    actor.set_actor_label(label)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    if scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if material is not None:
        comp.set_material(0, material)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


def spawn_lights():
    pitch, yaw, roll = SUN_ROT
    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 4000),
        unreal.Rotator(roll=float(roll), pitch=float(pitch), yaw=float(yaw)))
    sun.set_actor_label("WLD_Sun")
    try:
        c = sun.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(SUN_INTENSITY)
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception as exc:
        lib.log(f"WARN sun config: {str(exc)[:100]}")
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 1000))
    sky.set_actor_label("WLD_Sky")
    try:
        c = sky.get_component_by_class(unreal.SkyLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(SKY_INTENSITY)
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception as exc:
        lib.log(f"WARN sky config: {str(exc)[:100]}")
    return sun, sky


def spawn_camera():
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(*CAM_LOC),
        unreal.Rotator(0, 0, 0))
    cam.set_actor_label("WLD_Cam")
    try:
        comp = cam.get_component_by_class(unreal.CineCameraComponent)
        lib.try_set(comp, "current_focal_length", 42.0)
    except Exception as exc:
        lib.log(f"WARN camera focal: {str(exc)[:100]}")
    try:
        rot = unreal.KismetMathLibrary.find_look_at_rotation(
            unreal.Vector(*CAM_LOC), unreal.Vector(*CAM_LOOK_AT))
        cam.set_actor_rotation(rot)
    except Exception as exc:
        lib.log(f"WARN camera aim: {str(exc)[:100]}")
    return cam


def build() -> dict:
    lib.log(f"=== {NAME} ===")
    report = {"level": NAME, "errors": [], "warnings": [], "forms": [],
              "materials": {}}

    for key, path in INSTANCES.items():
        asset = unreal.load_asset(path)
        report["materials"][key] = {"path": path, "loaded": asset is not None}
        if asset is None:
            report["warnings"].append(f"{key}: instance missing {path}")

    path = ensure_level()
    report["level_asset"] = path

    # forms: (label, shape, loc, scale, material_key, yaw)
    forms = (
        ("WLD_BankCube", "cube", (150, 0, 0), 3.0, None, 0.0),
        ("WLD_GroundStock", "plane", (-350, 0, -5), 10.0, None, 0.0),
        ("WLD_Canal", "plane", (0, 0, 0), 16.0, "canal", 0.0),
        ("WLD_Puddle", "plane", (450, 260, 5), 5.0, "puddle", 25.0),
    )
    for label, shape, loc, scale, mat_key, yaw in forms:
        mat = unreal.load_asset(INSTANCES[mat_key]) if mat_key else None
        if mat_key and mat is None:
            report["warnings"].append(
                f"{label}: no {mat_key} instance - renders engine default")
        ok = spawn_mesh(label, ENGINE_SHAPES[shape], loc, scale, mat,
                        yaw=yaw) is not None
        report["forms"].append({"label": label, "shape": shape,
                                "material": mat_key, "spawned": ok})
        if not ok:
            report["errors"].append(f"{label}: spawn failed")

    spawn_lights()
    spawn_camera()

    saved = lookdev_lib.save_current_level(report["level_asset"])
    report["level_saved"] = saved

    actors = unreal.EditorLevelLibrary.get_all_level_actors() or []
    labels = [a.get_actor_label() for a in actors]
    report["census"] = {
        "total": len(actors),
        "static_mesh": len([a for a in actors
                            if isinstance(a, unreal.StaticMeshActor)]),
        "all_forms_present": all(f["label"] in labels
                                 for f in report["forms"]),
    }

    report["notes"] = {
        "flow_is_time": ("Ripple fields scroll with Time - a still frame "
                         "proves band placement only; two frames at t and "
                         "t+2s prove the flow. Movie Render Queue on the "
                         "desktop is the real instrument."),
        "grazing_ink": ("The fresnel edge ink is judged where the bank cube "
                        "meets the canal plane; if the ink does not climb "
                        "the bank, the ripple normal is not feeding it."),
        "profile": ("The water master binds TP_Water at the master level; "
                    "instances cannot re-bind profiles on this build "
                    "(measured 2026-10-02, toon_profile_binding_probe_v3)."),
    }
    report["ok"] = (not report["errors"]) and saved
    _write_report(report)
    lib.log(f"{NAME}: ok={report['ok']} forms={len(report['forms'])} "
            f"saved={saved}")
    return report


def _write_report(report: dict) -> None:
    """Persist the fixture's evidence (see build_foliage_lookdev)."""
    import json
    out = (Path(__file__).resolve().parents[1] / "Saved" / "Audit"
           / "water_lookdev_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    return 0 if build()["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
