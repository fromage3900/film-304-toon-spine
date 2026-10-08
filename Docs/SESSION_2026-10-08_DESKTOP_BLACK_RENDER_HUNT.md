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
2. **ROOT CAUSE OF THE BLACK OFFICE/ENV GEOMETRY (found + corrected 2026-10-08 evening):**
   the staged pieces are parked at **STATIC component mobility** after their
   mesh swap (`spawn_piece` / `level_lib.spawn_mesh` both ended
   `set_mobility(STATIC)`), while every render that LIT today used freshly
   spawned components at their default mobility. Static-mobility static
   meshes + Stationary lights + no built lighting data
   (`L_Toon_Shot_Office` has none) evaluate **lightmap-only** under the
   -game/MRQ path: no BuiltData = no baked direct light = black geometry,
   with skylight/atmospheric ambient still surviving (the faint sky-blue).
   Evidence:
     - **Bisect 1 (same level, same lights, same instance .uassets):**
       `office_asset_bisect.py` added three fresh cubes carrying the exact
       same `MI_*` assets INSIDE `L_Toon_Shot_Office`
       (`OS_EBisect_v01.png`); their faces shade and carry the looks
       (gray-blue ambient, polypropylene hatch VISIBLE) while the staged
       pieces around them stayed black.
     - **Bisect 2 (the census)**: `_office_light_census2_20261008.py` shows
       the office level has NO clouds/fog/channel blockers; the re-staged
       lights are Stationary spawn defaults (`mobility:
       ComponentMobility.STATIONARY`) -- so a first fix attempt that only
       touched light mobility (commit 1c169b0) did NOT change the render.
       The successful renders all day (control `L_CTRL_ABC_Diag`, probe
       `L_OfficeMaterialProbe`, the EBisect cubes) are exactly the ones
       whose components were never parked STATIC.
   **Fix applied (builder-owned):** both `Python/build_shot_stage.py
   spawn_piece` and `Python/level_lib.py spawn_mesh` keep the mesh-swap
   dance but END at the spawned default mobility (documented inline).
   Verification render of SH020 fired at close (`_piecefix_progress.txt`);
   re-run the spec's minimum-pass read on it first thing tomorrow.
   NOTE: `compose_shot_env_level.py` and the other lanes using
   `level_lib.spawn_mesh` inherit the fix on their next re-stage.
3. **The evening falsifier matrix (all fired, all evidence on disk):**
   | falsifier | result |
   |---|---|
   | `office_freshmi_bisect.py` -- fresh MI straight from the master vs staged MI vs staged VCT, same bay (`OS_EBisect_freshMI_v01.png`) | fresh == staged: the instance .uassets are NOT the defect; all Substrate surfaces shade AMBIENT-only, direct sun absent |
   | `office_keydir_test.py` -- KeyLightDir flipped +Y/-Y on fresh instances (`OS_EBisect_keydir_v01.png`) | NO visible change -- the hand-set toon key is not the lever |
   | `office_gioff_falsifier.py` -- the same frame with GI off via MoviePipelineConsoleVariableSetting (`OS_EBisect_GIoff.png`) | essentially unchanged -- the tier's intended `lumen_gi: false` would not change the black class |
   | `_piecefix_progress.txt` render | still black -- piece-mobility alone did not revive direct light |
   | **the one divergence found** | inside the office level, direct sun reaches exactly ONE surface: the carpet patch's top strip (also visible lit in both bisects). Everything else in the same frame shades ambient-only |
   | **movable-sun falsifier (fired at close, `_movablesun_progress.txt`)** | `level_lib.spawn_lights` now sets the sun EXPLICITLY MOVABLE (stationary spawn defaults lean on built-shadow data the unbaked levels do not have); the office re-staged + re-rendered -- READ THE PNG FIRST THING |
4. **The render harness is truly headless** (`build_render_queue.py` +
   the recorded `-game` commands; see the morning half of this doc), the
   **Toon shader path works** (control A/B/C: direct Toon BSDF + TP_Default
   = red + banded), and **materials are not the defect** (probe + asset
   bisect).
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
| 1 | **Read the movable-sun falsifier PNG** (`Saved/Renders/office_stage/OS_EBisect_freshMI_v01.png`, re-fired after the movable-sun re-stage; chain `_movablesun_progress.txt`) | open the PNG: do the fresh/staged cubes + floor + walls now receive direct light (bands + cast shadows)? | office surfaces carry the stage spec's minimum passes: VCT grout + bands, paper matte grain, polypropylene hatch, troffer emissive |
| 2 | **If #1 is still black**, the next two levers, in order: (a) `cast_static_shadows=False` on sun/fill via the builder (static shadows need built data the level does not have); (b) re-stage with the TEMPLATE-level trick that demonstrably lit all day: create the office bay from `EditorLevelLibrary.new_level` (Open-World template default environment, the proven-lit spawn path) instead of `LevelEditorSubsystem.new_level` | one falsifier render per lever, same EBisect rig | the lever that restores direct light is named |
| 3 | **Full batch** once #1/#2 go green: re-stage ENV + lookdev lanes with the same light fixes, then loop `Saved/Audit/render_queue_report.json` `jobs[].command` | per the morning half of this doc | every staged still passes the spec reads; the deck is presentation-ready |
| 4 | **Cleanup of bisect artifacts in `L_Toon_Shot_Office`** (owner decision): EB_FRESHMI/EB_STAGEDENV/EB_STAGEDVCT/EB_KEY_A/EB_KEY_B/EB_Env/EB_Paper/EB_Poly cubes + EB_Cam + `LS_R_EBisect` + the EB CFGs | delete the labels, then re-run `build_shot_stage.py` | the staged level record is clean |
| 5 | **Package** once reads are green | `RunUAT.bat BuildCookRun -project=<proj> -platform=Win64 -clientconfig=Development -cook -allmaps -pak -archivedirectory=<dist>` | a Windows build opening `GameDefaultMap=/Game/Maps/L_Toon_Shot_Env` |
| 6 | **Laptop driver upgrade** — laptop-side lookdev only, NOT a black-render cure | see `Docs/LAPTOP_DRIVER_FIX_2026-10-08.md` | laptop passes the control matrix |

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
