# Toon Spine — Architecture & Dependency Map

## Overview

The toon spine is a single master material (`M_Master_Toon_Universal`) built on
UE 5.8's Substrate Toon BSDF. It provides:

- **Cel-shaded surface** via Substrate Toon BSDF with Toon Profile art-direction
- **Oil-paint / impressionist** blending (BaseTint ↔ AccentTint ↔ StrokeStrength)
- **SDF band relief** (world-position sine bands for architectural detail)
- **Gilding** (gold leaf overlay with emissive control)
- **Ink / pooling** (dark line work with wetness-driven roughness)
- **Temporal effects** (wind, smear, boil for hand-drawn animation feel)
- **Parallax** (height-based WPO for depth)
- **Audio reactivity** (bass/mid/treble weight — optional, for music-driven scenes)
- **Itto lane** (procedural cracks/ink wear breakup via Truchet + wear masks)
- **Madoka lane** (Voronoi vein glow + radial witch rings, emissive)
- **NikkiDreamGrade** (dreamy pastel color grading)
- **SpaceParallax** (space parallax effect)
- **ClothWindDrape** (cloth wind simulation for WPO)
- **ColorRamp3** (unified ramp: low/mid/high + contrast, shadow band tinting)
- **DF_ContactBlend** (contact blending)
- **Impressionist_Impasto** (impasto brush stroke effect)

## Dependency Graph (verified via headless UE scan)

```
M_Master_Toon_Universal
  ├── MF_ClothWindDrape          (cloth wind WPO)
  ├── MF_ColorRamp3             (unified color ramp)
  │   └── (called by MF_Itto, MF_Madoka)
  ├── MF_DF_ContactBlend        (contact blending)
  ├── MF_Impressionist_Impasto  (impasto brush strokes)
  ├── MF_Itto                   (procedural cracks/ink wear)
  │   └── MF_ColorRamp3
  ├── MF_Madoka                 (Voronoi vein glow + witch rings)
  │   └── MF_ColorRamp3
  ├── MF_NikkiDreamGrade        (dreamy pastel grade)
  ├── MF_NormalAdjust           (normal tweaking)
  ├── MF_SpaceParallax          (space parallax)
  ├── Day_to_Night_Color        ← UltraDynamicSky plugin (STRIP FOR FILM)
  └── MF_MeshBlend_Activator_Index  ← MeshBlend plugin (STRIP FOR FILM)
```

## Plugin Dependencies

**Two direct plugin dependencies:**

1. **MeshBlend** — `MF_MeshBlend_Activator_Index_0` (per-mesh material blending)
2. **UltraDynamicSky** — `Day_to_Night_Color` (sky color utility)

All 9 other MFs are clean — no plugin references.

**To strip for film:**
- Remove the `bMeshBlendActivator_Active` parameter and its MaterialFunctionCall node
- Remove the `Day_to_Night_Color` call (or replace with a simple lerp between two colors)
- Both are game-environment utilities — not needed for film/cinematic rendering

## Toon Profiles

18 Toon Profile assets provide art-direction presets:

- **TP_Default** — neutral cel shading
- **TP_Stucco** — matte architectural
- **TP_Stone** — rough stone
- **TP_Wood** — warm wood
- **TP_Gold** — metallic gold
- **TP_Glass** — translucent glass
- **TP_Foliage** — soft organic
- **TP_Ornamental** — decorative detail
- **TP_Hero** — character hero
- **TP_Character** — character base
- **TP_Melusina** — Melusina character
- **TP_NikkiDream** — dreamy pastel
- **TP_Cosmic** — cosmic/space
- **TP_Water** — water surface
- **TP_Impressionist_Wet** — wet impressionist
- **TP_Impressionist_Impasto** — impasto impressionist
- **TP_Impressionist_Dry** — dry impressionist
- **TP_Test** — test profile

## Substrate Toon BSDF

The master uses `MaterialExpressionSubstrateToonBSDF` connected to `MP_FRONT_MATERIAL`.
This is UE 5.8's experimental toon shading path, built on the Substrate framework.

Key features:
- Real lights drive the bands (not screen-space quantization)
- Coexists with Lumen GI
- Per-material stylization
- No engine fork required

## Outlines

Outlines are **not** part of the toon shader. They remain a separate concern:
- Post-process depth/normal edge detection, or
- Inverted-hull mesh overlay

The master exposes `EdgeStrength` and `InkColor` parameters for outline control,
but the actual outline pass must be set up separately in the post-process chain.

## Binary Scan Method

The dependency graph was verified by scanning the `.uasset` binary for ASCII
asset path strings. This is reliable for UE assets because asset references
are stored as full package paths in the binary. No editor required.

To re-verify: `extract_dependencies.py` in the UE editor, or binary scan with
the method described above.
