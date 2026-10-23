"""Isolated Hython inspection of Dana FBX capture data; no source rig mutation."""
import json
from pathlib import Path
import traceback
import hou

ROOT = Path('G:/film-304-toon-spine')
OUT = ROOT / 'Saved/Audit/HoudiniDana_20261016'
OUT.mkdir(parents=True, exist_ok=True)
report = {'houdini': hou.applicationVersionString(), 'license': str(hou.licenseCategory()),
          'source': 'C:/Users/froma/Downloads/C_DanaRenderTest_OSC.fbx',
          'source_modified': False, 'stage': 'initializing'}


def write():
    (OUT / 'probe.json').write_text(json.dumps(report, indent=2))


try:
    types = hou.sopNodeTypeCategory().nodeTypes()
    report['available_types'] = sorted(name for name in types if any(
        key in name for key in ['fbxcharacterimport', 'fbxskinimport', 'fbxcharacteroutput', 'jointcapturebiharmonic']))
    geo = hou.node('/obj').createNode('geo', 'DANA_FBX_READONLY_PROBE')
    node = geo.createNode('kinefx::fbxcharacterimport', 'Existing_Dana_FBX')
    report['import_parameters'] = [{'name': p.name(), 'label': p.parmTemplate().label()}
                                    for p in node.parms()]
    file_parm = node.parm('fbxfile') or node.parm('file')
    if file_parm is None:
        candidates = [p for p in node.parms()
                      if p.parmTemplate().type() == hou.parmTemplateType.String
                      and 'file' in p.name().lower() and 'fbx' in p.parmTemplate().label().lower()]
        if len(candidates) == 1:
            file_parm = candidates[0]
    if file_parm is None:
        raise RuntimeError('Inspect recorded node parameters to choose FBX file input')
    file_parm.set(report['source'])
    report['file_parameter'] = file_parm.name()
    report['stage'] = 'cooking_import'
    write()
    node.cook(force=True)
    outputs = []
    for index, label in enumerate(['rest_geometry', 'capture_skeleton', 'animated_skeleton']):
        output = geo.createNode('null', 'INSPECT_' + label)
        output.setInput(0, node, index)
        geometry = output.geometry()
        data = {'index': index, 'label': label, 'points': len(geometry.points()),
                'primitives': len(geometry.prims()),
                'point_attributes': [a.name() for a in geometry.pointAttribs()],
                'primitive_attributes': [a.name() for a in geometry.primAttribs()],
                'detail_attributes': [a.name() for a in geometry.globalAttribs()]}
        if geometry.findPointAttrib('name'):
            data['joint_names_sample'] = list(geometry.pointStringAttribValues('name'))[:100]
        for name in ['name', 'path', 'shop_materialpath']:
            if geometry.findPrimAttrib(name):
                values = geometry.primStringAttribValues(name)
                counts = {}
                for value in values:
                    counts[value] = counts.get(value, 0) + 1
                data[name + '_counts'] = counts
        capture = geometry.findPointAttrib('boneCapture')
        if capture:
            weighted = 0
            for point in geometry.points():
                value = point.attribValue(capture)
                if any(value[i] >= 0 and value[i + 1] > 1e-6 for i in range(0, len(value) - 1, 2)):
                    weighted += 1
            data['weighted_points'] = weighted
            data['unweighted_points'] = len(geometry.points()) - weighted
        outputs.append(data)
        report['outputs'] = outputs
        write()
    report['import_errors'] = node.errors()
    report['import_warnings'] = node.warnings()
    report['stage'] = 'native_import_inspected'
    report['fbx_export_tested'] = False
    report['maya_binary_opened'] = False
    geo.layoutChildren()
    native = OUT / 'Dana_FBX_Readonly_Probe.hip'
    hou.hipFile.save(str(native))
    report['native_scene'] = hou.hipFile.path()
    write()
    print(json.dumps({'stage': report['stage'], 'license': report['license'],
                      'outputs': outputs}, indent=2))
except Exception:
    report['stage'] = 'probe_blocked'
    report['error'] = traceback.format_exc()
    write()
    raise
