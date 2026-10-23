"""Cook the Film 304 Brutalist Shot Composer HDA headlessly and dump its instance points to JSON.

Why: the Houdini Engine plugin in the editor reported cook errors on this HDA (no message surfaced)
while the same .hda cooks cleanly in hython, so shots are composed headlessly and placed in UE from this file.

Run:
    & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" \\
        Tools/houdini/brutalist_composer/cook_to_json.py --mode 0 --out Saved/GoalEst/e1_points.json \\
        [--set cam_posx=-5 --set cam_posy=2.8 --set cam_posz=-25 ...]

Units in the JSON are Houdini metres (Y-up); `Python/place_composer_json.py` converts to UE cm (x, z, y).
"""
import argparse
import json
from pathlib import Path

import hou

REPO = Path(__file__).resolve().parents[3]
HDA = REPO / "Content" / "Houdini" / "HDA_Brutalist_ShotComposer.hda"
ATTRS = ["unreal_instance", "unreal_material_instance", "unreal_material", "unreal_material_0", "unreal_material_1",
         "unreal_material_instance_0", "unreal_material_instance_1", "category", "asset_name"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", action="append", default=[], help="parm=value (float/int/bool; use parm=v1,v2,v3 for tuples)")
    a = ap.parse_args()

    hou.hda.installFile(str(HDA))
    geo = hou.node("/obj").createNode("geo", "cook")
    n = geo.createNode("film304_brutalist_shot_composer", "composer")
    n.parm("scene_mode").set(a.mode)
    for kv in a.set:
        k, v = kv.split("=", 1)
        if k in ("cam_pos", "cam_target"):  # tuples are exposed as cam_posx/y/z in the SOP; accept both spellings
            for axis, val in zip("xyz", v.split(",")):
                n.parm(k + axis).set(float(val))
            continue
        p = n.parm(k)
        if p is None:
            raise SystemExit(f"unknown parm {k}")
        t = p.parmTemplate().type()
        p.set(float(v) if t == hou.parmTemplateType.Float else int(float(v)))
    n.cook(force=True)
    g = n.geometry()
    pts = []
    for p in g.points():
        pos = p.position()
        row = {"p": [pos[0], pos[1], pos[2]]}
        for k in ATTRS:
            try:
                row[k] = p.attribValue(k)
            except hou.OperationFailed:
                pass
        for k in ("rot", "scale", "orient", "Cd"):
            try:
                row[k] = list(p.attribValue(k))
            except hou.OperationFailed:
                pass
        pts.append(row)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"mode": a.mode, "set": a.set, "errors": list(n.errors()), "count": len(pts), "points": pts}, indent=1))
    print(f"[cook_to_json] mode {a.mode}: {len(pts)} points -> {out} errors={list(n.errors())}")


main()
