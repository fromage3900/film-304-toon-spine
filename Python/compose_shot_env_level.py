"""Compose the prototype shot-environment level from the render spec.

WHY
---
`specs/humber_toon_spine/prototype_renders.v1.json` selects 8 of the 25 Brutalist
meshes and places them as a depth-layered vista, plus one camera per environment
shot. Nothing built the Unreal side, so "we can shoot the set" was only true on
paper. This turns the spec into a real level.

A THIRD LEVEL, DELIBERATELY
---------------------------
`L_Brutalist_Layout` is the review grid and stays untouched -- its six rows of
comparison variants are not a scene. `L_Toon_Lookdev` carries a Landscape, 64
landscape streaming proxies, 64 World Partition HLODs and a volumetric cloud
(measured with `project_query get_stats`); that is not a budget to prototype in
on a 4 GB GPU. The shot set gets its own lean level.

SPEC IS THE SOURCE OF TRUTH
---------------------------
Objects, scene positions, camera placements and focal lengths are read from the
spec, never retyped here. `Docs/CONTENT_CONVENTIONS.md` forbids copy-paste
between a spec and the asset it drives: a retyped number drifts silently.

Positions in the spec are UE world centimetres, NOT the manifest's Blender
review positions. The Blender->Unreal mapping (x*100, -y*100, z*100) established
in `stage_brutalist_layout.py` exists to REPRODUCE reviewed positions; applying
it to hand-composed coordinates would double-negate. Focal lengths and render
frames still come from the shot manifest.

GROUNDING IS MEASURED, NOT ASSUMED
----------------------------------
The exported meshes do not share one pivot convention: `OFFICE_BarbicanScale`
reports its local centre half a height above its origin (base-aligned) while the
city blocks and cubicles sit 1.7-4.1 m off (symmetric pivots). Rather than encode
an assumption, this measures each placed actor's world bounds and lifts it so
`min.z == 0`, recording every correction in the report. A piece that needed no
correction records 0.0.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/compose_shot_env_level.py",
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
SPEC = REPO / "specs" / "humber_toon_spine" / "prototype_renders.v1.json"
MESH_ROOT = "/Game/Environment/Brutalist"
REPORT = Path(os.environ.get("TEMP", ".")) / "shot_env_level_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "shot_env_level_report.json"

GROUND_LABEL = "ENV_Ground"
LIGHT_LABELS = ("LGT_Sun", "LGT_Sky", "Sky")
# Bounds are floats; a piece already resting on the plane reads exactly 0.
GROUNDING_TOL_UU = 5.0


def log(m):
    unreal.log("[ShotEnv] " + str(m))


def load_spec():
    if not SPEC.exists():
        raise RuntimeError("render spec missing: %s" % SPEC)
    return json.loads(SPEC.read_text(encoding="utf-8-sig"))


def ensure_dir(path):
    """Create a content folder if absent (never fails on an existing one)."""
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def owned_labels(spec):
    """Every actor label this script can create, so cleanup is safe and scoped.

    Only actors WE own are removed on a re-run -- destroying every actor in a
    level is fatal headless on an engine template map (build_test_level.py).
    """
    labels = set(LIGHT_LABELS)
    labels.add(GROUND_LABEL)
    for piece in spec["scene"]:
        labels.add(piece["object"])
    for shot in spec["shots"]:
        labels.add(shot["camera_label"])
    return labels


def remove_owned_actors(labels):
    removed = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() in labels:
                unreal.EditorLevelLibrary.destroy_actor(a)
                removed += 1
        except Exception:                                          # noqa: BLE001
            continue
    return removed


def open_or_create_level(pkg):
    """Idempotent: an existing set is reloaded and cleaned, never stacked."""
    ensure_dir(pkg.rsplit("/", 1)[0])

    # Switching levels while a map is dirty makes the editor raise a "save
    # changes?" MODAL, which blocks the game thread and leaves MCP unresponsive
    # (AGENTS.md rule 8 -- observed 2026-10-01 as MODAL_OPEN title='' text='').
    # Fail closed and let a human resolve it rather than wedge the editor.
    # get_dirty_MAP_packages only: the _content_ variant enumerates every loaded
    # package and took >30 s, which is what abandoned the HTTP client that time.
    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError(
            "dirty map package(s) %s -- save or discard them in the editor "
            "before composing; switching levels would open a blocking modal"
            % dirty)

    sub = unreal.LevelEditorSubsystem()
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        if not sub.load_level(pkg):
            raise RuntimeError("could not load %s" % pkg)
        log("reloaded existing level %s" % pkg)
        return "reloaded"
    if not sub.new_level(pkg):
        raise RuntimeError("could not create %s" % pkg)
    log("created level %s" % pkg)
    return "created"


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
    return actor, mesh, asset


def world_bounds(actor, mesh):
    """World AABB of an unrotated, unscaled actor: asset bounds + actor location.

    `mesh.get_bounds()` is the mesh's box in its OWN space, so adding the actor
    location is exact while rotation and scale are identity -- which they are for
    every building here (the ground plane, which IS scaled, is placed explicitly).
    """
    b = mesh.get_bounds()
    loc = actor.get_actor_location()
    return (float(loc.x) + float(b.origin.x) - float(b.box_extent.x),
            float(loc.y) + float(b.origin.y) - float(b.box_extent.y),
            float(loc.z) + float(b.origin.z) - float(b.box_extent.z),
            float(b.box_extent.x) * 2.0,
            float(b.box_extent.y) * 2.0,
            float(b.box_extent.z) * 2.0)


def spawn_ground(cfg):
    """A plane big enough to ground the masses and catch the shadow terminator."""
    mesh = unreal.load_asset(cfg["mesh"])
    if mesh is None:
        raise RuntimeError("ground mesh not found: %s" % cfg["mesh"])
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(GROUND_LABEL)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    # /Engine/BasicShapes/Plane is 100 uu across at scale 1.
    s = float(cfg["size_uu"]) / 100.0
    actor.set_actor_scale3d(unreal.Vector(s, s, 1.0))
    mi = unreal.load_asset(cfg["material"])
    if mi is not None:
        comp.set_material(0, mi)
    else:
        log("WARN ground material not found: %s" % cfg["material"])
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor, mesh


def sun_rotator(cfg):
    """Build the sun rotation from spec WITHOUT positional ambiguity.

    BUG (2026-10-02): this used to be
        unreal.Rotator(cfg["sun_rotation"][0], cfg["sun_rotation"][1],
                       cfg["sun_rotation"][2])
    but unreal.Rotator's positional constructor is (roll, pitch, yaw), while
    the spec's `sun_rotation` is (pitch, yaw, roll). The spec value
    [-46.0, 0.0, 35.0] - a sun 46 degrees ABOVE the horizon - was therefore
    applied as roll=-46, pitch=0, yaw=35, i.e. the sun sat exactly ON the
    horizon. Measured on the live light: {pitch: 0.000000, yaw: 35, roll: -46}.

    Consequence: every up-facing surface (the 200 m ground plane and every roof)
    received grazing light of effectively zero, so the 2026-10-02 prototype
    stills rendered as near-black silhouettes with no readable terminator. The
    spec's own ground note says the plane exists to make toon banding readable,
    so this silently defeated the thing it was added for.

    Keyword args make the ordering explicit and survive future edits.
    """
    pitch, yaw, roll = (cfg["sun_rotation"] + [0.0, 0.0, 0.0])[:3]
    return unreal.Rotator(roll=float(roll), pitch=float(pitch), yaw=float(yaw))


def spawn_lights(cfg):
    """Sun + sky + atmosphere, so the set reads on open."""
    d = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 4000.0),
        sun_rotator(cfg))
    d.set_actor_label("LGT_Sun")
    try:
        c = d.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(float(cfg["sun_intensity"]))
        c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception:                                              # noqa: BLE001
        pass

    if cfg.get("sky"):
        unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyLight, unreal.Vector(0.0, 0.0, 1000.0)).set_actor_label("LGT_Sky")
    if cfg.get("atmosphere"):
        try:
            unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0)).set_actor_label("Sky")
        except Exception as e:                                     # noqa: BLE001
            log("WARN SkyAtmosphere not spawned: %s" % e)


def spawn_camera(shot, filmback):
    """One CineCameraActor per shot, aimed with find_look_at_rotation.

    `Docs/GROUP_STAGING_GUIDE.md` section 3 fixes the framing: 16:9 at 24 fps with
    critical acting inside 93% action safe.

    The filmback is DERIVED FROM THE DELIVERABLE RESOLUTION and passed in, never
    hardcoded. take_high_res_screenshot constrains the captured frame to the
    CAMERA's filmback aspect, so an inherited 35 x 24.89 Academy back (1.406:1)
    returned 1012 x 720 for a 1280 x 720 request. It fails silently AND reframes
    every shot -- a focal length means nothing until the back matches the output.
    """
    loc = shot["location_uu"]
    tgt = shot["target_uu"]
    loc_v = unreal.Vector(float(loc[0]), float(loc[1]), float(loc[2]))
    rot = unreal.MathLibrary.find_look_at_rotation(
        loc_v, unreal.Vector(float(tgt[0]), float(tgt[1]), float(tgt[2])))

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor, loc_v, rot)
    actor.set_actor_label(shot["camera_label"])

    comp = actor.get_cine_camera_component()
    focal = float(shot["focal_length_mm"])
    comp.set_editor_property("current_focal_length", focal)
    fb_w, fb_h = float(filmback[0]), float(filmback[1])
    try:
        comp.set_editor_property(
            "filmback", unreal.CameraFilmbackSettings(fb_w, fb_h))
        comp.set_editor_property("constrain_aspect_ratio", True)
        comp.set_editor_property("aspect_ratio", fb_w / fb_h)
    except Exception as e:                                         # noqa: BLE001
        # Loud, not swallowed: a wrong back silently reframes the deliverable.
        log("WARN filmback not set on %s: %s" % (shot["camera_label"], e))
    return actor, focal, [fb_w, round(fb_h, 4)]


def build():
    spec = load_spec()
    report = {"errors": [], "level": spec["level"]["package"],
              "placed": [], "cameras": [], "grounding": [], "boxes": []}

    report["level_action"] = open_or_create_level(spec["level"]["package"])
    removed = remove_owned_actors(owned_labels(spec))
    log("removed %d previously owned actor(s)" % removed)

    g = spec["level"].get("ground", {})
    if g.get("enabled"):
        try:
            spawn_ground(g)
            report["ground"] = "%s @ %s uu" % (g["mesh"], g["size_uu"])
        except Exception as e:                                     # noqa: BLE001
            report["errors"].append("ground: %s" % e)
            log("FAILED ground: %s" % e)

    spawn_lights(spec["level"]["lights"])

    for piece in spec["scene"]:
        loc = [float(v) for v in piece["position_uu"]]
        try:
            actor, mesh, asset = spawn_mesh(
                piece["object"], piece["collection"],
                unreal.Vector(loc[0], loc[1], loc[2]))
        except Exception as e:                                     # noqa: BLE001
            report["errors"].append("%s: %s" % (piece["object"], e))
            log("FAILED %s: %s" % (piece["object"], e))
            continue

        mnx, mny, mnz, sx, sy, sz = world_bounds(actor, mesh)
        correction = 0.0
        if abs(mnz) > GROUNDING_TOL_UU:
            correction = -mnz
            actor.set_actor_location(
                unreal.Vector(loc[0], loc[1], loc[2] + correction), False, False)
            mnz += correction
        report["grounding"].append({
            "object": piece["object"],
            "z_correction_uu": round(correction, 1),
            "min_z_after_uu": round(mnz, 1),
        })
        report["placed"].append({
            "object": piece["object"], "role": piece["role"], "asset": asset,
            "requested_uu": loc, "z_correction_uu": round(correction, 1),
            "size_uu": [round(sx, 1), round(sy, 1), round(sz, 1)],
        })
        report["boxes"].append([piece["object"], round(mnx, 1), round(mny, 1),
                                round(mnz, 1), round(sx, 1), round(sy, 1),
                                round(sz, 1)])
        log("placed %s size=%.0f x %.0f x %.0f  dz=%+.1f"
            % (piece["object"], sx, sy, sz, correction))

    # The filmback comes from the deliverable, and the deliverable aspect is
    # recorded so verify() can prove the cameras match it.
    tier_res = spec["render_tier"]["resolution"]
    aspect = float(tier_res["width"]) / float(tier_res["height"])
    fb_spec = spec["render_tier"].get("filmback_mm")
    filmback = ([float(fb_spec["width"]), float(fb_spec["height"])]
                if fb_spec else [35.0, 35.0 / aspect])
    report["deliverable_resolution"] = [int(tier_res["width"]),
                                        int(tier_res["height"])]
    report["deliverable_aspect"] = round(aspect, 5)

    for shot in spec["shots"]:
        try:
            _actor, focal, fb = spawn_camera(shot, filmback)
            report["cameras"].append({
                "shot_id": shot["shot_id"], "label": shot["camera_label"],
                "focal_length_mm": focal, "location_uu": shot["location_uu"],
                "render_frame": shot["render_frame"],
                "still_name": shot["still_name"],
                "filmback_mm": fb, "filmback_aspect": round(fb[0] / fb[1], 5),
            })
            log("camera %s @ %smm filmback %.3f x %.4f (aspect %.5f)"
                % (shot["camera_label"], focal, fb[0], fb[1], fb[0] / fb[1]))
        except Exception as e:                                     # noqa: BLE001
            report["errors"].append("camera %s: %s" % (shot["shot_id"], e))
            log("FAILED camera %s: %s" % (shot["shot_id"], e))

    # Bounds live on level actors, not assets: persist or a reload loses them.
    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["level_saved"] = True
    except Exception as e:                                         # noqa: BLE001
        report["level_saved"] = False
        report["errors"].append("save level: %s" % e)
        log("FAILED saving level: %s" % e)

    report["expected_pieces"] = len(spec["scene"])
    report["placed_count"] = len(report["placed"])
    report["expected_shots"] = len(spec["shots"])
    return report


def _overlaps(a, b):
    """True when two AABBs intersect on ALL three axes (conservative but cheap)."""
    for axis in range(3):
        a0, a1 = a[1 + axis], a[1 + axis] + a[4 + axis]
        b0, b1 = b[1 + axis], b[1 + axis] + b[4 + axis]
        if a1 <= b0 or b1 <= a0:
            return False
    return True


def verify(report):
    """Re-check the composition from the report's own measured numbers."""
    ok = (report["placed_count"] == report["expected_pieces"]
          and len(report["cameras"]) == report["expected_shots"]
          and report.get("level_saved") is True
          and not report["errors"])

    grounded = [g for g in report["grounding"]
                if abs(g["min_z_after_uu"]) <= GROUNDING_TOL_UU]
    report["grounded_count"] = len(grounded)
    if len(grounded) != report["placed_count"]:
        ok = False
        report["errors"].append(
            "grounding: %d of %d pieces rest on z=0"
            % (len(grounded), report["placed_count"]))

    # A camera whose filmback aspect differs from the deliverable gets its frame
    # SILENTLY reframed by take_high_res_screenshot -- that is exactly how a
    # 1280x720 request produced 1012x720. Checked here so it cannot ship again.
    want_aspect = report.get("deliverable_aspect", 0.0)
    bad_aspect = [c["label"] for c in report["cameras"]
                  if abs(float(c.get("filmback_aspect", 0.0)) - want_aspect)
                  > 0.001]
    report["aspect_mismatched_cameras"] = bad_aspect
    if bad_aspect:
        ok = False
        report["errors"].append(
            "filmback aspect != deliverable aspect (%.5f) on %s -- the capture "
            "would be reframed" % (want_aspect, bad_aspect))

    # Intersecting buildings would read as geometry errors in every still, and
    # these positions are hand-composed rather than measured from a review.
    pairs = []
    for i in range(len(report["boxes"])):
        for j in range(i + 1, len(report["boxes"])):
            if _overlaps(report["boxes"][i], report["boxes"][j]):
                pairs.append([report["boxes"][i][0], report["boxes"][j][0]])
    report["overlapping_pairs"] = pairs
    if pairs:
        ok = False
        report["errors"].append("overlapping pieces: %s" % pairs)

    report["ok"] = ok
    return report


def write_report(report):
    """TEMP first: a repo write can fail while the editor still holds the level."""
    text = json.dumps(report, indent=2, sort_keys=True)
    REPORT.write_text(text, encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(text, encoding="utf-8")
    except Exception as e:                                         # noqa: BLE001
        log("WARN could not write audit copy: %s" % e)
    return text


if __name__ == "__main__" or "unreal" in sys.modules:
    r = verify(build())
    write_report(r)
    log("ok=%s placed=%d/%d cameras=%d/%d grounded=%d overlaps=%d"
        % (r["ok"], r["placed_count"], r["expected_pieces"],
           len(r["cameras"]), r["expected_shots"], r["grounded_count"],
           len(r["overlapping_pairs"])))
    for e in r["errors"]:
        log("ERROR %s" % e)
    log("report -> %s" % REPORT)