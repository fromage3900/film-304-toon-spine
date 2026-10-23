# Session Handoff: Film 304 Cast & Material Finish
**Author:** Antigravity (Pair Programming Agent)  
**Target Agent:** Claude Sonnet  
**Date:** 2026-10-17  
**Context:** Unreal Engine 5.8-CL-55116800 | Project: `HumberToonShader.uproject` (`G:\film-304-toon-spine`)  
**Active Level:** `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.umap`  

---

## 1. Executive Summary & Lane Boundaries

This handoff transfers ownership of the **Unreal Engine Film Lane (Cast Lineup & Material Finalization)** to Sonnet while Antigravity focuses on the **Houdini / Houdini Engine procedural Brutalist architectural framing pipeline**.

### ⚠️ Critical Operational Guardrails:
1. **Active Map Authority:** Work is strictly scoped to `L_Film_Office`. **Do NOT touch or modify `L_Toon_Shot_Hallway`** (owned by composition). Never switch maps blindly or issue blanket "Save All" commands.
2. **Creative Ownership:** Brennan owns composition, cameras, lighting rigs, level saves, and final Movie Render Queue (MRQ) submissions. You are acting as Technical Director / TD for material wiring and cast staging integrity.
3. **Repository State:** Branch is `feature/render-harness-20261008`. Do **NOT** run `git reset --hard`, `git clean`, `git stash`, or blanket Git commits. All WIP is preserved.

---

## 2. Canon Master Shader Status

* **Canon Asset:** `/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06`
* **Complexity & Expressions:** 675 expressions.
* **Compiled Styles (7 Looks):**
  1. `Toon` (736 instructions, 13 samplers)
  2. `Smooth` (751 instructions, Substrate smooth branch)
  3. `Watercolour` (841 instructions)
  4. `Gouache`
  5. `Halftone` (UV-anchored filtered dot coverage)
  6. `OrderedDither`
  7. `NoiseDither`
* **Dependency Closure:** 22/22 allowlisted packages in `Saved/Audit/EveningExecution_20261017/film_delivery_closure.json`. 0 private/Melodia dependencies remain. `NormalAdjust` collapsed from 10 duplicate subgraphs to 1 single 29-expression node.
* **Morph & Skeletal Target Fix (Completed):** Both `M_UniversalToon_Film304_v06` and cornea masters previously had `used_with_morph_targets = False`. This was corrected to `True` and recompiled alongside `used_with_skeletal_mesh = True`. Source builder scripts now preserve these flags.
* **Handoff Archive Draft:** `Film304_ToonShader_UE58_DRAFT_v02.zip` (SHA256: `a9e7492fe0154a0ccaa28c3d4b2fa7e334999b26968552c10e7ee23e9bcb06c2`).

---

## 3. Cast Material Wiring & Mesh Staging Status

### 3.1. David & Sam (Updated on Stage)
* **Mesh Assets:**
  * David: `/Game/Staging/Film304Repaired_20261017/David/SK_David_Film304_v01` (11 sections, 2 blink morphs, 150 bones).
  * Sam: `/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01` (12 sections, 2 blink morphs, 221 bones).
* **Held Animations:** Applied via `AS_David_HeldPose_v02` and `AS_Sam_HeldPose_v02`.
* **Transforms in `L_Film_Office`:**
  * Rotations corrected (pitch/roll zeroed, yaw preserved at 180°).
  * Scale normalized to 170cm reference (`scale = 2.20995`).
  * Floor-snapped: bounds bottom at `Z = 0.0`.
  * Receipt: `Saved/Audit/EveningExecution_20261017/office_cast_final_david_sam.json`.

### 3.2. Active Diagnostic — Skin VT Sampling (Immediate Priority)
* **The Background:** Historical imports bundled each character's 3 UDIM tiles into single 6144×2048 strips. These were replaced by true 2048² sRGB DXT1 virtual texture tiles (`BaseColorTile1001/1002/1003`) under `/Game/Materials/Textures/OneDriveRigs_20261016/`.
* **The Symptom:** Brennan reported *"Clothing works, skin does not"* after the initial David/Sam application.
* **Current Diagnostic State in `L_Film_Office`:**
  * **David component slot 0** is temporarily overridden with `MI_OneDriveRigs_David_Skin_20261016` (old reference).
  * **Sam** remains on the film canon baseline: `MI_Film304_Sam_Skin_Toon` (`M_UniversalToon_Film304_v06`).
* **Sonnet's Action Item:**
  1. Have Brennan inspect the A/B viewport/render between David and Sam.
  2. If the `used_with_morph_targets` recompile resolved the issue on Sam: clear the slot 0 override on David's actor component so both use the film canon `MI_Film304_{David,Sam}_Skin_Toon`.
  3. If skin still fails to sample visually, check `Virtual Texture Streaming` pool / streaming settings in project settings, or inspect UV channel mappings in the viewport buffer visualization.

### 3.3. Dana (Awaiting Held Pose & Staging Swap)
* **Approved Staging Candidate:** `/Game/Staging/Film304Repaired_20261017/Dana/SK_Dana_Film304_v10e`.
  * Restores 12 sections (adds `danairis_mat` and `danateeth_mat`, fixing the blank sclera/missing iris issue).
  * All 8 morph targets preserved; eye follow parented to `Head_M`.
* **Held Pose State:** Maya offline intake authored candidate `Dana_HeldPose_v07_24fps.fbx` (`Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/`).
* **Sonnet's Action Item:**
  1. Once v07 readback passes independent Houdini/Maya verification, import `AS_Dana_HeldPose_v07` into `/Game/Staging/Film304Repaired_20261017/Dana/Poses/`.
  2. Swap `Film_Cast_Dana` actor in `L_Film_Office` to `SK_Dana_Film304_v10e` and assign the held pose.
  3. Ensure Dana's 12 material slots inherit the baseline family via `Python/bind_film304_baseline_cast.py`.

### 3.4. Spider
* Staged meshes: `/Game/Staging/CastRigs_20261016/Spider/Spider_Deform_v2`.
* 3 film-owned baseline instances: `MI_Film304_Spider_Body`, `MI_Film304_Spider_Eye`, `MI_Film304_Spider_Fang`.
* Comic chitin ramp and rim highlight properties mapped.

---

## 4. Environment & Brutalist Materials Status

* Generated via `Python/setup_canon_master_and_building_materials.py` and saved to `Saved/Audit/canon_master_and_building_materials_report.json`.
* **15 Brutalist Static Meshes Bound:**
  * Concrete facade slots $\rightarrow$ `MI_Film304_BrutalistConcrete` (warm-grey, `Roughness: 0.75`, `RampStrength: 1.0`).
  * Asphalt / ground slots $\rightarrow$ `MI_Film304_BrutalistAsphalt` (dark road, `Roughness: 0.90`, `RampStrength: 0.8`).
  * Glazing / window slots $\rightarrow$ `MI_Film304_BrutalistGlazing` (`M_Master_Toon_Glass`, `Roughness: 0.08`, `Metallic: 0.2`).

---

## 5. Diagnostic Cleanup Notice
* 161 test packages (old probe levels, lash diagnostics, scratch materials) were cleanly archived into `Saved/Recovery/Film304_Diagnostics_20261017.zip` and pruned from `/Game/` with zero broken referencers.

---

## 6. Key Script & Tool Directory

| Script / Tool | Purpose |
|---|---|
| `Python/apply_office_repaired_cast.py` | Applies mesh, scale (170cm), held pose, and zeroed pitch/roll to named actors in `L_Film_Office`. |
| `Python/bind_film304_baseline_cast.py` | Binds all 35 cast sections to film-owned `MI_Film304_*` baseline instances. |
| `Python/repair_film_office_stage.py` | Stage repair script: sets lighting (PointLight 12,000 lm, SpotLight 28,000 lm, rim kicker). |
| `Python/setup_canon_master_and_building_materials.py` | Establishes Brutalist architectural material instances and assigns them to static mesh slots. |
| `Python/inspect_v06_wiring.py` | Graph expressions and null-texture audit for `M_UniversalToon_Film304_v06`. |
| `Python/check_param_wiring.py` | AST checker asserting that all declared parameters in builder scripts are consumed. |

---

## 7. Definition of Done for Sonnet
1. **Skin Texture Verification:** David and Sam render with intended skin tone in `L_Film_Office` under daylight and studio lights without seams or blank fallbacks.
2. **Dana Staging:** `Film_Cast_Dana` upgraded to `v10e` with 12 sections (eyes and teeth distinct) and grounded held pose.
3. **Lineup Review:** All four cast members (Dana, David, Sam, Spider) grounded at `Z = 0.0`, facing camera, in held poses with active toon ramp banding (`RampStrength = 0.85–0.90`).
4. **Visual Evidence:** Final lookdev PNG recorded in `Saved/Renders/universal_film_styles/` and reviewed with Brennan.
