# Tilable Textures — Houdini COP2 Network

**Deliverable:** `06_Houdini_COP/Film304_TilableTextures_v01.hip`
**Builder:** `06_Houdini_COP/build_cop_textures_v4.py` (run with `hython`)
**Generated:** 2026-11-17 · Brennan Shepherd

Five 512 × 512 RGB textures, each **measurably seamless** — seam error
`0.000` on both axes (see `08_Evidence/seam_report.json`).

---

## 1. The problem

The repo's existing generated patterns were not actually seamless. Measured
on the source PNGs:

| Texture | seam L-R | seam T-B |
|---|---|---|
| `T_Dither_Bayer.png` | 127.0 | 127.0 |
| `T_Noise_White.png` | 79.5 | 85.7 |
| `T_HatchPattern.png` | 47.8 | 31.9 |
| `T_Hatch_Diagonal.png` | 31.9 | 31.9 |
| `T_SDF_Strokes.png` | 4.0 | 6.5 |

(Seam = mean absolute difference between opposite edge columns/rows, 0–255.)

## 2. The technique

A `ramp` COP is periodic **only if its first and last colours match**. The
builder therefore emits every band as an explicit point list whose final point
carries the same value as the first, and holds the last point just inside the
tile:

```
p1  pos 0.0        colour LO
p2  pos 1/2n       colour HI
p3  pos 2/2n       colour LO
...
p_n pos 1 - 1e-6   colour LO      <- same as p1
```

Sampling outside the last point holds at `LO`, and the first column also
samples `LO`, so the wrap column meets the start column **exactly**.

The naive alternative — a `ramp` with `cycles = k` — does **not** do this: it
produces a sawtooth that jumps from 255 back to 0 at the wrap (measured seam
255.0). Do not use `cycles` alone.

## 3. The networks

Five independent `/img` networks, one per texture. Separate networks are used
because the `comp` ROP reliably renders the network's display node; switching
display flags inside one network did not take effect.

| Network | Composition |
|---|---|
| `tx_concrete` | 3 band ramps (2 / 8 / 32 periods, horizontal + vertical) summed |
| `tx_metalpanel` | 8-period groove grid (X × Y) + 64-period fine grain on both axes |
| `tx_blinds` | 24-period vertical bands |
| `tx_hatch` | 48-period horizontal rules |
| `tx_facade` | 6-period X over 20-period Y panels |

Composite operators used: `ramp`, `add`, `multiply`, `over`, `min`, `invert`,
`blur`. No math/trig COP is available in this Houdini build, so every pattern
is built from band ramps — which is what makes the seam guarantee possible.

## 4. Rendering

A single `comp` ROP (`/out/film304_tilable_out`) renders each network:

```
coppath     /img/<network>
tres        specify
res1/res2   512
trange      normal, f1=f2=1
copoutput   <OUT>/T_Tilable_<name>_512.png
```

## 5. Rebuild / extend

1. Edit `build_cop_textures_v4.py`.
2. `hython build_cop_textures_v4.py` — re-creates the networks, re-renders, re-saves the hip.
3. Measure: compare opposite edge columns/rows; both must be `0.000`.

To add a texture: write a new band-ramp composition, add a network, add an
entry to the `jobs` list. Keep the first colour equal to the last.

## 6. Honest scoping

- These are **procedural base tiles** (albedo/height), not final production
  maps. No normal or roughness maps are generated — derive them from the
  height if needed.
- Greyscale only; tint in the material.
- 512 × 512, 8-bit PNG.
