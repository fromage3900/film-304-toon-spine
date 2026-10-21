# Headless FBX + UV Packmaster pipeline (Film 304)

This is the supported way to move Houdini geometry into Unreal with packed UVs.

## 1. Export from Houdini (headless)

```
"C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" \
  Tools/houdini/export_headless_fbx_uv.py <scene.hip> <node_path> <out.fbx>
```

The script adds a `uvtexture` SOP when the geometry has no `uv` attribute, so the FBX
always carries a UV set for the packer.

## 2. Pack UVs in Blender (headless)

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup \
  --python-use-system-env \
  --python Tools/blender/pack_uv_with_uvpm.py -- \
  --input  path/in.fbx \
  --output path/out.fbx
```

Set `PYTHONPATH` to the UV Packmaster extension directory before running:

```
$env:PYTHONPATH = "C:\Users\<you>\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default"
```

The script marks every edge as a seam before unwrapping so that no face collapses to a
zero-area UV island (the UVPM engine rejects those). UV Packmaster then packs the
resulting islands into the 0-1 space.

## 3. Known limit

UV Packmaster's engine returns a fatal error when a single mesh contains more than
~127 UV islands. The ceiling grid ships as 127 components, so it is at the limit. If a
future asset exceeds that count, split it into sub-meshes (one FBX per component) and
pack each separately, or raise the island count by merging components in Houdini.

## 4. Verification

```
python Tools/verify_git_consistency.py
```

Check the exported FBX opens in Blender with a non-empty UV layer and that the packed
UVs lie inside 0-1.
