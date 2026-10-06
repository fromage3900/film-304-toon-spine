# Toon expansion close-out — 2026-10-02

Record of the office-film toon pass. Measured claims only; the evidence files are named
next to each one so a later session can re-derive rather than trust this document.

## What changed

| Area | Before | After |
|---|---|---|
| Textures | none in the repo | **9** generated (`Content/Materials/Textures/`) |
| Toon profiles | 11 | **19** (8 new `TP_Office_*`) |
| Material instances | 18 | **18** (8 new `MI_Toon_Office_*`) |
| Pattern fields | 8 | **12** (Voronoi, Grid, Perforation, Weave) |
| Master | ramp inert; no emissive | `RampStrength` parameter; `EmissiveColor` lane |

**Spine build: 40 assertions, 0 failing** — `Saved/Audit/spine_build_report_2026-10-02.json`.
Textures: `Saved/Audit/texture_build_report.json`.

## Three defects found, and what each one actually was

### 1. The ramp subsystem was inert (real, pre-existing)

`build_master_toon.py` wired a hard constant `0.0` into both `MF_ColorRamp3` and
`MF_RampLUT`'s `Mask` input. Both functions end in `lerp(base_color, ramp_rgb, mask)`, so
at mask 0 they returned `BaseColor` unchanged: `bUsePaintedRamp` toggled between two
identical results and all six `Ramp*` parameters plus `RampTexture` were unreachable.

`verify_material` never caught it because it counts function **calls**, not their influence —
this repo's own "structurally valid, semantically empty" failure class. Fixed by promoting
the constant to a `RampStrength` scalar **defaulting to 0.0**, so every pre-existing
instance renders identically and the ramp is reachable on opt-in.

### 2. Three healthy profiles failed verification — the assertion was wrong, not the data

The first version of `verify_profile`'s texture check compared against an invented exact
string. Probing (`Saved/Audit/toon_texture_ref_probe.json`) showed UE 5.8 exports object
properties **quoted and fully qualified**:

```
ShadowHatchingPatternTexture="/Script/Engine.Texture2D'/Game/.../T_Hatch_Cross'"
```

The bindings had worked all along. Fixed with a real parser (`_field_value`) that reads the
field's own value, unit-tested against the exact export string before re-running the build.

### 3. `T_HatchPattern` was a dangling reference in *both* repos

`specs/humber_toon_spine/humber_toon_spine_manifest.v1.json` (byte-identical in Melodia and
this repo) names `T_HatchPattern`; Melodia's `tp_melusina.json` does too. **The asset
existed in neither.** This repo now generates it. Melodia's copy is still dangling — a
Melodia-lane item, not ours.

### 4. The spine was running with NO Toon Profile bound — found only by going live

`toon_profile` is a property of the **`MaterialExpressionSubstrateToonBSDF` node**, not of
the material and not of the material instance. All seven candidate property names were
rejected by UE on `MaterialInstanceConstant` (`toon_profile_binding_probe_v3.json`), so
`build_instances._apply()` had been writing to a property that **has never existed** —
swallowed by `spine_lib.try_set`, which reported success.

Consequence: **19 `TP_*` assets, zero bound.** Every surface in the film was shading on
engine defaults, while `verify_material` passed because it counted function calls.

Fixed three ways: the master binds `TP_Default` to its BSDF node; the dead call is removed
from `_apply()`; and **`verify_material` now fails the build if the profile is unbound**, so
it cannot pass silently again.

### 5. `try_set` was silently swallowing every expression write

```python
if obj.has_editor_property(prop):   # does NOT exist on material expressions
```

That method does not exist on expressions in this build, so every call raised and was
swallowed. `try_set` now attempts the set directly and logs the reason on failure.

### 6. Python module caching made builder edits invisible — the costliest bug here

Run repeatedly inside one long-lived editor via `run_python`, `__import__` returns the
module cached on the **first** import. Every edit made between runs was ignored: a newly
added logging block never printed while older code in the same file kept running, and the
`try_set` fix appeared to "do nothing". `build_spine.py` now evicts the builder modules from
`sys.modules` before importing, so a run reflects what is actually on disk.

This also invalidates a class of measurement: **a change to `Python/` is not live until the
module is re-imported**, and "the log printed the old code" is not evidence the new code ran.

### 7. Texture settings were being skipped while the build reported green

Enum resolution by `dir()`/`__members__` returned empty for all seven settings, so every
one was skipped as "unresolved" — and `TA_WRAP` merely *looked* applied because it is the
engine default. `build_textures.py` now resolves by direct member probing (real names:
`TF_NEAREST`, `TC_VECTOR_DISPLACEMENTMAP`, `TMGS_NO_MIPMAPS`), and **an unresolved enum is
a hard build failure** rather than a skip.

Measured before/after on `T_Dither_Bayer`: `TF_DEFAULT` → `TF_NEAREST`,
`TC_DEFAULT` → `TC_VECTOR_DISPLACEMENTMAP`. This mattered: `TC_DEFAULT` is block
compression, which averages 4×4 blocks and destroys the exact 16-level Bayer matrix.

## Three API facts this build does not match

Measured, because each would otherwise have failed mid-build:

1. `MaterialEditingLibrary.connect_material_expression` **does not exist**; use
   `connect_material_expressions` / `connect_material_property`.
2. `expression.has_editor_property()` **does not exist** on material expressions — set via
   `try/except set_editor_property`.
3. `get_inputs_for_material_expression()` returns **upstream objects, not pin names**. Use
   `get_material_expression_input_names()` (which is what `spine_lib.unary()` uses).

Also: `AssetImportTask` has no `automated_import_should_be_imported`, and enum member names
are **uppercase** (`TF_NEAREST`, `TA_WRAP`, `TC_DEFAULT`). `build_textures.py` now resolves
enums by pattern and writes every member list into its report, so a future mismatch is
diagnosable from a file instead of another four-minute editor boot.

## Gate status: 7 of 8, and the failure is not this pass

`Tools/verify_all.ps1` is **red**, on `fork sync (vendored vs upstream) — DRIFT: core.py`.

**Not caused by this work.** The vendored copy is from `10-01 16:17`; upstream
`P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/core.py` changed today at
`15:34` (67,674 → 73,918 bytes). Nothing in this session touched `Blender/`. The 2026-10-01
gate run passed precisely because upstream had not moved yet.

Re-vendoring is a deliberate Blender-side operation (`Tools/resync_fork.py --write`) and is
**not** done here — it touches the shared fork and is an owner call.

Everything else passes: Blender fork verifier 16/16, external actors 158 packages, package
naming, documented paths, pre-commit hook 8/8.

## Open decision: per-family Toon Profiles

A material instance **cannot** carry its own Toon Profile on this engine build — measured,
not assumed. `CONTENT_CONVENTIONS.md` says "pick by subject, not by taste", and each
`MI_Toon_*` names the profile it assumes, but right now **every instance inherits the single
profile bound to the master** (`TP_Default`), and `override_toon_profile` is `false`
everywhere.

Options, none of which this pass chose unilaterally:

1. **One shared profile + per-family look from instances.** The instance parameters already
   authored (`BaseTint`, `AccentTint`, `InkColor`, `Pattern*`, `Emissive*`) carry the
   variety; band structure stays global. Zero new masters.
2. **One master per family**, each bound to its own profile. Honours "pick by subject"
   literally, but multiplies masters against the "two masters" convention and every master
   re-binds all instances.
3. **Assign in-editor**, accepting that it is not reproducible from `Python/` — which
   contradicts `CONTENT_CONVENTIONS.md` ("change the builder, rebuild").

This is an owner decision, not a technical one.

## Known open items

- Per-family Toon Profiles (above).
- `L_Toon_Shot_Env` has no builder mapped, so `ASSETLIST.md` reports it `UNKNOWN`.
- `MF_ProceduralPatterns` is now 464 expressions (Voronoi contributes ~90). Fine for offline
  film rendering; worth revisiting if it ever must run per-frame.
- Melodia's `T_HatchPattern` reference is still dangling on that side.
- No lookdev capture yet — structure and bindings are verified by read-back, but nobody has
  *looked* at the office surfaces.