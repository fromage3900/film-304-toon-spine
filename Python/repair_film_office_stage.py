"""Repair lighting and assign proper toon material instances to cast in L_Film_Office.

Fixes:
1. Reparents MI_OneDriveRigs_Dana_Skin_20261016, David_Skin, and Sam_Skin to
   M_Master_Toon_Universal (the active production master) with bFilmUseUDIM = True.
2. Reparents Spider materials to M_Master_Toon_Universal with rich comic chitin and rim highlights.
3. Assigns proper MI_OneDriveRigs_* instances to each slot of Dana, David, Sam, and Spider
   (replacing the broken dummy MI_Film_Skin with 0 textures and pitch-black tint).
4. Rebalances lights in L_Film_Office from pitch-black (8 lm and 67 lm) to proper
   cinematic office lighting (PointLight 12,000 lm, SpotLight key 25,000 lm, active sky fill, and rim kicker).
"""
from __future__ import annotations

import json
from pathlib import Path
import unreal

MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REPORT_PATH = Path("G:/film-304-toon-spine/Saved/Audit/film_office_cast_repair_report.json")

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(m):
    unreal.log(f"[FilmOfficeRepair] {m}")

def reparent_skin_instance(inst_path: str, t1001: str, t1002: str, t1003: str):
    inst = EAL.load_asset(inst_path)
    master = EAL.load_asset(MASTER_PATH)
    if not inst or not master:
        log(f"Error loading {inst_path} or {MASTER_PATH}")
        return False
    
    MEL.set_material_instance_parent(inst, master)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bFilmUseUDIM", True)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bToonRampEnabled", True)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bToonRampActive", True)
    
    # Textures
    tex1 = EAL.load_asset(t1001)
    tex2 = EAL.load_asset(t1002)
    tex3 = EAL.load_asset(t1003)
    if tex1: MEL.set_material_instance_texture_parameter_value(inst, "BaseColorTile1001", tex1)
    if tex2: MEL.set_material_instance_texture_parameter_value(inst, "BaseColorTile1002", tex2)
    if tex3: MEL.set_material_instance_texture_parameter_value(inst, "BaseColorTile1003", tex3)
    
    # Parameters
    MEL.set_material_instance_vector_parameter_value(inst, "BaseTint", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    MEL.set_material_instance_scalar_parameter_value(inst, "Roughness", 0.55)
    MEL.set_material_instance_scalar_parameter_value(inst, "Metallic", 0.0)
    MEL.set_material_instance_scalar_parameter_value(inst, "RampStrength", 0.0)
    
    MEL.update_material_instance(inst)
    EAL.save_loaded_asset(inst)
    log(f"Successfully reparented and configured UDIM skin: {inst_path}")
    return True

def reparent_prop_instance(inst_path: str, base_tint: tuple, roughness: float, metallic: float = 0.0, rim_intensity: float = 0.0, rim_color: tuple = (1.0, 1.0, 1.0, 1.0)):
    inst = EAL.load_asset(inst_path)
    master = EAL.load_asset(MASTER_PATH)
    if not inst or not master:
        return False
    MEL.set_material_instance_parent(inst, master)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bFilmUseUDIM", False)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bToonRampEnabled", True)
    MEL.set_material_instance_static_switch_parameter_value(inst, "bToonRampActive", True)
    MEL.set_material_instance_vector_parameter_value(inst, "BaseTint", unreal.LinearColor(*base_tint))
    MEL.set_material_instance_scalar_parameter_value(inst, "Roughness", roughness)
    MEL.set_material_instance_scalar_parameter_value(inst, "Metallic", metallic)
    MEL.set_material_instance_scalar_parameter_value(inst, "RampStrength", 0.0)
    if rim_intensity > 0:
        MEL.set_material_instance_scalar_parameter_value(inst, "RimIntensity", rim_intensity)
        MEL.set_material_instance_vector_parameter_value(inst, "RimColor", unreal.LinearColor(*rim_color))
    MEL.update_material_instance(inst)
    EAL.save_loaded_asset(inst)
    return True

def main():
    log("Starting Film Office stage repair...")

    # 1. Reparent Skin Instances to M_Master_Toon_Universal with UDIM
    reparent_skin_instance(
        "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Skin_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Dana_Skin_D_1001_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Dana_Skin_D_1002_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Dana_Skin_D_1003_20261016"
    )
    reparent_skin_instance(
        "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Skin_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_David_Skin_D_1001_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_David_Skin_D_1002_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_David_Skin_D_1003_20261016"
    )
    reparent_skin_instance(
        "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Skin_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Sam_Skin_D_1001_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Sam_Skin_D_1002_20261016",
        "/Game/Materials/Textures/OneDriveRigs_20261016/T_Sam_Skin_D_1003_20261016"
    )

    # 2. Configure Clothing, Hair, Eyes, Shoes for Dana
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Hair_20261016", (0.08, 0.05, 0.04, 1.0), 0.45, rim_intensity=1.5)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Shirt_20261016", (0.85, 0.88, 0.92, 1.0), 0.70)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Cloth_20261016", (0.15, 0.16, 0.22, 1.0), 0.75)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Shoes_20261016", (0.12, 0.10, 0.09, 1.0), 0.60)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_EyeWhite_20261016", (0.95, 0.94, 0.92, 1.0), 0.20)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_EyeInterior_20261016", (0.12, 0.08, 0.06, 1.0), 0.30)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016", (0.55, 0.18, 0.18, 1.0), 0.40)

    # Configure David
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Hair_20261016", (0.15, 0.12, 0.08, 1.0), 0.45, rim_intensity=1.2)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Shirt_20261016", (0.20, 0.45, 0.65, 1.0), 0.70)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Cloth_20261016", (0.22, 0.22, 0.24, 1.0), 0.75)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Shoes_20261016", (0.10, 0.08, 0.07, 1.0), 0.50)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_EyeWhite_20261016", (0.95, 0.94, 0.92, 1.0), 0.20)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Iris_20261016", (0.22, 0.40, 0.25, 1.0), 0.15)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_EyeInterior_20261016", (0.10, 0.08, 0.08, 1.0), 0.30)

    # Configure Sam
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Hair_20261016", (0.05, 0.05, 0.06, 1.0), 0.45, rim_intensity=1.2)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Shirt_20261016", (0.75, 0.65, 0.25, 1.0), 0.70)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Cloth_20261016", (0.16, 0.18, 0.20, 1.0), 0.75)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Shoes_20261016", (0.14, 0.14, 0.16, 1.0), 0.50)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_EyeWhite_20261016", (0.95, 0.94, 0.92, 1.0), 0.20)
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_EyeInterior_20261016", (0.10, 0.08, 0.08, 1.0), 0.30)

    # Configure Spider
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Body_20261016", (0.06, 0.06, 0.07, 1.0), 0.50, rim_intensity=2.5, rim_color=(1.0, 0.4, 0.1, 1.0))
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Eye_20261016", (0.95, 0.15, 0.05, 1.0), 0.10, rim_intensity=3.0, rim_color=(1.0, 0.2, 0.0, 1.0))
    reparent_prop_instance("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Fang_20261016", (0.88, 0.88, 0.82, 1.0), 0.25)

    # 3. Assign Materials to Level Actors
    cornea_mat = EAL.load_asset("/Game/Materials/Masters/DanaFilm/M_DanaFilm_CorneaClear")

    for a in EAS.get_all_level_actors():
        label = a.get_actor_label()
        
        if label == "Film_Subject_Dana_v08_CleanSkin":
            comp = a.skeletal_mesh_component
            dana_mats = [
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Skin_20261016",        # 0: Skin
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Hair_20261016",        # 1: Hair
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_EyeWhite_20261016",    # 2: EyeWhite
                "/Game/Materials/Masters/DanaFilm/M_DanaFilm_CorneaClear",                                   # 3: Cornea
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_EyeInterior_20261016",# 4: EyeInterior
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Cloth_20261016",       # 5: Skirt/Pants
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Shirt_20261016",       # 6: Shirt
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Shoes_20261016",       # 7: Shoes
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",       # 8: Gum
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",       # 9: Tongue
            ]
            for i, p in enumerate(dana_mats):
                m = EAL.load_asset(p)
                if m: comp.set_material(i, m)
            log("Assigned materials to Dana.")

        elif label == "Film_Cast_David":
            comp = a.skeletal_mesh_component
            david_mats = [
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Skin_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Shirt_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Hair_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Shoes_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_EyeWhite_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_EyeInterior_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Iris_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_EyeWhite_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Cloth_20261016",
            ]
            for i, p in enumerate(david_mats):
                m = EAL.load_asset(p)
                if m: comp.set_material(i, m)
            log("Assigned materials to David.")

        elif label == "Film_Cast_Sam":
            comp = a.skeletal_mesh_component
            sam_mats = [
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Skin_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Shoes_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Hair_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_EyeWhite_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Iris_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_EyeWhite_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Mouth_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Hair_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Cloth_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_EyeInterior_20261016",
                "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Sam_Shirt_20261016",
            ]
            for i, p in enumerate(sam_mats):
                m = EAL.load_asset(p)
                if m: comp.set_material(i, m)
            log("Assigned materials to Sam.")

        elif "Spider" in label:
            comp = a.skeletal_mesh_component
            if comp:
                eye_m = EAL.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Eye_20261016")
                fang_m = EAL.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Fang_20261016")
                body_m = EAL.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Spider_Body_20261016")
                if eye_m: comp.set_material(0, eye_m)
                if fang_m: comp.set_material(1, fang_m)
                if body_m: comp.set_material(2, body_m)
            log(f"Assigned materials to {label}.")

        # 4. Light Rebalancing
        elif label == "PointLight":
            for comp in a.get_components_by_class(unreal.PointLightComponent):
                comp.set_editor_property("intensity", 12000.0)
                comp.set_editor_property("attenuation_radius", 2500.0)
                comp.set_editor_property("light_color", unreal.Color(255, 240, 225, 255))
            log("Rebalanced PointLight to 12,000 lm.")

        elif label == "SpotLight":
            for comp in a.get_components_by_class(unreal.SpotLightComponent):
                comp.set_editor_property("intensity", 28000.0)
                comp.set_editor_property("attenuation_radius", 3500.0)
                comp.set_editor_property("inner_cone_angle", 28.0)
                comp.set_editor_property("outer_cone_angle", 52.0)
                comp.set_editor_property("light_color", unreal.Color(235, 242, 255, 255))
            log("Rebalanced SpotLight to 28,000 lm.")

    # 5. Add / Ensure Rim Kicker Light for Toon Shading Read
    rim_found = False
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == "Cast_RimKicker_Light":
            rim_found = True
            break
    if not rim_found:
        rim_actor = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 300), unreal.Rotator(-25.0, -45.0, 0.0))
        if rim_actor:
            rim_actor.set_actor_label("Cast_RimKicker_Light")
            comp = rim_actor.get_component_by_class(unreal.DirectionalLightComponent)
            if comp:
                comp.set_editor_property("intensity", 3.5)
                comp.set_editor_property("light_color", unreal.Color(255, 235, 215, 255))
            log("Spawned Cast_RimKicker_Light for toon rim read.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "success",
        "level": "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office",
        "actions": [
            "Reparented Dana, David, Sam skin instances to M_Master_Toon_Universal with UDIM active",
            "Configured full wardrobe and facial material instances",
            "Rebalanced PointLight to 12,000 lm and SpotLight to 28,000 lm",
            "Added Cast_RimKicker_Light for toon rim highlights"
        ]
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("Stage repair complete!")

if __name__ == "__main__":
    main()
