# Dana action-shot runbook — one real shot through the full chain

Purpose: produce **one accepted, grounded, UDS-lit Dana action shot** before any
further scope expansion. This is the critical path for the film. Nothing counts
as progress until this shot exists and passes the gate in §7.

## 0. Authority and inputs

- Root project: `G:\film-304-toon-spine\HumberToonShader.uproject` (root only; the nested copy is old).
- Validated candidate: `Saved\Audit\MayaDanaNative_20261016\ExportCandidate\Dana_CleanSkin_v08.fbx`
  - SHA-256: `bb995bafa312e2e351538db84e3ebdc002715179ad5ed848e7f63841b51c31f9`
- Expected mesh manifest: `Dana_CleanSkin_v08.expected_meshes.json` beside the FBX.
- Reports:
  - `Saved\Audit\MayaDanaNative_20261016\ExportCandidate\v08_report.json`
  - `Saved\Audit\MayaDanaNative_20261016\ExportCandidate\Dana_CleanSkin_v08.raw_weights.json`
  - `Saved\Audit\MayaDanaRoundtrip_20261016\Dana_CleanSkin_v08\verification.json`
- Shader parent: `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`
- Scene templates: `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Studio`, `L_Film_Office`, `L_Film_Arrival`
- Donor animation only: `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow`,
  `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Jog_Fwd` (2.133 s)

Rules carried forward (do not violate):

- Sparrow is an animation donor only. No Sparrow actor/character binding may remain in a film shot.
- Do not replace older Dana assets. Import into a new dated staging folder.
- Do not import materials/textures blindly; use explicit material slots.
- Do not generate a physics asset for every helper bone.
- Do not run `Python/light_and_animate_universal_film.py`; it is retired with a hard error.
- Do not run `build_spine.py` over the packaged Universal parent.
- Preserve the dirty Office map `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office` (do not Save All).

## 1. Pre-flight (no editor changes yet)

1. Confirm the candidate hash:
   `sha256sum Saved/Audit/MayaDanaNative_20261016/ExportCandidate/Dana_CleanSkin_v08.fbx`
   must equal `bb995bafa312e2e351538db84e3ebdc002715179ad5ed848e7f63841b51c31f9`.
2. Read all three reports above and note any non-zero error counts.
3. Confirm the editor lease/owner before touching anything:
   - Unreal PID and process owner
   - Monolith port (expected 9316 in last handoff)
   - dirty map state (must remain dirty, not saved)
4. Confirm the Universal parent exists at `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`
   and that `r.Substrate.ProjectGBufferFormat=0` is set.

Abort if any of these fail.

## 2. Import (single import, new folder)

Import v08 **once** into `/Game/Staging/DanaFilmRuntime_20261016`.

- Import as one skeletal character with morph targets.
- Do not replace older Dana assets.
- Do not import materials/textures blindly.
- Avoid generating a physics asset for every helper bone.

Read back and record:

- mesh count (expected 19 render meshes)
- skeleton/root hierarchy (expected roots include `Root_M`, `Spine1_M`, `Chest_M`,
  `Head_M`, `Shoulder_L/R`, `Elbow_L/R`, `Wrist_L/R`, `Hip_L/R`, `Knee_L/R`,
  `Ankle_L/R`)
- material slots
- bounds
- both morph channels (`Blink_L`, `Blink_R`)

Evidence file: `Saved/Audit/DanaFilmRuntime_import_20261016.json`

Abort if any render section is missing or morph channels are absent.

## 3. Unreal deformation checks (Maya/Houdini proof is not enough)

Verify in Unreal:

1. Head/lash following during head turn.
2. Blink using **both** eyelid bone motion **and** the matching body morph
   (toggling the body morph alone must not animate lashes).
3. Legs/hips and a body pose.
4. Source scale from bounds; establish floor contact from evaluated bounds rather
   than guessing a unit conversion.

Record pass/fail per check with screenshots or sequence captures.

Abort if lashes do not follow the head or blink does not use both channels.

## 4. Retarget one Sparrow clip

- Donor mesh: `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow`
- Donor clip: `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Jog_Fwd` (2.133 s)
- Target chains: `Root_M`, `Spine1_M`, `Chest_M`, `Head_M`, `Shoulder_L/R`,
  `Elbow_L/R`, `Wrist_L/R`, `Hip_L/R`, `Knee_L/R`, `Ankle_L/R`

Steps:

1. Inspect actual source/target reference poses; do not assume Paragon axes match.
2. Use a supported retarget route (the legacy `Orion_Proto_Retarget` Rig class does not load in UE 5.8).
3. Create one retargeted clip for Dana.
4. Play it back on the imported Dana skeleton and inspect for sliding, clipping,
   T-pose fallback, and body/lash loss.

Evidence file: `Saved/Audit/DanaFilmRuntime_retarget_20261016.json`

Abort if the clip shows T-pose fallback or body/lash loss.

## 5. Material assignment

- Use per-character instances of the working Universal shader/film variant.
- Override materials on the scene component using explicit slot names.
- Make a per-character child of the closest `MI_Film_*` instance for changes;
  do not change shared skin colors globally.
- Verify the UDIM sampling route; do not discard source diffuse detail.
- Check cornea, lashes, and proxy sections with the rig owner.
- Dana's `Hidden` mapping is specific to her existing reference import and must not
  be copied blindly to other rigs.

Evidence file: `Saved/Audit/DanaFilmRuntime_materials_20261016.json`

## 6. Compose one grounded action shot

- Duplicate `L_Film_Studio` (or Office/Arrival) for Dana.
- Replace the subject actor's mesh with the validated candidate.
- Preserve the source mesh asset and material slots.
- Set actor display height and floor contact from evaluated bounds (Dana stage
  normalizes to 170 cm for consistent camera testing; this is stage scale, not
  a rig-unit correction).
- Keep UDS daylight; composition, floor contact and exposure still require
  actual cast-frame review.
- Add the retargeted clip to a sequence and render a short take.

Inspect for:

- T-pose fallback
- body/lash loss
- sliding
- clipping
- darkness / exposure problems

## 7. Acceptance gate (all required)

A shot is accepted only when all are true:

1. Candidate hash matches v08.
2. All 19 render meshes present in Unreal import.
3. Both morph channels present and blink uses bone + morph.
4. Retargeted clip plays without T-pose fallback, body/lash loss, sliding, or clipping.
5. Grounded floor contact and reasonable exposure in the rendered frame.
6. No Sparrow actor or character binding remains in the shot.
7. Evidence files listed above exist and are readable.
8. Render is produced through an MRQ preset (see `Docs/MRQ_RENDER_GATE.md`).

If any item fails, the shot is not accepted and the failure must be recorded
before retrying. Do not mark the film task complete until this gate passes.
