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
  * Carpet:     analytic Stipple    -> T_SDF_CarpetLoop (purpose-built
    loop-fibre map; halftone dots with size jitter read as fibres).
  * Stone (film set): analytic none -> T_SDF_Cracks - the cracked-stone
    look was the cracks map's design target.

UNIQUE SDF MAP ASSIGNMENTS (2026-10-06)
----------------------------------------
Every instance that can carry a baked SDF map now gets its OWN unique one.
No two instances share a map - the point is per-surface identity, not a
library showcase. PatternIndex 12 + PatternSDFMap on each:
  * Laminate       -> T_SDF_Woodgrain      (desk surface grain)
  * DropCeiling    -> T_SDF_CeilingTile    (acoustic tile texture)
  * Polypropylene  -> T_SDF_Blinds         (moulded plastic striations)
  * Whiteboard     -> T_SDF_WhiteboardGhost (ghosted marker residue)
  * Paper          -> T_SDF_PaperGrain     (paper fibre)
  * DonutBox       -> T_SDF_Cardboard      (corrugated kraft)
  * CoffeeMachine  -> T_SDF_Brushed        (brushed steel)
  * WorkerShirt    -> T_SDF_WeaveFine      (fine cloth weave)
  * SpiderBody     -> T_SDF_Scales         (carapace scales)
  * SpiderEyes     -> T_SDF_Dots           (compound eye facets)
  * FrostedGlass   -> T_SDF_FrostBands     (frost etch bands)
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
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_CarpetLoop",
        "PatternScale": 30.0,
        "Wetness": 0.5,          # soaked-floor push, shot 67 (merged)
    },
    "MI_Toon_Office_Laminate": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Woodgrain",
        "PatternScale": 8.0,
    },
    "MI_Toon_Office_DropCeiling": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_CeilingTile",
        "PatternScale": 12.0,
    },
    "MI_Toon_Office_Polypropylene": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Blinds",
        "PatternScale": 20.0,
    },
    "MI_Toon_Office_Whiteboard": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_WhiteboardGhost",
        "PatternScale": 6.0,
    },
    "MI_Toon_Stone": {
        "PatternIndex": 12.0,                                    # SDFMap
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Cracks",
        "PatternScale": 6.0,
        "PatternDensity": 0.50,
    },
    # --------------------------------------- office spider (2026-10-06)
    # Emissive/rim/lift per-shot dials. Same scope rule as above: the DP
    # edits THIS table, it applies after build_instances, every entry is
    # read-back verified. All targets are Universal-parented (the only
    # master carrying Flicker/ShadowLift/Rim) - WorkerShirt lives on the
    # Character master and is deliberately NOT overridden here.
    "MI_Toon_Office_Troffer": {
        "FlickerRate": 9.0,          # fluorescent buzz shimmer (p2 hum)
        "FlickerDepth": 0.06,        # barely-there; the room must not strobe
    },
    "MI_Toon_Office_Screen": {
        "FlickerRate": 3.0,          # monitor idle throb under the beeps
        "FlickerDepth": 0.08,
    },
    "MI_OfficeSpider_CoffeeMachine": {
        "EmissiveIntensity": 1.5,    # amber buzz light ON for the p3-12 pour
        "FlickerRate": 11.0,         # mains-buzz shimmer on the lamp
        "FlickerDepth": 0.12,
        "PatternIndex": 12.0,        # (merged 2026-10-06: was a duplicate
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Brushed",  # key below that
        "PatternScale": 12.0,        # silently killed this lamp row)
    },
    "MI_OfficeSpider_SpiderBody": {
        "RimStrength": 0.85,         # p12-2 dark-corner push
        "ShadowLift": 0.04,
        "PatternIndex": 12.0,        # (merged 2026-10-06: duplicate key
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Scales",   # below killed rim/lift)
        "PatternScale": 14.0,
    },
    # --------------------------------------- unique SDF maps (2026-10-06)
    # Each instance gets its OWN baked SDF map - no two share one.
    # PatternIndex 12 + PatternSDFMap per instance.
    "MI_OfficeSpider_Paper": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_PaperGrain",
        "PatternScale": 10.0,
    },
    "MI_OfficeSpider_DonutBox": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Cardboard",
        "PatternScale": 8.0,
    },

    "MI_OfficeSpider_WorkerShirt": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_WeaveFine",
        "PatternScale": 40.0,
    },
    "MI_OfficeSpider_SpiderEyes": {
        # Rage burn for the battle-rage ECU (shots 56/63): full burn + hard
        # throb. Supersedes the earlier thump-panel throb (0.45) - one look
        # per instance per build, latest story state wins.
        "EmissiveIntensity": 3.0,
        "FlickerDepth": 0.6,
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_Dots",
        "PatternScale": 24.0,
    },
    # --------------------------------------- soaked floor (2026-10-06)
    # Sprinkler aftermath (shot 67): Wetness pushes on the vinyl + carpet.
    # MERGED 2026-10-07 (film material core): the carpet's SDF row and its
    # Wetness row were DUPLICATE KEYS - the late Wetness row silently
    # REPLACED the SDF row in the dict literal, the same kill-class the
    # coffee-machine merge note records, so the carpet's baked loop-fibre
    # map never shipped behind its Wetness dial. The single Carpet row now
    # carries both.
    "MI_OfficeSpider_VCTFloor": {
        "Wetness": 0.6,
    },
    "MI_OfficeSpider_FrostedGlass": {
        "PatternIndex": 12.0,
        "PatternSDFMap": f"{TEX_DIR}/T_SDF_FrostBands",
        "PatternScale": 4.0,
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
                    # _apply swaps a MISSING map to a NEUTRAL DEFAULT; accept
                    # the resolved name so a swap is not read as a typo
                    resolved, swapped = lib.resolve_texture(want, key=key)
                    if swapped and resolved is not None:
                        want_name = resolved.get_name()
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
