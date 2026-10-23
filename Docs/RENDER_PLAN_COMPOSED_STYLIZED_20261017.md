# Composed + stylized render plan — 2026-10-17 (supersedes the "Remaining gates" list in SESSION_HANDOFF_20261017_CAST_WIRING.md)

Rule for every gate below: **a viewed screenshot is the evidence.** Compile receipts, readbacks and
"parameter bound" are not approval. Capture with `claireon.slate_screenshot(target="level_viewport")`
from `Film_Cam_OfficeMedium` / `Film_Cam_OfficeWide`; open the PNG and look at it.
(`capture_scene_preview` cannot judge toon materials — do not use it.)

## State at the start of this plan (verified today, not assumed)

| Item | State | Evidence |
|---|---|---|
| Film304 look roots (7) | Were parentless (66/69 instances on WorldGridMaterial). Re-parented to `M_UniversalToon_Film304_v06`, saved | readback: 58/69 → v06 |
| `M_Film304_CorneaClear` | Was missing from disk. Restored from `Film304_ToonShader_UE58_DRAFT_v02.zip`, 3 cornea instances re-parented, saved | readback |
| L_Film_Office art slots | 54/54 on Film304 instances, 0 on WorldGrid. **In memory only, map NOT saved** | readback |
| New scene instances | 10 under `/Game/Materials/Instances/Film304/Scene/`. Desk/Spider clones carry roughness only, no textures (source had none) | readback |
| Dana | Actor now on `SK_Dana_Film304_v10e`, 12 sections on Film304 instances, transform kept. **No animation**: v10e has no AnimSequence; held pose v07 is gated (`animation_curves: 0`) so it was NOT imported. She stands in rest/T-pose | v10e skeleton query; `Dana_HeldPose_v07_fresh_readback.json` |
| Dana v10e FBX | Blender 4.5 import crashed in my UV audit, so **Dana UVs are unmeasured** | audit run |

## What the UV audit found (David, Sam; Blender 4.5 read-only, `uv_audit.py`)

1. **Skin UVs are correct UDIM, not misaligned.** David body U 0.005–2.925 (5808/9224 faces outside 0–1 by design, tiles 1001–1003). David arms land on tile index 1 (1896 of ~3300 arm faces), matching the brown arm/hand art in `DavidSkin_Tile2.png`. The master's selector (`floor(U) > 0.5` → 1002, `> 1.5` → 1003, `frac(UV)` coords, VirtualColor samplers) is logically correct.
2. **Pants/trousers are the real defect, and it is a texture-assignment bug.** `MI_Film304_{David,Sam,Dana}_Cloth_Toon` bind `T_*_Shoes_D_20261016` (the **shoes** atlas). David pants, shirt and shoes UV sets each span the whole 0–1 square (pants U 0.013–0.987; shirt 0–1; shoes 0–1), so they cannot share one atlas. Result visible in the viewport: one leg black, one leg brown hex-leather, white hip patch. Fix is a per-part texture or a flat colour — see Gate B.
3. **Mirrored shoe UVs.** David `Shoe_Rt` 1004/1004 faces and Sam `Shoe_Rt` 2034/2034 faces have negative UV area (mirrored island). Normal for mirrored geometry, but it will flip any normal map's green channel on that shoe. Mark for the normal-map gate.
4. **Sam pants:** 2 zero-area UV faces (harmless, note only).
5. **Not a UV problem, still open:** in the first screenshot David (the dark-skinned figure, `y≈-10`) shows grey arms/neck while his face is brown, and Sam (pale, `y≈-69`) shows correct skin. David's tile 2 art is brown, so the grey is not the texture. Cause unknown. Do not claim it fixed until a screenshot shows it. Candidates in order: toon ramp/lighting washing out dark albedo, VT not resident at capture, a David-specific instance override.

## Maps: normal / AO / roughness (answer to "what about those")

- **Supplied by the artists: none.** Cast only has base-colour tiles and the clothing/shoe atlas.
- **Derived, labelled derived:** `Saved/OfflineIntake/20261017/task7_derived_maps/preview/` has AO, curvature and tangent normal for UDIM 1001/1002/1003 and the shoe atlas (2048²), plus `derived_head_preview_normal_applied_1024.png`. They are OpenGL-style (+Y) and need Flip Green on import.
- **v06 has the sockets** (`NormalMap`, `RoughnessMap`, `MetallicMap`, `DetailNormal`, `ORM`, no per-tile versions). It does **not** have per-tile `NormalTile100x` / `RoughnessTile100x` or AO; those exist only on the legacy `M_Master_Toon_Universal`. So a 3-tile normal on skin needs v06 extended first (Gate D).
- Nothing is wired yet. No roughness map exists even as derived; skin uses scalar Roughness 0.72.

## Gates (do in order; stop and screenshot at each)

**A. Skin reads correctly (baseline Toon look).** Screenshot David, Sam, Dana from OfflineMedium. Pass = skin tone continuous face→neck→arms→hands on all three, no grey patches. First chase David's grey arms (try Smooth look and a brighter fill; screenshot each). Dana's skin read near-black in today's capture, include her.

**B. Clothing.** Replace the shoes-atlas-on-pants binding: pants and shirt get flat colour (TextureWeight 0 + BaseTint) sampled from the known source colours, shoes keep the atlas. Pass = both legs the same colour, shoes show leather/sole detail, shirt has no body outline showing through (the pale shirt in the close-up shows the torso through it; check for z-fighting/shell overlap).

**C. Dana.** Import a held pose only after a re-export reads `animation_curves > 0` (v05/v06/v07 all failed that). Until then she stays in the reference pose. Re-run UV audit on v10e with a working importer (Blender 4.3 or the NPR build already installed). Pass = screenshot with eyes showing iris+sclera, mouth sections correct, not black.

**D. Maps (optional, quality).** Extend v06 with per-tile Normal/AO (copy the legacy `bFilmUseUDIM_Normal` branch), import derived maps with Flip Green and correct compression (normal = TC_Normalmap, AO = masks/linear, VT enabled), test on one head only, screenshot with/without. Mirrored shoe islands get checked here.

**E. Props/set.** Desk and Spider clones are untextured. Screenshot each; add albedo from `OneDriveRigs` sources if they look flat.

**F. Composed shots.** Brennan owns cameras, lights, saves and MRQ submission. Frame from authored cameras only. Per shot: screenshot at 100% screen percentage, full res, then submit through the MRQ presets in the runbook.

**G. Stylized passes.** One shot, seven looks, same camera: Toon, Smooth, Watercolour, Gouache, Halftone, OrderedDither, NoiseDither. Method: switch the look root (`MI_Film304_<Look>`) that the cast instances inherit from, not per-actor edits; screenshot each; check print stability across two adjacent frames (halftone/dither must not crawl). Pass = all seven readable, skin tones survive every look, no look turns the face black or white.

**H. Persist and deliver.** Only after A–G pass visually: save map (with Brennan), refresh `Film304_ToonShader_UE58_DRAFT_v03.zip` (v02 predates the morph/skeletal flag fix and the cornea master restore), re-run `film_delivery_closure`, reopen project, confirm 0 WorldGrid instances.

## Known risks

- **Everything in the level is unsaved.** An editor restart reverts David/Sam/Dana/props to the old `OneDriveRigs` overrides. Do not close the editor before Gate H or a map save.
- `git status` shows ~20 deleted `Content/Materials/Masters/DanaFilm/*` files and many modified `.uasset`s. Nothing was committed today. The DanaFilm masters are the original source of the cornea graph; the film copy now lives only in `M_Film304_CorneaClear` (and the draft zip).
- `MI_Film304_Brutalist{Concrete,Asphalt,Glazing}` still parent to `/Game/EnvSandbox/.../M_Master_Toon_Universal`. They work, but they are not on the canon master; other maps untouched.

## Progress log (loop)

### Gate A — skin — PARTIAL PASS (2026-10-17 ~20:57)
- Method: viewport screenshots along the `Film_Cam_OfficeMedium` line of sight (viewport camera only; no scene camera moved).
- Finding: grey/black skin on the **dark-skinned** casts (David, Dana) is a *shading* issue, not UVs or textures. Proof: binding Sam's tiles onto David's instance rendered orange correctly (`Saved/Screenshots/gateA7_david_with_sam_tiles.png`); `BaseTint`, `FilmGradeSaturation`, `Roughness`, `FilmPaperLift`, `RimIntensity` had no effect (`gateA3/A4/A6`); `TextureWeight=0` + tint rendered tan (`gateA5`); `FilmGradeShadowLift` is the lever (0.3 too strong/peach `gateA6_lift03`, 0.12 beige `gateA8_lift12`, **0.06 warm brown** `gateA8_lift06`).
- Applied + saved: `FilmGradeShadowLift = 0.06` on `MI_Film304_David_Skin_Toon` and `MI_Film304_Dana_Skin_Toon`. Sam unchanged (reads correctly).
- Result screenshot: `Saved/Screenshots/gateA9_dana_after.png` — David warm brown (slightly lighter than the deep-brown tile art), Dana dark brown with visible orange irises.
- Not done / still open: root cause inside v06 (why dark albedo falls to grey before the lift) was not located; the lift is a workaround. David skin on the real asset is slightly lighter than the source art. Sam's hair is blown out to pure white (Gate B/E candidate).
- Dana's remaining oddities seen: white/coral trousers (Gate B), T-pose (Gate C).

### Gate B — clothing — PARTIAL PASS (2026-10-17 ~21:05)
- Done + saved: `MI_Film304_{David,Sam,Dana}_Cloth_Toon` now `TextureWeight 0` + flat `BaseTint` (David (0.03,0.035,0.045); Sam/Dana (0.07,0.09,0.15) **placeholders, owner to confirm real trouser colours**). Shoes keep the atlas.
- Evidence: `Saved/Screenshots/gateB1_medium.png` — the black/brown-hex/white leg patchwork is gone on all three; each trouser is one even colour. Shirts unchanged (pink Sam, white David, turquoise Dana).
- NOT passed: David's trousers should be near-black but render light grey. Probes: tint 0 + Roughness 0.82 = black with white specular streaks (`gateB2`), tint 0.008 = light grey (`gateB3`), tint 0 + Roughness 1.0 = light grey (`gateB4`). So v06 gives a very different result for tiny albedo/roughness changes at the dark end.
- Correction to my Gate A note: I hypothesised rough-surface reflection haze caused the dark-skin grey. **Falsified** — David skin at Roughness 0.45 and 0.25 stayed grey (`gateB5_skin_r45/r25.png`). Real cause still unlocated; `FilmGradeShadowLift 0.06` remains the workaround.
- Not checked yet: whether Sam's shirt shows his torso through it (blotchy darker patches on the back in `gateA2_*`/`gateA3`), likely overlapping shirt+skin shells. Needs a mesh-side look.
- NEW TASK (v06 root cause): "dark albedo → grey/light" in `M_UniversalToon_Film304_v06`. Bisect by duplicating the master and removing branches (lighting/spec/ramp) while screenshotting a dark-skin head. Do on a copy, never on v06 directly.

### Loop tick 1 — Dana skin — PASS (2026-10-17 ~21:27)
- Reopen check after restart: map `L_Film_Office`, all cast slots on Film304 instances (Dana 12/12, David 11/11, Sam 12/12, Spider 3/3), outline PPV fix persisted (`VineBranchMask = Black`), held poses intact, no `Poses_Headless` assets yet. (Open map was briefly switched to `L_Toon_Office_ProceduralVariants` by the user; resolved.)
- Jev answered this time (`choice: Dana skin…`, confidence 0.88): the first successful Jev call of the day.
- Root cause (NOT a UV/tile fault, my earlier hypotheses were wrong): `MI_Film304_Dana_Skin_Toon` carried overrides copied from her old source instance: `PaletteRampStrength 1.931`, `PaletteRampDriver 2.0`, peach `PaletteRampLow/Mid/High`, `TextureWeight 0.908`, `Roughness 0.808`. The palette ramp replaced the tile colour (near-black before, pale peach after the restart). David/Sam carry none of these.
- Fix saved: `PaletteRampStrength 0`, `TextureWeight 1.0`, `Roughness 0.72` (kept `FilmGradeShadowLift 0.06`).
- Evidence: before `Saved/Screenshots/dana1_asset.png`, `dana2_tint_only.png`; after `dana3_palette_off.png` (brown skin, readable face; chair and L desk visible in frame). The `PaletteRamp*` colour overrides remain on the asset but are inert at strength 0.
- Note for the earlier "dark skin → grey" workaround: after the restart David reads rich brown; the `FilmGradeShadowLift 0.06` may now be partly unnecessary. Re-test with lift 0 under the new lights before keeping it.
- Next in order: cast light rig; then the pattern mosaic in variants A/B/C/E; Cline poses pending.

### Loop tick 2 — PPV variants staged — PARTIAL (2026-10-17 ~21:36)
- Jev (ok, 0.82): "stage four PPV variants as disabled volumes". Lights were skipped on purpose: the scene already has a key `SpotLight`, a cool `PointLight` fill and `Cast_RimKicker_Light`, and the handoff says the owner owns lights.
- Built (new assets): `/Game/Materials/PostProcess/Film304/Variants/MI_PP_Film304_{P2_WatercolourPaper,P3_RisoPrint,P4_CleanCinematic}`, children of `MI_StorybookOutline_Render2026` with `VineBranchMask = Black`. New volumes in `L_Film_Office` (UNSAVED level change): `PPV_P2_WatercolourPaper`, `PPV_P3_RisoPrint`, `PPV_P4_CleanCinematic` (unbound, priority 100, **disabled**). `PPV_StorybookOutline` (P1) left enabled.
- Screenshots (same camera): `ppvvar_P1_InkViolet.png`, `ppvvar_P2_WatercolourPaper.png`, `ppvvar_P3_RisoPrint.png`, `ppvvar_P4_CleanCinematic.png`.
- Verdict: P3 is the only clearly visible stylised outline; P1 faint at distance (distance fade 3000–4000); **P2 does not read as watercolour** (this PP material has no paper/wash layer, only ink/halftone); P4 is the clean baseline. To make P2 real, add a paper-grain overlay + colour-bleed to a film-owned copy of the PP material (plan §4), not parameters alone.
- Observed in frame: a white office chair beside the right desk (selected in the editor) and the L-shaped desk on the left — the targets for David's seat and Dana's lean.

### Loop tick 3 — office lighting — PASS (2026-10-17 ~21:45), user-requested
- User asked for "proper office lights" and lighting variation (Houdini Engine is installed; not needed for this step).
- Staged in `L_Film_Office` (UNSAVED level change, all tagged `OfficeLights`): six troffer fixtures `Film_Troffer_1..6` at z=300 over the cast (x∈{-170,-45,80}, y∈{-120,0}), each = emissive panel (`MI_Toon_Office_Troffer`, 120×60) + dark housing + `RectLight` (120×60, Movable, no shadows, radius 650).
- Tuning: first pass at 14 cd flooded the set, blew the desks to white and greyed David (`light2_troffers.png`). 3.5 cd keeps contrast (`light3_troffers_3p5.png`); 1.5 cd is also fine.
- Variants: `Python/apply_office_lighting_variant.py` — `apply("FluorescentDay" | "WarmAfternoon" | "NightOffice" | "SpiderDread")`; touches only the troffer lights, `SpotLight` (key), `PointLight` (fill) and `Cast_RimKicker_Light`; spawns/saves nothing. Screenshots: `lightvar_FluorescentDay.png`, `lightvar_WarmAfternoon.png` (warm gold wall wash, long shadows — strongest mood), `lightvar_NightOffice.png` (dim, cool), `lightvar_SpiderDread.png` (two fixtures, hard figure shadows on the wall).
- Limits: the Ultra Dynamic Sky behind the set is unchanged between variants, so "Night" does not darken the outside; varying UDS time-of-day is a follow-up. The editor was left on FluorescentDay.
- Still open: cast unposed (Cline), P2 paper layer, variants A/B/C/E mosaic, cameras, props, Houdini lookdev.

### Loop tick 4 — sky time-of-day per lighting variant — PASS (2026-10-17 ~21:55)
- Jev (ok, 0.88): "vary Ultra Dynamic Sky time-of-day per lighting variant". Cline: no `Poses_Headless` assets yet (it is running probes in `Saved/ClinePosing/`).
- `Film_UDS_Daylight` exposes `Time of Day` (authored value **652.8**, i.e. just after dawn). Setting it with `setattr` is not enough; setting through `claireon.uobject_set_property(object_path, property_path="Time of Day", value=...)` updates the sky live.
- `Python/apply_office_lighting_variant.py` now also sets it: FluorescentDay 1200, WarmAfternoon 1730, NightOffice 2300, SpiderDread 2130.
- Screenshots: `skytod_NightOffice.png` (black sky, city skyline silhouette, readable cast), `skytod_WarmAfternoon.png` (golden hour, shafts through the angled glass facade, long warm shadows — best mood), `skytod_script_FluorescentDay.png` (noon, blue sky, skyline, glass facade).
- Newly visible set pieces: a city skyline silhouette mesh and a tilted glass facade, previously hidden by the dusk sky. The user has the skyline selected in the editor.
- Caution carried to the master-shader task: at noon David's dark skin reads grey again even with `FilmGradeShadowLift 0.06`; the "dark albedo goes grey" behaviour is lighting-dependent (worst under bright flat light), not just a lift problem.
- Editor left on FluorescentDay at noon (sky TOD 1200; authored 652.8 — restore via `uobject_set_property` if wanted). All of tick 2–4's level changes (3 PPVs, 6 troffers, sky TOD) are UNSAVED.

### Loop tick 5 — material variants re-test / mosaic — PASS with caveats (2026-10-17 ~21:55)
- Jev (ok, 0.82): re-test the coarse mosaic. Cline: still no `Poses_Headless` assets (it is authoring: `Saved/ClinePosing/author_poses.py`, `pose_lib.py`, chair measurement files).
- Camera for these shots: from the head bone along the medium-camera line (`mos2_*` onward). Earlier close-ups (`mos0/mos1`) were mis-framed through the glass facade and are unusable.
- Mosaic status after the restart + paper scale 500: **gone** on A, B, E.
- Verdicts on Sam's skin (FluorescentDay, noon sky):
  - **E Riso halftone** (`mos2_E_RisoHalftone.png`): clean coherent halftone dots on face and arm; reads as a printed comic panel. Strongest.
  - **B Gouache impasto** (`mos3_B_GouacheImpasto.png`): fine cross-hatch grain over warm skin; reads painterly. Good.
  - **A Watercolour wash** (`mos3_A_WatercolourWash.png`): smooth and soft but pale/washed (skin tone drains). Tuned `FilmPaperLift 0.08`, `PastelLift 0.05`; still pale. Acceptable as a "wash" look; would need `BaseTint` saturation or a stronger tile contribution for real skin tone.
  - **C Painted normals**: was grey and faceted (`mos1/mos3/mos4/mos5/mos7/mos8`). Root cause found by diffing against the stock `MI_Film304_Sam_Skin_Smooth`: on the **Smooth** look, `bUseHeightToNormal` must be **ON** and `bImpasto_Active` **OFF**; either deviation turns skin into grey facets (`bImpasto_Active=True` on Smooth is broken; on Gouache it works). Fixed C = Smooth + `bUseHeightToNormal` True + `HeightMap = T_SDF_PaperGrain`, `HeightToNormalStrength 1.2`, `NormalStrength 1.3`, impasto off (`mos9_C_brushgrain.png`: clean warm skin, subtle painterly shading). Painterly-normal effect is still subtle; a real brush height/normal tile (see research) would sell it.
  - D Ink & flat, F Soft pastel: not re-shot this tick.
- All six variant skin children now carry `BaseTint = white` (they had inherited the master's mid-grey default); no visible effect on A, but matches the stock instances.
- Open: A needs more skin colour; C needs a real brush texture; D and F re-shoot; P2 paper layer; scene dressing / Houdini lookdev; cameras; props; Cline poses.

### Loop tick 6 — Cline's poses assigned and placed — PARTIAL PASS (2026-10-17 ~22:05)
- Cline delivered (no errors, no pre-existing assets touched, no actor moved, no map saved, no git): `Poses_Headless/AS_David_Seated`, `AS_Dana_LeanDesk`, `AS_Sam_ArmsCrossed`; report `Saved/ClinePosing/report.json`. Numeric checks: feet within 0.6 cm of the floor; David pelvis 6 cm above the 44.2 cm seat; Dana right wrist 1.2 cm from the desk top; Sam wrists 5 cm beyond the opposite elbows. Cline's own limits: hip flex for David only 53° (a 90° sit would lift the feet ~18 cm with this seat height and leg length), no self-intersection test, Dana's arm needs a visual check.
- Done by me (UNSAVED level changes): assigned all three as single-node poses; rotated David −70.6° so his feet point along the chair's local +Y (toward the desk) and moved him so his pelvis sits over `P_Chair_KS` (actor now at (−142.4, −36.9)); moved Dana 13 cm toward the L desk `SM_P_OfficeDesk_AC_FilmStage_20261016` (now at (11.3, 28.9)).
- Evidence: `Saved/Screenshots/pose2_all_medium.png`.
- Read of the screenshot: **David** reads seated in the chair, facing the desk (legs hidden by the right-hand desk, so lower body not yet verified). **Dana** is no longer in a T-pose; she stands beside the L desk with a hand on its edge, but it reads as *standing at* the desk, not leaning (weak). **Sam** stands with forearms held out in front of him — reads as a gesture/fold, not clearly crossed (acceptable per "or his arms whatever"). Minor: a patch glitch on Sam's right sleeve/shoulder (skin showing through the shirt).
- Next: Dana's lean needs more (tilt her toward the desk / hip against the edge, move 10 cm closer); verify David's legs from another angle; Sam sleeve overlap.

### Loop tick 7 — David's seat verified — PASS (2026-10-17 ~22:08)
- Jev (ok, but low confidence 0.62): verify David from a second angle. Done with viewport-only cameras: `seat_side.png`, `seat_high34.png`.
- Result: David is genuinely seated on `P_Chair_KS`: pelvis on the cushion, thighs on the seat, shins vertical, sneakers on the floor, torso upright, hands on thighs, facing the desk. Reads as a slightly perched sit (53° hip flex, as Cline warned) — natural, no floating, no chair clipping visible from these angles.
- New defect now clearly visible (`seat_high34.png`, right edge): **Sam's right sleeve/shoulder has orange skin blotches showing through the pink shirt** (shirt and skin shells overlap/z-fight on the arm). This is the next fix.
- Still open: Dana's lean (stands at the desk), Sam sleeve overlap, paper PP layer for P2, A skin colour, C brush texture, D/F re-shoot, v06 dark-albedo root cause (on a copy), scene dressing / Houdini, camera stack, props.

### Loop tick 8 — Sam's sleeve skin-through — NOT FIXED by material; handed to Cline (2026-10-17 ~22:14)
- Close-up `sleeve1_before.png`: skin blotches on Sam's right shoulder, upper arm and cuff poke through the pink sleeve (separate shells, too close).
- Tried: `bClothWind_Active` + `ClothDisplacementScale 1.0` on `MI_Film304_Sam_Shirt_Toon` (the master's world-position-offset path). Result `sleeve2_disp1.png`: **whole shirt turned grey and faceted**, skin patches unchanged. Reverted at once (`sleeve3_reverted.png`: pink again). Nothing was saved; the instance now carries three scalar overrides equal to the master defaults (`ClothDisplacementScale 1.0`, `Cloth_WindStrength 0`, `Cloth_FoldingAmount 0`), inert.
- Finding (v06, second case): enabling static-switch permutations **`bClothWind_Active`** (and, on the Smooth look, **`bImpasto_Active`**) makes the albedo path collapse to grey faceted shading. Add to the master root-cause list next to "dark albedo goes grey".
- Next step: `Docs/CLINE_SAM_SLEEVE_FIX_PROMPT_20261017.md` (new mesh `SK_Sam_Film304_v02`, offset shirt shell 0.3–0.5 cm on arms/shoulders, same skeleton so poses still play). I will assign and screenshot when it exists.

### Loop tick 9 — scene dressing: David's workstation — PASS (2026-10-17 ~22:20)
- Jev (ok, 0.82): "dress the set". No `SK_Sam_Film304_v02` from Cline yet (sleeve fix still pending the user pasting `Docs/CLINE_SAM_SLEEVE_FIX_PROMPT_20261017.md`).
- Placed on `Film_ExistingOfficeDesk` (top z 53.8, in front of David's chair), all tagged `SetDress`, auto-scaled by mesh bounds to real-world sizes (UNSAVED level change): monitor (`P_ComputerMonitor_AC`, 52 cm), keyboard (`P_Keyboard_KS`, 44 cm), mouse, desk lamp (`P_Lamp_EF`, scaled to ~0.68 of the first pass so it is not oversized), coffee mug, phone, and a paper sheet (`paper_sheet`; it stands on edge and is invisible; needs a rotation, low value).
- Finding: the `/Game/Meshes/Office/Props/*` meshes arrive on `WorldGridMaterial` (grey checker in every shot) because their materials are missing; the `OneDriveRigs` env props (`SM_P_*_FilmStage`) already have instances. Fixed with six new film prop instances (new, saved): `/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_{Plastic,Screen,Paper,Ceramic,Metal,LampShade}` (children of `MI_Film304_Toon`, `TextureWeight 0` + `BaseTint`). Assigned Plastic to monitor/keyboard/mouse/phone, LampShade to the lamp, Ceramic to the mug, Paper to the sheet.
- Evidence: before materials `dress1_workstation.png` (checker props, oversized lamp), after `dress2_materials.png`, `dress3_lamp_fixed.png` (clean workstation).
- Not dressed yet: the L desk `SM_P_OfficeDesk_AC_FilmStage_20261016/17` (occupancy of the L unknown), walls (whiteboard, clock, frames, shelves), floor (plant, bins, filing cabinets, bookshelf), the break-room kit. Candidates exist under `/Game/Staging/OneDriveRigs_20261016/Environment/` (`SM_P_Whiteboard_SG`, `SM_P_Clock_AC`, `SM_S_Plant_PMB`, `SM_P_FilingCabinets_SG`, `SM_P_Bookshelf_PMB`, `SM_P_Bin0*_SY`, `SM_P_PictureFrame_AC`, `SM_P_Calendar_SG`).
