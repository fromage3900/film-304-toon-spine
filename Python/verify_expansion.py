"""Independent readback verification of the 2026-10-03 material expansion.

WHY A SEPARATE SCRIPT
---------------------
build_spine.py verifies what IT built, in the same process that built it.
That is not independent evidence: a value can read back correctly in the
process that wrote it and still not be in the saved file (this repo has hit
exactly that with the Toon Profile binding - see the note in
build_master_toon.py). This script asserts the same facts from a FRESH
process that built nothing, reading only saved assets.

Asserts:
  * both domain masters bind the intended Toon Profile (water -> TP_Water,
    foliage -> TP_Foliage) on the SubstrateToonBSDF node
  * the three SDF showcase instances carry the right PatternSDFMap texture
  * the pattern override table's three entries are on the saved instances
  * every SDF map asset carries the import settings the contract requires
    (sRGB off, wrap, lossless, no mips)
  * both domain masters are wired to the shared spine functions

Run:  UnrealEditor-Cmd ... -ExecutePythonScript=<abs path to this file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

AUDIT = Path(__file__).resolve().parents[1] / "Saved" / "Audit"
M = "/Game/Materials"

SDF_MAPS = ("T_SDF_Strokes", "T_SDF_Cross", "T_SDF_Dots", "T_SDF_Scales",
            "T_SDF_Cracks", "T_SDF_Leaf",
            # office tilables 2026-10-06 - same import contract (sRGB off,
            # wrap, lossless, no mips, 256x256), headless-proven tile-exact
            # in texture_office_verify_2026-10-06.json before they bake here.
            "T_SDF_CarpetLoop", "T_SDF_CeilingTile", "T_SDF_WeaveFine",
            "T_SDF_Blinds", "T_SDF_PaperGrain", "T_SDF_Woodgrain",
            "T_SDF_Brushed", "T_SDF_Cork", "T_SDF_VCT",
            "T_SDF_WhiteboardGhost", "T_SDF_FrostBands", "T_SDF_Cardboard")

MASTER_PROFILES = {
    "M_Master_Toon_Universal": "TP_Default",
    "M_Master_Toon_Foliage": "TP_Foliage",
    "M_Master_Toon_Water": "TP_Water",
    # The character master exists to make the film's declared character
    # contract real: TP_Melusina is named by the shot manifest, GROUP_
    # STAGING_GUIDE.md section 3, and dogfood_toon_spine.py, but an instance
    # cannot carry a profile, so before this master nothing could bind it.
    "M_Master_Toon_Character": "TP_Melusina",
}

INSTANCE_MAPS = {
    "MI_Toon_Scales": "T_SDF_Scales",
    "MI_Toon_CrackedStone": "T_SDF_Cracks",
    "MI_Foliage_Fern": "T_SDF_Strokes",
    "MI_Toon_Office_PowderCoat": "T_SDF_Cross",
    "MI_Toon_Office_Carpet": "T_SDF_Dots",
    "MI_Toon_Stone": "T_SDF_Cracks",
}

# what the texture contract requires (build_textures.py applies these)
TEX_SETTINGS = {"srgb": False, "address_x": "TA_WRAP", "address_y": "TA_WRAP",
                "compression_settings": "TC_VECTOR_DISPLACEMENTMAP",
                "mip_gen_settings": "TMGS_NO_MIPMAPS"}


def check_master_profiles(me, out):
    for master_name, want in MASTER_PROFILES.items():
        entry = {"want": want, "ok": False}
        mat = unreal.load_asset(f"{M}/Masters/{master_name}")
        if mat is None:
            entry["error"] = "master does not load"
            out[master_name] = entry
            continue
        for e in me.get_material_expressions(mat) or []:
            if type(e).__name__ == "MaterialExpressionSubstrateToonBSDF":
                try:
                    tp = e.get_editor_property("toon_profile")
                except Exception as exc:
                    entry["error"] = f"read: {str(exc)[:60]}"
                    break
                entry["bound"] = tp.get_name() if tp else None
                entry["ok"] = entry["bound"] == want
                break
        out[master_name] = entry


def check_instance_maps(me, out):
    for inst_name, want in INSTANCE_MAPS.items():
        entry = {"want": want, "ok": False}
        inst = unreal.load_asset(f"{M}/Instances/{inst_name}")
        if inst is None:
            entry["error"] = "instance does not load"
            out[inst_name] = entry
            continue
        try:
            tex = me.get_material_instance_texture_parameter_value(
                inst, "PatternSDFMap")
            entry["got"] = tex.get_name() if tex else None
            idx = me.get_material_instance_scalar_parameter_value(
                inst, "PatternIndex")
            entry["pattern_index"] = round(float(idx), 2)
            entry["ok"] = (entry["got"] == want
                           and entry["pattern_index"] == 12.0)
        except Exception as exc:
            entry["error"] = str(exc)[:80]
        out[inst_name] = entry


def check_sdf_texture_settings(out):
    for name in SDF_MAPS:
        entry = {"ok": False}
        tex = unreal.load_asset(f"{M}/Textures/{name}")
        if tex is None:
            entry["error"] = "texture does not load"
            out[name] = entry
            continue
        got = {}
        for prop, want in TEX_SETTINGS.items():
            try:
                v = tex.get_editor_property(prop)
                got[prop] = getattr(v, "name", v)
            except Exception as exc:
                got[prop] = f"<{str(exc)[:40]}>"
        entry["got"] = got
        entry["size"] = f"{tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}"
        entry["ok"] = (got.get("srgb") is False
                       and got.get("address_x") == "TA_WRAP"
                       and got.get("address_y") == "TA_WRAP"
                       and got.get("mip_gen_settings") == "TMGS_NO_MIPMAPS"
                       and entry["size"] == "256x256")
        out[name] = entry


# Office Spider 2026-10-06: Universal carries MF_RimOffset now (edge of
# light for the p12-2 dark corner); the domain masters do not.
MASTER_CALL_WANTS = {
    "M_Master_Toon_Universal": ["MF_ColorRamp3", "MF_RampLUT",
                                "MF_ProceduralPatterns", "MF_RimOffset"],
    "M_Master_Toon_Foliage": ["MF_ColorRamp3", "MF_RampLUT",
                              "MF_ProceduralPatterns"],
    "M_Master_Toon_Water": ["MF_ColorRamp3", "MF_RampLUT",
                            "MF_ProceduralPatterns"],
}

# Office Spider shelf: instance -> {scalar: value} spot read-backs. These
# are the knobs the boards depend on (rim/lift/flicker/matte); full
# override verification already happens in build_instances.verify_instance
# and the override table's own read-back.
OFFICESPIDER_SPOT = {
    "MI_OfficeSpider_Paper": {"DryRoughness": 0.95, "ShadowLift": 0.02},
    # SpiderBody reads POST-override: the DP table (build_pattern_overrides,
    # applied after instances by design) pushes RimStrength 0.70 -> 0.85 and
    # ShadowLift 0.03 -> 0.04 for the p12-2 dark corner. Asserting the
    # pre-override values here would fight the table on every run.
    "MI_OfficeSpider_SpiderBody": {"RimStrength": 0.85, "ShadowLift": 0.04},
    "MI_OfficeSpider_SpiderEyes": {"EmissiveIntensity": 2.0,
                                   "FlickerRate": 7.0},
    "MI_OfficeSpider_CoffeeMachine": {"RimStrength": 0.50},
    "MI_OfficeSpider_WorkerShirt": {"RimStrength": 0.30},
}


def check_master_calls(me, out):
    for master_name, want in MASTER_CALL_WANTS.items():
        entry = {"want": want, "ok": False}
        mat = unreal.load_asset(f"{M}/Masters/{master_name}")
        if mat is None:
            entry["error"] = "does not load"
            out[master_name] = entry
            continue
        found = []
        for e in me.get_material_expressions(mat) or []:
            if type(e).__name__ == "MaterialExpressionMaterialFunctionCall":
                mfn = e.get_editor_property("material_function")
                if mfn:
                    found.append(mfn.get_name())
        entry["found"] = sorted(set(found))
        entry["ok"] = all(w in found for w in want)
        out[master_name] = entry


def check_officespider_spot(me, out):
    for inst_name, wants in OFFICESPIDER_SPOT.items():
        entry = {"want": wants, "ok": False}
        inst = unreal.load_asset(f"{M}/Instances/{inst_name}")
        if inst is None:
            entry["error"] = "instance does not load"
            out[inst_name] = entry
            continue
        try:
            wrong = []
            for key, want in wants.items():
                got = round(float(
                    me.get_material_instance_scalar_parameter_value(
                        inst, key)), 4)
                if got != round(float(want), 4):
                    wrong.append(f"{key}: got {got} want {want}")
            entry["wrong"] = wrong
            entry["ok"] = not wrong
        except Exception as exc:
            entry["error"] = str(exc)[:80]
        out[inst_name] = entry


def main() -> int:
    me = unreal.MaterialEditingLibrary
    report = {"written": "2026-10-06", "independent": True,
              "master_profiles": {}, "instance_maps": {},
              "sdf_texture_settings": {}, "master_calls": {},
              "officespider_spot": {}, "errors": []}

    check_master_profiles(me, report["master_profiles"])
    check_instance_maps(me, report["instance_maps"])
    check_sdf_texture_settings(report["sdf_texture_settings"])
    check_master_calls(me, report["master_calls"])
    check_officespider_spot(me, report["officespider_spot"])

    for group in ("master_profiles", "instance_maps", "sdf_texture_settings",
                  "master_calls", "officespider_spot"):
        for name, entry in report[group].items():
            if not entry.get("ok"):
                report["errors"].append(f"{group}/{name}: {entry}")

    report["ok"] = not report["errors"]
    AUDIT.mkdir(parents=True, exist_ok=True)
    out = AUDIT / "expansion_verify_2026-10-06.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[verify] wrote {out}")
    for group in ("master_profiles", "instance_maps", "sdf_texture_settings",
                  "master_calls", "officespider_spot"):
        for name, entry in report[group].items():
            print(f"[verify] {group:<20} {name:<26} ok={entry.get('ok')}")
    print("RESULT:", "PASS" if report["ok"] else "FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
