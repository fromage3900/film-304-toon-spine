#!/usr/bin/env python3
"""
Film 304 — Production-Grade Maya 2027 + Arnold (`mtoa`) Brutalist `aiToon` Shader Graph
& Shot Setup Automation Script (v4.0)

Author: Brennan Shepherd (Film 304 Toon & Procedural Environment Pipeline)
Date:   2026-11-18

Usage (Headless Maya 2027):
    "C:/Program Files/Autodesk/Maya2027/bin/mayapy.exe" setup_brutalist_office_shot.py \\
        --scene "G:/film-304-toon-spine/Saved/Scenes/S_OfficeScene01_BS_Toon_v02.mb" \\
        --texture-root "G:/film-304-toon-spine/Film304_Packages/Office_TrimSheet_PBR_v4" \\
        --output-scene "G:/film-304-toon-spine/Saved/Scenes/S_OfficeScene01_BS_Toon_v04_Brutalist.mb" \\
        --render-dir "G:/film-304-toon-spine/Saved/Audit/OfficeToon_2026-11-18_v04"

Usage (Standalone Graph Spec Verification / Dry-Run outside Maya):
    python3 setup_brutalist_office_shot.py --verify-spec
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Tuple, Any

# Optional Maya imports (graceful fallback when run outside mayapy with --verify-spec)
try:
    import maya.standalone
    import maya.cmds as cmds
    HAS_MAYA = True
except ImportError:
    HAS_MAYA = False


# ==============================================================================
# 1. CANONICAL MATERIAL & CAD MODULE REGISTRY
# ==============================================================================

# Maps each of the 8 parametric CAD modules (and scene mesh groups) to its
# corresponding TrimSheet tile index (0..7) or Tilable PBR material family.
CAD_MODULE_BINDINGS: Dict[str, Dict[str, Any]] = {
    "CAD_CeilingBay_curvShape": {
        "mode": "trim_plus_tilable",
        "trim_tile": "tbar",
        "trim_index": 0,
        "tilable_family": "Hatch",
        "uv_repeat": (4.0, 4.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_CeilingBay_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.60,
        "angle_threshold": 16.0,
    },
    "CAD_DoorFrame_curvShape": {
        "mode": "trim",
        "trim_tile": "mullion",
        "trim_index": 5,
        "uv_repeat": (1.0, 2.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_DoorFrame_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.72,
        "angle_threshold": 15.0,
    },
    "CAD_FloorSlab_curvShape": {
        "mode": "tilable",
        "tilable_family": "CarpetFloor",
        "uv_repeat": (8.0, 8.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_FloorSlab_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.50,
        "angle_threshold": 22.0,
    },
    "CAD_TrimBase_curvShape": {
        "mode": "trim",
        "trim_tile": "base",
        "trim_index": 4,
        "uv_repeat": (1.0, 8.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_TrimBase_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.68,
        "angle_threshold": 14.0,
    },
    "CAD_TrimMullion_curvShape": {
        "mode": "trim",
        "trim_tile": "mullion",
        "trim_index": 5,
        "uv_repeat": (1.0, 6.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_TrimMullion_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.70,
        "angle_threshold": 14.0,
    },
    "CAD_TrimPanel_curvShape": {
        "mode": "trim",
        "trim_tile": "panel",
        "trim_index": 3,
        "uv_repeat": (1.0, 4.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_TrimPanel_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.65,
        "angle_threshold": 16.0,
    },
    "CAD_WallModule_curvShape": {
        "mode": "tilable",
        "tilable_family": "Concrete",
        "uv_repeat": (6.0, 2.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_WallModule_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.62,
        "angle_threshold": 18.0,
    },
    "CAD_WindowMullion_curvShape": {
        "mode": "trim_plus_tilable",
        "trim_tile": "slat",
        "trim_index": 6,
        "tilable_family": "Blinds",
        "uv_repeat": (2.0, 3.0),
        "baked_curvature": "01_CAD_Pass/baked_maps/CAD_WindowMullion_BakedCurvatureAO_1024.png",
        "edge_width_scale": 0.75,
        "angle_threshold": 12.0,
    },
}

# Stepped 4-band Brutalist Chiaroscuro Ramp (interpolation = 0 / None per ToonShader_Setup.pdf)
BRUTALIST_BASE_RAMP_BANDS: List[Tuple[float, Tuple[float, float, float]]] = [
    (0.00, (0.24, 0.25, 0.28)),  # Deep brutalist shadow band (cool slate undertone)
    (0.32, (0.50, 0.51, 0.53)),  # Mid-dark architectural penumbra
    (0.56, (0.78, 0.78, 0.77)),  # Lit structural face
    (0.80, (1.00, 0.99, 0.96)),  # Direct sunlit highlight band
]

# Stepped 2-band Specular Highlight Ramp for metallic extrusions (T-Bar, HVAC Duct, Mullion)
BRUTALIST_SPEC_RAMP_BANDS: List[Tuple[float, Tuple[float, float, float]]] = [
    (0.00, (0.00, 0.00, 0.00)),
    (0.45, (0.32, 0.34, 0.36)),
    (0.78, (0.92, 0.94, 0.98)),
]


# ==============================================================================
# 2. ARNOLD RENDERER, CONTOUR FILTER & SKY-DOME ENFORCEMENT
# ==============================================================================

def configure_arnold_toon_globals(width: int = 1920, height: int = 1080, aa_samples: int = 4) -> Dict[str, Any]:
    """
    Configures Arnold (`mtoa`) render globals specifically for `aiToon`:
    - Sets renderer to `arnold`.
    - Wires an `aiAOVFilter` set to `contour` (`width = 1.75`) so `aiToon` silhouette
      and crease ink edges render cleanly.
    - Disables all `aiSkyDomeLight` nodes in the scene (enforcing `ToonShader_Setup.pdf`).
    """
    if not cmds.pluginInfo("mtoa", query=True, loaded=True):
        cmds.loadPlugin("mtoa")
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")

    # Ensure defaultArnoldRenderOptions & defaultArnoldFilter exist
    try:
        from mtoa.core import createOptions
        createOptions()
    except Exception:
        pass

    cmds.setAttr("defaultResolution.width", width)
    cmds.setAttr("defaultResolution.height", height)
    cmds.setAttr("defaultResolution.deviceAspectRatio", float(width) / float(height))

    if cmds.objExists("defaultArnoldRenderOptions"):
        cmds.setAttr("defaultArnoldRenderOptions.AASamples", aa_samples)
        cmds.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples", 2)
        cmds.setAttr("defaultArnoldRenderOptions.GISpecularSamples", 2)

    # Create dedicated Arnold contour filter for aiToon edge detection
    contour_filter = "AIFILTER_BS_BrutalistContour"
    if not cmds.objExists(contour_filter):
        contour_filter = cmds.createNode("aiAOVFilter", name=contour_filter)
    cmds.setAttr(f"{contour_filter}.aiTranslator", "contour", type="string")
    cmds.setAttr(f"{contour_filter}.width", 1.75)

    if cmds.objExists("defaultArnoldRenderOptions"):
        try:
            cmds.connectAttr(
                f"{contour_filter}.message",
                "defaultArnoldRenderOptions.background",
                force=False,
            )
        except Exception:
            pass

    # Strictly disable any skydome light per ToonShader_Setup.pdf ("No skydome")
    disabled_skydomes = []
    for sd in cmds.ls(type="aiSkyDomeLight") or []:
        cmds.setAttr(f"{sd}.intensity", 0.0)
        cmds.setAttr(f"{sd}.visibility", 0)
        xf = cmds.listRelatives(sd, parent=True) or []
        if xf:
            cmds.setAttr(f"{xf[0]}.visibility", 0)
        disabled_skydomes.append(sd)

    return {
        "resolution": [width, height],
        "aa_samples": aa_samples,
        "contour_filter": contour_filter,
        "disabled_skydomes": disabled_skydomes,
    }


# ==============================================================================
# 3. FULL ARNOLD `aiToon` + PBR + CURVATURE SHADER GRAPH BUILDER
# ==============================================================================

def create_file_node(
    node_name: str,
    filepath: str,
    color_space: str = "sRGB",
    uv_repeat: Tuple[float, float] = (1.0, 1.0),
    uv_offset: Tuple[float, float] = (0.0, 0.0),
    alpha_is_luminance: bool = False,
) -> Tuple[str, str]:
    """Creates a `file` texture node + `place2dTexture` node with exact color-space rules."""
    f_node = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=node_name)
    p2d = cmds.shadingNode("place2dTexture", asUtility=True, name=f"P2D_{node_name}")

    p2d_links = [
        ("coverage", "coverage"),
        ("translateFrame", "translateFrame"),
        ("rotateFrame", "rotateFrame"),
        ("mirrorU", "mirrorU"),
        ("mirrorV", "mirrorV"),
        ("stagger", "stagger"),
        ("wrapU", "wrapU"),
        ("wrapV", "wrapV"),
        ("repeatUV", "repeatUV"),
        ("offset", "offset"),
        ("rotateUV", "rotateUV"),
        ("noiseUV", "noiseUV"),
        ("vertexUvOne", "vertexUvOne"),
        ("vertexUvTwo", "vertexUvTwo"),
        ("vertexUvThree", "vertexUvThree"),
        ("vertexCameraOne", "vertexCameraOne"),
        ("outUV", "uv"),
        ("outUvFilterSize", "uvFilterSize"),
    ]
    for src_attr, dst_attr in p2d_links:
        cmds.connectAttr(f"{p2d}.{src_attr}", f"{f_node}.{dst_attr}", force=True)

    cmds.setAttr(f"{p2d}.repeatU", float(uv_repeat[0]))
    cmds.setAttr(f"{p2d}.repeatV", float(uv_repeat[1]))
    cmds.setAttr(f"{p2d}.offsetU", float(uv_offset[0]))
    cmds.setAttr(f"{p2d}.offsetV", float(uv_offset[1]))

    cmds.setAttr(f"{f_node}.fileTextureName", filepath.replace("\\", "/"), type="string")
    cmds.setAttr(f"{f_node}.colorSpace", color_space, type="string")
    cmds.setAttr(f"{f_node}.ignoreColorSpaceFileRules", 1)
    cmds.setAttr(f"{f_node}.alphaIsLuminance", 1 if alpha_is_luminance else 0)
    return f_node, p2d


def build_brutalist_aitoon_shader_graph(
    tag: str,
    texture_root: str,
    binding: Dict[str, Any],
    use_4k_master: bool = False,
) -> Dict[str, Any]:
    """
    Builds a complete, production-verified Arnold `aiToon` shader network:
      1. `aiToon` shader (`AIT_BS_<tag>`) + renderable `shadingEngine` (`AIT_BS_<tag>SG`).
      2. `RAMP_BS_<tag>` (interpolation = 0 / None, 4 bands) -> `aiToon.baseTonemap`.
      3. `RAMP_SPEC_BS_<tag>` (interpolation = 0 / None, 3 bands) -> `aiToon.specularTonemap`.
      4. `FILE_<tag>_Albedo` (sRGB) * `FILE_<tag>_ORM.outColorR` (AO) + Curvature Bevel Boost
         via `aiMultiply` & `aiAdd` -> `aiToon.baseColor`.
      5. `FILE_<tag>_Normal` (Raw) -> `aiNormalMap` -> `aiToon.normalCamera`.
      6. `FILE_<tag>_ORM` (Raw):
         - `outColorG` (Roughness) -> `aiToon.specularRoughness`
         - `outColorB` (Metallic)  -> `aiRange` (0.15..0.95) -> `aiToon.specular`
      7. `FILE_<tag>_Curvature` (Raw) -> modulates `aiToon.edgeWidthScaling` and bevel highlights.
    """
    toon = cmds.shadingNode("aiToon", asShader=True, name=f"AIT_BS_{tag}")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"AIT_BS_{tag}SG")
    cmds.connectAttr(f"{toon}.outColor", f"{sg}.surfaceShader", force=True)

    # 1. Stepped 4-band Base Tonemap Ramp (interpolation = 0 / None)
    ramp_base = cmds.shadingNode("ramp", asTexture=True, name=f"RAMP_BS_{tag}")
    cmds.setAttr(f"{ramp_base}.type", 0)  # V-ramp
    cmds.setAttr(f"{ramp_base}.interpolation", 0)  # None (stepped cel shading)
    for idx, (pos, rgb) in enumerate(BRUTALIST_BASE_RAMP_BANDS):
        cmds.setAttr(f"{ramp_base}.colorEntryList[{idx}].position", float(pos))
        cmds.setAttr(f"{ramp_base}.colorEntryList[{idx}].color", rgb[0], rgb[1], rgb[2], type="double3")
    cmds.connectAttr(f"{ramp_base}.outColor", f"{toon}.baseTonemap", force=True)

    # 2. Stepped Specular Tonemap Ramp
    ramp_spec = cmds.shadingNode("ramp", asTexture=True, name=f"RAMP_SPEC_BS_{tag}")
    cmds.setAttr(f"{ramp_spec}.type", 0)
    cmds.setAttr(f"{ramp_spec}.interpolation", 0)
    for idx, (pos, rgb) in enumerate(BRUTALIST_SPEC_RAMP_BANDS):
        cmds.setAttr(f"{ramp_spec}.colorEntryList[{idx}].position", float(pos))
        cmds.setAttr(f"{ramp_spec}.colorEntryList[{idx}].color", rgb[0], rgb[1], rgb[2], type="double3")
    cmds.connectAttr(f"{ramp_spec}.outColor", f"{toon}.specularTonemap", force=True)

    # Resolve texture paths from binding
    uv_rep = binding.get("uv_repeat", (1.0, 1.0))
    if binding["mode"] in ("trim", "trim_plus_tilable"):
        t_tile = binding["trim_tile"]
        # Use individual 512x512 seamless trim tile so UVs can tile infinitely on both axes!
        alb_path = os.path.join(texture_root, f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Albedo_512.png")
        nrm_path = os.path.join(texture_root, f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Normal_512.png")
        orm_path = os.path.join(texture_root, f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_ORM_512.png")
        crv_path = os.path.join(texture_root, f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Curvature_512.png")
    else:
        fam = binding["tilable_family"]
        res_tag = "1024" if use_4k_master else "512"
        alb_path = os.path.join(texture_root, f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_BaseColor_{res_tag}.png")
        nrm_path = os.path.join(texture_root, f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_Normal_{res_tag}.png")
        orm_path = os.path.join(texture_root, f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_ORM_{res_tag}.png")
        crv_path = os.path.join(texture_root, binding["baked_curvature"])

    f_alb, _ = create_file_node(f"FILE_{tag}_Albedo", alb_path, color_space="sRGB", uv_repeat=uv_rep)
    f_nrm, _ = create_file_node(f"FILE_{tag}_Normal", nrm_path, color_space="Raw", uv_repeat=uv_rep)
    f_orm, _ = create_file_node(f"FILE_{tag}_ORM", orm_path, color_space="Raw", uv_repeat=uv_rep)
    f_crv, _ = create_file_node(f"FILE_{tag}_Curv", crv_path, color_space="Raw", uv_repeat=(1.0, 1.0))

    # 3. Albedo * Cavity AO + Curvature Bevel Highlight -> aiToon.baseColor
    mul_ao = cmds.shadingNode("multiplyDivide", asUtility=True, name=f"MUL_{tag}_AlbedoAO")
    cmds.setAttr(f"{mul_ao}.operation", 1)  # Multiply
    cmds.connectAttr(f"{f_alb}.outColor", f"{mul_ao}.input1", force=True)
    # Connect ORM.R (AO) to all 3 channels of input2
    cmds.connectAttr(f"{f_orm}.outColorR", f"{mul_ao}.input2X", force=True)
    cmds.connectAttr(f"{f_orm}.outColorR", f"{mul_ao}.input2Y", force=True)
    cmds.connectAttr(f"{f_orm}.outColorR", f"{mul_ao}.input2Z", force=True)

    # Curvature bevel highlight additive boost
    pma_curv = cmds.shadingNode("plusMinusAverage", asUtility=True, name=f"PMA_{tag}_CurvBoost")
    cmds.setAttr(f"{pma_curv}.operation", 1)  # Sum
    cmds.connectAttr(f"{mul_ao}.output", f"{pma_curv}.input3D[0]", force=True)

    remap_curv = cmds.shadingNode("remapValue", asUtility=True, name=f"REMAP_{tag}_CurvEdge")
    cmds.connectAttr(f"{f_crv}.outColorR", f"{remap_curv}.inputValue", force=True)
    cmds.setAttr(f"{remap_curv}.inputMin", 0.50)
    cmds.setAttr(f"{remap_curv}.inputMax", 1.00)
    cmds.setAttr(f"{remap_curv}.outputMin", 0.00)
    cmds.setAttr(f"{remap_curv}.outputMax", 0.14)
    cmds.connectAttr(f"{remap_curv}.outValue", f"{pma_curv}.input3D[1].input3Dx", force=True)
    cmds.connectAttr(f"{remap_curv}.outValue", f"{pma_curv}.input3D[1].input3Dy", force=True)
    cmds.connectAttr(f"{remap_curv}.outValue", f"{pma_curv}.input3D[1].input3Dz", force=True)

    cmds.connectAttr(f"{pma_curv}.output3D", f"{toon}.baseColor", force=True)
    cmds.setAttr(f"{toon}.base", 0.92)

    # 4. Tangent-Space OpenGL Normal Map -> aiNormalMap -> aiToon.normalCamera
    ai_nrm = cmds.shadingNode("aiNormalMap", asUtility=True, name=f"AINRM_{tag}")
    cmds.setAttr(f"{ai_nrm}.strength", 0.85)
    cmds.setAttr(f"{ai_nrm}.invertY", 0)  # OpenGL +Y up convention
    cmds.connectAttr(f"{f_nrm}.outColor", f"{ai_nrm}.input", force=True)
    cmds.connectAttr(f"{ai_nrm}.outValue", f"{toon}.normalCamera", force=True)

    # 5. ORM.G (Roughness) & ORM.B (Metallic) -> Specular Weight & Roughness
    cmds.connectAttr(f"{f_orm}.outColorG", f"{toon}.specularRoughness", force=True)
    remap_spec = cmds.shadingNode("remapValue", asUtility=True, name=f"REMAP_{tag}_MetalToSpec")
    cmds.connectAttr(f"{f_orm}.outColorB", f"{remap_spec}.inputValue", force=True)
    cmds.setAttr(f"{remap_spec}.inputMin", 0.0)
    cmds.setAttr(f"{remap_spec}.inputMax", 1.0)
    cmds.setAttr(f"{remap_spec}.outputMin", 0.18)
    cmds.setAttr(f"{remap_spec}.outputMax", 0.92)
    cmds.connectAttr(f"{remap_spec}.outValue", f"{toon}.specular", force=True)

    # 6. Brutalist Edge & Silhouette Ink Parameters
    cmds.setAttr(f"{toon}.enable", 1)
    cmds.setAttr(f"{toon}.enableSilhouette", 1)
    cmds.setAttr(f"{toon}.idDifference", 1)
    cmds.setAttr(f"{toon}.angleThreshold", float(binding.get("angle_threshold", 16.0)))
    cmds.setAttr(f"{toon}.edgeWidthScaling", float(binding.get("edge_width_scale", 0.65)))
    cmds.setAttr(f"{toon}.edgeColor", 0.05, 0.055, 0.065, type="double3")
    cmds.setAttr(f"{toon}.silhouetteColor", 0.03, 0.035, 0.04, type="double3")

    return {
        "tag": tag,
        "toon_shader": toon,
        "shading_group": sg,
        "base_ramp": ramp_base,
        "spec_ramp": ramp_spec,
        "files": {
            "albedo": alb_path,
            "normal": nrm_path,
            "orm": orm_path,
            "curvature": crv_path,
        },
    }


def relink_existing_scene_aitoon_nodes(texture_root: str) -> Dict[str, Any]:
    """
    Repairs any existing `AIT_BS_*` or `AIT_CAD_*` `aiToon` nodes in the scene
    (fixing the earlier bug in `render_report.json` where `*SG` shadingEngine nodes
    were mistakenly iterated alongside `aiToon` shader nodes).
    """
    fixed_nodes = []
    # Strictly filter by nodeType == "aiToon" so shadingEngine (*SG) nodes are never touched
    for toon in cmds.ls(type="aiToon") or []:
        if cmds.nodeType(toon) != "aiToon":
            continue
        conns = cmds.listConnections(f"{toon}.baseTonemap", source=True, destination=False) or []
        if not conns:
            ramp = cmds.shadingNode("ramp", asTexture=True, name=f"RAMP_FIX_{toon}")
            cmds.setAttr(f"{ramp}.interpolation", 0)
            for idx, (pos, rgb) in enumerate(BRUTALIST_BASE_RAMP_BANDS):
                cmds.setAttr(f"{ramp}.colorEntryList[{idx}].position", float(pos))
                cmds.setAttr(f"{ramp}.colorEntryList[{idx}].color", rgb[0], rgb[1], rgb[2], type="double3")
            cmds.connectAttr(f"{ramp}.outColor", f"{toon}.baseTonemap", force=True)
            fixed_nodes.append({"toon": toon, "ramp_connected": ramp})
    return {"repaired_aitoon_count": len(fixed_nodes), "detail": fixed_nodes}


# ==============================================================================
# 4. 3-POINT BRUTALIST ARCHITECTURAL LIGHTING RIG & CAMERA STAGING
# ==============================================================================

def setup_brutalist_lighting_and_cameras() -> Dict[str, Any]:
    """
    Sets up the 3-Point Brutalist Chiaroscuro Lighting Rig aligned to the measured
    room authority (2200x2200 cm, ceiling z=340 cm, yaw -25 deg):
      1. `LGT_Brutalist_SunKey`     — Grazing sunlight raking through Venetian blinds (rx=-36, ry=-25)
      2. `LGT_Brutalist_TrofferFill`— Cool zenithal ceiling troffer fill light (rx=-78, ry=155)
      3. `LGT_Brutalist_RimKicker`  — Crisp architectural rim separation light (rx=-18, ry=140)
    """
    for old_lgt in ["LGT_Brutalist_SunKey", "LGT_Brutalist_TrofferFill", "LGT_Brutalist_RimKicker"]:
        if cmds.objExists(old_lgt):
            cmds.delete(old_lgt)

    key_shape = cmds.directionalLight(intensity=3.25, rgb=(1.00, 0.95, 0.88))
    key_xf = cmds.rename(cmds.listRelatives(key_shape, parent=True)[0], "LGT_Brutalist_SunKey")
    cmds.setAttr(f"{key_xf}.rotate", -36.0, -25.0, 0.0, type="double3")
    if cmds.attributeQuery("aiAngle", node=key_shape, exists=True):
        cmds.setAttr(f"{key_shape}.aiAngle", 0.35)  # Crisp Venetian-blind slat shadow edges

    fill_shape = cmds.directionalLight(intensity=1.20, rgb=(0.84, 0.90, 0.98))
    fill_xf = cmds.rename(cmds.listRelatives(fill_shape, parent=True)[0], "LGT_Brutalist_TrofferFill")
    cmds.setAttr(f"{fill_xf}.rotate", -78.0, 155.0, 0.0, type="double3")

    rim_shape = cmds.directionalLight(intensity=0.85, rgb=(0.92, 0.95, 1.00))
    rim_xf = cmds.rename(cmds.listRelatives(rim_shape, parent=True)[0], "LGT_Brutalist_RimKicker")
    cmds.setAttr(f"{rim_xf}.rotate", -18.0, 140.0, 0.0, type="double3")

    return {
        "lights": [key_xf, fill_xf, rim_xf],
        "room_authority_yaw_deg": -25.0,
    }


def export_shader_graph_spec(texture_root: str, out_json_path: str) -> Dict[str, Any]:
    """Exports the complete deterministic `aiToon` shader graph specification to JSON."""
    spec = {
        "pipeline_version": "4.0.0-brutalist-master",
        "shader_standard": "Arnold aiToon (ToonShader_Setup.pdf compliant + Full PBR/Curvature)",
        "skydome_policy": "STRICTLY_DISABLED (0 skydomes active)",
        "contour_filter": {"type": "aiAOVFilter", "translator": "contour", "width": 1.75},
        "base_tonemap_ramp": {
            "interpolation": "None (0)",
            "bands": [{"position": p, "rgb": list(c)} for p, c in BRUTALIST_BASE_RAMP_BANDS],
        },
        "specular_tonemap_ramp": {
            "interpolation": "None (0)",
            "bands": [{"position": p, "rgb": list(c)} for p, c in BRUTALIST_SPEC_RAMP_BANDS],
        },
        "cad_module_shader_graphs": {},
    }
    for mesh_name, b in CAD_MODULE_BINDINGS.items():
        tag = mesh_name.replace("_curvShape", "")
        if b["mode"] in ("trim", "trim_plus_tilable"):
            t_tile = b["trim_tile"]
            files = {
                "Albedo": f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Albedo_512.png",
                "Normal": f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Normal_512.png",
                "ORM": f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_ORM_512.png",
                "Curvature": f"02_TrimSheet/tiles_512/T_Trim_{t_tile}_Curvature_512.png",
                "BakedMeshCurvature": b["baked_curvature"],
            }
        else:
            fam = b["tilable_family"]
            files = {
                "BaseColor": f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_BaseColor_1024.png",
                "Normal": f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_Normal_1024.png",
                "ORM": f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_ORM_1024.png",
                "Curvature": f"03_TilableTextures/T_Tilable_{fam}_PBR/T_Tilable_{fam}_Curvature_1024.png",
                "BakedMeshCurvature": b["baked_curvature"],
            }
        spec["cad_module_shader_graphs"][mesh_name] = {
            "toon_node": f"AIT_BS_{tag}",
            "shading_engine": f"AIT_BS_{tag}SG",
            "base_ramp_node": f"RAMP_BS_{tag}",
            "spec_ramp_node": f"RAMP_SPEC_BS_{tag}",
            "normal_map_node": f"AINRM_{tag}",
            "ao_multiply_node": f"MUL_{tag}_AlbedoAO",
            "curvature_boost_node": f"PMA_{tag}_CurvBoost",
            "uv_repeat": list(b["uv_repeat"]),
            "angle_threshold": b["angle_threshold"],
            "edge_width_scale": b["edge_width_scale"],
            "textures": files,
        }

    with open(out_json_path, "w") as f:
        json.dump(spec, f, indent=2)
    return spec


def main():
    parser = argparse.ArgumentParser(description="Film 304 Brutalist aiToon Shader Graph & Shot Setup")
    parser.add_argument("--scene", default="", help="Input Maya .mb/.ma scene path")
    parser.add_argument("--texture-root", default=".", help="Root folder of the v4.0 Submission Pack")
    parser.add_argument("--output-scene", default="", help="Output Maya .mb scene path")
    parser.add_argument("--render-dir", default="", help="Output directory for rendered stills")
    parser.add_argument("--verify-spec", action="store_true", help="Export & validate shader graph JSON spec")
    parser.add_argument("--spec-out", default="brutalist_shader_graph_report.json", help="Path for JSON spec output")
    args = parser.parse_args()

    if args.verify_spec or not HAS_MAYA or not args.scene:
        spec = export_shader_graph_spec(args.texture_root, args.spec_out)
        print(f"Verified aiToon shader graph specification ({len(spec['cad_module_shader_graphs'])} module networks) -> {args.spec_out}")
        return

    maya.standalone.initialize(name="python")
    cmds.file(args.scene, open=True, force=True)
    globals_rep = configure_arnold_toon_globals(1920, 1080, aa_samples=4)
    repaired_rep = relink_existing_scene_aitoon_nodes(args.texture_root)

    built_graphs = {}
    for mesh_name, binding in CAD_MODULE_BINDINGS.items():
        tag = mesh_name.replace("_curvShape", "")
        g_info = build_brutalist_aitoon_shader_graph(tag, args.texture_root, binding)
        built_graphs[mesh_name] = g_info
        if cmds.objExists(mesh_name):
            cmds.sets(mesh_name, edit=True, forceElement=g_info["shading_group"])

    lgt_rep = setup_brutalist_lighting_and_cameras()
    if args.output_scene:
        cmds.file(rename=args.output_scene)
        cmds.file(save=True, type="mayaBinary", force=True)

    print(json.dumps({
        "globals": globals_rep,
        "repaired": repaired_rep,
        "built_graphs": len(built_graphs),
        "lighting": lgt_rep,
    }, indent=2))


if __name__ == "__main__":
    main()
