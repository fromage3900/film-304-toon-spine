# UE 5.8 toon research port — what Melodia's documented research means for the 304 office film

**Written 2026-10-02.** Source of truth for the toon decisions in this repo that are
not derivable from the builders themselves.

Every claim below cites the Melodia file it came from. Melodia is read-only input here:
nothing in `P:/MelodiaMelusinaV2-Laptop` was modified to produce this document. Where
Melodia's research is a *recommendation for a large open-world game* and the film is a
bounded office set, the port says so rather than importing the rule wholesale.

## 1. The stack is Epic-native Substrate Toon, and that is a choice

`UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md` §1.3 concludes the Melodia platform is
"architecturally sound … but Epic-native Substrate Toon, **not a studio toon framework**."
The research compares two viable routes:

| Route | What it costs | Status |
|---|---|---|
| (a) Epic's experimental `SubstrateToonBSDF` + `ToonProfile` | no fork; parameters still move | **adopted here** |
| (b) engine fork (MooaToon) | fork/Substrate conflict, licence, physics maintenance | **ruled out** |

The fork is excluded for this film on the same grounds Melodia excluded it: it is mutually
exclusive with Substrate, and a student capstone cannot carry a maintained engine fork.

**The one finding that changes our defaults:** the project sits on `Blendable` GBuffer,
which caps the closure set — one closure feature per pixel, no F90, no per-pixel diffusion
SSS, no haziness, no native glints (same doc, §1.3). For an office film this is a **good**
trade: fluorescent troffers and a window key want diffuse + a tight specular, not
dispersion. Do not spend time attempting hair/anisotropic glint here.

## 2. The ramp contract — the single biggest artist control

Research §4.1 ranks ramp shape first, noting MooaToon exposes exactly light/shadow *range*
+ ramp and that it "is the single biggest control artists use."

**This repo already has the shape and was not using it.** `MF_ColorRamp3` exposes
`RampLow/RampMid/RampHigh/RampPosMid/RampContrast/RampSharpness`, and `MF_RampLUT` takes a
painted 1D texture. But the master hard-wired a constant `0.0` into both functions' `Mask`
input, and both end in `lerp(base_color, ramp_rgb, mask)` — so at mask 0 they returned
`BaseColor` unchanged. `bUsePaintedRamp` was switching between two identical results and all
six `Ramp*` parameters were unreachable.

The build verifier never caught it, because it counts function **calls**, not their
influence. That is this repo's own documented failure mode
(`CONTENT_CONVENTIONS.md`: "a copied asset can be structurally fine and semantically
empty").

**Fixed 2026-10-02** by promoting that constant to a `RampStrength` scalar defaulting to
`0.0` — every pre-existing instance renders identically, and the ramp becomes reachable
the moment an artist raises it. `T_Ramp_2Band/3Band/4Band/Smooth` supply the painted path.

## 3. Shadows carry colour, never black

Carried from the Infinity Nikki intake (`UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md`)
and the manifest's own canonical value: `shadow_tint_hex: "#352D40"`, a warm violet.

Applied as a rule in `build_toon_profiles.py`: **no office ramp's darkest stop reaches 0.**
A cel shadow that hits zero reads as a hole punched in the film. The darkest stop is lifted
above black; hue itself lives in the instance `BaseTint`, because ToonProfile ramps are
scalar-valued (`_step4` writes one `Value` into all three colour curves) and cannot carry
per-channel tint.

## 4. What was deliberately *not* ported

Research §4 lists seven adoptions. Three are out of scope for this film and are recorded
here so nobody re-litigates them:

- **Outline lane with velocity (research §4.2).** The film already ships the inverted-hull
  pass (`M_Outline_InvertedHull` + `MI_Outline_{Thin,Heavy}`), and `TOON_SPINE.md` keeps
  outlines separate from the toon shader. The velocity-writing screen-space variant is a
  real improvement but is a second pass, not a fix for anything currently broken.
- **Face shadow / baked normals (§4.3, §4.2).** Character lane. There are no characters in
  `Content/` yet.
- **Adaptive GBuffer tier (§4.6).** Worth +15% cook cost and SM5 fallback. Not for a film
  that renders offline.

## 5. Measurement standard, inherited

The film repo's rule — *assert on the report file, not the log* — came from this lane. Two
concretely applied cases:

- **Probing beats assuming.** `Saved/Audit/toon_surface_probe_v2.json` measured the actual
  `SubstrateToonBSDF` pin surface before the master was edited, which is how the emissive
  lane found a **native `EmissiveColor` pin** and preferred it over `MP_EMISSIVE_COLOR`.
- **Read back, don't assume success.** `build_textures.py` re-reads every imported
  texture's settings into the report, because `srgb`/`filter`/`mip_gen_settings` enum
  member names move between engine builds.

## 6. Open, honestly

- `T_HatchPattern` is referenced by `specs/humber_toon_spine/humber_toon_spine_manifest.v1.json`
  and by Melodia's `specs/toon_profiles/tp_melusina.json`, and **the asset does not exist in
  either repo**. `build_textures.py` now generates it, which closes the dangling reference
  here. Melodia's own copy remains dangling — that is a Melodia-lane item, not ours.
- The office film has no characters, no water and no foliage lanes yet; the corresponding
  research sections stay unported until those exist.