# DCC pose-polish research — Maya 2027 / Cascadeur 2026 / Blender / UE-native

Date: 2026-10-17 (evening pass) · Scope: how to polish the three Film 304 poses
(`AS_David_Seated`, `AS_Sam_ArmsCrossed`, `AS_Dana_LeanDesk`) beyond the v1
headless-procedural pass, using Maya or Cascadeur headless where they help.

## TL;DR

| Route | Headless | Verdict |
| --- | --- | --- |
| **Maya 2027 (`mayapy`)** | yes, proven | **Best "alternative" route for body contacts.** The artist rigs are full AdvancedSkeleton rigs (24 IK handles each). A posed Maya joint set converts to UE bone-locals **exactly** (round-trip 4.6e-5 cm over 122 bones). Leg IK works; arm IK does not drive the deform arm in this rig (use FK arms). |
| **Cascadeur 2026.1.3** | no, GUI-bound | CLI Python **does execute** (`--run-python-code`), but the process is a full GUI app, startup ~10 s, no headless flag. Useful only as an optional physics/centre-of-mass checker or for additive layers; not worth the pipeline risk for three static poses. |
| **Blender 4.5** | yes, proven | Already used for the Sam sleeve; can also solve IK, but re-importing the cast rigs is heavier than Maya and adds a second source of truth. Keep it for mesh work. |
| **UE-native additive** | yes, proven | **Recommended primary polish.** Fingers, wrist pronation, palm alignment and contact refinement as an additive pass on the existing pose assets, verified with the existing gates. Deterministic, no axis-conversion risk. |

The single biggest visual defect in v1 is **fingers at rest** (splayed), because
v1 keyed only the spine/limb chain. Finger and wrist work is cheap and safe in
UE; body contact solving is where Maya adds real value.

## Evidence produced by this pass

All under `Saved/ClinePosing/dcc_inventory/`:

| File | What it proves |
| --- | --- |
| `david_maya_probe.json`, `sam_maya_probe.json` | rig inventory: joints, skin influences, IK handles, controls, constraints |
| `david_maya_ik.json` | headless IK/FK test on David: switch channels, handle moves, joint travel, finger FK travel, rest + posed world matrices for all 538 joints |
| `ue_ref_world.json` | UE reference pose (world + local) for every bone of David/Sam/Dana, read-only |
| `align_check.json` | Kabsch fit Maya rest → UE rest: **body max 2.4e-5 cm**, det = −1 (right-handed Y-up → left-handed Z-up) |
| `ue_pose_from_maya.json` | 122-bone conversion of the posed Maya rig to UE bone-locals; **round-trip max 4.6e-5 cm** |
| `maya_ik_probe.py`, `maya_rig_probe.py`, `probe_ref_world.py`, `align_check.py`, `maya_to_ue.py` | repeatable probes and converter |
| `casc_probe_out.json`, `casc_run*.log` | proof Cascadeur executes injected Python, with its API version and scene manager reachable |

## Maya 2027 — what actually works

### Install and invocation

* `C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe` (Maya 2027; the 2025
  install has no `mayapy`).
* Rig sources (read-only): `G:/Film304_AssetIntake_20261016_Source/3rd Year Film/Rigs/`
  * David `Temp/David_Rig_v1.51/David_Rig_v1.51.mb` (38 MB)
  * Sam `Guy/Sam Rig/C_Guy.mb` (38 MB)
  * Dana `Temp/Dana_Rig_v1.5/Dana_Rig_v1.5.mb`
* Command used:
  `mayapy Saved/ClinePosing/dcc_inventory/maya_ik_probe.py <rig.mb> <out.json> --test`
* A rig opens in **~20–25 s**; the scene is opened with
  `executeScriptNodes=False` and **never saved**.

### Rig inventory (measured)

| Rig | joints | skin-weighted joints | IK handles | control curves | constraints on joints |
| --- | --- | --- | --- | --- | --- |
| David | 538 | 276 | 24 | 327 | 380 |
| Sam | 663 | 317 | 24 | 367 | 460 |

Both are AdvancedSkeleton-style: `FKIKLeg_L/R`, `FKIKArm_L/R`,
`IKSpineHandle_M` (spline), toe/ankle un-twist handles, and FK controls for
every finger (`FKIndexFinger1_L` …). The deform chain (`Root_M`, `Hip_L`,
`Knee_L`, `ElbowPart1_L`, …) is **constraint-driven** from separate IK and FK
skeletons, so the pose must be read after `cmds.refresh(force=True)`.

### FK/IK switch semantics (probed)

* Channel: `FKIKBlend` on `FKIKLeg_L` / `FKIKArm_L` (not `fkik`).
* **10 = IK, 0 = FK.**
* Defaults: legs `10` (IK), arms `0` (FK).

### What the probe proved

* **Leg IK is live.** Moving `IKLeg_L` or `IKLegHandle_L` +6 cm world Y moved
  `Ankle_L` by exactly 6.0 cm and `Toes_L` followed; the knee/thigh re-solved.
  This is the useful half for seated/leaning contact work.
* **Arm IK does not drive the deform arm** in this rig: with `FKIKBlend = 10`
  and `ikBlend = 1.0`, translating `IKArm_L` by 6 cm moved the handle 6 cm but
  `Wrist_L` by only **0.12 cm**. The arm deform chain stays on FK. Consequence:
  author arms with the FK shoulder/elbow/wrist controls (or the existing UE
  solver), not with `IKArmHandle_L`.
* **Finger FK works.** `rotateY`/`rotateZ` on `FKIndexFinger1_L` moved the tip
  **1.09 cm** at 20°; `rotateX` moved it **0.046 cm** (twist about the finger
  axis), so the curl axis is Y/Z on that control and X is twist.

### The Maya → UE bridge (the important result)

A direct FBX round-trip is not required. World matrices are enough:

```
C       = [s*R | t]                rest Maya world -> rest UE world
D       = M_posed * M_rest^-1      Maya world-space delta
D_ue    = C * D * C^-1             the same delta in UE world space
W'_ue   = D_ue * W_rest_ue
L'_b    = W'_parent^-1 * W'_b
```

* The fit is a **similarity with det = −1** (Maya right-handed Y-up, UE
  left-handed Z-up). Forcing `det = +1` produces a 6 cm error at the ankles —
  the classic handedness trap.
* Scale is **1.000000**, so no unit conversion is needed (both rigs are cm).
* Rest alignment: **42/42 body joints exact to 2.4e-5 cm**; across all 122
  shared joints (including fingers) the residual is < 1e-4 cm.
* Posed conversion: 122 bones, **round-trip max 4.6e-5 cm**; the probe's
  +6 cm Maya Y ankle move lands at **+6.000 cm UE Z**, as expected.
* No UE run is needed for the conversion itself; only the final write into an
  `AnimSequence` needs the editor.

### Cost / risk

* ~25 s per rig per process; `mayapy` is single-scene, so one process per
  character.
* Rigs load with Redshift/Arnold node warnings (harmless; plugins missing).
* The source `.mb` is never saved.
* Arm IK is not usable as-is; finger and leg controls are.

## Cascadeur 2026.1.3 — CLI works, headless does not

* Install: `C:\Program Files\Cascadeur\cascadeur.exe`, version **2026.1.3**
  (`b3cc25e8…`), embedded Python 3.11.
* The executable exposes `--run-python-code` and `--run-script` (strings in
  `cascadeur.exe` and `presenter_lib.dll`).
* **Proven**: `cascadeur.exe --run-python-code=exec(open(r'…\casc_probe.py').read())`
  wrote a marker from inside the app:

```json
{"cwd":"c:\\Windows\\System32\\spool\\drivers\\x64\\3",
 "version":"2026.1.3","has_application":true,"scenes":1,
 "scene":"<csc.view.Scene object …>"}
```

* **But it is a GUI application.** The process stayed alive with a window after
  the script ran; `--help` printed only startup logs and exited. There is no
  documented headless/offscreen flag. Launch pattern that survives the tool's
  process-tree kill: `Invoke-CimMethod Win32_Process Create` (scheduled tasks
  are denied), then poll the marker file, then `Stop-Process`.
* API surface relevant to polish (from `resources/scripts/python/samples/api_document.py`):
  * `csc.fbx.FbxSceneLoader` / `FbxLoader` — import/export FBX, import animation;
  * `csc.layers` — layers, cycles, **Additive Layers (Alpha)**;
  * `csc.tools.attractor.attract` — IK-like attraction;
  * `csc.tools.AutoPhysicTool` — only `turn_off` / `turn_off_all_fulcrum_points`
    are documented; **AutoPosing is a rig-generation behaviour**
    (`rig_gen2/autoposing/autoposing_factory.py`), not a one-call "solve pose";
  * `csc.tools.AnimationUnbakingTool`, `csc.tools.AutoPosingTool` exist as tool
    handles but are not scripted at the "pose this character" level.
* Verdict: **do not use as the primary authoring route** for three static poses.
  It is a reasonable optional check for centre-of-mass/physics plausibility
  (Dana's lean, Sam's crossed-arm balance) or for an additive secondary-motion
  layer later. Risks: sign-in/licence prompt, GUI dependency, non-determinism,
  and a heavy FBX round-trip on a custom skeleton.

## Blender 4.5 — keep it for mesh work

* `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe` is the working
  build (the 4.3 path is broken).
* Already used headlessly for the Sam clean-cast / sleeve work; can also solve
  IK with bone constraints, but importing the three cast rigs and re-exporting
  would duplicate Maya's job with a second axis/scale convention.
* Best use: the sleeve offset and any mesh-level fix; not pose authoring.

## UE-native additive polish — recommended

This is the cheapest way to make the existing poses read better, and it reuses
the verified `pose_lib` FK model and the existing verification gates.

1. **Fingers (biggest win).**
   * Curl axis: knuckle line = normalize(`IndexFinger1 - PinkyFinger1`) in
     component space; test ±5° on the middle phalanx and keep the sign that
     reduces fingertip→palm distance.
   * Cumulative curl per character:
     * David (hands on thighs): 25/20/15/10° + thumb 15/10/10°
     * Sam (arms crossed, hands tucked): 55/50/40/30° + thumb wrap 25/20/30°
     * Dana (right palm on desk): 5/5/5°; left hand on stomach: 20/15/10°
   * `Cup_L/R` rotates with the palm; do not leave it at rest.
2. **Wrist / palm orientation.**
   * Current palm normal ≈ normalize(cross(`IndexFinger1 - PinkyFinger1`,
     `MiddleFinger1 → MiddleFinger3`)); choose the sign that gives the smaller
     correction.
   * Desired normals: David palms down (0,0,−1); Dana right palm down (0,0,−1),
     left toward the stomach; Sam each palm toward the opposite upper arm.
   * Apply the minimal rotation to the wrist's world orientation (children
     follow), then a small flexion so the hand lies along the thigh/desk edge.
3. **Contact refinement.** Re-solve arms with the existing coordinate-descent
   solver against *skeleton-space* targets (world target ÷ actor scale):
   * David: wrists 6.9 cm high on the thigh midpoints → bring to ~2 cm above
     the thigh surface, fingers following the thigh slope;
   * Sam: wrists 4–6 cm in front of the chest, elbows wider than wrists, hands
     under the opposite upper arm;
   * Dana: hip within ~3 cm of the desk edge, right forearm along the edge.
4. **Key every weighted bone.** Extend `Rig.relevant` to the skin-weighted set
   (Maya's `weighted_joints` lists: David 276, Sam 317; Dana from its rig) and
   write identical keys at both frames. Verification: track count == weighted
   bone count, and a fresh-process readback that checks each weighted bone has
   a non-default key.
5. **Do not overwrite v1.** Duplicate the pose asset to `…_Polish01` (or refine
   in place only after the fresh probe, since the level was saved again at
   22:27 and 22:46).

## Comparison

| | Maya | Cascadeur | Blender | UE-native |
| --- | --- | --- | --- | --- |
| true headless | **yes** | no (GUI) | **yes** | **yes** |
| drives the cast rigs | **yes, exact** | needs FBX rerig | needs FBX import | native |
| IK legs / feet | **yes** | yes | yes | analytic, already implemented |
| IK arms | **no (rig wiring)** | yes | yes | analytic solver |
| fingers | **yes (FK controls)** | yes | yes | **yes (bones exist)** |
| determinism | **high** | medium | high | **high** |
| setup cost | medium (25 s/rig) | high | medium | **low** |
| risk to assets | none (read-only) | FBX round-trip | mesh only | lowest |

## Recommended sequence

1. Fresh read-only probe (the level was re-saved at 22:27 and 22:46, so the
   seat/desk/actor measurements in `report.json` are stale).
2. Maya, per character: open rig, set `FKIKBlend = 10` on legs, place
   `IKLeg_L/R` for floor/seat contact, pose arms with FK controls, curl fingers
   with FK finger controls; `refresh`; dump world matrices; convert with
   `maya_to_ue.py`; write a new `AnimSequence`.
3. UE additive pass: wrist/palm alignment + finger refinement on top of the
   Maya result, key every weighted bone, run the existing gates plus
   fingertip/palm/elbow checks.
4. Optional Cascadeur check: import the resulting FBX and inspect
   centre-of-mass/physics, not for final output.

## Reproduction

```powershell
# Maya inventory + IK test (detached; mayapy lives ~25 s)
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = 'cmd.exe /c "G:\film-304-toon-spine\Saved\ClinePosing\dcc_inventory\run_maya_ik.cmd"'
}

# UE reference pose (read-only; back up the Monolith sentinel first)
powershell -File Saved\ClinePosing\run_ue.ps1 -Script Saved\ClinePosing\dcc_inventory\probe_ref_world.py -Tag refworld

# Offline alignment + conversion
python Saved\ClinePosing\dcc_inventory\align_check.py
python Saved\ClinePosing\dcc_inventory\maya_to_ue.py
```

## Limitations / notes

* The Maya arm-IK finding is specific to these two rigs; a different rig may
  wire `IKArmHandle_L` correctly. Re-probe before assuming.
* `david_maya_ik.json`'s "posed" state is a synthetic probe (leg handle +6 cm,
  arm control +6 cm), not a production pose — it exists to validate the bridge.
* The UE reference pose is the imported skeleton rest, not necessarily the
  artist's preferred A-pose; the delta-based bridge handles that.
* The level `.umap` mtime changed at 22:46:42 local during this pass, after our
  only UE run finished (22:39:54). No map was loaded or saved by these scripts;
  the change came from the live editor / another process.
* Monolith deletes `Plugins/Monolith/Saved/.monolith_running` on shutdown even
  in commandlet mode. The live editor was restarted during this pass (PID
  111816, 22:53), so the sentinel was rewritten to point at the *current* editor
  (`{"pid":111816,"port":9316,...}`, port 9316 confirmed owned by 111816)
  rather than restoring the stale pre-restart file.

## Implemented in this pass — additive UE polish (`_Polish01`)

`Saved/ClinePosing/polish_poses.py` created three new assets from the v1 poses
(v1 files untouched, mtime 01:54:54). Every skeleton bone is keyed with two
identical frames; wrist position is unchanged, so all v1 contact targets are
preserved.

| Character | Asset | Bones keyed / skeleton | Weighted keyed | Palm error before → after | Fingertip→wrist before → after | Fingertip moved vs v1 |
| --- | --- | --- | --- | --- | --- | --- |
| David | `AS_David_Seated_Polish01` | **150 / 150** | 119 / 119 | 89.8°/87.0° → **3.0°/3.0°** | 8.18 → **7.89 cm** | 12.3 / 12.0 cm |
| Sam | `AS_Sam_ArmsCrossed_Polish01` | **221 / 221** | 174 / 174 | 69.3°/64.4° → **6.6°/6.6°** | 8.36 → **7.04 cm** | 4.6 / 3.8 cm |
| Dana | `AS_Dana_LeanDesk_Polish01` | **1230 / 1230** | 332 / 332 | 54.2°/81.8° → **2.5°/1.2°** | 6.18 → 6.03/6.18 cm | 3.8 / 2.8 cm |

* Every phalanx 1–4 curls (per-finger cumulative angles 25/20/15/10 for David,
  50/42/32/22 for Sam, 8/7/6/4 right + 22/18/14/8 left for Dana), thumb curls
  and opposes, `Cup` follows the palm.
* Palm normals are aligned by a minimal world rotation of the wrist; the
  measured residual is 1–7° (the remainder comes from re-measuring the hand
  axis after the finger bases move).
* Endpoint error **0.0** on all three; a fresh process readback
  (`polish_readback.json`) confirms 2 keys, 1 frame, track count == bone count.
* Evidence: `Saved/ClinePosing/polish_report.json`,
  `Saved/ClinePosing/polish_readback.json`, logs `polish_20261017_230125.log`
  and `polishreadback_20261017_230344.log`.
* Visual review is still required: the large wrist rotations (80–90° for
  David/Dana right) are numerically correct but the silhouette and
  hand-to-thigh/desk contact need a screenshot before these replace v1.
