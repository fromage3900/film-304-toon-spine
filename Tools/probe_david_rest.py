"""Probe the fresh David rig: rest-pose bounds, visible meshes, face controls.

Run headless via the dcc-mcp Maya session (execute_python file_path).
Writes Saved/Scenes/david_rest_probe.json.
"""
from __future__ import annotations

import json
import re

import maya.cmds as cmds

SRC = "G:/film-304-toon-spine/Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
OUT = "G:/film-304-toon-spine/Saved/Scenes/david_rest_probe.json"


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
    try:
        cmds.setAttr(node + ".visibility", lock=False)
    except Exception:
        pass
    try:
        cmds.setAttr(node + ".visibility", True)
    except Exception:
        pass


def main() -> None:
    cmds.file(new=True, force=True)
    cmds.file(
        SRC,
        i=True,
        namespace="David",
        mergeNamespacesOnClash=False,
        ignoreVersion=True,
        type="mayaBinary",
    )

    # Reset FK controls to rest.
    for c in cmds.ls("David:FK*", type="transform") or []:
        for attr in ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"):
            if not cmds.attributeQuery(attr, node=c, exists=True):
                continue
            try:
                if not cmds.getAttr(c + "." + attr, lock=True):
                    cmds.setAttr(c + "." + attr, 0)
            except Exception:
                pass

    # Make the body and partial body visible.
    for n in ("David:David_Body_GEO", "David:David_PartialBody_GEO", "David:David_Body_breathe"):
        force_visible(n)

    # Measure visible, non-rest-shape meshes.
    visible = []
    all_meshes = []
    for m in cmds.ls("David:*", type="mesh", long=True) or []:
        tr = (cmds.listRelatives(m, parent=True) or [m])[0]
        name = m.split("|")[-1]
        if "Orig" in name or "Base" in name:
            continue
        try:
            vis = bool(cmds.getAttr(tr + ".visibility"))
        except Exception:
            vis = False
        rec = {"mesh": name, "transform": tr, "visible": vis,
               "bbox": [round(v, 3) for v in cmds.exactWorldBoundingBox(m)]}
        all_meshes.append(rec)
        if vis:
            visible.append(m)

    bbox = [round(v, 3) for v in cmds.exactWorldBoundingBox(visible)] if visible else None

    # Face controls / relevant controls.
    face = [c for c in (cmds.ls("David:*", type="transform") or [])
            if re.search(r"(brow|mouth|lid|jaw|cheek|nose|lip|eye|tongue|teeth)", c, re.I)]

    positions = {}
    for c in ("David:FKHead_M", "David:FKNeck_M", "David:FKChest_M",
              "David:FKWrist_L", "David:FKWrist_R",
              "David:FKAnkle_L", "David:FKAnkle_R", "David:FKRoot_M",
              "David:RootX_M", "David:IKXRoot_M"):
        if cmds.objExists(c):
            positions[c] = [round(v, 3) for v in cmds.xform(c, q=True, ws=True, t=True)]

    data = {
        "source": SRC,
        "namespace": "David",
        "visible_mesh_count": len(visible),
        "all_mesh_count": len(all_meshes),
        "visible_bbox": bbox,
        "visible_size": [round(bbox[i + 3] - bbox[i], 3) for i in range(3)] if bbox else None,
        "face_controls": face,
        "positions": positions,
        "meshes": all_meshes,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    cmds.file(rename="G:/film-304-toon-spine/Saved/Scenes/_david_rest_probe.mb")
    cmds.file(save=True, type="mayaBinary", force=True)
    print("DAVID_PROBE_OK", json.dumps({k: data[k] for k in
          ("visible_mesh_count", "visible_bbox", "visible_size")}))


if __name__ == "__main__":
    main()
