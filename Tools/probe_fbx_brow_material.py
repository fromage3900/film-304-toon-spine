"""Micro-probe: does a component-level shading-group assignment survive FBXExport?"""
import tempfile
from pathlib import Path
import maya.standalone

maya.standalone.initialize(name='python')
from maya import cmds, mel

try:
    cmds.file(new=True, force=True)
    cube = cmds.polyCube(name='BrowCube')[0]
    shader = cmds.shadingNode('lambert', asShader=True, name='samBrowPatch_mat')
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='samBrowPatch_matSG')
    cmds.connectAttr(shader + '.outColor', sg + '.surfaceShader', force=True)
    cmds.sets([cube + '.f[0:3]'], edit=True, forceElement=sg)
    members = cmds.sets(sg, query=True)
    print('members:', members)
    print('isMember fly:', cmds.sets(cube + '.f[0]', isMember=sg))
    out = Path(tempfile.gettempdir()) / 'brow_fbx_probe.fbx'
    if out.exists():
        out.unlink()
    cmds.loadPlugin('fbxmaya', quiet=True)
    mel.eval('FBXResetExport;')
    mel.eval('FBXExportSkins -v true; FBXExportShapes -v true; FBXExportEmbeddedTextures -v false;')
    mel.eval('FBXExport -f "%s" -s;' % out.as_posix())
    data = out.read_bytes()
    print('probe_bytes:', len(data), '| brow hits:', data.count(b'samBrowPatch_mat'), '| Material refs:',
          data.count(b'Material'))
    # variant B: assign via whole-shape instead of faces
    sg2 = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='WholeShapeSG')
    cmds.connectAttr(shader + '.outColor', sg2 + '.surfaceShader', force=True)
    cmds.sets([cube], edit=True, forceElement=sg2)
    out2 = Path(tempfile.gettempdir()) / 'brow_fbx_probe2.fbx'
    if out2.exists():
        out2.unlink()
    mel.eval('FBXExport -f "%s" -s;' % out2.as_posix())
    data2 = out2.read_bytes()
    print('whole-shape probe hits:', data2.count(b'samBrowPatch_mat'))
finally:
    cmds.file(new=True, force=True)
    maya.standalone.uninitialize()
