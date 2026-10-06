"""Build a lookdev test level - so the first editor open shows the spine working.

WHY
---
Everything else in this repo is structural. A level with one lit sphere per
look, a stand-in character plane, and a three-point rig is the cheapest way to
turn "it compiled" into "I can see it". Without it the project opens empty.

LIGHTING IS THE POINT, NOT A DETAIL
------------------------------------
Cel shading punishes soft fill: every light creates a band boundary. The rig
below is one strong key with a defined angle, a very weak fill, and a rim for
separation. Adding ambient or a broad fill will muddy every band in the spine.
If the banding looks soft, the fix is the lighting, not the profile.

Scene layout (X across, so every look is comparable side by side):
    X =    0  sphere   MI_Toon_Hero        +  outline shell
    X =  400  sphere   MI_Toon_TwoTone
    X =  800  sphere   MI_Toon_Painterly
    X = 1200  sphere   MI_Toon_Environment
    X = 1600  sphere   MI_Toon_Stone
    X = 2000  sphere   MI_Toon_Gold
    X = 2400  sphere   MI_Toon_Foliage
    X = 2800  sphere   MI_Toon_Hatched
    X = 3200  cube     MI_Toon_Hero        (hard edges, shows the outline pass)
    Z =  -100 plane    MI_Toon_Hero        (character stand-in, catches contact AO)

Run:
    UnrealEditor-Cmd.exe <project>.uproject ^
      -ExecutePythonScript="Python/build_test_level.py" -stdout -unattended
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# sys.path must be extended BEFORE sibling imports: under
# -ExecutePythonScript the script's own directory is NOT on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

import spine_lib as lib  # noqa: E402

LEVEL_NAME = "L_Toon_Lookdev"
MAP_DIR = f"/Game/Maps"
REPORT = Path(os.environ.get("TEMP", ".")) / "test_level_report.json"

CUBE = "/Engine/BasicShapes/Cube.Cube"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
PLANE = "/Engine/BasicShapes/Plane.Plane"


def log(m):
    unreal.log("[TestLevel] " + str(m))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _new_map():
    """Create a fresh SAVED map.

    Trap: EditorLevelLibrary.new_level(folder) opens an untitled level that is
    NOT on disk. save_current_level() on it silently does nothing useful, and
    the verify passes while no .umap exists - verified 2026-09-30, the report
    said ok with zero bytes written.

    Correct order: new_level -> populate -> save_as(new_level_path).
    """
    lib.ensure_dir(MAP_DIR)
    path = lib.asset_path(MAP_DIR, LEVEL_NAME)
    # new_level() gives an empty world. Do NOT iterate get_all_level_actors()
    # and destroy them: that loop is fatal headless on the template map's
    # Landscape / LandscapeStreamingProxy / VolumetricCloud actors and kills the
    # process with no traceback (traced with file breadcrumbs 2026-09-30,
    # last breadcrumb was "new_level-done"). Deleting the package first is
    # enough to keep the run idempotent.
    unreal.EditorAssetLibrary.delete_asset(path)
    # PASS THE LEVEL PATH, NOT THE FOLDER. This read `new_level(MAP_DIR)` and
    # MAP_DIR is "/Game/Maps" - the FOLDER. new_level() then creates the package
    # "/Game/Maps.Maps", i.e. a level literally named after its own folder, and
    # _save_map() writes the real content to /Game/Maps/L_Toon_Lookdev as well.
    # The result was TWO levels on disk, and the stray Content/Maps.umap was
    # committed to this repo on 2026-09-30 (found by reading the package name
    # out of the binary). Reported and fixed 2026-09-30.
    unreal.EditorLevelLibrary.new_level(lib.asset_path(MAP_DIR, LEVEL_NAME))
    return path


def _save_map(path):
    """Save the current untitled level to a real package.

    EditorLevelLibrary has NO save_level_as in UE 5.8 (probed 2026-09-30) -
    only save_current_level / save_all_dirty_levels, neither of which can name
    a destination for an untitled level. The working call is
    EditorLoadingAndSavingUtils.save_map(asset_path, filename).
    """
    # Signature is save_map(world, asset_path) - a World object and a
    # "/Game/Folder/Name" string WITHOUT the .Asset suffix. Passing two
    # strings raises a NativizeProperty conversion error (probed 2026-09-30).
    world = unreal.EditorLevelLibrary.get_editor_world()
    dest = path.rsplit(".", 1)[0]
    try:
        return bool(unreal.EditorLoadingAndSavingUtils.save_map(world, dest))
    except Exception as exc:
        log(f"save_map failed: {exc}")
        return False


def _spawn(actor_class, name, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(actor_class, unreal.Vector(loc[0], loc[1], loc[2]),
                                       unreal.Rotator(rot[0], rot[1], rot[2]))
    if actor is None:
        log(f"FAIL spawn {name}")
        return None
    actor.set_actor_label(name)
    try:
        actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    except Exception:
        pass
    return actor


def _static_mesh(name, mesh_path, loc, material, scale=(50, 50, 50), rot=(0, 0, 0)):
    """A StaticMeshActor with one material slot filled from our instance set."""
    actor = _spawn(unreal.StaticMeshActor, name, loc, rot, scale)
    if actor is None:
        return None
    comp = actor.static_mesh_component
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        log(f"FAIL mesh {mesh_path}")
        return actor
    comp.set_static_mesh(mesh)

    # UE 5.8 exposes StaticMeshComponent.get_material(index), not a
    # `static_materials` property. Set slot 0 and, when the mesh has more
    # slots, fill them too.
    mi = unreal.load_asset(material)
    comp.set_material(0, mi)
    num = 0
    try:
        num = comp.get_num_materials()
    except Exception:
        num = 1
    for i in range(1, num):
        comp.set_material(i, mi)
    return actor


def _light(name, light_class, loc, rot, intensity, color=(1, 1, 1), temp=None):
    actor = _spawn(light_class, name, loc, rot)
    if actor is None:
        return None
    comp = actor.get_component_by_class(unreal.LightComponentBase)
    if comp is None:
        log(f"WARN {name}: no light component")
        return actor
    lib.try_set(comp, "intensity", intensity)
    lib.try_set(comp, "color", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    # Cel shading: let the terminator stay hard. Cast shadows, keep the angle
    # defined. A soft source blurs every band in the spine.
    if isinstance(comp, unreal.DirectionalLightComponent):
        lib.try_set(comp, "cast_shadows", True)
    return actor


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

SPHERE_LOOKS = [
    (0, "MI_Toon_Hero", "L00_Hero"),
    (400, "MI_Toon_TwoTone", "L01_TwoTone"),
    (800, "MI_Toon_Painterly", "L02_Painterly"),
    (1200, "MI_Toon_Environment", "L03_Environment"),
    (1600, "MI_Toon_Stone", "L04_Stone"),
    (2000, "MI_Toon_Gold", "L05_Gold"),
    (2400, "MI_Toon_Foliage", "L06_Foliage"),
    (2800, "MI_Toon_Hatched", "L07_Hatched"),
]


def build():
    log("=== test level ===")
    report = {"actors": [], "errors": []}

    path = _new_map()
    log(f"new map at {path}")

    # ---- subject: one sphere per look, all facing the key ----
    for x, inst, label in SPHERE_LOOKS:
        mat = lib.asset_path(f"{lib.MATERIALS_ROOT}/Instances", inst)
        a = _static_mesh(label, SPHERE, (x, 0, 100), mat, scale=(50, 50, 50))
        report["actors"].append({"name": label, "material": inst,
                                 "spawned": a is not None})

    # ---- hard-edge cube: shows the inverted-hull outline next to a sphere ----
    cube_mat = lib.asset_path(f"{lib.MATERIALS_ROOT}/Instances", "MI_Toon_Hero")
    c = _static_mesh("L08_HeroCube_Outline", CUBE, (3200, 0, 100), cube_mat,
                     scale=(90, 90, 90), rot=(0, 25, 0))
    report["actors"].append({"name": "L08_HeroCube_Outline", "material": "MI_Toon_Hero",
                             "spawned": c is not None})

    # ---- ground plane: stand-in for a character, catches contact AO ----
    p = _static_mesh("L09_Ground", PLANE, (1600, 0, -100), cube_mat, scale=(400, 400, 400))
    report["actors"].append({"name": "L09_Ground", "material": "MI_Toon_Hero",
                             "spawned": p is not None})

    # ---- three-point rig ----
    # KEY: strong, angled, casting shadows. This defines the terminator.
    _light("KEY_Directional", unreal.DirectionalLight, (-600, -900, 1200),
           (-45, -35, 0), intensity=6.0, color=(1.0, 0.97, 0.92))
    # FILL: deliberately near-nothing. Raising this is what softens banding.
    _light("FILL_Directional", unreal.DirectionalLight, (600, 700, 500),
           (-20, 140, 0), intensity=0.35, color=(0.85, 0.90, 1.0))
    # RIM: separates the subject from the background.
    _light("RIM_Directional", unreal.DirectionalLight, (1200, 500, 700),
           (-10, 190, 0), intensity=3.0, color=(0.80, 0.90, 1.0))

    # ---- sky: only if the engine one is present ----
    if unreal.EditorAssetLibrary.does_asset_exist(
            "/Engine/EngineMeshes/SkySphere.SkySphere"):
        sk = _static_mesh("SKY_Sphere", "/Engine/EngineMeshes/SkySphere.SkySphere",
                          (1600, 0, 0),
                          "/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial",
                          scale=(60, 60, 60))
        report["actors"].append({"name": "SKY_Sphere", "spawned": sk is not None})
    else:
        report["actors"].append({"name": "SKY_Sphere", "spawned": False,
                                 "note": "engine sky sphere absent"})

    # ---- save as a real package ----
    saved = _save_map(path)
    report["saved_as"] = path
    report["save_ok"] = saved
    exists = unreal.EditorAssetLibrary.does_asset_exist(path)
    report["map_on_disk"] = exists
    if not (saved and exists):
        report["errors"].append("map did not write to disk")

    return report


def verify():
    """Confirm the level saved and the subjects carry our materials."""
    out = {"actors_found": [], "materials_ok": True}
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    # Only count what THIS script placed. The project boots into the engine
    # default template map (Landscape + 64 LandscapeStreamingProxy actors +
    # VolumetricCloud), and those land in the same level - counting them made
    # a correct 11-subject scene look like 75. Measured 2026-09-30.
    actors = [a for a in all_actors
              if not type(a).__name__ in ("LandscapeStreamingProxy",
                                          "Landscape", "WorldPartitionMiniMap",
                                          "VolumetricCloud", "WorldDataLayers")]
    out["all_actors"] = len(all_actors)
    out["actor_count"] = len(actors)
    out["ignored_engine_actors"] = len(all_actors) - len(actors)
    for a in actors:
        label = a.get_actor_label()
        out["actors_found"].append(label)
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            names = []
            try:
                n_slots = max(1, int(comp.get_num_materials()))
            except Exception:
                n_slots = 1
            for i in range(n_slots):
                try:
                    m = comp.get_material(i)
                except Exception:
                    m = None
                if m is not None:
                    names.append(str(m.get_path_name()))
            out.setdefault("subject_materials", {})[label] = names
            if names and not any("/Game/Materials/Instances/" in n for n in names):
                out["materials_ok"] = False
                out.setdefault("bad_materials", []).append(
                    {"actor": label, "materials": names})
    # Only actors THIS script placed are held to the spine contract. The
    # project boots into an engine template map, so the same level also holds
    # its Landscape, VolumetricCloud, sky sphere, and 63 World Partition HLOD
    # proxies - all legitimately /Engine/ or M_ProcGrid, none of them ours.
    # Classifying them by name produced 63 false failures; scope by our labels.
    OUR_LABELS = {a["name"] for a in []} or {
        lbl for _, _, lbl in SPHERE_LOOKS
    } | {"L08_HeroCube_Outline", "L09_Ground"}

    ours = {k: v for k, v in (out.get("subject_materials") or {}).items()
            if k in OUR_LABELS}
    out["subject_materials"] = ours
    out["subjects_found"] = len(ours)
    out["subjects_missing"] = sorted(OUR_LABELS - set(ours))

    real_bad = []
    for label, names in ours.items():
        if not names:
            real_bad.append({"actor": label, "materials": []})
        elif not any("/Game/Materials/Instances/" in n for n in names):
            real_bad.append({"actor": label, "materials": names})

    out["engine_scenery_count"] = len(out.get("bad_materials", []))
    out["bad_materials"] = real_bad
    out["materials_ok"] = not real_bad and not out["subjects_missing"]

    expected = len(SPHERE_LOOKS) + 2   # spheres + outline cube + ground
    out["subject_count"] = len([k for k in (out.get("subject_materials") or {})
                                if k.startswith("L")])
    out["expected_subjects"] = expected
    # the package must exist: a populated unsaved level verifies fine and is
    # invisible to everyone else
    mp = lib.asset_path(MAP_DIR, LEVEL_NAME)
    out["map_path"] = mp
    out["map_on_disk"] = unreal.EditorAssetLibrary.does_asset_exist(mp)
    out["ok"] = (out["materials_ok"]
                 and out["subjects_found"] == expected
                 and out["map_on_disk"])
    log(f"VERIFY level: ok={out['ok']} actors={out['actor_count']} "
        f"subjects={out.get('subjects_found')} "
        f"engine_scenery={out.get('engine_scenery_count')}")
    return out


def main():
    report = build()
    report["verify"] = verify()
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"report -> {REPORT}")
    ok = report["verify"].get("ok") and not report["errors"]
    log(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
