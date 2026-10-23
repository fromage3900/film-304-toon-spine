# Session handoff — film cast and shader, 2026-10-17

## Current authority

Active goal: `EVENING_EXECUTION_PLAN_20261017.md`, six bounded gates. Live Jev
selected CAST_FIRST_THEN_SHADER at confidence 0.85; receipt:
`Saved/Audit/EveningExecution_20261017/jev_plan_review.json`.
User authorized Luna cast repair and held-pose work alongside root shader work.
User requests a refreshed handoff at 5% remaining allowance; latest check was
7% remaining. Check periodically during ongoing work and refresh before exhaustion.

**The lineup belongs only in L_Film_Office. Leave L_Toon_Shot_Hallway alone.**
The editor is now on Office, opened by Brennan for integration. Brennan owns composition, cameras, lights,
map saves and render submission. David/Sam Office actors are now updated (see below). No maps saved, no cameras/lights changed, and no Git mutations.

## Cast readiness

David and Sam clean candidates are imported and saved under
`/Game/Staging/Film304Repaired_20261017/{David,Sam}/SK_*_Film304_v01`.
David: 11 sections, 2 blink morphs, 150 imported bones. Sam: 12 sections,
2 blink morphs, 221 bones. Native/fresh Blender readbacks verify geometry,
weights, iris sections and head-follow parenting. Both UE hierarchies pass.

Dana's approved new candidate is `SK_Dana_Film304_v10e` in the Dana staging
folder. UE readback confirms 12 assigned sections, all 8 facial morphs,
FaceDeformationFollowHead parent Head_M and Eye_L beneath Head_M. Native
readback preserves rest matrices, weights and morph deltas, with measured
0.530166 cm eye motion for a 10-degree head turn. The extra raw FBX default
material was not imported as an extra section. Evidence: `ue_import_dana_v10e.json`,
`ue_dana_v10e_gate.json`, and `task1_face_eyes/report/v10e_face_follow_readback.json`.
Dana v09 has the old broken eye hierarchy; failed v10/v10b/v10c/v10d experiments
are not approved. Original source rigs remain unchanged.

All 35 section assignments on the three original staging imports are saved;
Dana v10e inherits the same 12 name-matched assignments. Each human skin uses
three separate verified 2048-square sRGB VT tiles; shoes/clothing use verified
source atlases. Hair, iris, sclera and oral sections have explicit corresponding
instances. Some source parts are authored flat colours, with no supplied maps.
Evidence: `repaired_cast_bindings.json`. New seven-look skin shelves exist. A further 28 film-owned Toon part instances
are saved (including Spider Body/Eye/Fang); six atlas bindings map BaseColorMap
to Universal Albedo. Transparent corneas use a separate copied optical master.
All 35 human sections on the current repaired staging meshes now use the
film-owned baseline family, including Dana v10e. `film_cast_part_instances.json`
and `film_baseline_cast_bindings.json` record saved readback. Opaque old Specular
controls have no asserted equivalent; appearance must be judged in the scene.
These are not yet the visible actors' materials.

David/Sam v02 relaxed held poses now pass independent FBX re-import: unchanged
feet, meaningful wrist drops, asymmetric elbow flex, slight head attitude,
unchanged rest rig within measured tolerance, and identical keys at frames 1–2.
The first armature-only export baked rest incorrectly; it was rejected. The final
mesh+armature export corrects that. Reports: each clean_cast character folder's
held_pose_v02_report.json. UE animation import and actual evaluated-pose checks now pass: 150/221 bones,
2 sample keys at 24fps, zero all-bone endpoint difference, wrist drops14–16cm,
ankle/toe shifts below0.00003cm. `ue_held_pose_evaluation.json`. Visual review remains open.
Spider and Dana final held animation remain open.
Office David/Sam actors now use repaired meshes, film baseline assignments and
serialized held animations. Obsolete flipped import pitch/roll corrected; original
XY/yaw preserved; provisional common source-unit scale gives176.7/179.1cm heights,
with bounds bottom at0. Evidence: office_cast_final_david_sam.json. Initial apply
receipt has an intermediate rotation/playback state; FINAL receipt supersedes it.
Use explicit Rotator keyword arguments and override_animation_data for persistence.
Dana actor is still on old mesh until her new held pose passes. Spider remains open.
Office baseline contains two spider actors; do not delete or rescale blindly.

## Shader readiness

Current candidate: `/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06`.
675 expressions; seven saved generic looks: Toon, Smooth, Watercolour, Gouache,
Halftone, OrderedDither and NoiseDither. Twenty-one skin look children bind the
actual three-tile VT sets for Dana, David and Sam. True smooth Substrate branch;
UV-anchored halftone with filtered dots and exact coverage endpoints, ordered
and deterministic noise dither, surface wash/grain controls, and normalized
input clamps. Roughness/metallic are clamped, and smooth metallic drives both
F0 and diffuse. Optional print computation is statically disabled for Toon/Smooth.

Latest observed permutations: Toon 736, Smooth 751, Watercolour 841 pixel
instructions, each 13 reported samplers and compiled. Receipt:
`film_physical_finish_compile_receipts.json`. This is compile proof only.
`film_delivery_closure.json` passes: 22 allowlisted packages, zero denied/private
or out-of-allowlist dependencies. Original Universal and private functions intact.
The owned NormalAdjust copy was reduced from ten duplicate subgraphs to one
complete 29-expression graph; all three calls were rebuilt and compiled.

v02/v03 are failed scratch versions; v04 retains private defaults. None are
delivery roots. `Film304_ToonShader_UE58_DRAFT_v02.zip` is the current hash/CRC-checked draft,
22 packages including clear cornea master and film eye profile. SHA256:
a9e7492fe0154a0ccaa28c3d4b2fa7e334999b26968552c10e7ee23e9bcb06c2.
v01 is stale. v02 remains explicitly unapproved for final delivery. Final archive, fresh project reopen and independent clean
source rebuild remain pending. The latest master graph snapshot has been refreshed.

## Approved diagnostic cleanup

User explicitly approved removal of L_CTRL_ABC_Diag, L_OfficeMaterialProbe,
L_Dana_CelRamp_Diagnostic and L_Dana_LashVisibility_Compare plus companion test
sequences. Registry found161 packages with no referencers outside approved sets.
Saved/Recovery/Film304_Diagnostics_20261017.zip preserves all161 files with verified
hashes/CRC. Four maps and four sequences removed through UE;134 leftover owned
external files removed only after exact archive hash/path verification. No archived
files remain under Content. Receipts: diagnostic_cleanup_inventory.json and
diagnostic_cleanup_receipt.json. Office/Hallway/film maps and shared dependencies
were excluded. No Git actions. Asset Registry may need rescan of removed externals.

## Latest visible-material issue — unresolved until owner confirms

After David/Sam Office application, Brennan reported missing textures, then
clarified CLOTHING WORKS, SKIN DOES NOT. The problem is specific to the skin path.
Latest diagnostic: only David component slot0 now overrides to the previous
MI_OneDriveRigs_David_Skin_20261016; Sam remains on new Universal. Await owner
A/B result. This is a temporary diagnostic, not final material parity. New mesh
defaults remain film-owned. Do not clear the override before reading owner reply. Effective
actor readback confirms correct skin3tile VT bindings, TextureWeight1, UDIMtrue,
and clothing/shoe Albedo atlases; skin permutation compiles. This does not prove
visible sampling. Found both film Universal and cornea masters had
used_with_morph_targets=False. Enabled it alongside skeletal usage, recompiled
and saved both; source builders now preserve those flags. Await owner symptom
choice/visible confirmation; do NOT claim fixed yet. Check actual visible failure
before changing UVs or replacing the Universal. Diagnostic cleanup complete.
Shader draftv02 predates usage-flag fix; refresh after confirmed correction.
Dana v05/v06 held-pose FBXs are not import candidates. Maya confirmed v05 scene
has keyed transforms but its initial FBX omitted animation curves; v06 selection
omitted all 19 meshes. A fresh v07 export now selects the full DAG and includes
the cast meshes; independent Maya readback is running and must pass before any
animation import. Pose-source scene: `Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_Candidate_v05.mb`.
v07 FBX: `Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v07_24fps.fbx`.
Build measurements: wrists at (+16.20,42.60,-0.15) and (-16.80,43.00,+0.15) cm;
14.50/14.10 cm below shoulders, hands 13.41/14.04 cm from hip joints, 8.18/8.82 cm
lateral torso-envelope clearance. Root, hip/ankle matrices and weighted foot envelope
are unchanged. Source v10e SHA-256 remains `4c565521f080f21bf0b5346fe36b950497936175f5442291cf2eb6f5d2009baf`;
all eight morphs retained in the held scene. Do not import until v07 readback confirms
rest geometry/bind/hierarchy, eight morph deltas, 24fps held keys and matching frame
endpoints. Supporting build/export/readback receipts are in the same `held_pose` folder.

## Remaining gates

Finish compatible held animation, coordinate Office actor application without
interrupting Hallway composition, verify grounded poses and materials through
owner-authored film renders, check print stability in motion and parameter edges,
then prove clean rebuild/reopen and produce a current class archive. Goal active;
compile/dependency/readback receipts are not visual or final-delivery approval.

## Historical overnight findings

The following is retained diagnostic history. Current state above supersedes its
old deferred/import/placement queue and visual readiness claims.

## 1. The main finding — read this first

**Every rig's imported skin textures were broken, and it was not a material problem.**

Each source PNG is a clean 2048×2048 single tile. But the importer detected the UDIM naming
pattern (`David_Diffuse.1001.png` → looks for `.1002` / `.1003` siblings) and **combined all
three tiles into one 6144×2048 virtual texture — once per import**. Three assets, each the
full strip. Evidence: all three Dana assets were exactly 8,967,257 bytes; all three David
exactly 8,971,405; Sam 11,774,187/11,774,187/11,774,188.

Consequence: the UDIM master's `frac(UV)` + tile-select logic sampled only the leftmost third
of each strip — **the head tile, painted across the entire body.** Arms got face, legs got
face. This is why Dana looked flat and wrong, and why David and Sam would have too.

It also explains a false lead: the skin *material* was never broken. `MI_OneDriveRigs_Dana_Skin`
was already correctly parented to the 3-tile UDIM master with all three tiles bound. The
textures feeding it were wrong.

**Fix, applied and verified for Dana, David and Sam:**
1. Copy each tile to a clean-named file (no `.1001` pattern) under
   `Saved/OfflineIntake/20261017/skin_tiles/<Rig>/` — otherwise the importer regroups them.
2. Re-import → true 2048² sRGB DXT1 tiles.
3. Enable `virtual_texture_streaming` and save (the UDIM master samples
   `SAMPLERTYPE_VirtualColor`; a non-VT texture bound there will not read).
4. Rebind `BaseColorTile1001/1002/1003` on that rig's `MI_OneDriveRigs_<Rig>_Skin`, save
   **immediately**.
5. Fix the master's own defaults too, so the next instance does not inherit the trap.

`Python/wire_rig_skin.py` does steps 3-5 for any rig, driven by
`Saved/Audit/MasterConvergence_20261017/_wire_request.json`.

**Result, verified in a level render (`DIAG_WHITE_v01.png`):** Dana reads dark brown skin,
dark hair, green shirt — not white. The only white left on her is her eyes, which is defect 2.

## 2. Defect two — blank white eyes (not fixed yet, cause proven)

The iris is **not separate geometry**; it is a per-face material split on the eyeball meshes.
The v08 import chain assigned each duplicate wholly to its first shading engine, flattening
every per-face split. So iris faces inherit the sclera material: a white ball with a small
pupil, no iris. No texture work can fix this — the iris section does not exist in the mesh.

`Dana_CleanSkin_v09.fbx` is already built and triple-verified
(`Saved/OfflineIntake/20261017/task1_face_eyes/`): 8 morph targets
(`Blink_L/R`, `Brow_Up`, `Brow_Down`, `Smile`, `Frown`, `Mouth_Wide`, `Jaw_Open`), 46,041
triangles and 1,231 bones identical to v08, sections **10 → 12** (adds `danairis_mat` and
`danateeth_mat`; all 10 existing names unchanged). David and Sam need the same offline Maya
pass — their rigs are the same family, so the same per-face-split loss is expected.

## 3. Asset state at handoff

**Durable (saved to disk):**

| Asset | State |
|---|---|
| `M_Master_Toon_Universal` | untouched, compiles clean, 1,303 expr / 1,341 px / 17 samplers |
| `M_OneDriveRigs_FilmToon_UDIM_20261016` | defaults rebound to Dana's correct tiles |
| `MI_OneDriveRigs_{Dana,David,Sam}_Skin` | 3 correct 2048² VT tiles each |
| `MI_OneDriveRigs_{Dana,David,Sam}_Shoes` | atlas already bound (`BaseColorMap`) |
| `MI_OneDriveRigs_{Dana,David,Sam}_Cloth` | reparented to the Albedo master + atlas bound |
| 19 × `MI_Film_*` | back on Universal, original overrides restored (37/11/10) |

**Not durable (in-memory only, lost when the editor closed):** the cast placement. The lane
never saves the level, so `Film_Cast_David/Sam/Spider` and their positions are gone. Re-run
`Python/place_cast.py` (spawns), `Python/fix_cast_meshes.py` (assigns meshes) and
`Python/tighten_cast.py` (groups them beside Dana) after loading `L_Film_Office`.
`cast_camera.py` / `verify_cam.py` spawn session cameras — **they are the part that kept
failing; prefer the authored `Film_Cam_OfficeMedium` / `Film_Cam_OfficeWide`.**

**Deleted:** `M_Film_Toon_Master`, `M_Film_Toon_Universal_Trimmed` (my two failed trim
attempts), and `T_DanaSkinTile1_Test`.

**Still present but now unreferenced:** the broken 6144×2048 strips
`T_{Dana,David,Sam}_Skin_D_1001/1002/1003_20261016`. Safe to delete once nothing points at
them — check before removing.

## 4. What I got wrong this session

- **I read "trim the Universal master" as "build up from the film master"** and reparented 19
  instances onto a master that did not have their parameters. All materials went dead. Restored
  and verified. Lesson: when the instruction names an asset as the thing being trimmed, that
  asset is the base.
- **I spent several rounds on camera placement instead of using the known-good authored
  cameras.** The scene-capture route is fine; my camera positions were the problem — they were
  outside the room or behind lamp fittings. The room is roughly `y ∈ [-250, +131]`, back wall
  at `y ≈ +131`, left wall panel at `x ≈ -371`.
- **`capture_scene_preview` cannot judge these materials** — it renders Dana black even though
  she is correct in the level. The Substrate toon BSDF does not respond to that preview scene's
  lighting. Asset previews are useless for look verification here; use the level render.
- **Two Python/API traps worth remembering:** `build_material_graph` renames node IDs on every
  call, so resolve nodes by `ParameterName`/class inside a single build, never across builds;
  and `get_inputs_for_material_expression(material, expression)` needs **both** arguments.
- **An unsaved reparent is silently reverted** by the next package reload. Save each instance
  immediately after changing it, then verify by re-reading — the tool reporting OK is not
  evidence.

## 5. The master trim — deferred, with the safe method

Deferred because the material wiring mattered more tonight. Not cancelled: the trim is about
**handoff hygiene** — Humber collaborators should not receive Melodia's shader functions, only
what the film needs.

What I learned about the graph, which makes the trim much smaller than it looked:

- The Melodia content lives in **shared material functions**, not in the master's own graph:
  `MF_Madoka` (280 exprs), `MF_Itto` (206), `MF_MeshBlend_Activator` (7). Deleting those three
  **call nodes** removes ~490 expressions of Melodia content in one step and leaves the shared
  function assets untouched for other materials.
- After that, delete the content parameter expressions (~130 names — the list is in
  `Python/trim_master_take2.py`), then sweep. That reached 841 expressions cleanly.
- **The failure mode:** the next layer of orphan cleanup (a `StaticSwitchParameter` and six
  `ComponentMask`s with deleted inputs) sits **in the live toon path, not in Melodia branches**.
  Deleting those and sweeping collapsed the material to 88 expressions with no textures and no
  switches. **Never run the aggressive orphan sweep on this graph.** Stop at the parameter
  pass and fix the remaining broken nodes individually, or accept the 841-expression version.
- Runtime cost of leaving it alone is near zero: the Melodia features sit behind static
  switches that are off by default and are compiled out. The trim buys authoring hygiene, not
  frames.

## 6. Open queue, in value order

1. **Import `Dana_CleanSkin_v09.fbx`** — morphs + the restored iris/teeth sections. Biggest
   visual jump; fixes the blank eyes and enables blinking/expression. Update the lane's slot
   map for 10 → 12 sections.
2. **Offline Maya pass for David and Sam** — same per-face iris preservation + morph export.
   `Python/export_dana_clean_skin_v09_face_morphs.py` is the chain to extend.
3. **Re-place the cast** in `L_Film_Office` (the three scripts in §3) and verify with the
   authored wide camera.
4. **Derived normal maps** — 15 PNGs at 2048² under `task7_derived_maps/` (AO / curvature /
   tangent normal per tile + the shoes atlas), all labelled derived. Need a normal sample added
   to the UDIM master (it has no normal input) and **Flip Green** on import (they are
   OpenGL-style +Y). Test one material before committing.
5. **Tile 1003's AO is saturated** (mean 10/255) — the leg skin sits inside the pants/shoe
   shells. A skin-only-occluder rerun is a one-parameter change if it matters.
6. **The trim**, per §5, when the handout to Humber is actually being prepared.
