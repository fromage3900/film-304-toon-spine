"""Test FK controls against the visible, fully-skinned body mesh."""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

OUT = "G:/film-304-toon-spine/Saved/Scenes/david_fk_test.json"


def bb(sub: str):
    ms = [m for m in (cmds.ls(type="mesh", long=True) or [])
          if sub in m and "Orig" not in m and "Base" not in m]
    return [round(v, 2) for v in cmds.exactWorldBoundingBox(ms)] if ms else None


def main() -> None:
    out = {"tests": []}
    try:
        cmds.file("G:/film-304-toon-spine/Saved/Scenes/_david_rest_probe2.mb",
                  open=True, force=True, ignoreVersion=True)
        # Make the body visible
        for n in ("David1:David_Body_GEO", "David1:David_PartialBody_GEO"):
            if cmds.objExists(n):
                try:
                    cmds.setAttr(n + ".visibility", True)
                except Exception:
                    pass
        before = bb("David_Body_GEOShape")
        out["body_bbox"] = before

        def test(label, node, attr, val, sub="David_Body_GEOShape"):
            b = bb(sub)
            rec = {"label": label, "node": node, "attr": attr, "val": val, "before": b}
            if not cmds.objExists(node):
                rec["missing"] = True
                out["tests"].append(rec)
                return
            try:
                cmds.setAttr(node + "." + attr, val)
                a = bb(sub)
                rec["after"] = a
                rec["delta"] = [round(a[i] - b[i], 2) for i in range(6)] if a and b else None
                cmds.setAttr(node + "." + attr, 0)
            except Exception:
                rec["error"] = traceback.format_exc()
            out["tests"].append(rec)

        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKShoulder_L " + axis, "David1:FKShoulder_L", axis, 30)
        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKElbow_L " + axis, "David1:FKElbow_L", axis, 30)
        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKHip_L " + axis, "David1:FKHip_L", axis, 30)
        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKKnee_L " + axis, "David1:FKKnee_L", axis, 30)
        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKHead_M " + axis, "David1:FKHead_M", axis, 30)
        for axis in ("rotateX", "rotateY", "rotateZ"):
            test("FKJaw_M " + axis, "David1:FKJaw_M", axis, 20)
        for axis in ("translateX", "translateY", "translateZ"):
            test("FKRoot_M " + axis, "David1:FKRoot_M", axis, 10)
    except Exception:
        out["fatal"] = traceback.format_exc()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("FK_TEST_DONE")


if __name__ == "__main__":
    main()
