# Goal: cinematic render quality and godrays (2026-10-18)

Status: **Phase 1 complete and verified against the live editor** (2026-10-19). Phases 2–4
pending rendered proof.

## Correction to the Phase 1 finding: the scripts are not the authoritative values

Probing the live editor showed the saved level does **not** match any setup script:

| Property | Live level | Scripts write |
|---|---|---|
| `fog_density` | 0.0055 | 0.0016 / 0.0018 / 0.002 / 0.003 / 0.006 / 0.0075 |
| `fog_height_falloff` | 0.06488 | 0.12 / 0.08 |
| `fog_max_opacity` | 1.0 | 0.92 / 0.65 |
| `start_distance` | 7357.9 | 3000 |
| `volumetric_fog_extinction_scale` | 2.5 | 1.2 |

So the drift is worse than "five scripts disagree". The level was hand-tuned past all of
them, and none of the real values were written down anywhere. **The scripts are stale, not
authoritative** — re-running them would not restore the approved look, it would replace it
with something nobody has seen.

This also corrects the extinction question flagged below: the level holds 2.5, which the
v07 doc entry calls "the prior". The proposed 4.0 was never applied or visually approved.
`REVIEWED_EXTINCTION_SCALE` is therefore 2.5, matching reality, with 4.0 deferred to a
rendered A/B rather than adopted as a default.

Sequence chosen by Jev (`Saved/Audit/Film304_Closeout_20261018/jev_fog_godray_review.json`,
choice A, confidence 0.88, live). Jev's reasoning: godrays *are* a volumetric fog effect, so
the medium must be stable before the effect can be iterated or A/B tested. Creative lighting
work done on a drifting fog baseline produces results that cannot be compared.

## Phase 1 — Lock fog (DONE)

Problem found in the audit: five scripts wrote `fog_density` with five different values and
nothing detected the conflict, so re-running any of them silently changed the approved look.
Two of them also hard-coded `volumetric_fog_extinction_scale = 1.2`, reverting the
render-reviewed 4.0 from the v07 comparison in `GOAL_ESTABLISHING_SHOTS_20261017.md`.

Delivered:

- `Python/film304_fog.py` — single source of truth. Label-resolved actor lookup with a
  singleton assert; every mutation requires an explicit `FogIntent`; `apply()` returns a
  before/after receipt; `drift_report()` is a read-only guard; only
  `apply_reviewed_baseline()` may write the extinction scale.
- `Python/audit_fog_drift.py` — read-only pre-render gate. Exits non-zero on ownership errors
  (duplicate fog, unbound UDS hook, visible UDS internal fog).
- `Tools/check_film304_fog_offline.py` — 15 assertions against a stubbed `unreal`, runnable
  without the editor. Currently passing.
- Migrated all 5 writers and both fragile lookups. `Tools/houdini/execute_houdini_cinematic_lookdev.py`
  no longer loops over *every* height fog actor of class, which would have re-enabled fog on
  duplicates.
- `Python/check_fog.py` deprecated — it read `volumetric_fog`, which the live probe
  confirmed is **not a readable editor property in UE 5.8 at all**. The script was reading
  a property that does not exist while every writer set `enable_volumetric_fog`.

Bugs caught before they reached production:
- Offline checks caught the UDS custom-fog reference being stringified (a UObject repr always
  looked unbound) and a `None` hook being skipped rather than flagged. Both would have made
  the audit lie in the direction it needs to be trusted.
- The live probe caught the 4.0 extinction assumption in the first draft of this document.
- The live probe also revealed that the editor caches `film304_fog` across script runs, so
  edits were invisible until a reload. Both live scripts now `importlib.reload()`.

Verification actually performed (not assumed):
- `Python/audit_fog_drift.py` run live: singleton owner, UDS hook bound to `EST_Fog_E1`, UDS
  internal fog hidden, `drift.clean == true`.
- `Python/verify_fog_apply_live_20261018.py` round trip: wrote the old 1.2 clobber value,
  confirmed drift detection fires with two findings, restored 2.5, and asserted the level
  was byte-identical afterwards.
- `Tools/check_film304_fog_offline.py`: 15 assertions against a stubbed unreal, passing.

## Phase 2 — Close the temporal reprojection footgun (PENDING)

`r.VolumetricFog.TemporalReprojection=0` cut loop seam drift 82 percent (wrap MAE
1.8899 → 0.3451) but lived in one delivery script, so any new sequence that forgot it
inherited the full drift.

- [x] Single definition in `film304_fog.render_console_overrides()`
- [ ] Apply to every MRQ config that renders a volumetric-fog shot, not just
      `CFG_Office_Still20/ Motion48`. Audit `Content/MoviePipelines/Film304Closeout_20261018/`
      and `Content/MoviePipelines/Film304Dusk_20261018/`.
- [ ] Verify on a dusk or skyline sequence (not just the office) — that is where fog history
      accumulates most.

Kept shot-scoped on purpose. The global project setting was rejected in review.

## Phase 3 — Godray rig: resolve the toon wash-out (PENDING)

Current state: three `Film_WindowShaft` spots (140cd, 4300K, 1500 atten, 11/18 cone,
volumetric scattering 6.0, volumetric shadow on) plus `Light_Cinematic_SunBeam` at
intensity 5.5 / volumetric scattering 3. `SCENE_LIGHTING_AUDIT_20261018.md` flags two
competing 4–5 intensity directionals in one toon frame as the likely wash-out.

Open question, unresolved in the current docs: `FILM_PIPELINE.md` says post-process cel
shading and the outline pass fight fog and translucency, yet Mie volumetric scattering at
g=0.65 is on globally. The audit's "toon tolerates fog" line was never backed by a render.

- [x] **Lighting/PPV re-audited live** — `Python/audit_lighting_ppv_live.py`, receipt
      `Saved/Audit/Film304_Closeout_20261018/lighting_ppv_live_audit.json`. Results below.

- [ ] **The godray rig has the same clobber bug the fog had.** Live shafts sit at
      **180 cd / volumetric scattering 8.0**. `converge_master_showcase_20261018.py`
      writes **140 / 6.0**. Re-running that script silently drops every window shaft by
      22% intensity and 25% volumetric scattering — i.e. weakens exactly the godrays this
      plan exists to strengthen. Port the shafts into a single source of truth the same way
      `film304_fog.py` was done, and make the audit fail on the delta rather than just
      report it.
- [ ] Then run the fog A/B below, on a fixed camera, with matched everything else.

A fifth arm is now available for free: extinction 2.5 vs the proposed 4.0. That comparison was
already half-run — the level has 2.5 and the v07 note says 4.0 was proposed and never applied —
so it needs no new setup, only two renders.

### Fog ownership: what actually writes what (2026-10-19)

Replacing the sky (`Film_UDS_Daylight` was relabelled `Ultra_Dynamic_Sky` and the
`Custom Height Fog Actor` hook reset to None) exposed the real architecture. The first
conclusion drawn here was **wrong and has been corrected** — recording it because the
wrong version was plausible and produced a fix that broke volumetrics.

**Wrong version:** "the hook re-applies the sky's fog settings every tick, so both
components must be seeded, and volumetrics cannot be enabled from Python at all — it
needs a UI toggle in the sky's details panel." Acting on that produced a dual-write
"seed both components" fix which *switched volumetrics back off*.

**Reproduced, correct version:**

| Action (hook bound, sky internal fog hidden) | Result |
|---|---|
| write `enable_volumetric_fog=True` on `EST_Fog_E1` only | **holds**, 3+ ticks |
| write volumetric settings on the sky's internal fog component | UDS re-evaluates and forces `enable_volumetric_fog` back to **False** in the same tick |

So the hook is not the writer. **Writing to the sky's internal fog component is.**
`apply_reviewed_baseline()` therefore writes the external actor only, and
`seed_both_fog_components()` is retained but documented as a trap. The audit's drive
report exposes `do_not_write: "the sky's internal ExponentialHeightFogComponent"` so the
constraint travels with the data.

What remains true about ownership: with the hook bound the sky supplies its own fog, and
unbinding the hook lets UDS force-enable its internal `HeightFog` on the next tick,
which is double fog. So keep the hook bound and the sky's internal fog hidden.

**Live state, verified across three separate invocations:** one visible fog
(`EST_Fog_E1`), hook bound, sky internal fog hidden, `enable_volumetric_fog = True`,
extinction 2.5, Mie 0.65, `drift.clean = true`, `godrays_possible = true`.

`fog_density` was deliberately left at 0.00551 — the sky swap moved it (0.0055 →
0.0075 → 0.00551) and there is no evidence which value is intended. The warm
establishing-stage inscattering tint (0.55, 0.40, 0.30) was also zeroed by the swap;
restore it if the exterior look depends on it.

**This settles the earlier "let UDS own the environment" question.** It does own the sky
and its internal fog. `EST_Fog_E1` remains the single visible fog and is writable, but
one component must be left alone.

### Live lighting/PPV findings (2026-10-19)

**This settles the earlier "let UDS own the environment" question.** It already does,
and more completely than expected: `EST_Fog_E1` is now a passthrough that UDS overwrites.
Writing fog values on `EST_Fog_E1` directly will not hold. `film304_fog.apply()` is
still correct for *auditing* and for per-shot sequencer tracks, but level-level fog
authority belongs to the sky.

### Live lighting/PPV findings (2026-10-19)

Both of `SCENE_LIGHTING_AUDIT_20261018.md`'s recommendations were **already applied**. That
document is stale and should not be used as the work list.

| Audit doc claimed | Live | Verdict |
|---|---|---|
| RimKicker 4.88 | **0.5** | changed |
| EST_Fill 0 (disabled) | **1.1**, channel 1 only | changed |
| SunBeam 5.5, vol scatter 3 | 5.5, vol scatter **2.5** | partly changed |
| 5 PPVs, all priority 100, weight 1.0 | **13 PPVs, all weight 0.0 or disabled** | resolved |
| 7 point, 2 spot lights | 42 total: 3 dir, 9 spot, 12 point, 15 rect | changed |

- `competing_directional_keys: false` — only SunBeam is >= 4. The "do not run two 4-5
  intensity directionals" rule is **not** currently violated. Do not "fix" it.
- `ppv_stack_is_single_writer: true` — every PPV is weight 0.0 except the dormant
  outline/compare set, all of which are disabled. No contested priority.
- **Consequence for Phase 3:** the two rig problems the plan was going to fix are already
  fixed. Phase 3 is now just the fog A/B and the shaft clobber. Do not re-do the rig work.
- `EST_Fill_E1` is correctly on **channel 1 only** while RimKicker and SunBeam are channel 0 —
  that is the intended "fill never touches the office set" behaviour from the establishing
  pass, and it is intact.
- `Film_City_Searchlight_01/02/03` (95000/70000/60000 cd) are **not visible**; they are
  night-sequence-only, as `build_city_night_showcase` intended. They are not a day-scene
  wash-out risk.

### The A/B (needs rendered proof — do not skip)

Interior office shot, `LS_Closeout_WindowHero48f_v01` or the DuskHero equivalent, fixed
camera, all other settings identical:

| | Arm | Purpose |
|---|---|---|
| A | volumetric Mie fog on, g=0.65, extinction 4.0 | current |
| B | volumetric Mie **off**, distance fog only | tests the toon-compat assumption |

Inspect both at full res for: outline integrity on characters and window frames, material
separation in the cubicle labyrinth, shaft readability, and overall value range. Record the
actual images, not a summary.

If B reads better for interiors, split by shot type — volumetric for exterior establishing
and skyline, distance-only for interior toon — rather than choosing globally. That is the
shape of the fix; the render decides it.

### Exterior godrays

Lower risk, and the fog setup is already correct there. Keep volumetric Mie on. The exterior
work is skyline composition and fog depth (`GOAL_ESTABLISHING_SHOTS_20261017.md`), not rig
changes.

## Definition of done

- [ ] `audit_fog_drift.py` exits 0 on every delivery level, with values at the reviewed baseline
- [ ] Every volumetric MRQ config carries the temporal reprojection override
- [ ] Godray rig has one dominant key; PPV stack is single-writer per shot
- [ ] Interior A/B rendered at full res and inspected; decision recorded with image paths
- [ ] Fade-loop seam re-measured after any fog change; no declaration of a perfect seam

## Constraints

- One idempotent assembly/save pass per session; one curated render batch after approval gates.
- Reacquire editor actors after MRQ/reload rather than holding stale component references.
- Advisory text is not visual approval. Jev ranked the sequencing; Jev has not seen a render.
- Do not declare an atmosphere loop seamless from setup alone — v11 improved seam error
  82 percent but did not reach zero.