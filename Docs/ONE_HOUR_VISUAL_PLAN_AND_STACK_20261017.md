# One-hour visual plan + professional PPV / film / camera stack — 2026-10-17

Companion to `RENDER_PLAN_COMPOSED_STYLIZED_20261017.md` (gates A–H, progress log there).
Everything below was checked against the live project today; items marked **UNVERIFIED** have not been seen in a screenshot.

## 0. What changed since the gate plan

| Item | Result | Evidence |
|---|---|---|
| **PPV outline fixed** | `PPV_StorybookOutline` was failing to compile: `M_PP_StorybookOutline_Render2026` has a `TextureObjectParameter VineBranchMask` with no default texture, so UE fell back to the default material and drew long streaks across the frame. Bound `/Engine/EngineResources/Black` on `MI_StorybookOutline_Render2026` and saved. | streaks: `Saved/Screenshots/fix2_medium.png`; off = clean: `ppv1_outline_off.png`; fixed: `ppv3_vinemask_bound.png`; violet dotted ink outline now visible in `variant_0_base.png` |
| Sam's hair "glow" | Was **lighting**, not material. My `TextureWeight` edit was reverted (back to 0.84). | `fix3_medium_after_revert.png` |
| Jev | Called `jev_rank` twice via the user's adapter (`~/.claude/mcp_servers/jev_mcp.py`): both returned "Jev returned no answer content" (free Nous model; the earlier evening review also timed out). **No Jev ranking exists.** The ranking in §1 is mine. | script output |

Dependency flag: the outline PPV and its blend function live in `/Game/Melodia/_PROJECT/…` and `/Game/ArtOfShader/…`. Those are not film-owned and will not pass the delivery allowlist. §4 plans the replacement.

## 1. Ranking of candidate improvements (mine, not Jev's)

Ranked by visible payoff per minute, with what each unblocks.

1. **Pose the cast** — unposed figures undermine every other look. Unblocks camera work.
2. **Dana skin** — near-black even with Sam's tiles bound, so her UV/tile sampling is wrong, not just dark albedo.
3. **Light rig for cast read** (key/fill/rim) — cheapest large gain; the Sam hair glow was lighting.
4. **Pick the look** (variants below) — team decision, zero cost to stage, high payoff.
5. **Film-owned PPV chain** (replaces Melodia/ArtOfShader outline).
6. **Camera stack** from the storyboard shots.
7. Trouser/shirt true colours + Sam shirt shell overlap.
8. Root-cause dark-albedo grey in v06 (do on a copy; large but not visible until 1–4 are done).
9. Missing props (mug, swatter, shoes).
10. Spider hero pass, MRQ proto presets.

## 2. The hour (60 min, one visible improvement per block, each ends in a viewed screenshot)

| Min | Block | Do | Pass = |
|---|---|---|---|
| 0–10 | **Pose** | David/Sam: author 3 expressive poses each as AnimSequences from their held-pose rigs (shoulder/hand/head offsets driven by Control Rig or bone transforms), assign as single-node pose. Dana: build IK Rig for `SK_Dana_Film304_v10e`, retarget `A_DanaFilm_Pose_IDLE_A` with the existing `IKRetargeter_SparrowToDana` pattern, assign. | All three visibly posed in `Film_Cam_OfficeMedium`, Dana no longer T-posed |
| 10–20 | **Dana skin** | Bind Sam's tiles to Dana as a diagnostic already done: still black ⇒ UV audit of v10e (Blender 4.3 or the NPR build; 4.5 crashed on the FBX). Check U range; if single 0–1, set `bFilmUseUDIM` false and bind tile 1001 alone. | Dana face/arms show brown skin |
| 20–30 | **Lights** | Three-point rig scoped to the cast (key warm 4800 K, cool fill, rim from the window side) added as actors with a `LightingChannel` for characters only so the set is untouched. Reduce hair blow-out. | Sam hair no longer white-clipped, faces readable |
| 30–40 | **Look choice** | Screenshot variants A–F (below) on all three at matched camera and lights, post as a contact sheet for the team. | Team can pick |
| 40–50 | **PPV variants** | Build the four volumes in §3 as disabled PPVs (one enabled at a time), capture each. | Four comparable frames |
| 50–60 | **Camera** | Apply the §5 lens/aperture table to `Film_Cam_OfficeMedium` and `Film_Cam_OfficeWide` (owner approval needed before touching scene cameras; else do it on duplicate cameras `…_Pro`). | Medium and wide frames with real DOF |

## 3. Staged variants for the team

### 3a. Material variants — **staged as saved assets**, previewed on Sam's skin

Folder `/Game/Materials/Instances/Film304/Variants/`. Each variant is a root `MI_Film304_Variant_<Name>` (parented to a Film304 look root, tuned) plus a `…_SamSkin` child with Sam's tiles. Retarget any cast part by re-parenting its instance to the variant root.

| Variant | Look | Key parameters | Screenshot | Verdict (honest) |
|---|---|---|---|---|
| A_WatercolourWash | Watercolour | wash 1.0, pooling 2.5, granulation 0.8, paper lift 0.25, paper scale now 500 | `variant_A_WatercolourWash.png` | **Coarse square mosaic** on the face at scale 110. Retuned to 500 but **UNVERIFIED** (the later captures were under changed camera/lighting). |
| B_GouacheImpasto | Gouache | impasto 0.8/0.5/0.7, height→normal 1.0, normal 1.4 | `variant_B_GouacheImpasto.png` | Same mosaic as A. |
| C_PaintedNormals | Smooth | impasto 0.5, normal 1.6, height→normal, detail 0.6 @ tiling 6 | `variant_C_PaintedNormals.png` | Same mosaic; the "painterly normals" read is not visible yet. |
| D_InkAndFlat | Toon | ramp 1.0, sharpness 6, contrast 1.5, rim 0.3 | `variant_D_InkAndFlat.png` | Strong ink-shadow look; too dark and plum on skin, promising for night/spider shots. |
| E_RisoHalftone | Halftone | halftone 0.8, freq 64, coverage 0.5 | `variant_E_RisoHalftone.png` | Same mosaic; dots not readable at this scale. |
| F_SoftPastel | Smooth | pastel 0.35, ramp 0.6, paper 0.1, gran 0.3 | `variant_F_SoftPastel.png` | **Clean and readable**: soft peach, the safest pick today. |

Finding: A, B, C and E share a pattern/noise layer that renders as hard-edged cells at face scale. That is a v06 print/paper-layer scale issue to fix before the team can fairly judge watercolour, gouache or halftone. Next action: raise pattern frequency (or make it screen/object-space) and re-shoot A/B/C/E under a fixed camera and the new lights.

### 3b. PPV variants (to stage as four volumes, all unbound, priority-ordered, one enabled)

Base: the now-working `MI_StorybookOutline_Render2026` (violet dotted ink outline, `OutlineColor (0.02,0.02,0.05)`, `EdgeStrength 0.92`, `OutlineWidth 1.5`, `MinWidthPx 1 / MaxWidthPx 2.5`).

| Variant | Intent | Settings |
|---|---|---|
| P1 Ink violet (current) | Spider-Verse-leaning dotted ink | as saved |
| P2 Watercolour paper | wash + paper edge, thin sepia line | `OutlineColor` sepia, `EdgeStrength 0.5`, `HalftoneAmount 0`, add paper overlay, bloom low |
| P3 Riso print | halftone shadows, offset colour | `HalftoneAmount 0.6`, line at 2 px, slight chroma offset |
| P4 Clean cinematic | outline only on characters (stencil), grade-led | `StencilCharacterWeight 1`, `StencilPropWeight 0.3`, `DistanceFadeStart 1500` |

### 3c. Indie/stylised research (what it suggests for us)

- Student and indie shorts typically test **post-process vs surface-material** toon early and keep exposed, artist-friendly parameters so other departments can tune (Abertay Summer Shorts toon-shader write-up, via [Inven/Neople search result set](https://www.invenglobal.com/articles/22927/natural-toon-shading-techniques-from-a-dungeon-fighter-technical-artist-at-neople)). Fits our look-root-per-style design.
- **Watercolour** is commonly a post wash plus paper overlay with adjustable edge/colour bleed ([Fab watercolour post-process listing](https://www.fab.com/listings/5d4abd66-f425-42ec-b21a-643e23001164?lang=de)): matches variant A + P2.
- **Painterly normals**: tools derive stylised normal detail from albedo or accept painted strokes ([ABN Painterly Normals / Substance stylisation, 80.lv](https://80.lv/articles/give-you-hand-painted-brush-strokes-real-depth-lighting-in-substance-3d-painter)); Arcane keeps a hand-painted feel via baked-in brush normals and 2D effects layered on top ([RedShark on Arcane](https://redsharknews.com/why-netflixs-arcane-looks-so-good-how-fortiche-ramped-up-the-animation-pipeline)). For us: author a brush-stroke normal/height tile and drive `HeightMap`/`DetailNormal` rather than relying on `bImpasto_Active` alone.
- **Hand-drawn ink lines that follow 3D** (Spider-Verse approach) are line-art tooling rather than a plain edge filter ([BlenderNation, Grease Pencil + Geometry Nodes](https://www.blendernation.com/2026/09/06/sticking-hand-drawn-ink-lines-to-3d-animation-with-blender-grease-pencil-and-geometry-nodes/)). Our dotted outline P1 is the realtime stand-in.
- Epic's own guidance: ACES filmic tone mapper with per-range grading, non-destructive; use the **CineCamera for DOF** rather than the volume ([Epic post-process docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-effects-in-unreal-engine), [filmic tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine)). Research found nothing authoritative on toon-outline best practice or on film grain settings, so those choices below are mine.

## 4. Professional stack (post / film / camera), from the repo's shots and boards

Source of truth: `OFFICE_SPIDER_SHOT_PLAN.md` §1 (global stack), `MRQ_PRESETS_BY_ACT.md` (SH010…SH690 presets), `SB_OfficeSpider_notes.md` + `SB_OfficeSpider_Page1–17.png` (73 shots), `SHOT_COMPOSITION_SCENERY_PLAN_20261017.md`, `MRQ_RENDER_GATE.md`.

**Conflict to resolve first.** The shot plan says the only grade is `MI_Toon_PostComposite` ("no second grade") and outlines are inverted-hull `MI_Outline_Thin/Heavy`. The live scene instead uses a Melodia screen-space outline PPV, and v06 also carries its own `FilmGrade*` / paper / print controls. That is three overlapping owners of grade, grain and line. Decision needed from the team (recommendation in bold):

| Layer | Owner | Recommendation |
|---|---|---|
| Line | inverted hull vs screen-space PPV | **Screen-space PPV, film-owned copy** (hull cannot do dotted/variable ink and costs geometry); keep hull only for the spider if its silhouette needs it |
| Grade | `PostComposite` vs v06 `FilmGrade*` | **`PostComposite` is the single grade** (shot plan rule). Leave v06 `FilmGrade*` at 0 on cast/props so two grades never stack |
| Paper/print | v06 per-material vs post | **Look variants do per-material paper/print; PPV does none** unless variant P2 is chosen |
| Tone map | engine | ACES filmic, fixed exposure per sequence (no auto exposure), set on one unbound PPV |
| DOF | volume vs camera | **CineCamera only** |

**Film-owned chain (build order):** (1) copy `M_PP_StorybookOutline_Render2026` and the one blend function into `/Game/Materials/PostProcess/Film304/`, give every texture parameter a valid default, (2) one unbound PPV `PPV_Film304_Master` (tone map, exposure, grain 0.08, vignette 0.35 per the shot plan), (3) one outline PPV `PPV_Film304_Ink` (priority above), (4) per-act bound PPVs only for mood (Act IV hot key, Act V sprinkler/fire). Remove `/Game/Melodia/_PROJECT/…` and `/Game/ArtOfShader/…` references and re-run the delivery closure.

## 5. Camera stack from the boards

Present: `Film_Cam_OfficeMedium`, `Film_Cam_OfficeWide`. Table is derived from the shot plan/storyboard; sensor, apertures and focus distances are proposals to confirm with the DP.

| Board shot type | Sequences | Lens | Aperture / focus | Move |
|---|---|---|---|---|
| Establish, exterior | SH010 | 24 mm | f/8, deep | slow push-in |
| Office wide / hallway | SH020, SH080, SH090 | 28–35 mm | f/5.6, focus on cast | static / track |
| OTS desk, typing | SH020, SH030 | 40–50 mm | f/2.8, focus laptop | static |
| Calendar / prop ECU | SH060 | 85 mm macro | f/2.0, thin | rack to note |
| Face reactions | SH060, 9, 15, 44, 55, 56 | 85 mm | f/1.8, eyes | push-in |
| Money shot, spider reveal | SH110 (12) | 35 mm | f/4, split focus worker L / spider R | pan right |
| Spider closeup | SH350 (38) | 100 mm macro | f/2.8 | grazing key |
| Handheld struggle | SH250, SH310 | 28 mm | f/4 | handheld shake |
| Chase top-down | SH320 | 24 mm | f/8 | top-down track |

Each camera also needs `aim_at`, verified `forward·aim ≥ 0.9` per the scenery plan, and a matching `CFG_OS_SH###_proto_v01` MRQ preset.

## 6. Open items needing a person

1. Real trouser colours for Sam and Dana (currently placeholder slate blue).
2. Choice of §4 line/grade ownership.
3. Whether I may add duplicate `…_Pro` cameras or edit the two scene cameras.
4. Which variant(s) the team wants rolled onto all cast parts.
5. Jev: adapter returns empty content; fix the model/endpoint or I continue without it.

## 7. Session event: editor closed by the user at ~21:16 (2026-10-17)

- Cause: the user closed it (confirmed). It had stopped responding to MCP calls just before; my `EditorAssetLibrary.delete_asset` on a half-created `AS_Dana_Pose_Relaxed` logged "ForceDeleteObject failed … package potentially corrupt" and the editor hung from then on, so the hang was likely mine; the close itself was deliberate. The first create failed on `set_frame_rate(24 fps)` ("not a multiple or factor of 30 fps"); only 30 fps (or no call) works for AnimSequences made by the factory.
- **On disk (saved):** `AS_David_Pose_Explain`, `AS_Sam_Pose_Shrug` (screenshot `Saved/Screenshots/pose1_medium.png` showed both posed); all Film304 instance fixes (skin lift, cloth colours, Variants A–F); the outline PPV fix (`MI_StorybookOutline_Render2026` VineBranchMask = Black). No Dana pose file exists.
- **Lost (in memory only):** assigning those two poses to the David/Sam actors in `L_Film_Office`.
- Pose-authoring recipe that worked (rig = AdvancedSkeleton names; component forward = +Y): duplicate the held-pose AnimSequence, `controller.open_bracket` → `set_bone_track_keys(bone, [t]*n, [q]*n, [s]*n)` → `close_bracket`; local delta = `q_old * Rotator(roll,pitch,yaw).quaternion()`. Shoulder Z− swings the arm forward, shoulder Y+ raises it outward, elbow Z− flexes the forearm forward/up, same sign on both sides.
- Requested next poses: David **seated in the chair**, Dana **leaning on the L desk**, Sam **standing, arms crossed (or any relaxed fold)**.
