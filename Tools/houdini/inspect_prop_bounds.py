import unreal

props = [
    ("monitor", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerMonitor_AC_FilmStage_20261016"),
    ("tower", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerTower_AC_FilmStage_20261016"),
    ("keyboard", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Keyboard_KS_FilmStage_20261016"),
    ("mouse", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Mouse_KMP_FilmStage_20261016"),
    ("laptop", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Laptop_KS_FilmStage_20261016"),
    ("phone", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Phone_KS_FilmStage_20261016"),
    ("lamp", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Lamp_EF_FilmStage_20261016"),
    ("bin", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Bin01_SY_FilmStage_20261016"),
    ("frame", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_PictureFrame_AC_FilmStage_20261016"),
    ("pen", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Pen_KMP_FilmStage_20261016"),
    ("sticky", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_StickyNote_PMB_FilmStage_20261016"),
    ("file", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_File_EF_FilmStage_20261016"),
    ("book", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Book_PMB_FilmStage_20261016"),
    ("plant", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016"),
    ("cactus", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Cactus_PMB_FilmStage_20261016"),
    ("succulent", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Succulent_PMB_FilmStage_20261016"),
    ("mug", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016"),
    ("pastry_dome", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_PastryCover_ZMJ_FilmStage_20261016"),
    ("pastry", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Pastry_ZMJ_FilmStage_20261016"),
    ("coffee_bag", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeBag_ZMJ_FilmStage_20261016"),
    ("coffee_tin", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeTin_ZMJ_FilmStage_20261016"),
    ("espresso", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016"),
    ("watercooler", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Watercooler_KS_FilmStage_20261016"),
    ("whiteboard", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Whiteboard_SG_FilmStage_20261016"),
    ("vending", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_VenndingMachine_Osc_FilmStage_20261016"),
    ("printer", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Printer_KS_FilmStage_20261016"),
    ("drawers", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016"),
    ("chair", "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016")
]

for name, path in props:
    mesh = unreal.load_asset(path)
    if mesh:
        box = mesh.get_bounding_box()
        # box.min.z and box.max.z
        print(f"{name:15} | min_z={box.min.z:6.2f} | max_z={box.max.z:6.2f} | height={box.max.z - box.min.z:6.2f}")
    else:
        print(f"{name:15} | NOT FOUND: {path}")
