# MRQ render gate — when a shot may be called "final"

MRQ presets are currently listed as "not yet started" in
`Docs/OFFICE_SPIDER_SHOT_PLAN.md`. This document defines the minimum gate before
any shot may be marked final. No shot is final without passing every item here.

## 1. Preset naming

Use the existing convention:

- `CFG_<PROD>_<SHOT>_<variant>_v<nn>` under `Content/MoviePipelines/`
- Examples already present: `CFG_OS_SH020_proto_v02`, `CFG_COMP_SH010_proto_v02`

Required prefixes:

- `proto_` — blocking/lookdev renders (not final)
- `final_` — only after §3 passes

## 2. Minimum render settings

- HDR 16-bit EXR for color grading.
- 256+ samples for clean toon edges.
- MSAA or TAA (toon edges are sensitive to aliasing).
- Movie Render Pipeline output, not viewport capture.

## 3. Acceptance checklist (all required)

For each shot, all must be true in the rendered output:

1. No T-pose fallback or frozen pose.
2. All expected render meshes present (19 for Dana).
3. No body or lash loss.
4. No sliding, clipping, or floating (floor contact verified from evaluated bounds).
5. Exposure and floor contact read correctly in frame.
6. Outlines present and weighted correctly (`MI_Outline_Thin` characters/props,
   `MI_Outline_Heavy` architecture).
7. No missing material/texture references or pink shaders.
8. Post-composite grade applied (`MI_Toon_PostComposite`) — grain 0.08, vignette 0.35.
9. Render produced through a named MRQ preset, not a manual viewport capture.
10. Evidence (rendered frame + report JSON) saved under `Saved/Audit/`.

## 4. What is NOT acceptable as proof

- Viewport screenshots.
- T-pose or neutral-pose frames.
- Sparrow character substituted for a film character.
- Dark frames used to imply "moody" lighting without exposure verification.
- A sequence that has not been played back for sliding/clipping.

## 5. Failure handling

If any item fails:

- Record the failure in `Saved/Audit/<shot>_render_failure.json`.
- Do not mark the shot final.
- Do not reuse the failed frame as evidence.
- Fix the underlying cause (rig, material, lighting, or composition) before retry.

## 6. Scope rule

MRQ presets are added per act, in this order:

1. Act I–II porcelain pass (correct surfaces, shakeout).
2. Shots 21/38/55/72 spider macros (rim/halo tuning).
3. Full act passes after the Dana gate in `Docs/DANA_ACTION_SHOT_RUNBOOK.md` passes.
