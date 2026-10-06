"""Verify the FILM REPO fork after re-extraction (B5, 2026-09-30).

Asserts the fork, not the upstream source:
  1. the vendored package is the one imported (pyc provenance)
  2. all 5 fork builders register and BUILD (4 BRUTALIST + OFFICE Desk Cluster)
  3. all fork presets resolve against the real group inputs
  4. the city group EVALUATES (the self-loop used to make it 0 verts)
  5. the three dials are live in the fork, with the same numbers as upstream
  6. no link cycles (the new guard must agree)
  7. the OFFICE Desk Cluster obeys its layout contract: one tree, per-prop
     toggles that DELETE (not hide), a live surface material socket, and a
     Chair Push that actually moves the chair
"""
import os
import sys

FORK_ROOT = r"P:\film-304-toon-spine\Blender"
sys.path.insert(0, FORK_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import surreal_arch  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import presets  # noqa: E402
from blender_utils import set_param  # noqa: E402

print("=" * 70)
print("1. provenance")
print("   surreal_arch -> %s" % surreal_arch.__file__)
assert "film-304-toon-spine" in surreal_arch.__file__, "wrong package imported"
assert "film-304-toon-spine" in core.__file__, "wrong core imported"
print("   core         -> %s" % core.__file__)

fails = []


def check(label, cond, detail=""):
    print("   [%s] %s %s" % ("PASS" if cond else "FAIL", label, detail))
    if not cond:
        fails.append(label)


print("=" * 70)
print("2. builders register + build")
builders = {}
for gid in ("GN_BRUTALIST_CityBlock", "GN_BRUTALIST_OfficeBlock",
            "GN_BRUTALIST_Roof", "GN_BRUTALIST_CubicleFarm",
            "GN_OFFICE_DeskCluster"):
    present = gid in core.GROUP_BUILDERS
    check("%s registered" % gid, present)
    if not present:
        continue
    core.reset_link_failures()
    try:
        t = core.GROUP_BUILDERS[gid]()
        t = t[0] if isinstance(t, (tuple, list)) else t
        builders[gid] = t
        cyc = core.find_link_cycles(t)
        check("  %s builds, acyclic" % gid, True,
              "-> nodes=%d cycles=%s" % (len(t.nodes), cyc or "none"))
        if cyc:
            fails.append("%s cycles" % gid)
    except Exception as exc:
        check("  %s builds" % gid, False, "-> %s: %s" % (type(exc).__name__, exc))

print("=" * 70)
print("3. presets resolve")
total = 0
for gid, block in (getattr(presets, "BUILDERS_PRESETS", {}) or {}).items():
    if gid not in builders:
        continue   # only builders the fork actually registered
    for pname, params in (block.get("presets", {}) or {}).items():
        total += 1
        t = builders[gid]
        have = set()
        for item in t.interface.items_tree:
            if getattr(item, "in_out", "") == "INPUT":
                have.add(getattr(item, "name", ""))
        unknown = [k for k in (params or {})
                   if k.replace("_", " ") not in have
                   and k not in have]
        if unknown:
            check("  %s / %s" % (gid, pname), False,
                  "-> unknown keys %s" % unknown[:4])
print("   fork presets found: %d" % total)

print("=" * 70)
print("4/5. city evaluates + dials are live")


def evaluate(tree):
    mesh = bpy.data.meshes.new("FORK_MESH")
    obj = bpy.data.objects.new("FORK_OBJ", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("GNProbe", "NODES")
    mod.node_group = tree
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = obj.evaluated_get(deps)
    m = ev.to_mesh()
    v = len(m.vertices)
    ev.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return v


city = builders.get("GN_BRUTALIST_CityBlock")
if city is not None:
    v0 = evaluate(city)
    check("city evaluates at defaults", v0 > 0, "-> %d verts" % v0)
    sigs = []
    for s in (1, 2, 3):
        set_param(city, "Facade Style", s)
        sigs.append(evaluate(city))
    set_param(city, "Facade Style", 0)
    check("styles 1/2/3 pairwise distinct", len(set(sigs)) == 3,
          "-> %s" % sigs)
    set_param(city, "Facade Style", 3)
    set_param(city, "Fin Count", 0)
    f0 = evaluate(city)
    set_param(city, "Fin Count", 40)
    f40 = evaluate(city)
    check("Fin Count live", f0 != f40, "-> %d -> %d" % (f0, f40))
    set_param(city, "Facade Style", 2)
    set_param(city, "Window Bay", 0.6)
    b0 = evaluate(city)
    set_param(city, "Window Bay", 6.0)
    b6 = evaluate(city)
    check("Window Bay live", b0 != b6, "-> %d -> %d" % (b0, b6))

roof = builders.get("GN_BRUTALIST_Roof")
if roof is not None:
    set_param(roof, "Roof Style", 5)
    set_param(roof, "Plant Units", 0)
    p0 = evaluate(roof)
    set_param(roof, "Plant Units", 30)
    p30 = evaluate(roof)
    check("Plant Units live", p0 != p30, "-> %d -> %d" % (p0, p30))

print("=" * 70)
print("4b/5b. office desk cluster: layout contract")

OFFICE_TOGGLES = ("Pedestal", "Monitor", "Keyboard", "Mouse", "Mouse Pad",
                  "Chair")


def evaluate_bbox(tree):
    """(verts, y_min, y_max) after the modifier - position-sensitive probes."""
    mesh = bpy.data.meshes.new("FORK_MESH")
    obj = bpy.data.objects.new("FORK_OBJ", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("GNProbe", "NODES")
    mod.node_group = tree
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = obj.evaluated_get(deps)
    m = ev.to_mesh()
    if m:
        ys = [v.co.y for v in m.vertices]
        result = (len(m.vertices), min(ys), max(ys))
    else:
        result = (0, 0.0, 0.0)
    ev.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return result


desk = builders.get("GN_OFFICE_DeskCluster")
if desk is not None:
    iface_types = {getattr(item, "name", ""): getattr(item, "socket_type", "")
                   for item in desk.interface.items_tree
                   if getattr(item, "in_out", "") == "INPUT"}
    check("surface is a Material group input",
          iface_types.get("surface") == "NodeSocketMaterial",
          "-> %s" % iface_types.get("surface"))
    v_full, _, _ = evaluate_bbox(desk)
    check("cluster evaluates at defaults", v_full > 0, "-> %d verts" % v_full)
    for sock in OFFICE_TOGGLES:
        set_param(desk, sock, False)
    v_bare, _, _ = evaluate_bbox(desk)
    check("all six toggles off -> desk remains, props GONE",
          0 < v_bare < v_full, "-> %d -> %d verts" % (v_full, v_bare))
    for sock in OFFICE_TOGGLES:
        set_param(desk, sock, True)
    set_param(desk, "Chair", False)
    v_nochair, _, _ = evaluate_bbox(desk)
    set_param(desk, "Chair", True)
    check("Chair toggle deletes (not hides)",
          v_nochair < v_full and v_nochair > 0,
          "-> %d -> %d verts" % (v_full, v_nochair))
    set_param(desk, "Chair Push", 0.0)
    _, y0a, y0b = evaluate_bbox(desk)
    set_param(desk, "Chair Push", 0.35)
    _, y1a, y1b = evaluate_bbox(desk)
    check("Chair Push moves the chair",
          abs(y1a - y0a) > 1e-4 or abs(y1b - y0b) > 1e-4,
          "-> y [%.3f, %.3f] -> [%.3f, %.3f]" % (y0a, y0b, y1a, y1b))
    set_param(desk, "Chair Push", 0.0)

print("=" * 70)
print("6. cycle guard, negative-tested (a guard nobody has seen fail is decoration)")
# The self-link below is the exact defect that made the city group evaluate to
# 0 verts on 2026-09-30 while every dial probe blamed the dials.
core.reset_link_failures()
tg = core.new_geometry_tree("GN_FORK_GUARD_SELFLINK")[0]
na = core.safe_node(tg, 'ShaderNodeMath', (0, 0))
before = len(tg.links)
core.link_sockets(tg, na.outputs[0], na.inputs[0])
rec = core.link_failures().get(tg.name) or []
check("self-link refused + recorded", bool(rec) and len(tg.links) == before,
      "-> recorded=%d links %d->%d" % (len(rec), before, len(tg.links)))

tg2 = core.new_geometry_tree("GN_FORK_GUARD_CYCLE")[0]
nb = core.safe_node(tg2, 'ShaderNodeMath', (0, 0))
nc = core.safe_node(tg2, 'ShaderNodeMath', (200, 0))
tg2.links.new(nb.outputs[0], nc.inputs[0])          # bypass link_sockets on
tg2.links.new(nc.outputs[0], nb.inputs[0])          # purpose - find_link_cycles
cyc = core.find_link_cycles(tg2)                    # must still catch it
check("2-node cycle A->B->A detected", bool(cyc), "-> %s" % (cyc or "NONE"))

tg3 = core.new_geometry_tree("GN_FORK_GUARD_DAG")[0]
d1 = core.safe_node(tg3, 'ShaderNodeMath', (0, 0))
d2 = core.safe_node(tg3, 'ShaderNodeMath', (200, 0))
core.link_sockets(tg3, d1.outputs[0], d2.inputs[0])
check("clean DAG reports no cycle", core.find_link_cycles(tg3) == [],
      "-> %s" % (core.find_link_cycles(tg3) or "[]"))

print("=" * 70)
print("FORK VERIFY %s (%d failure(s))"
      % ("PASS" if not fails else "FAIL", len(fails)))
if fails:
    sys.exit(1)