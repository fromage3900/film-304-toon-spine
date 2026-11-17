"""Probe partial-body skinning, jaw blendshape, and spider root control."""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

OUT = "G:/film-304-toon-spine/Saved/Scenes/david_skin_probe3.json"


def bbox(sub: str):
    ms = [m for m in (cmds.ls(type="mesh", long=True) or [])
          if sub in m and "Orig" not in m]
    return [round(v, 2) for v in cmds.exactWorldBoundingBox(ms)] if ms else None


def mesh_info(sub: str):
    ms = [m for m in (cmds.ls(type="mesh", long=True) or [])
          if sub in m and "Orig" not in m]
    rec = []
    for m in ms:
        hist = cmds.listHistory(m) or []
        scs = [h for h in hist if cmds.nodeType(h) == "skinCluster"]
        inf = {}
        for s in scs:
            inf[s] = (cmds.skinCluster(s, q=True, influence=True) or [])[:60]
        rec.append({"mesh": m, "scs": scs, "inf": inf})
    return rec


def main() -> None:
    out = {}
    try:
        cmds.file("G:/film-304-toon-spine/Saved/Scenes/_david_rest_probe2.mb",
                  open=True, force=True, ignoreVersion=True)
        for sub in ("David_PartialBody_GEO", "David_Body_breathe",
                    "David_Body_GEO", "David_Shirt_GEO"):
            out[sub] = mesh_info(sub)

        out["chin_before"] = bbox("ChinRegionShape")
        if cmds.objExists("David1:BM_Regions"):
            try:
                cmds.setAttr("David1:BM_Regions.David_BMH_JawOpen", 1.0)
                out["chin_jawBS1"] = bbox("ChinRegionShape")
                cmds.setAttr("David1:BM_Regions.David_BMH_JawOpen", 0.0)
            except Exception:
                out["jawBS_err"] = traceback.format_exc()

        sp = [m for m in (cmds.ls(type="mesh", long=True) or []) if "Spider:" in m]
        out["spider_before"] = ([round(v, 2) for v in cmds.exactWorldBoundingBox(sp)]
                                if sp else None)
        for node in ("Spider:wolfSpider_Body_ctl", "Spider:wolfSpiderRig"):
            if cmds.objExists(node):
                try:
                    cmds.setAttr(node + ".translateY", 100)
                    out[node + "_after"] = [round(v, 2) for v in cmds.exactWorldBoundingBox(sp)]
                    cmds.setAttr(node + ".translateY", 0)
                except Exception:
                    out[node + "_err"] = traceback.format_exc()
        out["spider_ctl_attrs"] = (cmds.listAttr("Spider:wolfSpider_Body_ctl",
                                                 userDefined=True) or [])[:60]
    except Exception:
        out["fatal"] = traceback.format_exc()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("SKIN3_DONE")


if __name__ == "__main__":
    main()
