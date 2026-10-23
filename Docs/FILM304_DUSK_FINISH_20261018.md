# Film 304 — Dusk colour, texture and final render setup (2026-10-18)

Palette chosen by the owner: **A — Dusk Terracotta & Teal**.

This pass was executed against the live `L_Film_Office` and saved to new copies.
`L_Film_Office.umap` itself was **not** overwritten. The delivered level is:

```
/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06
```

## 1. Audit — before and after

| Metric | Before | After (v05 evidence / v06 final) |
|---|---:|---:|
| Actors | 220 | 211 |
| Unique material assets referenced | 86 | 73 |
| Legacy / non-film material paths | 20 | **3 accepted exceptions** |
| `WorldGridMaterial` slots | **8** | **0** |
| Instances with texture overrides | 14 (cast + WarmWall) | **23** |
| Instances with `TextureWeight > 0` | 11 | **20** |
| Enabled post-process volumes | 1 (Storybook outline) | 1 (same volume, re-graded) |
| Unbound PPVs at priority 100 | 5 | 5 (4 disabled by design) |

Remaining legacy exceptions, all deliberate:

1. `MID_UDS_K_0` on the Ultra Dynamic Sky sphere — third-party sky material.
2. `MI_Toon_Office_Troffer` on the six troffer **panels** — the emissive practical.
3. None else: the break-room vending machine (`VenndingMachine`, misspelled in the
   asset set) was remapped to `MI_Dusk_Plastic` in v06.

## 2. Colour — what changed

The previous scene used a single dark `BaseTint` with `PaletteRampMid/High` set to
the *same* value, so the colour ramp was collapsed. The Dusk pass uses a flat
tint plus the parent's proven toon value ramp, and carries the warm/cool split in
the **lights**:

| Surface | Instance | BaseTint (sRGB) |
|---|---|---|
| Walls | `MI_Dusk_Wall` | `#75604F` |
| Feature wall | `MI_Dusk_WarmWall` | `#8A5A48` |
| Floor | `MI_Dusk_Floor` | `#6A6258` |
| Desks | `MI_Dusk_Desk` | `#937450` |
| Ceiling | `MI_Dusk_Ceiling` | `#C4BCAA` |
| Glazing | `MI_Dusk_Glazing` | `#2E6F6B` |
| Metal | `MI_Dusk_Metal` | `#4C5157` |
| Plastic | `MI_Dusk_Plastic` | `#4C5157` |
| Ceramic | `MI_Dusk_Ceramic` | `#B4553C` |
| Paper | `MI_Dusk_Paper` | `#EDE6D6` |
| Lamp shade | `MI_Dusk_LampShade` | `#D9B27A` |
| Frame | `MI_Dusk_Frame` | `#4C5157` |
| Plant | `MI_Dusk_Plant` | `#4F6B4A` |
| Chair | `MI_Dusk_Chair` | `#34383D` |
| Break room | `MI_Dusk_Breakroom` | `#B08A5E` |
| Whiteboard | `MI_Dusk_Whiteboard` | `#E8E6E0` |
| Monitor | `MI_Dusk_Monitor` | `#22262B` |
| Blinds | `MI_Dusk_Blinds` | `#C9C4B8` |

Light rig at v05:

| Light | Intensity | Colour |
|---|---:|---|
| `Light_Cinematic_SunBeam` | 10 | `(255,225,195)` warm key |
| `EST_Fill_E1` | 1.2 | `(160,182,255)` cool fill |
| `SpotLight` | 30 | `(255,225,190)` warm key |
| `Cast_RimKicker_Light` | 8 | `(210,235,255)` cool rim |
| `Light_David_DeskLamp` | 20 | `(255,214,160)` practical |
| `Light_Workstation_Row_Troffer` | 20 | `(255,248,235)` |

The previous rig had **no warm key at all**: sun `(220,240,255)`, fill
`(150,175,255)`, and the desk lamp / spot / rim kicker at intensity 0.

## 3. Texture — what changed

PBR diffuse maps were imported from `Saved/PBR/` into
`/Game/Materials/Textures/Film304/PBRImport20261018/`:

`T_Film304_PBR_{concrete,terrazzo,steel,glazing}_D` (1024², sRGB, DXT).

They are bound to `Albedo` at `TextureWeight` 0.10–0.30 with `UVScale` 2–10.
Desks and the break room use the existing Paragon wood diffuse
`/Game/ParagonSparrow/.../T_Wood01_D`; this is a third-party reference and can be
swapped for a film-owned wood map before delivery.

The `T_SDF_*` office maps are **RG distance fields**, not colour. They are bound
only to `HeightMap` with `bUseHeightToNormal=True`
(`CarpetLoop`, `Woodgrain`, `Cracks`, `CeilingTile`, `WeaveFine`, `Brushed`,
`PaperGrain`, `FrostBands`, `Blinds`). Binding them to `Albedo` is what turned
the test floor pink — do not repeat it.

### The ramp trap (important)

The v06 master's inherited `RampLow/Mid/High` defaults are pink/magenta
(measured `[0.85,0.40,0.62]`, `[0.78,0.55,0.82]`, `[0.60,0.78,0.95]`). Any
instance that activates `RampStrength` without overriding those stops will go
pink. The Dusk instances therefore set `RampLow/Mid/High == BaseTint` and
`PaletteRampStrength = 0`; colour comes from `BaseTint` and the light rig.
`MI_DuskTest_*` / `MI_Dbg_*` are debug assets and must not be assigned.


## 4. VFX — what changed

| Item | Before | After |
|---|---|---|
| `VFX_DustMotes_WindowRays` | UDS Dust at full strength, rendering as dense **orange confetti** across the windows and set | Actor hidden in game and component visibility off in v05/v06 |
| `Film_David_SnorePuff_1…4` | `M_DavidSnorePuff_v01` | Left as-is (the cards are not mesh components; the v03 SoftFade upgrade needs a sprite/billboard pass) |
| Volumetric fog | `EST_Fog_E1` active | unchanged |
| PPV stack | Storybook outline enabled; P2/P3/P4/Ink disabled | same single enabled volume, re-graded |

The dust removal is the single largest visual VFX improvement in this pass: the
particles were covering the cast and blowing out the window bays. A subtle,
low-count replacement should be authored as a film-owned Niagara system (warm
motes, 0.02–0.05 opacity, camera-facing, no bloom) before the final shoot.

## 5. Final render setup

Created under `/Game/Sequences/Film304Dusk_20261018/` and
`/Game/MoviePipelines/Film304Dusk_20261018/`:

| Shot | Camera | Sequence |
|---|---|---|
| DUSK01_Medium | `Film_Cam_OfficeMedium` | `LS_DUSK01_Medium` |
| DUSK02_Window | `CineCam_Hero_WindowEstablishing` | `LS_DUSK02_Window` |
| DUSK03_DeskLineup | `CineCam_Hero_DeskLineup` | `LS_DUSK03_DeskLineup` |

Each sequence is 24 fps, frames 0–48, with a camera cut and the four cast idle
clips bound (`AS_{Sam,David,Dana,Spider}_OfficeIdle_48f_*`), so the render never
falls back to a rest pose.

Configs per shot:

| Variant | AA samples | Output | Use |
|---|---:|---|---|
| `..._proof_v01` | 2 × 8 = 16 | 1920×1080 PNG + EXR | look/dev, fast iteration |
| `..._final_v01` | 4 × 64 = **256** | 1920×1080 PNG + 16-bit EXR | gate-compliant final still |

Both variants: `FULLY_LOAD` streaming, cinematic quality, engine warmup
120/48, render warmup 32/16, custom range 18–19 (one still).

Exact commands (also in
`Saved/Audit/Film304_Finish_20261018/final_render_commands.json`):

```powershell
# DUSK01 proof
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "G:\film-304-toon-spine\HumberToonShader.uproject" `
  /Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06 `
  -game `
  -LevelSequence="/Game/Sequences/Film304Dusk_20261018/LS_DUSK01_Medium.LS_DUSK01_Medium" `
  -MoviePipelineConfig="/Game/MoviePipelines/Film304Dusk_20261018/CFG_FILM304_DUSK01_Medium_proof_v01.CFG_FILM304_DUSK01_Medium_proof_v01" `
  -windowed -log -unattended
```

Swap `_proof_v01` for `_final_v01` for the 256-sample pass. Output goes to
`Showcase/Film304_Dusk_20261018/`.

## 6. Verification

Read-only in-editor audit (`level_material_vfx_audit.json`):

- 211 actors, 192 material slots, 73 unique materials.
- `WORLDGRID=0`.
- `TEXTURED=23`, `TEXTURE_WEIGHT_NONZERO=20`.
- PPV: `PPV_StorybookOutline enabled=True`, bloom 0.30, vignette 0.28,
  grain 0.05, fringe 0.08, bias 1.0; P2/P3/P4/Ink disabled.
- MRQ read-back: final `spatial=4 temporal=64`, PNG=True, EXR=True,
  streaming=FULLY_LOAD, cinematic=True, sequence range 0–48, 5 bindings.

Viewport evidence: `Saved/Audit/Film304_Finish_20261018/dusk_v5_{medium,window,desks}.png`
(captured before the v06 save).

## 7. Known remaining issues

1. **Warm wall is still hot.** In the v5 medium frame the right wall averages
   `rgb(226,177,102)`. If the DP wants less orange, lower
   `MI_Dusk_WarmWall` `BaseTint` to `#6F4C3E` or drop `SpotLight` to 20.
2. **Cast highlights.** The face region still reaches 255 in places; a final
   stop of bias 0.8 or key 8 is the next calibration.
3. **HVAC grid.** Remapped to `MI_Dusk_Metal` in v05; the ceiling still reads
   warm because the troffer practicals are warm. Confirm in the proof render.
4. **CineCamera actor mesh** is visible in viewport screenshots (the large blue
   camera). It is an editor-only visualization and should not appear in MRQ;
   confirm in the proof frame.
5. **Snore puff soft-fade** (`M_DavidSnorePuff_v03_SoftFade`) is not applied;
   the cards are not `MeshComponent`s. Needs a sprite/decall pass.
6. **`_v02` map is empty (13 KB).** It was saved from a world that had already
   been switched by a concurrent editor session. Do not use it. `v06` is the
   valid final.
7. **Third-party dependencies:** Ultra Dynamic Sky (sky, fog, dust) and the
   Paragon wood diffuse. Both need an allowlist entry or a film-owned
   replacement before delivery closure.

## 8. Reproduce

```powershell
# 1. audit (read-only)
powershell -File Tools/mcp_exec.ps1 -Path Python/audit_film304_render_20261018.py

# 2. rebuild instances + repoint + save a new map
powershell -File Tools/mcp_exec.ps1 -Path Python/build_film304_dusk_pass_20261018.py

# 3. finish (ramp neutralisation, lighting, grade, evidence, map)
powershell -File Tools/mcp_exec.ps1 -Path Python/finish_film304_dusk_20261018.py

# 4. sequences + MRQ configs + commands
powershell -File Tools/mcp_exec.ps1 -Path Python/build_film304_final_mrq_20261018.py
```

The scripts refuse to run unless the live world is `L_Film_Office`, so a
concurrent level switch cannot silently overwrite a Dusk copy.

