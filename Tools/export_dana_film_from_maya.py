"""Export Dana's visible, bound render meshes rather than Maya rig helpers.

Run with a working Maya mayapy executable. The source .mb is read, never saved.
The exporter refuses an unbound visible body instead of inventing new weights.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Humber_FinalYear_Prep/Content/Meshes/Characters/Dana/Dana_Rig_v1.5.mb'
OUTPUT = ROOT / 'Saved/Exports/DanaImportAudit/Dana_Film_DeformOnly.fbx'
REPORT = ROOT / 'Saved/Audit/dana_maya_export.json'

def export():
    import maya.cmds as cmds
    import maya.mel as mel

    cmds.file(str(SOURCE), open=True, force=True, executeScriptNodes=False, ignoreVersion=True)
    cmds.currentTime(cmds.playbackOptions(query=True, minTime=True), edit=True)
    def is_visible(node):
        current = node
        while current:
            if cmds.attributeQuery('visibility', node=current, exists=True) and not cmds.getAttr(current+'.visibility'):
                return False
            parents = cmds.listRelatives(current, parent=True, fullPath=True) or []
            current = parents[0] if parents else None
        return True

    meshes = []
    excluded = []
    influence_joints = set()
    for shape in cmds.ls(type='mesh', long=True):
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if not parents:
            continue
        transform = parents[0]
        basename = transform.rsplit('|',1)[-1].rsplit(':',1)[-1]
        helper = bool(re.search(r'Region|upperLower|bodyBreath|squint', basename, re.I))
        if cmds.getAttr(shape+'.intermediateObject') or helper or not is_visible(shape):
            excluded.append(transform)
            continue
        history = cmds.listHistory(shape, pruneDagObjects=True) or []
        skins = cmds.ls(history, type='skinCluster') or []
        influences = set(j for skin in skins for j in (cmds.skinCluster(skin, query=True, influence=True) or []))
        shading_groups = cmds.listConnections(shape, type='shadingEngine') or []
        meshes.append({'mesh':transform,'shape':shape,'triangles':cmds.polyEvaluate(shape, triangle=True),'skin_clusters':skins,'influences':sorted(influences),'shading_groups':shading_groups})
        influence_joints.update(influences)
    body = [m for m in meshes if re.search(r'Dana_Body', m['mesh'], re.I)]
    problems = []
    if len(body) != 1:
        problems.append('Expected one visible Dana body; found %d' % len(body))
    elif not body[0]['skin_clusters']:
        problems.append('Visible Dana body has no skinCluster. Inspect the final body output and binding in Maya before exporting.')
    if not meshes or not influence_joints:
        problems.append('No visible bound render geometry was found')
    # Include only the required deformation hierarchy. Constraint/control
    # networks are not selected or followed by the FBX exporter.
    joints = set(influence_joints)
    for joint in list(joints):
        parents = cmds.listRelatives(joint, parent=True, fullPath=True) or []
        while parents and cmds.nodeType(parents[0]) == 'joint':
            joints.add(parents[0])
            parents = cmds.listRelatives(parents[0], parent=True, fullPath=True) or []
    report = {'source':str(SOURCE),'output':str(OUTPUT),'render_meshes':meshes,'excluded_helpers':sorted(set(excluded)),'influence_count':len(influence_joints),'selected_joint_count':len(joints),'problems':problems,'result':'blocked' if problems else 'exporting'}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if problems:
        raise RuntimeError('; '.join(problems))
    if OUTPUT.exists():
        raise RuntimeError('Export already exists; preserve it and choose a new output name for a subsequent revision')
    cmds.loadPlugin('fbxmaya', quiet=True)
    mel.eval('FBXResetExport;')
    for statement in ('FBXExportSkins -v true;', 'FBXExportShapes -v true;', 'FBXExportConstraints -v false;', 'FBXExportInputConnections -v false;', 'FBXExportBakeComplexAnimation -v true;', 'FBXExportCameras -v false;', 'FBXExportLights -v false;', 'FBXExportEmbeddedTextures -v false;'):
        mel.eval(statement)
    mel.eval('FBXExportBakeComplexStart -v %s;' % cmds.playbackOptions(query=True,minTime=True))
    mel.eval('FBXExportBakeComplexEnd -v %s;' % cmds.playbackOptions(query=True,maxTime=True))
    cmds.select([m['mesh'] for m in meshes] + sorted(joints), replace=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    mel.eval('FBXExport -f "%s" -s;' % OUTPUT.as_posix())
    report['result'] = 'exported_requires_import_and_deformation_verification'
    report['bytes'] = OUTPUT.stat().st_size
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    import maya.standalone
    maya.standalone.initialize(name='python')
    try:
        export()
    finally:
        maya.standalone.uninitialize()
