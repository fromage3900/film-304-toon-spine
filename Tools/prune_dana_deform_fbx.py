"""Make a bounded Dana FBX preview with only render meshes and deform bones.

Preserves source mesh streams and existing skin clusters. It cannot restore
the source body's missing skin cluster and is not a final rig export.
"""
import hashlib
import json
import sys
from pathlib import Path

from io_scene_fbx import encode_bin, parse_fbx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from filter_dana_render_fbx import child, name, triangles, writable


def hierarchy(root):
    objects = child(root, b'Objects').elems
    links = child(root, b'Connections').elems
    by_id = {int(x.props[0]): x for x in objects if x.props}
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
             and any(p in meshes for p in parents.get(i, []))}
    clusters = {i for i, o in deformers.items() if o.props[-1] == b'Cluster'
                and any(p in skins for p in parents.get(i, []))}
    bone_ids = {source for source, target in oo
                if target in clusters and source in models}
    mesh_models = {p for mesh in meshes for p in parents.get(mesh, []) if p in models}
    needed = bone_ids | mesh_models
    model_parents = {i: next((p for p in parents.get(i, []) if p in models), None)
                     for i in models}
    for initial in tuple(needed):
        current = model_parents.get(initial)
        visited = set()
        while current is not None and current not in visited:
            visited.add(current)
            needed.add(current)
            current = model_parents.get(current)
    roots = {i for i in needed if model_parents.get(i) not in needed}
    return objects, links, models, meshes, deformers, skins, clusters, needed, roots


def update_counts(root):
    objects = child(root, b'Objects').elems
    definitions = child(root, b'Definitions')
    if definitions is None:
        return
    total = child(definitions, b'Count')
    if total is not None:
        total.props[0] = len(objects)
    for group in definitions.elems:
        if group.id == b'ObjectType' and group.props:
            count = child(group, b'Count')
            if count is not None:
                count.props[0] = sum(o.id == group.props[0] for o in objects)


def main(source, target):
    source, target = Path(source), Path(target)
    if not source.is_file() or target.exists():
        raise RuntimeError('Input missing or output already exists')
    root, version = parse_fbx.parse(str(source))
    objects, links, models, meshes, deformers, skins, clusters, needed, roots = hierarchy(root)
    if (len(meshes), len(skins), len(clusters), len(needed), len(roots)) != (14, 11, 64, 76, 1):
        raise RuntimeError('Unexpected geometry or deform hierarchy')
    if sum(triangles(geo) for geo in meshes.values()) != 37822:
        raise RuntimeError('Unexpected triangle count')
    removed_ids = set()
    removed_counts = {}
    for item in objects:
        if not item.props:
            continue
        ident = int(item.props[0])
        remove = ((item.id == b'Model' and ident not in needed)
                  or (item.id == b'Geometry' and ident not in meshes)
                  or (item.id == b'Deformer' and ident not in skins | clusters)
                  or item.id == b'Pose')
        if remove:
            removed_ids.add(ident)
            key = name(item.id)
            removed_counts[key] = removed_counts.get(key, 0) + 1
    child(root, b'Objects').elems[:] = [o for o in objects
                                       if not o.props or int(o.props[0]) not in removed_ids]
    child(root, b'Connections').elems[:] = [c for c in links
        if len(c.props) < 3 or (int(c.props[1]) not in removed_ids
                               and int(c.props[2]) not in removed_ids)]
    update_counts(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    encode_bin.write(str(target), writable(root), version)
    checked, checked_version = parse_fbx.parse(str(target))
    _, _, final_models, final_meshes, _, final_skins, final_clusters, final_needed, final_roots = hierarchy(checked)
    if (checked_version, len(final_models), len(final_meshes), len(final_skins),
            len(final_clusters), len(final_needed), len(final_roots)) != (version, 76, 14, 11, 64, 76, 1):
        raise RuntimeError('Pruned FBX did not round-trip its deform hierarchy')
    report = {
        'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output': str(target), 'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'fbx_version': version, 'mesh_count': len(final_meshes),
        'triangles': sum(triangles(g) for g in final_meshes.values()),
        'model_count_before': len(models), 'model_count_after': len(final_models),
        'skin_count': len(final_skins), 'cluster_count': len(final_clusters),
        'deform_root': name(final_models[next(iter(final_roots))].props[1]),
        'removed_object_counts': removed_counts,
        'body_skin_cluster_count': 0,
        'qualification': 'Preview deform export only. Body has no skin cluster in source FBX.',
    }
    audit = target.parents[2] / 'Audit' / 'dana_fbx_deform_prune.json'
    audit.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('DANA_FBX_DEFORM_PRUNE', json.dumps(report), flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) != 2:
        raise SystemExit('Expected source and output FBX paths after --')
    main(*args)
