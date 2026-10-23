"""Task1 face/eye census of the native Dana rig (read-only, runs on a scratch copy).

Extends Tools/inspect_dana_native_maya.py (same open + never-save pattern) with:
  - blendShape census (nodes, base meshes, aliases, target shapes, weight ranges)
  - setDrivenKey (SDK) wiring census: driver plug -> driven plug for face systems
  - face-control attribute census (keyword-matched, with value ranges)
  - full material inventory: every render mesh -> ALL shading engines -> shader
    node type + color/transparency file textures + per-face member lists for
    small meshes (detects per-face material splits such as sclera/iris)
  - eye bone census (Eye/Iris/Pupil L/R): world matrices, constraints
  - per-candidate-control mesh movement probe: which render meshes move and by
    how many cm when the control is driven to its extreme, then restored
  - face anchor positions (head/eye joints, body bbox) for preview camera work

The scene is opened from argv[1] (scratch copy), never saved, and the file is
SHA256-hashed before/after. Results go to <argv2>/inspection_face_eyes.json.
"""
import json, hashlib, traceback, datetime, sys, math
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

r = {'tool': 'inspect_dana_face_eyes_task1.py', 'source': str(SOURCE),
     'source_saved': False, 'scene_scripts_enabled': False, 'stage': 'starting',
     'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    (OUT / 'inspection_face_eyes.json').write_text(json.dumps(r, indent=2, default=str))

save()

# The 19 render meshes the v08 chain exports (paths + vertex counts from v08_report.json)
EXPORT_MESHES = {
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
BUILTIN_ATTRS = {'translateX','translateY','translateZ','rotateX','rotateY','rotateZ',
                 'scaleX','scaleY','scaleZ','visibility','tx','ty','tz','rx','ry','rz',
                 'sx','sy','sz','v','shearXY','shearXZ','shearYZ'}
FACE_KEYS = ['blink','brow','smile','frown','jaw','mouth','wide','squint','look','aim',
             'open','close','lid','sneer','pucker','cheek','snarl','grin','sad','pout',
             'lips','teeth','tongue','nose','eye','visor']

try:
    r['source_sha256_before'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    import maya.standalone
    r['stage'] = 'initializing_maya'; save()
    maya.standalone.initialize(name='python')
    from maya import cmds
    import maya.api.OpenMaya as om
    r['maya_version'] = cmds.about(version=True)

    r['stage'] = 'opening_scene'; save()
    cmds.file(str(SOURCE), open=True, force=True, ignoreVersion=True,
              executeScriptNodes=False, loadReferenceDepth='none', prompt=False)
    cmds.evaluationManager(mode='off')
    cmds.currentTime(1, edit=True, update=True)
    r['references'] = cmds.file(query=True, reference=True) or []
    r['joints_total'] = len(cmds.ls(type='joint') or [])
    r['mesh_shapes_total'] = len(cmds.ls(type='mesh', long=True) or [])

    # ---------- 1. blendShape census ----------
    r['stage'] = 'census_blendshapes'; save()
    def bs_targets(bs, amap):
        out = []
        for wa in [a for a in (cmds.listAttr(bs, multi=True) or []) if a.startswith('weight[')]:
            idx = wa[len('weight['):-1]
            row = {'weight_index': int(idx), 'alias': amap.get(wa)}
            for item, label in ((600, 'target_at_1.0'), (-600, 'target_at_-1.0'), (500, 'target_at_0.5')):
                plug = '%s.inputTarget[0].inputTargetGroup[%s].inputTargetItem[%d].inputGeomTarget' % (bs, idx, item)
                try:
                    conns = cmds.listConnections(plug, source=True, destination=False, shapes=True) or []
                except Exception:
                    conns = []
                if conns: row[label] = conns[0]
            try:
                row['default_value'] = cmds.getAttr('%s.%s' % (bs, wa))
            except Exception:
                pass
            out.append(row)
        return out
    bss = []
    for bs in cmds.ls(type='blendShape', long=True) or []:
        entry = {'node': bs, 'short': bs.rsplit('|', 1)[-1]}
        try: entry['envelope'] = cmds.getAttr(bs + '.envelope')
        except Exception: pass
        try: entry['base_meshes'] = cmds.blendShape(bs, query=True, geometry=True) or []
        except Exception: entry['base_meshes'] = None
        try: entry['target_query_raw'] = cmds.blendShape(bs, query=True, target=True) or []
        except Exception: entry['target_query_raw'] = None
        aliases = cmds.aliasAttr(bs, query=True) or []
        amap = {aliases[i+1]: aliases[i] for i in range(0, len(aliases), 2)} if aliases else {}
        entry['aliases'] = amap
        entry['targets'] = bs_targets(entry['short'], amap)
        entry['feeds'] = cmds.listConnections(bs + '.outputGeometry', destination=True, source=False, shapes=True) or []
        bss.append(entry)
    r['blendshapes'] = bss
    r['blendshape_count'] = len(bss)
    save()

    # ---------- 2. SDK / animCurve wiring census ----------
    r['stage'] = 'census_sdk_wiring'; save()
    curves = cmds.ls(type='animCurve', long=True) or []
    r['animcurve_total'] = len(curves)
    face_rows = []; ctrl_driven = []; type_hist = {}
    for c in curves:
        t = cmds.nodeType(c)
        type_hist[t] = type_hist.get(t, 0) + 1
        try:
            src = cmds.listConnections(c, source=True, destination=False, plugs=True) or []
            dst = cmds.listConnections(c, source=False, destination=True, plugs=True) or []
        except Exception:
            continue
        if not dst: continue
        drv = src[0] if src else None
        row = {'curve': c.rsplit('|', 1)[-1], 'curve_type': t, 'driver': drv, 'driven': dst}
        blob = ' '.join(dst) + ' ' + (drv or '')
        low = blob.lower()
        if drv and drv.split('.')[0].rsplit('|', 1)[-1].lower().startswith(('ctrl', 'lidgetup', 'lidsetup')):
            ctrl_driven.append(row)
        if 'facegroup' in low or 'face' in low:
            face_rows.append(row)
    r['sdk_face_related'] = face_rows
    r['sdk_face_related_count'] = len(face_rows)
    r['sdk_ctrl_driven'] = ctrl_driven
    r['sdk_ctrl_driven_count'] = len(ctrl_driven)
    r['animcurve_type_histogram'] = type_hist
    save()

    # ---------- 3. face-control attribute census ----------
    r['stage'] = 'census_face_controls'; save()
    controls = {}
    def attr_range(node, a):
        rng = {}
        for key, flag in (('min', 'minValue'), ('max', 'maxValue')):
            try:
                v = cmds.addAttr('%s.%s' % (node, a), query=True, **{flag: True})
                if v is not None: rng[key] = v
            except Exception:
                pass
        return rng
    for tr in cmds.ls(transforms=True, long=True) or []:
        short = tr.rsplit('|', 1)[-1]
        try:
            custom = [a for a in (cmds.listAttr(tr, keyable=True) or []) if a not in BUILTIN_ATTRS]
        except Exception:
            continue
        if not custom: continue
        lowblob = ' '.join(a.lower() for a in custom)
        if not (any(any(k in a for k in FACE_KEYS) for a in lowblob.split()) or 'ctrl' in short.lower()
                or 'FaceGroup' in tr or 'LidSetup' in short):
            continue
        detail = {}
        for a in custom:
            row = {'current': None, 'range': attr_range(short, a)}
            try: row['current'] = cmds.getAttr(tr + '.' + a)
            except Exception: pass
            detail[a] = row
        controls[tr] = detail
    r['face_controls'] = controls
    r['face_control_count'] = len(controls)
    save()

    # ---------- 4. material inventory ----------
    r['stage'] = 'census_materials'; save()
    mat_rows = []
    for shape in cmds.ls(type='mesh', long=True) or []:
        if cmds.getAttr(shape + '.intermediateObject'): continue
        sges = []
        try: sges = cmds.listConnections(shape, destination=False, source=True, type='shadingEngine') or []
        except Exception: pass
        try: sges = list(set(sges) | set(cmds.listSets(object=shape, type=1) or []))
        except Exception: pass
        sges = [s for s in sges if cmds.nodeType(s) == 'shadingEngine']
        srows = []
        for sge in sorted(set(sges)):
            srow = {'shading_engine': sge}
            shaders = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
            sh = shaders[0] if shaders else None
            srow['shader'] = sh; srow['shader_type'] = cmds.nodeType(sh) if sh else None
            if sh:
                for plug in ('color', 'transparency', 'incandescence'):
                    try:
                        files = cmds.listConnections(sh + '.' + plug, source=True, destination=False, type='file') or []
                    except Exception:
                        files = []
                    if files:
                        srow[plug + '_textures'] = [{'node': f.rsplit('|', 1)[-1],
                                                     'path': cmds.getAttr(f + '.fileTextureName')} for f in files]
            try:
                members = cmds.sets(sge, query=True) or []
                srow['member_count'] = len(members)
                if len(members) <= 8:
                    srow['members'] = [str(m) for m in members]
            except Exception:
                pass
            srows.append(srow)
        mat_rows.append({'shape': shape, 'vertices': cmds.polyEvaluate(shape, vertex=True),
                         'shading_engines': srows})
    r['material_inventory'] = mat_rows
    save()

    # ---------- 5. eye bones + constraints ----------
    r['stage'] = 'census_eye_bones'; save()
    eye_names = {'Eye_L', 'Eye_R', 'Iris_L', 'Iris_R', 'Pupil_L', 'Pupil_R'}
    eye_rows = []
    for j in cmds.ls(type='joint', long=True) or []:
        short = j.rsplit('|', 1)[-1].rsplit(':', 1)[-1]
        if short in eye_names:
            cons = [n for n in (cmds.listConnections(j, source=True, destination=False) or [])
                    if cmds.nodeType(n).endswith('Constraint')]
            eye_rows.append({'joint': j, 'parent': (cmds.listRelatives(j, parent=True, fullPath=True) or [None])[0],
                             'world_matrix': [round(x, 6) for x in cmds.xform(j, query=True, worldSpace=True, matrix=True)],
                             'constraints': cons})
    r['eye_bones'] = eye_rows
    r['face_joints'] = [j for j in (cmds.ls(type='joint', long=True) or []) if 'FaceGroup' in j]
    r['face_joint_count'] = len(r['face_joints'])
    anchors = {}
    for want in ('Head_M', 'Eye_L', 'Eye_R', 'Jaw_M'):
        hits = [j for j in (cmds.ls(type='joint', long=True) or [])
                if j.rsplit('|', 1)[-1].rsplit(':', 1)[-1] == want]
        if hits:
            pos = cmds.xform(hits[0], query=True, worldSpace=True, translation=True)
            anchors[want] = {'path': hits[0], 'world_position_cm': [round(p, 4) for p in pos]}
    r['face_anchors'] = anchors
    try:
        bb = cmds.exactWorldBoundingBox('|Group|Geometry|Dana_Body_GEO')
        r['body_world_bbox_cm'] = [round(v, 3) for v in bb]
    except Exception:
        r['body_world_bbox_cm'] = None
    save()

    # ---------- 6. per-control mesh movement probe ----------
    r['stage'] = 'probe_control_motion'; save()
    def pts(path):
        return cmds.xform(path + '.vtx[*]', query=True, worldSpace=True, translation=True)
    baseline = {}
    for p in EXPORT_MESHES:
        if cmds.objExists(p): baseline[p] = pts(p)
    r['probe_baseline_meshes'] = len(baseline)
    def maxdelta(a, b):
        d = 0.0
        for i in range(0, len(a), 3):
            dx = a[i] - b[i]; dy = a[i+1] - b[i+1]; dz = a[i+2] - b[i+2]
            dd = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dd > d: d = dd
        return d
    # build candidate plug list: custom keyable attrs on ctrl-like nodes, keyword-matched
    candidates = []
    seen = set()
    for tr, detail in controls.items():
        for a in detail:
            low = a.lower()
            if any(k in low for k in FACE_KEYS):
                plug = tr + '.' + a
                if plug not in seen:
                    seen.add(plug); candidates.append(plug)
    r['probe_candidate_count'] = len(candidates)
    probes = []
    for plug in candidates:
        row = {'plug': plug}
        try:
            if not cmds.getAttr(plug, settable=True):
                row['skipped'] = 'not settable'; probes.append(row); continue
            cur = cmds.getAttr(plug)
            node, a = plug.rsplit('.', 1)
            rng = attr_range(node, a)
            # choose drive value: known max if defined, else 10 for blink family (native closed), else 1.0
            if 'max' in rng and float(rng['max']) != 0: value = float(rng['max'])
            elif 'blink' in a.lower(): value = 10.0
            else: value = 1.0
            row['value'] = value
            if cur == value:
                value = value * 0.9 if value else 1.0
                row['value'] = value
            cmds.setAttr(plug, value); cmds.dgdirty(allPlugs=True)
            cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)
            deltas = {}
            for p, base in baseline.items():
                d = maxdelta(pts(p), base)
                if d > 0.005: deltas[p.rsplit('|', 1)[-1]] = round(d, 4)
            row['movers_cm'] = deltas
            row['max_motion_cm'] = round(max(deltas.values()), 4) if deltas else 0.0
            cmds.setAttr(plug, cur); cmds.dgdirty(allPlugs=True)
            cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)
            # confirm restoration
            back = maxdelta(pts('|Group|Geometry|Dana_Body_GEO'), baseline['|Group|Geometry|Dana_Body_GEO']) if '|Group|Geometry|Dana_Body_GEO' in baseline else None
            row['restored_max_residual_cm'] = round(back, 6) if back is not None else None
        except Exception as e:
            row['error'] = str(e)
            try:
                cmds.setAttr(plug, cur); cmds.dgdirty(allPlugs=True)
                cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)
            except Exception:
                pass
        probes.append(row)
        if len(probes) % 5 == 0: save()
    r['control_motion_probe'] = probes
    r['stage'] = 'census_complete'; save()

    r['source_sha256_after'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    r['source_unchanged'] = r['source_sha256_before'] == r['source_sha256_after']
    print(json.dumps({'stage': r['stage'], 'blendshape_count': r['blendshape_count'],
                      'sdk_face_related': r['sdk_face_related_count'], 'sdk_ctrl_driven': r['sdk_ctrl_driven_count'],
                      'face_control_count': r['face_control_count'], 'joints': r['joints_total'],
                      'source_unchanged': r['source_unchanged']}))
except Exception:
    r['stage'] = 'blocked'; r['error'] = traceback.format_exc(); save(); print(r['error'])
finally:
    try:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass
