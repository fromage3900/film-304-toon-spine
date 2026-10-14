"""Read FBX anatomy, material regions and actual skin influences in a private Blender process."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

root = Path('G:/film-304-toon-spine')
paths = sys.argv[sys.argv.index('--')+1:]
rows = []
for filename in paths:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=filename)
    objects = list(bpy.context.scene.objects)
    meshes = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        parts = []
        for index, slot in enumerate(obj.material_slots):
            polygons = [p for p in mesh.polygons if p.material_index == index]
            ids = set(i for p in polygons for i in p.vertices)
            points = [obj.matrix_world @ mesh.vertices[i].co for i in ids]
            bounds = [[min(v[k] for v in points),max(v[k] for v in points)] for k in range(3)] if points else None
            parts.append({'index':index,'material':slot.material.name if slot.material else None,'vertices':len(ids),'polygons':len(polygons),'triangles':sum(len(p.vertices)-2 for p in polygons),'world_bounds':bounds})
        influence_ids = set(g.group for v in mesh.vertices for g in v.groups if g.weight > .00001)
        meshes.append({'name':obj.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'parts':parts,'weighted_groups':[g.name for g in obj.vertex_groups if g.index in influence_ids], 'unweighted_vertices':sum(not any(g.weight > .00001 for g in v.groups) for v in mesh.vertices)})
    armatures = []
    weighted = set(g for m in meshes for g in m['weighted_groups'])
    for obj in objects:
        if obj.type != 'ARMATURE':
            continue
        ancestors = set()
        for bone in obj.data.bones:
            if bone.name in weighted:
                parent = bone
                while parent:
                    ancestors.add(parent.name)
                    parent = parent.parent
        armatures.append({'name':obj.name,'bones':len(obj.data.bones),'weighted_bones':sum(b.name in weighted for b in obj.data.bones),'weighted_plus_ancestors':len(ancestors),'unweighted_leaf_bones':sum(b.name not in ancestors and not b.children for b in obj.data.bones),'roots':[b.name for b in obj.data.bones if b.parent is None]})
    rows.append({'file':filename,'meshes':meshes,'armatures':armatures})
    print('FBX_AUDIT',filename,'meshes',len(meshes),'verts',sum(m['vertices'] for m in meshes),'bones',sum(a['bones'] for a in armatures))
out = root / 'Saved/Audit/dana_fbx_anatomy.json'
out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
