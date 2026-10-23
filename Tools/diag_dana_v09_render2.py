"""Diagnostic #2: body bbox in the FBX scene, clip-attr census, and two simple
euler-rotation camera probes (no look-at matrix math).
"""
import json, glob, traceback
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds

OUTPUT = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx')
PREVIEW = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/preview')
r = {'stage': 'starting'}
def short(n): return n.rsplit('|', 1)[-1].rsplit(':', 1)[-1]

try:
    cmds.loadPlugin('fbxmaya', quiet=True)
    cmds.file(str(OUTPUT), open=True, force=True, ignoreVersion=True, executeScriptNodes=False, prompt=False)
    tf = [t for t in (cmds.ls(type='transform', long=True) or []) if short(t) == 'Dana_Body_GEO'][0]
    bb = cmds.exactWorldBoundingBox(tf)
    r['body_bbox_fbx_scene'] = [round(v, 3) for v in bb]
    def joint_pos(n):
        hits = [j for j in (cmds.ls(type='joint', long=True) or []) if short(j) == n]
        return [round(v, 3) for v in cmds.xform(hits[0], query=True, worldSpace=True, translation=True)] if hits else None
    r['anchors'] = {n: joint_pos(n) for n in ('Head_M', 'Eye_L', 'Eye_R')}
    r['camera_clip_attrs'] = cmds.listAttr('Task1PreviewCamShape' if cmds.objExists('Task1PreviewCamShape') else 'perspShape', string='*lip*') if True else []
    r['globals_clip_attrs'] = cmds.listAttr('defaultRenderGlobals', string='*lip*') or []
    # lights
    key = cmds.directionalLight(rgb=(1, 1, 1), intensity=2.0)
    key_tf = cmds.listRelatives(key, parent=True)[0]
    cmds.setAttr(key_tf + '.rotate', -35, 25, 0)
    cmds.ambientLight(rgb=(0.5, 0.5, 0.5), intensity=1.0)
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware', type='string')
    cmds.setAttr('defaultRenderGlobals.imageFormat', 32)
    cmds.setAttr('defaultResolution.width', 64)
    cmds.setAttr('defaultResolution.height', 64)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 1.0)
    cmds.workspace(fileRule=['images', PREVIEW.as_posix()])
    # Camera B: euler only. eye_mid=(0,67.77,1.62); place above-front, pitch down.
    cam_tf, cam_sh = cmds.camera(name='DiagCamB', focalLength=50)
    cmds.setAttr(cam_sh + '.renderable', 1)
    cmds.setAttr(cam_sh + '.backgroundColor', 0.25, 0.25, 0.25, type='float3')
    cmds.setAttr(cam_tf + '.translate', 0.0, 73.8, 31.6)
    cmds.setAttr(cam_tf + '.rotate', -11.3, 0, 0)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', 'diag2_euler', type='string')
    cmds.render(cam_sh)
    r['files'] = {p.name: p.stat().st_size for p in PREVIEW.rglob('diag2_*')}
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
