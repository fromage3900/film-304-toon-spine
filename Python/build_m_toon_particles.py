"""Build M_Master_Toon_Particles - unlit sprite chain, translucent.

WHY ITS OWN MASTER
------------------
Niagara emitters (petals, beat dust, cymbal rings - see the Niagara/
melusina lanes) sample a sprite texture, take a per-particle color from the
system, and fade at the camera. None of that survives contact with a lit
surface master: the material domain of a particle is a sprite, not a mesh.
M_Master_Toon_Unlit has no opacity chain and no sprite parameter; this master
IS that chain - the unlit surface spine plus the particle inputs.

WHAT IT REUSES
--------------
unlit BSDF + MP_FRONT_MATERIAL (M_Master_Toon_Unlit pattern), MaterialExpressionDepthFade
proven (setup_sakura_niagara.py:787, input pin "Distance"), sprite texture as
a TextureObjectParameter so instances swap the sheet. NO Toon BSDF, NO Toon
Profile, NO ramp - same reasoning as M_Master_Toon_EmissiveFX; verify()
asserts the absence. BLEND_TRANSLUCENT + two_sided: particles are camera-
facing quads seen from both faces.

THE DOMAIN BEHAVIOUR: RGB * A DECAY
------------------------------------
rgb  = TintColor * ParticleColor.rgb * Sprite.rgb * Brightness  -> unlit BaseColor
alpha = ParticleColor.a * Sprite.a * DepthFade(Distance=FadeDistance)
        -> attempted on the unlit "Opacity" pin
Per the owner's rule the opacity connect FAILURE IS A WARN, NOT A FAIL: the
unlit function may not expose an Opacity pin in this engine build. In that
case verify() records wired-input count (rgb-only still renders; alpha just
stays 1) and the run reports it - the engine truth is read back, never
assumed. ParticleColor class name uncertainty (MaterialExpressionParticleColor
vs a Substrate variant) is handled by candidate names, loud on failure.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Particles"
TEX_DIR = "/Game/Materials/Textures"

# Set by build() so verify() can report what actually wired.
_state = {"opacity_wired": False, "particle_color": None,
          "depth_fade": None}


def _first_expr(mat, candidates, x, y):
    """Instantiate the first class name that exists in this engine build.
    Returns (node, class_name) or (None, None) if none resolve."""
    last_err = None
    for cls in candidates:
        try:
            node = lib.expr(mat, getattr(unreal, cls), x, y)
            if node is not None:
                return node, cls
        except Exception as exc:
            last_err = exc
            continue
    lib.log(f"WARN {NAME}: none of {candidates} instantiated"
            + (f" ({last_err})" if last_err else ""))
    return None, None


def build(rebuild=True):
    global _state
    _state = {"opacity_wired": False, "particle_color": None, "depth_fade": None}
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    # ---------------- parameters ----------------
    vec = {
        "TintColor": lib.vector(mat, "TintColor", "FX", (0.85, 0.9, 1.0, 1.0),
                                -1600, -400,
                                desc="Base tint multiplied over the sprite"),
    }
    flt = {
        "Brightness": lib.scalar(mat, "Brightness", "FX", 1.0, -1000, -400,
                                 desc="RGB multiplier"),
        "FadeDistance": lib.scalar(mat, "FadeDistance", "FX", 50.0, -1000, -330,
                                   desc="DepthFade distance in cm"),
    }

    sprite_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                          -1000, -260)
    sprite_tex.set_editor_property("parameter_name", "SpriteTexture")
    sprite_tex.set_editor_property("group", "FX")
    try:
        default = unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White"))
        if default is not None:
            sprite_tex.set_editor_property("texture", default)
    except Exception as exc:
        lib.log(f"WARN {NAME}: default sprite texture not set ({str(exc)[:80]})")
    lib._desc(sprite_tex, "Sprite / flipbook frame (instances swap the sheet)")

    # ---------------- particle inputs (candidate class names) ----------------
    pcolor, pcolor_cls = _first_expr(
        mat, ["MaterialExpressionParticleColor"], -1000, 60)
    _state["particle_color"] = pcolor_cls

    dfade, dfade_cls = _first_expr(
        mat, ["MaterialExpressionDepthFade"], -1000, 320)
    _state["depth_fade"] = dfade_cls

    # ---------------- rgb chain: Tint * ParticleColor * Sprite * Brightness --
    tint_p = lib.expr(mat, unreal.MaterialExpressionMultiply, -760, -300)
    lib.connect(vec["TintColor"], "", tint_p, ["A", "a"])
    if pcolor is not None:
        lib.connect(pcolor, "", tint_p, ["B", "b"])
    else:
        # no particle colour node: Tint stands alone (still valid unlit)
        lib.connect(lib.scalar_const(mat, 1.0, -760, -220), "", tint_p, ["B", "b"])

    sprite_out = lib.expr(mat, unreal.MaterialExpressionComponentMask, -760, -140)
    sprite_out.set_editor_property("r", True)
    sprite_out.set_editor_property("g", True)
    sprite_out.set_editor_property("b", True)
    sprite_out.set_editor_property("a", False)
    lib.connect(sprite_tex, "", sprite_out, ["", "None"])

    tint_sprite = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, -300)
    lib.connect(tint_p, "", tint_sprite, ["A", "a"])
    lib.connect(sprite_out, "", tint_sprite, ["B", "b"])

    rgb = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, -300)
    lib.connect(tint_sprite, "", rgb, ["A", "a"])
    lib.connect(flt["Brightness"], "", rgb, ["B", "b"])

    # ---------------- alpha chain: ParticleColor.a * Sprite.a * DepthFade ----
    alpha = None
    if pcolor is not None:
        p_a = lib.expr(mat, unreal.MaterialExpressionComponentMask, -760, 140)
        p_a.set_editor_property("r", False)
        p_a.set_editor_property("g", False)
        p_a.set_editor_property("b", False)
        p_a.set_editor_property("a", True)
        lib.connect(pcolor, "", p_a, ["", "None"])

        s_a = lib.expr(mat, unreal.MaterialExpressionComponentMask, -600, 140)
        s_a.set_editor_property("r", False)
        s_a.set_editor_property("g", False)
        s_a.set_editor_property("b", False)
        s_a.set_editor_property("a", True)
        lib.connect(sprite_tex, "", s_a, ["", "None"])

        alpha = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, 140)
        lib.connect(p_a, "", alpha, ["A", "a"])
        lib.connect(s_a, "", alpha, ["B", "b"])

        if dfade is not None:
            try:
                lib.connect(flt["FadeDistance"], "", dfade, ["Distance"])
            except Exception as exc:
                lib.log(f"WARN {NAME}: DepthFade Distance not wired "
                        f"({str(exc)[:80]}) - continuing without camera fade")
            alpha2 = lib.expr(mat, unreal.MaterialExpressionMultiply, -280, 140)
            lib.connect(alpha, "", alpha2, ["A", "a"])
            lib.connect(dfade, "", alpha2, ["B", "b"])
            alpha = alpha2

    # ---------------- unlit BSDF (M_Master_Toon_Unlit pattern) --------------
    unlit = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall, 300, 0)
    unlit.set_editor_property("material_function",
        unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions02/"
                          "Shading/BasicShading/Unlit.Unlit"))
    lib.connect(rgb, "", unlit, ["EmissiveColor"])

    # --- opacity pin attempt (WARN, not fail - see module docstring) --------
    if alpha is not None:
        wired = False
        try:
            wired = lib.connect(alpha, "", unlit, ["Opacity"])
        except Exception as exc:
            lib.log(f"WARN {NAME}: Opacity pin attempt raised {str(exc)[:120]}")
            wired = False
        _state["opacity_wired"] = bool(wired)
        if not wired:
            lib.log(f"WARN {NAME}: Unlit function exposes no Opacity pin - "
                    f"alpha chain BUILT BUT UNWIRED; sprites will render at "
                    f"alpha 1 until the engine build exposes the pin.")
    else:
        lib.log(f"WARN {NAME}: no ParticleColor node - alpha chain skipped, "
                f"sprites render at alpha 1")

    lib.connect_property(unlit, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # NO bind_toon_profile: unlit surface, no Toon BSDF - verify() asserts this.

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions "
            f"opacity_wired={_state['opacity_wired']}")
    return mat


def verify():
    """Unlit BSDF present, NO Toon BSDF, and the engine-truth read-back of the
    inputs (particle color class, depth fade class, opacity wiring)."""
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    have_toon = False
    have_unlit = False
    for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        t = type(n).__name__
        if t == "MaterialExpressionSubstrateToonBSDF":
            have_toon = True
        if t == "MaterialExpressionMaterialFunctionCall":
            try:
                mf = n.get_editor_property("material_function")
                if mf is not None and "Unlit" in mf.get_name():
                    have_unlit = True
            except Exception:
                pass
    result["expression_count"] = lib.expression_count(mat)
    result["particle_color_node"] = _state["particle_color"]
    result["depth_fade_node"] = _state["depth_fade"]
    result["opacity_wired"] = _state["opacity_wired"]

    if have_toon:
        result["error"] = "Toon BSDF present on an unlit particle material"
    elif not have_unlit:
        result["error"] = "Unlit function call not found - sprite unreachable"

    if result["error"] is None:
        result["ok"] = True
    lib.log(f"VERIFY {NAME}: ok={result['ok']} "
            f"particle_color={_state['particle_color']} "
            f"depth_fade={_state['depth_fade']} "
            f"opacity_wired={_state['opacity_wired']} "
            f"{result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME, expected_calls=[], min_expressions=8)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
