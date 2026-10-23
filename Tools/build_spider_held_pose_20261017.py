"""Build and independently re-import a small Spider held-pose candidate."""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Saved/Exports/CastRigExport/Spider/Spider_Deform_v2.fbx"
OUT = ROOT / "Saved/OfflineIntake/20261017/clean_cast/Spider"
FPS = 24
FRAMES = (0, 1)
FOOT_TOLERANCE_M = 3e-7
GEOMETRY_CHANGE_MIN_M = 1e-7
REST_TOLERANCE = 1e-5
POSE_DEGREES = {"L": 3.2, "R": -1.8}
FANG_MESHES = {"wolfSpider_fang_L_geo": "L", "wolfSpider_fang_R_geo": "R"}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def vec(v):
    return [float(x) for x in v]


def matrix_rows(m):
    return [[float(x) for x in row] for row in m]


def reset_import(filepath, use_anim):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(filepath), use_anim=use_anim)
    bpy.context.view_layer.update()


def object_inventory():
    return (
        sorted((o for o in bpy.data.objects if o.type == "ARMATURE"), key=lambda o: o.name),
        sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name),
    )


def hierarchy(arm):
    return {b.name: b.parent.name if b.parent else None for b in arm.data.bones}


def rest_delta(a, b):
    if hierarchy(a) != hierarchy(b):
        raise RuntimeError("Skeleton hierarchy differs for " + a.name)
    if len(a.data.bones) != len(b.data.bones):
        raise RuntimeError("Skeleton bone count differs for " + a.name)
    largest = (0.0, None)
    for bone in a.data.bones:
        other = b.data.bones.get(bone.name)
        if other is None:
            raise RuntimeError("Missing rest bone %s on %s" % (bone.name, b.name))
        delta = max(abs(float(bone.matrix_local[r][c] - other.matrix_local[r][c])) for r in range(4) for c in range(4))
        if delta > largest[0]:
            largest = (delta, bone.name)
    return {"max_matrix_component_delta_armature_units": largest[0], "bone": largest[1]}


def rig_rest_snapshot(arms):
    return {
        arm.name: {
            "hierarchy": hierarchy(arm),
            "matrices": {bone.name: matrix_rows(bone.matrix_local) for bone in arm.data.bones},
        }
        for arm in arms
    }


def rest_delta_snapshot(source, exported, arm_name):
    if hierarchy(exported) != source["hierarchy"]:
        raise RuntimeError("Skeleton hierarchy differs for " + arm_name)
    if len(exported.data.bones) != len(source["matrices"]):
        raise RuntimeError("Skeleton bone count differs for " + arm_name)
    largest = (0.0, None)
    for bone in exported.data.bones:
        matrix = source["matrices"].get(bone.name)
        if matrix is None:
            raise RuntimeError("Missing source rest bone %s on %s" % (bone.name, arm_name))
        delta = max(abs(matrix[r][c] - float(bone.matrix_local[r][c])) for r in range(4) for c in range(4))
        if delta > largest[0]:
            largest = (delta, bone.name)
    return {"max_matrix_component_delta_armature_units": largest[0], "bone": largest[1]}


def mesh_vertices_world(mesh):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps)
    data = ev.to_mesh()
    try:
        return [ev.matrix_world @ v.co for v in data.vertices]
    finally:
        ev.to_mesh_clear()


def mesh_signature(mesh):
    return {
        "vertex_count": len(mesh.data.vertices),
        "polygon_count": len(mesh.data.polygons),
        "groups": sorted(g.name for g in mesh.vertex_groups),
        "armature_modifiers": sorted(m.object.name for m in mesh.modifiers if m.type == "ARMATURE" and m.object),
        "shape_keys": sorted(k.name for k in mesh.data.shape_keys.key_blocks) if mesh.data.shape_keys else [],
    }


def mean(points):
    if not points:
        raise RuntimeError("Cannot measure empty point set")
    return sum(points, Vector()) / len(points)


def max_displacement(a, b):
    if len(a) != len(b):
        raise RuntimeError("Evaluated mesh vertex count changed")
    return max(((x - y).length for x, y in zip(a, b)), default=0.0)


def all_tip_matrices(arms):
    result = {}
    for arm in arms:
        for bone in arm.pose.bones:
            n = bone.name.lower()
            if n.endswith("_tip") and ("lega_" in n or "legb_" in n or "legc_" in n or "legd_" in n or "smalllega_" in n):
                result[arm.name + "/" + bone.name] = matrix_rows(arm.matrix_world @ bone.matrix)
    return result


def matrix_metric_delta(a, b):
    if set(a) != set(b):
        raise RuntimeError("Contact-tip inventory changed")
    return max((abs(a[k][r][c] - b[k][r][c]) for k in a for r in range(4) for c in range(4)), default=0.0)


def armature_pose_snapshot(arms):
    return {
        arm.name: {
            "object_matrix_world": matrix_rows(arm.matrix_world),
            "bones": {b.name: matrix_rows(arm.matrix_world @ b.matrix) for b in arm.pose.bones},
        }
        for arm in arms
    }


def curve_map(action, owner):
    curves = []
    if hasattr(action, "fcurves"):
        curves = list(action.fcurves)
    else:
        slot = owner.animation_data.action_slot if owner.animation_data else None
        for layer in action.layers:
            for strip in layer.strips:
                bags = [strip.channelbag(slot)] if slot else list(strip.channelbags)
                for bag in bags:
                    if bag:
                        curves.extend(list(bag.fcurves))
    return curves


def set_pose_and_measure(main, meshes, arms):
    fang_details = {}
    mesh_by_name = {m.name: m for m in meshes}
    for mesh_name, side in FANG_MESHES.items():
        mesh = mesh_by_name.get(mesh_name)
        if mesh is None:
            raise RuntimeError("Missing deform fang mesh " + mesh_name)
        group_name = "wolfSpider_fangA_%s_c" % side
        group = next((g for g in mesh.vertex_groups if g.name == group_name), None)
        if group is None:
            raise RuntimeError("Fang mesh lacks expected weighted group " + group_name)
        weighted_ids = []
        for v in mesh.data.vertices:
            if any(item.group == group.index and item.weight > 0.01 for item in v.groups):
                weighted_ids.append(v.index)
        if not weighted_ids:
            raise RuntimeError("Fang influence has no weighted vertices: " + group_name)
        arm = next((a for a in arms if a.name == "wolfSpider_joints"), None)
        bone = arm.pose.bones.get(group_name) if arm else None
        if bone is None:
            raise RuntimeError("Missing measured fang pose bone " + group_name)
        before_vertices = mesh_vertices_world(mesh)
        points = [before_vertices[i] for i in weighted_ids]
        pivot = arm.matrix_world @ bone.head
        tip = arm.matrix_world @ bone.tail
        centroid_vector = mean(points) - pivot
        axis = centroid_vector.cross(tip - pivot)
        if axis.length < 1e-8:
            axis = (tip - pivot).cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-8:
            axis = (tip - pivot).cross(Vector((0.0, 1.0, 0.0)))
        if axis.length < 1e-8:
            raise RuntimeError("Could not derive stable rotation axis from measured fang geometry " + side)
        axis.normalize()
        angle = math.radians(POSE_DEGREES[side])
        world_delta = Quaternion(axis, angle)
        arm_q = arm.matrix_world.to_quaternion()
        local_delta = arm_q.inverted() @ world_delta @ arm_q
        pivot_arm = bone.head.copy()
        around_pivot = Matrix.Translation(pivot_arm) @ local_delta.to_matrix().to_4x4() @ Matrix.Translation(-pivot_arm)
        bone.matrix = around_pivot @ bone.matrix.copy()
        bpy.context.view_layer.update()
        after_vertices = mesh_vertices_world(mesh)
        moved = max_displacement(before_vertices, after_vertices)
        if moved <= GEOMETRY_CHANGE_MIN_M:
            raise RuntimeError("Measured fang geometry did not change for " + side)
        fang_details[side] = {
            "mesh": mesh.name,
            "bone": bone.name,
            "weighted_vertex_count": len(weighted_ids),
            "rotation_degrees": POSE_DEGREES[side],
            "rotation_axis_world_derived_from_fang_geometry": vec(axis),
            "pivot_world_m": vec(pivot),
            "bone_tail_world_m": vec(tip),
            "weighted_vertex_centroid_before_world_m": vec(mean(points)),
            "max_mesh_vertex_displacement_m": moved,
            "bone_matrix_after": matrix_rows(arm.matrix_world @ bone.matrix),
        }
    return fang_details


def add_two_key_actions(arms):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start, scene.frame_end = FRAMES
    actions = {}
    # The Spider deform source carries eleven distinct armatures. Feeding one
    # NLA take per armature to the FBX exporter can create a cross-product of
    # unrelated takes on re-import, so only the geometry-driving main rig gets
    # this held action. Follicle rigs remain present and static.
    main = next(a for a in arms if a.name == "wolfSpider_joints")
    for arm in (main,):
        arm.animation_data_create()
        action = bpy.data.actions.new(name=(arm.name + "_SpiderHeldPose_v01").replace(":", "_"))
        arm.animation_data.action = action
        actions[arm.name] = action
        bpy.context.view_layer.objects.active = arm
        for frame in FRAMES:
            scene.frame_set(frame)
            for bone in arm.pose.bones:
                bone.rotation_mode = "QUATERNION"
                bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
                bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
                bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)
    scene.frame_set(FRAMES[0])
    bpy.context.view_layer.update()
    return actions


def evaluate_imported(candidate, source):
    reset_import(source, False)
    source_arms, source_meshes = object_inventory()
    source_arms_by_name = {o.name: o for o in source_arms}
    source_mesh_by_name = {o.name: o for o in source_meshes}
    if len(source_arms) != 11 or len(source_meshes) != 11:
        raise RuntimeError("Clean source fresh import inventory mismatch")
    source_mesh_sig = {m.name: mesh_signature(m) for m in source_meshes}
    source_verts = {m.name: mesh_vertices_world(m) for m in source_meshes}
    source_tips = all_tip_matrices(source_arms)
    source_rest = rig_rest_snapshot(source_arms)

    reset_import(candidate, True)
    cand_arms, cand_meshes = object_inventory()
    if len(cand_arms) != 11 or len(cand_meshes) != 11:
        raise RuntimeError("Fresh candidate FBX inventory mismatch: %d arms / %d meshes" % (len(cand_arms), len(cand_meshes)))
    cand_arms_by_name = {o.name: o for o in cand_arms}
    cand_mesh_by_name = {o.name: o for o in cand_meshes}
    if set(cand_arms_by_name) != set(source_arms_by_name) or set(cand_mesh_by_name) != set(source_mesh_by_name):
        raise RuntimeError("Fresh candidate object names differ from clean source")
    rest = {name: rest_delta_snapshot(source_rest[name], cand_arms_by_name[name], name) for name in source_arms_by_name}
    if any(item["max_matrix_component_delta_armature_units"] > REST_TOLERANCE for item in rest.values()):
        raise RuntimeError("Candidate rest matrices do not match clean source: %s" % rest)
    modifier_differences = {}
    for m in cand_meshes:
        actual = mesh_signature(m)
        expected = source_mesh_sig[m.name]
        for field in ("vertex_count", "polygon_count", "groups", "shape_keys"):
            if actual[field] != expected[field]:
                raise RuntimeError("Fresh candidate mesh %s differs in %s" % (m.name, field))
        if actual["armature_modifiers"] != expected["armature_modifiers"]:
            modifier_differences[m.name] = {
                "source": expected["armature_modifiers"],
                "candidate": actual["armature_modifiers"],
                "source_only": sorted(set(expected["armature_modifiers"]) - set(actual["armature_modifiers"])),
                "candidate_only": sorted(set(actual["armature_modifiers"]) - set(expected["armature_modifiers"])),
            }
    main = cand_arms_by_name["wolfSpider_joints"]
    if main.animation_data is None or main.animation_data.action is None:
        # FBX NLA import commonly promotes the selected take to the active action.
        actions = [a for a in bpy.data.actions if "SpiderHeldPose" in a.name]
        if not actions:
            raise RuntimeError("Fresh FBX has no imported held-pose action")
        main.animation_data_create()
        main.animation_data.action = actions[0]
    action = main.animation_data.action
    frame_range = [float(action.frame_range[0]), float(action.frame_range[1])]
    expected_frames = [float(FRAMES[0] + 1), float(FRAMES[1] + 1)]
    if frame_range != expected_frames:
        raise RuntimeError("Fresh action range %s differs from expected %s" % (frame_range, expected_frames))
    curves = curve_map(action, main)
    channel_map = {}
    for curve in curves:
        channel_map.setdefault((curve.data_path, curve.array_index), curve)
    for bone in main.data.bones:
        for path, width in (("location", 3), ("rotation_quaternion", 4), ("scale", 3)):
            data_path = 'pose.bones["%s"].%s' % (bone.name, path)
            for i in range(width):
                curve = channel_map.get((data_path, i))
                if curve is None:
                    raise RuntimeError("Missing imported channel %s[%d]" % (data_path, i))
                keys = list(curve.keyframe_points)
                if len(keys) != 2 or [float(k.co.x) for k in keys] != expected_frames:
                    raise RuntimeError("Imported channel lacks exact two held keys: %s[%d]" % (data_path, i))
                if abs(float(keys[0].co.y - keys[1].co.y)) > 1e-6:
                    raise RuntimeError("Imported channel changes between held keys: %s[%d]" % (data_path, i))
    frame_results = {}
    for frame in expected_frames:
        bpy.context.scene.frame_set(int(frame))
        bpy.context.view_layer.update()
        positions = {m.name: mesh_vertices_world(m) for m in cand_meshes}
        mesh_delta = {name: max_displacement(source_verts[name], positions[name]) for name in source_verts}
        tip_after = all_tip_matrices(cand_arms)
        tip_delta = matrix_metric_delta(source_tips, tip_after)
        frame_results[str(int(frame))] = {
            "max_vertex_displacement_from_clean_source_m_by_mesh": mesh_delta,
            "all_contact_tip_matrix_max_component_delta": tip_delta,
            "contact_tip_gate_tolerance": FOOT_TOLERANCE_M,
        }
        if tip_delta > FOOT_TOLERANCE_M:
            raise RuntimeError("Fresh FBX changed contact tip matrices by %.9g" % tip_delta)
        if max(mesh_delta.get(k, 0.0) for k in FANG_MESHES) <= GEOMETRY_CHANGE_MIN_M:
            raise RuntimeError("Fresh FBX does not produce a measurable fang geometry change")
    if frame_results[str(int(expected_frames[0]))] != frame_results[str(int(expected_frames[1]))]:
        raise RuntimeError("Fresh FBX held frames do not evaluate identically")
    return {
        "status": "passed_fresh_independent_blender_fbx_reimport",
        "armature_count": len(cand_arms),
        "mesh_count": len(cand_meshes),
        "rest_matrix_deltas": rest,
        "imported_action_name": action.name,
        "imported_action_frame_range": frame_range,
        "main_rig_bone_count": len(main.data.bones),
        "main_rig_location_rotation_scale_channel_count": len(channel_map),
        "armature_modifier_readback_differences": modifier_differences,
        "frames": frame_results,
    }


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(str(SOURCE))
    OUT.mkdir(parents=True, exist_ok=True)
    blend = OUT / "Spider_HeldPose_Candidate_v06.blend"
    fbx = OUT / "Spider_HeldPose_v06_24fps.fbx"
    report_path = OUT / "held_pose_v06_report.json"
    for path in (blend, fbx, report_path):
        if path.exists():
            raise FileExistsError("Preserving existing candidate artifact: " + str(path))

    reset_import(SOURCE, False)
    arms, meshes = object_inventory()
    if len(arms) != 11 or len(meshes) != 11:
        raise RuntimeError("Source import inventory mismatch: %d arms / %d meshes" % (len(arms), len(meshes)))
    if not any(a.name == "wolfSpider_joints" and len(a.data.bones) == 69 for a in arms):
        raise RuntimeError("Verified main 69-bone Spider deform skeleton was not imported")
    signatures = {m.name: mesh_signature(m) for m in meshes}
    armature_inventory = {a.name: len(a.data.bones) for a in arms}
    if any(name not in signatures for name in FANG_MESHES):
        raise RuntimeError("Expected dedicated fang meshes are missing")
    if any(signatures[name]["vertex_count"] != 33 for name in FANG_MESHES):
        raise RuntimeError("Fang mesh vertex inventory differs from prior deform readback")
    before_snapshot = armature_pose_snapshot(arms)
    tips_before = all_tip_matrices(arms)
    mesh_before = {m.name: mesh_vertices_world(m) for m in meshes}
    details = set_pose_and_measure(arms[0] if arms[0].name == "wolfSpider_joints" else next(a for a in arms if a.name == "wolfSpider_joints"), meshes, arms)
    tips_after = all_tip_matrices(arms)
    tip_delta = matrix_metric_delta(tips_before, tips_after)
    if tip_delta > FOOT_TOLERANCE_M:
        raise RuntimeError("Authoring changed contact tip matrices by %.9g" % tip_delta)
    post_snapshot = armature_pose_snapshot(arms)
    # Non-main armatures must be exactly static; main-rig change is limited to fang joints.
    changed_bones = []
    for arm_name, state in before_snapshot.items():
        for bone_name, matrix in state["bones"].items():
            other = post_snapshot[arm_name]["bones"][bone_name]
            delta = max(abs(matrix[r][c] - other[r][c]) for r in range(4) for c in range(4))
            if delta > 1e-8:
                changed_bones.append((arm_name, bone_name, delta))
    allowed = {"wolfSpider_fangA_L_c", "wolfSpider_fangA_R_c"}
    if any(arm != "wolfSpider_joints" or bone not in allowed for arm, bone, _ in changed_bones):
        raise RuntimeError("Pose changed non-fang or follicle skeleton transforms: %s" % changed_bones)
    geom_changes = {}
    for mesh in meshes:
        after = mesh_vertices_world(mesh)
        geom_changes[mesh.name] = max_displacement(mesh_before[mesh.name], after)
    actions = add_two_key_actions(arms)
    # Assert complete key coverage on every skeleton, including all follicle ancestors.
    key_counts = {}
    for arm in (next(a for a in arms if a.name == "wolfSpider_joints"),):
        action = actions[arm.name]
        expected_curve_count = len(arm.pose.bones) * 10
        curves = curve_map(action, arm)
        if len(curves) != expected_curve_count:
            raise RuntimeError("%s has %d curves, expected %d" % (arm.name, len(curves), expected_curve_count))
        for curve in curves:
            keys = list(curve.keyframe_points)
            if len(keys) != 2 or [float(k.co.x) for k in keys] != list(map(float, FRAMES)) or abs(float(keys[0].co.y - keys[1].co.y)) > 1e-7:
                raise RuntimeError("Non-held or incomplete channel in " + arm.name)
        key_counts[arm.name] = {"bones": len(arm.pose.bones), "channels": len(curves), "keys_per_channel": 2}

    scene = bpy.context.scene
    scene.frame_set(FRAMES[0])
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in arms + meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(a for a in arms if a.name == "wolfSpider_joints")
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, object_types={"ARMATURE", "MESH"},
        bake_anim=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
        add_leaf_bones=False, use_armature_deform_only=False,
        axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
    )
    verification = evaluate_imported(fbx, SOURCE)
    report = {
        "status": "offline_spider_held_pose_candidate_built_and_fresh_reimport_verified_pending_visual_review_and_ue_import",
        "source_fbx": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "candidate_blend": str(blend),
        "candidate_fbx": str(fbx),
        "report": str(report_path),
        "blender_version": bpy.app.version_string,
        "frame_rate": FPS,
        "frames": list(FRAMES),
        "armature_count": len(arms),
        "mesh_count": len(meshes),
        "armatures": armature_inventory,
        "meshes": signatures,
        "full_source_skeleton_hierarchies_exported": True,
        "includes_non_deform_ancestor_and_follicle_bones": True,
        "armature_pose_key_inventory": key_counts,
        "pose": {
            "method": "measured world rotation about each fang joint head; axis derived from that fang's weighted geometry centroid and measured bone vector",
            "fangs": details,
            "changed_pose_bones": [{"armature": a, "bone": b, "max_matrix_component_delta": d} for a, b, d in changed_bones],
            "contact_tip_matrix_max_component_delta": tip_delta,
            "contact_tip_matrix_limit": FOOT_TOLERANCE_M,
            "geometry_max_displacement_from_bind_m_by_mesh": geom_changes,
        },
        "fresh_independent_reimport": verification,
        "limitations": [
            "Offline Blender FBX verification only; no UE import or animation evaluation was performed.",
            "Visual silhouette review remains required before use.",
            "The Spider source contains eleven armatures and eleven mesh parts, so this full deform-set FBX is intended for animation-only import against the already imported compatible skeleton after a separate UE compatibility check.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
