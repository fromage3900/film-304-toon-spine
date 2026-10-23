"""Fresh-process independent readback for consolidated David/Sam FBX candidates."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]

def main(character):
    base = ROOT / 'Saved/OfflineIntake/20261017/clean_cast' / character
    source = base / (character + '_CleanFilm_UE_v01.fbx')
    report_path = base / 'consolidated_readback.json'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(arms) == 1, 'Expected one armature, got '+str(len(arms))
    assert len(meshes) == 1, 'Expected one mesh, got '+str(len(meshes))
    arm, mesh = arms[0], meshes[0]
    assert mesh.data.shape_keys, 'No shape keys after fresh FBX import'
    keys = list(mesh.data.shape_keys.key_blocks.keys())
    for name in ['Blink_L', 'Blink_R']:
        assert name in keys, 'Missing '+name
        key = mesh.data.shape_keys.key_blocks[name]
        basis = mesh.data.shape_keys.key_blocks['Basis']
        delta = max((mesh.matrix_world.to_3x3() @ (a.co-b.co)).length
                    for a, b in zip(key.data, basis.data))
        assert delta > 0.00001, 'Empty '+name
    def bone_suffix(suffix):
        matches = [b for b in arm.data.bones if b.name.rsplit(':', 1)[-1] == suffix]
        assert len(matches) == 1, 'Expected one bone '+suffix
        return matches[0]
    follow = bone_suffix('FaceDeformationFollowHead')
    assert follow.parent and follow.parent.name.rsplit(':', 1)[-1] == 'Head_M', 'Face follow hierarchy lost'
    head = arm.pose.bones[bone_suffix('Head_M').name]
    eye = arm.pose.bones[bone_suffix('Eye_L').name]
    head.rotation_mode = 'XYZ'
    bpy.context.view_layer.update()
    eye_before = eye.matrix.translation.copy()
    head.rotation_euler.z += 0.15
    bpy.context.view_layer.update()
    eye_motion = (eye.matrix.translation-eye_before).length
    assert eye_motion > 0.00001, 'Head rotation did not move eye bone'
    head.rotation_euler.z -= 0.15
    bpy.context.view_layer.update()
    unweighted = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups) < 0.99]
    assert not unweighted, 'Vertices lost skin weights: '+str(len(unweighted))
    section_counts = {}
    for face in mesh.data.polygons:
        material = mesh.material_slots[face.material_index].material
        assert material, 'Null material section'
        section_counts[material.name] = section_counts.get(material.name, 0) + 1
    iris_sections = {n: c for n, c in section_counts.items() if 'iris' in n.lower() and c > 0}
    assert iris_sections, 'Iris material section lost in consolidation'
    bounds = [mesh.matrix_world @ Vector(v) for v in mesh.bound_box]
    lo = [min(v[i] for v in bounds) for i in range(3)]
    hi = [max(v[i] for v in bounds) for i in range(3)]
    dims = [hi[i] - lo[i] for i in range(3)]
    report = {
        'tool': 'Blender '+bpy.app.version_string,
        'source': str(source),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'status': 'fresh_process_readback_passed_pending_ue',
        'armature': arm.name,
        'bones': len(arm.data.bones),
        'face_follow_parent': follow.parent.name,
        'head_follow_eye_motion_blender_units': eye_motion,
        'mesh': mesh.name,
        'vertices': len(mesh.data.vertices),
        'triangles': sum(len(p.vertices)-2 for p in mesh.data.polygons),
        'dimensions_blender_units': dims,
        'material_sections_polygon_counts': section_counts,
        'morphs': keys,
        'blink_max_delta_blender_units': {
            name: max((mesh.matrix_world.to_3x3() @ (a.co-b.co)).length
                      for a, b in zip(mesh.data.shape_keys.key_blocks[name].data,
                                      mesh.data.shape_keys.key_blocks['Basis'].data))
            for name in ['Blink_L', 'Blink_R']
        },
        'iris_sections_polygon_counts': iris_sections,
        'unweighted_vertices': len(unweighted),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--')+1])
