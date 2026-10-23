"""Standalone FBX gate for Dana_CleanSkin_v09: meshes, morphs, materials, skeleton.

Opens only the exported FBX (fast), measures everything on the imported scene:
  - per-mesh vertex counts vs the v08 mesh contract (morph-helper transforms
    allowed as the exact documented extra set)
  - per-morph channel names + vertex deltas at weight 1.0
  - per-mesh material (shader) names via set membership (listSets), including
    the per-face iris split on both eyeball meshes
  - joint count

Run:  mayapy.exe gate_dana_v09_fbx.py
"""
import json, traceback, datetime, math
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds

OUTPUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
REPORT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/report/v09_fbx_gate.json')

MESHES = {
    'Dana_Body_GEO': 9249, 'Dana_Eyelashes_Lf_GEO': 39, 'Dana_Eyelashes_Rt_GEO': 39,
    'Dana_Eye_Lf_GEO': 1121, 'Dana_Eye_Rt_GEO': 1121, 'Dana_Cornea_Lf_GEO': 161,
    'Dana_Cornea_Rt_GEO': 161, 'Dana_EyeInt_Lf_GEO': 51, 'Dana_EyeInt_Rt_GEO': 51,
    'Dana_Jeans_GEO': 2172, 'Dana_Shirt_GEO': 1564, 'Dana_Shoe_Lf_GEO': 1031,
    'Dana_Shoe_Rt_GEO': 1031, 'Dana_LongHair_Bang_GEO': 474, 'Dana_LongHair_Main_GEO': 566,
    'Dana_Lower_Teeth_GEO1': 2192, 'Dana_UpperTeeth_GEO': 2194, 'Dana_Tongue_GEO': 165,
    'Dana_Eyebrows_GEO': 178,
}
MORPH_HELPERS = {'Blink_L', 'Blink_R', 'Brow_Up', 'Brow_Down', 'Smile', 'Frown', 'Mouth_Wide', 'Jaw_Open'}
EXPECTED_MESH_MATS = {
    'Dana_Body_GEO': {'danaSkin_mat'}, 'Dana_Eyelashes_Lf_GEO': {'danaHair_mat'},
    'Dana_Eyelashes_Rt_GEO': {'danaHair_mat'}, 'Dana_Eye_Lf_GEO': {'danaEye_mat', 'danaIris_mat'},
    'Dana_Eye_Rt_GEO': {'danaEye_mat', 'danaIris_mat'}, 'Dana_Cornea_Lf_GEO': {'danaCornea_mat'},
    'Dana_Cornea_Rt_GEO': {'danaCornea_mat'}, 'Dana_EyeInt_Lf_GEO': {'danaEyeInt_mat'},
    'Dana_EyeInt_Rt_GEO': {'danaEyeInt_mat'}, 'Dana_Jeans_GEO': {'danaPants_mat'},
    'Dana_Shirt_GEO': {'danaShirt_mat'}, 'Dana_Shoe_Lf_GEO': {'danaShoes_mat'},
    'Dana_Shoe_Rt_GEO': {'danaShoes_mat'}, 'Dana_LongHair_Bang_GEO': {'danaHair_mat'},
    'Dana_LongHair_Main_GEO': {'danaHair_mat'}, 'Dana_Lower_Teeth_GEO1': {'danaTeeth_mat', 'danaGum_mat'},
    'Dana_UpperTeeth_GEO': {'danaTeeth_mat', 'danaGum_mat'}, 'Dana_Tongue_GEO': {'danaTongue_mat'},
    'Dana_Eyebrows_GEO': {'danaHair_mat'},
}

r = {'tool': 'gate_dana_v09_fbx.py', 'source': str(OUTPUT), 'stage': 'starting',
     'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    REPORT.write_text(json.dumps(r, indent=2, default=str))

def pts(path):
    return cmds.xform(path + '.vtx[*]', query=True, worldSpace=True, translation=True)

def err_max(a, b):
    mx = 0.0
    for i in range(0, len(a), 3):
        dx = a[i] - b[i]; dy = a[i + 1] - b[i + 1]; dz = a[i + 2] - b[i + 2]
        dd = dx * dx + dy * dy + dz * dz
        if dd > mx: mx = dd
    return math.sqrt(mx)

def shape_sges(shape):
    found = set()
    try:
        found |= {s for s in (cmds.listSets(object=shape, type=1) or []) if cmds.nodeType(s) == 'shadingEngine'}
    except Exception:
        pass
    try:
        found |= set(cmds.listConnections(shape, type='shadingEngine') or [])
    except Exception:
        pass
    return sorted(found)

def shader_of(sge):
    sh = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
    return (sh[0].rsplit(':', 1)[-1].rsplit('|', 1)[-1] if sh else None)

try:
    save()
    cmds.loadPlugin('fbxmaya', quiet=True)
    cmds.file(str(OUTPUT), open=True, force=True, ignoreVersion=True, executeScriptNodes=False, prompt=False)
    cmds.evaluationManager(mode='off')
    r['stage'] = 'opened'
    # ---- transforms of interest ----
    tf_by_short = {}
    for t in (cmds.ls(type='transform', long=True) or []):
        short = t.rsplit('|', 1)[-1].rsplit(':', 1)[-1]
        tf_by_short.setdefault(short, []).append(t)
    missing = [n for n in MESHES if n not in tf_by_short]
    if missing:
        raise RuntimeError('Meshes missing from FBX: %s' % missing)
    extra = [n for n in tf_by_short if (n in MESHES or n in MORPH_HELPERS or n.startswith('MorphTarget_')
              or n in ('RenderMeshes',)) is False and tf_by_short[n] and cmds.listRelatives(tf_by_short[n][0], shapes=True, noIntermediate=True)]
    extra = [n for n in tf_by_short if n not in MESHES and n not in MORPH_HELPERS and tf_by_short[n]
             and (cmds.listRelatives(tf_by_short[n][0], shapes=True, noIntermediate=True) or [])]
    r['extra_mesh_transforms'] = sorted(set(extra))
    # ---- per-mesh measurements ----
    meshes = {}
    for name, want_v in MESHES.items():
        tf = tf_by_short[name][0]
        shape = cmds.listRelatives(tf, shapes=True, noIntermediate=True, fullPath=True)[0]
        row = {'vertices': cmds.polyEvaluate(shape, vertex=True), 'faces': cmds.polyEvaluate(shape, face=True),
               'skins': [s.rsplit(':', 1)[-1] for s in (cmds.ls(cmds.listHistory(shape, pruneDagObjects=True) or [], type='skinCluster') or [])]}
        sges = shape_sges(shape)
        mats = {shader_of(s) for s in sges}
        row['shaders'] = sorted(x for x in mats if x)
        row['material_fail'] = sorted(EXPECTED_MESH_MATS[name] - set(row['shaders']))
        sge_detail = []
        for s in sges:
            sh = shader_of(s)
            if sh in ('danaIris_mat', 'danaEye_mat', 'danaGum_mat', 'danaTeeth_mat'):
                members = [str(m) for m in (cmds.sets(s, query=True) or []) if name in str(m)]
                sge_detail.append({'shader': sh, 'members': members})
        if sge_detail:
            row['split_detail'] = sge_detail
        meshes[name] = row
    r['meshes'] = meshes
    r['mesh_vertex_pass'] = all(meshes[n]['vertices'] == v for n, v in MESHES.items())
    r['mesh_skin_pass'] = all(meshes[n]['skins'] for n in MESHES)
    r['mesh_material_pass'] = all(not meshes[n]['material_fail'] for n in MESHES)
    # ---- morphs ----
    body_tf = tf_by_short['Dana_Body_GEO'][0]
    bodyshape = cmds.listRelatives(body_tf, shapes=True, noIntermediate=True, fullPath=True)[0]
    bs = [b for b in (cmds.ls(cmds.listHistory(bodyshape, pruneDagObjects=True) or [], type='blendShape') or [])]
    r['blendshape_nodes'] = [b.rsplit(':', 1)[-1] for b in bs]
    morph = {'channels': [], 'deltas_cm': {}}
    if bs:
        al = cmds.aliasAttr(bs[0], query=True) or []
        amap = {al[i]: al[i + 1] for i in range(0, len(al), 2)} if al else {}
        morph['channels'] = sorted(amap.keys())
        rest = pts(body_tf)
        for alias, plug in amap.items():
            cmds.setAttr(bs[0] + '.' + plug, 1.0)
            cmds.dgdirty(allPlugs=True)
            cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)
            morph['deltas_cm'][alias] = round(err_max(pts(body_tf), rest), 4)
            cmds.setAttr(bs[0] + '.' + plug, 0.0)
            cmds.dgdirty(allPlugs=True)
            cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)
    r['morph_check'] = morph
    r['morph_pass'] = set(morph['channels']) == MORPH_HELPERS and all(v > 0.05 for v in morph['deltas_cm'].values())
    # ---- skeleton ----
    r['joint_count'] = len(cmds.ls(type='joint', long=True) or [])
    r['stage'] = 'gated'
    r['gate_pass'] = r['mesh_vertex_pass'] and r['mesh_skin_pass'] and r['mesh_material_pass'] and r['morph_pass']
    save()
    print(json.dumps({k: r[k] for k in ('stage', 'gate_pass', 'mesh_vertex_pass', 'mesh_skin_pass',
                                        'mesh_material_pass', 'morph_pass', 'joint_count',
                                        'extra_mesh_transforms', 'morph_check')}, indent=1))
except Exception:
    r['stage'] = 'blocked'; r['error'] = traceback.format_exc(); save(); print(r['error']); raise
finally:
    try:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass
