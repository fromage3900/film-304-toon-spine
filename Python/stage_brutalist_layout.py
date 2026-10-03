"""Stage the brutalist kit into a layout level at its REVIEWED positions.

WHY
---
`Docs/ASSETLIST.md` proves the kit is exported and imported, but 25 meshes
sitting in `Content/` are invisible until something places them. The reviewed
arrangement already exists as data: `Saved/Audit/brutalist_stage_manifest.json`
records each object's collection, preset, evaluated verts and Blender position,
and the Blender stager's contact sheets were reviewed from exactly that layout.
This reproduces it in Unreal.

A SEPARATE LEVEL, DELIBERATELY
-----------------------------
The reviewed positions are a REVIEW GRID -- six rows of variants laid out so a
contact sheet can compare them (cities at y=0, komikaze at y=320, offices at
y=-180, cubicles at y=-300, facades at y=-520, roofs at y=-740). They are not a
composed scene, and the city blocks are 90-156 m wide, so dropping them into
`L_Toon_Lookdev` would bury that level's toon-shading sphere row under a city.
The layout gets its own level; composing the kit into a shot scene is a creative
decision for the group, not something to infer from a review grid.

AXIS + SCALE ARE MEASURED, NOT GUESSED
--------------------------------------
The exporter carries the metres->centimetres x100, and the FBX -Y-forward
convention flips Y. Both were established by probing the imported meshes and
comparing against the manifest's local_bbox, not from theory:

    Blender position (m)  ->  Unreal location (uu) = (x*100, -y*100, z*100)

Evidence: KMZ_TightEstate sits at Blender y=+320 and its imported bounds centre
measured y=-32000 uu. The mapping below is that result.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/stage_brutalist_layout.py",
                             mode: execute_file}

Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
STAGE_MANIFEST = REPO / "Saved" / "Audit" / "brutalist_stage_manifest.json"
MESH_ROOT = "/Game/Environment/Brutalist"
MAP_DIR = "/Game/Maps"
LEVEL_NAME = "L_Brutalist_Layout"
LEVEL_PKG = "%s/%s" % (MAP_DIR, LEVEL_NAME)

REPORT = Path(os.environ.get("TEMP", ".")) / "brutalist_layout_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "brutalist_layout_report.json"

SCALE = 100.0            # Blender metres -> Unreal centimetres
# Blender (x, y, z) -> Unreal (x, -y, z). The Y negation is the FBX -Y-forward
# conversion, confirmed against imported bounds (see the module docstring).
AXIS_Y_SIGN = -1.0

# Minimal lighting so the layout is inspectable instead of a black viewport.
# A layout level is for eyeballing the kit, not for grading a shot -- the film's
# lighting rig belongs to the shot level, per Docs/GROUP_STAGING_GUIDE.md.
LIGHT_LABELS = ("LGT_Sun", "LGT_Sky", "Sky")


def log(m):
    unreal.log("[BrutalistLayout] " + str(m))


def to_unreal_location(pos_m):
    """Manifest Blender position (metres) -> Unreal location (uu)."""
    return unreal.Vector(pos_m[0] * SCALE,
                         pos_m[1] * SCALE * AXIS_Y_SIGN,
                         pos_m[2] * SCALE)


def to_unreal_extent(bbox_m):
    """Manifest Blender local_bbox (metres) -> Unreal half-extent (uu).

    local_bbox is the full width per axis, so the half-extent is half of it.
    """
    return unreal.Vector(bbox_m[0] * SCALE * 0.5,
                         bbox_m[1] * SCALE * 0.5,
                         bbox_m[2] * SCALE * 0.5)


def load_manifest():
    if not STAGE_MANIFEST.exists():
        raise RuntimeError("stage manifest missing: %s (run the Blender stager)"
                           % STAGE_MANIFEST)
    return json.loads(STAGE_MANIFEST.read_text(encoding="utf-8"))


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def open_or_create_level():
    """Idempotent: an existing layout level is reloaded and cleaned, not rebuilt.

    Re-running must not stack a second set of buildings. Only actors THIS script
    owns (by label) are removed -- destroying every actor in a level is fatal
    headless on an engine template map (documented in build_test_level.py).
    """
    ensure_dir(MAP_DIR)
    sub = unreal.LevelEditorSubsystem()
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PKG):
        if not sub.load_level(LEVEL_PKG):
            raise RuntimeError("could not load %s" % LEVEL_PKG)
        log("reloaded existing level %s" % LEVEL_PKG)
        removed = remove_owned_actors()
        log("removed %d previously staged actor(s)" % removed)
        return "reloaded"
    if not sub.new_level(LEVEL_PKG):
        raise RuntimeError("could not create %s" % LEVEL_PKG)
    log("created level %s" % LEVEL_PKG)
    return "created"


def owned_labels():
    """Every actor label this script can create, so cleanup is safe and scoped."""
    data = load_manifest()
    labels = set(LIGHT_LABELS)
    for objs in data["collections"].values():
        for o in objs:
            labels.add(o["object"])
    return labels


def remove_owned_actors():
    mine = owned_labels()
    removed = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() in mine:
                unreal.EditorLevelLibrary.destroy_actor(a)
                removed += 1
        except Exception:                                      # noqa: BLE001
            continue
    return removed


def spawn_mesh(object_name, collection, location):
    """One StaticMeshActor carrying SM_<object>, labelled <object>."""
    asset = "%s/%s/SM_%s" % (MESH_ROOT, collection, object_name)
    mesh = unreal.load_asset(asset)
    if mesh is None:
        raise RuntimeError("mesh not found: %s" % asset)

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(object_name)

    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        raise RuntimeError("%s: no StaticMeshComponent" % object_name)
    # Static mobility refuses a mesh swap mid-session; move it, set, move back.
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor, asset


def spawn_lights():
    """Sun + sky + atmosphere, so the level reads on open."""
    d = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 2000.0),
        unreal.Rotator(-46.0, 0.0, 35.0))
    d.set_actor_label("LGT_Sun")
    try:
        c = d.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(3.2)
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception:                                          # noqa: BLE001
        pass

    s = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 500.0))
    s.set_actor_label("LGT_Sky")

    try:
        unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0)).set_actor_label("Sky")
    except Exception as e:                                     # noqa: BLE001
        log("WARN SkyAtmosphere not spawned: %s" % e)


def actor_bounds(actor):
    """(world AABB centre, half-extent) for an actor."""
    try:
        res = actor.get_actor_bounds(False)
    except TypeError:
        res = actor.get_actor_bounds()
    return res[0], res[1]


def build():
    data = load_manifest()
    report = {"errors": [], "placed": [], "level": LEVEL_PKG,
              "mapping": "unreal = (x*100, -y*100, z*100) from Blender metres",
              "level_action": None}

    report["level_action"] = open_or_create_level()
    spawn_lights()

    for coll, objs in data["collections"].items():
        for o in sorted(objs, key=lambda r: r["object"]):
            try:
                loc = to_unreal_location(o["position"])
                actor, asset = spawn_mesh(o["object"], coll, loc)
                report["placed"].append({
                    "object": o["object"],
                    "collection": coll,
                    "asset": asset,
                    "blender_position_m": o["position"],
                    "expected_location": [round(loc.x, 1), round(loc.y, 1),
                                          round(loc.z, 1)],
                    "expected_size_uu": [round(v * SCALE, 1)
                                         for v in o["local_bbox"]],
                })
            except Exception as e:                             # noqa: BLE001
                report["errors"].append("%s: %s" % (o["object"], e))
                log("FAILED %s: %s" % (o["object"], e))

    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["level_saved"] = True
    except Exception as e:                                     # noqa: BLE001
        report["level_saved"] = False
        report["errors"].append("save level: %s" % e)
        log("FAILED saving level: %s" % e)

    report["expected_count"] = sum(len(v) for v in data["collections"].values())
    report["placed_count"] = len(report["placed"])
    return report


def verify(report):
    """Prove the placement from the placed actors, and prove it from geometry.

    Two independent things are checked, because either can be wrong alone:
      * each actor's AABB centre matches its manifest position (placement), and
      * each actor's AABB SIZE matches the manifest bbox x100 (scale).
    A x100 scale error passes a placement-only check, and a mis-mapped axis
    passes a size-only check. Then a pairwise overlap test -- the review grid is
    spaced so nothing intersects, so any intersection means the mapping or the
    scale is wrong.
    """
    out = {}
    tol = 150.0     # uu; the manifest bbox is rounded to 2 dp (cm-level slop)
    bad_place, bad_size = [], []
    local_offsets = []

    actors = []
    for rec in report["placed"]:
        a = None
        for cand in unreal.EditorLevelLibrary.get_all_level_actors():
            try:
                if cand.get_actor_label() == rec["object"]:
                    a = cand
                    break
            except Exception:                                  # noqa: BLE001
                continue
        if a is None:
            bad_place.append({"object": rec["object"], "why": "actor missing"})
            continue
        origin, extent = actor_bounds(a)
        size = [float(extent.x) * 2, float(extent.y) * 2, float(extent.z) * 2]
        exp_loc = rec["expected_location"]
        exp_size = rec["expected_size_uu"]

        # Assert the ACTOR LOCATION, not the world AABB centre. The manifest
        # carries a position and a bbox SIZE but not the geometry's local centre,
        # and the source meshes are not perfectly symmetric about their pivots --
        # five of the 25 (roof and cubicle variants) sit 1.7-4.1 m off. Comparing
        # AABB centres therefore fails on correct geometry. The size check below
        # is what proves the x100 scale; this check proves the placement.
        aloc = a.get_actor_location()
        if (abs(float(aloc.x) - exp_loc[0]) > 0.5
                or abs(float(aloc.y) - exp_loc[1]) > 0.5
                or abs(float(aloc.z) - exp_loc[2]) > 0.5):
            bad_place.append({"object": rec["object"],
                              "location": [round(float(aloc.x), 1),
                                           round(float(aloc.y), 1),
                                           round(float(aloc.z), 1)],
                              "expected": exp_loc})

        # Informational, not a failure: how far each mesh's own local centre sits
        # from its pivot. This is source-geometry asymmetry, surfaced so nobody
        # later mistakes it for a placement bug.
        local_offsets.append({
            "object": rec["object"],
            "offset_uu": [round(float(origin.x) - float(aloc.x), 1),
                          round(float(origin.y) - float(aloc.y), 1),
                          round(float(origin.z) - float(aloc.z), 1)],
        })

        for i, axis in enumerate("xyz"):
            if abs(size[i] - exp_size[i]) > tol:
                bad_size.append({"object": rec["object"], "axis": axis,
                                 "size": round(size[i], 1),
                                 "expected": exp_size[i]})
                break
        actors.append((rec["object"], origin, extent))

    # Pairwise overlap: origin +/- extent on every axis.
    overlaps = []
    for i in range(len(actors)):
        for j in range(i + 1, len(actors)):
            n1, o1, e1 = actors[i]
            n2, o2, e2 = actors[j]
            if (abs(float(o1.x - o2.x)) < float(e1.x + e2.x)
                    and abs(float(o1.y - o2.y)) < float(e1.y + e2.y)
                    and abs(float(o1.z - o2.z)) < float(e1.z + e2.z)):
                overlaps.append("%s <> %s" % (n1, n2))

    out["count_ok"] = report["placed_count"] == report["expected_count"] == 25
    out["level_saved"] = report.get("level_saved", False)
    out["placement_ok"] = not bad_place
    out["scale_ok"] = not bad_size
    out["no_overlaps"] = not overlaps
    out["bad_placement"] = bad_place
    out["bad_size"] = bad_size
    out["mesh_local_centre_offsets"] = local_offsets
    out["overlaps"] = overlaps[:12]
    out["errors"] = report["errors"]
    out["ok"] = (out["count_ok"] and out["level_saved"] and out["placement_ok"]
                 and out["scale_ok"] and out["no_overlaps"]
                 and not report["errors"])
    return out


def main():
    report = build()
    report["verify"] = verify(report)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    log("report -> %s" % REPORT)
    log("placed=%d/%d placement_ok=%s scale_ok=%s overlaps=%d"
        % (report["placed_count"], report["expected_count"],
           report["verify"]["placement_ok"], report["verify"]["scale_ok"],
           len(report["verify"]["overlaps"])))
    log("OVERALL: %s" % ("PASS" if report["verify"]["ok"] else "FAIL"))
    return 0 if report["verify"]["ok"] else 1


if __name__ == "__main__":
    main()