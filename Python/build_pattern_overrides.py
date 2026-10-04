"""Build the pattern override table - per-shot hatching without touching art.

WHY THIS EXISTS (TOON_SPINE.md "Next" item 2)
----------------------------------------------
The office set (and the SDF map library) made hatching a per-instance art
decision, which is right for a SURFACE and wrong for a SHOT: the DP wants
the same drywall to hatch differently at 15mm than at 85mm, and instances
are global assets - there is no per-shot instance.

This is the v1 of that table: a manifest of instance -> parameter overrides
that the DP edits as data, applied AFTER build_instances so a spine rebuild
cannot wipe it. Every entry is verified by read-back, so a typo'd parameter
name fails the build instead of silently doing nothing.

SCOPE NOTE
----------
This is instance-level, not runtime: one look per instance per build. True
per-shot material swaps (a different instance per camera) are a level-
composition concern (compose_shot_env_level.py), not this file.

REPOINTING DECISIONS (2026-10-03, the SDF map library's first assignments)
---------------------------------------------------------------------------
The office set's analytic patterns were chosen before baked SDF maps
existed. Where a baked map reads BETTER for the same mark, the instance is
re-pointed at it - PatternIndex 12 + PatternSDFMap - keeping strength and
density where they were already art-directed:
  * PowderCoat: analytic CrossHatch -> T_SDF_Cross (the baked engraving
    sibling: same two-family construction, sine-displaced, soft edges).
  * Carpet:     analytic Stipple    -> T_SDF_Dots  (halftone dots with size
    jitter read as fibres at carpet scale).
  * Stone (film set): analytic none -> T_SDF_Cracks - the cracked-stone
    look was the cracks map's design target.
Everything else keeps its analytic pattern on purpose: the point of the
library is a CHOICE, not a migration.
"""
from __future__ import annotations

import unreal

import spine_lib as lib
import build_instances as instances

TEX_DIR = "/Game/Materials/Textures"

# instance -> parameter overrides (S = scalar, T = texture asset path)
# the DP edits THIS table; nothing here touches surface colour or ink.
OVERRIDES = {
    "MI_Toon_Office_PowderCoat": {
        "PatternIndex": 12.0,                                    # SDFMap
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Cross",
        "PatternScale": 14.0,
    },
    "MI_Toon_Office_Carpet": {
        "PatternIndex": 12.0,                                    # SDFMap
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Dots",
        "PatternScale": 30.0,
    },
    "MI_Toon_Stone": {
        "PatternIndex": 12.0,                                    # SDFMap
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Cracks",
        "PatternScale": 6.0,
        "PatternDensity": 0.50,
    },
}


def build(rebuild=True) -> dict:
    del rebuild  # overrides are idempotent; the table is the rebuild
    lib.log(f"=== Pattern overrides ({len(OVERRIDES)}) ===")
    report = {"applied": {}, "errors": []}

    for name, overrides in OVERRIDES.items():
        inst = unreal.load_asset(
            lib.asset_path(instances.INSTANCE_DIR, name))
        if inst is None:
            report["errors"].append(f"{name}: instance not found")
            continue
        # _apply handles scalar/texture/bool dispatch; profile_name is
        # deliberately None - this table never touches the profile metadata
        instances._apply(inst, None, overrides)
        lib.save(inst)

        # verify by read-back, same rule as build_instances.verify_instance
        me = unreal.MaterialEditingLibrary
        wrong = []
        for key, want in overrides.items():
            try:
                if isinstance(want, str):
                    tex = me.get_material_instance_texture_parameter_value(
                        inst, key)
                    got = tex.get_name() if tex else ""
                    want_name = want.rsplit("/", 1)[-1].split(".")[0]
                else:
                    got = round(float(
                        me.get_material_instance_scalar_parameter_value(
                            inst, key)), 4)
                    want_name = round(float(want), 4)
                if got != want_name:
                    wrong.append(f"{key}: got {got} want {want_name}")
            except Exception as exc:
                wrong.append(f"{key}: {str(exc)[:60]}")
        entry = {"overrides": len(overrides), "ok": not wrong}
        if wrong:
            entry["error"] = "; ".join(wrong[:4])
            report["errors"].append(f"{name}: {entry['error']}")
        report["applied"][name] = entry
        lib.log(f"PATTERN OVERRIDE {name}: ok={entry['ok']} "
                f"{entry.get('error', '')}")

    return report


def main() -> int:
    return 0 if not build()["errors"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
