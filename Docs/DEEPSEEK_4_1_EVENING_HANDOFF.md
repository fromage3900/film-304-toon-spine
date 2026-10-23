# Humber / DeepSeek 4.1 continuation handoff

## Current checkpoint — supersedes the earlier failed v01 handoff

The resumed session reached the user's cutoff again: **95% used / 5% remaining in both the five-hour and weekly windows**. New technical work stopped. Refresh live usage before resuming; a five-hour reset does not replenish the weekly allowance.

**Dana's clothed export now passes native-vs-reimport Maya deformation checks and independent Houdini geometry/weight checks. It has NOT been imported into Unreal, retargeted, or rendered in an accepted action shot.** The existing Universal Toon shader package is ready. Do not mark the film task complete until cast action and UDS lighting are visually proven.

The user wants Melodia's existing working Universal Toon shader reused, UDS daylight, and the film cast in action. **Sparrow supplies animation only. Never put Sparrow's character into the film scenes or present T poses as finished renders.** Five additional rigs remain after the first validated pipeline.

## Authority and ownership

- Root project: `G:\film-304-toon-spine\HumberToonShader.uproject`. The nested duplicate project is old.
- Repo was already heavily modified on `feature/render-harness-20261008`. Preserve all WIP; no reset, clean, stash, branch switch, blanket staging, commits or pushes.
- Existing owner chat: **Update Toon Spine material masters**, ID `01a11492-9838-7451-8d4e-02fb1a450dc6`. The human authorized tandem coordination. Luna owns the Unreal editor/material lane; this chat owned isolated Maya/Houdini export work. Both were told to stop new work at cutoff.
- Last owner readback: Unreal PID 12172, Monolith port 9316, one dirty map: `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office`. Do not Save All or overwrite that map. Verify the current owner and process before any editor changes.
- Jev was actually consulted through TypeSafe SDK. Decision: `HOUDINI_BOUNDED_EXPORT_FIRST`; receipt `JEV_UPDATED_GOAL.json`. No score/reason was returned. The unrelated local Nous adapter was not labeled TypeSafe.

## Validated local Dana candidate

File: `G:\film-304-toon-spine\Saved\Audit\MayaDanaNative_20261016\ExportCandidate\Dana_CleanSkin_v08.fbx`

SHA-256: `bb995bafa312e2e351538db84e3ebdc002715179ad5ed848e7f63841b51c31f9`.

Contains **19 render meshes and two FBX Shape morph targets**: weighted full body; native L/R lashes; eyes, corneas and interiors; jeans, shirt and shoes; the native visible long-hair bang/main pair; teeth, tongue and eyebrows. Expected counts: `Dana_ClothedFilm_v08.expected_meshes.json` beside the FBX. The unweighted Base, duplicate facial intermediates and controller curve meshes are excluded. The small follicle-driven `PantsButton_GEO` accessory is explicitly not included; finish its attachment after the core action gate. The visible partial body is replaced by the actual weighted full body.

Native source: `G:\Film304_AssetIntake_20261016_Source\3rd Year Film\Rigs\Temp\Dana_Rig_v1.5\Dana_Rig_v1.5.mb`.

Source SHA-256 is unchanged: `007ca95e5baf844b41855a51c74249feace98ed1460c7e066fd967ce7d9bfc6e`. No source scene was saved. Maya 2027 standalone works. The source loads with existing missing Redshift/UI-node and deprecated-node warnings; do not save over it to remove those warnings.

### What was actually proven

- Maya reopened v08. Its raw FBX object inventory is exactly **19 Mesh + 2 Shape** objects. Maya reconstructs `Blink_L` / `Blink_R` helper meshes from those Shape targets; these are morph data, not extra character render meshes.
- Five post-FBX pose comparisons against the native rig passed on all 19 meshes: head turn 15 degrees; left shoulder bend 25 degrees; left blink; right blink; left blink combined with head turn. Blink tests use native slider value 10.
- Worst native-to-FBX position error: **0.001874344 cm / 0.018744 mm**, on the shirt during shoulder bend. Body-only worst error is about 0.000879 cm. Acceptance tolerance was 0.01 cm, and the tests recorded actual nonzero native motion.
- Independent Houdini import: **all 19 topology/weight checks pass**, all required vertices weighted and normalized, no unexpected render/packed/controller meshes, no import errors/warnings. Capture output has 179 points; animated hierarchy has 1,250 points. These are Houdini hierarchy counts, not an asserted Unreal bone count.
- The original source and the checked candidate hashes were unchanged by inspection.

Reports:

- `Saved/Audit/MayaDanaNative_20261016/ExportCandidate/v08_report.json`
- `Saved/Audit/MayaDanaNative_20261016/ExportCandidate/Dana_CleanSkin_v08.raw_weights.json`
- `Saved/Audit/MayaDanaRoundtrip_20261016/Dana_CleanSkin_v08/verification.json`

### Export adaptations and limits

Direct native FBX exports v01/v02 dropped the final body/lashes and/or exported facial intermediate shapes. They are superseded and rejected. The successful path copies evaluated render geometry into an isolated export stage, copies native skin weights, and uses the original native hierarchy.

The exporter drops tiny native weights. Exact native weight copying was checked first (zero delta), then a documented derived-copy cleanup removed weights below 0.00101 and normalized survivors before transport. For the body, 68 vertices changed, maximum individual weight delta about 0.001008. The posed comparisons above measure the resulting error; no verifier tolerance was relaxed to hide missing body skinning.

The native lid joints live under a face root that stays stationary during head turns; the final source lashes receive additional head deformation elsewhere. The export creates **26 lid influence copies under `Head_M`**, driven from native local face matrices. This fixes head following while preserving tested blink motion. Native body eyelid closure is sampled into `Blink_L` / `Blink_R` morphs. Eyebrows have no source skin cluster, so their isolated copy uses an explicit rigid `Head_M` attachment that passed the same posed comparisons. Do not claim eyebrow weights were copied from a nonexistent skin cluster.

This proves the five tested poses and transport, not every facial expression, jaw animation, hip/leg motion, cloth collision, or Unreal skinning behavior. A runtime blink needs **both eyelid bone motion and the matching body morph**; toggling the body morph alone does not animate lashes. Bake a short combined eyelid-bone/body-morph blink take from this export setup if needed.

## Next actions, in order

1. Refresh quota and coordinate the editor lease with Luna. Verify v08 hash and read the final reports. Preserve the dirty Office map.
2. Import **v08 once** into a new dated staging folder, e.g. `/Game/Staging/DanaFilmRuntime_20261016`. Import as one skeletal character with morph targets; do not replace older Dana assets or import materials/textures blindly. Avoid generating a physics asset for every helper bone. Read back actual mesh, skeleton/root hierarchy, material slots, bounds and both morph channels. Confirm all 19 render sections survive. No bare/core-only candidate belongs in film shots.
3. Verify head/lash following, blink bone+morph behavior, legs/hips and a body pose in Unreal. Maya/Houdini proof does not certify Unreal deformation. Check source scale from bounds and establish floor contact rather than guessing a unit conversion.
4. Retarget ONE Sparrow clip onto Dana. Existing donor mesh: `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow`; clip: `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Jog_Fwd` (2.133 seconds). Donor assets are data only. Native Dana body chains use `Root_M`, `Spine1_M`, `Chest_M`, `Head_M`, `Shoulder_L/R`, `Elbow_L/R`, `Wrist_L/R`, `Hip_L/R`, `Knee_L/R`, `Ankle_L/R`. Inspect actual source/target reference poses and map them; do not assume Paragon axes match. The old `Orion_Proto_Retarget` was omitted because its legacy `Rig` class does not load in UE5.8. Use a supported retarget route.
5. Apply per-character instances of the working Universal shader/film variant using explicit material slots and diffuse maps. Verify the UDIM sampling route; do not throw away source diffuse detail or substitute the simple intake preview parents as the delivered Universal shader.
6. Compose one grounded, UDS-lit Dana action shot and inspect a short sequence for T-pose fallback, body/lash loss, sliding, clipping and darkness. Only then expand the other two scenes and five remaining rigs. Native four-key Dana/David clips are export tests, not action.
7. Finish the button accessory and other visible polish against the actual motion. Each remaining rig needs its own verified mesh, skin, visibility and face-control contract; do not run Dana's hard-coded contract on another rig.

## Reproduction tools

Installed Maya: `C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe`. Houdini Indie: `C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe`.

Tested final exporter copy: `G:\film-304-toon-spine\Tools\export_dana_clean_skin_v08.py`. Raw FBX inspector: `Tools/check_fbx_raw_weights.py`. Independent verifier: `Tools/verify_dana_native_export_houdini.py` with FBX path and optional expected-mesh JSON as arguments.

The tested exporter retains local source/output paths and depends on the existing contract helper at `Saved/Audit/MayaDanaNative_20261016/ExportCandidate/export_dana_native_candidate.py`; a copy is included in `continuation_scripts/`. It refuses to overwrite an existing candidate. To make another version, copy the tested script and change its output/report version together; preserve v08 and the source. Do not rerun the rejected old helper as a candidate builder. `check_fbx_raw_weights.py` must sit beside the final exporter for its independent FBX inspection.

PowerShell launches stalled intermittently on this machine. The observed working runner is a `.cmd` file that sets `MAYA_LOCATION=C:\Program Files\Autodesk\Maya2027` and launches the full quoted executable/script paths. Do not restart a job on a mere observation timeout: inspect its process/session and output state first. One attempted rerun correctly refused to overwrite v03, but clobbered that old diagnostic report; final v08 proof is separate and intact.

## Shader and scene state

Shader-only archive `UniversalToonShader_UE58_20261016.zip`: 38 packages, 1,870,709 bytes, verified CRC and asset hashes. SHA-256 `6b94783b27a336e66febbaa1760848aae5cff6d825d1bb5d6a012322003541b6`. No rigs/gameplay are included. Verified engine build: `5.8.0-55116800+++UE5+Release-5.8`; same-machine reopening was checked, another workstation remains separate proof. Preserve license requirements for included third-party dependencies.

Approved original parent: `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`, 1,303 expressions / 16 function calls. Older `/Game/Materials/Masters/M_Master_Toon_Universal` is different and preserved. Humber renderer key `r.Substrate.ProjectGBufferFormat=0` matches Melodia. Do not replace the entire configuration or run `build_spine.py` over this parent.

Luna's isolated profile-only variant: `/Game/Materials/Masters/OneDriveRigs_20261016/M_Master_UniversalToon_DanaFilmClean_20261016`. Owner reported compilation, expression/function parity, and identical 1,512 edges / 4 outputs; root profile changes to `TP_DanaFilm_Clean`. Source/variant inherited 165 validator records still need severity classification and a visual check. Mixed unused branches alone are not a reason to rebuild a shader the user expressly chose to reuse. Original Universal remains unchanged. See `Saved/Audit/OneDriveRigs_20261016/universal_profile_variant.json` and the owner chat for latest material updates.

The five simpler OneDriveRigs parents remain **intake previews**, not the delivered Universal shader. Owner readback reported 32 valid MIs / 12 texture overrides, 86/86 static assignments, and zero validation issues for those preview graphs. Their UDIM selector is 16 expressions after orphan UV cleanup. Cornea preview is translucent, two-sided, skeletal-enabled. These do not prove final scene appearance.

Latest owner material correction: all nine Dana/David/Sam skin tile assets use virtual texture streaming. The preview UDIM parent's three Color samplers were changed to `SAMPLERTYPE_VirtualColor`, with matching Dana tile defaults, then explicitly saved. Owner reported compilation, 16 expressions, 3 pixel samples / 6 samplers, 313 VS / 456 PS instructions and zero validation issues. All three character skin instances override their three tiles. Evidence: `intake.json` → `material_verification.udim_sampler_correction`. **This fixes the preview parent; it does not prove the larger Universal variant accepts those VT textures or handles the UDIM layout. Verify that integration before assigning it to the cast.** Do not rebuild the shader to avoid checking its existing parameter/sampler contract.

Owner's material-only evidence archive is included as `MaterialEvidence_20261016.zip`, SHA-256 `1897c87324e99f1d3ac3f90648815b9871d80c3dabb37c9bd5600dd15cacf223`. It contains intake metadata and the saved preview UDIM material, not a rig or an approved replacement for Universal. `/root/jeva` is a local Codex collaborator; the TypeSafe Jev receipt comes from the SDK consultation, not that collaborator.

Scene templates: `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Studio`, `L_Film_Office`, `L_Film_Arrival`; matching sequences and render presets under `/Game/Sequences/UniversalFilm_20261016` and `/Game/MoviePipelines/UniversalFilm_20261016`. Each has one UDS daylight actor. Cast placeholders remain hidden pending real action. Composition, floor contact and exposure still require actual cast-frame review.

Dark T-pose renders and the floating Sparrow-character preview were rejected. `Python/light_and_animate_universal_film.py` is retired with a hard error guard; do not re-enable it. `cast_reconciliation.json` confirms no Sparrow actors/bindings and hidden pending Dana placeholders. Do not publish or encode the rejected frames.

The full repo check previously passed 8/9 gates; an older unrelated Office map failed the self-named package scan for `T_Noise_White`. No repo-wide clean/pass claim exists. No commit, push, group message, accepted cast action render or final portability proof was made.

## Package contents and privacy

This handoff bundle contains the shader zip, corrected guidance, tested scripts and reports. It deliberately excludes native rigs, candidate FBXs and copied vertex data because rig licensing is single-user. Local FBX/source paths above are for work on this machine. The original failed v01 report remains historical evidence; **v08 and its final native/Houdini reports are the current rig authority**.
