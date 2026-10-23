# Tools/melusina/inventory_from_ma.py
# Inventory the imported ARP scratch Maya ASCII file.
import json, hashlib, os, datetime
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\arp_import.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"
SRC = r"G:\MelusinaRigFinalSeparate\SK_MelusinaRigARP.fbx"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def short_name(node):
    return node.split("|")[-1] if node else node

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    data = {
        "tool": "inventory_from_ma",
        "version": "1.0.0",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "maya_version": cmds.about(version=True),
        "scratch_ma": MA,
        "scratch_ma_sha256": sha256(MA),
        "source": {"path": SRC, "sha256": sha256(SRC)},
    }
    cmds.file(MA, open=True, force=True)
    joints = cmds.ls(type="joint") or []
    data["joint_count"] = len(joints)
    joint_rows = []
    for j in joints:
        parents = cmds.listRelatives(j, parent=True, fullPath=True)
        parent = short_name(parents[0]) if parents else None
        t = cmds.xform(j, q=True, ws=True, t=True)
        joint_rows.append({"name": j, "parent": parent, "translate": t})
    data["joints"] = joint_rows
    data["root_joints"] = [j for j in joints if not cmds.listRelatives(j, parent=True)]

    meshes = cmds.ls(type="mesh") or []
    mesh_rows = []
    for m in meshes:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        transform = transforms[0] if transforms else m
        name = short_name(transform)
        try:
            vcount = cmds.polyEvaluate(m, vertex=True)
        except Exception:
            vcount = -1
        shading = cmds.listConnections(m, type="shadingEngine") or []
        mats = list(dict.fromkeys(shading))
        try:
            bbox = cmds.exactWorldBoundingBox(m)
        except Exception:
            bbox = None
        history = cmds.listHistory(m) or []
        skin_clusters = cmds.ls(history, type="skinCluster")
        skin_cluster = skin_clusters[0] if skin_clusters else None
        influences = []
        if skin_cluster:
            influences = cmds.skinCluster(skin_cluster, q=True, influence=True)
        mesh_rows.append({
            "mesh": m, "transform": name, "vertices": vcount,
            "material_slots": mats, "bbox": bbox,
            "skinCluster": skin_cluster, "influence_count": len(influences),
        })
    data["meshes"] = mesh_rows
    data["mesh_count"] = len(meshes)
    data["skinned_count"] = len([r for r in mesh_rows if r["skinCluster"]])
    data["total_vertices"] = sum(r["vertices"] for r in mesh_rows if r["vertices"] > 0)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("INVENTORY COMPLETE joints=%d meshes=%d skinned=%d verts=%d" % (
        data["joint_count"], data["mesh_count"], data["skinned_count"], data["total_vertices"]))

main()
