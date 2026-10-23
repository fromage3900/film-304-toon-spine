"""Rebuild the Film 304 establishing stage (E1/E2/E3) in the OPEN level. Idempotent per tag; saves nothing.

    import build_establishing_stage as b
    b.build_e1()            # sky + ground + fog + fill + composer massings + Cam_E1 + outline PPV

Inputs: Saved/GoalEst/e1b_points.json (from Tools/houdini/brutalist_composer/cook_to_json.py, hython).
Look settings are the ones verified by screenshots in Docs/GOAL_ESTABLISHING_SHOTS_20261017.md.
"""
import sys
import unreal

sys.path.insert(0, "G:/film-304-toon-spine/Python")
import place_composer_json as pc
import film304_fog

EL = unreal.EditorLevelLibrary
ORIGIN = (0, 20000, 0)
POINTS = "G:/film-304-toon-spine/Saved/GoalEst/e1b_points.json"
ENV = "/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_"
UDS_BP = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky"
PPV_MI = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/MI_StorybookOutline_Render2026"


def _by_label():
    return {a.get_actor_label(): a for a in EL.get_all_level_actors()}


def _chan(c0, c1):
    ch = unreal.LightingChannels()
    for k, v in (("channel0", c0), ("channel1", c1), ("channel2", False)):
        ch.set_editor_property(k, v)
    return ch


def hv(x, y, z):  # Houdini metres (x, y-up, z) -> UE cm on the stage
    return unreal.Vector(ORIGIN[0] + x * 100, ORIGIN[1] + z * 100, ORIGIN[2] + y * 100)


def ensure_sky(tod=1730.0):
    L = _by_label()
    if "EST_Sky" not in L:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(UDS_BP)
        a = EL.spawn_actor_from_class(cls, unreal.Vector(0, ORIGIN[1], 0))
        a.set_actor_label("EST_Sky")
    else:
        a = L["EST_Sky"]
    import claireon
    claireon.uobject_set_property(object_path=a.get_path_name(), property_path="Time of Day", value=str(tod))
    return a


def ensure_ground():
    L = _by_label()
    g = L.get("EST_Ground") or EL.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(ORIGIN[0], ORIGIN[1], -5))
    g.set_actor_label("EST_Ground")
    g.tags = ["EstablishingE1_Ground"]
    g.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
    g.set_actor_scale3d(unreal.Vector(30000, 30000, 1))
    g.static_mesh_component.set_material(0, unreal.load_asset(ENV + "Asphalt"))
    return g


def ensure_fog():
    L = _by_label()
    fg = L.get("EST_Fog_E1") or EL.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(ORIGIN[0], ORIGIN[1], 0))
    fg.set_actor_label("EST_Fog_E1")
    # Routed through film304_fog so the write carries an explicit intent and a
    # before/after receipt, and so it cannot revert the reviewed extinction scale.
    film304_fog.apply_stage_establishing(
        density=0.0016,
        height_falloff=0.12,
        start_distance=3000.0,
        max_opacity=0.92,
        inscattering_luminance=unreal.LinearColor(0.55, 0.40, 0.30, 1.0),
    )
    return fg


def ensure_fill(intensity=3.0):
    L = _by_label()
    f = L.get("EST_Fill_E1") or EL.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(-1200, 5000, 2600), unreal.Rotator(roll=0, pitch=-12, yaw=90))
    f.set_actor_label("EST_Fill_E1")
    lc = f.get_components_by_class(unreal.DirectionalLightComponent)[0]
    lc.set_editor_property("lighting_channels", _chan(False, True))
    lc.set_editor_property("cast_shadows", False)
    lc.set_editor_property("atmosphere_sun_light", False)
    lc.set_editor_property("intensity", intensity)
    lc.set_editor_property("light_color", unreal.Color(150, 175, 255, 255))
    return f


def ensure_camera():
    L = _by_label()
    loc, tgt = hv(-12, 26, -150), hv(0, 30, 200)
    cam = L.get("Cam_E1") or EL.spawn_actor_from_class(unreal.CineCameraActor, loc)
    cam.set_actor_label("Cam_E1")
    cam.set_actor_location(loc, False, False)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, tgt), False)
    cc = cam.get_cine_camera_component()
    cc.set_editor_property("current_focal_length", 24.0)
    fb = cc.get_editor_property("filmback")
    fb.sensor_width, fb.sensor_height = 35.0, 19.7
    cc.set_editor_property("filmback", fb)
    pp = cc.get_editor_property("post_process_settings")
    pp.set_editor_property("override_vignette_intensity", True)
    pp.set_editor_property("vignette_intensity", 0.55)
    pp.set_editor_property("override_color_gain_shadows", True)
    pp.set_editor_property("color_gain_shadows", unreal.Vector4(0.85, 0.92, 1.15, 1.0))
    cc.set_editor_property("post_process_settings", pp)
    return cam


def ensure_ppv():
    L = _by_label()
    v = L.get("EST_PPV_Ink") or EL.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(ORIGIN[0], ORIGIN[1], 0))
    v.set_actor_label("EST_PPV_Ink")
    v.set_editor_property("unbound", True)
    v.set_editor_property("priority", 100.0)
    s = v.get_editor_property("settings")
    wb = unreal.WeightedBlendable()
    wb.weight = 1.0
    wb.object = unreal.load_asset(PPV_MI)
    s.weighted_blendables = unreal.WeightedBlendables([wb])
    v.set_editor_property("settings", s)
    return v


def apply_e1_materials():
    mats = {k: unreal.load_asset(ENV + k) for k in ("Concrete", "Asphalt", "Glazing")}
    n = 0
    for a in EL.get_all_level_actors():
        if a.get_actor_label().startswith("EST_") and isinstance(a, unreal.StaticMeshActor):
            c = a.static_mesh_component
            c.set_editor_property("lighting_channels", _chan(True, True))
            # map by the mesh's own slot NAME (BR_Glazing / BR_Asphalt* / BR_Concrete*), not by the current instance
            slot_names = [str(s.material_slot_name) for s in c.static_mesh.static_materials]
            for i in range(len(c.get_materials())):
                nm = slot_names[i] if i < len(slot_names) else ""
                key = "Glazing" if "Glaz" in nm else ("Asphalt" if "Asphalt" in nm else "Concrete")
                c.set_material(i, mats[key])
                n += 1
    return n


def build_e1(points=POINTS):
    ensure_sky()
    ensure_ground()
    placed, missing = pc.place(points, origin=ORIGIN, tag="EstablishingE1", yaw_sign=-1)
    ensure_fog()
    ensure_fill()
    ensure_camera()
    ensure_ppv()
    slots = apply_e1_materials()
    return {"placed": len(placed), "missing": missing, "slots": slots}
