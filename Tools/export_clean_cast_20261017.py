"""Derived David/Sam export: exact evaluated geometry, skin weights and face slots.

Reuse the Dana evaluated-copy technique. One new skeleton includes transform
ancestors as joints; face follow is explicitly parented beneath Head_M. Native
scenes are never saved. Existing candidate files are never replaced.
"""
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path
import maya.standalone

ROOT = Path(__file__).resolve().parents[1]

def main(character):
    maya.standalone.initialize(name='python')
    from maya import cmds, mel
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma
    out = ROOT / 'Saved/OfflineIntake/20261017/clean_cast' / character
    out.mkdir(parents=True, exist_ok=True)
    output = out / (character + '_CleanFilm_v01.fbx')
    report_path = out / 'export_report.json'
    report = {'character': character, 'source_saved': False, 'status': 'starting'}
    def save(): report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    def dag(name):
        s = om.MSelectionList(); s.add(name); return s.getDagPath(0)
    def skinfn(name):
        s = om.MSelectionList(); s.add(name); return oma.MFnSkinCluster(s.getDependNode(0))
    def component(n):
        f = om.MFnSingleIndexedComponent(); c = f.create(om.MFn.kMeshVertComponent)
        f.setCompleteData(n); return c
    def points(name):
        return cmds.xform(name + '.vtx[*]', query=True, worldSpace=True, translation=True)
    def max_error(a, b):
        return max(math.sqrt(sum((a[i+k]-b[i+k])**2 for k in range(3))) for i in range(0,len(a),3))
    def tick():
        cmds.dgdirty(allPlugs=True); cmds.currentTime(2,edit=True,update=True)
        cmds.currentTime(1,edit=True,update=True)
    try:
        if output.exists(): raise RuntimeError('Existing candidate preserved: ' + str(output))
        sources = json.loads((ROOT / 'specs/cast/cast_rig_sources.v1.json').read_text())
        source = Path(sources['intake_root']) / sources['characters'][character]['source']
        report.update(source=str(source), source_sha256_before=hashlib.sha256(source.read_bytes()).hexdigest())
        contract = json.loads((ROOT / ('Saved/Audit/EveningExecution_20261017/native_%s.json' % character.lower())).read_text())
        cmds.file(str(source),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,
                  loadReferenceDepth='none',prompt=False)
        cmds.evaluationManager(mode='off'); cmds.currentTime(1,edit=True,update=True)
        cmds.namespace(add='FilmExport')
        group = cmds.createNode('transform',name='FilmExport:Export')
        root = cmds.createNode('joint',name='FilmExport:FilmRoot',parent=group)
        meshes = cmds.createNode('transform',name='FilmExport:Meshes',parent=group)
        paths = set()
        for row in contract['meshes']:
            for influence in cmds.skinCluster(row['skin'][0],query=True,influence=True):
                path = cmds.ls(influence,long=True)[0]
                while path:
                    paths.add(path)
                    path = (cmds.listRelatives(path,parent=True,fullPath=True) or [None])[0]
        report['source_ancestor_count'] = len(paths)
        mapped = {}
        used = set()
        for path in sorted(paths,key=lambda p:(p.count('|'),p)):
            name = path.rsplit('|',1)[-1].replace(':','_')
            if name in used: raise RuntimeError('Duplicate skeleton name: ' + name)
            used.add(name)
            parent = (cmds.listRelatives(path,parent=True,fullPath=True) or [None])[0]
            joint = cmds.createNode('joint',name='FilmExport:' + name,parent=mapped.get(parent,root))
            cmds.xform(joint,worldSpace=True,matrix=cmds.xform(path,query=True,worldSpace=True,matrix=True))
            mapped[path] = cmds.ls(joint,long=True)[0]
        # Face constraints are not FBX skeleton hierarchy: make the authored follow
        # transform a child of the exported Head_M while keeping its rest matrix.
        head_path = next(p for p in paths if p.endswith('|Head_M'))
        follow = [p for p in paths if p.endswith('|FaceDeformationFollowHead')]
        report['face_follow_reparent'] = []
        for path in follow:
            before = mapped[path]
            renamed = cmds.parent(before,mapped[head_path],absolute=True)[0]
            new = cmds.ls(renamed,long=True)[0]
            mapped = {p:(new + v[len(before):] if v == before or v.startswith(before+'|') else v)
                      for p,v in mapped.items()}
            report['face_follow_reparent'].append({'source':path,'parent':'Head_M'})
        report['meshes'] = []
        for row in contract['meshes']:
            src = row['mesh']; srcshape = cmds.listRelatives(src,shapes=True,noIntermediate=True,fullPath=True,type='mesh')[0]
            sd = dag(srcshape); fn = om.MFnMesh(sd); n = fn.numVertices
            duplicate = cmds.createNode('transform',name='FilmExport:'+src.rsplit('|',1)[-1],parent=meshes)
            cmds.xform(duplicate,worldSpace=True,matrix=cmds.xform(src,query=True,worldSpace=True,matrix=True))
            obj = om.MFnMesh().copy(sd.node(),dag(duplicate).node())
            dstshape = om.MDagPath.getAPathTo(obj).fullPathName()
            shaders, assignments = fn.getConnectedShaders(sd.instanceNumber())
            material_counts = {}
            if any(index < 0 for index in assignments): raise RuntimeError('Unassigned source faces: '+src)
            for index, shader in enumerate(shaders):
                sg = om.MFnDependencyNode(shader).name()
                faces = [duplicate+'.f[%d]' % i for i,v in enumerate(assignments) if v == index]
                if faces: cmds.sets(faces,edit=True,forceElement=sg)
                material_counts[sg] = len(faces)
            sf = skinfn(row['skin'][0]); influences = sf.influenceObjects()
            weights, count = sf.getWeights(sd,component(n))
            target_infs = [mapped[p.fullPathName()] for p in influences]
            cluster = cmds.skinCluster(target_infs,duplicate,toSelectedBones=True,
                       normalizeWeights=0,obeyMaxInfluences=False,name='FilmExport:'+src.rsplit('|',1)[-1]+'_Skin')[0]
            df = skinfn(cluster); target_order = [p.fullPathName() for p in df.influenceObjects()]
            columns = {p:i for i,p in enumerate(target_infs)}
            order = [columns[p] for p in target_order]
            copied = om.MDoubleArray([weights[v*count+j] for v in range(n) for j in order])
            df.setWeights(dag(dstshape),component(n),om.MIntArray(list(range(len(order)))),copied,False)
            cmds.setAttr(cluster+'.skinningMethod',cmds.getAttr(row['skin'][0]+'.skinningMethod'))
            df.setBlendWeights(dag(dstshape),component(n),sf.getBlendWeights(sd,component(n)))
            actual,_ = df.getWeights(dag(dstshape),component(n))
            delta = max(abs(a-b) for a,b in zip(actual,copied))
            error = max_error(points(src),points(duplicate))
            if delta > 1e-12 or error > 0.01: raise RuntimeError('Copy gate failed: '+src)
            report['meshes'].append({'source':src,'copy':duplicate,'vertices':n,
                'triangles':row['triangles'],'weight_copy_max_delta':delta,
                'rest_geometry_max_error_cm':error,'material_faces':material_counts})
            save()
        # Bake blink geometry from native evaluated controls. These are facial
        # targets, not imported rig helpers. Other expressions remain pose work.
        body = next(r for r in report['meshes'] if r['source'].endswith('|'+character+'_Body_GEO'))
        body_rest = points(body['source']); blend = None; report['morphs'] = []
        for index, side in enumerate(['L','R']):
            plug = 'ctrlEye_'+side+'.blink'; original = cmds.getAttr(plug)
            cmds.setAttr(plug,10.0); tick()
            srcshape = cmds.listRelatives(body['source'],shapes=True,noIntermediate=True,fullPath=True,type='mesh')[0]
            target = cmds.createNode('transform',name='FilmExport:Blink_'+side,parent=meshes)
            cmds.xform(target,worldSpace=True,matrix=cmds.xform(body['source'],query=True,worldSpace=True,matrix=True))
            om.MFnMesh().copy(dag(srcshape).node(),dag(target).node())
            motion = max_error(body_rest,points(target))
            cmds.setAttr(plug,original); tick()
            if motion <= 0.001: raise RuntimeError('Native blink did not move: '+side)
            if blend is None: blend=cmds.blendShape(target,body['copy'],frontOfChain=True,name='FilmExport:FaceMorphs')[0]
            else: cmds.blendShape(blend,edit=True,target=(body['copy'],index,target,1.0))
            weight_plug = blend+'.weight[%d]' % index
            if cmds.aliasAttr(weight_plug, query=True) != 'Blink_'+side:
                cmds.aliasAttr('Blink_'+side,weight_plug)
            cmds.setAttr(blend+'.weight[%d]' % index,0)
            cmds.delete(target)
            report['morphs'].append({'name':'Blink_'+side,'max_native_motion_cm':motion})
        cmds.loadPlugin('fbxmaya',quiet=True); mel.eval('FBXResetExport;')
        for statement in ['FBXExportSkins -v true;','FBXExportShapes -v true;',
            'FBXExportConstraints -v false;','FBXExportInputConnections -v false;',
            'FBXExportBakeComplexAnimation -v false;','FBXExportEmbeddedTextures -v false;',
            'FBXExportUpAxis y;']:
            mel.eval(statement)
        cmds.select(group,replace=True); cmds.select(group,hierarchy=True)
        mel.eval('FBXExport -f "%s" -s;' % output.as_posix())
        report['output'] = str(output); report['output_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
        report['source_unchanged'] = report['source_sha256_before'] == hashlib.sha256(source.read_bytes()).hexdigest()
        report['status'] = 'exported_copy_gates_passed_pending_independent_readback'
        report['bone_count'] = len(mapped)+1
        save(); print(json.dumps({'character':character,'status':report['status'],'output':str(output)}),flush=True)
    except Exception:
        report['status']='failed'; report['error']=traceback.format_exc(); save(); raise
    finally:
        cmds.file(new=True,force=True); maya.standalone.uninitialize()

if __name__ == '__main__':
    main(sys.argv[1])
