# SDF pattern pipeline — analytic shadow hatching for the 304 film

**Written 2026-10-01.** Status: implemented and wired; the spine rebuild asserts on it.
Companion to `Docs/TOON_SPINE.md` (the spine architecture) and `Docs/BRUTALIST_SET.md` (the set).

## 1. The problem this solves

A cel-shaded film needs *painted* detail that a PBR texture cannot give: hatching in shadow,
screentone on a flat wash, stipple on plaster, engraving lines on stone. Three facts shape the
solution:

1. **UE 5.8's Substrate Toon BSDF is experimental**, and its Toon Profile exposes shadow hatching
   only as `ShadowHatchingPatternTexture / Size / Strength` — a *texture*, one pattern per profile.
   (`build_toon_profiles.py` documents the field surface.)
2. **A texture bakes to a mip pyramid.** Hatching built from a texture blurs, swims and moirés as
   the camera moves — exactly what a film camera does. Hard, stable lines want an *analytic* field.
3. **Indie film budget.** Every pattern must be free to author, regenerate from code, and cheap to
   vary per character/prop without a new master material.

So the spine carries `MF_ProceduralPatterns`: an analytic pattern function the master inks through,
with a coverage knob an artist can drive from shadow.

## 2. Why "SDF" here means analytic distances, not Unreal distance fields

**UE 5.8 ships no usable SDF authoring node.** Only `DistanceFieldApproxAO` / `DistanceFieldGradient`
exist, and those read a mesh's *baked* field — they can sample, they cannot author a shape.
(`build_mf_patterns.py` records the probe.)

So every pattern is a **signed-distance-style field computed analytically** on a UV lattice and
hard-thresholded with `SmoothStep`. Halftone is the distance to a lattice point; cross-hatch is the
distance to two rotated line families; rings are the distance to the origin. Constructions follow the
standard 2D signed-distance catalogue (see §7).

Two consequences worth keeping in mind:

- **Crisp at any zoom.** The threshold is a step, so ink does not soften with distance.
- **No texture memory, no tiling-texture UV seams** — the field is a function of UV.

## 3. The pattern catalogue

`MF_ProceduralPatterns` inputs: `UV`, `Scale`, `Softness`, `Angle`, `CellIndex`, `Density`
(scalars except `UV`) and `SDFMap` (texture2D, the baked stroke field for CellIndex 12 —
must be connected by every caller; the master feeds it a `PatternSDFMap`
`TextureObjectParameter` defaulting to `T_SDF_Strokes`). Outputs: `Pattern` (raw field)
and `Mask` (hard-thresholded).

| `CellIndex` | Pattern | Construction | Use for |
|---|---|---|---|
| 0 | Halftone | offset dot lattice, distance to cell centre | screen-print cell shading |
| 1 | Checker | `Frac` on each axis, `If`-stepped | graphic flat, prop texture |
| 2 | Stripes | `Abs(Frac)` of one axis | hard parallel bars |
| 3 | Crackle | product of two rotated sines, fractionalised | Worley-ish breakup, ruin/plaster |
| 4 | InkSplat | rings around a lattice centre | high-contrast pooling |
| 5 | CrossHatch | `Min` of two 45° line fields (`u±v`) | engraving, pencil hatch, stone |
| 6 | Stipple | `Frac(Sin(u*12.9898 + v*78.233)*43758.5453)` | dry-brush, graphite grain |
| 7 | Rings | `Frac(Length(u, v))` | manga focal-line screentone burst |
| 8 | Voronoi | F1: 3×3 cell search, per-cell feature point from `Frac(Sin(dot(cell,k)) * 43758.5453)`, squared distances through `Min`, one `Sqrt` at the end | true F1 cell breakup — concrete, plaster, exposed aggregate |
| 9 | Grid | `Max` of `Abs(Frac(u)−0.5)` and `Abs(Frac(v)−0.5)`, ×2 | grout lines — drop-ceiling tile, carpet tile |
| 10 | Perforation | `1 − Saturate(Length(cell centre offset) × 1.4142)` | round holes — acoustic panel, speaker grille |
| 11 | Weave | warp/weft chosen by `Frac((Floor(u)+Floor(v))×0.5)×2` parity | over-under textile — cubicle fabric, acoustic cloth |
| 12 | SDFMap | TextureSample of `T_SDF_Strokes` at the rotated/scaled UV: R = continuous triangle of the wrapped stroke coordinate, shifted by (G−0.5)×0.22 per-stroke width jitter | hand-inked wavy hatch with wide soft edges — the analytic fields cannot blur without aliasing; this one is filtered. ANY `T_SDF_*` map rides this cell via per-instance `PatternSDFMap` |
| 13 | SubwayTile | running-bond courses (row parity from scalar ty, grout = Max of centred axes ×2) | kitchen/washroom tile |
| 14 | Blinds | broad slat faces (1−triangle) + lift cords at tx quarters | window walls |
| 15 | PaperFiber | fine two-axis laid grain gated by cell hash | paper tooth, texture-free |
| 16 | Brushed | per-column (tx) hash phase streaks | brushed steel, no banding |
| 17 | Chevron | true zigzag: column position vs triangle(row) | baffles, lobby walls |
| 18 | FrostBands | smooth sine gradient bands (the only soft analytic) | frosted glazing |

Rows 13–18 added 2026-10-06 (Office Spider). Rows 1, 5, 11 were
REWRITTEN the same day: the selector that routes them was inverted (every
index rendered field 0 — proven by code trace against live pin names, see
`build_mf_patterns.py`), and three cells were degenerate at the default
angle (checker = impulse, weave parity ≡ 0, crosshatch family B = 0)
because they derived independent axes from the identical float2 frame.
The axis rule is now in the builder docstring; headless proof (all 18
baked maps tile + selector identity + cell mirrors) is
`Saved/Audit/texture_office_verify_2026-10-06.json`.

Row 12 was added 2026-10-03. It is the texture sibling of row 5: the baked field is a
continuous triangle of the wrapped stroke coordinate (`|2·Frac(s)−1|`, 1 at the stroke
centre, 0 midway — row 9's polarity), so bilinear filtering yields wide clean soft edges
and a sine displacement bends the strokes organically. `T_SDF_Strokes` is generated by
`Python/build_textures.py` (256², sRGB off, wrap, lossless, no mips) and tiles exactly.
The R field flows through the same `Density`/`Softness` cut as every other pattern, and
the G hash jitters each stroke's half-width by up to ~11% of the spacing — the variance
that makes hatching read as hand ink rather than an engraving rule.

### The tilable SDF map library (2026-10-03, office set 2026-10-06)

`T_SDF_Strokes` grew into a library of eighteen RG maps, all generated by
`build_textures.py`, all tile-exact, all in the same two-channel contract:

| Map | Field (R) | G channel | Made for |
|---|---|---|---|
| `T_SDF_Strokes` | wavy diagonal stroke family, 1 at the stroke centre | per-stroke width hash | pen hatching, leaf veining |
| `T_SDF_Cross`   | `max` of two sine-displaced `(u±v)` families | per-stroke width hash | engraving cross-hatch |
| `T_SDF_Dots`    | soft-edged dots, half-offset lattice (even row count) | per-dot size hash | screentone with hand variance |
| `T_SDF_Scales`  | arc ring of the row-above circle (half-offset rows) | per-cell width hash | Melusina's tail, roof tiles, feathers |
| `T_SDF_Cracks`  | Worley border `F2−F1`, inverted to mark polarity | per-cell width hash | stone, dry earth, plaster |
| `T_SDF_Leaf`    | unioned capsule cover, 1 inside (soft silhouette) | spare (flat 128) | foliage master's opacity mask |
| `T_SDF_CarpetLoop` | elliptical loops, per-loop lean offset | lean/width hash | carpet pile (dots stays generic) |
| `T_SDF_CeilingTile` | pin grid + seeded fissures (edged-margined) | cell hash | acoustic drop-ceiling |
| `T_SDF_WeaveFine` | continuous thread crowns, true parity | cell hash | cubicle cloth, chair fabric |
| `T_SDF_Blinds`  | slat faces + cords at u .25/.75 | slat hash | window walls |
| `T_SDF_PaperGrain` | faint two-axis fibre, capped ~0.5 | fibre hash | paper close-ups |
| `T_SDF_Woodgrain` | streaks warped by integer swell | streak hash | laminate desk tops |
| `T_SDF_Brushed` | full-length phased streaks | column hash | steel, filing, legs |
| `T_SDF_Cork`    | fat kissing blobs | granule hash | bulletin boards |
| `T_SDF_VCT`     | border-peaked grout + speckle | speckle hash | break-room floors |
| `T_SDF_WhiteboardGhost` | wide soft arcs, capped 0.35 | arc hash | wiped-board ghosts |
| `T_SDF_FrostBands` | smooth sine bands (only smooth map) | flat hash | door glazing |
| `T_SDF_Cardboard` | kraft flute + full-mark speckle | speckle hash | donut box |

Every map is 256², sRGB off (data), wrap-addressed, lossless, no mips. The wrap
correctness criterion (and what `Saved/Audit/sdf_map_audit.json` asserts): the wrap
texel step must not exceed the tile's worst interior step — a period-correct field
tiles seamlessly by construction, and a real seam (a field element crossing the tile
edge) shows up as a wrap step the interior never produces. That criterion caught two
generator bugs on first authoring: the scales arc was placed two rows up (field read
all-zero) and the leaf falloff crossed the tile edge.

Consumption: `PatternSDFMap` on the master (a `TextureObjectParameter`) is
per-instance swappable, so any instance can point `PatternIndex = 12` at any map.
The map's R rides the same `Density`/`Softness` cut and the same shadow-driven
density as the analytic patterns; the G channel can be wired for width jitter when a
look wants it (the strokes-family jitters it internally on `CellIndex 12`).

Rows 8–11 were added 2026-10-02 for the office film. Row 8 closes the gap this document
recorded in §8 ("No true Voronoi/F1 cell pattern yet"): the earlier single-cell
approximation would only have been a jittered lattice, so the 3×3 neighbourhood search is
the real thing. Squared distance through `Min` is exact — `Sqrt` is monotonic, so the
argmin is unchanged — and it costs one square root instead of nine.

`Softness` is the edge width of the threshold — the *only* knob that softens the line. Keep it near
0.02 for cel work; raise it for a printed/painterly edge.

## 4. The knob that makes it film-usable: `Density`

`Density` (0..1) is **the level the field is cut against** — not a blend weight. At `Density = 0.5`
the pattern covers half the surface; raise it and more of the field passes the threshold, so the
hatch gets denser. That is precisely how a cel painter hatches into shadow: one direction in the
light, cross-hatch in the mid-tone, dense/near-solid in the core shadow.

The intended film workflow:

```
Toon diffuse ramp (Toon Profile)   -> band structure
MF_ProceduralPatterns              -> hatch field
Density  <- shadow terminator mask -> hatch densifies through the terminator
PatternStrength                    -> how much ink at all (0 = off)
```

`PatternStrength` defaults to **0**, so every material instance built before this change renders
identically until an artist opts in.

## 5. How it is wired

`M_Master_Toon_Universal` calls the function and inks `final_color` toward `InkColor` through the
mask. Parameters live in the **`Pattern`** group so they sort together in the MI editor:

| Parameter | Default | Meaning |
|---|---|---|
| `PatternStrength` | 0.0 | ink amount; 0 = off |
| `PatternIndex` | 0.0 | `CellIndex` — which pattern |
| `PatternScale` | 12.0 | cells per UV unit |
| `PatternAngle` | 0.0 | rotation, degrees |
| `PatternDensity` | 0.5 | hatch coverage in **light** |
| `PatternHatchShadowDensity` | 0.85 | hatch coverage in **shadow** |
| `PatternHatchShadowDrive` | 1.0 | how much the shadow mask drives density (0 = manual only) |
| `KeyLightDir` | (0,0,1) | key light direction for the hatch shadow mask |

`build_spine.py` asserts the master's `expected_calls` now includes `MF_ProceduralPatterns`, so the
wiring cannot silently vanish the way the 2026-09-29 cross-project copy lost all ten calls.

## 6. Authoring rules (this repo)

- **Change `Python/build_mf_patterns.py`, never the `.uasset`.** Regenerate with
  `build_spine.py` (see `Docs/TOON_SPINE.md` for the exact headless command).
- **Assert on the report file** (`%TEMP%/spine_build_report.json`), not the log.
- A per-character/prop look is a **material instance**, not a master copy
  (`Docs/CONTENT_CONVENTIONS.md`).
- Adding a pattern means: a `_name()` field function, an entry in the `fields` dict, a `scales`
  slot, and a docstring/table row here.

## 7. Research references

- Inigo Quilez, *2D distance functions* (iquilezles.org/articles/distfunctions2d) — the canonical
  catalogue of circle/box/segment distance fields these patterns are built from.
- Inigo Quilez, *Voronoi / cellular* and *Domain repetition* — the construction family behind
  Crackle; a true F1 Voronoi cell pattern is the natural next addition.
- Epic, *Substrate Toon* (UE 5.8) — the Toon BSDF and Toon Profile surface this composes with;
  experimental in 5.8, expect the parameter surface to move.
- StraySpark, *UE 5.8 Substrate Toon Shader Tutorial* and Proj Prod, *New Substrate Toon Shader in
  UE 5.8* — both confirm the practical split this repo already uses: **the toon shader owns surface
  shading; outlines stay a separate pass** (here `M_Outline_InvertedHull`).
- The GLSL hash `frac(sin(dot(p, k)) * m)` used by Stipple is the standard cheap value hash
  (constants `12.9898 / 78.233 / 43758.5453`).

## 8. Known limits / open work

- `PatternIndex` is a scalar `If` chain, not a static switch — deliberate, so one instance can
  switch pattern without a recompile; the cost is a few extra ALU ops.
- `Density` **is** driven from a shadow mask (implemented 2026-10-01): `KeyLightDir · Normal` →
  saturate → one-minus → scaled by `PatternHatchShadowDrive` → blended from `PatternDensity`
  (light) to `PatternHatchShadowDensity` (shadow). The mask is **hatch-only** — the Toon Profile
  still owns the band structure, so this does not become a second terminator authority.
  `PatternHatchShadowDrive = 0` returns density to fully manual.
- The shadow mask reads its own `PixelNormalWS` rather than reusing the master's later `normal`
  node — that node is defined after this block, and referencing it raised `NameError` on the first
  build attempt (caught by the spine report, not by a log line).
- A true Voronoi/F1 cell pattern is **no longer open** — added 2026-10-02 as
  `CellIndex 8` (3×3 neighbourhood, feature point per cell). Crackle remains the cheap
  approximation for surfaces that do not justify the ~90 extra nodes.
- `MF_ProceduralPatterns` was previously **unreferenced** (audit F6); it is now called by the
  master. A profile that wants hatching sets `PatternIndex`/`PatternDensity` on its instance.