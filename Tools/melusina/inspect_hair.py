# Tools/melusina/inspect_hair.py
import sys, json, os
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds, mel

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
HAIR = r"G:\MelusinaRigFinalSeparate\SM_MelusinaHair.fbx"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\hair_import.json"

def main():
    cmds.file(BIND, open=True, force=True)
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
        rows.append({
            "mesh": m,
            "transform": t,
            "vertices": cmds.polyEvaluate(m, vertex=True),
            "bbox": cmds.exactWorldBoundingBox(m),
            "materials": cmds.listConnections(m, type="shadingEngine") or [],
        })
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"hair_fbx": HAIR, "new_meshes": rows}, f, indent=2)

main()
