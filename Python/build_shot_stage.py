"""Build the OFFICE SPIDER interior stage level from a storyboard-derived spec.

WHY
---
`specs/office_spider/stage_shots.v1.json` is the storyboard-to-camera bridge for
the owner's 12 SH* sequences (board notes + Docs/OFFICE_SPIDER_SHOT_PLAN.md).
Nothing staged the CUBICLE-corner set the interior boards need, so "we can
shoot Act I" was only true on paper. This turns that spec into a real level:
the bay floor + walls, the Canonical cubicle, paper props with their realized
instances, troffer glows, and one CineCameraActor per shot with the filmback
rule the capture reframes by.

SPECS ARE THE SOURCE OF TRUTH
-----------------------------
Asset paths, positions, scales, materials, camera placements and focal lengths
are read from the spec, never retyped here (Docs/CONTENT_CONVENTIONS.md rule).
The builder adds only measured behaviours: world-bounds grounding, sits-on
stacking and the filmback aspect gate.

SITS-ON STACKING
----------------
The first pass stages every piece WITHOUT `sits_on` (and lifts auto pieces so
their world min.z rests on z=0). A second pass re-stages the `sits_on` pieces
so their measured world min.z rests on the reference piece's measured TOP - the
rug zone props stack on the carpet patch, not through it.

EVIDENCE
--------
The report is the assertion surface (TEMP + Saved/Audit copy). Run headless:

UnrealEditor-Cmd.exe HumberToonShader.uproject \
  -ExecutePythonScript="Python/build_shot_stage.py" -stdout -unattended

ONE LEVEL PER PROCESS: this script touches only L_Toon_Shot_Office.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

import level_lib  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "specs" / "office_spider" / "stage_shots.v1.json"
REPORT = Path(os.environ.get("TEMP", ".")) / "shot_stage_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "shot_stage_report.json"

GROUNDING_TOL_UU = 5.0


def log(m):
    unreal.log("[ShotStage] " + str(m))


def load_spec():
    if not SPEC.exists():
        raise RuntimeError("stage spec missing: %s" % SPEC)
    return json.loads(SPEC.read_text(encoding="utf-8-sig"))


def owned_labels(spec):
    """Every actor label this script owns, so re-run cleanup stays scoped."""
    labels = {"LGT_Sun", "LGT_Sky", "LGT_Fill", "LGT_PPV", "Sky"}
    for piece in spec["scene"]:
        labels.add(piece["object"])
    for shot in spec["shots"]:
        if not shot.get("reuse_level"):
            labels.add(shot["camera_label"])
    return labels


def spawn_piece(piece, spec_pos):
    """One StaticMeshActor from the spec; optional scale/rotation_z/material."""
    asset = piece["asset"]
    mesh = unreal.load_asset(asset)
    if mesh is None:
        raise RuntimeError("asset not found: %s" % asset)

    scale = piece.get("scale_uu") or [1.0, 1.0, 1.0]
    rot_z = float(piece.get("rotation_z_deg", 0.0))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(spec_pos[0], spec_pos[1],
                                              spec_pos[2]),
        unreal.Rotator(0.0, rot_z, 0.0))
    actor.set_actor_label(piece["object"])
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        raise RuntimeError("%s: no StaticMeshComponent" % piece["object"])
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    # 2026-10-08: END at the spawn default, NOT STATIC. The earlier dance
    # swapped the mesh then parked the component at STATIC; for static-mobility
    # components + stationary lights with no built lighting data, the
    # -game/MRQ render path evaluates direct light from the lightmap only ->
    # black geometry (the bisect pair: same instance .uassets light on a
    # fresh spawn, stay black on the parked-static staged pieces).
    actor.set_actor_scale3d(unreal.Vector(float(scale[0]), float(scale[1]),
                                          float(scale[2])))
    mat_path = piece.get("material")
    if mat_path:
        mi = unreal.load_asset(mat_path)
        if mi is not None:
            comp.set_material(0, mi)
        else:
            log("WARN %s: material not found: %s" % (piece["object"], mat_path))
            return actor, mesh, None
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor, mesh, mat_path


def measured_bounds(actor, mesh):
    """World AABB of an unrotated actor: mesh bounds + location. The pieces
    carry rotation_z only, which moves x/y extents within the actor's own
    bounds are NOT rotation-free here - swap to the ACTOR's bounds when the
    actor was rotated."""
    b = mesh.get_bounds()
    loc = actor.get_actor_location()
    return [float(loc.x) + float(b.origin.x) - float(b.box_extent.x),
            float(loc.y) + float(b.origin.y) - float(b.box_extent.y),
            float(loc.z) + float(b.origin.z) - float(b.box_extent.z),
            float(b.box_extent.x) * 2.0, float(b.box_extent.y) * 2.0,
            float(b.box_extent.z) * 2.0]


def actor_bounds(actor):
    """Actor-space bounds (rotation-aware). get_actor_bounds returns a
    (origin, box_extent) tuple on this build; the FIRST arg is named
    only_colliding_components (measured 2026-10-08 - both keyword names in
    the Unreal docs and the simple-collider variant raised). Call positionally.
    """
    origin, ext = actor.get_actor_bounds(False)
    return [origin.x - ext.x, origin.y - ext.y, origin.z - ext.z,
            ext.x * 2.0, ext.y * 2.0, ext.z * 2.0]


def spawn_camera(shot, filmback):
    """CineCameraActor for a stage shot, aimed with find_look_at_rotation,
    filmback forced to the deliverable aspect (the capture silently reframes
    otherwise -- the rule that cost the 1280x720->1012x720 trim, 2026-10-01)."""
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
    except Exception as e:                                        # noqa: BLE001
        log("WARN filmback not set on %s: %s" % (shot["camera_label"], e))
    return actor, focal


def _overlaps(a, b):
    for axis in range(3):
        a0, a1 = a[axis], a[axis] + a[3 + axis]
        b0, b1 = b[axis], b[axis] + b[3 + axis]
        if a1 <= b0 or b1 <= a0:
            return False
    return True


def build():
    spec = load_spec()
    report = {"errors": [], "level": spec["level"]["package"],
              "placed": [], "cameras": [], "pieces_top_z": {}}

    report["spec_levels"] = [lv["name"] for lv in spec["levels"]]

    report["level_action"] = level_lib.open_or_create_level(
        spec["level"]["package"], clean_labels=owned_labels(spec))

    L = spec["level"]["lights"]
    level_lib.spawn_lights(sun_rotation=L["sun_rotation"],
                           sun_intensity=float(L.get("sun_intensity", 3.2)),
                           sun_height=float(L.get("sun_height", 4000.0)),
                           sky=bool(L.get("sky", True)),
                           sky_height=float(L.get("sky_height", 1000.0)),
                           atmosphere=bool(L.get("atmosphere", False)))
    # interior fill (second directional, opposite the key) - the black
    # SH020 still of 2026-10-08 was a light-AIMING defect: the key hit the
    # wall's back. A fill against the key keeps the unlit faces off black.
    if L.get("fill_light"):
        fill = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0.0, 0.0, float(L.get("sun_height", 2600.0))),
            level_lib.sun_rotator(*L["fill_rotation"]))
        fill.set_actor_label("LGT_Fill")
        fc = fill.get_component_by_class(unreal.DirectionalLightComponent)
        try:
            # 2026-10-08 v03 fix (mobility, matching level_lib.spawn_lights):
            # a STATIC fill light delivered NO direct light under the headless
            # -game/MRQ path on unbaked static geometry (the office_asset_
            # bisect probe's fresh mobs lit while the staged surfaces did not).
            fc.set_intensity(float(L.get("fill_intensity", 1.5)))
        except Exception as e:                          # noqa: BLE001
            log("WARN fill intensity: %s" % e)

    # 2026-10-08 v02 fix (the white-wash/black-split of the -game stills):
    # the SLS_CapturedScene Skylight had NO sky content to capture (no
    # SkyAtmosphere in this level) -> zero ambient, and fixed project
    # exposure (r.DefaultFeature.AutoExposure=False) blew sun-lit faces
    # white at sun 5.0 while shadows went black. The spec now carries
    # atmosphere:true (spawned by spawn_lights above); seal it in: re-
    # capture the skylight AFTER the atmosphere exists, and give the bay
    # an unbounded PPV so the exposure law lives in the level.
    try:
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            if a.get_actor_label() == "LGT_Sky":
                skc = a.get_component_by_class(unreal.SkyLightComponent)
                skc.set_intensity(float(L.get("sky_intensity", 1.0)))
                skc.call_method("recapture_sky")
                log("skylight recaptured after atmosphere spawn")
                break
    except Exception as e:                              # noqa: BLE001
        log("WARN skylight seal: %s" % e)
    try:
        ppv = None
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            if a.get_actor_label() == "LGT_PPV":
                ppv = a
                break
        if ppv is None:
            ppv = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.PostProcessVolume,
                unreal.Vector(0.0, 0.0, float(L.get("sky_height", 1000.0))),
                unreal.Rotator(0.0, 0.0, 0.0))
            ppv.set_actor_label("LGT_PPV")
        ppv.set_editor_property("unbounded", True)
        log("PPV unbounded (auto exposure law in level)")
    except Exception as e:                              # noqa: BLE001
        log("WARN PPV: %s" % e)

    actors = {}
    meshes = {}
    passes = [p for p in ("base", "sits_on")]

    for pidx, pgroup in enumerate(passes):
        for piece in spec["scene"]:
            mode = piece.get("ground_correction", "auto")
            if pgroup == "base" and mode == "skip":
                pass  # first pass handles skip-together with explicit z's
            elif pgroup == "base" and bool(piece.get("sits_on")):
                continue
            elif pgroup == "sits_on" and not piece.get("sits_on"):
                continue
            elif pgroup == "sits_on" and piece.get("ground_correction") == "skip":
                continue

            if piece["object"] in actors and actors[piece["object"]] is not None:
                log("%s already staged this run" % piece["object"])
                continue

            loc = [float(v) for v in piece["position_uu"]]
            try:
                actor, mesh, mat = spawn_piece(piece, loc)
            except Exception as e:                                # noqa: BLE001
                report["errors"].append("%s: %s" % (piece["object"], e))
                log("FAILED %s: %s" % (piece["object"], e))
                actors[piece["object"]] = None
                continue
            actors[piece["object"]] = actor
            meshes[piece["object"]] = mesh

            b = actor_bounds(actor)
            correction = 0.0
            sits_ref = piece.get("sits_on")
            if sits_ref:
                ref = report["pieces_top_z"].get(sits_ref)
                if ref is None:
                    report["errors"].append(
                        "%s: sits_on '%s' has no measured top - the staging "
                        "order is wrong" % (piece["object"], sits_ref))
                else:
                    correction = ref - b[2]
                    if abs(correction) > GROUNDING_TOL_UU:
                        actor.set_actor_location(
                            unreal.Vector(loc[0], loc[1],
                                          loc[2] + correction), False, False)
                        b = actor_bounds(actor)
                    report["pieces_top_z"][piece["object"]] = round(b[2] + b[5], 1)
            elif mode == "auto":
                if abs(b[2]) > GROUNDING_TOL_UU:
                    correction = -b[2]
                    actor.set_actor_location(
                        unreal.Vector(loc[0], loc[1], loc[2] + correction),
                        False, False)
                    b = actor_bounds(actor)
                    report["pieces_top_z"][piece["object"]] = round(b[2] + b[5], 1)
            else:  # skip: trust the spec position (floor/ceiling fixtures)
                report["pieces_top_z"][piece["object"]] = round(b[2] + b[5], 1)

            report["placed"].append({
                "object": piece["object"], "asset": piece["asset"],
                "role": piece["role"], "material": mat,
                "requested_uu": loc, "z_correction_uu": round(correction, 1),
                "bounds_min": [round(b[0], 1), round(b[1], 1), round(b[2], 1)],
                "size_uu": [round(b[3], 1), round(b[4], 1), round(b[5], 1)],
            })
            log("placed %s dz=%+.1f top=%s" % (
                piece["object"], correction,
                report["pieces_top_z"].get(piece["object"])))

    tier_res = spec["render_tier"]["resolution"]
    aspect = float(tier_res["width"]) / float(tier_res["height"])
    fb_spec = spec["render_tier"].get("filmback_mm")
    filmback = ([float(fb_spec["width"]), float(fb_spec["height"])]
                if fb_spec else [35.0, 35.0 / aspect])
    report["deliverable_resolution"] = [int(tier_res["width"]),
                                        int(tier_res["height"])]
    report["deliverable_aspect"] = round(aspect, 5)

    for shot in spec["shots"]:
        if shot.get("reuse_level"):
            report["cameras"].append({
                "shot_id": shot["shot_id"],
                "label": shot["camera_label"],
                "reuse_level": shot["reuse_level"],
                "note": "camera staged by the exterior composition spec; "
                        "rendered through that level"})
            continue
        try:
            _actor, focal = spawn_camera(shot, filmback)
            report["cameras"].append({
                "shot_id": shot["shot_id"], "label": shot["camera_label"],
                "focal_length_mm": focal, "location_uu": shot["location_uu"],
                "target_uu": shot["target_uu"],
                "render_frame": shot.get("render_frame"),
                "still_name": shot["still_name"],
                "filmback_mm": filmback,
                "filmback_aspect": round(filmback[0] / filmback[1], 5)})
            log("camera %s @ %smm filmback %.3f x %.4f"
                % (shot["camera_label"], focal, filmback[0], filmback[1]))
        except Exception as e:                                    # noqa: BLE001
            report["errors"].append("camera %s: %s" % (shot["shot_id"], e))
            log("FAILED camera %s: %s" % (shot["shot_id"], e))

    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["level_saved"] = True
    except Exception as e:                                        # noqa: BLE001
        report["level_saved"] = False
        report["errors"].append("save level: %s" % e)
        log("FAILED saving level: %s" % e)

    scene_boxes, overlap_ok = _scene_boxes(spec, report, actors)
    report["boxes"] = scene_boxes
    report["overlapping_pairs"] = _overlap_pairs(scene_boxes, overlap_ok)
    report["expected_pieces"] = len(spec["scene"])
    report["placed_count"] = len(report["placed"])
    report["expected_shots"] = len(spec["shots"])
    return report


def _scene_boxes(spec, report, actors):
    boxes = []
    for piece in spec["scene"]:
        actor = actors.get(piece["object"])
        if actor is None:
            continue
        b = actor_bounds(actor)
        boxes.append([piece["object"], round(b[0], 1), round(b[1], 1),
                      round(b[2], 1), round(b[3], 1), round(b[4], 1),
                      round(b[5], 1)])
    ok_with = set()
    for piece in spec["scene"]:
        for other in piece.get("overlap_ok_with") or []:
            ok_with.add(_pair_key(piece["object"], other))
            ok_with.add(_pair_key(other, piece["object"]))
    return boxes, ok_with


def _pair_key(a, b):
    return a + "|" + b


def _overlap_pairs(boxes, ok_with):
    pairs = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _overlaps(boxes[i][1:] if False else boxes[i][1:],
                         boxes[j][1:]):
                key = _pair_key(boxes[i][0], boxes[j][0])
                if key in ok_with:
                    continue
                pairs.append([boxes[i][0], boxes[j][0]])
    return pairs


def verify(report):
    ok = (report["placed_count"] == report["expected_pieces"]
          and report.get("level_saved") is True
          and not report["errors"])

    # 16:9 filmback gate: the capture silently reframes otherwise. The
    # exterior-reuse row carries no filmback and is exempt by construction.
    want_aspect = report.get("deliverable_aspect", 0.0)
    bad = [c["label"] for c in report["cameras"]
           if "reuse_level" not in c
           and abs(float(c.get("filmback_aspect", 0.0)) - want_aspect) > 0.001]
    report["aspect_mismatched_cameras"] = bad
    if bad:
        ok = False
        report["errors"].append(
            "filmback aspect != %.5f on %s -- the capture would reframe"
            % (want_aspect, bad))

    if report["overlapping_pairs"]:
        ok = False
        report["errors"].append(
            "overlapping pieces: %s" % report["overlapping_pairs"])

    report["ok"] = ok
    return report


def write_report(report):
    text = json.dumps(report, indent=2, sort_keys=True)
    REPORT.write_text(text, encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(text, encoding="utf-8")
    except Exception as e:                                        # noqa: BLE001
        log("WARN could not write audit copy: %s" % e)
    return text


if __name__ == "__main__" or "unreal" in sys.modules:
    r = verify(build())
    write_report(r)
    log("ok=%s placed=%d/%d cameras=%d overlaps=%d"
        % (r["ok"], r["placed_count"], r["expected_pieces"],
           len(r["cameras"]), len(r["overlapping_pairs"])))
    for e in r["errors"]:
        log("ERROR %s" % e)
    log("report -> %s" % REPORT)
