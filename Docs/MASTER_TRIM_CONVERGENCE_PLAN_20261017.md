# Master trim + convergence plan — 2026-10-17

**Owner directive (2026-10-17):** trim `M_Master_Toon_Universal` of its Melodia functions and
converge with the film masters. This supersedes the earlier lane constraint
"no shader rebuild, no new masters" — the owner explicitly authorised authoring a film-owned
master. It does **not** authorise touching any Melodia/BS_GodFile asset.

**Companion docs:** `Docs/UNIVERSAL_FILM_STYLE_SESSION_PLAN_20261016.md` (render session of record),
`Docs/WORK_ORDER_OFFLINE_DCC_20261017.md` (offline Maya/Houdini prompts).

---

## 0. Why (measured, 2026-10-17)

| | `M_Master_Toon_Universal` (EnvSandbox) | `M_OneDriveRigs_FilmToon_UDIM_20261016` (film) |
|---|---|---|
| Expressions | **1,303** | **16** |
| Scalar params | 292 | 2 |
| Vector params | 66 | 1 |
| Texture params | 33 | 3 |
| Static switches | 33 | 0 |
| Samplers | 17 | 5 |
| Pixel shader instructions | **1,341** | **456** |
| Shading model | MSM_DefaultLit (classic) | MSM_DefaultLit + Substrate toon BSDF |

Census of the film lane's 19 `MI_Film_*` instances (2026-10-17, `material_query
get_instance_parameters`): **zero** overrides touch any Melodia feature. Every instance is
`tint + toon ramp + roughness`, and **every instance has an empty texture-override list** —
the master's own `TextureWeight` default is `0`, so no instance renders a texture at all.
That is the visible defect behind "material instances not properly set up with her textures".

**Phase 0 census complete** (`Saved/Audit/MasterConvergence_20261017/census_v01.json`):
all **62** instances parent the EnvSandbox master; only **51 of ~424 parameters** are ever
overridden by anything; only **2 of 62 instances bind any texture at all** —
`MI_Film_Skin_Realistic → Albedo = T_Dana_Skin_D_1001_20261016` and
`MI_Film_Shoes_Realistic → Albedo = T_Dana_Shoes_D_20261016`. So the Realistic style is
partially textured and Toon/Painterly are flat — and the skin bind is **tile 1001 only**,
which is the head tile. 44 of 62 instances override Melodia parameters purely to set them to
zero (`TemporalStrength`, `BoilIntensity`, `SmearStrength`, `SparkleIntensity`, `Iridescence`,
`Cloth_WindStrength`, `Grazing_Rim_Boost`, `DreamIntensity`, `NikkiHeroGradeStrength`,
`bClothWind_Active`, `bLayerB/C_Active`…): the lane pays 44 override slots per instance just
to switch the Melodia surface off. That is the trim's justification in one line.

Also measured: **no normal maps exist anywhere in the source intake** (18 image files total
across Dana/David/Sam — 12 `*_Diffuse` PNGs + 6 FAQ JPGs). "Her normal maps" cannot be bound
because they were never authored. See §6.

## 1. Goal

One film-owned toon master that:

1. reproduces the look the film lane already tuned (toon ramp, palette, rim, sheen);
2. supports **real textures** — including Dana's **3-tile UDIM skin** — with the texture path
   *on* by default rather than off;
3. carries none of the Melodia gameplay/creature surface;
4. compiles cheap enough to run a film render farm on.

## 2. KEEP list (film needs these)

**Textures:** `Albedo`, `NormalMap`, `ORM`, `HeightMap`, `RoughnessMap`, `MetallicMap`,
`OpacityMap`, `EmissiveMap`, `FaceSDF_Texture`,
**+ new** `BaseColorTile1001/1002/1003` (the proven 3-tile If-chain from the intake master).

**Switches:** `bUDIM_Albedo` (new, default off), `bUseHeightToNormal`, `bUseOpacityMap`,
`bUseEmissiveMap`, `bToonRampEnabled`, `bToonRampActive`, `bFaceSDF_UV1`.

**Scalars:** `TextureWeight`, `UVScale`, `UVRotation`, `UVOffsetU/V`, `NormalStrength`,
`NormalPower`, `HeightToNormalStrength`, `Roughness(+Scale/Bias)`, `Metallic(+Scale/Bias)`,
`PaletteRampStrength`, `RampStrength`, `RampSharpness`, `RampPosMid`, `RampContrast`,
`ToonRampStrength`, `RimPower/Intensity/Width/Bias/Clamp`, `SheenPower/Width/Bias`,
`FabricSheen`, `EmissiveMapIntensity`, `EmissiveMapUVScale`, `ImpastoStrength/Height/Coverage/
Roughness`, `OilPaintMix`, `InkDensity`, `StrokeMask`, `DreamRimPower/Cycles/Strength`,
`ShadowDreamStrength`, `ShadowSoftness`.

**Vectors:** `BaseTint`, `PaletteRampLow/Mid/High`, `RampLow/Mid/High`, `RimColor`,
`SheenTint`, `EmissiveMapTint`, `ShadowDreamTint`, `DreamRimColor`, `SkinSSS_Color`, `InkColor`.

*Phase 0 census is the final arbiter — anything in this list that no instance overrides and no
style needs gets dropped too.*

## 3. DROP list (Melodia-only, zero film references)

- **Anime crossover:** all `Madoka*`, all `Itto*`, `WitchBarrierWallpaperScale`
- **Celestial/constellation:** `Constellation*`, `Celestial*`, `bCelestial_Active`,
  `bCelestialUsesDreamPalette`
- **Fairy:** `FairyDust*`, `FairyGlyphMask`, `FairyMotifStyle`, `FairyHighlightThreshold`,
  `bFairyDust_Active`
- **Sparkle/glow:** `Sparkle*`, `GlowIntensity`, `InnerGlow*`, `BloomBoost`, `StarMap`,
  `SparkleMask`, `bSparkleAdvanced`
- **Chladni / MeshBlend:** `ChladniMask`, `ChladniColor`, `bMeshBlendActivator_Active`
- **Weather/elemental/time:** `Wetness*`, `SnowDust*`, `SnowUpBias`, `Moss*`, `Element*`,
  `TimeOfDay*`, `bWeather_Active`, `bElemental_Active`, `UseUDSTimeOfDay`
- **Gemstone/gilding:** `Gemstone*`, `IOR`, `Dispersion`, `GoldTint`, `GoldEmissive`,
  `GildingStrength`, `GoldRoughness`, `bGemstone_Active*`
- **SDF contact / distance:** `DFContact*`, `SDF_Seam*`, `ContactRim*`, `DitherDissolve*`,
  `DistanceFade*`, `AtmosphericFadeColor`, `LOD_Distance_Bounds`, `bDFContactBlend_Active`
- **Motif/transform:** `MagicalTransform`, `Motif*`, `TransformGlow`, `WipeSoftness`
- **Procedural ambience:** `Sigil*`, `Dawn*`, `Mist*`, `Glint*`, `DreamFlow*`, `DreamPulse*`,
  `DreamBloom*`, `DreamComposition`, `DreamThreshold`
- **Legacy stacks:** `Stack2_*`, `Stack3_*`, `bStackLayer2_Active_LEGACY`, `bStackLayer3_Active`
- **Layer B/C** (film uses Layer A only): `LayerB_*`, `LayerC_*`, `bLayerB_Active`,
  `bLayerC_Active`, all `LayerC*` scalars
- **Triplanar:** `Triplanar*`, `bTriplanar_Active`
- **Cloth wind / aniso:** `Cloth_Wind*`, `bClothWind_Active`, `FabricType`, `FabricAnisoLevel`,
  `FabricWeave*`, `bSheenUsesNormal`, `ToonAnisotropy`
- **Melodia systems:** `AutoBlendID`, `StaticAutoBlendID`, `NikkiHeroGradeStrength`, `bNikkiHero`,
  `Iridescence*`, `Grazing_Rim_*`, `MacroVariation*`, `Detail*`, `NoiseScale`, `TemporalStrength`,
  `BoilIntensity`, `SmearStrength`, `WindSpeed`, `Parallax*`

## 4. Phases

### Phase 0 — census (read-only, no risk)
1. `export_material_graph` on `M_Master_Toon_Universal` →
   `Saved/Audit/MasterConvergence_20261017/universal_graph.json`.
2. `get_instance_parameters` on **all 62** instances (19 film + 9 DanaProfessor + 34 styles)
   → `instance_overrides.json`; produce the final KEEP/DROP table with a
   "referenced by N instances" column per parameter.
3. Census which of the 62 are actually referenced by `L_Film_Office` and the WarmCourtyard
   level — unreferenced instances do not constrain the trim.
4. `get_compilation_stats` baseline (1,341 PS instructions / 17 samplers) for the §5 gate.

### Phase 1 — author `M_Film_Toon_Master` — **COMPLETE 2026-10-17**
- Path: `/Game/Materials/Masters/Film/M_Film_Toon_Master`.
- **Built by duplicating the proven 16-expression film UDIM master and extending it**, not by
  trimming Universal — trimming 1,303 expressions would have been slow and lossy, and the film
  master already carries the UDIM method Universal lacks.
- Result: **23 expressions, 30 connections, 0 build errors, compiled, saved.
  321 pixel instructions, 3 samplers, 10 parameters** — versus Universal's 1,303 / 1,341 / 17 / 424.
- Parameters: `TextureWeight` **1.0** (textures ON by default — the opposite of the EnvSandbox
  master, whose `0.0` default is why no film instance ever rendered a texture), `NormalStrength`
  1.0, `Metallic` 0.0, `Roughness` 0.72, `Specular` 0.18, `BaseTint` white, and four texture
  slots: `BaseColorTile1001/1002/1003` (Dana's UDIM set) + `NormalMap` (neutral).
- **UDIM chain retained** per owner decision 2026-10-17: `frac(UV)` sample coords, `floor(u)`
  tile select, nested `If` (1001 below 0.5, else 1002/1003).
- **Toon ramp discovery:** the ramp is not in-graph — it is a **ToonProfile asset**
  (`TP_DanaFilm_Clean`) on the `SubstrateToonBSDF`. Palette ramping is authored in that asset,
  so no palette graph belongs in the master.
- **Normal path:** bound to `T_Neutral_Normal` at `NormalStrength` 1.0 — a coherent, visually
  silent path, so a real map is only ever a re-bind.
- Evidence: `Saved/Audit/MasterConvergence_20261017/phase1_master_built.json`.
- Build-tool gotcha recorded for the next agent: `build_material_graph` renames node IDs on
  every call — resolve nodes by `ParameterName`/class *within* a single build, never hard-code
  IDs across builds.

### Phase 2 — reparent + rebind — **PARTIAL 2026-10-17**
1. ~~Record every instance's current parent~~ rollback path unchanged: one
   `set_instance_parent` call back to the EnvSandbox master.
2. **19 base `MI_Film_*` instances reparented and saved** (kept 5 params each, lost the
   Melodia surface). **The 34 style children and 9 WarmCourtyard instances deliberately stay**
   on Universal pending Phase 3 — the painterly set (`Impasto*`, `OilPaintMix`, `InkDensity`,
   `StrokeMask`) has no equivalent on the new master yet, so moving them now would collapse
   Painterly/Realistic into Toon.
3. **Textures bound:** `MI_Film_Skin` → UDIM tiles via the master defaults at `TextureWeight`
   1.0; `MI_Film_Shoes` → `Albedo = T_Dana_Shoes_D_20261016` with `bUDIM_Albedo = false`;
   everything else stays `TextureWeight 0` (flat tint), which is correct because no textures
   exist for those slots.
4. **Phase 1b added mid-flight:** a `bUDIM_Albedo` `StaticSwitchParameter` (default true) and a
   single-tile `Albedo` slot, because the UDIM-only albedo path would have forced every
   non-UDIM material through the 3-tile lookup. Master is now 28 expressions / 38 connections /
   321 px instructions / 3 samplers.

**Two defects caught by re-reading instead of trusting the tool's OK:**
- The first reparent pass **did not persist** — the instances were left unsaved and the master
  rebuild caused the editor to reload them from disk, silently reverting every parent. Fixed by
  saving each instance immediately after its reparent.
- 11 instances carried **`NormalStrength = 0`** from the old flat-toon setup. With a normal now
  actually wired into the BSDF, a zero-strength normal normalizes a zero vector and can shade
  as a degenerate/black normal. Cleared so they inherit the master's 1.0.

**Known debt (documented, not silent):** each reparented instance still carries ~33 orphan
overrides for params the new master does not have — compiler-ignored dead data, no visual
effect, but they will confuse any future override census.

### Phase 3 — A/B visual proof
Same actor, same `IDLE_A` pose, same camera, same lights, one variable:
- Row A: `MI_Film_*` on `M_Master_Toon_Universal` (current).
- Row B: same instance paths on `M_Film_Toon_Master`.
- Shots: Toon medium, Painterly medium, Realistic medium, **head close-up** (the face is the
  acceptance surface), plus a shoes/legwear crop.
- **Known unknown to settle first:** `MI_Film_Skin_Realistic` already binds tile 1001 (the head
  tile) alone. Render it before anything else — if the body shows the face texture smeared
  across it, the mesh UVs span [0,3] and single-tile skin binds are wrong; if it reads clean,
  the UVs sit in [0,1] and the UDIM machinery may be unnecessary for this mesh. This one render
  decides the whole skin strategy.
- Numeric diff per pair (mean/p50 luma, saturation, clip %) + **human view of every PNG**.
- **Accept:** face reads with skin texture and no tile seams; shoes/legwear read as authored;
  toon ramp visually equivalent or better; no over-exposure regression vs the calibrated stop.

### Phase 4 — retire the reference (after acceptance)
1. Assert **zero** `MI_Film_*` instances parent `M_Master_Toon_Universal`
   (`list_material_instances` on the EnvSandbox master → count 0 from this lane).
2. **Do not delete or edit the EnvSandbox master.** It is Melodia's asset and stays untouched
   on disk; this lane simply stops referencing it.
3. Write `Saved/Audit/MasterConvergence_20261017/summary.json` with before/after stats,
   reparent map, texture bindings, and the A/B render paths.

### Phase 5 — offline DCC handoff
Normal maps and facial morphs do not exist in-engine and cannot be authored in UE — that work
goes to the offline lane (`WORK_ORDER_OFFLINE_DCC_20261017.md`, TASK 1 and new TASK 7).

## 5. Rollback

Every reparent is reversible by one `set_instance_parent` call back to
`/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` using `reparent_before.json`.
No instance is ever deleted. The EnvSandbox master is never modified, so the old path stays
valid indefinitely.

## 6. Normal maps — the honest statement

The source rigs ship **diffuse-only**. Measured across the whole intake:
`Sam_Diffuse.1001–1003`, `Sam_Shoes_Diffuse`, `Dana_Diffuse.1001–1003`, `DanaShoes_Texture`,
`David_Diffuse.1001–1003`, `DavidShoes_Texture` — plus 6 FAQ JPGs. **No `_N`, `_Normal`,
`_NRM`, bump, roughness, AO or height map exists** for any of the three rigs, and the rig
author's own `TextureSetup.jpg` shows a Maya blinn with a **color input only** (Bump Mapping
0.800 is an unconnected default).

So the correct deliverable is: bind every texture that exists, leave the normal path coherent
and idle on a neutral map, and — if surface detail is wanted — get it from the offline lane
(TASK 7: Houdini bakes AO/curvature from the 46k-tri mesh and derives a tangent-space normal,
clearly labelled *derived*, not author-supplied).
