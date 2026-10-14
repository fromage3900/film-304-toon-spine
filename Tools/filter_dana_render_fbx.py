"""Remove Maya helper meshes from Dana's FBX without re-exporting its rig.

Run with Blender's Python, whose FBX parser and writer preserve the source
transforms, geometry streams, and skin cluster data. This does not create
missing body skin weights.
"""
import hashlib
import json
import sys
from pathlib import Path

from io_scene_fbx import data_types, encode_bin, parse_fbx


RENDER_MODELS = {
    'Dana_Eyebrows_GEO',
    'Dana_Eye_Lf_GEO', 'Dana_Cornea_Lf_GEO', 'Dana_EyeInt_Lf_GEO',
    'Dana_Eye_Rt_GEO', 'Dana_Cornea_Rt_GEO', 'Dana_EyeInt_Rt_GEO',
    'Dana_Shoe_Lf_GEO', 'Dana_Shoe_Rt_GEO', 'PantsButton_GEO',
    'Dana_Jeans_GEO', 'Dana_Shirt_GEO', 'Dana_Body_GEOBase',
    'Dana_Original_Hair_GEO',
}


def child(node, identifier):
    return next((item for item in node.elems if item.id == identifier), None)


def name(value):
    return value.decode('utf-8', 'replace').split('\x00')[0]


METHODS = {
    data_types.BOOL: 'add_bool',
    data_types.CHAR: 'add_char',
    data_types.INT8: 'add_int8',
    data_types.INT16: 'add_int16',
    data_types.INT32: 'add_int32',
    data_types.INT64: 'add_int64',
    data_types.FLOAT32: 'add_float32',
    data_types.FLOAT64: 'add_float64',
    data_types.BYTES: 'add_bytes',
    data_types.STRING: 'add_string',
    data_types.INT32_ARRAY: 'add_int32_array',
    data_types.INT64_ARRAY: 'add_int64_array',
    data_types.FLOAT32_ARRAY: 'add_float32_array',
    data_types.FLOAT64_ARRAY: 'add_float64_array',
    data_types.BOOL_ARRAY: 'add_bool_array',
    data_types.BYTE_ARRAY: 'add_byte_array',
}


def writable(node):
    result = encode_bin.FBXElem(node.id)
    for type_code, value in zip(node.props_type, node.props):
        method = METHODS.get(type_code)
        if method is None:
            raise RuntimeError('Unsupported FBX property type ' + repr(type_code))
        if type_code == data_types.BOOL:
            value = bool(value)
        elif type_code in (data_types.FLOAT32, data_types.FLOAT64):
            value = float(value)
        getattr(result, method)(value)
    result.elems = [writable(item) for item in node.elems]
    return result


def triangles(geometry):
    indices = child(geometry, b'PolygonVertexIndex').props[0]
    count = 0
    polygon_size = 0
    for index in indices:
        polygon_size += 1
        if index < 0:
            count += polygon_size - 2
            polygon_size = 0
    return count


def inspect(root):
    objects = child(root, b'Objects').elems
    connections = child(root, b'Connections').elems
    by_id = {int(item.props[0]): item for item in objects if item.props}
    model_for_geometry = {}
    for link in connections:
        if len(link.props) < 3 or link.props[0] != b'OO':
            continue
        geo_id, model_id = int(link.props[1]), int(link.props[2])
        if (geo_id in by_id and model_id in by_id
                and by_id[geo_id].id == b'Geometry'
                and by_id[model_id].id == b'Model'):
            model_for_geometry[geo_id] = model_id
    meshes = []
    for geo in objects:
        if geo.id != b'Geometry' or geo.props[-1] != b'Mesh':
            continue
        geo_id = int(geo.props[0])
        model_id = model_for_geometry.get(geo_id)
        if model_id is None:
            raise RuntimeError('Unattached mesh geometry: ' + str(geo_id))
        meshes.append((geo, by_id[model_id]))
    return objects, connections, meshes


def main(source, target):
    source, target = Path(source), Path(target)
    if not source.is_file():
        raise RuntimeError('Source FBX missing: ' + str(source))
    if target.exists():
        raise RuntimeError('Refusing to overwrite: ' + str(target))
    root, version = parse_fbx.parse(str(source))
    objects, connections, meshes = inspect(root)
    if len(meshes) != 37:
        raise RuntimeError('Unexpected source mesh count: ' + str(len(meshes)))
    kept = [(geo, model) for geo, model in meshes
            if name(model.props[1]).split(':')[-1] in RENDER_MODELS]
    if len(kept) != len(RENDER_MODELS):
        raise RuntimeError('Render mesh allowlist did not match exactly')
    removed = [(geo, model) for geo, model in meshes if (geo, model) not in kept]
    removed_ids = {int(item.props[0]) for pair in removed for item in pair}
    body = next(geo for geo, model in kept
                if name(model.props[1]).endswith(':Dana_Body_GEOBase'))
    body_id = int(body.props[0])
    deformers = {int(o.props[0]): o for o in objects if o.id == b'Deformer'}
    body_skin_ids = [int(link.props[1]) for link in connections
                     if len(link.props) >= 3 and link.props[0] == b'OO'
                     and int(link.props[2]) == body_id
                     and int(link.props[1]) in deformers
                     and deformers[int(link.props[1])].props[-1] == b'Skin']
    if body_skin_ids:
        raise RuntimeError('Body skin data changed; review before filtering')
    before_triangles = sum(triangles(geo) for geo, _ in meshes)
    retained_triangles = sum(triangles(geo) for geo, _ in kept)
    if before_triangles != 312553 or retained_triangles != 37822:
        raise RuntimeError('Unexpected source triangle count')
    child(root, b'Objects').elems[:] = [o for o in objects
                                       if not o.props or int(o.props[0]) not in removed_ids]
    child(root, b'Connections').elems[:] = [c for c in connections
        if len(c.props) < 3 or int(c.props[1]) not in removed_ids
        and int(c.props[2]) not in removed_ids]
    remaining_objects = child(root, b'Objects').elems
    definitions = child(root, b'Definitions')
    if definitions is not None:
        total = child(definitions, b'Count')
        if total is not None:
            total.props[0] = len(remaining_objects)
        for group in definitions.elems:
            if group.id == b'ObjectType' and group.props:
                count = child(group, b'Count')
                if count is not None:
                    count.props[0] = sum(o.id == group.props[0] for o in remaining_objects)
    target.parent.mkdir(parents=True, exist_ok=True)
    encode_bin.write(str(target), writable(root), version)
    checked, checked_version = parse_fbx.parse(str(target))
    _, _, checked_meshes = inspect(checked)
    checked_triangles = sum(triangles(geo) for geo, _ in checked_meshes)
    if checked_version != version or len(checked_meshes) != 14 or checked_triangles != 37822:
        raise RuntimeError('Filtered FBX failed readback')
    report = {
        'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output': str(target), 'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'fbx_version': version, 'source_meshes': len(meshes),
        'retained_meshes': len(checked_meshes),
        'source_triangles': before_triangles, 'retained_triangles': checked_triangles,
        'removed_triangles': before_triangles - checked_triangles,
        'removed_models': [name(model.props[1]) for _, model in removed],
        'body_skin_cluster_count': len(body_skin_ids),
        'qualification': 'Geometry filter only; visible body remains unbound in the source FBX.',
    }
    audit = target.parents[2] / 'Audit' / 'dana_fbx_geometry_filter.json'
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('DANA_FBX_GEOMETRY_FILTER', json.dumps(report), flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) != 2:
        raise SystemExit('Expected source and output FBX paths after --')
    main(*args)
