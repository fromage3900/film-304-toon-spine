"""Read native David/Sam topology, face materials and skin ownership; never save scenes."""
import hashlib
import json
import traceback
from pathlib import Path
import maya.standalone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/Audit/EveningExecution_20261017'

def main():
    maya.standalone.initialize(name='python')
    from maya import cmds
    import maya.api.OpenMaya as om
    sources = json.loads((ROOT / 'specs/cast/cast_rig_sources.v1.json').read_text())
    try:
        for character in ['David', 'Sam']:
            source = Path(sources['intake_root']) / sources['characters'][character]['source']
            contract = json.loads((ROOT / ('Saved/Audit/CastMayaExport_20261016/export_%s.json' % character.lower())).read_text())
            receipt = {'character': character, 'source': str(source),
                       'source_sha256_before': hashlib.sha256(source.read_bytes()).hexdigest(),
                       'maya_version': cmds.about(version=True), 'meshes': []}
            cmds.file(str(source), open=True, force=True, ignoreVersion=True,
                      executeScriptNodes=False, loadReferenceDepth='none', prompt=False)
            cmds.evaluationManager(mode='off')
            cmds.currentTime(1, edit=True, update=True)
            for item in contract['render_meshes']:
                transform = item['mesh']
                shapes = cmds.listRelatives(transform, shapes=True, noIntermediate=True, fullPath=True, type='mesh') or []
                if len(shapes) != 1:
                    raise RuntimeError('Ambiguous source shape: ' + transform)
                selection = om.MSelectionList(); selection.add(shapes[0])
                dag = selection.getDagPath(0); fn = om.MFnMesh(dag)
                shaders, assignment = fn.getConnectedShaders(dag.instanceNumber())
                rows = []
                for index, shader in enumerate(shaders):
                    sg = om.MFnDependencyNode(shader).name()
                    rows.append({'sg': sg, 'shader': cmds.listConnections(sg + '.surfaceShader', source=True, destination=False) or [],
                                 'faces': sum(v == index for v in assignment)})
                skins = cmds.ls(cmds.listHistory(shapes[0], pruneDagObjects=True) or [], type='skinCluster') or []
                influences = cmds.skinCluster(skins[0], query=True, influence=True) if len(skins) == 1 else []
                roots = set()
                for influence in influences:
                    current = cmds.ls(influence, long=True)[0]
                    while True:
                        parents = cmds.listRelatives(current, parent=True, fullPath=True, type='joint') or []
                        if not parents: break
                        current = parents[0]
                    roots.add(current)
                u, v = fn.getUVs()
                receipt['meshes'].append({'mesh': transform, 'vertices': fn.numVertices,
                    'triangles': len(fn.getTriangles()[1]) // 3,
                    'bounds': cmds.exactWorldBoundingBox(transform), 'skin': skins,
                    'influence_roots': sorted(roots), 'materials': rows,
                    'uv_bounds': [min(u), max(u), min(v), max(v)] if len(u) else None})
            receipt['joints'] = len(cmds.ls(type='joint') or [])
            receipt['face_blendshapes'] = cmds.ls(type='blendShape') or []
            receipt['face_controls'] = {name: cmds.listAttr(name, keyable=True) or []
                for name in ['ctrlEye_L', 'ctrlEye_R', 'ctrlMouth_M', 'asFaceBS'] if cmds.objExists(name)}
            receipt['source_unchanged'] = receipt['source_sha256_before'] == hashlib.sha256(source.read_bytes()).hexdigest()
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / ('native_%s.json' % character.lower())).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
            print(json.dumps({'character': character, 'meshes': len(receipt['meshes']),
                              'source_unchanged': receipt['source_unchanged']}), flush=True)
    finally:
        cmds.file(new=True, force=True)
        maya.standalone.uninitialize()

if __name__ == '__main__':
    main()
