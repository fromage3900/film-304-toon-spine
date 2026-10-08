# Handoff — next phase: staged deck → judged shader renders — 2026-10-08

**Read first:** `Docs/TOON_SPINE.md` (live spine inventory + the 2026-10-08
render-path state), `Docs/MELODIA_TOON_CONVERGENCE.md` (film material core,
§4–§6), `Docs/OFFICE_SPIDER_SHOT_PLAN.md` (73-shot plan + gaps).

## Where this lane stands (committed, verified)

- **Film material core is landed.** The six utilities (MF_NormalAdjust,
  MF_SurfaceWear, MF_DF_ContactBlend, MF_Impasto, MF_FilmGrade, stabilized
  MF_ClothWindDrape) + the static deep-night sky preset `MI_Toon_Sky_DeepNight`
  are generated through the builders, wired into the right masters
  (Universal / Landscape / PostComposite / Sky), and pass the gates:
  spine run 4 `OVERALL: PASS`; fresh-process compile-at-load clean across 15
  masters + 12 functions (`Saved/Audit/loadonly_gate_20261007.json`);
  `Tools/verify_all.ps1` 9/9; dogfood green except two pre-existing owner
  staging-slot naming violations (Slot #01/#03).
- **The camera stage is landed.** `specs/office_spider/stage_shots.v1.json`
  + `Python/build_shot_stage.py` built `L_Toon_Shot_Office` (14/14 pieces,
  0 overlaps, sits-on stacking, 16:9 filmbacks) with storyboard cameras
  `Cam_WS_SH020..SH060`; SH010 renders through the already-staged exterior
  (`Cam_Env_SH010`, `L_Toon_Shot_Env`). SH070–SH120 defer on recorded reasons
  (rigs not imported = plan gap 7.11; no kitchen shell = 7.12).
- **The render harness is machine-portable.** `Python/render_prototypes.py`
  now takes a `spec` override in the request file; the SAME request fires
  stills on any machine. Nothing needs code changes to move the render tier.

## The next-phase goal (one sentence)

**Turn the staged, verified deck into JUDGED shader renders: first on a
machine that renders Substrate (desktop / P:), then close the laptop's
defect, and only then extend the shot list (rigs, kitchen) and the MRQ tier.**

## Work orders, in priority order

| # | Work order | Owner / machine | First concrete step | Done when |
|---|---|---|---|---|
| 1 | **Texture fresh-load decay** (P0): textures read 256² in-process, load as the 32×32 default in fresh processes on THIS laptop, even for untouched committed assets | owner decision | open the project in the interactive editor ONCE and read `T_SDF_Strokes` size; then run the same load-only probe on the desktop (same G: bytes) | verify_expansion reads `ok=True` somewhere real, and the machine/scope of the defect is named |
| 2 | **Office Spider still batch on the SM6 workstation** (P1): fire the full `stage_shots.v1.json` shot list + the exterior spec's SH010/SH020/SH030/SH070 | desktop (`laptop` remote / P:) | write `_request.json` with `"spec": "...stage_shots.v1.json"`, shots SH020..SH060, then the exterior request; read the PNGs | every staged still exists at 1280×720 and the toon reads are judged (VCT grout + bands, paper grain, polypropylene hatch, troffer emissive) |
| 3 | **Deep-night sky preset review in SH010/SH020** (P1, the brief's own gate): the preset has no consumer level yet — a sky dome mesh carrying `M_Master_Toon_Sky` + `MI_Toon_Sky_DeepNight` needs staging into the exterior composition, then the same render pass | desktop | add the dome piece to `prototype_renders.v1.json` (inverted-facing sphere or backfaced card) + the preset instance, re-run compose + render | SH010/SH020 night stills judged; the preset is promoted or dialled |
| 4 | **Set + rig critical path** (P2, the film's own): kitchen/hallway build-out (plan gap 7.12) and the worker/spider/coworker rig binds (7.11); then stage SH070–SH120 cameras the same way | owner + toon lane | the compose-script extension for the break-room shell | SH110 (money shot) and SH100 staged; stills |
| 5 | **MRQ presets** (P3, final tier): the plan's gap 14 — preset assets + the video-tier pass, bound to camera-cut sequences | owner decision | author the MRQ preset (16:9, 1080p+, EXR) as a tracked asset via a builder | the final-render gate per act can run |
| 6 | **Guards** (P3): fold the fresh-process compile-at-load gate into `Tools/verify_all.ps1`; add the duplicate-key detector for the DP OVERRIDES table to `Tools/dogfood_toon_spine.py` | agent, any machine | one check each, both already have proven implementations from this session | both gates run in the standard entry points |

## Explicit non-goals (carry-over from the brief)

- Iridescence, sparkle, vein-glow/rings (`MF_Madoka`) stay out of Humber until
  a concrete shot demands one — no speculative functions.
- No time-of-day system; the night look is the static preset.
- No hand-edited graphs; every change lands through a builder.
- No wholesale merges from other machines/lanes; the laptop lane promotes
  named artifacts only.

## Pending owner decisions (blockers, named)

1. The texture `.uasset` rewrites in the working tree (256² r4 content, the
   `task.save=False` fix) — commit them after work order 1 lands, or keep
   dirty until then (they are currently deliberately uncommitted).
2. The owner's own dirty tree (Office Spider staging resaves, Config/ SM6 +
   ray tracing changes) — commit on their side; this lane did not touch it.
3. The laptop's driver (527.56) — upgrade vs keep rendering on the desktop.

## How to resume on a fresh checkout

```powershell
git fetch origin; git switch main; git pull        # canonical
# verify the spine before anything else:
UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript="Python/build_spine.py" -stdout -unattended
# assert %TEMP%/spine_build_report.json OVERALL: PASS
powershell -File Tools/verify_all.ps1              # 9/9
python Tools/dogfood_toon_spine.py --all           # (2 known slot naming FAILs, owner files)
```
