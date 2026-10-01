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
(scalars except `UV`). Outputs: `Pattern` (raw field) and `Mask` (hard-thresholded).

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
| `PatternDensity` | 0.5 | coverage; raise in shadow |
| `PatternScale` | 12.0 | cells per UV unit |
| `PatternAngle` | 0.0 | rotation, degrees |
| `PatternIndex` | 0.0 | `CellIndex` — which pattern |

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
- `Density` is **not yet driven from a shadow mask** in the master. The hook is there; wiring the
  terminator into `PatternDensity` per Toon Profile is the next step and is what turns this from an
  overlay into automatic shadow hatching.
- No true Voronoi/F1 cell pattern yet (Crackle approximates it with sine products).
- `MF_ProceduralPatterns` was previously **unreferenced** (audit F6); it is now called by the
  master. A profile that wants hatching sets `PatternIndex`/`PatternDensity` on its instance.