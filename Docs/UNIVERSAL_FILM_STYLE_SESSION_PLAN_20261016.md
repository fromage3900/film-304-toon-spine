# Universal Film — bounded style-render session plan (2026-10-16, late PM)

Owner asks, in order:

1. *"make a full updated bounded plan and render session with various instance renders (eg toon vs
   realistic vs painterly, etc.) and prep other characters in the scene as well"* (~23:00)
2. *"Make sure to play with local lighting intensely and pose the meshes"* (~23:10)

This document bounds that session. It changes no rig, retarget or shader authority; the rig
authority remains `Docs/DEEPSEEK_4_1_EVENING_HANDOFF.md` steps 1–7 and the loose ends named
there stay open unless a phase below explicitly closes one.

**Material-authority update (2026-10-17):** the texture/normal and master-authority work now
lives in `Docs/MASTER_TRIM_CONVERGENCE_PLAN_20261017.md` — trim `M_Master_Toon_Universal` of
its Melodia surface, converge on a film-owned `M_Film_Toon_Master`, and bind Dana's real
textures (3-tile UDIM skin + shoes atlas). This session plan's §"no new masters" constraint is
superseded there by owner instruction.

## 0. Verified input state

| Fact | Evidence |
|---|---|
| Editor pid 11932, **single** listener on 9316 | `Get-Process` + `Get-NetTCPConnection` |
| **A second writer is active in that editor** and currently owns it: break-room staging saved, cast-rig imports in flight | §3 |
| Dana runtime mesh `/Game/Staging/DanaFilmRuntime_20261016/Dana_CleanSkin_v08`: 46,041 tris · 1,230 bones · 10 sections · **0 morphs** · height 76.905 uu · floor z −0.0193 | `Saved/Audit/DanaFilmRuntime_20261016/readback_20261016.json` + `animation.get_skeletal_mesh_info` |
| v08 slot names (10): `danaSkin_mat, danaHair_mat, danaEye_mat, danaCornea_mat, danaEyeInt_mat, danaPants_mat, danaShirt_mat, danaShoes_mat, danaGum_mat, danaTongue_mat` — **no iris slot**, no `danapantsbutton_mat` | `animation.get_skeletal_mesh_info` |
| The rig is an **Advanced-Skeleton-style Maya rig**: skinning follows clean deform bones (`Shoulder_R → Elbow_R → Wrist_R`, `Hip_R → Knee_R → Ankle_R`, `Spine1_M/Spine2_M/Chest_M`, `Neck_M/Head_M`), while `FK*`/`SDK1FK*`/`Twist*`/`MotionSystem` subtrees are control and twist helpers | live bone census, 1,230 names |
| Bind-space frame: **+Z up, nose = local +Y, right arm extends along −X** (so a T-pose reads as arms spanning ±X) | bind transforms via `get_bone_transform(..., RTS_COMPONENT)` |
| Every `MI_Film_*` is a child of `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` with 38 overrides | `material.get_instance_parameters` |
| The master exposes toon ramp, painterly (`bImpasto_Active`, `Impasto*`, `OilPaintMix`, `InkDensity`, `StrokePattern`…) and PBR/SSS knobs — 413 parameters | `material.get_material_parameters` |
| Cast availability: **Dana v08** (validated transport) · **David** `/Game/Meshes/Office/Props/C_DavidRenderTest_OSC` (reference-grade) · **Sam, Spider**: sources only | `Saved/Audit/OneDriveRigs_20261016/intake.json` |
| Default bind pose of v08 is a **T-pose** | front-view still (v02) — see §4 correction |
| Capture convention: `AutomationLibrary.take_high_res_screenshot` (latent, one per invocation, caller polls) | `Python/render_prototypes.py`, `render_headless_driver.py` |
| Machine is the **RTX 4070 SUPER workstation** — one 1280×720 still costs ~18–20 s end-to-end | session timings |

## 1. Definitions

- **Instance render** — one still of a film set where every cast material slot points at one *style
  set*. Styles are **children of the existing `MI_Film_*` shelf**; no new masters, no edits to
  `M_Master_Toon_Universal`, no edits to the older `/Game/Materials/Masters/M_Master_Toon_Universal`.
- **Style set** — `{Toon, Painterly, Realistic}` × per-part MIs under
  `/Game/Materials/Instances/UniversalFilm_20261016/Styles/<Style>/`.
  **Toon** = the shelf as-is (control; cannot drift). **Painterly** = impasto/oil/ink overrides.
  **Realistic** = ramp off + texture-driven PBR, including the VT/UDIM probe.
- **Pose** — a deliberate act authored as a real **AnimSequence** (`A_DanaFilmPose_*`) from bind
  data, played on the subject and **held** (`play_rate 0`), never a loop and never the bind pose.
  A still that shows the bind T-pose is a defect, not a deliverable.
- **Local light rig** — session-only `SESSION_LIGHT_<PRESET>_*` actors (spot/rect/point) placed
  around the subject from a preset table, refreshed as a unit. Never saved into a map.
- **Cast prep** — staging a character in a film set so it can be shot. It is *not* a rig validation
  and never substitutes for one.

## 2. Scope — phases, acceptance, stop conditions

### P1 — Cast Dana v08 (no level save)
Swap the mesh on the existing `Film_Subject_*` actor, normalize stage height to **170 cm** from
evaluated bounds, ground min-Z to the floor, assign the 10 slots from the style set, face the
active camera with `yaw_offset = −90` (nose is local +Y).
- Accept: v08 mesh + 10 non-empty slots; world height 170 ± 1 cm; floor contact |min Z| ≤ 0.5 cm.
- **Idempotence requirement:** normalization must survive re-casting. v02 proved the naive form
  fails — it re-derived scale from already-scaled bounds and collapsed the actor to 80.21 cm. The
  shipped form re-derives the factor from *measured world height* in a bounded loop, so re-running
  converges instead of halving.

### P2 — Style shelf
a. `MI_Film_Gum` / `MI_Film_Tongue` (v08-only slots the shelf lacked) — **done**.
b. Three style sets as children of shelf MIs, each saved and read back — **done** for Skin/Shoes/
   Hair/Shirt/Skirt/EyeWhite/EyeInterior (+Gum/Tongue).
c. **VT/UDIM probe** (closes or falsifies handoff line 85): Realistic `Skin` `Albedo` →
   `T_Dana_Skin_D_1001_20261016`, read the compile result back.
- Accept: every style MI saves, compiles, re-reads with exactly the intended overrides.

### P3 — Pose authoring (new; owner directive 2)
Author `IDLE_A` (contrapposto stand, arms out of T, head turned to camera) and `GESTURE_B` (raised
forearm gesture) as AnimSequences via `animation.build_sequence_from_poses`, from ref-pose math:

    L' = L · (C⁻¹ · W · C)      L = bind local rot, C = bind component rot, W = desired world rot

1. `poseframes` mode computes per-bone parent-relative transforms and writes **predicted limb
   axes** — the sign convention is verified as numbers *before* a render is spent.
2. The sequence is built by Monolith's native data controller (an asset, not a component hack).
3. `apply_pose` plays it and holds frame 0.
- Accept: sequence exists on the v08 skeleton; predicted axes match the intended direction
  (arms down ≈ −Z, elbows forward ≈ +Y); the played pose is visibly non-bind in the still.
- Stop: if a sign is wrong, flip it in the `POSES` table and re-derive — never hand-nudge a render.

### P4 — Local light rig (new; owner directive 2)
`lights` mode builds a preset rig of local lights around the subject (`studio`, `dusk`, `highkey`),
front referenced to the active camera. Authored set lighting (`Film_Key/Fill/Rim`, `UDS`) is left
untouched so the authored look stays reproducible.
- Accept: rig record written with per-light kind/intensity/units/colour/location; frames gain
  readable modelling (measured mean luma and contrast move in the intended direction).
- Stop: a frame that clips to white or stays near-black is a HOLD. The rig is refreshed as a unit,
  never appended to a stale rig.
- Note: "intensely" is delivered as *three moods on one subject*, not as brighter versions of the
  same idea — the comparison between moods is the deliverable.

### P5 — Style stills (Dana alone)
One 1280×720 still per style × preset from `Film_Cam_OfficeMedium`, caller polls, then **each PNG is
opened and looked at** (plus measured decode: luma, contrast, saturation, dark/bright fraction).
- Accept: exact 1280×720 IHDR, subject visible, grounded, lit, **posed** (not T-pose).
- Stop: black/near-black frame = HOLD (the 2026-10-08 failure class).

### P6 — Other characters
a. Stage **David** beside Dana, same height/grounding/material treatment, labelled reference-grade.
b. Two-character stills: 3 styles × `OfficeMedium` + `OfficeWide`.
c. **Sam / Spider**: this session records their contract requirement and cast-slot plan; unless the
   in-flight import (see §3) lands them as validated meshes, it does not fake them.
- Stop: if David's mesh misbehaves, David is removed and Dana-alone stills are re-fired rather than
  shipping a broken actor.

### P7 — Record
One JSON report `Saved/Audit/UniversalFilm_20261016/style_session.json`: per-still measured facts,
style override readbacks, pose predictions, light-rig records, VT verdict, and the explicit list of
what was **not** proven.

## 3. Editor ownership (binding for this session)

At 23:12–23:17 the editor was found under a **different writer's** control:

| Evidence | Timestamp |
|---|---|
| `Saved/Claireon/Results/...` tool results written | 23:14:12 |
| `Python/build_breakroom_scene.py` staged the break room; `L_Toon_Shot_BreakRoom.umap` **saved**; PIE worlds created/torn down repeatedly | 23:15–23:16:12 |
| `BREAKROOM_JSON {"result":"staged_and_verified","counts":{"spawned":16,"cameras":3}}` → `Saved/Audit/BreakRoom_20261016/breakroom_stage.json` | 23:16:12 |
| Maya exports for David/Sam (`Saved/Exports/CastRigExport/...`), FBX content probes, `Python/import_cast_rigs.py` | 23:14:22–23:17:16 |

Two consequences this session accepts as constraints:

1. **One editor, one mutating surface.** That writer uses *Claireon*; this session uses *Monolith*.
   Both operating at once is the forbidden pattern. So this session does **not** mutate the open
   level while that writer is mid-flight, and it does not switch levels out from under them.
2. **A level guard, not a convention.** `SESSION_*` actors are scaffolding; any other writer's save
   would bake them into an authored map. The script therefore **refuses** to run `lights`,
   `poseframes`, `posecheck` or `fire` unless the open level is in an explicit allowlist
   (default `["L_Film_Office"]`) and prints `STYLE_SESSION_REFUSED` otherwise.

Sequencing rule: this session takes the editor only in a quiet window, on an allowed level, and
releases it. If the other writer's lane owns the editor for the rest of the night, the session script
is the handoff artifact and runs unchanged when the window opens.

## 4. Correction to earlier evidence (recorded, not buried)

The v01 calibration still was read as "arms down". The v02 front view shows the arms **straight out
at shoulder height** — the v01 read was a misread of a foreshortened arm seen in profile at low
exposure. **The default bind pose is a T-pose**, which is exactly the frame class this project already
rejected. Hence P3 is not optional polish; it is the difference between a calibration frame and a
deliverable.

## 5. Non-goals (explicit)

- No retarget, no Sparrow clip, no Sparrow actor (donor data only). No re-enabling
  `light_and_animate_universal_film.py`.
- No morph/blink work (v08 has none; bone-vs-morph stays an owner decision).
- No Sam/Spider export or import by this session; no Dana contract run on another rig.
- No master-material edits, no new masters, no `build_spine.py`.
- **No level saves**, no commits, no pushes, no branch moves (repo keeps its dirty entries).
- **No mutation while another writer owns the editor.**
- No MRQ/video, no Showcase publication — lookdev evidence, not approved frames.
- No claim that any frame is deformation-validated.

## 6. Evidence level this session can reach

**Measured-and-looked-at stills + reflected asset readback** (instance overrides, slot assignments,
bounds, pose predictions, PNG pixels). It cannot reach "rig-validated action" and will not claim it.
A style still proves *how the look reads on this mesh in this light in this pose*, nothing about
skinning quality, and nothing about the other rigs.

## 7. Rollback / idempotence

Everything is scripted in `Python/universal_film_style_session_20261016.py` driven by
`Saved/Renders/universal_film_styles/_request.json`, in `render_prototypes.py` convention: re-running
a mode is a no-op or a redo; a finished still is never re-fired. Session light actors are destroyed
and rebuilt as a unit on each rig change. Persisted assets are only the new style MIs, the two base
MIs, and the authored pose sequences; deleting those paths returns the project to its current state.
No level package is written by this session.
