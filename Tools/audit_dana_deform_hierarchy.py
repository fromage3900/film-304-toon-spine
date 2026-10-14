"""Read only FBX hierarchy audit for Dana's surviving render geometry."""
import json
import sys
from pathlib import Path

from io_scene_fbx import parse_fbx


def child(node, identifier):
    return next((x for x in node.elems if x.id == identifier), None)


def label(value):
    return value.decode('utf-8', 'replace').split('\x00')[0]


def scale(model):
    props = child(model, b'Properties70')
    if props:
        for item in props.elems:
            if item.id == b'P' and item.props and item.props[0] == b'Lcl Scaling':
                return [float(x) for x in item.props[-3:]]
    return [1., 1., 1.]


def main(filename):
    root, version = parse_fbx.parse(filename)
    objects = child(root, b'Objects').elems
    by_id = {int(x.props[0]): x for x in objects if x.props}
    links = child(root, b'Connections').elems
    oo = [(int(x.props[1]), int(x.props[2])) for x in links
          if len(x.props) >= 3 and x.props[0] == b'OO']
    parents = {}
    for source, target in oo:
        parents.setdefault(source, []).append(target)
    models = {i: o for i, o in by_id.items() if o.id == b'Model'}
    meshes = {i: o for i, o in by_id.items()
              if o.id == b'Geometry' and o.props[-1] == b'Mesh'}
    deformers = {i: o for i, o in by_id.items() if o.id == b'Deformer'}
    skins = {i for i, o in deformers.items() if o.props[-1] == b'Skin'
             and any(parent in meshes for parent in parents.get(i, []))}
    clusters = {i for i, o in deformers.items() if o.props[-1] == b'Cluster'
                and any(parent in skins for parent in parents.get(i, []))}
    bone_ids = {source for source, target in oo
                if target in clusters and source in models}
    model_parents = {i: next((p for p in parents.get(i, []) if p in models), None)
                     for i in models}
    needed = set(bone_ids)
    for bone in tuple(bone_ids):
        seen = set()
        current = model_parents.get(bone)
        while current is not None and current not in seen:
            seen.add(current)
            needed.add(current)
            current = model_parents.get(current)
    roots = {i for i in needed if model_parents.get(i) not in needed}
    zero_scale = {i for i in needed if any(abs(v) < 1e-6 for v in scale(models[i]))}
    mesh_models = {p for mesh in meshes for p in parents.get(mesh, []) if p in models}
    needed_with_mesh = needed | mesh_models
    for mesh_model in tuple(mesh_models):
        seen = set()
        current = model_parents.get(mesh_model)
        while current is not None and current not in seen:
            seen.add(current)
            needed_with_mesh.add(current)
            current = model_parents.get(current)
    mesh_roots = {i for i in needed_with_mesh if model_parents.get(i) not in needed_with_mesh}
    mesh_zero_scale = {i for i in needed_with_mesh
                       if any(abs(v) < 1e-6 for v in scale(models[i]))}
    def record(identifier):
        node = models[identifier]
        return {'id': identifier, 'name': label(node.props[1]),
                'type': label(node.props[-1]), 'scale': scale(node)}
    report = {
        'source': filename, 'fbx_version': version,
        'render_meshes': len(meshes), 'model_objects': len(models),
        'skin_deformers_on_render_geometry': len(skins),
        'clusters_on_render_geometry': len(clusters),
        'directly_weighted_bones': len(bone_ids),
        'weighted_bones_and_ancestors': len(needed),
        'required_roots': [record(i) for i in sorted(roots)],
        'zero_scale_required_models': [record(i) for i in sorted(zero_scale)],
        'weighted_bones_and_render_mesh_ancestors': len(needed_with_mesh),
        'required_roots_with_meshes': [record(i) for i in sorted(mesh_roots)],
        'zero_scale_with_meshes': [record(i) for i in sorted(mesh_zero_scale)],
        'render_mesh_model_roots': [record(i) for i in sorted(mesh_models)
                                    if model_parents.get(i) is None],
    }
    output = Path('G:/film-304-toon-spine/Saved/Audit/dana_fbx_deform_hierarchy.json')
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('DANA_DEFORM_HIERARCHY', json.dumps(report), flush=True)


if __name__ == '__main__':
    filename = sys.argv[sys.argv.index('--') + 1]
    main(filename)
