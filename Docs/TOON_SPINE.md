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

## Dependency Graph

```
M_Master_Toon_Universal
  ├── MF_ToonCharacterSurfaceCore        (toon surface logic)
  ├── MF_MooaToonBaseInput_2             (Mooa toon encoding)
  ├── MF_MooaEncodeAttributes            (attribute packing)
  ├── MF_MooaDecodeAttributes            (attribute unpacking)
  ├── MF_UVTransform                     (UV manipulation)
  ├── MF_UVChannelSwitch                 (UV channel selection)
  ├── MF_NormalAdjust                    (normal tweaking)
  ├── MF_Triplanar                       (triplanar projection)
  ├── MF_Triplanar_Stable                (stable triplanar)
  ├── MF_ParallaxCore                    (parallax mapping)
  ├── MF_RealParallax                    (real parallax)
  ├── MF_UniversalMacroDetail            (macro detail)
  ├── MF_SDF_BandRelief                  (SDF banding)
  ├── MF_SDF_UtilityToolkit_Core         (SDF utilities)
  └── MF_TranslucencyShadowToOpacityMask (translucency → opacity)
```

## Stripped Dependencies

The following were in the original game project but are **not needed** for film:

| MF / Plugin | Why stripped |
|-------------|--------------|
| MF_MeshBlend_Activator_Index_1 | MeshBlend plugin (game-specific mesh blending) |
| MF_Water* (15 files) | Water simulation (game-specific) |
| MF_Nikki* (14 files) | Nikki character effects (game-specific) |
| MF_ClothWindDrape | Cloth simulation (game-specific) |
| MF_VertexPaintBlend | Vertex paint (game-specific) |
| MF_UberBlendMode | Uber blend mode (game-specific) |
| MF_SpaceParallax | Space parallax (game-specific) |
| MF_Melodia* (2 files) | Melodia-specific effects |
| MF_Melusina_SDFIris | Character-specific SDF |

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
