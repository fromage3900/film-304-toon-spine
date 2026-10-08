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
2. **ROOT CAUSE OF THE BLACK OFFICE/ENV GEOMETRY (found 2026-10-08 evening):**
   the builders spawned sun/fill lights with a `MOVABLE -> set intensity ->
   STATIC` dance. In an unbaked level on the headless `-game`/MRQ path, a
   STATIC directional light is lightmap-only: with no BuiltData, **static
   geometry receives zero direct light** (shadows never form; only skylight
  /atmospheric ambient survives -- the faint sky-blue readings). The
   evidence chain:
     - `Python/office_asset_bisect.py` rendered FRESH cubes carrying the
       SAME .uasset instances INSIDE `L_Toon_Shot_Office`
       (`OS_EBisect_v01.png`): the fresh cubes + floor VCT speckles +
       cubicle partitions all LIT (ambient + texture execution alive);
       the staged environment around them (spawned with static lights)
       showed no direct-light response. Same instances, same bay,
       different light spawner = the mobility switch.
     - The levels that lit correctly all day (control bay
       `L_CTRL_ABC_Diag`, material probe `L_OfficeMaterialProbe`) were
       spawned with *fresh* (movable) lights.
     - `Python/_office_light_census2_20261008.py` rules out clouds, fog,
       light channels, and enabled-ness in the office level.
   **Fix applied (builder-owned):** `Python/level_lib.spawn_lights` now
   spawns/stays MOVABLE by default (`light_mobility="movable"`,
   documented WHY in-line); `Python/build_shot_stage.py`'s fill dropped the
   static dance. **L_Toon_Shot_Office was re-staged tonight** (14/14
   pieces, 0 errors) and the mobility-fix verification render of SH020 is
   the first work order for tomorrow morning (command recorded in
   `Saved/Audit/render_queue_report.json`; see `_mobilityfix_progress.txt`).
   NOTE: the static-dance pattern lives in `level_lib.spawn_lights` which
   also built `L_Toon_Shot_Env` and the lookdev levels -- after the office
   verification passes, re-stage + re-render those lanes with the same fix
   (the env buildings' black is expected to fall with it).
3. **The render harness is now truly headless and re-runnable.** The editor's
   `-ExecutePythonScript` closes the editor ~0.4 s after the script returns
   (measured 3×: `Cmd: QUIT_EDITOR`), so a post-tick/caller-poll pattern
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
4. **The Toon shader path works.** The A/B/C control
   (`Saved/Renders/controls/CTRL_ABC_20261008.png`, level
   `L_CTRL_ABC_Diag`): direct Substrate Toon BSDF + `TP_Default`
   bound in-material renders RED with visible banding in the `-game` MRQ
   path. Environment/lighting/exposure all alive.
5. **Materials are NOT the defect.** The material probe
   (`Python/build_material_probe.py`, `L_OfficeMaterialProbe`, still at
   `Saved/Renders/office_stage/OS_PROBE_materials_v01.png`) and the office
   asset bisect prove master instances light and carry their looks (taupe /
   tan / hatch / paper) under a working rig.

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
| 1 | **Verify tonight's mobility fix** (render of SH020 fired at close; see `_mobilityfix_progress.txt` + the refreshed judge file) | inspect `OS_SH020_proto_v02.png`: bands + grout + shadows present? | office stills carry the stage spec's minimum passes (VCT grout + bands, paper matte grain, polypropylene hatch, troffer emissive) |
| 2 | **Policy the same fix into the other lanes rendered black**: `L_Toon_Shot_Env` (compose_shot_env_level.py uses level_lib.spawn_lights) + lookdev levels; re-stage + re-render | loop `Saved/Audit/render_queue_report.json` `jobs[].command` | Brutalist exterior reads VALUE, not black; the shot list is presentation-ready |
| 3 | **Cleanup of bisect artifacts in `L_Toon_Shot_Office`** (leave-or-remove decision, owner): EB_Env/EB_Paper/EB_Poly cubes + EB_Cam (the asset-bisect actors), `LS_R_EBisect` + `CFG_OS_EBisect_v01` | delete the labels + re-run `build_shot_stage.py` | the staged level record is clean |
| 4 | **Control A/B/C rebuild** — cube A (legacy lit red) rendered BLACK in the control; it was authored inside a re-entrant storm. Keep the matrix honest | delete + rebuild `M_CTRL_Lit_Red` via `build_render_queue.py::build_ctrl_materials`, re-fire the `CTRL_ABC` job | A red, B documented (no-profile state), C red |
| 5 | **Package** once #1–#2 are green | `RunUAT.bat BuildCookRun -project=<proj> -platform=Win64 -clientconfig=Development -cook -allmaps -pak -archivedirectory=<dist>` | a Windows build opening `GameDefaultMap=/Game/Maps/L_Toon_Shot_Env` |
| 6 | **Laptop driver upgrade** — worth it for laptop-side lookdev, NOT the black-render cure | see `Docs/LAPTOP_DRIVER_FIX_2026-10-08.md` (R580 = last Pascal line) | laptop passes the control matrix |

## Git state at close (portable git: `D:\_PortableTools\MinGit\cmd\git.exe`)

- Committed + pushed: branch **`feature/render-harness-20261008`** (46 files:
  the harness builders, probes, judge, rig fix, audit JSONs, the two diag
  levels + control materials + CFG/LS_R diagnostic assets, the two session
  docs, `Config/DefaultGame.ini` [URL] packaging block). Commit subject:
  `feat(render): headless MRQ still harness + office-rig fix + the judged black-render verdicts`.
- Open the PR here: https://github.com/fromage3900/film-304-toon-spine/pull/new/feature/render-harness-20261008
  (the repo's pre-push hook refuses direct main pushes and requires the
  feature/ branch prefix — both guards behaved correctly during push).
- Local `main` was re-based onto `origin/main` first (1 ahead / 2 behind;
  the two remote-only commits were path-empty PR merges); the owner's dirty
  tree was stashed + POPPED during the rebase and is intact untouched.
- Portable-git one-time setup per machine:
  `git config --global --add safe.directory D:/film-304-toon-spine` and put
  `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64`
  on PATH before pushes (the pre-push hook shells out to `python`, and the
  WindowsApps Store stub breaks it).
- Gate state on this desktop: 8/9 — hooks PASS (8/8 self-test with the
  portable git wired), `fork sync (vendored vs upstream)` FAILs here (fork
  state belongs to the fork-owning machine — same class as the two known
  dogfood slot FAILs; see the morning handoff).

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
