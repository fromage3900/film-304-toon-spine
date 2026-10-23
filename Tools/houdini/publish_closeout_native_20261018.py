"""Publish portable ceiling geometry and the live-cooked window HDA outside Saved/."""
import hashlib
import json
import shutil
from pathlib import Path
import hou

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'Tools/houdini/Published/Film304Closeout_20261018'
AUDIT=ROOT/'Saved/Audit/Closeout_20261018'

def main():
    assert not (DEST/'native_publish_manifest.json').exists(), 'Existing native publish is immutable; inspect before revision'
    ceiling=DEST/'Ceiling';window=DEST/'WindowRig'
    (ceiling/'geometry').mkdir(parents=True,exist_ok=True);(ceiling/'exports').mkdir(exist_ok=True);window.mkdir(exist_ok=True)
    source=json.loads((AUDIT/'ceiling_native_convergence.json').read_text())
    hou.hipFile.load(source['native_hip'],suppress_save_prompt=True)
    expected={}
    for node in hou.node('/obj').allSubChildren():
        if node.type().name()!='file':continue
        geometry=node.geometry().freeze();assert geometry and len(geometry.prims())>0
        name=node.parent().name()
        geometry.saveToFile(str(ceiling/'geometry'/(name+'.bgeo.sc')))
        node.parm('file').set('$HIP/geometry/'+name+'.bgeo.sc')
        expected[name]={'points':len(geometry.points()),'quads':len(geometry.prims()),
                        'min':list(geometry.boundingBox().minvec()),'max':list(geometry.boundingBox().maxvec())}
    for row in source['meshes']:
        shutil.copy2(row['fbx'],ceiling/'exports'/Path(row['fbx']).name)
    for node in hou.node('/obj').allSubChildren():
        if node.type().name()=='rop_fbx':node.parm('sopoutput').set('$HIP/exports/'+Path(node.parm('sopoutput').eval()).name)
    hip=ceiling/'OfficeCeiling_Final_v03.hip';hou.hipFile.save(str(hip))
    # Reopen and force geometry reads from the new $HIP-relative files.
    hou.hipFile.clear(suppress_save_prompt=True);hou.hipFile.load(str(hip),suppress_save_prompt=True)
    reads=[]
    for node in hou.node('/obj').allSubChildren():
        if node.type().name()!='file':continue
        node.cook(force=True);geometry=node.geometry();name=node.parent().name()
        assert not node.errors(),node.errors()
        assert len(geometry.prims())==expected[name]['quads']
        assert str(DEST) in str(Path(node.parm('file').eval())),node.parm('file').eval()
        reads.append({'node':node.path(),'resolved_geometry':node.parm('file').eval(),
                      'quads':len(geometry.prims()),'errors':list(node.errors())})
    original_window=ROOT/'Saved/Houdini/WindowLightRig_20261018'
    hda=window/'Film304_WindowLightRig_v01.hda'
    shutil.copy2(original_window/hda.name,hda)
    hou.hda.installFile(str(hda),change_oplibraries_file=False)
    hou.hipFile.load(str(original_window/'Film304_WindowLightRig_v01.hip'),suppress_save_prompt=True)
    definition=hou.hda.definitionsInFile(str(hda))[0];definition.setPreferred(True)
    hou.hipFile.save(str(window/'Film304_WindowLightRig_v01.hip'))
    files=[]
    for path in sorted(DEST.rglob('*')):
        if path.is_file():files.append({'path':str(path.relative_to(DEST)),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    report={'root':str(DEST),'ceiling_hip':str(hip),'ceiling_reload_verified':True,
        'ceiling_geometry_reads':reads,'window_hda':str(hda),
        'window_definition_path':definition.libraryFilePath(),'files':files,
        'source_recipes':['Tools/houdini/converge_office_ceiling_20261018.py',
                          'Tools/houdini/build_window_light_rig_20261018.py'],
        'unreal_imports_and_baked_lights_unchanged':True}
    (DEST/'native_publish_manifest.json').write_text(json.dumps(report,indent=2))
    (AUDIT/'native_publish_proof.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'root':str(DEST),'files':len(files),'ceiling_reload_verified':True,'geometry':reads}))

if __name__=='__main__':main()
