"""Brow Option B (Sam): brow-region patch meshes with native weights, re-exported FBX.

Extends the proven export_clean_cast_20261017.py pipeline:
  - same FilmExport skeleton + evaluated-copy + weight-copy mechanics
  - same native blink bake (Blink_L / Blink_R morphs)
  - NEW: two brow-region patches (Lf/Rt) extracted from the body copy WITH its
    native skin cluster (brow joints, head chain, follow chain) and its
    FaceMorphs blendShape, then lifted 0.22 cm along vertex normals
  - NEW: dedicated samBrowPatch_mat shader so UE maps the patch to its own slot
Never modifies existing candidates or the source. Read gates abort before write.
"""
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path
import maya.standalone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/OfflineIntake/20261018/browB'
OUTPUT = OUT / 'Sam_CleanFilm_UE_v02_brow.fbx'

ANCHOR_SUFFIXES = ('browInnerJoint', 'browHalfJoint', 'browOuterJoint')
RADII = {'browInnerJoint': 1.05, 'browHalfJoint': 1.30, 'browOuterJoint': 1.05}
LIFT_CM = 0.22
PATCH_MAX_FACES = 720


def main():
    maya.standalone.initialize(name='python')
    from maya import cmds, mel
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'character': 'Sam', 'source_saved': False, 'status': 'starting'}
    report_path = OUT / 'export_report.json'
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
        return max(math.sqrt(sum((a[i+k]-b[i+k])**2 for k in range(3))) for i in range(0, len(a), 3))
    def tick():
        cmds.dgdirty(allPlugs=True); cmds.currentTime(2, edit=True, update=True)
        cmds.currentTime(1, edit=True, update=True)
    try:
        if OUTPUT.exists(): raise RuntimeError('Existing candidate preserved: ' + str(OUTPUT))
        sources = json.loads((ROOT / 'specs/cast/cast_rig_sources.v1.json').read_text())
        source = Path(sources['intake_root']) / sources['characters']['Sam']['source']
        report.update(source=str(source), source_sha256_before=hashlib.sha256(source.read_bytes()).hexdigest())
        contract = json.loads((ROOT / 'Saved/Audit/EveningExecution_20261017/native_sam.json').read_text())
        cmds.file(str(source), open=True, force=True, ignoreVersion=True, executeScriptNodes=False,
                  loadReferenceDepth='none', prompt=False)
        cmds.evaluationManager(mode='off'); cmds.currentTime(1, edit=True, update=True)
        cmds.namespace(add='FilmExport')
        group = cmds.createNode('transform', name='FilmExport:Export')
        root = cmds.createNode('joint', name='FilmExport:FilmRoot', parent=group)
        meshes = cmds.createNode('transform', name='FilmExport:Meshes', parent=group)
        paths = set()
        for row in contract['meshes']:
            for influence in cmds.skinCluster(row['skin'][0], query=True, influence=True):
                path = cmds.ls(influence, long=True)[0]
                while path:
                    paths.add(path)
                    path = (cmds.listRelatives(path, parent=True, fullPath=True) or [None])[0]
        mapped = {}
        used = set()
        for path in sorted(paths, key=lambda p: (p.count('|'), p)):
            name = path.rsplit('|', 1)[-1].replace(':', '_')
            if name in used: raise RuntimeError('Duplicate skeleton name: ' + name)
            used.add(name)
            parent = (cmds.listRelatives(path, parent=True, fullPath=True) or [None])[0]
            joint = cmds.createNode('joint', name='FilmExport:' + name, parent=mapped.get(parent, root))
            cmds.xform(joint, worldSpace=True, matrix=cmds.xform(path, query=True, worldSpace=True, matrix=True))
            mapped[path] = cmds.ls(joint, long=True)[0]
        head_path = next(p for p in paths if p.endswith('|Head_M'))
        follow = [p for p in paths if p.endswith('|FaceDeformationFollowHead')]
        report['face_follow_reparent'] = []
        for path in follow:
            before = mapped[path]
            renamed = cmds.parent(before, mapped[head_path], absolute=True)[0]
            new = cmds.ls(renamed, long=True)[0]
            mapped = {p: (new + v[len(before):] if v == before or v.startswith(before + '|') else v)
                      for p, v in mapped.items()}
            report['face_follow_reparent'].append({'source': path, 'parent': 'Head_M'})
        report['meshes'] = []
        for row in contract['meshes']:
            src = row['mesh']; srcshape = cmds.listRelatives(src, shapes=True, noIntermediate=True, fullPath=True, type='mesh')[0]
            sd = dag(srcshape); fn = om.MFnMesh(sd); n = fn.numVertices
            duplicate = cmds.createNode('transform', name='FilmExport:' + src.rsplit('|', 1)[-1], parent=meshes)
            cmds.xform(duplicate, worldSpace=True, matrix=cmds.xform(src, query=True, worldSpace=True, matrix=True))
            obj = om.MFnMesh().copy(sd.node(), dag(duplicate).node())
            dstshape = om.MDagPath.getAPathTo(obj).fullPathName()
            shaders, assignments = fn.getConnectedShaders(sd.instanceNumber())
            material_counts = {}
            if any(index < 0 for index in assignments): raise RuntimeError('Unassigned source faces: ' + src)
            for index, shader in enumerate(shaders):
                sg = om.MFnDependencyNode(shader).name()
                faces = [duplicate + '.f[%d]' % i for i, v in enumerate(assignments) if v == index]
                if faces: cmds.sets(faces, edit=True, forceElement=sg)
                material_counts[sg] = len(faces)
            sf = skinfn(row['skin'][0]); influences = sf.influenceObjects()
            weights, count = sf.getWeights(sd, component(n))
            target_infs = [mapped[p.fullPathName()] for p in influences]
            cluster = cmds.skinCluster(target_infs, duplicate, toSelectedBones=True,
                       normalizeWeights=0, obeyMaxInfluences=False, name='FilmExport:' + src.rsplit('|', 1)[-1] + '_Skin')[0]
            df = skinfn(cluster); target_order = [p.fullPathName() for p in df.influenceObjects()]
            columns = {p: i for i, p in enumerate(target_infs)}
            order = [columns[p] for p in target_order]
            copied = om.MDoubleArray([weights[v*count+j] for v in range(n) for j in order])
            df.setWeights(dag(dstshape), component(n), om.MIntArray(list(range(len(order)))), copied, False)
            cmds.setAttr(cluster + '.skinningMethod', cmds.getAttr(row['skin'][0] + '.skinningMethod'))
            df.setBlendWeights(dag(dstshape), component(n), sf.getBlendWeights(sd, component(n)))
            actual, _ = df.getWeights(dag(dstshape), component(n))
            delta = max(abs(a-b) for a, b in zip(actual, copied))
            error = max_error(points(src), points(duplicate))
            if delta > 1e-12 or error > 0.01: raise RuntimeError('Copy gate failed: ' + src)
            report['meshes'].append({'source': src, 'copy': duplicate, 'vertices': n,
                'triangles': row['triangles'], 'weight_copy_max_delta': delta,
                'rest_geometry_max_error_cm': error, 'material_faces': material_counts})
            save()
        body = next(r for r in report['meshes'] if r['source'].endswith('|Sam_Body_GEO'))
        body_rest = points(body['source']); blend = None; report['morphs'] = []
        for index, side in enumerate(['L', 'R']):
            plug = 'ctrlEye_' + side + '.blink'; original = cmds.getAttr(plug)
            cmds.setAttr(plug, 10.0); tick()
            srcshape = cmds.listRelatives(body['source'], shapes=True, noIntermediate=True, fullPath=True, type='mesh')[0]
            target = cmds.createNode('transform', name='FilmExport:Blink_' + side, parent=meshes)
            cmds.xform(target, worldSpace=True, matrix=cmds.xform(body['source'], query=True, worldSpace=True, matrix=True))
            om.MFnMesh().copy(dag(srcshape).node(), dag(target).node())
            motion = max_error(body_rest, points(target))
            cmds.setAttr(plug, original); tick()
            if motion <= 0.001: raise RuntimeError('Native blink did not move: ' + side)
            if blend is None:
                blend = cmds.blendShape(target, body['copy'], frontOfChain=True, name='FilmExport:FaceMorphs')[0]
            else:
                cmds.blendShape(blend, edit=True, target=(body['copy'], index, target, 1.0))
            weight_plug = blend + '.weight[%d]' % index
            if cmds.aliasAttr(weight_plug, query=True) != 'Blink_' + side:
                cmds.aliasAttr('Blink_' + side, weight_plug)
            cmds.setAttr(blend + '.weight[%d]' % index, 0)
            cmds.delete(target)
            report['morphs'].append({'name': 'Blink_' + side, 'max_native_motion_cm': motion})
        anchors = {'L': [], 'R': []}
        for path in sorted(paths):
            for suffix in ANCHOR_SUFFIXES:
                if path.endswith('|' + suffix + '_L'): anchors['L'].append((suffix, cmds.xform(path, query=True, worldSpace=True, translation=True)))
                if path.endswith('|' + suffix + '_R'): anchors['R'].append((suffix, cmds.xform(path, query=True, worldSpace=True, translation=True)))
        if len(anchors['L']) < 3 or len(anchors['R']) < 3: raise RuntimeError('Brow anchors missing: ' + json.dumps(anchors))
        report['brow_anchors'] = {side: [a[0] for a in anchors[side]] for side in ('L', 'R')}
        body_sd = dag(cmds.listRelatives(body['copy'], shapes=True, noIntermediate=True, fullPath=True)[0])
        body_fn = om.MFnMesh(body_sd)
        body_pts = body_fn.getPoints(om.MSpace.kWorld)
        body_ws_fn = om.MFnMesh(body_sd)
        body_row = next(r for r in contract['meshes'] if r['mesh'].endswith('|Sam_Body_GEO'))
        body_native_skin = body_row['skin'][0]
        body_srcshape = cmds.listRelatives(body_row['mesh'], shapes=True, noIntermediate=True, fullPath=True, type='mesh')[0]
        body_n = om.MFnMesh(dag(body_srcshape)).numVertices
        sf0 = skinfn(body_native_skin); influences0 = sf0.influenceObjects()
        weights0, count0 = sf0.getWeights(dag(body_srcshape), component(body_n))
        target_infs0 = [mapped[p.fullPathName()] for p in influences0]
        report['patches'] = []
        # Ride Sam's EXISTING source hair shader (proven to survive FBX export):
        # brow patches merge into the existing hair section and render in hair colour.
        brow_sg = 'pasted__blinn2SG'
        if not cmds.objExists(brow_sg):
            raise RuntimeError('Source hair shading group missing for brow patch merge: ' + brow_sg)
        num_polygons = body_fn.numPolygons
        for side in ('L', 'R'):
            keep = set()
            for fi in range(num_polygons):
                verts = [body_fn.getPolygonVertices(fi)[k] for k in range(body_fn.polygonVertexCount(fi))]
                hit = False
                for suffix, pos in anchors[side]:
                    r = RADII[suffix]
                    for v in verts:
                        p = body_pts[v]
                        d2 = sum((p[k] - pos[k]) ** 2 for k in range(3))
                        if d2 <= r * r:
                            hit = True
                            break
                    if hit: break
                if hit: keep.add(fi)
            if not keep: raise RuntimeError('Brow patch faces empty: ' + side)
            if len(keep) > PATCH_MAX_FACES: raise RuntimeError('Brow patch too broad: %s %d' % (side, len(keep)))
            patch = cmds.createNode('transform', name='FilmExport:Sam_BrowPatch_%s_GEO' % ('Lf' if side == 'L' else 'Rt'), parent=meshes)
            cmds.xform(patch, worldSpace=True, matrix=cmds.xform(body_row['mesh'], query=True, worldSpace=True, matrix=True))
            obj = om.MFnMesh().copy(dag(body_srcshape).node(), dag(patch).node())
            patch_shape = om.MDagPath.getAPathTo(obj).fullPathName()
            cluster = cmds.skinCluster(target_infs0, patch, toSelectedBones=True,
                       normalizeWeights=0, obeyMaxInfluences=False, name='FilmExport:Sam_BrowPatch_%s_Skin' % ('Lf' if side == 'L' else 'Rt'))[0]
            pf = skinfn(cluster); order0 = [p.fullPathName() for p in pf.influenceObjects()]
            columns = {p: i for i, p in enumerate(target_infs0)}
            order = [columns[p] for p in order0]
            copied = om.MDoubleArray([weights0[v*count0+j] for v in range(body_n) for j in order])
            pf.setWeights(dag(patch_shape), component(body_n), om.MIntArray(list(range(len(order)))), copied, False)
            cmds.setAttr(cluster + '.skinningMethod', cmds.getAttr(body_native_skin + '.skinningMethod'))
            complement = [patch + '.f[%d]' % fi for fi in range(num_polygons) if fi not in keep]
            cmds.polyDelFacet(complement)
            pfn = om.MFnMesh(dag(patch_shape))
            if pfn.numPolygons > PATCH_MAX_FACES: raise RuntimeError('Patch face count after delete: ' + str(pfn.numPolygons))
            if pfn.numVertices < 40: raise RuntimeError('Brow patch verts sparse: ' + side)
            normals = pfn.getVertexNormals(True, om.MSpace.kObject)
            pts = pfn.getPoints(om.MSpace.kObject)
            for i in range(len(pts)):
                p = pts[i]
                nv = normals[i]
                magnitude = math.sqrt(nv.x**2 + nv.y**2 + nv.z**2) or 1.0
                p.x += nv.x / magnitude * LIFT_CM
                p.y += nv.y / magnitude * LIFT_CM
                p.z += nv.z / magnitude * LIFT_CM
                pts[i] = p
            pfn.setPoints(pts, om.MSpace.kObject)
            face_count = pfn.numPolygons
            faces = [patch + '.f[%d]' % i for i in range(face_count)]
            cmds.sets(faces, edit=True, forceElement=brow_sg)
            missing = [i for i in range(face_count) if not cmds.sets((patch + '.f[%d]' % i), isMember=brow_sg)]
            if missing:
                raise RuntimeError('Brow patch shader membership thin %s: missing %d of %d (first=%s)'
                                   % (side, len(missing), face_count, missing[:6]))
            world = pfn.getPoints(om.MSpace.kWorld)
            bad = 0
            for i in range(pfn.numVertices):
                pt = om.MPoint(world[i])
                projected, _ = body_ws_fn.getClosestPoint(pt, om.MSpace.kWorld)
                dist = (om.MPoint(projected) - pt).length()
                if dist < 0.10 or dist > 0.55:
                    bad += 1
            if bad > max(4, pfn.numVertices // 20):
                raise RuntimeError('Patch lift gate failed %s: %d of %d' % (side, bad, pfn.numVertices))
            report['patches'].append({'side': side, 'copy': patch, 'vertices': pfn.numVertices,
                'faces': pfn.numPolygons, 'kept_face_candidates': len(keep), 'lift_cm': LIFT_CM,
                'bad_distance_samples': bad, 'sg_membership': 'full'})
            save()
        # FBX probe: confirm both patch materials survive a byte-level FBX write
        cmds.loadPlugin('fbxmaya', quiet=True); mel.eval('FBXResetExport;')
        for statement in ['FBXExportSkins -v true;', 'FBXExportShapes -v true;',
            'FBXExportConstraints -v false;', 'FBXExportInputConnections -v false;',
            'FBXExportBakeComplexAnimation -v false;', 'FBXExportEmbeddedTextures -v false;',
            'FBXExportUpAxis y;']:
            mel.eval(statement)
        probe = OUT / '_probe_brow.fbx'
        if probe.exists(): probe.unlink()
        cmds.select(group, replace=True); cmds.select(group, hierarchy=True)
        mel.eval('FBXExport -f "%s" -s;' % probe.as_posix())
        probe_bytes = probe.read_bytes()
        counts = {'patch_material_hits': probe_bytes.count(b'pasted__blinn2')}
        if counts['patch_material_hits'] == 0:
            raise RuntimeError('FBX probe lacks the brow material: %s' % counts)
        report['fbx_probe_materials'] = counts
        probe.unlink()
        cmds.select(group, replace=True); cmds.select(group, hierarchy=True)
        mel.eval('FBXExport -f "%s" -s;' % OUTPUT.as_posix())
        report['output'] = str(OUTPUT); report['output_sha256'] = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
        report['source_unchanged'] = report['source_sha256_before'] == hashlib.sha256(source.read_bytes()).hexdigest()
        report['status'] = 'exported_brow_patch_gates_passed_pending_ue_readback'
        report['bone_count'] = len(mapped) + 1
        save(); print(json.dumps({'character': 'Sam', 'status': report['status'], 'output': str(OUTPUT)}), flush=True)
    except Exception:
        report['status'] = 'failed'; report['error'] = traceback.format_exc(); save(); raise
    finally:
        cmds.file(new=True, force=True); maya.standalone.uninitialize()

if __name__ == '__main__':
    main()
