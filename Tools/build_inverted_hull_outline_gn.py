"""Build a reusable Geometry Node group for inverted-hull outlines.

Run:
  blender --background --factory-startup --python Tools/build_inverted_hull_outline_gn.py

Writes Saved/Blender/InvertedHullOutline.blend containing the group
MEL_InvertedHullOutline (input Geometry + Thickness, output Geometry).
"""
from __future__ import annotations

import bpy
from pathlib import Path

ROOT = Path("G:/film-304-toon-spine")
OUT = ROOT / "Saved" / "Blender" / "InvertedHullOutline.blend"
OUT.parent.mkdir(parents=True, exist_ok=True)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    name = "MEL_InvertedHullOutline"
    old = bpy.data.node_groups.get(name)
    if old is not None:
        for n in list(old.nodes):
            old.nodes.remove(n)
        tree = old
    else:
        tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.is_modifier = True
    tree.use_fake_user = True

    iface = tree.interface
    for item in list(iface.items_tree):
        if getattr(item, "item_type", "") == "SOCKET":
            iface.remove(item)
    iface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    iface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    iface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for item in iface.items_tree:
        if item.name == "Thickness" and item.in_out == "INPUT":
            item.default_value = 0.012
            item.min_value = 0.0
            item.max_value = 0.5

    gin = tree.nodes.new("NodeGroupInput")
    gin.location = (-600, 0)
    gout = tree.nodes.new("NodeGroupOutput")
    gout.location = (600, 0)

    normal_node = tree.nodes.new("GeometryNodeInputNormal")
    normal_node.location = (-400, -200)
    try:
        normal_node.domain = "POINT"
    except Exception:
        pass

    scale_vec = tree.nodes.new("ShaderNodeVectorMath")
    scale_vec.operation = "SCALE"
    scale_vec.location = (-200, -200)
    tree.links.new(normal_node.outputs["Normal"], scale_vec.inputs["Vector"])
    tree.links.new(gin.outputs["Thickness"], scale_vec.inputs["Scale"])

    setpos = tree.nodes.new("GeometryNodeSetPosition")
    setpos.location = (0, 0)
    tree.links.new(gin.outputs["Geometry"], setpos.inputs["Geometry"])
    tree.links.new(scale_vec.outputs["Vector"], setpos.inputs["Offset"])

    flip = tree.nodes.new("GeometryNodeFlipFaces")
    flip.location = (200, 0)
    tree.links.new(setpos.outputs["Geometry"], flip.inputs["Mesh"])

    merge = tree.nodes.new("GeometryNodeMergeByDistance")
    merge.location = (400, 0)
    try:
        merge.inputs["Distance"].default_value = 0.0001
    except Exception:
        pass
    tree.links.new(flip.outputs["Mesh"], merge.inputs["Geometry"])

    tree.links.new(merge.outputs["Geometry"], gout.inputs["Geometry"])

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    print("SAVED_GN", OUT)


if __name__ == "__main__":
    build()





