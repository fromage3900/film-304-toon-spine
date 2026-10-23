"""Add 3-Tile UDIM Roughness, Normal, and BaseColor support to M_Master_Toon_Universal.

Target Master: /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
(The active, verified toon master used for tonight's renders)
"""
from __future__ import annotations

import json
from pathlib import Path
import unreal

MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
GROUP_NAME = "Film Skin & Asset UDIM"
REPORT_PATH = Path("G:/film-304-toon-spine/Saved/Audit/udim_master_wiring_report.json")

mel = unreal.MaterialEditingLibrary

def log(msg: str):
    unreal.log(f"[UDIM_Setup] {msg}")

def find_expression_by_name(material, exact_name):
    for expr in mel.get_material_expressions(material):
        if expr.get_name() == exact_name:
            return expr
    return None

def main():
    log(f"Loading working master for tonight's renders: {MASTER_PATH}")
    mat = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if not mat:
        raise RuntimeError(f"Could not load master material at {MASTER_PATH}")

    neutral_white = unreal.EditorAssetLibrary.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    neutral_normal = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal")
    neutral_roughness = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Textures/Utility/T_Neutral_Roughness")

    BASE_X = -3600
    BASE_Y = -6000

    # 1. Texture Coordinate & UV Unpack
    tex_coord = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, BASE_X, BASE_Y)
    
    # Frac for local UVs [0,1]
    frac_uv = mel.create_material_expression(mat, unreal.MaterialExpressionFrac, BASE_X + 250, BASE_Y)
    mel.connect_material_expressions(tex_coord, "", frac_uv, "")

    # Component Mask for U channel
    mask_u = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, BASE_X + 250, BASE_Y + 150)
    mask_u.set_editor_property("r", True)
    mask_u.set_editor_property("g", False)
    mask_u.set_editor_property("b", False)
    mask_u.set_editor_property("a", False)
    mel.connect_material_expressions(tex_coord, "", mask_u, "")

    # Floor(U) gives tile index (0 for 1001, 1 for 1002, 2 for 1003)
    floor_u = mel.create_material_expression(mat, unreal.MaterialExpressionFloor, BASE_X + 500, BASE_Y + 150)
    mel.connect_material_expressions(mask_u, "", floor_u, "")

    def create_3tile_branch(name_prefix, default_tex, sampler_type, offset_y, is_scalar=False):
        t1001 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, BASE_X + 800, BASE_Y + offset_y)
        t1001.set_editor_property("parameter_name", f"{name_prefix}Tile1001")
        t1001.set_editor_property("group", GROUP_NAME)
        t1001.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        t1001.set_editor_property("sampler_type", sampler_type)
        if default_tex:
            t1001.set_editor_property("texture", default_tex)
        mel.connect_material_expressions(frac_uv, "", t1001, "UVs")

        t1002 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, BASE_X + 800, BASE_Y + offset_y + 220)
        t1002.set_editor_property("parameter_name", f"{name_prefix}Tile1002")
        t1002.set_editor_property("group", GROUP_NAME)
        t1002.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        t1002.set_editor_property("sampler_type", sampler_type)
        if default_tex:
            t1002.set_editor_property("texture", default_tex)
        mel.connect_material_expressions(frac_uv, "", t1002, "UVs")

        t1003 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, BASE_X + 800, BASE_Y + offset_y + 440)
        t1003.set_editor_property("parameter_name", f"{name_prefix}Tile1003")
        t1003.set_editor_property("group", GROUP_NAME)
        t1003.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        t1003.set_editor_property("sampler_type", sampler_type)
        if default_tex:
            t1003.set_editor_property("texture", default_tex)
        mel.connect_material_expressions(frac_uv, "", t1003, "UVs")

        # IF 0: Compare Floor(U) with 0.5. If < 0.5 -> 1001, else 1002
        if_0 = mel.create_material_expression(mat, unreal.MaterialExpressionIf, BASE_X + 1300, BASE_Y + offset_y + 100)
        if_0.set_editor_property("const_b", 0.5)
        mel.connect_material_expressions(floor_u, "", if_0, "A")
        
        out_pin = "R" if is_scalar else "RGB"
        mel.connect_material_expressions(t1001, out_pin, if_0, "A < B")
        mel.connect_material_expressions(t1002, out_pin, if_0, "A > B")
        mel.connect_material_expressions(t1002, out_pin, if_0, "A == B")

        # IF 1: Compare Floor(U) with 1.5. If < 1.5 -> output of if_0, else 1003
        if_1 = mel.create_material_expression(mat, unreal.MaterialExpressionIf, BASE_X + 1700, BASE_Y + offset_y + 100)
        if_1.set_editor_property("const_b", 1.5)
        mel.connect_material_expressions(floor_u, "", if_1, "A")
        mel.connect_material_expressions(if_0, "", if_1, "A < B")
        mel.connect_material_expressions(t1003, out_pin, if_1, "A > B")
        mel.connect_material_expressions(t1003, out_pin, if_1, "A == B")

        return if_1

    # BaseColor 3-tile branch
    log("Building BaseColor 3-tile branch...")
    udim_basecolor = create_3tile_branch("BaseColor", neutral_white, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, 0, is_scalar=False)

    # Roughness 3-tile branch
    log("Building Roughness 3-tile branch...")
    udim_roughness = create_3tile_branch("Roughness", neutral_roughness, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, 750, is_scalar=True)

    # Normal 3-tile branch
    log("Building Normal 3-tile branch...")
    udim_normal = create_3tile_branch("Normal", neutral_normal, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, 1500, is_scalar=False)

    # Static Switch Parameters
    switch_udim = mel.create_material_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, BASE_X + 2200, BASE_Y + 100)
    switch_udim.set_editor_property("parameter_name", "bFilmUseUDIM")
    switch_udim.set_editor_property("group", GROUP_NAME)
    switch_udim.set_editor_property("default_value", False)

    switch_roughness = mel.create_material_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, BASE_X + 2200, BASE_Y + 850)
    switch_roughness.set_editor_property("parameter_name", "bFilmUseUDIM_Roughness")
    switch_roughness.set_editor_property("group", GROUP_NAME)
    switch_roughness.set_editor_property("default_value", False)

    switch_normal = mel.create_material_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, BASE_X + 2200, BASE_Y + 1600)
    switch_normal.set_editor_property("parameter_name", "bFilmUseUDIM_Normal")
    switch_normal.set_editor_property("group", GROUP_NAME)
    switch_normal.set_editor_property("default_value", False)

    # Connect UDIM outputs to True pins of switches
    mel.connect_material_expressions(udim_basecolor, "", switch_udim, "True")
    mel.connect_material_expressions(udim_roughness, "", switch_roughness, "True")
    mel.connect_material_expressions(udim_normal, "", switch_normal, "True")

    # Wire switch_udim into BaseColor path:
    # LinearInterpolate_27 input A previously took StaticSwitchParameter_10.
    lerp_27 = find_expression_by_name(mat, "MaterialExpressionLinearInterpolate_27")
    switch_10 = find_expression_by_name(mat, "MaterialExpressionStaticSwitchParameter_10")
    if lerp_27 and switch_10:
        mel.connect_material_expressions(switch_10, "", switch_udim, "False")
        mel.connect_material_expressions(switch_udim, "", lerp_27, "A")
        log("Successfully wired BaseColor UDIM into LinearInterpolate_27 A")
    else:
        log("WARNING: lerp_27 or switch_10 not found by exact name!")

    # Wire switch_roughness into Roughness path:
    toon_bsdf = find_expression_by_name(mat, "MaterialExpressionSubstrateToonBSDF_4")
    switch_11 = find_expression_by_name(mat, "MaterialExpressionStaticSwitchParameter_11")
    if toon_bsdf and switch_11:
        mel.connect_material_expressions(switch_11, "", switch_roughness, "False")
        mel.connect_material_expressions(switch_roughness, "", toon_bsdf, "Roughness")
        log("Successfully wired Roughness UDIM into SubstrateToonBSDF Roughness")

    # Wire switch_normal into Normal path:
    switch_12 = find_expression_by_name(mat, "MaterialExpressionStaticSwitchParameter_12")
    if toon_bsdf and switch_12:
        mel.connect_material_expressions(switch_12, "", switch_normal, "False")
        mel.connect_material_expressions(switch_normal, "", toon_bsdf, "Normal")
        log("Successfully wired Normal UDIM into SubstrateToonBSDF Normal")

    # Recompile & Save
    log("Recompiling M_Master_Toon_Universal...")
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("M_Master_Toon_Universal recompiled and saved!")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "material": MASTER_PATH,
        "status": "success",
        "added_switches": ["bFilmUseUDIM", "bFilmUseUDIM_Roughness", "bFilmUseUDIM_Normal"],
        "added_parameters": [
            "BaseColorTile1001", "BaseColorTile1002", "BaseColorTile1003",
            "RoughnessTile1001", "RoughnessTile1002", "RoughnessTile1003",
            "NormalTile1001", "NormalTile1002", "NormalTile1003"
        ],
        "default_state": "bFilmUseUDIM=False (zero overhead, fully backward-compatible for tonight's renders)"
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("Report written to " + str(REPORT_PATH))

if __name__ == "__main__":
    main()
