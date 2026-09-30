"""Build MF_OutlineInvertedHull - the ink line, as an overlay material.

WHY A SEPARATE MATERIAL
-----------------------
UE 5.8's Substrate Toon BSDF owns surface shading only. Ink lines are not part
of it. The standard game/animation approach is an inverted-hull overlay on the
skeletal mesh's OverlayMaterial slot: flip normals, push vertices along them,
render unlit black. It sits next to the toon surface and never fights it.

Wiring for the mesh:
    SkeletalMesh -> OverlayMaterial = MI_Outline (parent MF_OutlineInvertedHull)
    Material -> Blend Mode = Masked, Shading Model = Unlit

Because it is unlit, it ignores the Toon Profile entirely - which is what you
want from an ink line.

Thickness here is in world units along the normal, so it holds up under camera
move instead of thinning to nothing. `ThicknessScale` lets a material instance
art-direct per asset.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Outline_InvertedHull"


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, folder=lib.MASTER_DIR, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    # Masked (not Opaque) so the expanded hull keeps its silhouette, and so a
    # texture-driven outline can punch holes for fine detail.
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    except Exception:
        pass
    try:
        mat.set_editor_property("two_sided", False)
    except Exception:
        pass

    ink = lib.vector(mat, "InkColor", "Ink", (0.02, 0.02, 0.04, 1.0), -1200, -200,
                     desc="Line colour")
    thickness = lib.scalar(mat, "Thickness", "Ink", 0.012, -1200, -40,
                          desc="Outline width in world units")
    thickness_scale = lib.scalar(mat, "ThicknessScale", "Ink", 1.0, -1200, 60,
                                 desc="Per-asset thickness multiplier")

    # thickness * scale, clamped so a mis-set instance cannot invert the mesh
    mul = lib.expr(mat, unreal.MaterialExpressionMultiply, -900, 0)
    lib.binary(thickness, thickness_scale, mul)

    clamped = lib.expr(mat, unreal.MaterialExpressionClamp, -720, 0)
    lo = lib.scalar_const(mat, 0.0, -900, 140)
    hi = lib.scalar_const(mat, 0.5, -900, 220)
    lib.unary(mul, clamped)
    lib.connect(lo, "", clamped, ["Min", "min"])
    lib.connect(hi, "", clamped, ["Max", "max"])

    # world-space normal scaled by thickness
    normal = lib.expr(mat, unreal.MaterialExpressionVertexNormalWS, -900, 320)
    offset = lib.expr(mat, unreal.MaterialExpressionMultiply, -540, 120)
    lib.binary(normal, clamped, offset)
    lib.connect_property(offset, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # unlit emissive = ink colour; opacity mask stays white so the hull is solid
    lib.connect_property(ink, unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    opaque_mask = lib.scalar_const(mat, 1.0, -540, -200)
    lib.connect_property(opaque_mask, unreal.MaterialProperty.MP_OPACITY_MASK)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat
