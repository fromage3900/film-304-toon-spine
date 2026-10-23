"""Render Dana v09 face-morph preview PNGs from the exported FBX (scratch scene only).

Opens fbx/Dana_CleanSkin_v09.fbx in mayapy, sets requested morph channels to
1.0, aims a camera at the measured eye midpoint, and renders with the Maya
Software renderer to task1_face_eyes/preview/. Also renders rest + per-shape
singles. Untextured imported shaders get flat readable lambert colors
(session-only presentation; nothing is saved into any source location).

Run:  mayapy.exe render_dana_v09_preview_task1.py
"""
import json, glob, math, traceback, datetime
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
import maya.api.OpenMaya as om

OUTPUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
PREVIEW = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/preview')
REPORT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/report/v09_preview_report.json')
PREVIEW.mkdir(parents=True, exist_ok=True)

SHOTS = {
    'face_rest': [],
    'face_blink_L_browUp_jawOpen': [('Blink_L', 1.0), ('Brow_Up', 1.0), ('Jaw_Open', 1.0)],
    'face_blink_L': [('Blink_L', 1.0)],
    'face_brow_up': [('Brow_Up', 1.0)],
    'face_jaw_open': [('Jaw_Open', 1.0)],
    'face_smile': [('Smile', 1.0)],
}
COLORS = {  # flat presentation colors by FBX material name (session-only)
    'danaSkin_mat': (0.93, 0.78, 0.68), 'danaHair_mat': (0.25, 0.16, 0.10),
    'danaEye_mat': (0.95, 0.95, 0.94), 'danaIris_mat': (0.28, 0.15, 0.06),
    'danaCornea_mat': (0.85, 0.92, 0.95), 'danaEyeInt_mat': (0.10, 0.02, 0.02),
    'danaPants_mat': (0.25, 0.32, 0.55), 'danaShirt_mat': (0.35, 0.62, 0.60),
    'danaShoes_mat': (0.20, 0.18, 0.17), 'danaTeeth_mat': (0.96, 0.95, 0.90),
    'danaGum_mat': (0.85, 0.55, 0.55), 'danaTongue_mat': (0.88, 0.50, 0.50),
}
TRANSPARENCY = {'danaCornea_mat': 0.92}  # clear cornea so the iris reads through

r = {'tool': 'render_dana_v09_preview_task1.py', 'source': str(OUTPUT), 'stage': 'starting',
     'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    REPORT.write_text(json.dumps(r, indent=2, default=str))

def short(n):
    return n.rsplit('|', 1)[-1].rsplit(':', 1)[-1]

def tick():
    cmds.dgdirty(allPlugs=True)
    cmds.currentTime(2, edit=True, update=True); cmds.currentTime(1, edit=True, update=True)

try:
    cmds.loadPlugin('fbxmaya', quiet=True)
    cmds.file(str(OUTPUT), open=True, force=True, ignoreVersion=True, executeScriptNodes=False, prompt=False)
    cmds.evaluationManager(mode='off')
    r['stage'] = 'opened'; save()

    # ---- flat readable colors for ALL imported shaders (session-only presentation;
    # native texture paths do not resolve in the scratch scene and render black) ----
    recolored = []
    for sge in (cmds.ls(type='shadingEngine', long=True) or []):
        sh = cmds.listConnections(sge + '.surfaceShader', source=True, destination=False) or []
        if not sh: continue
        name = short(sh[0])
        if name in COLORS:
            lambert = cmds.shadingNode('lambert', asShader=True, name='Task1Preview_' + name)
            cmds.setAttr(lambert + '.color', *COLORS[name], type='float3')
            if name in TRANSPARENCY:
                t = TRANSPARENCY[name]
                cmds.setAttr(lambert + '.transparency', t, t, t, type='float3')
            cmds.connectAttr(lambert + '.outColor', sge + '.surfaceShader', force=True)
            recolored.append({'shading_engine': short(sge), 'was': name, 'flat_color': lambert})
    r['recolored'] = recolored; save()

    # ---- find body mesh + morph channels ----
    tf = [t for t in (cmds.ls(type='transform', long=True) or []) if short(t) == 'Dana_Body_GEO'][0]
    shape = cmds.listRelatives(tf, shapes=True, noIntermediate=True, fullPath=True)[0]
    bs = cmds.ls(cmds.listHistory(shape, pruneDagObjects=True) or [], type='blendShape') or []
    if not bs:
        raise RuntimeError('No blendShape on imported body mesh')
    al = cmds.aliasAttr(bs[0], query=True) or []
    amap = {al[i]: al[i + 1] for i in range(0, len(al), 2)} if al else {}
    r['morph_channels'] = sorted(amap.keys())

    def set_morphs(values):
        for alias, plug in amap.items():
            target = dict(values).get(alias, 0.0)
            cmds.setAttr(bs[0] + '.' + plug, target)
        tick()

    def body_state():
        v = cmds.xform(tf + '.vtx[*]', query=True, worldSpace=True, translation=True)
        return v

    # ---- camera from measured face anchors (euler only; matrix look-at proved empty) ----
    def joint_pos(short_name):
        hits = [j for j in (cmds.ls(type='joint', long=True) or []) if short(j) == short_name]
        return cmds.xform(hits[0], query=True, worldSpace=True, translation=True) if hits else None
    eye_l = joint_pos('Eye_L'); eye_r = joint_pos('Eye_R'); head = joint_pos('Head_M')
    if not (eye_l and eye_r and head):
        raise RuntimeError('Face anchor joints not found in FBX: %s %s %s' % (eye_l, eye_r, head))
    eye_mid = ((eye_l[0] + eye_r[0]) / 2, (eye_l[1] + eye_r[1]) / 2, (eye_l[2] + eye_r[2]) / 2)
    # camera above-front of the eyes, pitched down to aim at the measured eye midpoint
    cam_pos = (eye_mid[0], eye_mid[1] + 6.0, eye_mid[2] + 30.0)
    dy = eye_mid[1] - cam_pos[1]; dz = eye_mid[2] - cam_pos[2]
    pitch = math.degrees(math.atan2(dy, -dz))
    cam_tf, cam_sh = cmds.camera(name='Task1PreviewCam', focalLength=50)
    cmds.setAttr(cam_sh + '.renderable', 1)
    cmds.setAttr(cam_sh + '.backgroundColor', 0.25, 0.25, 0.25, type='float3')
    try: cmds.setAttr(cam_sh + '.bestFitClippingPlanes', 0)
    except Exception as e: r.setdefault('warnings', []).append('bestFit: %s' % e)
    cmds.setAttr(cam_sh + '.nearClipPlane', 1.0); cmds.setAttr(cam_sh + '.farClipPlane', 500.0)
    cmds.setAttr(cam_tf + '.translate', *cam_pos)
    cmds.setAttr(cam_tf + '.rotate', pitch, 0, 0)
    r['camera'] = {'eye_mid_cm': [round(v, 3) for v in eye_mid],
                   'position_cm': [round(v, 3) for v in cam_pos],
                   'pitch_deg': round(pitch, 3)}
    # lights
    key = cmds.directionalLight(rgb=(1, 1, 1), intensity=2.2)
    key_tf = cmds.listRelatives(key, parent=True)[0]
    cmds.setAttr(key_tf + '.rotate', -35, 25, 0)
    fill = cmds.directionalLight(rgb=(0.6, 0.7, 0.9), intensity=0.8)
    fill_tf = cmds.listRelatives(fill, parent=True)[0]
    cmds.setAttr(fill_tf + '.rotate', 40, -30, 0)
    cmds.ambientLight(rgb=(0.45, 0.45, 0.45), intensity=0.9)
    r['stage'] = 'render_setup'; save()

    # ---- render globals: mayaSoftware, PNG (index parsed from enum + probe-confirmed) ----
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware', type='string')
    enum_raw = cmds.attributeQuery('imageFormat', node='defaultRenderGlobals', listEnum=True)
    enum_str = ':'.join(enum_raw) if isinstance(enum_raw, list) else str(enum_raw)
    png_value = None
    counter = 0
    for part in enum_str.split(':'):
        name = part
        if '=' in part:
            name, _, val = part.partition('=')
            counter = int(val)
        if name.strip().upper() == 'PNG':
            png_value = counter
        counter += 1
    if png_value is None:
        raise RuntimeError('PNG not found in imageFormat enum: ' + enum_str)
    cmds.setAttr('defaultResolution.width', 64)
    cmds.setAttr('defaultResolution.height', 64)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 1.0)
    cmds.workspace(fileRule=['images', PREVIEW.as_posix()])
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', 'task1_fmt_probe', type='string')
    cmds.setAttr('defaultRenderGlobals.imageFormat', png_value)
    for old in glob.glob(str(PREVIEW / '**' / 'task1_fmt_probe*'), recursive=True):
        Path(old).unlink()
    cmds.render(cam_sh)
    made = glob.glob(str(PREVIEW / '**' / 'task1_fmt_probe*'), recursive=True)
    if not any(p.lower().endswith('.png') for p in made):
        raise RuntimeError('imageFormat=%d did not produce a .png (made=%s)' % (png_value, made))
    for old in made:
        Path(old).unlink()
    cmds.setAttr('defaultResolution.width', 800)
    cmds.setAttr('defaultResolution.height', 800)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 1.0)
    r['png_format_index'] = png_value
    r['workspace_images_dir'] = PREVIEW.as_posix(); save()

    # ---- render shots ----
    rest = body_state()
    results = {}
    def err_max(a, b):
        mx = 0.0
        for i in range(0, len(a), 3):
            dx = a[i] - b[i]; dy = a[i + 1] - b[i + 1]; dz = a[i + 2] - b[i + 2]
            dd = dx * dx + dy * dy + dz * dz
            if dd > mx: mx = dd
        return math.sqrt(mx)
    for shot, values in SHOTS.items():
        set_morphs(values)
        delta = round(err_max(body_state(), rest), 4)
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', shot, type='string')
        cmds.render(cam_sh)
        produced = sorted(glob.glob(str(PREVIEW / '**' / (shot + '*')), recursive=True))
        results[shot] = {'morphs': values, 'body_delta_cm': delta,
                         'files': [Path(p).name for p in produced],
                         'paths': produced,
                         'bytes': [Path(p).stat().st_size for p in produced]}
        r['shots'] = results; save()
    set_morphs([])
    r['stage'] = 'rendered'
    r['all_pngs_present'] = all(results[s]['files'] for s in results)
    r['stage_note'] = 'PNGs rendered from the exported v09 FBX with the Maya Software renderer'
    save()
    print(json.dumps({'stage': r['stage'], 'morph_channels': r['morph_channels'], 'camera': r['camera'],
                      'shots': results, 'all_pngs_present': r['all_pngs_present']}))
except Exception:
    r['stage'] = 'blocked'; r['error'] = traceback.format_exc(); save(); print(r['error']); raise
finally:
    try:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass
