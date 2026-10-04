# Toon Suite Close-Out - 2026-10-02

## Shipped
- Spine **40/40 checks**, 0 errors, `OVERALL: PASS`. Master `M_Master_Toon_Universal`
  has a verified `TP_Default` bound to its Substrate Toon BSDF.
- **Office set material assignment is now generated, not hand-placed.**
  `Python/build_office_set_materials.py` runs inside `build_spine.py`, so it cannot
  drift. Verified on disk by binary scan of the `.uasset`s.

| Mesh | Before | After |
|---|---|---|
| `SM_OFFICE_{BarbicanScale,CivicSlab,SlenderTower}` | **no material at all** | `MI_Toon_Environment` |
| `SM_CUBICLE_{Canonical,MazeShift,OpenPlan,Swarm}` | `MI_Toon_Environment` | `MI_Toon_Office_Polypropylene` |

Three of the eight office meshes were shipping with `material_interface=None`
and therefore rendered with **nothing at all**. That was the real reason the
office instances looked orphaned.

## Fixed this session: the sun was on the horizon
`unreal.Rotator`'s positional constructor is `(roll, pitch, yaw)`, but the render
spec's `sun_rotation` is `(pitch, yaw, roll)`. The spec value `[-46, 0, 35]` - a
sun 46 degrees above the horizon - was applied as `roll=-46, pitch=0`, i.e. the
sun sat exactly **on** the horizon. Measured live: `{pitch: 0.000000, yaw: 35,
roll: -46}`.

Every up-facing surface therefore got grazing light of effectively zero, and the
200 m ground plane existed specifically so the key-light terminator would make
toon banding readable - so the bug silently defeated the thing it was added for.
The first four stills came out near-black silhouettes and proved nothing about
the materials.

Fixed in `Python/compose_shot_env_level.py` with explicit keyword args, and
applied to the live level by `Saved/Audit/fix_sun_rotation.py`
(after: `{pitch: -46, yaw: 0, roll: 35}`). The before/after is recorded in
`Saved/Audit/sun_fix.json`. SH020 went 280 KB -> 850 KB.

## Visual proof
Four stills in `Saved/Renders/prototypes/`, re-rendered after the light fix:
`COMP_SH010/020/030/070_proto_v01.png`, all 1280x720. Geometry, cast shadows,
terminators, and the generated dither texture on the ground plane all read
correctly. Companion evidence (mesh -> material -> profile, plus shot metadata)
is in `Saved/Audit/toon_office_evidence_2026-10-02.json`.

## Honest limits
- **Toon banding is still not clearly legible.** Lighting is fixed, but most
  building faces read near-black, so band structure and shadow-side value need a
  lookdev pass. These stills are structural proof, not final lookdev sign-off.
- 5 `MI_Toon_Office_*` instances stay unreferenced because their interior
  geometry does not exist yet - prop brief Wave 1 is 1 of 8 builders done.
- All instances share `TP_Default`; `TP_Office_*` remain authored-but-unbound.

## Open owner decisions
1. **Profile strategy** - shared `TP_Default` (recommended), one master per
   family, or manual editor assignment (loses Python reproducibility).
2. **Fork drift** on the vendored `core.py` - resync with approval, or record as
   an accepted baseline.

Not committed or pushed. `verify_all.ps1` is still 7/8, failing only on that
same pre-existing vendored `core.py` drift.