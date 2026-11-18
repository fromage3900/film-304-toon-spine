"""UV unwrap + pack the canonical office assets in Blender, headless.

Uses the installed addons where they actually run headless, and Blender's
built-in UV tools otherwise. Records which packer produced each result.

Run:
    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b \
        --factory-startup -P Blender/uv_unwrap_pack_canon.py
"""
import bpy, os, sys, json, math, traceback
import addon_utils

ROOT = r"G:\film-304-toon-spine"
CANON = r"G:\film-304-canon-onedrive\3D Models\FBX Files"
OUT = os.path.join(ROOT, "Film304_Packages", "Office_UV_Unwrapped_2026-11-17")
FBI = os.path.join(OUT, "01_FBX")
UVI = os.path.join(OUT, "02_UVLayouts")
os.makedirs(FBI, exist_ok=True)
os.makedirs(UVI, exist_ok=True)

# ---- enable the owner's addons -------------------------------------------
ADDONS = ("uvpackmaster3", "ZenUtils", "SimpleBake", "BL_BakeLab2")
enabled, failed = [], {}
for name in ADDONS:
    try:
        addon_utils.enable(name, default_set=True)
        enabled.append(name)
    except Exception as e:
        failed[name] = repr(e)[:120]

UVPM_OPS = []
try:
    import bpy as _b
    UVPM_OPS = [o for o in dir(_b.ops.uvpackmaster3) if not o.startswith("_")]
except Exception:
    pass

# ---- asset list: the office + break-room set ------------------------------
ASSETS = sorted({n for n in os.listdir(CANON) if n.lower().endswith(".fbx")})

TEXEL_DENSITY = 10.0     # px per cm at 1024 texture
ANGLE = math.radians(66.0)

report = {"blender": bpy.app.version_string, "addons_enabled": enabled,
          "addons_failed": failed, "uvpm3_ops": UVPM_OPS,
          "texel_density": TEXEL_DENSITY, "assets": []}


def unwrap_object(obj, use_uvpm):
    """Smart-project + pack one object's UVs. Returns a result dict."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    packer = "blender"
    try:
        bpy.ops.uv.smart_project(angle_limit=ANGLE, island_margin=0.02,
                                 area_weight=0.0, correct_aspect=True,
                                 scale_to_bounds=False)
    except Exception as e:
        bpy.ops.uv.unwrap(method='ANGLE', margin=0.02)
        packer = "blender-fallback-unwrap"

    try:
        bpy.ops.uv.average_islands_scale()
    except Exception:
        pass

    if use_uvpm:
        done = False
        for op in ("pack", "pack_islands", "pack_mode"):
            fn = getattr(getattr(bpy.ops, "uvpackmaster3", None), op, None)
            if fn is None:
                continue
            try:
                fn()
                packer = "uvpackmaster3.%s" % op
                done = True
                break
            except Exception:
                continue
        if not done:
            try:
                bpy.ops.uv.pack_islands(margin=0.02)
            except Exception:
                pass
    else:
        try:
            bpy.ops.uv.pack_islands(margin=0.02)
        except Exception:
            pass

    bpy.ops.object.mode_set(mode="OBJECT")

    # UV stats
    uv = me.uv_layers.active.data
    lo = [1e9, 1e9]
    hi = [-1e9, -1e9]
    for loop in uv:
        u, v = loop.uv
        lo[0] = min(lo[0], u); lo[1] = min(lo[1], v)
        hi[0] = max(hi[0], u); hi[1] = max(hi[1], v)
    return {"packer": packer,
            "uv_lo": [round(lo[0], 4), round(lo[1], 4)],
            "uv_hi": [round(hi[0], 4), round(hi[1], 4)],
            "uv_area": round(max(0.0, (hi[0] - lo[0]) * (hi[1] - lo[1])), 4),
            "loops": len(uv), "polys": len(me.polygons)}


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.scene.new(type="NEW")

for name in ASSETS:
    path = os.path.join(CANON, name)
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=path, use_custom_normals=True)
    except Exception as e:
        report["assets"].append({"file": name, "error": "import: %s" % repr(e)[:160]})
        continue
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not new:
        report["assets"].append({"file": name, "error": "no mesh imported"})
        continue

    results = []
    for obj in new:
        try:
            r = unwrap_object(obj, use_uvpm=bool(UVPM_OPS))
        except Exception as e:
            r = {"error": repr(e)[:200]}
        results.append(r)

    # export FBX with UVs
    out_fbx = os.path.join(FBI, name)
    try:
        bpy.ops.object.select_all(action="DESELECT")
        for o in new:
            o.select_set(True)
        bpy.ops.export_scene.fbx(filepath=out_fbx, use_selection=True,
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                                 mesh_smooth_type="FACE", add_leaf_bones=False)
        exported = os.path.exists(out_fbx)
    except Exception as e:
        exported = False
        report["assets"].append({"file": name, "error": "export: %s" % repr(e)[:160]})

    # UV layout image
    layout = None
    try:
        bpy.ops.object.select_all(action="DESELECT")
        for o in new:
            o.select_set(True)
        bpy.context.view_layer.objects.active = new[0]
        bpy.ops.uv.export_layout(filepath=os.path.join(UVI, name.replace(".fbx", "") + ".png"),
                                 mode="PNG", size=(1024, 1024), opacity=0.0,
                                 export_all=True, modified=False)
        layout = os.path.join(UVI, name.replace(".fbx", "") + ".png")
        layout = layout if os.path.exists(layout) else None
    except Exception:
        layout = None

    report["assets"].append({"file": name, "objects": len(new),
                             "exported": exported, "uv_layout": layout,
                             "results": results})
    # drop for the next file
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)

with open(os.path.join(OUT, "uv_report.json"), "w") as fh:
    json.dump(report, fh, indent=2, default=str)

ok = [a for a in report["assets"] if a.get("exported")]
print("BLENDER UV RUN DONE: %d/%d exported, addons=%s, uvpm_ops=%s"
      % (len(ok), len(ASSETS), enabled, UVPM_OPS), flush=True)
for a in report["assets"][:6]:
    print("  ", a.get("file"), a.get("exported"), (a.get("results") or [{}])[0].get("packer"),
          (a.get("results") or [{}])[0].get("uv_area"), flush=True)
