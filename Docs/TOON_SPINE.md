# Toon spine — architecture and dependency map

Rewrite 2026-09-30. The previous version of this file described the **source** project it was
extracted from, not this repo: it listed 12 material functions (`MF_Madoka`, `MF_Itto`,
`MF_ClothWindDrape`, `Day_to_Night_Color`, …), 18 toon profiles (`TP_Melusina`, `TP_Stucco`,
`TP_Wood`, `TP_Glass`, `TP_Impressionist_*`), and a `MeshBlend` plugin dependency. **None of those
exist here.** Anyone following it looked for assets that were never extracted.

Everything below is from the files in this repo: `Content/` and `Python/`.

## What the spine is

Two master materials, three material functions, eleven toon profiles and ten instances — a
Substrate Toon shading spine that a film can shoot with, with no game-system dependencies.

```
Content/Materials/
  Masters/       M_Master_Toon_Universal      the spine
                 M_Outline_InvertedHull       the outline pass
  Functions/     MF_ColorRamp3                 ramp generation
                 MF_RampLUT                    LUT-driven ramp lookup
                 MF_ProceduralPatterns         hatching / pattern source
  ToonProfiles/  TP_Default  TP_Stone  TP_Foliage  TP_Gold  TP_Hero
                 TP_Hatched  TP_TwoTone  TP_Environment  TP_SoftPainterly
                 TP_Warm  TP_Cool
  Instances/     MI_Toon_{Hero,Stone,Foliage,Gold,Hatched,TwoTone,Painterly,Environment}
                 MI_Outline_{Thin,Heavy}
```

## Dependency graph

Verified two ways: the builders' own expected-call lists
(`Python/build_spine.py` asserts `["MF_ColorRamp3", "MF_RampLUT"]` for the master), and a
binary scan of `M_Master_Toon_Universal.uasset` that reads the `/Game/...` package references
out of the file. Both agree, and that agreement is the point — a copied master can keep a
structurally valid graph with **zero** function calls and still look fine in the editor (that
happened in the source project: 751,265 → 666,458 bytes with all ten `MaterialFunctionCall`
references silently gone).

```
M_Master_Toon_Universal
├── MF_ColorRamp3          ramp / band generation
└── MF_RampLUT             LUT-driven ramp lookup into the ramp from ColorRamp3

M_Outline_InvertedHull     standalone; no MF dependencies

TP_*  (11)                 data assets read by the master's Toon Profile input
MI_*  (18 instances)       inherit from the two masters
```

`MF_ProceduralPatterns` is built and shipped but **nothing references it** in the current graph.
That is a known open question, not a discovery — see `Docs/AUDIT_2026-09-30.md`.

## Plugin dependencies

**None.** The uproject enables only what a content project needs:

```json
"Plugins": [ MovieRenderPipeline, PythonScriptPlugin ]
```

Specifically absent, and deliberately so: `MeshBlend` (in the source project the master called
`MF_MeshBlend_*` functions), the water simulation, and the Nikki character-effect materials. If
you find a dangling function call, it is a missed extraction — report it, do not re-add the
plugin.

## Toon profiles

A Toon Profile is a **data asset** that the master reads, not a material. That is what lets one
master serve a cel-shaded hero, a soft-ramped background and everything between without
duplicating the graph.

They are authored through `MaterialInstance.import_text` because `ToonProfile` only exposes
`settings` as a property — that constraint was probed rather than assumed
(`Python/build_toon_profiles.py`), and `verify_profile` asserts against the **imported text**,
not against a log line.

## Substrate Toon

`Config/DefaultEngine.ini` sets `r.Substrate=True` and
`r.Substrate.OpaqueMaterialRoughRefraction=False`; Substrate is default-on in 5.7+. The master
terminates in `MaterialExpressionSubstrateToonBSDF`, with BaseColor / Roughness / Normal wired
from the graph.

**Substrate Toon is experimental in UE 5.8.** Expect parameters to move. Validate against real
content in the first week, not the last.

## Outlines

Outlines are **not** part of the toon shader. This repo ships the inverted-hull approach:

- `M_Outline_InvertedHull` — unlit hull material
- `MI_Outline_Thin` (characters) / `MI_Outline_Heavy` (architecture)

The post-process alternative (depth/normal edge detection) is described in
`Docs/FILM_PIPELINE.md` and is not implemented here.

## How to re-derive any of this

Do not trust this document alone — re-derive it. All three methods are cheap:

```powershell
# 1. the builders assert their own expected calls and write a report
UnrealEditor-Cmd.exe MelodiaToonFilm.uproject -ExecutePythonScript="Python/build_spine.py" -stdout -unattended

# 2. the dependency trace, written to Saved/DependencyMap.json
#    (run inside the editor)
py "Python/extract_dependencies.py"

# 3. a binary scan for /Game/... package references - no editor needed
```

If this file and method 1 disagree, **method 1 is right** and this file is the bug.
