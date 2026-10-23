"""Build offline relaxed standing held-pose animation candidates for David and Sam."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "Saved/OfflineIntake/20261017/clean_cast"
FPS = 24
FRAME_START = 0
FRAME_END = 1
FOOT_TOLERANCE_M = 0.002
MIN_WRIST_DROP_M = 0.12
MAX_HAND_TORSO_GAP_M = 0.30
MIN_HAND_TORSO_CLEARANCE_M = 0.005
MIN_ELBOW_FLEX_DEG = 4.0
MAX_ELBOW_FLEX_DEG = 22.0
MIN_ELBOW_ASYMMETRY_DEG = 1.5
MIN_HEAD_ATTITUDE_DEG = 1.0
MAX_HEAD_ATTITUDE_DEG = 8.0
MAX_HAND_HIP_VERTICAL_DELTA_M = 0.14
REST_MATRIX_TOLERANCE = 0.001

# Per-character differences are modest and expressed as measurable world-space
# targets. No local bone axis is assumed; rotations are solved from imported
# bone matrices and measured limb vectors.
POSE_STYLE = {
    "David": {
        "wrist_lateral_m": {"L": 0.137, "R": 0.145},
        "elbow_flex_deg": {"L": -7.0, "R": -10.0},
        "head_tilt_deg": 2.8,
        "head_nod_deg": -1.5,
    },
    "Sam": {
        "wrist_lateral_m": {"L": 0.145, "R": 0.134},
        "elbow_flex_deg": {"L": -11.0, "R": -6.0},
        "head_tilt_deg": -2.4,
        "head_nod_deg": 2.0,
    },
}


def vec(value):
    return [float(x) for x in value]


def suffix_map(arm):
    out = {}
    for bone in arm.pose.bones:
        key = bone.name.rsplit(":", 1)[-1]
        if key in out:
            raise RuntimeError("Duplicate bone suffix: " + key)
        out[key] = bone
    return out


def world_head(arm, bone):
    bpy.context.view_layer.update()
    return arm.matrix_world @ bone.head


def world_tail(arm, bone):
    bpy.context.view_layer.update()
    return arm.matrix_world @ bone.tail


def world_bone_matrix(arm, bone):
    bpy.context.view_layer.update()
    return arm.matrix_world @ bone.matrix


def elbow_flex_degrees(shoulder, elbow, wrist):
    proximal = (shoulder - elbow).normalized()
    distal = (wrist - elbow).normalized()
    cosine = max(-1.0, min(1.0, float(proximal.dot(distal))))
    return 180.0 - math.degrees(math.acos(cosine))


def rotate_bone_about_world_pivot(arm, bone, world_delta):
    """Apply a world-space rotation to this bone and its descendants."""
    bpy.context.view_layer.update()
    pivot_arm = bone.head.copy()
    arm_rotation = arm.matrix_world.to_quaternion()
    local_delta = arm_rotation.inverted() @ world_delta @ arm_rotation
    rotation_matrix = local_delta.to_matrix().to_4x4()
    around_pivot = Matrix.Translation(pivot_arm) @ rotation_matrix @ Matrix.Translation(-pivot_arm)
    bone.matrix = around_pivot @ bone.matrix.copy()
    bpy.context.view_layer.update()


def mesh_world_vertices(mesh):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(deps)
    data = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in data.vertices]
    finally:
        evaluated.to_mesh_clear()


def vertices_for_groups(mesh, group_names):
    group_indices = {group.index for group in mesh.vertex_groups if group.name in group_names}
    if not group_indices:
        raise RuntimeError("No mesh vertex groups found for: " + ", ".join(sorted(group_names)))
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(deps)
    data = evaluated.to_mesh()
    try:
        result = []
        for vertex in data.vertices:
            if any(item.group in group_indices and item.weight >= 0.10 for item in vertex.groups):
                result.append(evaluated.matrix_world @ vertex.co)
        if not result:
            raise RuntimeError("No weighted vertices found for: " + ", ".join(sorted(group_names)))
        return result
    finally:
        evaluated.to_mesh_clear()


def bounds(points):
    return {
        "min": [float(min(point[i] for point in points)) for i in range(3)],
        "max": [float(max(point[i] for point in points)) for i in range(3)],
    }


def xyz_bounds_delta(before, after):
    return {
        axis: {
            "min": float(after["min"][index] - before["min"][index]),
            "max": float(after["max"][index] - before["max"][index]),
        }
        for index, axis in enumerate(("x", "y", "z"))
    }


def max_bounds_component_delta(delta):
    return max(abs(value) for axis in delta.values() for value in axis.values())


def group_names_by_predicate(mesh, predicate):
    return {group.name for group in mesh.vertex_groups if predicate(group.name.rsplit(":", 1)[-1].lower())}


def hand_torso_metrics(mesh, character, side, wrist):
    hand_names = group_names_by_predicate(
        mesh,
        lambda name: name.endswith("_" + side.lower())
        and ("finger" in name or "wrist" in name),
    )
    torso_names = group_names_by_predicate(
        mesh,
        lambda name: any(token in name for token in ("spine", "chest", "root_m", "rootpart", "hip_")),
    )
    hand_points = vertices_for_groups(mesh, hand_names)
    torso_points = vertices_for_groups(mesh, torso_names)
    hand_box = bounds(hand_points)
    torso_box = bounds(torso_points)
    sign = 1.0 if side == "L" else -1.0
    torso_outer_x = torso_box["max"][0] if sign > 0 else torso_box["min"][0]
    hand_inner_x = hand_box["min"][0] if sign > 0 else hand_box["max"][0]
    clearance = sign * (hand_inner_x - torso_outer_x)
    center = [sum(point[i] for point in hand_points) / len(hand_points) for i in range(3)]
    shoulder_to_wrist = (wrist - Vector(center)).length
    if clearance < MIN_HAND_TORSO_CLEARANCE_M:
        raise RuntimeError(
            "%s %s hand is inside or too close to torso envelope: %.4f m"
            % (character, side, clearance)
        )
    if shoulder_to_wrist > MAX_HAND_TORSO_GAP_M:
        raise RuntimeError("%s %s hand envelope is unexpectedly detached from wrist" % (character, side))
    return {
        "hand_weight_groups": sorted(hand_names),
        "torso_weight_groups": sorted(torso_names),
        "hand_world_bounds_m": hand_box,
        "torso_world_bounds_m": torso_box,
        "hand_center_world_m": vec(center),
        "wrist_to_hand_center_m": float(shoulder_to_wrist),
        "lateral_hand_to_torso_clearance_m": float(clearance),
        "limits": {
            "minimum_lateral_clearance_m": MIN_HAND_TORSO_CLEARANCE_M,
            "maximum_wrist_to_hand_center_m": MAX_HAND_TORSO_GAP_M,
        },
    }


def hierarchy_signature(arm):
    return {
        bone.name: (bone.parent.name if bone.parent else None)
        for bone in arm.data.bones
    }


def rest_matrix_delta(source_arm, exported_arm):
    largest = 0.0
    largest_bone = None
    for name, source_bone in source_arm.data.bones.items():
        exported_bone = exported_arm.data.bones.get(name)
        if exported_bone is None:
            raise RuntimeError("Export is missing rest bone " + name)
        delta = max(
            abs(float(source_bone.matrix_local[row][column] - exported_bone.matrix_local[row][column]))
            for row in range(4)
            for column in range(4)
        )
        if delta > largest:
            largest = delta
            largest_bone = name
    return {"max_matrix_component_delta_armature_units": largest, "largest_delta_bone": largest_bone}


def find_scene_rig_and_mesh():
    arms = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if len(arms) != 1 or len(meshes) != 1:
        raise RuntimeError("Expected exactly one armature and one mesh; got %d and %d" % (len(arms), len(meshes)))
    arm, mesh = arms[0], meshes[0]
    if mesh.find_armature() is not arm:
        raise RuntimeError("Mesh is not bound to the imported armature")
    return arm, mesh


def set_held_pose(arm, mesh, character):
    bones = suffix_map(arm)
    style = POSE_STYLE[character]
    before = {}
    for side in ("L", "R"):
        shoulder = bones["Shoulder_" + side]
        elbow = bones["Elbow_" + side]
        wrist = bones["Wrist_" + side]
        shoulder_head = world_head(arm, shoulder)
        wrist_head = world_head(arm, wrist)
        vector = wrist_head - shoulder_head
        before[side] = {
            "shoulder": shoulder_head.copy(),
            "elbow": world_head(arm, elbow).copy(),
            "wrist": wrist_head.copy(),
            "shoulder_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, shoulder)],
            "elbow_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, elbow)],
            "wrist_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, wrist)],
            "limb_vector": vector.copy(),
        }
        side_sign = 1.0 if shoulder_head.x >= 0 else -1.0
        lateral = style["wrist_lateral_m"][side]
        target_x = side_sign * lateral
        target_y = float(vector.y)
        length = vector.length
        vertical_sq = length * length - target_x * target_x - target_y * target_y
        if vertical_sq <= 0:
            raise RuntimeError("Wrist target exceeds measured arm reach for %s %s" % (character, side))
        target = Vector((target_x, target_y, -math.sqrt(vertical_sq)))
        q_world = vector.normalized().rotation_difference(target.normalized())
        rotate_bone_about_world_pivot(arm, shoulder, q_world)

        # Apply a small, asymmetric elbow flex in a measured world-space plane.
        elbow_world = world_head(arm, elbow)
        flex = math.radians(style["elbow_flex_deg"][side])
        q_elbow = Quaternion(Vector((1.0, 0.0, 0.0)), flex)
        rotate_bone_about_world_pivot(arm, elbow, q_elbow)

    head = bones["Head_M"]
    head_world = world_head(arm, head)
    head_matrix_before = world_bone_matrix(arm, head)
    head_rotation_before = head_matrix_before.to_3x3().to_quaternion()
    tilt = Quaternion(Vector((0.0, 1.0, 0.0)), math.radians(style["head_tilt_deg"]))
    nod = Quaternion(Vector((1.0, 0.0, 0.0)), math.radians(style["head_nod_deg"]))
    rotate_bone_about_world_pivot(arm, head, tilt @ nod)
    bpy.context.view_layer.update()
    head_rotation_after = world_bone_matrix(arm, head).to_3x3().to_quaternion()
    head_angle_delta = (head_rotation_before.inverted() @ head_rotation_after).angle

    measurements = {}
    for side in ("L", "R"):
        shoulder = bones["Shoulder_" + side]
        elbow = bones["Elbow_" + side]
        wrist_bone = bones["Wrist_" + side]
        shoulder_after = world_head(arm, shoulder)
        elbow_after = world_head(arm, elbow)
        wrist_after = world_head(arm, wrist_bone)
        drop = float(shoulder_after.z - wrist_after.z)
        if drop < MIN_WRIST_DROP_M:
            raise RuntimeError("%s %s wrist drop %.4f m is below %.4f m" % (character, side, drop, MIN_WRIST_DROP_M))
        if abs(wrist_after.x) > 0.32:
            raise RuntimeError("%s %s wrist is too far outside the body envelope" % (character, side))
        measurements[side] = {
            "shoulder_world_m": vec(shoulder_after),
            "elbow_world_m": vec(elbow_after),
            "wrist_world_m": vec(wrist_after),
            "shoulder_to_wrist_world_m": vec(wrist_after - shoulder_after),
            "shoulder_to_wrist_length_m": float((wrist_after - shoulder_after).length),
            "wrist_drop_from_shoulder_m": drop,
            "elbow_flex_from_straight_degrees": elbow_flex_degrees(shoulder_after, elbow_after, wrist_after),
            "required_minimum_drop_m": MIN_WRIST_DROP_M,
            "shoulder_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, shoulder)],
            "elbow_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, elbow)],
            "wrist_matrix_world": [[float(x) for x in row] for row in world_bone_matrix(arm, wrist_bone)],
        }
        measurements[side]["hand_torso"] = hand_torso_metrics(mesh, character, side, wrist_after)
        hip_center = (
            world_head(arm, bones["Hip_L"]) + world_head(arm, bones["Hip_R"])
        ) * 0.5
        hand_center = Vector(measurements[side]["hand_torso"]["hand_center_world_m"])
        hand_hip_delta = float(hand_center.z - hip_center.z)
        if abs(hand_hip_delta) > MAX_HAND_HIP_VERTICAL_DELTA_M:
            raise RuntimeError("%s %s hand is not near hip height: delta %.4f m" % (character, side, hand_hip_delta))
        measurements[side]["hand_torso"]["hip_center_world_m"] = vec(hip_center)
        measurements[side]["hand_torso"]["hand_to_hip_vertical_delta_m"] = hand_hip_delta
        measurements[side]["hand_torso"]["maximum_hand_to_hip_vertical_delta_m"] = MAX_HAND_HIP_VERTICAL_DELTA_M
    flex_left = measurements["L"]["elbow_flex_from_straight_degrees"]
    flex_right = measurements["R"]["elbow_flex_from_straight_degrees"]
    if not (MIN_ELBOW_FLEX_DEG <= flex_left <= MAX_ELBOW_FLEX_DEG):
        raise RuntimeError("%s left elbow flex is outside the relaxed range: %.2f degrees" % (character, flex_left))
    if not (MIN_ELBOW_FLEX_DEG <= flex_right <= MAX_ELBOW_FLEX_DEG):
        raise RuntimeError("%s right elbow flex is outside the relaxed range: %.2f degrees" % (character, flex_right))
    if abs(flex_left - flex_right) < MIN_ELBOW_ASYMMETRY_DEG:
        raise RuntimeError("%s elbows do not meet the minimum measured asymmetry" % character)
    if not (MIN_HEAD_ATTITUDE_DEG <= math.degrees(head_angle_delta) <= MAX_HEAD_ATTITUDE_DEG):
        raise RuntimeError("%s head attitude is outside the subtle-angle range" % character)
    measurements["head_attitude"] = {
        "head_world_position_m": vec(world_head(arm, head)),
        "head_world_matrix_before": [[float(x) for x in row] for row in head_matrix_before],
        "head_world_matrix_after": [[float(x) for x in row] for row in world_bone_matrix(arm, head)],
        "orientation_delta_degrees": float(math.degrees(head_angle_delta)),
        "requested_tilt_degrees": style["head_tilt_deg"],
        "requested_nod_degrees": style["head_nod_deg"],
    }
    return before, measurements


def insert_two_identical_frames(arm):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    bpy.context.view_layer.objects.active = arm
    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions.new(name="%s_HeldPose_v02" % arm.name.replace(":", "_"))
    for frame in (FRAME_START, FRAME_END):
        scene.frame_set(frame)
        for pose_bone in arm.pose.bones:
            pose_bone.rotation_mode = "QUATERNION"
            pose_bone.keyframe_insert(data_path="location", frame=frame, group=pose_bone.name)
            pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=pose_bone.name)
            pose_bone.keyframe_insert(data_path="scale", frame=frame, group=pose_bone.name)
    scene.frame_set(FRAME_START)


def action_fcurves(action, owner=None):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    curves = []
    slot = owner.animation_data.action_slot if owner and owner.animation_data else None
    for layer in action.layers:
        for strip in layer.strips:
            bags = [strip.channelbag(slot)] if slot else list(strip.channelbags)
            for bag in bags:
                if bag:
                    curves.extend(list(bag.fcurves))
    return curves


def exported_curve_inventory(action, owner=None):
    inventory = {}
    for curve in action_fcurves(action, owner):
        path = curve.data_path
        if path.startswith('pose.bones['):
            inventory.setdefault(path, {})[str(curve.array_index)] = [
                {
                    "frame": float(point.co.x),
                    "value": float(point.co.y),
                }
                for point in curve.keyframe_points
            ]
    return inventory


def import_clean_and_pose_for_verification(character, clean_fbx, pose_fbx):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(clean_fbx), use_anim=False)
    clean_arm, clean_mesh = find_scene_rig_and_mesh()
    source_hierarchy = hierarchy_signature(clean_arm)
    bpy.ops.import_scene.fbx(filepath=str(pose_fbx), use_anim=True)
    imported_arms = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    pose_arm = next(obj for obj in imported_arms if obj != clean_arm)
    pose_actions = [action for action in bpy.data.actions if action.name in {pose_arm.animation_data.action.name if pose_arm.animation_data and pose_arm.animation_data.action else ""}]
    if not pose_actions:
        pose_actions = [action for action in bpy.data.actions if "HeldPose" in action.name]
    if len(pose_actions) != 1:
        raise RuntimeError("Expected one imported held-pose action; found %d" % len(pose_actions))
    action = pose_actions[0]
    if hierarchy_signature(pose_arm) != source_hierarchy:
        raise RuntimeError("Exported pose hierarchy differs from the clean source")
    if len(pose_arm.data.bones) != len(clean_arm.data.bones):
        raise RuntimeError("Exported pose skeleton has a different bone count")
    rest_delta = rest_matrix_delta(clean_arm, pose_arm)
    if rest_delta["max_matrix_component_delta_armature_units"] > REST_MATRIX_TOLERANCE:
        raise RuntimeError("Exported skeleton rest matrices differ from clean source: %s" % rest_delta)
    pose_meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj != clean_mesh]
    if len(pose_meshes) != 1:
        raise RuntimeError("Expected exactly one exported mesh on fresh FBX re-import; got %d" % len(pose_meshes))
    pose_mesh = pose_meshes[0]
    if pose_mesh.find_armature() is not pose_arm:
        raise RuntimeError("Freshly re-imported mesh is not bound to the exported armature")
    clean_foot_groups = group_names_by_predicate(clean_mesh, lambda name: "ankle_" in name or "toes_" in name)
    clean_foot_bounds = bounds(vertices_for_groups(clean_mesh, clean_foot_groups))
    if len(pose_arm.data.bones) != len(clean_arm.data.bones):
        raise RuntimeError("Full exported hierarchy, including ancestors, did not survive re-import")
    clean_arm.animation_data_create()
    clean_arm.animation_data.action = action
    clean_arm.animation_data.action_slot = pose_arm.animation_data.action_slot
    imported_curves = action_fcurves(action, pose_arm)
    imported_curve_map = {}
    for curve in imported_curves:
        imported_curve_map.setdefault(curve.data_path, {})[curve.array_index] = curve
    imported_bone_curve_count = 0
    for bone_name in source_hierarchy:
        for channel, width in (("location", 3), ("rotation_quaternion", 4), ("scale", 3)):
            path = 'pose.bones["%s"].%s' % (bone_name, channel)
            curves = imported_curve_map.get(path, {})
            if len(curves) != width:
                raise RuntimeError("FBX re-import lacks %s channels for %s" % (channel, bone_name))
            for index in range(width):
                curve = curves[index]
                keys = list(curve.keyframe_points)
                if len(keys) != 2 or [float(key.co.x) for key in keys] != [float(FRAME_START + 1), float(FRAME_END + 1)]:
                    raise RuntimeError("FBX bone channel %s[%d] does not have the two expected keys" % (path, index))
                if abs(float(keys[0].co.y - keys[1].co.y)) > 1e-6:
                    raise RuntimeError("FBX bone channel %s[%d] is not a held value" % (path, index))
                imported_bone_curve_count += 1
    object_curve_values = {}
    for path in ("location", "rotation_euler", "rotation_quaternion", "scale"):
        for index, curve in imported_curve_map.get(path, {}).items():
            keys = list(curve.keyframe_points)
            if len(keys) != 2 or abs(float(keys[0].co.y - keys[1].co.y)) > 1e-6:
                raise RuntimeError("Armature object %s[%d] changes across the held clip" % (path, index))
            object_curve_values["%s[%d]" % (path, index)] = [float(keys[0].co.y), float(keys[1].co.y)]
    root_location_path = 'pose.bones["FilmExport:FilmRoot"].location'
    root_location_curves = imported_curve_map.get(root_location_path, {})
    if len(root_location_curves) != 3 or any(
        max(abs(float(key.co.y)) for key in curve.keyframe_points) > 1e-5
        for curve in root_location_curves.values()
    ):
        raise RuntimeError("FBX animation contains root translation")
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    result = {
        "action_name": action.name,
        "bone_count": len(clean_arm.data.bones),
        "rest_matrix_delta": rest_delta,
        "fresh_fbx_mesh_count": len(pose_meshes),
        "fresh_fbx_mesh_vertices": len(pose_mesh.data.vertices),
        "fresh_fbx_mesh_material_slots": len(pose_mesh.material_slots),
        "fresh_fbx_mesh_morphs": sorted(key.name for key in pose_mesh.data.shape_keys.key_blocks) if pose_mesh.data.shape_keys else [],
        "fresh_fbx_mesh_is_skinned_to_exported_rig": True,
        "fresh_fbx_bone_curve_count": imported_bone_curve_count,
        "fresh_fbx_required_bone_curves": len(source_hierarchy) * 10,
        "fresh_fbx_channels_per_bone": ["location[3]", "rotation_quaternion[4]", "scale[3]"],
        "fresh_fbx_armature_object_transform_keys_constant": object_curve_values,
        "fresh_fbx_root_bone_translation_keys": [
            [float(key.co.x), float(key.co.y)]
            for key in root_location_curves[0].keyframe_points
        ],
        "clean_source_foot_envelope_m": clean_foot_bounds,
        "frames": {},
    }
    imported_frames = (FRAME_START + 1, FRAME_END + 1)
    for frame in imported_frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        bone_map = suffix_map(clean_arm)
        wrists = {}
        for side in ("L", "R"):
            shoulder = world_head(clean_arm, bone_map["Shoulder_" + side])
            wrist = world_head(clean_arm, bone_map["Wrist_" + side])
            wrists[side] = {
                "shoulder_world_m": vec(shoulder),
                "wrist_world_m": vec(wrist),
                "wrist_drop_from_shoulder_m": float(shoulder.z - wrist.z),
            }
        feet_points = vertices_for_groups(
            clean_mesh, clean_foot_groups,
        )
        foot_bounds = bounds(feet_points)
        foot_delta = xyz_bounds_delta(clean_foot_bounds, foot_bounds)
        if max_bounds_component_delta(foot_delta) > FOOT_TOLERANCE_M:
            raise RuntimeError("Fresh FBX foot envelope changed beyond tolerance: %s" % foot_delta)
        result["frames"][str(frame)] = {
            "wrists": wrists,
            "foot_world_bounds_m": foot_bounds,
            "foot_envelope_component_delta_m": foot_delta,
            "clean_mesh_vertices": len(clean_mesh.data.vertices),
            "action_frame_range": [float(action.frame_range[0]), float(action.frame_range[1])],
        }
    if result["frames"][str(imported_frames[0])] != result["frames"][str(imported_frames[1])]:
        raise RuntimeError("Freshly imported frames do not evaluate identically")
    # Blender's FBX importer offsets the exported zero-based clip by one frame.
    imported_range = (float(FRAME_START + 1), float(FRAME_END + 1))
    if tuple(action.frame_range) != imported_range:
        raise RuntimeError("Imported action frame range is %s" % (action.frame_range,))
    return result


def build(character):
    base = BASE_DIR / character
    clean_fbx = base / (character + "_CleanFilm_UE_v01.fbx")
    output_blend = base / (character + "_HeldPose_Candidate_v02.blend")
    output_fbx = base / (character + "_HeldPose_v02_24fps.fbx")
    report_path = base / "held_pose_v02_report.json"
    if not clean_fbx.is_file():
        raise FileNotFoundError(str(clean_fbx))
    for path in (output_blend, output_fbx, report_path):
        if path.exists():
            raise RuntimeError("Existing candidate artifact preserved: " + str(path))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(clean_fbx), use_anim=False)
    arm, mesh = find_scene_rig_and_mesh()
    expected_bones = 149 if character == "David" else 220
    if len(arm.data.bones) != expected_bones:
        raise RuntimeError("Expected %d clean bones, got %d" % (expected_bones, len(arm.data.bones)))
    clean_hierarchy = hierarchy_signature(arm)
    mesh_before = bounds(mesh_world_vertices(mesh))
    feet_groups = group_names_by_predicate(mesh, lambda name: "ankle_" in name or "toes_" in name)
    feet_before = bounds(vertices_for_groups(mesh, feet_groups))
    before, pose_metrics = set_held_pose(arm, mesh, character)
    mesh_after = bounds(mesh_world_vertices(mesh))
    feet_after = bounds(vertices_for_groups(mesh, feet_groups))
    foot_delta = xyz_bounds_delta(feet_before, feet_after)
    largest_foot_delta = max(abs(value) for axis in foot_delta.values() for value in axis.values())
    if largest_foot_delta > FOOT_TOLERANCE_M:
        raise RuntimeError("Foot envelope moved %.6f m, exceeding %.6f m" % (largest_foot_delta, FOOT_TOLERANCE_M))

    insert_two_identical_frames(arm)
    action = arm.animation_data.action
    fcurves = action_fcurves(action, arm)
    if len(fcurves) != len(arm.pose.bones) * 10:
        # 3 location + 4 quaternion + 3 scale curves per bone.
        raise RuntimeError("Expected 10 keyed curves per bone; got %d curves for %d bones" % (len(action.fcurves), len(arm.pose.bones)))
    curve_inventory = exported_curve_inventory(action, arm)
    if len(curve_inventory) != len(arm.pose.bones) * 3:
        raise RuntimeError("Animation action does not contain all location/quaternion/scale paths")
    for path_curves in curve_inventory.values():
        for keys in path_curves.values():
            if len(keys) != 2 or keys[0]["frame"] != FRAME_START or keys[1]["frame"] != FRAME_END:
                raise RuntimeError("A bone channel lacks exactly two keyed frames")
            if abs(keys[0]["value"] - keys[1]["value"]) > 1e-7:
                raise RuntimeError("Held-pose frame values differ")

    bpy.context.scene.frame_set(FRAME_START)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend), check_existing=False)
    animation_data = arm.animation_data
    slot = animation_data.action_slot
    track = animation_data.nla_tracks.new()
    track.name = action.name + "_Export"
    strip = track.strips.new(action.name, FRAME_START, action)
    strip.action_slot = slot
    animation_data.action = None
    bpy.context.scene.frame_set(FRAME_START)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=str(output_fbx),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        bake_anim=True,
        bake_anim_use_nla_strips=True,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
        add_leaf_bones=False,
        use_armature_deform_only=False,
        axis_forward="-Z",
        axis_up="Y",
        apply_scale_options="FBX_SCALE_UNITS",
    )

    armature_name = arm.name
    mesh_name = mesh.name
    bone_count = len(arm.data.bones)
    mesh_vertex_count = len(mesh.data.vertices)
    triangle_count = sum(len(poly.vertices) - 2 for poly in mesh.data.polygons)
    morph_names = sorted(key.name for key in mesh.data.shape_keys.key_blocks) if mesh.data.shape_keys else []
    hierarchy_hash = hashlib.sha256(json.dumps(clean_hierarchy, sort_keys=True).encode("utf-8")).hexdigest()
    verification = import_clean_and_pose_for_verification(character, clean_fbx, output_fbx)
    report = {
        "character": character,
        "status": "offline_held_pose_candidate_built_and_fresh_reimport_verified_pending_visual_review_and_ue_import",
        "source_fbx": str(clean_fbx),
        "source_sha256": hashlib.sha256(clean_fbx.read_bytes()).hexdigest(),
        "candidate_blend": str(output_blend),
        "candidate_fbx": str(output_fbx),
        "report": str(report_path),
        "tool": bpy.app.version_string,
        "frame_rate": FPS,
        "frames": [FRAME_START, FRAME_END],
        "armature": armature_name,
        "bone_count": bone_count,
        "hierarchy_sha256": hierarchy_hash,
        "mesh": mesh_name,
        "vertices": mesh_vertex_count,
        "triangles": triangle_count,
        "morphs": morph_names,
        "source_skeleton_hierarchy_included": True,
        "includes_non_deform_ancestor_bones": True,
        "fbx_export_contains_one_skinned_mesh": True,
        "rest_matrix_tolerance_armature_units": REST_MATRIX_TOLERANCE,
        "animation_channels": {
            "action_fcurves": len(fcurves),
            "bone_channel_paths": len(curve_inventory),
            "channels_per_bone": ["location[3]", "rotation_quaternion[4]", "scale[3]"],
            "identical_two_frame_keys": True,
            "armature_object_root_motion": False,
            "fresh_reimport_all_bone_location_quaternion_scale_channels": True,
        },
        "pose": {
            "measured_pre_pose_matrices_and_limb_vectors": {
                side: {
                    "shoulder_world_m": vec(values["shoulder"]),
                    "elbow_world_m": vec(values["elbow"]),
                    "wrist_world_m": vec(values["wrist"]),
                    "shoulder_to_wrist_world_m": vec(values["limb_vector"]),
                    "shoulder_matrix_world": values["shoulder_matrix_world"],
                    "elbow_matrix_world": values["elbow_matrix_world"],
                    "wrist_matrix_world": values["wrist_matrix_world"],
                }
                for side, values in before.items()
            },
            "measured_post_pose": pose_metrics,
        },
        "mesh_world_bounds_before_m": mesh_before,
        "mesh_world_bounds_after_m": mesh_after,
        "foot_weighted_vertex_groups": sorted(feet_groups),
        "foot_envelope_before_m": feet_before,
        "foot_envelope_after_m": feet_after,
        "foot_envelope_component_delta_m": foot_delta,
        "foot_envelope_max_component_delta_m": largest_foot_delta,
        "foot_envelope_limit_m": FOOT_TOLERANCE_M,
        "foot_envelope_gate": "passed",
        "fresh_independent_reimport": verification,
        "limits": {
            "minimum_wrist_drop_from_shoulder_m": MIN_WRIST_DROP_M,
            "minimum_hand_to_torso_lateral_clearance_m": MIN_HAND_TORSO_CLEARANCE_M,
            "maximum_wrist_to_hand_center_m": MAX_HAND_TORSO_GAP_M,
            "hand_to_hip_vertical_delta_max_m": MAX_HAND_HIP_VERTICAL_DELTA_M,
            "elbow_flex_range_degrees": [MIN_ELBOW_FLEX_DEG, MAX_ELBOW_FLEX_DEG],
            "minimum_left_right_elbow_asymmetry_degrees": MIN_ELBOW_ASYMMETRY_DEG,
            "head_attitude_range_degrees": [MIN_HEAD_ATTITUDE_DEG, MAX_HEAD_ATTITUDE_DEG],
        },
        "limitations": [
            "No UE animation asset was created or imported.",
            "No camera render or human visual review was performed; inspect the silhouette before production use.",
            "The torso and hand intersection gate uses weighted-vertex bounds and lateral clearance.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    arg = sys.argv[sys.argv.index("--") + 1]
    if arg not in POSE_STYLE:
        raise ValueError("Character must be David or Sam")
    build(arg)
