"""Dana_CleanSkin_v09 export: native face morph targets + per-face material splits.

Extends Tools/export_dana_clean_skin_v08.py (same isolated evaluated-mesh chain,
same exact native skin weight copy, same FBX settings, source never saved) with:
  1. 8 face morph targets baked on the body copy from the rig's OWN face system
     (asFaceBS channels + native blink/jaw SDK controls), following the v08
     blink-bake precedent.
  2. Per-face material assignments replicated on every duplicate (v08 assigned
     the whole mesh to sgs[0], which destroyed the native danaIris_mat split on
     the eyeball caps and the danaTeeth_mat/danaGum_mat split on teeth).
  3. Readback gates: FBX reopened in Maya; per-mesh vertex counts, morph channel
     names, per-morph vertex deltas, per-face material membership all measured.

Run:  mayapy.exe export_dana_clean_skin_v09_face_morphs.py
"""
import json, hashlib, traceback, datetime, math
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds, mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

SOURCE = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/scratch/Dana_Rig_v1.5.mb')
OUTPUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
REPORT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/report/v09_export_report.json')

report = {'tool': 'export_dana_clean_skin_v09_face_morphs.py', 'source_saved': False, 'stage': 'starting',
          'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    REPORT.write_text(json.dumps(report, indent=2, default=str))

def dag(name):
    s = om.MSelectionList(); s.add(name); return s.getDagPath(0)

def skinfn(name):
    s = om.MSelectionList(); s.add(name); return oma.MFnSkinCluster(s.getDependNode(0))

def component(n):
    f = om.MFnSingleIndexedComponent(); c = f.create(om.MFn.kMeshVertComponent); f.setCompleteData(n); return c

def pts(path):
    return cmds.xform(path + '.vtx[*]', query=True, worldSpace=True, translation=True)

def err_stats(a, b):
    """max and rms vertex distance (cm) between two flat world position lists."""
    mx = 0.0; s = 0.0; n = 0
    for i in range(0, len(a), 3):
        dx = a[i] - b[i]; dy = a[i + 1] - b[i + 1]; dz = a[i + 2] - b[i + 2]
        dd = dx * dx + dy * dy + dz * dz
        if dd > mx: mx = dd
        s += dd; n += 1
    return math.sqrt(mx), math.sqrt(s / n)

def tick():
    cmds.dgdirty(allPlugs=True)
    cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)

def find_animcurve(plug):
    """Resolve the animCurve driving a plug, walking through unitConversion nodes."""
    seen = set()
    stack = [plug]
    while stack:
        p = stack.pop()
        for src_plug in (cmds.listConnections(p, source=True, destination=False, plugs=True) or []):
            node = src_plug.rsplit('.', 1)[0]
            if node in seen: continue
            seen.add(node)
            t = cmds.nodeType(node)
            if t == 'animCurve':
                return node
            if t == 'unitConversion':
                stack.append(node + '.input')
    return None

# Identical mesh contract to v08 (paths + vertex counts from v08_report.json)
MESHES = {
    '|Group|Geometry|Dana_Body_GEO': 9249,
    '|Group|Geometry|Dana_Eyelashes_Lf_GEO': 39,
    '|Group|Geometry|Dana_Eyelashes_Rt_GEO': 39,
    '|Group|Geometry|Dana_Eye_Lf_GEO_GRP|Dana_Eye_Lf_GEO': 1121,
    '|Group|Geometry|Dana_Eye_Rt_GEO_GRP|Dana_Eye_Rt_GEO': 1121,
    '|Group|Geometry|Dana_Eye_Lf_GEO_GRP|Dana_Cornea_Lf_GEO': 161,
    '|Group|Geometry|Dana_Eye_Rt_GEO_GRP|Dana_Cornea_Rt_GEO': 161,
    '|Group|Geometry|Dana_Eye_Lf_GEO_GRP|Dana_EyeInt_Lf_GEO': 51,
    '|Group|Geometry|Dana_Eye_Rt_GEO_GRP|Dana_EyeInt_Rt_GEO': 51,
    '|Group|Geometry|Dana_Jeans_GEO': 2172,
    '|Group|Geometry|Dana_Shirt_GEO': 1564,
    '|Group|Geometry|Dana_Shoe_Lf_GEO': 1031,
    '|Group|Geometry|Dana_Shoe_Rt_GEO': 1031,
    '|Group|Geometry|Dana_Hair_Options_GRP|Dana_LongHair_GRP|Dana_LongHair_Bang_GEO': 474,
    '|Group|Geometry|Dana_Hair_Options_GRP|Dana_LongHair_GRP|Dana_LongHair_Main_GEO': 566,
    '|Group|Geometry|Dana_Lower_Teeth_GEO1': 2192,
    '|Group|Geometry|Dana_UpperTeeth_GEO': 2194,
    '|Group|Geometry|Dana_Tongue_GEO': 165,
    '|Group|Geometry|Dana_Eyebrows_GEO': 178,
}

try:
    if OUTPUT.exists():
        raise RuntimeError('Refusing to overwrite existing v09 candidate')
    report['source_sha256_before'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    cmds.file(str(SOURCE), open=True, force=True, ignoreVersion=True, executeScriptNodes=False,
              loadReferenceDepth='none', prompt=False)
    cmds.evaluationManager(mode='off'); cmds.currentTime(1, edit=True, update=True)

    # ---- verify the face morph system exists as measured by the census ----
    if not cmds.objExists('asFaceBS'):
        raise RuntimeError('asFaceBS blendShape missing; census out of date')
    aliases = cmds.aliasAttr('asFaceBS', query=True) or []
    alias_list = [aliases[i] for i in range(0, len(aliases), 2)]
    report['asFaceBS_channels_present'] = alias_list
    need = ['brow_raiser_L', 'brow_raiser_R', 'brow_outerRaiser_L', 'brow_outerRaiser_R',
            'brow_innerRaiser_L', 'brow_innerRaiser_R', 'brow_lowerer_L', 'brow_lowerer_R',
            'brow_innerLowerer_L', 'brow_innerLowerer_R', 'mouth_smile_C', 'mouth_smile_L',
            'mouth_smile_R', 'mouth_frown_L', 'mouth_frown_R', 'mouth_wide_L', 'mouth_wide_R']
    missing = [a for a in need if a not in alias_list]
    if missing:
        raise RuntimeError('Census channels missing from asFaceBS: %s' % missing)

    # ---- measure the jaw SDK domain: resolve its animCurve, else scan empirically ----
    jaw_curve = find_animcurve('FKSDK1Jaw_M.rotateX')
    if not jaw_curve:
        jaw_curve = find_animcurve('FKSDK1Jaw_M.rotate')
    report['jaw_sdk_curve'] = jaw_curve
    jaw_domain = None
    if jaw_curve:
        tc = cmds.keyframe(jaw_curve, query=True, timeChange=True) or []
        if tc:
            jaw_domain = (min(tc), max(tc))
    report['jaw_sdk_domain_translateY'] = jaw_domain
    jaw_original = cmds.getAttr('ctrlMouth_M.translateY')
    jaw_rest_rot = cmds.getAttr('Jaw_M.rotateX')
    jaw_pos = cmds.xform('Jaw_M', query=True, worldSpace=True, translation=True)
    def jaw_region_stats(flat, base):
        best = 0.0
        for i in range(0, len(flat), 3):
            dx0 = flat[i] - jaw_pos[0]; dy0 = flat[i + 1] - jaw_pos[1]; dz0 = flat[i + 2] - jaw_pos[2]
            if dx0 * dx0 + dy0 * dy0 + dz0 * dz0 < 225.0:
                dx = flat[i] - base[i]; dy = flat[i + 1] - base[i + 1]; dz = flat[i + 2] - base[i + 2]
                dd = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dd > best: best = dd
        return best
    body_base = pts('|Group|Geometry|Dana_Body_GEO')
    scan_values = [jaw_domain[0], jaw_domain[1]] if jaw_domain else []
    scan_values += [v for v in (-10.0, -8.0, -5.0, -3.0, -2.0, -1.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0)]
    jaw_candidates = []
    for v in sorted(set(round(float(x), 6) for x in scan_values)):
        cmds.setAttr('ctrlMouth_M.translateY', v); tick()
        rot = cmds.getAttr('Jaw_M.rotateX')
        jaw_candidates.append({'translateY': v,
                               'max_body_motion_cm': round(err_stats(pts('|Group|Geometry|Dana_Body_GEO'), body_base)[0], 4),
                               'jaw_region_motion_cm': round(jaw_region_stats(pts('|Group|Geometry|Dana_Body_GEO'), body_base), 4),
                               'Jaw_M_rotateX': rot,
                               'jaw_rot_delta': abs(rot - jaw_rest_rot)})
        cmds.setAttr('ctrlMouth_M.translateY', jaw_original); tick()
    report['jaw_probe'] = jaw_candidates
    # jaw open = extreme with the largest authored jaw rotation (SDK output), tiebreak on region motion
    live = [c for c in jaw_candidates if c['jaw_rot_delta'] > 0.01]
    if not live:
        raise RuntimeError('Jaw SDK scan produced no jaw rotation; wiring differs from census')
    best = max(live, key=lambda c: (c['jaw_rot_delta'], c['jaw_region_motion_cm']))
    jaw_open_value = best['translateY']
    report['jaw_open_value_used'] = jaw_open_value
    report['jaw_open_pose'] = best

    # ---- stage + exact mesh copies (v08 chain, with per-face material replication) ----
    cmds.namespace(add='FilmExport')
    stage = cmds.createNode('transform', name='FilmExport:RenderMeshes')
    head_inverse = om.MMatrix(cmds.xform('Head_M', query=True, worldSpace=True, matrix=True)).inverse()
    face_copies = {}
    def mapped_influence(path):
        if '|faceHeadJoint|' not in path: return path
        if path not in face_copies:
            name = path.rsplit('|', 1)[-1]
            joint = cmds.createNode('joint', name='FilmExport:Face_' + name, parent='Head_M')
            matrix = cmds.createNode('multMatrix', name='FilmExport:FaceSpace_' + name)
            cmds.connectAttr(path + '.worldMatrix[0]', matrix + '.matrixIn[0]')
            cmds.setAttr(matrix + '.matrixIn[1]', *list(head_inverse), type='matrix')
            cmds.connectAttr(matrix + '.matrixSum', joint + '.offsetParentMatrix')
            face_copies[path] = cmds.ls(joint, long=True)[0]
        return face_copies[path]

    report['meshes'] = []
    for path, count in MESHES.items():
        srcshape = (cmds.listRelatives(path, shapes=True, noIntermediate=True, fullPath=True, type='mesh') or [])[0]
        srcdag = dag(srcshape); srcmesh = om.MFnMesh(srcdag)
        if srcmesh.numVertices != count:
            raise RuntimeError('Source topology changed: ' + path)
        clusters = cmds.ls(cmds.listHistory(srcshape, pruneDagObjects=True) or [], type='skinCluster') or []
        if len(clusters) == 1:
            srcskin = skinfn(clusters[0]); influences = srcskin.influenceObjects()
            weights, n = srcskin.getWeights(srcdag, component(count))
        elif not clusters and path.endswith('|Dana_Eyebrows_GEO'):
            srcskin = None; influences = [dag('Head_M')]; weights = om.MDoubleArray([1.0] * count); n = 1
        else:
            raise RuntimeError('Ambiguous source skin history: ' + path)
        base_name = path.rsplit('|', 1)[-1]
        dup = cmds.createNode('transform', name='FilmExport:' + base_name, parent=stage)
        cmds.xform(dup, worldSpace=True, matrix=cmds.xform(path, query=True, worldSpace=True, matrix=True))
        dstobj = om.MFnMesh().copy(srcdag.node(), dag(dup).node())
        dstshape = om.MDagPath.getAPathTo(dstobj).fullPathName()
        mapped = [mapped_influence(p.fullPathName()) for p in influences]
        dupskin = cmds.skinCluster(mapped, dup, toSelectedBones=True, normalizeWeights=0,
                                   obeyMaxInfluences=False, name='FilmExport:' + base_name + '_Skin')[0]
        dstskin = skinfn(dupskin); dstinfs = dstskin.influenceObjects()
        source_columns = {p: i for i, p in enumerate(mapped)}
        order = [source_columns[p.fullPathName()] for p in dstinfs]
        copied = om.MDoubleArray([weights[v * n + j] for v in range(count) for j in order])
        dstskin.setWeights(dag(dstshape), component(count), om.MIntArray(list(range(len(order)))), copied, False)
        if clusters and cmds.objExists(clusters[0] + '.skinningMethod'):
            cmds.setAttr(dupskin + '.skinningMethod', cmds.getAttr(clusters[0] + '.skinningMethod'))
        dstskin.setBlendWeights(dag(dstshape), component(count),
                                srcskin.getBlendWeights(srcdag, component(count)) if srcskin else om.MDoubleArray([0.0] * count))
        actual, _ = dstskin.getWeights(dag(dstshape), component(count))
        delta = max(abs(a - b) for a, b in zip(actual, copied))
        if delta > 1e-12:
            raise RuntimeError('Native skin weight copy changed values: ' + path)
        for v in range(count):  # v08 transport cleanup: FBX drops tiny native weights
            row = copied[v * len(order):(v + 1) * len(order)]
            kept = [w if w >= 0.00101 else 0.0 for w in row]
            total = sum(kept)
            if total <= 0:
                raise RuntimeError('Transport cleanup would unweight a vertex')
            for j, w in enumerate(w / total for w in kept):
                copied[v * len(order) + j] = w
        dstskin.setWeights(dag(dstshape), component(count), om.MIntArray(list(range(len(order)))), copied, False)
        # --- per-face material replication (v09 change; v08 used sgs[0] only) ---
        # Reuse the NATIVE shading engines directly: exact material parity by
        # construction, and the FBX carries the native shader (material) names.
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
        mat_rows = []
        src_sges = shape_sges(srcshape)
        uses_lambert1 = False
        for sge in src_sges:
            shaders = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
            if not shaders: continue
            if shaders[0] == 'lambert1': uses_lambert1 = True
            for m in (cmds.sets(sge, query=True) or []):
                m = str(m)
                if m == base_name or m == srcshape.rsplit('|', 1)[-1]:
                    cmds.sets(dstshape, edit=True, forceElement=sge)
                    mat_rows.append({'shader': shaders[0], 'member': 'whole'})
                elif m.startswith(base_name + '.') or m.startswith(srcshape.rsplit('|', 1)[-1] + '.'):
                    suffix = m[m.index('.'):]
                    cmds.sets(dup + suffix, edit=True, forceElement=sge)
                    mat_rows.append({'shader': shaders[0], 'member': suffix})
        # drop default initialShadingGroup membership the fresh copy starts with
        if not uses_lambert1:
            try:
                cmds.sets(dstshape, edit=True, remove='initialShadingGroup')
            except Exception as e:
                report.setdefault('warnings', []).append('initialShadingGroup removal failed on %s: %s' % (path, e))
        dup_sges = [s for s in shape_sges(dstshape) if s.rsplit(':', 1)[-1] != 'initialShadingGroup']
        if not dup_sges:
            report['mat_debug_last'] = {'src_sges': src_sges, 'mat_rows': mat_rows,
                                        'src_members_sample': [str(m) for m in (cmds.sets(src_sges[0], query=True) or [])[:6]] if src_sges else None}
            raise RuntimeError('Material replication produced no shading engines: ' + path)
        report['meshes'].append({'source': path, 'copy': dup, 'vertices': count, 'source_skin': clusters[0] if clusters else None,
                                 'copied_skin': dupskin, 'influences': len(order), 'max_weight_delta': delta,
                                 'material_bindings': mat_rows, 'shading_engines_on_copy': len(dup_sges)})
        save()

    # ---- free asFaceBS channels from their SDK drivers so baked values survive eval ----
    # (the SDK curves rewrite the weights whenever the DG re-evaluates; scene is never saved)
    al = cmds.aliasAttr('asFaceBS', query=True) or []
    chan_plugs = [al[i + 1] for i in range(0, len(al), 2)]
    freed = []
    for cp in chan_plugs:
        plug = 'asFaceBS.' + cp
        for src in (cmds.listConnections(plug, source=True, destination=False, plugs=True, skipConversionNodes=False) or []):
            freed.append({'from': src, 'to': plug})
            cmds.disconnectAttr(src, plug)
    report['freed_channel_connections'] = freed
    if len(freed) < 40:
        report.setdefault('warnings', []).append('only %d of %d channels had SDK connections to free' % (len(freed), len(chan_plugs)))
    save()

    # ---- bake the 8 face morph targets on the body copy (v08 blink precedent, generalized) ----
    bodyrow = next(m for m in report['meshes'] if m['source'].endswith('|Dana_Body_GEO'))
    bodycopy = bodyrow['copy']
    srcbody = (cmds.listRelatives(bodyrow['source'], shapes=True, noIntermediate=True, fullPath=True, type='mesh'))[0]
    rest = pts(srcbody)
    MORPHS = [
        ('Blink_L', [('ctrlEye_L', 'blink', 10.0)]),
        ('Blink_R', [('ctrlEye_R', 'blink', 10.0)]),
        ('Brow_Up', [('asFaceBS', 'brow_raiser_L', 1.0), ('asFaceBS', 'brow_raiser_R', 1.0),
                     ('asFaceBS', 'brow_outerRaiser_L', 1.0), ('asFaceBS', 'brow_outerRaiser_R', 1.0),
                     ('asFaceBS', 'brow_innerRaiser_L', 1.0), ('asFaceBS', 'brow_innerRaiser_R', 1.0)]),
        ('Brow_Down', [('asFaceBS', 'brow_lowerer_L', 1.0), ('asFaceBS', 'brow_lowerer_R', 1.0),
                       ('asFaceBS', 'brow_innerLowerer_L', 1.0), ('asFaceBS', 'brow_innerLowerer_R', 1.0)]),
        ('Smile', [('asFaceBS', 'mouth_smile_C', 1.0), ('asFaceBS', 'mouth_smile_L', 1.0), ('asFaceBS', 'mouth_smile_R', 1.0)]),
        ('Frown', [('asFaceBS', 'mouth_frown_L', 1.0), ('asFaceBS', 'mouth_frown_R', 1.0)]),
        ('Mouth_Wide', [('asFaceBS', 'mouth_wide_L', 1.0), ('asFaceBS', 'mouth_wide_R', 1.0)]),
        ('Jaw_Open', [('ctrlMouth_M', 'translateY', jaw_open_value)]),
    ]
    blend = None
    report['morph_bakes'] = []
    for name, drivers in MORPHS:
        restore_stack = []
        applied = []
        for node, attr, value in drivers:
            plug = node + '.' + attr
            old = cmds.getAttr(plug)
            restore_stack.append((plug, old))
            cmds.setAttr(plug, value)
            applied.append({'plug': plug, 'value': value, 'readback': cmds.getAttr(plug)})
        tick()
        posed = pts(srcbody)
        motion = err_stats(posed, rest)[0]
        target = cmds.createNode('transform', name='FilmExport:MorphTarget_' + name, parent=stage)
        om.MFnMesh().copy(dag(srcbody).node(), dag(target).node())
        if blend is None:
            blend = cmds.blendShape(target, bodycopy, frontOfChain=True, name='FilmExport:FaceMorphs')[0]
            index = 0
        else:
            index = len(report['morph_bakes'])
            cmds.blendShape(blend, edit=True, target=(bodycopy, index, target, 1.0))
        cmds.aliasAttr(name, blend + '.weight[' + str(index) + ']')
        cmds.delete(target)
        report['morph_bakes'].append({'name': name, 'drivers': applied, 'source_motion_cm': round(motion, 4),
                                      'channel_index': index})
        for plug, old in restore_stack:
            cmds.setAttr(plug, old)
        tick()
        save()
    report['body_morph_node'] = blend
    for row in report['morph_bakes']:
        if row['source_motion_cm'] <= 0.05:
            raise RuntimeError('Degenerate morph delta: %s (%f cm)' % (row['name'], row['source_motion_cm']))
    # restore the SDK connections freed for baking (hygiene; scene is never saved)
    for row in freed:
        cmds.connectAttr(row['from'], row['to'], force=True)

    for curve in cmds.ls(type='nurbsCurve', long=True) or []:
        cmds.setAttr(curve + '.intermediateObject', True)
    cmds.loadPlugin('fbxmaya', quiet=True); mel.eval('FBXResetExport;')
    for s in ['FBXExportSkins -v true;', 'FBXExportShapes -v true;', 'FBXExportInputConnections -v false;',
              'FBXExportIncludeChildren -v false;', 'FBXExportConstraints -v false;', 'FBXExportCameras -v false;',
              'FBXExportLights -v false;', 'FBXExportEmbeddedTextures -v false;', 'FBXExportTriangulate -v false;']:
        mel.eval(s)
    cmds.select([m['copy'] for m in report['meshes']] + (cmds.ls(type='joint', long=True) or []),
                replace=True, noExpand=True)
    report['stage'] = 'exporting'; save()
    mel.eval('FBXExport -f "%s" -s;' % OUTPUT.as_posix())
    report['candidate_bytes'] = OUTPUT.stat().st_size

    # ---- FK regression: copy must track source through a head rotation (v08 test) ----
    baseline_all = {row['source']: pts(row['source']) for row in report['meshes']}
    old = cmds.getAttr('FKHead_M.rotateY')
    cmds.setAttr('FKHead_M.rotateY', 15.0); tick()
    fk_tests = []
    for row in report['meshes']:
        mx, rms = err_stats(pts(row['source']), pts(row['copy']))
        fk_tests.append({'mesh': row['source'].rsplit('|', 1)[-1], 'max_source_copy_error_cm': round(mx, 6),
                         'rms_error_cm': round(rms, 8)})
    report['fk_head15_copy_track'] = fk_tests
    cmds.setAttr('FKHead_M.rotateY', old); tick()
    worst = max(t['max_source_copy_error_cm'] for t in fk_tests)
    report['fk_head15_max_error_cm'] = worst
    if worst > 0.01:
        raise RuntimeError('Copy no longer tracks source under FK: %f cm' % worst)

    cmds.file(new=True, force=True)
    cmds.file(str(OUTPUT), open=True, force=True, ignoreVersion=True, executeScriptNodes=False, prompt=False)
    cmds.evaluationManager(mode='off')
    # ---- FBX readback: meshes, morphs, materials ----
    expected = {p.rsplit('|', 1)[-1]: n for p, n in MESHES.items()}
    expected_mesh_mats = {
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
    readback = {}
    for shape in cmds.ls(type='mesh', long=True) or []:
        if cmds.getAttr(shape + '.intermediateObject'): continue
        parent = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        name = parent.rsplit('|', 1)[-1].rsplit(':', 1)[-1]
        sge_rows = []
        for sge in (cmds.listConnections(shape, destination=False, source=True, type='shadingEngine') or []):
            shaders = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
            members = [str(m) for m in (cmds.sets(sge, query=True) or [])]
            sge_rows.append({'shading_engine': sge.rsplit(':', 1)[-1],
                             'shader': (shaders[0].rsplit(':', 1)[-1] if shaders else None),
                             'member_count': len(members),
                             'members_sample': [m for m in members if m.startswith(name) or m == parent.rsplit('|', 1)[-1]][:4]})
        readback[name] = {'shape': shape, 'vertices': cmds.polyEvaluate(shape, vertex=True),
                          'skins': cmds.ls(cmds.listHistory(shape, pruneDagObjects=True) or [], type='skinCluster') or [],
                          'shaders': sorted({s['shader'] for s in sge_rows if s['shader']})}
    report['readback'] = readback
    mat_fail = {name: {'expected': sorted(want), 'found': readback[name]['shaders']}
                for name, want in expected_mesh_mats.items()
                if name not in readback or not want.issubset(set(readback[name]['shaders']))}
    report['readback_material_fail'] = mat_fail
    # iris per-face split must exist on both eyeball meshes (member ranges recorded)
    iris_check = {}
    for name in ('Dana_Eye_Lf_GEO', 'Dana_Eye_Rt_GEO'):
        row = readback.get(name)
        iris_check[name] = {'total_faces': cmds.polyEvaluate(readback[name]['shape'], face=True) if row else None,
                            'shaders': row['shaders'] if row else None,
                            'sge_members': [s for s in (readback.get(name, {}).get('sge_detail') or [])] if False else None}
        if row:
            detail = []
            for sge in (cmds.listConnections(row['shape'], destination=False, source=True, type='shadingEngine') or []):
                shaders = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
                detail.append({'shader': (shaders[0].rsplit(':', 1)[-1] if shaders else None),
                               'members': [str(m) for m in (cmds.sets(sge, query=True) or [])]})
            iris_check[name]['sge_detail'] = detail
    report['iris_face_split_readback'] = iris_check
    # morphs on body
    mesh_tf = [t for t in (cmds.ls(type='transform', long=True) or [])
               if t.rsplit('|', 1)[-1].rsplit(':', 1)[-1] == 'Dana_Body_GEO']
    if len(mesh_tf) != 1: raise RuntimeError('Body mesh not unique in FBX readback')
    bodyshape = cmds.listRelatives(mesh_tf[0], shapes=True, noIntermediate=True, fullPath=True)[0]
    bs = cmds.ls(cmds.listHistory(bodyshape, pruneDagObjects=True) or [], type='blendShape') or []
    report['fbx_blendshape_nodes'] = bs
    morph_check = {'channels': [], 'deltas_cm': {}}
    if bs:
        al = cmds.aliasAttr(bs[0], query=True) or []
        amap = {al[i]: al[i + 1] for i in range(0, len(al), 2)} if al else {}
        morph_check['channels'] = sorted(amap.keys())
        restpts = pts(mesh_tf[0])
        for alias, plug in amap.items():
            cmds.setAttr(bs[0] + '.' + plug, 1.0); tick()
            morph_check['deltas_cm'][alias] = round(err_stats(pts(mesh_tf[0]), restpts)[0], 4)
            cmds.setAttr(bs[0] + '.' + plug, 0.0); tick()
    report['fbx_morph_check'] = morph_check
    report['readback_mesh_pass'] = all(name in readback and readback[name]['vertices'] == n and readback[name]['skins']
                                       for name, n in expected.items()) and set(readback) == set(expected)
    want_channels = {'Blink_L', 'Blink_R', 'Brow_Up', 'Brow_Down', 'Smile', 'Frown', 'Mouth_Wide', 'Jaw_Open'}
    report['fbx_morph_pass'] = bool(morph_check['channels']) and set(morph_check['channels']) == want_channels \
        and all(v > 0.05 for v in morph_check['deltas_cm'].values()) and not mat_fail
    report['source_sha256_after'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report['source_unchanged'] = report['source_sha256_before'] == report['source_sha256_after']
    report['stage'] = 'v09_export_checked'; save()
    print(json.dumps({'stage': report['stage'], 'readback_mesh_pass': report['readback_mesh_pass'],
                      'fbx_morph_pass': report['fbx_morph_pass'], 'morph_deltas_cm': morph_check['deltas_cm'],
                      'iris_face_split_readback': iris_check, 'material_fail': mat_fail,
                      'jaw_open_value': jaw_open_value, 'source_unchanged': report['source_unchanged']}))
except Exception:
    report['stage'] = 'blocked'; report['error'] = traceback.format_exc(); save(); print(report['error']); raise
finally:
    try:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass
