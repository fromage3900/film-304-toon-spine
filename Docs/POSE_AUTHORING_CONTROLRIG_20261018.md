# Fixed poses with Control Rigs — what exists, what to build, how to gate it

Date: 2026-10-18 · Evidence: `Saved/Audit/Poses/inventory.json`,
`pose_library.json`, `david_seated_bones.json`

## 1. Measured state

| Thing | Reality |
|---|---|
| `CR_David`, `CR_Dana`, `CR_Sam`, `CR_Spiders` | Real `ControlRigBlueprint`s (IndependentRig), hierarchy imported from the `SK_*` skeletons, `bExposesAnimatableControls = True`, a `FilmRoot` null — **but no authored controls** (no `*_CONTROL` elements in the hierarchy) |
| The rig that actually made the shipped poses | Sequencer's transient **native `FKControlRig`** (`Saved/Audit/Film304Idle_20261017/artist_pose_edit.json`: 304 elements, `head_m_CONTROL`, `elbow_r_CONTROL`, …) |
| Shipped poses | **17 AnimSequences**, all 2-key holds. Six are the fixed poses (`AS_David_Seated`, `AS_Dana_LeanDesk`, `AS_Sam_ArmsCrossed` + `_Polish01`) |
| Where they live | `/Game/Staging/Film304Repaired_20261017/Poses_Headless/` — a staging folder, not a production one |
| Frame rate | **Inconsistent**: David/Sam pose sequences are 1/24 s (24 fps), Dana's are 1/30 s (30 fps). The idle sequences are 24 fps |
| Pose-space scale | Head top ≈ **75 pose-cm** for David seated. Pose space is *not* level centimetres; never compare a bone Z to a chair's world height |

## 2. The target contract

A fixed pose is **two identical keys on an AnimSequence**. The Control Rig is the
authoring surface; the sequence is the render artifact. Bake because MRQ should
not evaluate a rig graph per frame, and every existing gate already reads
AnimSequences.

Minimum control set to add to each `CR_*` (then expose as animatable):

| Group | Controls |
|---|---|
| Body | `CTRL_Root`, `CTRL_Hips`, `CTRL_Spine_01..03`, `CTRL_Neck`, `CTRL_Head` |
| Arms | `IK_Hand_L/R` + `Pole_Elbow_L/R`, `CTRL_Clavicle_L/R`, `CTRL_Wrist_L/R`, `CTRL_Fingers_L/R`, `CTRL_Thumb_L/R` |
| Legs | `IK_Foot_L/R` + `Pole_Knee_L/R`, `CTRL_Ball_L/R`, `CTRL_Toes_L/R` |
| Face | `CTRL_Eye_L/R`, `CTRL_LidUpper_L/R`, `CTRL_BrowInner/Outer_L/R`, `CTRL_Jaw` |
| Switches | `IKFK_Arm_L/R`, `IKFK_Leg_L/R`, `FootRoll`, `ArmStretch` (all default off) |

Naming note: controls are `CTRL_*`; bones keep the imported names `Root_M`,
`Spine1_M`, `Ankle_L`. The Maya prompt used lowercase (`root_m`) — do not key
those names in UE.

## 3. Workflow

1. **Author** in `CR_<character>` (Sequencer Control Rig track), or headlessly
   with bone-local deltas for a first pass.
2. **Hold**: duplicate the frame-0 keys onto the last frame. No tangent drift.
3. **Bake** to `/Game/Animations/Poses/<Character>/AS_<Character>_<Pose>_v##`.
   Never overwrite an existing pose asset; add `_v02`.
4. **Verify** with `Python/verify_pose_library.py` (reads
   `specs/cast/pose_library.v1.json`).
5. **Visual gate**: one frame from the actual shot camera per pose. Numbers
   cannot see floating wrists, fingers entering a skull, or a seated pose that
   reads as "perched".

## 4. The gate (implemented)

`Python/verify_pose_library.py` → `Saved/Audit/Poses/pose_library.json`

- key count == 2 and endpoint error < 1e-3 (translation, scale, and a quaternion
  angle — not just the linear channels)
- feet within −2 … +5 **pose-cm** of the reference floor (Z = 0)
- records pelvis Z, ankle/toe Z, and wrist-vs-opposite-elbow for review
- anything needing the level (seat top, desk edge) is reported as
  `not_checked`, never silently passed

Current result: **6/6 pass**, with two `not_checked` entries that require the
level (David's seat contact, Dana's desk contact). Those are the two that must
be signed off on a frame.

## 5. Traps this closes

- **24 vs 30 fps.** Do not call `set_frame_rate(24)` on a 30 fps asset; and do
  not mix 24 fps poses with 30 fps idles in one blend without checking.
- **Staging paths.** Production poses belong under
  `/Game/Animations/Poses/<Character>/`; the current ones are under
  `/Game/Staging/...` and will be lost in a staging cleanup.
- **Rig without controls.** A `CR_*` with only an imported hierarchy cannot be
  posed in Sequencer usefully. Today the project works around this with the
  transient `FKControlRig`; that is why the rig assets and the shipped poses do
  not match.
- **Unit confusion.** Pose-space cm ≠ level cm. Seat/desk contact must be
  measured in-level, against actor bounds.
