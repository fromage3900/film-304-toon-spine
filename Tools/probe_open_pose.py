"""Probe the opened David rig's FK axes and reference the spider.

Opens the source (which runs its rig setup), references C_Spider.ma, then
tests each FK axis on the body/hair bbox. Writes JSON only; saves nothing.
"""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

DAVID = "G:/film-304-toon-spine/Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
SPIDER = "G:/film-304-toon-spine/Saved/OfflineIntake/Source/C_Spider.ma"
OUT = "G:/film-304-toon-spine/Saved/Scenes/open_pose_probe.json"


def bb(nodes):
    try:
        return [round(v, 2) for v in cmds.exactWorldBoundingBox(nodes)]
    except Exception:
        return None


def main() -> None:
    out = {"tests": []}
    try:
        cmds.file(DAVID, open=True, force=True, ignoreVersion=True)
        out["david_open"] = True
        out["david_hair"] = bb("David_Hair_GEO")
        out["david_body"] = bb("David_Body_GEOShape")

        # Reference the spider (do not import; preserve its setup).
        try:
            cmds.file(SPIDER, reference=True, namespace="Spider", ignoreVersion=True,
                      mergeNamespacesOnClash=False, type="mayaAscii")
            out["spider_ref"] = True
        except Exception:
            out["spider_ref_error"] = traceback.format_exc()
        spider_meshes = cmds.ls("*:wolfSpider_Body_geoShape", type="mesh") or []
        out["spider_meshes"] = spider_meshes[:5]
        out["spider_bbox"] = bb(spider_meshes) if spider_meshes else None
        out["spider_roots"] = [n for n in (cmds.ls("*:wolfSpider*ctl", type="transform") or [])][:20]

        # Axis probe on the visible body and hair.
        body_mesh = "David_Body_GEOShape"
        hair_mesh = "David_Hair_GEO"
        for ctrl, mesh in (("FKShoulder_L", body_mesh), ("FKShoulder_R", body_mesh),
                           ("FKElbow_L", body_mesh), ("FKHip_L", body_mesh),
                           ("FKKnee_L", body_mesh), ("FKHead_M", hair_mesh)):
            if not cmds.objExists(ctrl):
                out["tests"].append({"ctrl": ctrl, "missing": True})
                continue
            base = bb(mesh)
            for axis in ("rotateX", "rotateY", "rotateZ"):
                for val in (30, -30, 60, -60):
                    if not cmds.attributeQuery(axis, node=ctrl, exists=True):
                        continue
                    try:
                        cmds.setAttr(ctrl + "." + axis, val)
                        after = bb(mesh)
                        delta = ([round(after[i] - base[i], 2) for i in range(6)]
                                 if after and base else None)
                        out["tests"].append({"ctrl": ctrl, "axis": axis, "val": val,
                                             "base": base, "after": after, "delta": delta})
                        cmds.setAttr(ctrl + "." + axis, 0)
                    except Exception:
                        out["tests"].append({"ctrl": ctrl, "axis": axis, "val": val,
                                             "error": traceback.format_exc()})
    except Exception:
        out["fatal"] = traceback.format_exc()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("OPEN_POSE_PROBE_DONE")


if __name__ == "__main__":
    main()
