# Tools/melusina/add_hair.py
import sys, json, os
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds, mel
from melusina_common import write_json

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
HAIR = r"G:\MelusinaRigFinalSeparate\SM_MelusinaHair.fbx"
OUT_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_with_hair.ma"
OUT_JSON = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\hair_bind_report.json"

def main():
    cmds.file(BIND, open=True, force=True)
    joints = cmds.ls(type="joint") or []
    before = set(cmds.ls(type="mesh") or [])
    cmds.loadPlugin("fbxmaya", quiet=True)
    mel.eval("FBXResetImport")
    mel.eval('FBXImportMode -v "add"')
    mel.eval('FBXImport -f "%s"' % HAIR.replace("\\", "/"))
    after = set(cmds.ls(type="mesh") or [])
    new = sorted(after - before)
    rows = []
    for m in new:
        t = cmds.listRelatives(m, parent=True, fullPath=True)[0]
        cmds.select(clear=True)
        cmds.select(joints, add=True)
        cmds.select(t, add=True)
        name = "%s_skinCluster" % t.replace("|", "_").replace(" ", "_")
        sc_name = None
        try:
            sc = cmds.skinCluster(name=name, toSelectedBones=True, bindMethod=0, skinMethod=0,
                                  normalizeWeights=1, obeyMaxInfluences=True,
                                  maximumInfluences=4, dropoffRate=4.0)
            sc_name = sc[0] if isinstance(sc, list) else sc
        except Exception as exc:
            sc_name = "FAILED: %s" % exc
        rows.append({
            "mesh": m,
            "transform": t,
            "vertices": cmds.polyEvaluate(m, vertex=True),
            "skinCluster": sc_name,
        })
    cmds.file(rename=OUT_MA)
    cmds.file(save=True, type="mayaAscii")
    write_json(OUT_JSON, {
        "hair_fbx": HAIR,
        "joint_count": len(joints),
        "hair_meshes": rows,
        "saved_ma": OUT_MA,
    })

main()
