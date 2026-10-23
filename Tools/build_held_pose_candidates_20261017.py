"""Create offline held-pose source candidates from verified consolidated FBXs."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]

POSES = {
    'David': {'Shoulder_L': (0.00, 0.00, 0.10), 'Elbow_L': (0.10, 0.00, 0.00),
              'Shoulder_R': (0.00, 0.00, -0.05), 'Elbow_R': (-0.04, 0.00, 0.00),
              'Head_M': (0.00, 0.035, -0.035)},
    'Sam': {'Shoulder_L': (0.00, 0.00, 0.04), 'Elbow_L': (0.04, 0.00, 0.00),
            'Shoulder_R': (0.00, 0.00, -0.10), 'Elbow_R': (-0.10, 0.00, 0.00),
            'Head_M': (0.00, -0.035, 0.035)},
}

def bounds(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    points = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    lo = [min(v[i] for v in points) for i in range(3)]
    hi = [max(v[i] for v in points) for i in range(3)]
    return lo, hi

def bone_suffix(arm, suffix):
    matches = [b for b in arm.pose.bones if b.name.rsplit(':', 1)[-1] == suffix]
    assert len(matches) == 1, 'Expected exactly one '+suffix
    return matches[0]

def main(character):
    base = ROOT / 'Saved/OfflineIntake/20261017/clean_cast' / character
    source = base / (character + '_CleanFilm_UE_v01.fbx')
    output = base / (character + '_HeldPose_Candidate_v01.blend')
    report_path = base / 'held_pose_candidate.json'
    if output.exists():
        raise RuntimeError('Existing pose candidate preserved: '+str(output))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
    low_before, high_before = bounds(mesh)
    rest = {}
    for name, delta in POSES[character].items():
        bone = bone_suffix(arm, name)
        bone.rotation_mode = 'XYZ'
        rest[name] = [0.0, 0.0, 0.0]
        bone.rotation_euler = tuple(delta)
    bpy.context.view_layer.update()
    low_after, high_after = bounds(mesh)
    # No leg or root channels are touched. Feet remain planted when the mesh's
    # bottom envelope stays within 2 mm of its imported rest envelope.
    bottom_delta = abs(low_after[2] - low_before[2])
    assert bottom_delta <= 0.002, 'Pose moved the floor contact envelope by more than 2 mm'
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True); mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    report = {
        'character': character,
        'status': 'offline_held_pose_source_candidate_saved_pending_visual_review_and_ue_pose_asset',
        'source_fbx': str(source),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'pose_blend': str(output),
        'armature': arm.name,
        'bones': len(arm.data.bones),
        'mesh': mesh.name,
        'triangles': sum(len(p.vertices)-2 for p in mesh.data.polygons),
        'pose_local_euler_radians': {k: list(v) for k, v in POSES[character].items()},
        'bounds_before_blender_units': {'min': low_before, 'max': high_before},
        'bounds_after_blender_units': {'min': low_after, 'max': high_after},
        'floor_envelope_delta_blender_units': bottom_delta,
        'foot_contact_gate': 'passed_envelope_only',
        'limitations': ['no UE PoseAsset created', 'silhouette and clipping need visual review',
                        'grounding measured by unchanged lowest-vertex envelope'],
    }
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--')+1])
