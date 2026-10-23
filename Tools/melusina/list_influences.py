# Tools/melusina/list_influences.py
import re, json, os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\arp_import.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\body_influences.json"

def decode(name):
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

def main():
    cmds.file(MA, open=True, force=True)
    meshes = cmds.ls(type="mesh") or []
    body = None
    for m in meshes:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        if not transforms:
            continue
        name = decode(transforms[0].split("|")[-1])
        if name == "Melusina":
            body = m
            break
    result = {"body_mesh": body}
    if body:
        history = cmds.listHistory(body) or []
        skin_clusters = cmds.ls(history, type="skinCluster")
        if skin_clusters:
            sc = skin_clusters[0]
            influences = cmds.skinCluster(sc, q=True, influence=True)
            result["skinCluster"] = sc
            result["influence_count"] = len(influences)
            result["influences"] = [decode(i) for i in influences]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

main()
