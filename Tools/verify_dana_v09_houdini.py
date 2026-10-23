"""Independent hython readback of Dana_CleanSkin_v09.fbx (task1 gate).

Extends Tools/verify_dana_native_export_houdini.py (same kinefx fbxcharacterimport
approach, read-only) with: the full 19-mesh v08 profile, true triangle counts
(sum of vertices-per-primitive - 2), morph channel census via blendshape_channel
attributes, per-channel morph-target vertex deltas, and skeleton point counts
for regression against the v08 baselines. Writes evidence JSON + a .hip scene.

Run:  hython.exe verify_dana_v09_houdini.py
"""
import sys, json, hashlib, traceback, datetime
from pathlib import Path
import hou

FBX = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
OUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/report')
OUT.mkdir(parents=True, exist_ok=True)

PROFILE = {
    'Dana_Body_GEO': 9249, 'Dana_Eyelashes_Lf_GEO': 39, 'Dana_Eyelashes_Rt_GEO': 39,
    'Dana_Eye_Lf_GEO': 1121, 'Dana_Eye_Rt_GEO': 1121, 'Dana_Cornea_Lf_GEO': 161,
    'Dana_Cornea_Rt_GEO': 161, 'Dana_EyeInt_Lf_GEO': 51, 'Dana_EyeInt_Rt_GEO': 51,
    'Dana_Jeans_GEO': 2172, 'Dana_Shirt_GEO': 1564, 'Dana_Shoe_Lf_GEO': 1031,
    'Dana_Shoe_Rt_GEO': 1031, 'Dana_LongHair_Bang_GEO': 474, 'Dana_LongHair_Main_GEO': 566,
    'Dana_Lower_Teeth_GEO1': 2192, 'Dana_UpperTeeth_GEO': 2194, 'Dana_Tongue_GEO': 165,
    'Dana_Eyebrows_GEO': 178,
}
EXPECTED_MORPHS = {'Blink_L', 'Blink_R', 'Brow_Up', 'Brow_Down', 'Smile', 'Frown', 'Mouth_Wide', 'Jaw_Open'}
V08_SKELETON = {'capture_skeleton_points': 179, 'animated_hierarchy_points': 1250}

r = {'tool': 'verify_dana_v09_houdini.py', 'source': str(FBX), 'stage': 'starting',
     'production_ready': False, 'deformation_tested': False, 'animation_retarget_tested': False,
     'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    (OUT / 'v09_houdini_verification.json').write_text(json.dumps(r, indent=2, default=str))

def digest():
    return hashlib.sha256(FBX.read_bytes()).hexdigest()

save()
try:
    r['source_sha256_before'] = digest()
    geo = hou.node('/obj').createNode('geo', 'DANA_V09_READBACK')
    imp = geo.createNode('kinefx::fbxcharacterimport', 'V09_READ_ONLY')
    imp.parm('fbxfile').set(FBX.as_posix())
    imp.parm('importinvisibleshapes').set(False)
    imp.cook(force=True)
    g = imp.geometry()
    r['import_errors'] = imp.errors(); r['import_warnings'] = imp.warnings()
    if g is None:
        raise RuntimeError('Native importer did not return geometry')
    capture = g.findPointAttrib('boneCapture')
    meshes = {}
    morph_channels = {}
    morph_targets = {}
    rest_points = {}
    for prim in g.prims():
        name = prim.attribValue('name') if g.findPrimAttrib('name') else 'UNNAMED'
        simple = name.rsplit(':', 1)[-1]
        m = meshes.setdefault(simple, {'names': set(), 'points': set(), 'polygons': 0, 'triangles': 0,
                                       'packed_primitives': 0, 'morph_channels': []})
        m['names'].add(name)
        if prim.type() == hou.primType.PackedGeometry:
            channel = prim.attribValue('blendshape_channel') if g.findPrimAttrib('blendshape_channel') else ''
            target = prim.attribValue('blendshape_name') if g.findPrimAttrib('blendshape_name') else ''
            suffix = channel.rsplit('.', 1)[-1].rsplit(':', 1)[-1]
            if suffix:
                m['morph_channels'].append(suffix)
                morph_channels.setdefault(suffix, 0)
                morph_channels[suffix] += 1
                try:
                    pg = prim.geometry()
                    if pg is not None:
                        morph_targets[suffix] = [tuple(p.position()) for p in pg.points()]
                except Exception:
                    pass
            else:
                m['packed_primitives'] += 1
        else:
            m['polygons'] += 1
            m['triangles'] += max(len(prim.vertices()) - 2, 0)
            m['points'].update(p.number() for p in prim.points())
            if simple == 'Dana_Body_GEO':
                rest_points = {p.number(): tuple(p.position()) for p in prim.points()}
    result = {}
    points = g.points()
    for name, m in meshes.items():
        weighted = 0; max_influences = 0; minimum = None; maximum = None
        for index in m['points']:
            v = points[index].attribValue(capture) if capture else []
            weights = [v[i + 1] for i in range(0, len(v) - 1, 2) if v[i] >= 0 and v[i + 1] > 1e-6]
            total = sum(weights); weighted += bool(weights)
            max_influences = max(max_influences, len(weights))
            minimum = total if minimum is None else min(minimum, total)
            maximum = total if maximum is None else max(maximum, total)
        result[name] = {'names': sorted(m['names']), 'polygon_points': len(m['points']),
                        'polygons': m['polygons'], 'triangles': m['triangles'],
                        'packed_primitives': m['packed_primitives'],
                        'morph_channels': sorted(set(m['morph_channels'])),
                        'weighted_vertices': weighted, 'max_influences_per_vertex': max_influences,
                        'weight_sum_min': minimum, 'weight_sum_max': maximum}
    r['meshes'] = result
    # profile checks
    checks = {}
    for name, count in PROFILE.items():
        m = result.get(name, {})
        checks[name] = bool(m.get('polygon_points') == count and m.get('weighted_vertices') == count
                            and m.get('weight_sum_min', 0) >= 0.999 and m.get('weight_sum_max', 2) <= 1.001)
    r['profile_checks'] = checks
    r['profile_pass'] = all(checks.values()) and set(result) == set(PROFILE)
    r['unexpected_meshes'] = sorted(set(result) - set(PROFILE))
    r['total_triangles'] = sum(m['triangles'] for m in result.values())
    r['total_polygons'] = sum(m['polygons'] for m in result.values())
    # morph channel census + target deltas vs rest
    r['morph_channels'] = sorted(morph_channels.keys())
    deltas = {}
    for ch, tpts in morph_targets.items():
        if not rest_points or len(tpts) != len(rest_points):
            deltas[ch] = None
            continue
        mx = 0.0
        for i, p in enumerate(tpts):
            q = rest_points[i]
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
            if d > mx: mx = d
        deltas[ch] = round(mx ** 0.5, 4)
    r['morph_target_max_delta_cm'] = deltas
    r['morph_pass'] = set(morph_channels.keys()) == EXPECTED_MORPHS
    # skeleton regression vs v08 baselines
    for i, label in [(1, 'capture_skeleton'), (2, 'animated_hierarchy')]:
        n = geo.createNode('null', label); n.setInput(0, imp, i); s = n.geometry()
        r[label] = {'points': len(s.points()), 'primitives': len(s.prims())}
    r['skeleton_regression_pass'] = (r['capture_skeleton']['points'] == V08_SKELETON['capture_skeleton_points']
                                     and r['animated_hierarchy']['points'] == V08_SKELETON['animated_hierarchy_points'])
    r['source_sha256_after'] = digest()
    r['source_unchanged'] = r['source_sha256_before'] == r['source_sha256_after']
    r['stage'] = 'v09_houdini_verified'
    r['gate_pass'] = r['profile_pass'] and r['morph_pass'] and r['skeleton_regression_pass'] and not r['import_errors']
    hou.hipFile.save(str(OUT / 'V09_Independent_Readback.hip'))
except Exception:
    r['stage'] = 'verification_blocked'; r['error'] = traceback.format_exc()
save()
print(json.dumps({k: r[k] for k in ('stage', 'gate_pass', 'profile_pass', 'morph_pass', 'morph_channels',
                                    'morph_target_max_delta_cm', 'skeleton_regression_pass', 'capture_skeleton',
                                    'animated_hierarchy', 'total_triangles', 'total_polygons',
                                    'unexpected_meshes', 'import_errors', 'source_unchanged')}, indent=1))
