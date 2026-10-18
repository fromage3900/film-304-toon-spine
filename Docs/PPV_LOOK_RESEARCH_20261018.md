# PPV look research and polish notes (2026-10-18)

## Current PPV settings (from scene probe)

| PPV | Key overrides | Best use |
|---|---|---|
| `PPV_P2_WatercolourPaper` | warm paper tint (244,237,224), vignette 0.35, exposure +0.4 | Soft, painterly, watercolor-inspired shots; good for gentle character moments |
| `PPV_StorybookOutline` | saturation/contrast +6-8%, chromatic fringe 0.08, bloom 0.4, film grain 0.05, vignette 0.28 | Storybook/illustrated look; supports outlines and graphic styling |
| `PPV_P3_RisoPrint` | cool paper tint (243,241,255), vignette 0.2, exposure +0.3 | Riso/print aesthetic; graphic, slightly cool |
| `PPV_P4_CleanCinematic` | neutral tint, bloom 0.4, histogram auto-exposure, vignette 0.12 | Clean cinematic baseline; best default for film renders |
| `EST_PPV_Ink` | no overrides | Likely ink-only or placeholder; not a full look |

## Research notes (indie film)

- Toon/cel films usually keep the post look **restrained**: a single global grade plus subtle vignette/grain. Heavy bloom or chromatic fringe can fight the flat color bands.
- `MI_Toon_PostComposite` already provides the shared grade (grain 0.08, vignette 0.35). PPVs should be treated as **shot-specific style overlays**, not competing global grades.
- For a comedic office short, `CleanCinematic` is the safest hero look; `StorybookOutline` can be reserved for stylized beats (spider macros, title cards).
- `WatercolourPaper` and `RisoPrint` are strong stylizations and should be used sparingly to avoid inconsistent tone across acts.

## Polish recommendations

1. Keep only one PPV active per shot (BlendWeight 1, others 0).
2. Standardize vignette: 0.12–0.28 for cinematic, 0.35 only for stylized/painterly beats.
3. Keep bloom threshold high (0.95) to avoid glowing toon edges.
4. Film grain: 0.05–0.08 max; higher grain fights flat color.
5. Auto-exposure: prefer fixed exposure for toon consistency; histogram method is acceptable if min/max are tight.
6. Do not stack PPVs; the current equal-priority stack is the main risk.

## Suggested assignment

- Act I (office routine): `PPV_P4_CleanCinematic`
- Spider macros (shots 21, 38, 55, 72): `PPV_StorybookOutline`
- Donut Day inserts: `PPV_P2_WatercolourPaper` (optional)
- Title card (shot 65): `PPV_P3_RisoPrint` (optional)
- Default fallback: none (global post composite only)
