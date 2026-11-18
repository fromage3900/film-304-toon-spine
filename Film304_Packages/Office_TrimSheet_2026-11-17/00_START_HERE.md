# Office Trim Sheet — Start Here

**Assembled:** 2026-11-17 · **Author:** Brennan Shepherd
**Source meshes:** the canonical OneDrive office set (`G:/film-304-canon-onedrive`)

A 2048 × 1024 trim atlas that skins the whole Film 304 office from one texture
set — T-bar, troffer bezel, duct flange, panel trim, baseboard, mullion, blind
slat and ceiling reveal. Four maps, eight tiles, every tile **exactly seamless**.

---

## Maps

| File | Contents |
|---|---|
| `T_OfficeTrim_Height_2048x1024.png` | Trim profiles as height (drives the normal) |
| `T_OfficeTrim_Albedo_2048x1024.png` | Per-trim material tint |
| `T_OfficeTrim_Normal_2048x1024.png` | Tangent-space normal, OpenGL +Y up, derived from height |
| `T_OfficeTrim_ORM_2048x1024.png` | R = cavity AO, G = roughness, B = metallic (0) |
| `atlas_report.json` | Layout, per-tile seam measurements, conventions |

## Layout

4 × 2 grid of 512 × 512 tiles:

| | col 0 | col 1 | col 2 | col 3 |
|---|---|---|---|---|
| **row 0** | `tbar` | `troffer` | `duct` | `panel` |
| **row 1** | `base` | `mullion` | `slat` | `reveal` |

UV assignment: tile *i* occupies `u ∈ [i mod 4 / 4, (i mod 4 + 1) / 4]`,
`v ∈ [floor(i/4) / 2, (floor(i/4)+1) / 2]`.

---

## How it was made

1. **Houdini COP2** (`02_Houdini_COP/Film304_OfficeTrimSheet_v01.hip`) builds one
   network per tile — a `ramp` whose **first and last point colours are
   identical**, which is what makes the wrap column meet the start column
   exactly. Rendered to 512² tiles.
2. **Python** places the eight tiles on the atlas and derives the normal
   (Sobel on height) and ORM (cavity AO + roughness).

Measured per tile, both axes: **seam = 0.000** for height and albedo.

---

## Rebuild

```
hython 02_Houdini_COP/build_trimsheet_final.py     # tiles + hip
python 02_Houdini_COP/assemble_trimsheet.py        # atlas + normal + ORM
```

Edit the `TILES` table in the builder to change a profile; each entry is a list
of `(position, height)` pairs, and the packager closes the loop automatically.

---

## Honest scoping

- Profiles are **authoritative trim shapes** (correct silhouettes and reveals),
  not scanned surface detail. Grain/weathering is not included.
- Albedo is a flat per-trim tint; paint variation in the material.
- The atlas edges are tile **borders** and are not expected to match — the seam
  guarantee is per tile, not across the sheet.
- Mesh→texture baking (curvature from the actual office meshes) was **not**
  available in this Houdini install: there is no bake or mantra ROP, and the
  OpenGL ROP renders black headless. Curvature is therefore authored
  procedurally, not baked. See `03_Docs/TRIM_SHEET.md`.
