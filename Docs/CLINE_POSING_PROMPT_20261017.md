# Prompt for Cline — headless posing + import (Film 304)

Paste everything below the line into Cline.

---

You are working in the Unreal 5.8 project at `G:\film-304-toon-spine` (project file `HumberToonShader.uproject`, engine `C:\Program Files\Epic Games\UE_5.8`). Your job is to author three character poses as AnimSequence assets, **headlessly**, and report evidence. Another agent is working in a live editor on the same project at the same time, so follow the safety rules exactly.

## Safety rules (non-negotiable)
1. Run the engine only as `UnrealEditor-Cmd.exe HumberToonShader.uproject -run=pythonscript -script=<your .py> -unattended -nop4 -nosplash -NullRHI` (or equivalent). Never open the GUI editor.
2. **Write only new assets** under `/Game/Staging/Film304Repaired_20261017/Poses_Headless/`. Never overwrite, rename, move or delete any existing asset. Never call `delete_asset` (a failed delete hung the editor earlier). If a name exists, pick a new one (`_v2`).
3. Never save or modify any map (`.umap`). Loading `L_Film_Office` read-only to measure things is fine; do not save it.
4. No git commands (no add/commit/stash/checkout). Do not edit materials or instances.
5. Put scripts and logs in `G:\film-304-toon-spine\Saved\ClinePosing\`, not in `Content/`.
6. AnimSequence frame rate: do **not** call `set_frame_rate(24)` (it throws; 24 is not a multiple/factor of 30). Leave the default 30 fps. Pose = 1 frame (2 keys), identical values.

## The three poses
Skeletons use AdvancedSkeleton joint names: `root_m, spine1_m, spine2_m, chest_m, neck_m, head_m, shoulder_l/r, elbow_l/r, wrist_l/r, hip_l/r, knee_l/r, ankle_l/r, toes_l/r`. Track names are lowercase.

| Character | Skeletal mesh | Starting AnimSequence to duplicate | Output asset | Pose |
|---|---|---|---|---|
| David | `/Game/Staging/Film304Repaired_20261017/David/SK_David_Film304_v01` | `/Game/Staging/Film304Repaired_20261017/David/Poses/AS_David_HeldPose_v02` | `AS_David_Seated` | **Seated on an office chair**, back mostly upright, hands resting on thighs or on a desk edge |
| Dana | `/Game/Staging/Film304Repaired_20261017/Dana/SK_Dana_Film304_v10e` | none exists: create with `unreal.AnimSequenceFactory` (`target_skeleton` = the mesh's skeleton) | `AS_Dana_LeanDesk` | **Leaning against the L-shaped desk**, weight on one leg, hip/forearm against the desk edge, other arm relaxed or crossed |
| Sam | `/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01` | `/Game/Staging/Film304Repaired_20261017/Sam/Poses/AS_Sam_HeldPose_v02` | `AS_Sam_ArmsCrossed` | **Standing, arms crossed over chest** (any natural folded or relaxed pose is acceptable if crossing fights the mesh) |

Existing already-saved examples you can read for reference (do not modify): `AS_David_Pose_Explain`, `AS_Sam_Pose_Shrug` in the same `Poses` folders.

## Method that already worked (reuse it)
- Duplicate the held-pose sequence (`EditorAssetLibrary.duplicate_asset(src, dst)`), load it, `ctrl = anim.controller`.
- `ctrl.open_bracket(unreal.Text("pose"), False)` … `ctrl.close_bracket(False)` in a `try/finally`.
- For each bone to change: `base = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, bone, 0, False)` (local, parent-relative); `q = base.rotation * unreal.Rotator(roll=..., pitch=..., yaw=...).quaternion()` (delta in the bone's own frame); `ctrl.set_bone_track_keys(bone, [base.translation]*n, [q]*n, [base.scale3d]*n)` with `n = unreal.AnimationLibrary.get_num_keys(anim)`.
- Save with `EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False)`.
- For Dana (no existing animation): `ctrl.set_number_of_frames(unreal.FrameNumber(1))`, then for each bone `ctrl.add_bone_curve(unreal.Name(bone))` followed by `ctrl.set_bone_track_keys(...)`. Get reference-pose locals via `pose = skeleton.get_reference_pose()` then `unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.LOCAL)`. Dana's skeleton is in T-pose at rest, so her arms need a large shoulder lowering (about −70° on the Y axis, see below).

## Axis facts already measured on David's rig (check Sam and Dana the same way; do not assume)
Component-space forward is **+Y**. Local rotation deltas (Euler roll=X, pitch=Y, yaw=Z) on an arm that hangs down:
- `shoulder_*` **Z−** swings the arm forward; **Y+** raises it outward; same sign on both sides.
- `elbow_*` **Z−** flexes the forearm forward and up; same sign on both sides.
- Forward vector was found from `toes_l − ankle_l` in component space.
Do forward kinematics yourself to choose axes for the hips and knees, which are not measured yet: compose parent-relative transforms with `unreal.MathLibrary.compose_transforms(child_local, parent_comp)` from the root down, rotate one joint about X/Y/Z by ±45°, and print the resulting child displacement in up/forward/lateral. Pick the axis that moves the shin backward (knee flex) and the thigh forward (hip flex). Record the table in your evidence file.

## Seated pose specifics (David)
- Measure the chair and seat height read-only: load `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office`, list static mesh actors whose label/mesh contains `chair` (and the L desk: `Film_ExistingOfficeDesk`, `Film_DeskReturn`), print location, yaw, and world bounds. Report the seat-top Z and which chair is nearest the desk.
- Hip flex ~85–95°, knee flex ~90–100°, ankles flat. Lower `root_m` (translation, local Z in its frame; confirm which local axis is vertical via FK) so the pelvis sits at seat-top Z plus a few cm. Keep feet at floor Z=0 (verify by FK: ankle component Z within 2 cm of the standing value).
- Spine slightly upright, head level. Hands: forearms forward, wrists near thigh tops.

## Leaning pose specifics (Dana)
- L desk is two desk actors forming an L; use the nearer edge to Dana (`Film_Subject_Dana_v08_CleanSkin` at about (-1.5, 26.5, -0.7), yaw -120). Report the desk edge height and normal.
- Weight on one leg (hip offset), spine tilted ~8–12° toward the desk, the near forearm or hip contacting the desk edge, head turned slightly. Arms lowered from the T-pose first.

## Evidence required (write `Saved/ClinePosing/report.json` and print a summary)
For each output asset: path, key count, tracks changed with the delta applied, and FK checks: (a) feet Z within 2 cm of standing, (b) wrist/hand positions relative to the body (crossed arms: each wrist beyond the opposite elbow's lateral position), (c) seated: pelvis Z vs seat-top Z, (d) lean: nearest body point to the desk edge in cm. Also list any warning lines from the engine log.

## Do not
- Do not assign poses to actors or move any actor; the other agent will do that and verify with screenshots.
- Do not change any existing pose asset or any material.
- Do not try to render or screenshot headless; verification is numeric here, visual in the editor.

When finished, reply with: the three asset paths, `report.json` path, the FK axis table, the chair/desk measurements, and anything you were unsure about.
