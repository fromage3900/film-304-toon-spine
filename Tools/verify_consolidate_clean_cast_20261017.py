"""Independent Blender gates and one-mesh FBX for the UE legacy importer."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]

def main(character):
    base = ROOT / 'Saved/OfflineIntake/20261017/clean_cast' / character
    source = base / (character + '_CleanFilm_v01.fbx')
    output = base / (character + '_CleanFilm_UE_v01.fbx')
    report_path = base / 'blender_verification.json'
    report = {'tool': 'Blender '+bpy.app.version_string, 'source': str(source),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'status':'starting'}
    def save(): report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if output.exists(): raise RuntimeError('Existing consolidated candidate preserved')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False)
    arms = [o for o in bpy.data.objects if o.type=='ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type=='MESH']
    native = json.loads((base/'export_report.json').read_text())
    expected = {r['source'].rsplit('|',1)[-1]:r for r in native['meshes']}
    report['mesh_inventory'] = []
    assert len(arms)==1, 'Must be exactly one armature'
    arm = arms[0]
    report['bone_count'] = len(arm.data.bones)
    # Maya exports preserve the FilmExport namespace as a Blender bone prefix.
    # Resolve by suffix but verify the actual imported parent relationship.
    def bone_named(suffix):
        matches = [b for b in arm.data.bones if b.name.rsplit(':', 1)[-1] == suffix]
        assert len(matches) == 1, 'Expected one bone named '+suffix+', got '+repr([b.name for b in matches])
        return matches[0]
    follow = bone_named('FaceDeformationFollowHead')
    assert follow.parent and follow.parent.name.rsplit(':',1)[-1]=='Head_M', 'Face must follow Head_M'
    for obj in meshes:
        name = obj.name.rsplit(':',1)[-1]
        assert name in expected and len(obj.data.vertices)==expected[name]['vertices'], 'Mesh inventory differs: '+name
        assert any(m.type=='ARMATURE' and m.object==arm for m in obj.modifiers), 'Unbound mesh: '+name
        unweighted = [v.index for v in obj.data.vertices if sum(g.weight for g in v.groups)<0.99]
        assert not unweighted, 'Unweighted vertices: '+name
        counts = {}
        for face in obj.data.polygons:
            mat = obj.material_slots[face.material_index].material
            assert mat, 'Null material'
            counts[mat.name] = counts.get(mat.name,0)+1
        if name in [character+'_Eye_Lf_GEO',character+'_Eye_Rt_GEO']:
            assert any('iris' in n.lower() and count>0 for n,count in counts.items()), 'Missing iris split'
        report['mesh_inventory'].append({'name':name,'vertices':len(obj.data.vertices),
            'material_faces':counts,'morphs':list(obj.data.shape_keys.key_blocks.keys()) if obj.data.shape_keys else []})
    assert set(expected)=={r['name'] for r in report['mesh_inventory']}, 'Missing native mesh'
    body = next(o for o in meshes if o.name.rsplit(':',1)[-1]==character+'_Body_GEO')
    assert body.data.shape_keys, 'Blink targets missing'
    blocks = body.data.shape_keys.key_blocks
    for name in ['Blink_L','Blink_R']:
        assert name in blocks, 'Blink missing: '+name
        delta = max((a.co-b.co).length for a,b in zip(blocks[name].data,blocks[0].data))
        assert delta>0.00001, 'Empty blink'
    # Evaluate an actual head motion: iris bones must move with Head_M, not stay
    # in their former sibling subtree. Restore before writing the candidate.
    head = arm.pose.bones[bone_named('Head_M').name]; head.rotation_mode='XYZ'
    eye = arm.pose.bones[bone_named('Eye_L').name]; bpy.context.view_layer.update()
    before = eye.matrix.translation.copy()
    head.rotation_euler.z += 0.15; bpy.context.view_layer.update()
    motion = (eye.matrix.translation-before).length
    assert motion>0.00001, 'Head motion did not move eyes'
    head.rotation_euler.z -= 0.15; bpy.context.view_layer.update()
    report['head_follow_eye_motion_blender_units'] = motion
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes: obj.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    body.name=character+'_CleanFilm'
    report['consolidated_vertices']=len(body.data.vertices)
    report['consolidated_materials']=[s.material.name for s in body.material_slots]
    report['consolidated_morphs']=list(body.data.shape_keys.key_blocks.keys())
    assert all(name in body.data.shape_keys.key_blocks for name in ['Blink_L','Blink_R'])
    assert len(body.data.vertices)==sum(r['vertices'] for r in expected.values())
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); arm.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(output),use_selection=True,object_types={'ARMATURE','MESH'},
        apply_unit_scale=True,global_scale=1.0,bake_space_transform=False,add_leaf_bones=False,
        primary_bone_axis='Y',secondary_bone_axis='X',use_mesh_modifiers=False,
        mesh_smooth_type='FACE',bake_anim=False,path_mode='AUTO')
    report.update(output=str(output),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  status='independent_readback_and_consolidation_passed_pending_ue')
    save(); print(json.dumps(report))

if __name__=='__main__':
    main(sys.argv[sys.argv.index('--')+1])
