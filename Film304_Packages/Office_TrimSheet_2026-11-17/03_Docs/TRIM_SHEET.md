# Office Trim Sheet — technical notes

## 1. What a trim sheet is for

One texture set skins many repeated parts. Instead of a unique texture per
mesh, every part maps onto a region of a shared atlas. That keeps texture
memory flat as the set grows and lets one material serve the whole office.

The eight profiles here cover the office's repeated dressing:

| Tile | Use | Profile character |
|---|---|---|
| `tbar` | ceiling suspension grid | raised rib, 120 cm bay |
| `troffer` | light fixture bezel | twin frame, 134 × 105 cm |
| `duct` | HVAC trunk/branch | paired flanges at segment joints |
| `panel` | wall panel edge | narrow raised edge bead |
| `base` | baseboard | stepped base profile |
| `mullion` | window mullion | centre ridge |
| `slat` | blind slats | alternating slat/gap |
| `reveal` | ceiling tile edge | recessed groove |

## 2. Seamlessness

Each tile is a `ramp` COP whose **first and last point colours are identical**,
with the final point placed at `1 − 1e-6`. Sampling past it holds the last
value, so the wrap column equals the start column exactly.

Measured (`atlas_report.json` → `per_tile_seams`), all eight tiles, height and
albedo, both axes: **0.000**.

Do **not** use a `ramp` with `cycles = k` for this — it produces a sawtooth that
jumps from 255 back to 0 at the wrap (measured seam 255.0).

## 3. Normal map

Derived from height with a Sobel kernel, strength 2.0:

```
n = normalize(-dH/dx * s,  dH/dy * s,  1)   ->  RGB = n*0.5 + 0.5
```

OpenGL convention (+Y up). Invert the green channel if a DirectX pipeline
complains.

## 4. ORM

- **R** — cavity AO from the height field (deeper = darker).
- **G** — roughness, higher where the surface is darker (recesses read rougher).
- **B** — metallic, 0 (all dielectrics).

## 5. Known limits

- **No mesh baking in this install.** Houdini 22.0.368 here exposes no `bake`
  ROP and no `mantra`; the `opengl` ROP renders a black frame headless. So
  curvature/edge-wear from the *actual* office meshes could not be baked, and
  the curvature response is authored procedurally in the profiles instead.
  If a bake-capable Houdini is available, the same atlas UVs can be baked into
  directly.
- **Albedo is a flat tint.** The COP2 `multiply` with a `color` COP did not
  take (the colour feeds as alpha); the per-tile tint is applied in the
  assembler instead. Noted so the provenance is not misread.
- **No surface grain.** These are authoritative trim *shapes*; add grain in the
  material or a detail normal.

## 6. Source meshes

`G:/film-304-canon-onedrive/3D Models/FBX Files/` (from
`Downloads/OneDrive_2026-11-17.zip`) — 107 FBX including `O_BreakRoomWall_ZMJ`,
`BreakRoomTogether_ZMJ`, `O_WallWindow_ZMJ`. The repo previously held several
of these only as `.uasset`.
