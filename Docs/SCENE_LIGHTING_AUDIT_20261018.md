# Scene lighting/post-process audit — L_Film_Office (2026-10-18)

## Findings

### Directional lights
- `Cast_RimKicker_Light` (DirectionalLight_0): Intensity 4.88 — active rim/key contributor.
- `EST_Fill_E1` (DirectionalLight_1): Intensity 0 — effectively disabled.
- `Light_Cinematic_SunBeam` (DirectionalLight_3): Intensity 5.5, VolumetricScatteringIntensity 3 — strong second key with heavy volumetric scattering. This is the most likely wash-out competitor with the rim kicker.

Recommendation: keep one dominant key for toon readability. Prefer `Cast_RimKicker_Light` as the key and either disable `Light_Cinematic_SunBeam` or reduce it to a low rim/accent (intensity <= 1, volumetric scattering <= 1). Do not run two 4–5 intensity directional lights in the same toon frame.

### Post-process volumes
All five PPVs are unbound, BlendWeight 1.0, Priority 100:
- `EST_PPV_Ink`
- `PPV_P2_WatercolourPaper`
- `PPV_P3_RisoPrint`
- `PPV_P4_CleanCinematic`
- `PPV_StorybookOutline`

With equal priority and full blend weight, they compete; the effective look is ambiguous and can wash out material reads. For toon, the post stack should be single-writer (`MI_Toon_PostComposite` is already the global grade).

Recommendation: choose one look per shot/sequence. Set non-active PPVs to BlendWeight 0 or Priority lower, or remove them from the shot level. Keep the stack explicit in the shot plan.

### Other lights
- 7 point lights (ceiling cavities, desk lamps) — likely acceptable if intensities are modest.
- 2 spot lights (hero fill, unnamed spot) — check for overlap with the key.
> **STALE — re-read live before acting.** Every number below was re-read from the live
> editor on 2026-10-19 (`Python/audit_lighting_ppv_live.py`). Both recommendations in this
> document had already been applied and the figures no longer match:
> RimKicker 4.88 → **0.5**; EST_Fill 0 → **1.1**; SunBeam vol scatter 3 → **2.5**;
> "5 PPVs all at weight 1.0" → **13 PPVs, all weight 0.0 or disabled**.
> `competing_directional_keys: false` and `ppv_stack_is_single_writer: true` today.
> See `GOAL_GODRAYS_AND_CINEMATIC_QUALITY_20261018.md`. Kept for history only.

- 1 exponential height fog (`EST_Fog_E1`) — keep, but see the caveat below. Ownership is
  now single-source: resolve and mutate it only through `Python/film304_fog.py`, and run
  `Python/audit_fog_drift.py` before delivery renders.

  Caveat, still unproven: "toon tolerates fog if materials are authored for it" is an
  assumption, not a rendered result. `FILM_PIPELINE.md` states that post-process cel
  shading and the outline pass fight fog, bloom and translucency, yet forward Mie
  volumetric scattering at g=0.65 is enabled globally. The interior toon shots have never
  been compared with volumetric Mie fog on versus distance fog only. That A/B is now the
  open question for godray work — see `GOAL_GODRAYS_AND_CINEMATIC_QUALITY_20261018.md`.

## Recommended next actions

1. Pick the hero look for the Dana shot (clean cinematic vs storybook outline).
2. Disable or reduce `Light_Cinematic_SunBeam`.
3. Set PPV blend weights so only the chosen look is active (others 0).
4. Re-render the Dana frame and compare material reads.
5. Record the chosen settings in the shot evidence file.

## Updated plan

Phase 1 (Dana gate) remains the critical path, with lighting cleanup added as a sub-gate:

1. Audit lighting/PPV stack (this doc).
2. Apply recommended light/PPV changes.
3. Verify deformation on Dana.
4. Retarget already complete.
5. Compose Dana shot with chosen lighting.
6. Render proto MRQ and fill evidence template.

No final renders until lighting is stable.
