"""Probe the fresh David rig (namespace-safe): rest bounds + face controls.

The source .mb carries an internal `David` namespace, so importing with
namespace="David" produces `David1`. All lookups here are suffix-based.
"""
from __future__ import annotations

import json
import re

import maya.cmds as cmds

SRC = "G:/film-304-toon-spine/Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
OUT = "G:/film-304-toon-spine/Saved/Scenes/david_rest_probe2.json"


def force_visible(node: str) -> None:
    if not cmds.objExists(node):
        return
    conns = cmds.listConnections(node + ".visibility", source=True, destination=False) or []
    for c in conns:
        for plug in ("outValue", "output", "visibility"):
            try:
                cmds.disconnectAttr(c + "." + plug, node + ".visibility")
                break
            except Exception:
                continue
    for lock in (False,):
        try:
            cmds.setAttr(node + ".visibility", lock=lock)
        except Exception:
            pass
    try:
        cmds.setAttr(node + ".visibility", True)
    except Exception:
        pass


def main() -> None:
    cmds.file(new=True, force=True)
    cmds.file(SRC, i=True, namespace="David1", mergeNamespacesOnClash=False,
              ignoreVersion=True, type="mayaBinary")

    # Reset FK controls by suffix.
    for c in cmds.ls("*:FK*", type="transform") or []:
        for attr in ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"):
            if not cmds.attributeQuery(attr, node=c, exists=True):
                continue
            try:
                if not cmds.getAttr(c + "." + attr, lock=True):
                    cmds.setAttr(c + "." + attr, 0)
            except Exception:
                pass

    # Visible the root group and all non-helper mesh transforms.
    for g in cmds.ls("*:Group", type="transform") or []:
        force_visible(g)
    meshes = cmds.ls(type="mesh", long=True) or []
    for m in meshes:
        tr = (cmds.listRelatives(m, parent=True) or [m])[0]
        name = m.split("|")[-1]
        if "Orig" in name or "Base" in name:
            continue
        force_visible(tr)

    visible = []
    recs = []
    for m in meshes:
        name = m.split("|")[-1]
        if "Orig" in name or "Base" in name:
            continue
        tr = (cmds.listRelatives(m, parent=True) or [m])[0]
        try:
            vis = bool(cmds.getAttr(tr + ".visibility"))
        except Exception:
            vis = False
        rec = {"mesh": name, "transform": tr, "visible": vis,
               "bbox": [round(v, 3) for v in cmds.exactWorldBoundingBox(m)]}
        recs.append(rec)
        if vis:
            visible.append(m)

    bbox = [round(v, 3) for v in cmds.exactWorldBoundingBox(visible)] if visible else None
    face = [c for c in (cmds.ls("*", type="transform") or [])
            if re.search(r"(brow|mouth|lid|jaw|cheek|nose|lip|eye|tongue|teeth)", c, re.I)]
    positions = {}
    for suffix in ("FKHead_M", "FKNeck_M", "FKChest_M", "FKWrist_L", "FKWrist_R",
                   "FKAnkle_L", "FKAnkle_R", "FKRoot_M", "RootX_M", "IKXRoot_M"):
        nodes = cmds.ls("*:" + suffix, type="transform") or []
        if nodes:
            positions[suffix] = [round(v, 3) for v in cmds.xform(nodes[0], q=True, ws=True, t=True)]

    data = {
        "source": SRC,
        "visible_mesh_count": len(visible),
        "all_mesh_count": len(recs),
        "visible_bbox": bbox,
        "visible_size": [round(bbox[i + 3] - bbox[i], 3) for i in range(3)] if bbox else None,
        "face_controls": face,
        "positions": positions,
        "meshes": recs,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    cmds.file(rename="G:/film-304-toon-spine/Saved/Scenes/_david_rest_probe2.mb")
    cmds.file(save=True, type="mayaBinary", force=True)
    print("DAVID_PROBE2_OK", json.dumps({k: data[k] for k in
          ("visible_mesh_count", "visible_bbox", "visible_size")}))


if __name__ == "__main__":
    main()
