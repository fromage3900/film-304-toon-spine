import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. HIDE SAM ENTIRELY — No more broken zombie pose!
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        a.set_actor_hidden_in_game(True)
        # Also move far out of frame just to be 1000% certain
        a.set_actor_location(unreal.Vector(5000.0, 5000.0, -1000.0), False, False)
        print("Permanently removed Film_Cast_Sam from frame")
        break

# 2. FIX CRAZY EXPOSURE & HARSH LIGHTING
# A. Tone down the harsh grazing sun kicker from 4.88 to 0.85
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Cast_RimKicker_Light":
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_editor_property("intensity", 0.85)
        if hasattr(c, "specular_scale"):
            c.set_editor_property("specular_scale", 0.15)
        print("Toned down Cast_RimKicker_Light: intensity=0.85, specular=0.15")

# B. Tone down ceiling troffers from 14.0 to 3.5 cd
for a in eas.get_all_level_actors():
    if "Troffer" in a.get_actor_label() and "Light" in a.get_actor_label():
        c = a.get_component_by_class(unreal.LightComponentBase)
        if c:
            c.set_editor_property("intensity", 3.5)
            print(f"Toned down {a.get_actor_label()} to 3.5 cd")

# C. Tone down cavity and fill lights
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Light_Hero_CharacterFill", "Light_Ceiling_Cavity", "SpotLight"]):
        c = a.get_component_by_class(unreal.LightComponentBase)
        if c:
            cur = c.get_editor_property("intensity")
            c.set_editor_property("intensity", cur * 0.35)
            print(f"Dimmed {lbl} from {cur:.1f} to {cur*0.35:.1f}")

# D. Calibrate PPV_StorybookOutline exposure to true cinematic dusk (-1.1 EV)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_StorybookOutline":
        s = a.settings
        s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
        s.set_editor_property("auto_exposure_bias", -1.1)
        s.set_editor_property("auto_exposure_min_brightness", 0.005)
        s.set_editor_property("auto_exposure_max_brightness", 8.0)
        s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
        print("Calibrated PPV_StorybookOutline auto_exposure_bias to -1.1 EV")
        break

# E. Increase floor roughness so it doesn't wash out with mirror specular
floor_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_GroundedFloor_Toon")
if floor_mat:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(floor_mat, "DryRoughness", 0.92)
    print("Set MI_Film304_GroundedFloor_Toon DryRoughness to 0.92")

# Save level state cleanly
unreal.EditorLoadingAndSavingUtils.save_current_level()

# Pilot camera to Shot 1 (Master Ensemble) and take screenshot
cloc = unreal.Vector(250.0, -210.0, 108.0)
crot = unreal.Rotator(pitch=-0.2, yaw=130.5, roll=0.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
res = claireon.slate_screenshot(target="level_viewport", filename="showcase_dusk_moody_master.png", directory=str(OUT))
print("Screenshot result:", res)
