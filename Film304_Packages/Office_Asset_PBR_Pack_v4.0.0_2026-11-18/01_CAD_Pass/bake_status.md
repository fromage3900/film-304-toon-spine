# Bake status — mesh → texture curvature

**Date:** 2026-11-17 · **Author:** Brennan Shepherd
**Verdict: NOT ACHIEVED in this Houdini install.** Recorded so the claim is not
over-read.

## What was tried

Houdini 22.0.368 **Indie**, headless via `hython`.

The ROP is `baketexture` (not `bake` — `bake` does not exist, which is what an
earlier probe wrongly concluded meant "no baking available"). It exposes
curvature baking directly: `vm_bake_curvaturesdist`, `vm_bake_curvaturesscale`,
`vm_uvhires1` for hi-res → low-res.

Three attempts:

| Attempt | Config | Result |
|---|---|---|
| v1 | `vm_uvtype=udim`, pattern `%(CHANNEL)s.%(UDIM)d` | 2048² TGA written, **all black** (source was a flat 4-point plane with no UVs) |
| v2 | `vm_uvtype=udim`, 1024², unwrapped | **~1,000 spurious black frames** — the `%(…)` pattern was never substituted, so output names became `…%.%-<pid>.tga` and mantra rendered per-tile |
| v3 | `vm_uvtype=uv`, literal filename, 512², unwrapped, `rop.errors()` read | `rop.render()` → `hou.OperationFailed`; with the object present it **hangs >7 min** and leaves a **corrupt 2,591-byte stub** that no image reader can open |

`rop.errors()` on a stale object path reported
`No match for object 1: '/obj/bake_mullion'`, confirming the ROP does validate
its object — but with a valid object it still fails.

## Root cause (best reading)

The `baketexture` ROP depends on mantra UV-render support that this Indie
install does not carry. `mantra.exe` exists, but the ROP cannot complete a UV
bake — it errors or hangs rather than rendering.

## Also found — the canon FBX have no UVs

Every canon FBX checked ships **without a UV attribute**:

```
O_BreakRoomWall_ZMJ.fbx    pts=4     prims=2     uv=False
O_BreakRoomShelf_ZMJ.fbx   pts=152   prims=284   uv=False
O_Counter_ZMJ.fbx          pts=216   prims=209   uv=False
SM_VenetianBlinds_Bay.fbx  pts=144   prims=108   uv=False
SM_Houdini_Office_Ceiling_Tiles.fbx pts=3200 prims=2400 uv=False
```

So no tool can bake them as-is. An unwrap pass must come first, regardless of
which baker is used.

## What to use instead

**Adobe Substance 3D Painter is installed** (`C:\Program Files\Adobe\Adobe
Substance 3D Painter`) and it is the tool the group already uses — the canon
OneDrive drive contains **69 `.spp` projects** (`T_BreakRoomWall_JCF`,
`T_CarpetFloor_JCF`, …). Painter bakes curvature, AO, normal, position,
thickness and world-space normal from a hi-res source, and it is where these
canon assets were textured in the first place.

Fallback: Blender 5.2 Cycles bake (also installed).

## What this means for the trim sheet

The curvature response in `02_TrimSheet/` is **authored procedurally** into the
trim profiles, not baked from the meshes. That is stated in the trim-sheet
docs; this file is the evidence.
