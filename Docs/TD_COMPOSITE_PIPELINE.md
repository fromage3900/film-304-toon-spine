# TouchDesigner composite pipeline - Film 304

**Status: BUILT AND PROVEN on one frame (2026-11-17).** No message was sent to
the professor or the group. This is a finishing-path proof, not a delivered shot.

- Script: `C:/MelodiaTouchDesigner/tools/td_film_composite.py` (idempotent, `fc_` prefix)
- Live project: `C:/MelodiaTouchDesigner/grandmaster_melodia7.22.toe`
- Bridge: Envoy on `127.0.0.1:9870` (twozero/`:40404` is NOT used here)
- Proof still: `C:/tmp/film_composite_proof.png`
- Before/after: `C:/tmp/film_compare.png`

## How to run

1. Confirm Envoy: `mcp__envoy__get_td_status` (connected: true).
2. Run the durable script in TD:
   `mcp__envoy__execute_python(code=<contents of td_film_composite.py>)`.
3. Change `INPUT_FILE` at the top of the script for another plate.
4. Verify: `mcp__envoy__get_op_errors(op_path="/project1/fc_out", recurse=True)`
   and save a still: `op("/project1/fc_out").save(path)`.
5. To export a movie: set `EXPORT = True` and re-run (MovieFileOut, `mjpa`),
   or pulse `/project1/fc_rec.par.record`.

## Network (under `/project1`)

```
fc_filein -> fc_resize -> fc_levels -> fc_bloom_thresh -> fc_bloom_blur
          -> fc_bloom_gain -> fc_bloom_add (+ levels)
          -> fc_vig_mul (x circular ramp from fc_vig_keys)
          -> fc_grain_add (+ scaled noise) -> fc_grade -> fc_out
```

## Verified result

- Output 1280x720, matching the source plate; `fc_out` errorCount 0.
- Source mean 0.339 -> graded mean 0.31; teal wardrobe `[0.61,0.85,0.77]`
  stays `[0.61,0.86,0.78]` (no white-shift); red/orange stays within ~0.02.
- Eye check of the side-by-side image: restrained finish, shot still readable.
- The project has 107 warnings, all pre-existing (Embody sync-file notices,
  `water_vfx` cook loops, missing plates). None come from `fc_*`.

## Traps that cost real time here - do not re-discover

- In Envoy `execute_python`, OP classes live in the `td` module
  (`td.moviefileinTOP`); bare names are not in the exec namespace.
- There is no `colorcorrectTOP` in this build - use `levelTOP`.
- `levelTOP.brightness1` is a MULTIPLIER; setting it to 0 blacks the frame.
- Generator TOPs (ramp/noise) default to 256x256; force `outputresolution='custom'`
  on generators and composites or the chain collapses to a black 256x256 frame.
- Ramp TOP `type='radial'` is ANGULAR (pinwheel). Use `circular` with a key
  table (`pos/r/g/b/a`) and `extendleft/right='hold'` for a real vignette.
- Threshold TOP `comparator='less'` keeps HIGHLIGHTS above threshold here;
  `greater` passed the dark 92% of the frame and washed the image out.
- Bloom threshold must be >=0.95 or bright teal wardrobe pixels bloom to white.
- `noiseTOP` uses `mono`, not `monochrome`; `mathTOP` uses `preoff/gain`.

## Better shots - next steps (Film 304)

The SSS/porcelain fix for `MI_Dana_Skin` is in `BS_GodFile/Saved/DanaProfessor/`
(`fix_skin_sss.py`, `refine.py`, `build.py` patched). For film-usable shots,
follow `Docs/DANA_ACTION_SHOT_RUNBOOK.md`: v08 hash check, import, deformation
checks, retarget `Jog_Fwd`, material assignment, compose one grounded action
shot, MRQ render. Feed those renders through this pipeline to prove the path.

