# PPV outline wiring — measured, fixed, and how to tune it

Date: 2026-10-18 · Level: `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office`
Decision: **PP-only outline** (no Houdini curvature / inverted-hull lane in this pass).

Everything below was read from live objects in the running editor, not inferred
from package names. Evidence: `Saved/Audit/PPV/wiring.json`,
`capability.json`, `outline_defaults.json`, `preset_build.json`,
`stage_ppv.json`, `verify_stage.json`, `finalize_stage.json`.

---

## 1. What was actually wired (before this pass)

| Finding | Measurement |
|---|---|
| Post-process volumes in the level | **9**, not 5: `PPV_StorybookOutline`, `PPV_P2_WatercolourPaper`, `PPV_P3_RisoPrint`, `PPV_P4_CleanCinematic`, `EST_PPV_Ink`, `PPV_ToonOutlineHalftoneStack`, `PPV_ToonOutlineOnly`, `PPV_ToonOutlineClean`, `PPV_ToonOutlineRiso` |
| Active volumes | **2 at BlendWeight 1**: `PPV_StorybookOutline` (priority 100) and `PPV_ToonOutlineHalftoneStack` (priority 200) |
| Consequence | Both applied an outline → **every edge inked twice** |
| Stencil capability | `r.CustomDepth = 1` → Custom Depth **without** stencil. `r.CustomDepthTemporalAAJitter = 1`, `r.TemporalAA.Upsampling = 1`, `r.AntiAliasingMethod = 4` (TSR) were already correct |
| Actors writing custom depth/stencil | **0 of 214** |
| Consequence | The material's entire stencil branch (`Stencilndex`, `StenciRangeMin/Max`, `Stenci*Weight`, style colours, hero-skip) could never fire |
| Un-foldered actors | **113 of 214** |
| `MI_Outline_Heavy` | **parent = None** (broken instance; MRQ gate item 6 could not pass for architecture) |
| Film-owned post MIs | 9 stale overrides each (`BaseTint`, `PaletteRampLow/Mid/High`, `TextureWeight`, `Roughness`, `Cloth_*`) left over from a reparent — these silently did nothing |
| `MI_Composite_Dither` | Actually set `GrainStrength = 0.85`, `VignetteStrength = 0.35`, `HalftoneStrength = 1.0` — grain two orders of magnitude above the researched 0.05–0.08 |
| `MI_Outline_Storybook` | Set **no** outline parameter at all; it was a copy of the Melodia instance plus stale junk |
| Inverted-hull lane | `M_Outline_InvertedHull`, `MI_Outline_Thin/Heavy` are not referenced by this level |

---

## 2. The shader's real semantics (corrects two earlier assumptions)

From the compiled custom node in `M_PP_StorybookOutline_Render2026`:

```hlsl
float distRatio = RefDistance / max(dC, 1.0);
float widthPx   = clamp(max(OutlineWidth,0.0001) * distRatio * max(InkBlurRadius,0.05),
                        max(MinWidthPx,1.0), max(MaxWidthPx,0.5));
widthPx = max(round(widthPx), 1.0);          // integer, snapped per frame
float taper  = lerp(1.0, saturate(distRatio), saturate(TaperStrength));
float falloff = 1.0 - saturate((dC - FalloffStart) / max(FalloffEnd - FalloffStart, 1.0));
// ink edges are multiplied by falloff * taper
```

**Corrections to the earlier plan:**

1. **Line length at distance is `MinWidthPx` / `MaxWidthPx`**, not a "stencil length". `OutlineWidth` is the width *in pixels at `RefDistance`*; beyond that the line thins by `RefDistance/depth` until it hits `MinWidthPx`. `InkBlurRadius` also multiplies width, so it is a width control, not only a blur.
2. **Disappearance is `FalloffStart` / `FalloffEnd`** (defaults 3000 / 8000). `DistanceFadeStart/End/Strength` only tint ink toward `AtmosphericFadeColor` — aerial perspective, not visibility. The observed "faint at 3000–4000" was `FalloffStart`.
3. **Taper** at `TaperStrength = 0` is off (constant width). The default is 0.6, which thins far lines even when `MinWidthPx` would hold them.

**Stencil classes** (read raw from `PPI_CustomStencil`):

| Value | Meaning |
|---|---|
| 0 | world / props — uses `StencilPropWeight` |
| 1–3 | style colours `Style1Color` … `Style3Color` |
| 4 | hero skip — no ink at all |
| 5 | character — uses `StencilCharacterWeight` |
| 6 | foliage — uses `StencilFoliageWeight` |

`StenciRangeMin/Max` (note the asset's spelling) and `Stencilndex` belong to
`MF_StencilDepthAlpha`; the master's current path (`V7.1`) reads the raw
stencil instead, so the class value on the component is what matters.

---

## 3. The preset ladder (built, verified, saved)

Spec: `specs/film304_look/ppv_presets.v1.json`
Builder: `Python/build_ppv_presets.py` (asset-only; no level change)

Six presets, each a pair — `MI_Outline_<id>` (child of the Melodia outline
master) and `MI_Composite_<id>` (child of `M_Master_Toon_PostComposite`):

| Preset | Use | Outline width intent | Frame halftone / grain |
|---|---|---|---|
| `Clean` | hero default, dialogue | 2 px at 6 m, 1 px at 20 m | 0.00 / 0.04 |
| `Storybook` | illustrated beats | 3 px near, 1 px far | 0.18 / 0.06 |
| `Dither` | fine ordered dither read | 3 px near, 1.25 px floor | 0.35 / 0.05 |
| `Riso` | two-colour print | 3.2 px near, 1.25 px floor | 0.45 / 0.05 |
| `Watercolour` | painterly | 3 px, sepia ink, soft mean blend | 0.00 / 0.05 |
| `SpiderMacro` | macro inserts | 4 px near, 2 px floor, tight falloff | 0.30 / 0.05 |

Widths in `preset_build.json` are computed with the shader's own arithmetic for
2 m, 6 m, 15 m, 40 m, 80 m and 200 m, so a preset's far-distance behaviour is
provable without a render.

**To make lines hold further:** raise `MinWidthPx` (hard floor), raise
`FalloffEnd` (visibility), and lower `TaperStrength` (stop thinning). To make
distant architecture read, also raise `DepthRelativeThreshold` (0.015 → 0.03):
that is the coplanar-crease threshold, and it is the only lever the PP-only
lane has for shallow slab seams.

---

## 4. What changed in this pass

- Rebuilt **12** material instances in place (`MI_Outline_{Clean,Storybook,Dither,Riso,Watercolour,SpiderMacro}`,
  `MI_Composite_{…}`), clearing stale overrides first. All 12 read back clean,
  parent asserted, saved (`preset_build.json` → `ok: true`).
- Fixed `MI_Outline_Heavy` → reparented to `M_Outline_InvertedHull`,
  `Thickness 0.02`, `ThicknessScale 1.6`, `InkColor` restored.
- Staged a single writer: `PPV_ToonOutlineClean` = 1, every other volume = 0,
  saved. Dirty set was empty before the change, so nothing unrelated was
  persisted (`stage_ppv.json`, `finalize_stage.json` → `dirty: []`).
- Archived the 32 HDA backups from `Content/Houdini/backup/` to
  `Saved/Houdini/Backups/HDA_Brutalist_ShotComposer/`, and the unreferenced
  `Content/SK_David_Film304_v01_CtrlRig_Take1.uasset` to
  `Saved/Archive/ContentStubs/`.
- A/B frames: `Saved/Audit/PPV/ppv_single_writer_clean.png.png` and
  `ppv_double_stack_ab.png.png`. The difference is **subtle in this frame**;
  the single-writer change is correct on structure, but it is not a look
  revolution and should not be sold as one.

---

## 5. Still open

1. **Stencil is still off.** `r.CustomDepth=3` in `Config/DefaultEngine.ini`,
   then write `custom_depth_stencil_value` per family (0 world/props,
   5 character, 6 foliage, 4 hero-skip). Until both happen, every
   `Stencil*Weight` in the presets is inert. Do this as an isolated change and
   re-shoot the same frame.
2. **Only 3 of 9 volumes point at a film-owned pair.** `PPV_ToonOutlineClean`,
   `PPV_ToonOutlineRiso`, `PPV_ToonOutlineHalftoneStack` still carry
   `MI_Outline_Storybook` + a composite; repoint each to its matching
   `MI_Outline_<id>`. `PPV_StorybookOutline` still carries the Melodia instance.
3. **`MI_Composite_*` blendable weight is 0.5 on Clean and 1.0 on Riso.** The
   composite is a full-frame grade, so a 0.5 blend is half a grade. Decide per
   shot; it is a look choice, not a wiring bug.
4. **113 un-foldered actors**, 21 CineCameras. Folder plan and HISM batching are
   in `Docs/SCOPED_ORGANIZATION_PLAN_20261016.md` and the Houdini docs.
5. **`PPV_StorybookOutline` vs `EST_PPV_Ink`** both reference the Melodia
   instance. `EST_PPV_Ink` is redundant once P1 is off the Melodia master.
