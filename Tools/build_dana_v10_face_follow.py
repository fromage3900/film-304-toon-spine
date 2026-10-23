"""Minimal derived Dana v10 FBX: parent the native face-follow joint to Head_M."""
import datetime
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path
import maya.standalone

maya.standalone.initialize(name='python')
from maya import cmds, mel
import maya.api.OpenMaya as om

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx'
OUTPUT = ROOT / 'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx'
REPORT = ROOT / 'Saved/OfflineIntake/20261017/task1_face_eyes/report/v10e_face_follow_build.json'
EXPECTED = {
    'Dana_Body_GEO': 9249, 'Dana_Eyelashes_Lf_GEO': 39, 'Dana_Eyelashes_Rt_GEO': 39,
    'Dana_Eye_Lf_GEO': 1121, 'Dana_Eye_Rt_GEO': 1121, 'Dana_Cornea_Lf_GEO': 161,
    'Dana_Cornea_Rt_GEO': 161, 'Dana_EyeInt_Lf_GEO': 51, 'Dana_EyeInt_Rt_GEO': 51,
    'Dana_Jeans_GEO': 2172, 'Dana_Shirt_GEO': 1564, 'Dana_Shoe_Lf_GEO': 1031,
    'Dana_Shoe_Rt_GEO': 1031, 'Dana_LongHair_Bang_GEO': 474, 'Dana_LongHair_Main_GEO': 566,
    'Dana_Lower_Teeth_GEO1': 2192, 'Dana_UpperTeeth_GEO': 2194, 'Dana_Tongue_GEO': 165,
    'Dana_Eyebrows_GEO': 178,
}

report = {'tool':'build_dana_v10_face_follow.py','stage':'starting','source':str(SOURCE),
          'output':str(OUTPUT),'source_saved':False,
          'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')

def short(path):
    return path.rsplit('|',1)[-1].rsplit(':',1)[-1]

def pick_joint(name):
    hits=[j for j in (cmds.ls(type='joint',long=True) or []) if short(j)==name]
    if len(hits)!=1:
        related=[j for j in (cmds.ls(type='joint',long=True) or []) if any(k in short(j).lower() for k in ['face','head','eye'])]
        raise RuntimeError('Expected one joint %s; got %s; related joints=%s' % (name,hits,related))
    return hits[0]

def pick_transform(name):
    hits=[n for n in (cmds.ls(long=True) or []) if short(n)==name and cmds.nodeType(n)=='transform']
    if len(hits)!=1: raise RuntimeError('Expected one transform %s; got %s' % (name,hits))
    return hits[0]

def mesh_map():
    out={}
    for shape in cmds.ls(type='mesh',long=True) or []:
        if cmds.getAttr(shape+'.intermediateObject'): continue
        parents=cmds.listRelatives(shape,parent=True,fullPath=True) or []
        if not parents: continue
        name=short(parents[0])
        if name in EXPECTED:
            if name in out: raise RuntimeError('Duplicate mesh transform '+name)
            out[name]=(parents[0],shape)
    return out

def world_matrix(node):
    return list(cmds.xform(node,query=True,worldSpace=True,matrix=True))

def matrix_delta(a,b):
    return max(abs(float(x)-float(y)) for x,y in zip(a,b))

try:
    if OUTPUT.exists(): raise RuntimeError('Existing v10 candidate preserved: '+str(OUTPUT))
    if not SOURCE.is_file(): raise FileNotFoundError(str(SOURCE))
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report['source_sha256_before']=source_hash
    cmds.loadPlugin('fbxmaya',quiet=True)
    cmds.file(str(SOURCE),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,prompt=False)
    cmds.evaluationManager(mode='off')
    cmds.currentTime(1,edit=True,update=True)
    meshes=mesh_map()
    if set(meshes)!=set(EXPECTED): raise RuntimeError('Source mesh inventory mismatch: '+repr(sorted(set(EXPECTED)^set(meshes))))
    joints=cmds.ls(type='joint',long=True) or []
    report['source_joint_count']=len(joints)
    report['source_mesh_count']=len(meshes)
    report['source_vertex_count']=sum(cmds.polyEvaluate(x[1],vertex=True) for x in meshes.values())
    follow=pick_transform('FaceDeformationFollowHead')
    head=pick_joint('Head_M')
    report['face_follow_parent_before']=short((cmds.listRelatives(follow,parent=True,fullPath=True) or [''])[0])
    if report['face_follow_parent_before']=='Head_M':
        raise RuntimeError('Source already has direct Head_M parent; v10 repair is unnecessary')
    follow_world_before=world_matrix(follow)
    head_world_before=world_matrix(head)
    cmds.parent(follow,head,absolute=True)
    follow=pick_transform('FaceDeformationFollowHead')
    new_parent=(cmds.listRelatives(follow,parent=True,fullPath=True) or [''])[0]
    report['face_follow_parent_after']=short(new_parent)
    report['face_follow_world_matrix_delta']=matrix_delta(follow_world_before,world_matrix(follow))
    report['head_world_matrix_delta']=matrix_delta(head_world_before,world_matrix(head))
    if short(new_parent)!='Head_M': raise RuntimeError('Face follow was not reparented directly under Head_M')
    if report['face_follow_world_matrix_delta']>1e-7: raise RuntimeError('Face follow rest world matrix changed')
    if report['head_world_matrix_delta']>1e-7: raise RuntimeError('Head rest world matrix changed')
    report['stage']='reparented_preserving_rest'
    save()
    # Probe true motion through the new chain, then restore the source bind pose.
    eye=pick_joint('Eye_L')
    eye_before=cmds.xform(eye,query=True,worldSpace=True,translation=True)
    old_rot=cmds.getAttr(head+'.rotateX')
    cmds.setAttr(head+'.rotateX',old_rot+10.0)
    cmds.dgdirty(allPlugs=True)
    cmds.currentTime(2,edit=True,update=True); cmds.currentTime(1,edit=True,update=True)
    eye_after=cmds.xform(eye,query=True,worldSpace=True,translation=True)
    motion=math.sqrt(sum((float(eye_after[i])-float(eye_before[i]))**2 for i in range(3)))
    cmds.setAttr(head+'.rotateX',old_rot)
    cmds.dgdirty(allPlugs=True)
    cmds.currentTime(2,edit=True,update=True); cmds.currentTime(1,edit=True,update=True)
    report['head_pitch_test_degrees']=10.0
    report['eye_l_world_displacement_cm']=motion
    if motion<0.05: raise RuntimeError('Head rotation did not move Eye_L meaningfully')
    # Export the same native mesh and joint inventory; only the parent relationship changed.
    mel.eval('FBXResetExport;')
    for command in [
        'FBXExportSkins -v true;', 'FBXExportShapes -v true;',
        'FBXExportInputConnections -v true;', 'FBXExportIncludeChildren -v false;',
        'FBXExportConstraints -v false;', 'FBXExportCameras -v false;',
        'FBXExportLights -v false;', 'FBXExportEmbeddedTextures -v false;',
        'FBXExportTriangulate -v false;'
    ]: mel.eval(command)
    current_meshes=mesh_map()
    current_joints=cmds.ls(type='joint',long=True) or []
    cmds.select([row[0] for row in current_meshes.values()]+current_joints,replace=True,noExpand=True)
    report['stage']='exporting'
    save()
    mel.eval('FBXExport -f "%s" -s;' % OUTPUT.as_posix())
    report['candidate_bytes']=OUTPUT.stat().st_size
    report['candidate_sha256']=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    report['source_sha256_after']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
    if not report['source_unchanged']: raise RuntimeError('Source FBX hash changed')
    report['stage']='v10_exported_pending_independent_readback'
    save()
    print(json.dumps(report))
except Exception:
    report['stage']='blocked'; report['error']=traceback.format_exc(); save()
    print(report['error']); raise
finally:
    try:
        cmds.file(new=True,force=True)
        maya.standalone.uninitialize()
    except Exception:
        pass



