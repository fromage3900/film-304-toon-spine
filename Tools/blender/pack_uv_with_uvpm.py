"""Headless Blender helper: import FBX, ensure UVs, attempt UV Packmaster pack, export FBX.

Usage:
  blender --background --factory-startup --python-use-system-env \
    --python Tools/blender/pack_uv_with_uvpm.py -- \
    --input  path/in.fbx \
    --output path/out.fbx \
    --addon-path "C:/Users/<you>/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/user_default"

Notes:
  * UV Packmaster 3 must be installed and its engine registered.
  * If the engine returns a fatal error, the script still exports the mesh with its
    existing UVs so the pipeline does not lose geometry.
"""
import argparse
import os
import sys

import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--addon-path", default=os.path.join(
        os.path.expanduser("~"),
        "AppData", "Roaming", "Blender Foundation", "Blender", "5.2",
        "extensions", "user_default"))
    return p.parse_args(argv)


def enable_uvpm(addon_path):
    if addon_path not in sys.path:
        sys.path.insert(0, addon_path)
    bpy.ops.preferences.addon_enable(module="uvpackmaster3")
    # UVPM pack operator requires a scenario id when invoked headless.
    try:
        bpy.types.UVPACKMASTER3_OT_pack.SCENARIO_ID = "pack.general"
    except Exception:
        pass


def ensure_uv(obj):
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    # Mark every edge as a seam so each face becomes its own island; this avoids
    # degenerate (zero-area) UV islands that the UVPM engine rejects.
    bpy.ops.mesh.mark_seam(clear=False)
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001)
    bpy.ops.object.mode_set(mode="OBJECT")


def main():
    args = parse_args()
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Clean scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.import_scene.fbx(filepath=input_path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("No mesh objects found in FBX")
    obj = meshes[0]

    try:
        enable_uvpm(args.addon_path)
        uvpm_available = True
    except Exception as exc:
        print("UVPM enable failed:", repr(exc))
        uvpm_available = False

    ensure_uv(obj)

    if uvpm_available:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.uvpackmaster3.pack("EXEC_DEFAULT", pack_op_type="0")
            print("UVPM pack: OK")
        except Exception as exc:
            print("UVPM pack failed (exporting with existing UVs):", repr(exc))
        bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True)
    print("EXPORTED:", output_path)


if __name__ == "__main__":
    main()
