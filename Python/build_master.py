"""Rebuild M_Master_Toon_Universal from scratch in a clean project.

Run in UE 5.8 editor:
  py "<repo>/Python/build_master.py"

This creates the master with Substrate Toon BSDF root, wired to the
extracted MF functions. No MeshBlend, no game-specific dependencies.
"""
from __future__ import annotations

import unreal

import material_lib as lib

MASTER_NAME = "M_Master_Toon_Universal"
FUNCTION_DIR = "/Game/Materials/Functions"
PROFILE_DIR = "/Game/Materials/ToonProfiles"
MASTER_DIR = "/Game/Materials/Masters"


def build_master() -> str:
    lib.ensure_directory(MASTER_DIR)
    path = lib.asset_path(MASTER_DIR, MASTER_NAME)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log(f"[ToonFilm] {path} already exists, skipping")
        return path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        MASTER_NAME, MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not material:
        raise RuntimeError(f"Failed to create {MASTER_NAME}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set_editor_property(material, "bUsesSubstrate", True)

    # --- Parameters (grouped) ---
    base_tint = lib.vector_param(material, "BaseTint", "Palette", (0.55, 0.48, 0.42, 1.0), -1600, -80)
    accent_tint = lib.vector_param(material, "AccentTint", "Palette", (0.72, 0.62, 0.52, 1.0), -1600, 80)
    lib.scalar_param(material, "UVScale", "UV", 1.0, -1600, 220)
    lib.scalar_param(material, "UVRotation", "UV", 0.0, -1600, 320)
    normal_map = lib.texture_param(material, "NormalMap", "Maps", -1600, 420)
    rough_map = lib.texture_param(material, "RoughnessMap", "Maps", -1600, 540)
    height_map = lib.texture_param(material, "HeightMap", "Maps", -1600, 660)
    lib.scalar_param(material, "ParallaxScale", "Parallax", 0.04, -1600, 780)
    lib.scalar_param(material, "ParallaxSteps", "Parallax", 8.0, -1600, 880)
    lib.scalar_param(material, "GildingStrength", "Gilding", 0.0, -1600, 980)
    gold_tint = lib.vector_param(material, "GoldTint", "Gilding", (0.85, 0.65, 0.25, 1.0), -1600, 1080)
    lib.scalar_param(material, "GoldEmissive", "Gilding", 0.0, -1600, 1180)
    lib.scalar_param(material, "OilPaintStrength", "OilPaint", 0.0, -1600, 1280)
    lib.scalar_param(material, "StrokeStrength", "OilPaint", 0.55, -1600, 1380)
    lib.scalar_param(material, "BrushScale", "OilPaint", 0.045, -1600, 1480)
    lib.scalar_param(material, "TemporalStrength", "Temporal", 0.0, -1600, 1580)
    lib.scalar_param(material, "WindSpeed", "Temporal", 0.15, -1600, 1680)
    lib.scalar_param(material, "NoiseScale", "Temporal", 1.5, -1600, 1780)
    lib.scalar_param(material, "SmearStrength", "Temporal", 0.0, -1600, 1880)
    lib.scalar_param(material, "BoilIntensity", "Temporal", 0.0, -1600, 1980)
    lib.scalar_param(material, "InkIntensity", "Ink", 0.0, -1600, 2080)
    ink_color = lib.vector_param(material, "InkColor", "Ink", (0.05, 0.08, 0.15, 1.0), -1600, 2180)
    lib.scalar_param(material, "PoolingStrength", "Ink", 0.5, -1600, 2280)
    lib.scalar_param(material, "Wetness", "Ink", 0.0, -1600, 2380)
    lib.scalar_param(material, "OrnamentStyle", "Ornament", 0.0, -1600, 2480)
    lib.scalar_param(material, "OrnamentScale", "Ornament", 1.0, -1600, 2580)
    lib.scalar_param(material, "CurvatureSensitivity", "Ornament", 2.0, -1600, 2680)
    lib.scalar_param(material, "AudioReactivity", "Audio", 0.0, -1600, 2780)
    lib.scalar_param(material, "BassWeight", "Audio", 1.0, -1600, 2880)
    lib.scalar_param(material, "MidWeight", "Audio", 0.5, -1600, 2980)
    lib.scalar_param(material, "TrebleWeight", "Audio", 0.25, -1600, 3080)
    dry_roughness = lib.scalar_param(material, "DryRoughness", "Surface", 0.78, -1600, 3180)
    wet_roughness = lib.scalar_param(material, "WetRoughness", "Surface", 0.25, -1600, 3280)
    lib.scalar_param(material, "EdgeStrength", "Outline", 1.0, -1600, 3380)

    # --- Graph ---
    # Band mask (SDF-style)
    world = lib.create_expression(material, unreal.MaterialExpressionWorldPosition, -1200, 200)
    mask_xy = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -1020, 200)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")
    band_scale = lib.scalar_param(material, "BandScale", "SDF", 0.035, -1200, 320)
    band_strength = lib.scalar_param(material, "BandStrength", "SDF", 0.12, -1200, 420)
    scale_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -840, 220)
    lib.connect(mask_xy, "", scale_mul, "A")
    lib.connect(band_scale, "", scale_mul, "B")
    sin_n = lib.create_expression(material, unreal.MaterialExpressionSine, -660, 220)
    sin_n.set_editor_property("period", 1.0)
    lib.connect_unary(scale_mul, sin_n)
    abs_n = lib.create_expression(material, unreal.MaterialExpressionAbs, -480, 220)
    lib.connect_unary(sin_n, abs_n)
    band_mask = lib.create_expression(material, unreal.MaterialExpressionMultiply, -300, 220)
    lib.connect(abs_n, "", band_mask, "A")
    lib.connect(band_strength, "", band_mask, "B")

    # Oil paint blend
    stroke_mask = lib.scalar_param(material, "StrokeStrength", "OilPaint", 0.55, -1200, 480)
    oil_blend = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -720, 80)
    lib.connect(base_tint, "", oil_blend, "A")
    lib.connect(accent_tint, "", oil_blend, "B")
    lib.connect(stroke_mask, "", oil_blend, "Alpha")

    oil_mod = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -480, 80)
    lib.connect(base_tint, "", oil_mod, "A")
    lib.connect(oil_blend, "", oil_mod, "B")
    lib.connect(lib.scalar_param(material, "OilPaintStrength", "OilPaint", 0.0, -1200, 580), "", oil_mod, "Alpha")

    # Band lerp
    band_lerp = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -280, 120)
    lib.connect(oil_mod, "", band_lerp, "A")
    lib.connect(accent_tint, "", band_lerp, "B")
    lib.connect(band_mask, "", band_lerp, "Alpha")

    # Gilding
    gild_color = lib.create_expression(material, unreal.MaterialExpressionMultiply, -720, 720)
    lib.connect(lib.scalar_param(material, "GildingStrength", "Gilding", 0.0, -1200, 780), "", gild_color, "A")
    lib.connect(gold_tint, "", gild_color, "B")
    color_gild = lib.create_expression(material, unreal.MaterialExpressionAdd, -80, 120)
    lib.connect(band_lerp, "", color_gild, "A")
    lib.connect(gild_color, "", color_gild, "B")

    # Ink
    ink_mask = lib.scalar_param(material, "InkIntensity", "Ink", 0.0, -1200, 920)
    final_color = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 120, 120)
    lib.connect(color_gild, "", final_color, "A")
    lib.connect(ink_color, "", final_color, "B")
    lib.connect(ink_mask, "", final_color, "Alpha")

    # Temporal
    temporal_mod = lib.scalar_param(material, "TemporalStrength", "Temporal", 0.0, -1200, 1120)
    temporal_vec = lib.create_expression(material, unreal.MaterialExpressionMultiply, 200, 1120)
    lib.connect(temporal_mod, "", temporal_vec, "A")
    const_temp = lib.create_expression(material, unreal.MaterialExpressionConstant3Vector, 0, 1120)
    const_temp.set_editor_property("constant", unreal.LinearColor(0.02, 0.02, 0.03, 1.0))
    lib.connect(const_temp, "", temporal_vec, "B")
    color_temporal = lib.create_expression(material, unreal.MaterialExpressionAdd, 320, 120)
    lib.connect(final_color, "", color_temporal, "A")
    lib.connect(temporal_vec, "", color_temporal, "B")

    # Roughness
    rough_lerp = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 120, 520)
    lib.connect(dry_roughness, "", rough_lerp, "A")
    lib.connect(wet_roughness, "", rough_lerp, "B")
    lib.connect(lib.scalar_param(material, "Wetness", "Ink", 0.0, -1200, 620), "", rough_lerp, "Alpha")

    # Normal
    pixel_normal = lib.create_expression(material, unreal.MaterialExpressionPixelNormalWS, 120, 680)

    # Parallax WPO
    parallax_h = lib.scalar_param(material, "ParallaxHeight", "Parallax", 0.04, -1200, 840)
    height_sample = lib.create_expression(material, unreal.MaterialExpressionMultiply, 120, 840)
    lib.connect(parallax_h, "", height_sample, "A")
    lib.connect(lib.scalar_param(material, "ParallaxScale", "Parallax", 0.04, -1200, 940), "", height_sample, "B")
    vertex_n = lib.create_expression(material, unreal.MaterialExpressionVertexNormalWS, 320, 900)
    wpo = lib.create_expression(material, unreal.MaterialExpressionMultiply, 520, 860)
    lib.connect(height_sample, "", wpo, "A")
    lib.connect(vertex_n, "", wpo, "B")
    unreal.MaterialEditingLibrary.connect_material_property(wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # --- Substrate Toon BSDF ---
    toon_bsdf = lib.create_expression(material, unreal.MaterialExpressionSubstrateToonBSDF, 720, 360)
    lib.connect_toon_pin(toon_bsdf, color_temporal, ("BaseColor", "DiffuseColor"))
    lib.connect_toon_pin(toon_bsdf, rough_lerp, ("Roughness",))
    lib.connect_toon_pin(toon_bsdf, pixel_normal, ("Normal", "TangentNormal", "NormalMap"))
    lib.connect_front_material(material, toon_bsdf)

    unreal.MaterialEditingLibrary.recompile_material(material)
    lib.save_package(material)
    unreal.log(f"[ToonFilm] built {path}")
    return path


if __name__ == "__main__":
    build_master()
