"""Read-only Blender census of Dana v09's imported skeleton/object layout."""
import json
import sys
from collections import Counter
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx'
OUT = ROOT / 'Saved/OfflineIntake/20261017/task1_face_eyes/report/v09_blender_layout.json'

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SOURCE), use_anim=False)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    names = Counter(b.name for a in arms for b in a.data.bones)
    report = {
        'source': str(SOURCE),
        'status': 'layout_read',
        'armature_objects': len(arms),
        'total_bones': sum(len(a.data.bones) for a in arms),
        'duplicate_bone_names': {k:v for k,v in names.items() if v > 1},
        'armatures': [], 'meshes': [], 'object_hierarchy': [],
    }
    for o in bpy.data.objects:
        if any(k.lower() in o.name.lower() for k in ['main','facegroup','facemotion','deformationsystem']):
            report['object_hierarchy'].append({
                'object': o.name, 'type': o.type,
                'parent': o.parent.name if o.parent else None,
                'parent_type': o.parent_type, 'parent_bone': o.parent_bone,
                'constraints': [{'name': c.name, 'type': c.type,
                                 'target': getattr(c, 'target', None).name if getattr(c, 'target', None) else None,
                                 'subtarget': getattr(c, 'subtarget', '')} for c in o.constraints],
            })
    for a in arms:
        report['armatures'].append({
            'object': a.name,
            'parent': a.parent.name if a.parent else None,
            'constraints': [{'name': c.name, 'type': c.type,
                             'target': getattr(c, 'target', None).name if getattr(c, 'target', None) else None,
                             'subtarget': getattr(c, 'subtarget', '')} for c in a.constraints],
            'matrix_world': [list(row) for row in a.matrix_world],
            'bones': len(a.data.bones),
            'selected_bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None}
                               for b in a.data.bones if any(k.lower() in b.name.lower()
                                   for k in ['Root_M','Head_M','FaceDeformationFollowHead','Eye_L','Jaw_M'])],
        })
    for m in meshes:
        report['meshes'].append({
            'object': m.name,
            'parent': m.parent.name if m.parent else None,
            'parent_type': m.parent_type,
            'parent_bone': m.parent_bone,
            'constraints': [{'name': c.name, 'type': c.type,
                             'target': getattr(c, 'target', None).name if getattr(c, 'target', None) else None,
                             'subtarget': getattr(c, 'subtarget', '')} for c in m.constraints],
            'vertices': len(m.data.vertices),
            'vertex_group_count': len(m.vertex_groups),
            'polygons': len(m.data.polygons),
            'shape_keys': list(m.data.shape_keys.key_blocks.keys()) if m.data.shape_keys else [],
            'armature_modifiers': [mod.object.name if mod.object else None for mod in m.modifiers if mod.type == 'ARMATURE'],
            'material_slots': [s.material.name if s.material else None for s in m.material_slots],
            'vertex_groups_without_bone': [g.name for g in m.vertex_groups
                if not any(g.name == b.name for a in arms for b in a.data.bones)],
        })
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','armature_objects','total_bones','duplicate_bone_names']}))

if __name__ == '__main__':
    main()
