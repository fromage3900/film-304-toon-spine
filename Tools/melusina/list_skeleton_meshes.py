# Tools/melusina/list_skeleton_meshes.py
import re, json, os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\skeleton_test.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\skeleton_meshes.json"

def decode(name):
    if name is None:
        return None
    name = name.split("|")[-1]
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

def main():
    cmds.file(MA, open=True, force=True)
    rows = []
    for m in cmds.ls(type="mesh") or []:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        t = transforms[0] if transforms else m
        name = decode(t.split("|")[-1])
        try:
            v = cmds.polyEvaluate(m, vertex=True)
        except Exception:
            v = -1
        mats = cmds.listConnections(m, type="shadingEngine") or []
        rows.append({
            "transform": t,
            "name": name,
            "vertices": v,
            "material_count": len(set(mats)),
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"count": len(rows), "meshes": rows}, f, indent=2)

main()
