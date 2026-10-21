"""Headless Houdini helper: load a hip file and export selected geometry to FBX with UVs.

Usage (hython):
  hython Tools/houdini/export_headless_fbx_uv.py <hip_file> <node_path> <output_fbx>

Example:
  hython Tools/houdini/export_headless_fbx_uv.py scene.hip /obj/geo1/output out.fbx
"""
import os
import sys

import hou


def main():
    if len(sys.argv) < 4:
        print("Usage: hython export_headless_fbx_uv.py <hip> <node> <out_fbx>")
        sys.exit(2)

    hip_path, node_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    hou.hipFile.load(hip_path, suppress_save_prompt=True)

    node = hou.node(node_path)
    if node is None:
        raise SystemExit("Node not found: {}".format(node_path))

    # Ensure a UV attribute exists; create one if missing.
    geo = node.geometry()
    if geo is None or "uv" not in [a.name() for a in geo.pointAttribs()]:
        uv_node = node.createOutputNode("uvtexture")
        uv_node.parm("type").set(0)  # Per-vertex UV
        node = uv_node

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    rop = hou.node("/out").createNode("filmboxfbx")
    rop.parm("soppath").set(node.path())
    rop.parm("sopoutput").set(out_path)
    rop.parm("execute").pressButton()
    print("EXPORTED:", out_path)


if __name__ == "__main__":
    main()
