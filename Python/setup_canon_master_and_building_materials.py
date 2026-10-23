"""Make M_UniversalToon_Film304_v06 the canon master, create clean film instances, and bind to Brutalist meshes."""
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
OUT_AUDIT = REPO / "Saved" / "Audit" / "canon_master_and_building_materials_report.json"

CANON_MASTER = "/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06"
GLASS_MASTER = "/Game/Materials/Masters/M_Master_Toon_Glass"
INST_FOLDER = "/Game/Materials/Instances/Film304/Environment"
PROFILE_ENV = "/Game/Materials/ToonProfiles/TP_Environment"

ME = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

EAL.make_directory(INST_FOLDER)

canon_master_asset = unreal.load_asset(CANON_MASTER)
if not canon_master_asset:
    raise RuntimeError(f"Could not load canon master: {CANON_MASTER}")

report = {
    "canon_master": CANON_MASTER,
    "created_instances": {},
    "assigned_meshes": {}
}

# 1. Create or update Canon Material Instances under Film304/Environment
def get_or_create_instance(name, parent_asset):
    path = f"{INST_FOLDER}/{name}"
    if EAL.does_asset_exist(path):
        inst = unreal.load_asset(path)
    else:
        inst = AT.create_asset(name, INST_FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    ME.set_material_instance_parent(inst, parent_asset)
    return inst, path

# Instance A: Concrete (Massing)
mi_concrete, path_concrete = get_or_create_instance("MI_Film304_BrutalistConcrete", canon_master_asset)
ME.set_material_instance_scalar_parameter_value(mi_concrete, "RampStrength", 1.0)
ME.set_material_instance_scalar_parameter_value(mi_concrete, "TextureWeight", 0.0)
ME.set_material_instance_scalar_parameter_value(mi_concrete, "Roughness", 0.75)
ME.set_material_instance_scalar_parameter_value(mi_concrete, "Metallic", 0.0)
# Warm-grey architectural concrete tint
ME.set_material_instance_vector_parameter_value(mi_concrete, "BaseTint", unreal.LinearColor(0.55, 0.55, 0.58, 1.0))
# Default non-painted ramp so toon profile is active
try:
    ME.set_material_instance_static_switch_parameter_value(mi_concrete, "bUsePaintedRamp", False)
except Exception:
    pass
ME.update_material_instance(mi_concrete)
EAL.save_loaded_asset(mi_concrete, only_if_is_dirty=False)
report["created_instances"]["MI_Film304_BrutalistConcrete"] = path_concrete

# Instance B: Asphalt / Ground
mi_asphalt, path_asphalt = get_or_create_instance("MI_Film304_BrutalistAsphalt", canon_master_asset)
ME.set_material_instance_scalar_parameter_value(mi_asphalt, "RampStrength", 0.8)
ME.set_material_instance_scalar_parameter_value(mi_asphalt, "TextureWeight", 0.0)
ME.set_material_instance_scalar_parameter_value(mi_asphalt, "Roughness", 0.90)
ME.set_material_instance_scalar_parameter_value(mi_asphalt, "Metallic", 0.0)
# Dark pavement tint
ME.set_material_instance_vector_parameter_value(mi_asphalt, "BaseTint", unreal.LinearColor(0.12, 0.12, 0.13, 1.0))
try:
    ME.set_material_instance_static_switch_parameter_value(mi_asphalt, "bUsePaintedRamp", False)
except Exception:
    pass
ME.update_material_instance(mi_asphalt)
EAL.save_loaded_asset(mi_asphalt, only_if_is_dirty=False)
report["created_instances"]["MI_Film304_BrutalistAsphalt"] = path_asphalt

# Instance C: Glazing / Glass Windows
# We can use either M_Master_Toon_Glass or canon master with high specular/smoothness
glass_parent = unreal.load_asset(GLASS_MASTER) or canon_master_asset
mi_glass, path_glass = get_or_create_instance("MI_Film304_BrutalistGlazing", glass_parent)
ME.set_material_instance_scalar_parameter_value(mi_glass, "RampStrength", 0.9)
ME.set_material_instance_scalar_parameter_value(mi_glass, "Roughness", 0.08)
ME.set_material_instance_scalar_parameter_value(mi_glass, "Metallic", 0.2)
# Dark cyan/navy architectural tint reflecting sky
ME.set_material_instance_vector_parameter_value(mi_glass, "BaseTint", unreal.LinearColor(0.10, 0.18, 0.25, 1.0))
ME.update_material_instance(mi_glass)
EAL.save_loaded_asset(mi_glass, only_if_is_dirty=False)
report["created_instances"]["MI_Film304_BrutalistGlazing"] = path_glass

# Ground/Env uses MI_Film304_BrutalistAsphalt and MI_Film304_BrutalistConcrete directly

# 2. Assign Material Instances to Brutalist Static Mesh Slots
BRUTALIST_MESHES = [
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TightEstate",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_LowSprawl",
    "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster",
    "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_CivicSuperblock",
    "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TightEstate",
    "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_LowSprawl",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_Bunker",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
    "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_CivicColonnade",
    "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_PunchedEstate",
    "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_TowerRibbon",
]

for mesh_path in BRUTALIST_MESHES:
    sm = unreal.load_asset(mesh_path)
    if not sm:
        report["assigned_meshes"][mesh_path] = "FAILED: load error"
        continue
    
    mats = sm.get_editor_property("static_materials")
    slot_assignments = []
    
    for idx, smat in enumerate(mats):
        slot_name_str = str(smat.get_editor_property("material_slot_name"))
        slot_name_lower = slot_name_str.lower()
        
        target_mi = mi_concrete
        if "glaz" in slot_name_lower or "glass" in slot_name_lower or "window" in slot_name_lower:
            target_mi = mi_glass
        elif "asphalt" in slot_name_lower or "ground" in slot_name_lower or "street" in slot_name_lower or "road" in slot_name_lower:
            target_mi = mi_asphalt
        elif "concrete" in slot_name_lower or "massing" in slot_name_lower or "facade" in slot_name_lower or "wall" in slot_name_lower or "material_0" in slot_name_lower:
            target_mi = mi_concrete
            
        sm.set_material(idx, target_mi)
        slot_assignments.append({
            "slot_index": idx,
            "slot_name": slot_name_str,
            "assigned": target_mi.get_path_name()
        })
        
    EAL.save_loaded_asset(sm, only_if_is_dirty=False)
    report["assigned_meshes"][sm.get_name()] = slot_assignments
    unreal.log(f"[CANON_MASTER] Assigned {len(slot_assignments)} slots on {sm.get_name()}")

OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
OUT_AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"[CANON_MASTER] Completed setup and saved audit to {OUT_AUDIT}")
