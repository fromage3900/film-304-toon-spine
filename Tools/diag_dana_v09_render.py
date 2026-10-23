"""Diagnostic: why are v09 preview renders black? Reports visibility/layer state,
renders 64x64 probes from the look-at camera and persp with a gray background.
"""
import json, glob, traceback
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
import maya.api.OpenMaya as om

OUTPUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
PREVIEW = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/preview')
PREVIEW.mkdir(parents=True, exist_ok=True)
r = {'stage': 'starting'}

def short(n): return n.rsplit('|', 1)[-1].rsplit(':', 1)[-1]

try:
    cmds.loadPlugin('fbxmaya', quiet=True)
    cmds.file(str(OUTPUT), open=True, force=True, ignoreVersion=True, executeScriptNodes=False, prompt=False)
    # display layers
    layers = cmds.ls(type='displayLayer', long=True) or []
    r['display_layers'] = []
    for lay in layers:
        vis = None
        try: vis = cmds.getAttr(lay + '.visibility')
        except Exception: pass
        r['display_layers'].append({'layer': short(lay), 'visibility': vis})
    # mesh visibility
    r['mesh_visibility'] = []
    for t in (cmds.ls(type='transform', long=True) or []):
        if short(t) == 'Dana_Body_GEO':
            shape = cmds.listRelatives(t, shapes=True, noIntermediate=True, fullPath=True)[0]
            r['mesh_visibility'].append({'mesh': short(t),
                                         'tf_visible': cmds.getAttr(t + '.visibility'),
                                         'shape_visible': cmds.getAttr(shape + '.visibility'),
                                         'tf_layered_draw_override': cmds.listConnections(t + '.drawOverride', source=True) or [],
                                         'shape_layered_draw_override': cmds.listConnections(shape + '.drawOverride', source=True) or []})
    # force everything visible
    for lay in layers:
        if short(lay) != 'defaultLayer':
            cmds.setAttr(lay + '.visibility', 1)
    for t in (cmds.ls(type='transform', long=True) or []):
        if short(t) == 'Dana_Body_GEO':
            shape = cmds.listRelatives(t, shapes=True, noIntermediate=True, fullPath=True)[0]
            cmds.setAttr(t + '.visibility', 1); cmds.setAttr(shape + '.visibility', 1)
    # lights + gray background camera setup
    key = cmds.directionalLight(rgb=(1, 1, 1), intensity=2.0)
    amb = cmds.ambientLight(rgb=(0.5, 0.5, 0.5), intensity=1.0)
    # camera A: look-at from measured anchors
    def joint_pos(n):
        hits = [j for j in (cmds.ls(type='joint', long=True) or []) if short(j) == n]
        return cmds.xform(hits[0], query=True, worldSpace=True, translation=True) if hits else None
    el, er, hd = joint_pos('Eye_L'), joint_pos('Eye_R'), joint_pos('Head_M')
    eye_mid = om.MVector((el[0] + er[0]) / 2, (el[1] + er[1]) / 2, (el[2] + er[2]) / 2)
    fwd = (eye_mid - om.MVector(*hd)).normal()
    up = om.MVector(0, 1, 0)
    right = (fwd ^ up).normal(); tup = (right ^ fwd).normal()
    pos = eye_mid + fwd * 30.0
    m = om.MMatrix([right.x, right.y, right.z, 0, tup.x, tup.y, tup.z, 0,
                    -fwd.x, -fwd.y, -fwd.z, 0, pos.x, pos.y, pos.z, 1])
    cam_tf, cam_sh = cmds.camera(name='DiagCam', focalLength=50)
    cmds.xform(cam_tf, worldSpace=True, matrix=list(m))
    cmds.setAttr(cam_sh + '.renderable', 1)
    cmds.setAttr(cam_sh + '.backgroundColor', 0.25, 0.25, 0.25, type='float3')
    try: cmds.setAttr(cam_sh + '.autoRenderClip', 0)
    except Exception as e: r['autoRenderClip'] = 'no attr: %s' % e
    cmds.setAttr(cam_sh + '.nearClipPlane', 1.0); cmds.setAttr(cam_sh + '.farClipPlane', 500.0)
    r['camera_a'] = {'pos': [round(v, 2) for v in (pos.x, pos.y, pos.z)],
                     'fwd': [round(v, 3) for v in (fwd.x, fwd.y, fwd.z)],
                     'world_matrix_now': [round(v, 2) for v in cmds.xform(cam_tf, query=True, worldSpace=True, matrix=True)]}
    # camera B: persp
    persp_sh = 'perspShape'
    cmds.setAttr(persp_sh + '.renderable', 1)
    cmds.setAttr(persp_sh + '.backgroundColor', 0.25, 0.25, 0.25, type='float3')
    # render settings
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware', type='string')
    cmds.setAttr('defaultRenderGlobals.imageFormat', 32)
    cmds.setAttr('defaultResolution.width', 64)
    cmds.setAttr('defaultResolution.height', 64)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 1.0)
    cmds.workspace(fileRule=['images', PREVIEW.as_posix()])
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', 'diag_lookat', type='string')
    cmds.render(cam_sh)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', 'diag_persp', type='string')
    cmds.render(persp_sh)
    r['files'] = {p.name: p.stat().st_size for p in PREVIEW.rglob('diag_*')}
    r['stage'] = 'done'
    print(json.dumps(r, indent=1, default=str))
except Exception:
    r['stage'] = 'blocked'; r['error'] = traceback.format_exc(); print(r['error']); raise
finally:
    try:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass
