import unreal

task = unreal.AssetImportTask()
task.filename = "G:/film-304-toon-spine/Content/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid.fbx"
task.destination_path = "/Game/Meshes/Architecture"
task.destination_name = "SM_Houdini_Ceiling_HVAC_Grid"
task.replace_existing = True
task.automated = True
task.save = True

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
if mesh:
    num_sec = mesh.get_num_sections(0)
    print(f"Imported successfully! Num sections: {num_sec}")
    for i in range(num_sec):
        mat = mesh.get_material(i)
        print(f"  Slot {i}: {mat.get_name() if mat else 'None'}")
else:
    print("Failed to load imported mesh!")
