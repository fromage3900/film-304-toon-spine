# Toon spine — architecture and dependency map

Rewrite 2026-09-30. The previous version of this file described the **source** project it was
extracted from, not this repo: it listed 12 material functions (`MF_Madoka`, `MF_Itto`,
`MF_ClothWindDrape`, `Day_to_Night_Color`, …), 18 toon profiles (`TP_Melusina`, `TP_Stucco`,
`TP_Wood`, `TP_Glass`, `TP_Impressionist_*`), and a `MeshBlend` plugin dependency. **None of those
exist here.** Anyone following it looked for assets that were never extracted.

Everything below is from the files in this repo: `Content/` and `Python/`.

## What the spine is

Sixteen masters (the fourteen `build_spine.py` builds plus the two Painterly
assets), five material functions, **twenty-six** toon profiles, **thirty-four**
instances and **nineteen** generated textures — a Substrate Toon shading spine that a
film can shoot with, with no game-system dependencies.

Counts are the **tracked** set — what a fresh clone actually receives (`git ls-files`
under `Content/Materials/`). A further 132 `.uasset` files sit untracked in
`Masters/` and `Functions/`: they are a byte-identical copy of Melodia assets whose
internal `/Game/...` paths still point at Melodia, so none of them resolve here.
`specs/humber_toon_spine/melodia_intake_manifest.v1.json` records why raw `.uasset`
copying is not an intake channel. Do not count them.

```
Content/Materials/
  Masters/       M_Master_Toon_Universal      the spine (opaque surfaces)
                 M_Master_Toon_Character      the character spine master (TP_Melusina)
                 M_Master_Toon_Foliage        masked two-sided cards, sway WPO
                 M_Master_Toon_Water          stylized water, scrolling ripple normal
                 M_Master_Toon_Sky            banded sky dome (unlit, no Toon Profile)
                 M_Master_Toon_Landscape      ground planes with macro variation
                 M_Master_Toon_Face           skin shading with an authored shadow layer
                 M_Master_Toon_Hair           anisotropic read from a root-to-tip ramp
                 M_Master_Toon_Glass          toon interior + fresnel-only edge
                 M_Master_Toon_EmissiveFX     unlit pattern glow, optional pulse
                 M_Master_Toon_Particles      unlit sprite chain, translucent
                 M_Master_Toon_PostComposite  the film-wide grade, one shared writer
                 M_Toon_Unlit_Character       the shadowless character master
                 M_Outline_InvertedHull       the outline pass
                 M_PainterlyGouache           the gouache look (standalone, + _Inst)
  Functions/     MF_ColorRamp3                 ramp / band generation
                 MF_RampLUT                    LUT-driven ramp lookup
                 MF_ProceduralPatterns         analytic + baked pattern field (13 patterns)
                 MF_PBRDetail                  detail/height shaping
                 MF_RimOffset                  view/normal-space rim into EmissiveColor
  ToonProfiles/  TP_Default  TP_Stone  TP_Foliage  TP_Gold  TP_Hero
                 TP_Hatched  TP_TwoTone  TP_Environment  TP_SoftPainterly
                 TP_Warm  TP_Cool  TP_Water  TP_Melusina  TP_Character
                 TP_Landscape  TP_Face  TP_Hair  TP_Glass
                 TP_Office_{Carpet,Laminate,DropCeiling,Troffer,
                            PowderCoat,Screen,Polypropylene,Whiteboard}
  Instances/     MI_Toon_{Hero,Stone,Foliage,Gold,Hatched,TwoTone,Painterly,
                            Environment,Office_*,Melusina,Character,Scales,
                            CrackedStone,Sky,Landscape,Face,Hair,Glass,
                            EmissiveFX,Particles,PostComposite}
                 MI_Foliage_{Fern,Hedge}      on the foliage master
                 MI_Water_{Canal,Puddle}      on the water master
                 MI_Outline_{Thin,Heavy}
  Textures/      T_Dither_Bayer  T_Hatch_{Cross,Diagonal}  T_HatchPattern
                 T_Ramp_{2Band,3Band,4Band,Smooth}  T_Noise_White
                 T_SDF_{Strokes,Cross,Dots,Scales,Cracks,Leaf}   tilable SDF map library
```

Counts at the top of this file are the tracked inventory as of the 2026-10-05
freeze commit. The latest headless spine build (run 2, 2026-10-05) reported
4/4 functions, 14/14 masters, 26/26 profiles, 32/32 instances, 15/15 textures,
3/3 pattern overrides, office set 8/8 assigned, `errors: []` —
**`OVERALL: PASS`** (the instance stage covers the 32 `MI_Toon_*`/`MI_Foliage_*`/
`MI_Water_*`; the two `MI_Outline_*` are built by `build_m_outline.py`, giving
the 34 on disk).

**`M_Master_Toon_Character` now exists.** It was previously "code, not an
asset": `Python/build_master_toon_character.py` was committed and registered in
`build_spine.py`, but the headless run had been held deliberately because a
second Unreal process could not be started safely alongside a running editor.
The 2026-10-05 staging build generated it, so `MI_Toon_Melusina` and
`MI_Toon_Scales` now pick up `TP_Melusina` through it as authored.

Two changes in the 2026-10-02 pass:

- **`MF_ProceduralPatterns` gained four patterns in this pass** — `Voronoi`, `Grid`,
  `Perforation` and `Weave` were added for the office film, taking the set to 12 at
  that point; the 2026-10-03 SDF work added a 13th (`_sdfmap`, CellIndex 12), which
  is what the tree above counts. The table in `Docs/SDF_PATTERN_PIPELINE.md` §3 is
  the authority for each.
- **The `ToonProfile` texture fields now resolve.** `ShadowHatchingPatternTexture` and
  `DiffuseRampOffsetTexture` were `None` on every profile here; they now bind against
  `Content/Materials/Textures/`, generated by `Python/build_textures.py`, which runs
  **before** the profiles in `build_spine.py`. Note that the manifest's
  `shading_pipeline.hatching_pattern` (`T_HatchPattern`) was a **dangling reference in this
  repo *and* in Melodia** — the asset existed in neither.

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

TP_*  (26)                 data assets read by the master's Toon Profile input
MI_*  (34 instances)       inherit from the masters
```

`MF_ProceduralPatterns` is called by the master since 2026-10-02 (hatch density is
shadow-driven; see `Docs/SDF_PATTERN_PIPELINE.md` §5). The "unreferenced" audit finding (F6)
is closed.

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

## State 2026-10-05: staging build — run 1 FAIL, three fixes, run 2 PASS

The 2026-10-05 staging run was the first full 14-master headless build. Run 1
reported `OVERALL: FAIL`: two builders failed their own verify and PostComposite
failed its shader compile, and in both cases the defect was invisible to the
in-process checks because the broken node instantiated without error — only the
shader compile rejected it.

1. **Dead Unlit function (`M_Master_Toon_EmissiveFX`, `M_Master_Toon_Particles`).**
   Both builders called `/Engine/Functions/Engine_MaterialFunctions02/Shading/
   BasicShading/Unlit.Unlit`, which does not exist in UE 5.8: `load_asset`
   returns `None`, a null `MaterialFunctionCall` is saved, verify's `calls=1`
   counted the dead call, and the report read "Unlit function call not found".
   Both now terminate in `MaterialExpressionSubstrateUnlitBSDF` wired from
   BaseColor — the pattern `M_Toon_Unlit_Character` and `M_Master_Toon_Sky`
   already used (those two never failed).
2. **`M_Master_Toon_PostComposite` shader failure.** The report read ok=true at
   graph level, but the shader compile failed twice:
   `SceneColor lookups are only available when MaterialDomain = Surface` —
   a `MaterialExpressionSceneColor` node Python can instantiate is still illegal
   in `MD_POST_PROCESS`; the scene source is now
   `MaterialExpressionSceneTexture` with `InputId = PPI_POST_PROCESS_INPUT0`
   (the dreamprint pattern) — and `Arithmetic between types float2 and float3`
   in the vignette, which used the float3 `lib.constant`; it is now a
   `MaterialExpressionConstant2Vector`.

Run 2 (`Saved/Logs/build_spine_run2_unlit_pp_fix.log`): **`OVERALL: PASS`** —
4/4 functions, 14/14 masters, 26/26 profiles, 32/32 instances, 15/15 textures,
3/3 pattern overrides, office set 8/8 assigned, `errors: []`, and no
post-rebuild `LogMaterial` compile failure (the single `Failed to compile`
line in the log is the startup load of run 1's stale on-disk PostComposite,
before the rebuild). Binary checks on the saved `.uasset` files confirm
`SubstrateUnlitBSDF` present in EmissiveFX/Particles with no `BasicShading`
reference, and `SceneTexture` + `Constant2Vector` present with no
`MaterialExpressionSceneColor` in PostComposite. Gates after the build:
`Tools/verify_all.ps1` 9/9 PASS, `Tools/dogfood_toon_spine.py --all` 6/6 PASS.

The run-2 editor process exited 3 on a teardown-only crash
(`EXCEPTION_ACCESS_VIOLATION` in `UnrealEditor-SemanticSearch.dll`, ~7 s after
`saved dirty packages` and the report write) — post-save shutdown noise, not a
build defect; run 1 had exited 0.

## State 2026-10-03: six graph defects fixed, full rebuild PASS

The 2026-10-02 session found and fixed six build-order/wiring defects in the generated graph
(each was live in the editor's compiled material, not just in code):

1. `MF_ColorRamp3` `Power` pin names were `A`/`B` on this 5.8 build (code said `Base`/`Exp`) —
   the ramp exponent was silently unwired.
2. `MF_ColorRamp3` fed its own output back into an input (`Reentrant expression found`).
3. `MF_ProceduralPatterns` `Length` parameter was unwired at four sites — pattern cells
   collapsed to 0-scale (the "no patterns visible" symptom).
4. The master's `PatternSoftness` function input was never connected (pattern edges were
   hard-coded hard).
5. `MF_RampLUT`'s sampler `Tex` input was unwired — the LUT slot did nothing.
6. The master's `RampTexture` slot was a `TextureSampleParameter2D` (float3) feeding a
   texture2D input — `Cannot cast from float3 to texture2D`. It is now a
   `TextureObjectParameter` with `T_Ramp_Smooth` as default.

`build_spine.py` full rebuild: **OVERALL PASS** — 4 MFs verified, 18/18 instances verified,
office set 8/8 assigned, zero `LogMaterial` compile failures. The spine report
(`%TEMP%/spine_build_report.json`) is the assertion surface.

**Visual lookdev on this machine is driver-blocked.** UE 5.8 caps this laptop's D3D12 feature
level at SM5 (`LogRHI: Using Highest Feature Level of D3D12: SM5`, NVIDIA driver 527.56) and
Substrate requires SM6 — so every Substrate material, including a trivial red control, renders
the default material here. This is an RHI gate, not a spine defect: `-d3d12TargetedShaderModel=SM6`
does not lift it (capability check, not preference). Until the NVIDIA driver is updated (or lookdev
runs on the desktop), verify structure via the spine report and treat any on-screen capture of
Substrate materials on this machine as invalid. Capture instruments additionally need a
control-first check (`capture_material_grid` rendered default for a plain red material even
independent of the RHI gate).

## Next: SDF map creation (the 2026-10-03 focus)

Sequenced so each step lands in the builder + report, not the .uasset:

1. **DONE 2026-10-03 — baked SDF maps as a pattern source.** `T_SDF_Strokes`
   (RG: continuous triangle distance + per-stroke width jitter) is generated by
   `build_textures.py`; `MF_ProceduralPatterns` gained an `SDFMap` texture2D
   input and `CellIndex 12`, and the master feeds it a `PatternSDFMap`
   `TextureObjectParameter` (per-instance swappable). See the row-12 notes in
   `Docs/SDF_PATTERN_PIPELINE.md` §3.
2. **Per-shot pattern scale/strength authoring** — the office set currently sets
   `PatternScale`/`PatternStrength` per instance; a shot-level override table (map+shot →
   params) so the DP can dial hatching per camera without touching instances.
3. **A true F1 Voronoi variant with distance output** — already satisfiable:
   the `Pattern` output of `CellIndex 8` IS the raw F1 distance (only `Mask`
   is thresholded). Add a dedicated output only when a real consumer appears.

## Lookdev fixtures (2026-10-03)

Three controlled fixture levels, each built by its own script and each with a
fixed camera + one deliberate light rig, so a review compares pixels rather
than impressions:

| Level | Script | Judges |
|---|---|---|
| `L_Gouache_Lookdev` | `Python/build_gouache_lookdev.py` | the gouache master (sphere/cube/cone + stock baseline + grey exposure ball) |
| `L_Foliage_Lookdev` | `Python/build_foliage_lookdev.py` | the foliage master (generated card meshes: quad/cross/fan, alpha cut by `T_SDF_Leaf`) |
| `L_Water_Lookdev` | `Python/build_water_lookdev.py` | the water master (canal/puddle/bank: ripple scale, flow, grazing edge ink) |

**ONE LEVEL LOAD PER PROCESS.** Loading a second level in the same headless
process fatals — `World Memory Leaks: 2 leaks objects and packages`
(`EditorServer.cpp:2544`) — and `collect_garbage()` does not clear it. The
fixtures therefore build through `Tools/build_lookdev_levels.py`, which spawns
one `UnrealEditor-Cmd` per level and gates each on **the .umap existing on
disk**, not on the exit code: a Python exception makes the editor exit 0
having built nothing, which happened twice before the gate was added.

Two more traps that cost runs, both now handled in `Python/lookdev_lib.py`:
`create_asset` does **not** put a level on disk (it makes an *untitled* world
current, and a following `load_level` then fatals on that world), so creation
goes `new_blank_map` → spawn → `save_map`; and a *phantom* registry entry
(package name known, no file) must be purged first or the create path is
skipped against a name the registry already claims.

Fixtures are rebuildable, not art: one driver run re-creates all three
deterministically. Their censuses are the evidence — gouache 13 actors / 10
static meshes, foliage 9 / 6, water 7 / 4, all forms present
(`Saved/Audit/{gouache,foliage,water}_lookdev_report.json`).

**None of this is a render.** `-NullRHI` means no pixels; the fixtures prove
the scenes are built and persisted correctly, and the frames still need the
desktop (or an NVIDIA driver past 582.28) to be judged.

## Per-shot pattern overrides (2026-10-03)

`Python/build_pattern_overrides.py` is the DP's table: instance → parameter
overrides (pattern index, SDF map, scale, density), applied *after*
`build_instances` so a spine rebuild cannot wipe it, every entry verified by
read-back. It is instance-level, not runtime — one look per instance per
build; true per-shot swaps are a level-composition concern.

First entries re-point three looks at the baked SDF maps where the map reads
better than the analytic pattern for the same mark: PowderCoat → `T_SDF_Cross`,
Carpet → `T_SDF_Dots`, Stone → `T_SDF_Cracks`. Everything else keeps its
analytic pattern on purpose — the library is a choice, not a migration.

## Verification (2026-10-03)

Two independent paths, deliberately:

* `build_spine.py` verifies what it builds, in-process (4/4 masters, 24/24
  instances, 22/22 profiles, 3/3 pattern overrides, 0 errors).
* `Python/verify_expansion.py` re-asserts the same facts from a **fresh
  process that built nothing**, reading only saved assets — master→profile
  bindings, instance→SDF-map assignments, the six maps' import settings
  (sRGB off, wrap, lossless, no mips, 256²), and the domain masters' function
  calls. Report: `Saved/Audit/expansion_verify_2026-10-03.json`.
  A value can read back correctly in the process that wrote it and still not
  be in the file; this repo has hit exactly that with the Toon Profile bind,
  so the second path is not ceremony.

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
