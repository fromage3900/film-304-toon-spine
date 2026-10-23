# Tools/melusina/arp_inventory.py
# Read-only inventory of Melusina's ARP rig FBX using Maya 2027 mayapy.
import json, hashlib, os, datetime, sys
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds, mel

SRC = r"G:\MelusinaRigFinalSeparate\SK_MelusinaRigARP.fbx"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"

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
        "tool": "arp_inventory",
        "version": "1.0.0",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "maya_version": cmds.about(version=True),
        "maya_product": cmds.about(product=True),
        "source": {
            "path": SRC,
            "size_bytes": os.path.getsize(SRC),
            "sha256_before": sha256(SRC),
        },
    }
    cmds.file(newFile=True, force=True)
    cmds.currentUnit(linear="cm", time="film", angle="deg")
    cmds.upAxis(ax="y")
    import_ok = True
    try:
        cmds.loadPlugin("fbxmaya", quiet=True)
        mel.eval("FBXResetImport")
        mel.eval('FBXImportMode -v "add"')
        mel.eval("FBXImportFillTimeline -v true")
        fbx_path = SRC.replace("\\", "/")
        mel.eval('FBXImport -f "%s"' % fbx_path)
    except Exception as exc:
        import_ok = False
        data["import_error"] = str(exc)
        print("IMPORT ERROR: %s" % exc)
    data["import_ok"] = import_ok

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
            "mesh": m,
            "transform": name,
            "vertices": vcount,
            "material_slots": mats,
            "bbox": bbox,
            "skinCluster": skin_cluster,
            "influence_count": len(influences),
        })
    data["meshes"] = mesh_rows
    data["mesh_count"] = len(meshes)
    data["skinned_count"] = len([r for r in mesh_rows if r["skinCluster"]])
    data["total_vertices"] = sum(r["vertices"] for r in mesh_rows if r["vertices"] > 0)
    data["source"]["sha256_after"] = sha256(SRC)
    data["source_intact"] = data["source"]["sha256_before"] == data["source"]["sha256_after"]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("ARP INVENTORY COMPLETE joints=%d meshes=%d skinned=%d intact=%s" % (
        data["joint_count"], data["mesh_count"], data["skinned_count"], data["source_intact"]))

main()
