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
- 1 exponential height fog — keep; toon tolerates fog if materials are authored for it.

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
