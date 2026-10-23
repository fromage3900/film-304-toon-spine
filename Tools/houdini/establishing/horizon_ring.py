"""Procedural horizon ring for the Film 304 establishing shots (hython).

Generates raw geometry (not instances): N tower blocks on a ring around the stage origin, plus a separate mesh of
*lit window* quads with warm/cool colour baked into point Cd. Two FBX files are written so UE can give them two
materials (flat toon body / emissive windows):

    <out>/E1_horizon_body.fbx
    <out>/E1_horizon_windows.fbx
    <out>/E1_horizon_report.json

Houdini units are metres, Y-up; the FBX ROP converts to centimetres (convertunits). The camera looks down +z.

    hython Tools/houdini/establishing/horizon_ring.py --out Saved/GoalEst/horizon --seed 7 --count 220
"""
import argparse
import json
import math
import random
from pathlib import Path

import hou

WARM = (1.00, 0.62, 0.28)
COOL = (0.55, 0.78, 1.00)


def _new_geo():
    g = hou.Geometry()
    g.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    return g


def _quad(geo, pts, color, outward):
    """Add a quad whose winding faces `outward`; colour goes on the points."""
    p = [geo.createPoint() for _ in range(4)]
    for pt, pos in zip(p, pts):
        pt.setPosition(hou.Vector3(*pos))
        pt.setAttribValue("Cd", color)
    a, b, c = (hou.Vector3(*pts[i]) for i in (0, 1, 2))
    n = (b - a).cross(c - a)
    ordered = p if n.dot(hou.Vector3(*outward)) >= 0 else list(reversed(p))
    poly = geo.createPolygon()
    for pt in ordered:
        poly.addVertex(pt)


def _box(geo, cx, cz, w, d, h, color, y0=0.0):
    x0, x1, z0, z1, y1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2, y0 + h
    _quad(geo, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], color, (0, 0, -1))
    _quad(geo, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color, (0, 0, 1))
    _quad(geo, [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], color, (-1, 0, 0))
    _quad(geo, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], color, (1, 0, 0))
    _quad(geo, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], color, (0, 1, 0))


def _windows_on_face(geo, rng, origin, u_axis, normal, span_w, span_h, pitch_u, pitch_v, lit, win_w, win_h, off, y0):
    """Lit-window quads on one vertical face. `origin` is the face's lower-left corner."""
    nu = max(1, int(span_w // pitch_u))
    nv = max(1, int(span_h // pitch_v))
    count = 0
    for iu in range(nu):
        for iv in range(nv):
            if rng.random() > lit:
                continue
            cool = rng.random() < 0.15
            base = COOL if cool else WARM
            k = 0.55 + 0.45 * rng.random()
            col = (base[0] * k, base[1] * k, base[2] * k)
            u = (iu + 0.5) * pitch_u - win_w / 2
            v = y0 + (iv + 0.5) * pitch_v - win_h / 2
            ox, oy, oz = origin
            ax, az = u_axis
            p0 = (ox + ax * u + normal[0] * off, oy + v, oz + az * u + normal[2] * off)
            p1 = (p0[0] + ax * win_w, p0[1], p0[2] + az * win_w)
            p2 = (p1[0], p1[1] + win_h, p1[2])
            p3 = (p0[0], p0[1] + win_h, p0[2])
            _quad(geo, [p0, p1, p2, p3], col, normal)
            count += 1
    return count


def build(args):
    rng = random.Random(args.seed)
    body, wins = _new_geo(), _new_geo()
    placed, nwin = [], 0
    attempts = 0
    while len(placed) < args.count and attempts < args.count * 40:
        attempts += 1
        forward = rng.random() < args.forward_bias
        ang = math.radians(rng.uniform(-args.fov_half, args.fov_half)) if forward else math.radians(rng.uniform(0, 360))
        r = rng.uniform(args.rmin, args.rmax)
        cx, cz = r * math.sin(ang), r * math.cos(ang)   # angle 0 = +z (the shot direction)
        scale = 0.7 + 0.9 * (r / args.rmax)
        w = rng.uniform(28, 95) * scale
        d = rng.uniform(28, 95) * scale
        h = (35 + (rng.random() ** 2.2) * 250) * scale
        if any(math.hypot(cx - p[0], cz - p[1]) < 0.62 * (max(w, d) + max(p[2], p[3])) for p in placed):
            continue
        placed.append((cx, cz, w, d))
        tone = 0.42 + 0.18 * rng.random()
        _box(body, cx, cz, w, d, h, (tone, tone * 0.98, tone * 1.04))
        if rng.random() < 0.45:   # rooftop box
            _box(body, cx + rng.uniform(-w / 5, w / 5), cz + rng.uniform(-d / 5, d / 5), w * 0.35, d * 0.35, h * 0.06 + 3, (tone * 0.9,) * 3, y0=h)
        pitch_u, pitch_v = 5.5 + r / 550.0, 4.2 + r / 800.0
        win_w, win_h = pitch_u * 0.52, pitch_v * 0.55
        off = 0.35 + r / 4000.0
        lit = args.lit * (0.6 + 0.8 * rng.random())
        x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
        y0 = 4.0
        nwin += _windows_on_face(wins, rng, (x0, 0, z0 - 0.0), (1, 0), (0, 0, -1), w, h - y0, pitch_u, pitch_v, lit, win_w, win_h, off, y0)
        nwin += _windows_on_face(wins, rng, (x0, 0, z1), (1, 0), (0, 0, 1), w, h - y0, pitch_u, pitch_v, lit, win_w, win_h, off, y0)
        nwin += _windows_on_face(wins, rng, (x0, 0, z0), (0, 1), (-1, 0, 0), d, h - y0, pitch_u, pitch_v, lit, win_w, win_h, off, y0)
        nwin += _windows_on_face(wins, rng, (x1, 0, z0), (0, 1), (1, 0, 0), d, h - y0, pitch_u, pitch_v, lit, win_w, win_h, off, y0)
    return body, wins, len(placed), nwin


def export(geo, path, name):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bgeo = path.with_suffix(".bgeo")
    geo.saveToFile(str(bgeo))
    obj = hou.node("/obj").createNode("geo", name)
    f = obj.createNode("file", "read")
    f.parm("file").set(str(bgeo))
    f.setDisplayFlag(True)
    f.setRenderFlag(True)
    rop = hou.node("/out").createNode("filmboxfbx", name + "_rop")
    rop.parm("startnode").set(obj.path())
    rop.parm("sopoutput").set(str(path))
    rop.parm("convertunits").set(1)
    rop.parm("vcformat").set(0) if rop.parm("vcformat") else None
    rop.render()
    return path.stat().st_size if path.exists() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--count", type=int, default=220)
    ap.add_argument("--rmin", type=float, default=650.0)
    ap.add_argument("--rmax", type=float, default=3600.0)
    ap.add_argument("--forward-bias", dest="forward_bias", type=float, default=0.75)
    ap.add_argument("--fov-half", dest="fov_half", type=float, default=55.0)
    ap.add_argument("--lit", type=float, default=0.16)
    a = ap.parse_args()
    body, wins, n, nwin = build(a)
    out = Path(a.out)
    sb = export(body, out / "E1_horizon_body.fbx", "hz_body")
    sw = export(wins, out / "E1_horizon_windows.fbx", "hz_win")
    rep = {"seed": a.seed, "buildings": n, "lit_windows": nwin, "body_prims": len(body.prims()), "window_prims": len(wins.prims()),
           "body_fbx_bytes": sb, "windows_fbx_bytes": sw, "params": vars(a)}
    (out / "E1_horizon_report.json").write_text(json.dumps(rep, indent=1))
    print("[horizon_ring]", json.dumps(rep))


main()
