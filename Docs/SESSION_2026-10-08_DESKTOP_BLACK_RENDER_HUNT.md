# Handoff — 2026-10-08, session B: the black-render hunt lands the real cause

**Companion to `Docs/HANDOFF_2026-10-08_NEXT_PHASE.md`** (the morning's
lane state) — this is the afternoon session's record: what was done ON THIS
DESKTOP (Alienware Aurora R13, RTX 3080 Ti, driver 610.88, UE 5.8.2), what
was measured, and the exact resume points for the next session (likely on
another PC).

## What this session proved (all machine-portable, no laptop dependency)

1. **The morning's verdict ("machine defect, driver 527.56 class") is WRONG.**
   The black renders reproduce on THIS machine. `Saved/Audit/render_test_20261008.json`
   and `Docs/TOON_SPINE.md` line ~493 blame the laptop's driver; the MRQ
   `-game` control render proves the pipeline renders fine HERE.
2. **The render harness is now truly headless and re-runnable.** The editor's
   `-ExecutePythonScript` closes the editor ~0.4 s after the script returns
   (measured 3×: `Cmd: QUIT_EDITOR`), so the old post-tick/caller-poll pattern
   cannot run headless. The working path is the engine's own CLI (Option 1 of
   `MovieRenderPipelineCommandLine.cpp`):
     - `Python/build_render_queue.py` builds + saves, per still:
       `Content/Sequences/ProtoDiag/LS_R_<shot>` (1 frame, camera-cut bound to
       the staged camera) + `Content/MoviePipelines/CFG_<stem>` (MasterConfig:
       1280×720, PNG off of GameOverride FULLY_LOAD + Cine quality + the
       deferred pass — adding `MoviePipelineDeferredPassBase` is MANDATORY,
       else the shot builds with 0 passes and writes nothing);
     - then one `-game` process per still renders it and exits itself:
       `UnrealEditor-Cmd.exe <proj> L_Toon_Shot_Office -game -LevelSequence="/Game/Sequences/ProtoDiag/LS_R_SH020.LS_R_SH020" -MoviePipelineConfig="/Game/MoviePipelines/CFG_OS_SH020_proto_v02.CFG_OS_SH020_proto_v02" -windowed -unattended`
3. **The Toon shader path works.** The A/B/C control
   (`Saved/Renders/controls/CTRL_ABC_20261008.png`, level
   `penthouse L_CTRL_ABC_Diag`): direct Substrate Toon BSDF + `TP_Default`
   bound in-material renders RED with visible banding in the `-game` MRQ
   path. Environment/lighting/exposure all alive.
4. **The office stage's defect is the LEVEL'S LIGHTING RIG, exactly the
   owner's call.** `Python/_office_light_dump_20261008.py` dumps
   `L_Toon_Shot_Office`'s rig: it matched the spec on paper (sun 5.0, fill
   1.6, `SLS_CapturedScene` Skylight 1.0) — but with `atmosphere: false`
   the captured scene had NOTHING to capture → zero ambient; with the
   project's fixed exposure (`r.DefaultFeature.AutoExposure=False`) sun-lit
   faces blew white at 5.0 while shadows went black (the v02 white-wash/
   black-silhouette stills).
   **Fix applied (builder-owned):**
   - `specs/office_spider/stage_shots.v1.json`: `atmosphere: true` + the WHY
     recorded in `lighting_note`;
   - `Python/build_shot_stage.py`: skylight `recapture_sky()` AFTER the
     atmosphere spawns ("sky seal") + an unbounded `LGT_PPV` so the exposure
     law lives in the level; `LGT_PPV`/`Sky` added to `owned_labels`
     (re-run idempotency);
   - `L_Toon_Shot_Office` re-staged 14/14 pieces, 0 errors, and the v02
     renders are re-fired (see `Saved/Renders/_v03_progress.txt`).
5. **The material probe** (`Python/build_material_probe.py`,
   `L_OfficeMaterialProbe`, still at
   `Saved/Renders/office_stage/OS_PROBE_materials_v01.png`): under a
   working rig, master instances light and read (B taupe, D tan with
   hatch). The black was never the materials.

## Resume points (next session, in order)

**The judged state at close (`Saved/Audit/render_batch_desktop_20261008.json`):**

| still | verdict | mean_luma | reading |
|---|---|---|---|
| CTRL_ABC (control) | REAL | 144.6 | pipeline + direct Toon BSDF healthy |
| OS_SH020/030 | REAL (sky) | 75.1 | sky/atmosphere renders; master-instance surfaces inside are black/ambient-only |
| OS_SH040/050/060 | BLACK | 0.0 | all-geometry frames pitch black |
| COMP_SH010/020/030/070 | REAL (sky) | 51–68 | atmosphere renders; building silhouettes black |

| # | Work order | First concrete step | Done when |
|---|---|---|---|
| 1 | **Bisect the master's Oct-7 material core** — the sharpened diagnosis: master-derived Substrate instances receive ambient (faint sky-blue on the cubicle face in `OS_SH020_proto_v02`) but ZERO direct light, on BOTH machines, since the material-core landed (the Oct-5 real reads predate it). The direct BSDF control (cube C) works, so the data is not the suspect — the master's integration is. Highest-priority suspects in order: `MF_NormalAdjust`'s world-space normal weld (a NaN/collapsed normal kills N·L == no direct diffuse, while sky-IBL survives); the master's profile-bind path (`override_toon_profile=False` + the BSDF-carried binding, see `toon_profile_binding_probe_v3.json`); ShadowLift's zero-field. | rebuild the master WITHOUT the four surface-lane calls into a throwaway `M_Master_Toon_NoLanes` + one instance + one probe cube in `L_OfficeMaterialProbe` (via `build_render_queue.py`'s config/sequence helpers), render, compare against `M_Master_Toon_Universal` | the single lane/Knob that returns direct light to master instances is named |
| 2 | **Re-render the batch** with the named lane fixed (builders own the master; re-run the builders) | loop `Saved/Audit/render_queue_report.json` `jobs[].command` | every staged still passes the stage spec's reads: VCT grout + toon bands, paper matte grain, polypropylene hatch, troffer emissive |
| 3 | **The exterior black follows the same lead** — `L_Toon_Shot_Env` buildings carry `MI_Toon_Environment` in both slots; same master instance class, same zero-direct signature | re-render `COMP_SH010` after #1 lands | Brutalist exterior reads VALUE, not black |
| 4 | **Control A/B/C rebuild** — cube A (legacy lit red) rendered BLACK in the control; it was authored inside a re-entrant storm (drivers now guarded; materials possibly half-saved). Not load-bearing for #1, but keep the matrix honest | delete + rebuild `M_CTRL_Lit_Red` via `build_render_queue.py::build_ctrl_materials`, re-fire the `CTRL_ABC` job | A red, B documented (no-profile state), C red |
| 5 | **Package** once #1–#3 are green | `RunUAT.bat BuildCookRun -project=<proj> -platform=Win64 -clientconfig=Development -cook -allmaps -pak -archivedirectory=<dist>` | a Windows build opening `GameDefaultMap=/Game/Maps/L_Toon_Shot_Env` |
| 6 | **Laptop driver upgrade** — worth it for laptop-side lookdev, NOT the black-render cure | see `Docs/LAPTOP_DRIVER_FIX_2026-10-08.md` (R580 = last Pascal line) | laptop passes the control matrix |

## Explicit notes for the next machine

- This tree is shared by three machines (laptop `P:` / desktops). Commit your
  work with the portable git (`D:\_PortableTools\MinGit\cmd\git.exe`);
  `git config --global --add safe.directory D:/film-304-toon-spine` once per
  machine (the tree is owned by a foreign SID).
- Do NOT commit the owner's dirty tree (the modified MI/mesh re-saves);
  stage specific paths only. The pending owner decisions in the morning
  handoff still stand.
- The judge/decode helpers are pure stdlib (zlib+struct), so they run under
  UE's embedded Python at `-ExecutePythonScript` with no extra packages.
