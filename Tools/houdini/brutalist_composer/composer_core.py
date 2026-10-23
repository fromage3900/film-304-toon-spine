"""Core camera-driven compositional layout generator for Brutalist architecture, Interior Cubicles, & Breakroom Kits.

Designed under the compositional lens of Columbus College of Art & Design (CCAD):
- Visual Hierarchy & Scale: Endless modular rhythm vs tactile character workspace.
- Architectural Street Grid: Clean orthogonal alignment (0°, 90°, 180°, 270°) - NO random chaotic diagonals.
- Explicit Material Slot Preservation: Multi-slot assets retain asphalt plinths and concrete facades without global flattening.
- All paths use fully-qualified Unreal Engine object notation (Package.Asset).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# -------------------------------------------------------------------------
# Material Instances: Explicitly Mapped Unreal Material Instances (with .Asset dot syntax)
# -------------------------------------------------------------------------
MATERIALS = {
    # Brutalist Architectural Material Instances
    "concrete": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete.MI_Film304_BrutalistConcrete",
    "asphalt": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt.MI_Film304_BrutalistAsphalt",
    "glazing": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing.MI_Film304_BrutalistGlazing",

    # Office Interior Surface Material Instances
    "carpet": "/Game/Materials/Instances/MI_Toon_Office_Carpet.MI_Toon_Office_Carpet",
    "vct": "/Game/Materials/Instances/MI_OfficeSpider_VCTFloor.MI_OfficeSpider_VCTFloor",
    "ceiling": "/Game/Materials/Instances/MI_Toon_Office_DropCeiling.MI_Toon_Office_DropCeiling",
    "wall": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall.MI_Film_Wall",
    "wall_warm": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_WarmWall.MI_Film_WarmWall",
    "frosted_glass": "/Game/Materials/Instances/MI_OfficeSpider_FrostedGlass.MI_OfficeSpider_FrostedGlass",

    # Cubicle Partitions & Furniture Material Instances
    "polypropylene": "/Game/Materials/Instances/MI_Toon_Office_Polypropylene.MI_Toon_Office_Polypropylene",
    "powdercoat": "/Game/Materials/Instances/MI_Toon_Office_PowderCoat.MI_Toon_Office_PowderCoat",
    "laminate": "/Game/Materials/Instances/MI_Toon_Office_Laminate.MI_Toon_Office_Laminate",
    "desk_toon": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Desk.MI_Film_Desk",

    # Staging Office Rig Material Instances
    "desk_staging": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_OfficeDesk_AC_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_OfficeDesk_AC_FilmStage_20261016",
    "chair_staging": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Chair_KS_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_Chair_KS_FilmStage_20261016",
    "drawers_staging": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_DeskDrawers_SG_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_DeskDrawers_SG_FilmStage_20261016",
    "breakroom_table": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_BreakroomTable_AC_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_BreakroomTable_AC_FilmStage_20261016",

    # ZMJ Breakroom Kit Material Instances (Requires 6.0x Decimeter-to-Architectural Scale)
    "zmj_counter": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_Counter_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_Counter_ZMJ_FilmStage_20261016",
    "zmj_countertop": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_CounterTop_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_CounterTop_ZMJ_FilmStage_20261016",
    "zmj_espresso": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_EspressoMachine_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_EspressoMachine_ZMJ_FilmStage_20261016",
    "zmj_fridge": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_Fridge_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_Fridge_ZMJ_FilmStage_20261016",
    "zmj_cabinet": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_Cabinet_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_Cabinet_ZMJ_FilmStage_20261016",
    "zmj_shelf": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016",
    "zmj_coffeebag": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_CoffeeBag_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_CoffeeBag_ZMJ_FilmStage_20261016",
    "zmj_coffeemug": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016",
    "zmj_pastrycover": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_PastryCover_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_PastryCover_ZMJ_FilmStage_20261016",
    "zmj_pastry": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_Pastry_ZMJ_FilmStage_20261016.MI_OneDriveRigs_Env_SM_O_Pastry_ZMJ_FilmStage_20261016",

    # Ancillary Office Props
    "vending_machine": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_VenndingMachine_Osc_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_VenndingMachine_Osc_FilmStage_20261016",
    "watercooler": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Watercooler_KS_FilmStage_20261016.MI_OneDriveRigs_Env_SM_S_Watercooler_KS_FilmStage_20261016",
    "whiteboard": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Whiteboard_SG_FilmStage_20261016.MI_OneDriveRigs_Env_SM_P_Whiteboard_SG_FilmStage_20261016",
    "plant": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016.MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016",
    "cactus": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Cactus_PMB_FilmStage_20261016.MI_OneDriveRigs_Env_SM_S_Cactus_PMB_FilmStage_20261016",
    "keyboard": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Keyboard_KS_FilmStage_20261016.MI_OneDriveRigs_Env_SM_S_Keyboard_KS_FilmStage_20261016",
    "phone": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Phone_KS_FilmStage_20261016.MI_OneDriveRigs_Env_SM_S_Phone_KS_FilmStage_20261016",

    # Film304 prop instances (children of MI_Film304_Toon; flat BaseTint, TextureWeight 0) used by the hero workstation
    "prop_plastic":   "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Plastic.MI_Film304_Prop_Plastic",
    "prop_screen":    "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Screen.MI_Film304_Prop_Screen",
    "prop_paper":     "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Paper.MI_Film304_Prop_Paper",
    "prop_ceramic":   "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Ceramic.MI_Film304_Prop_Ceramic",
    "prop_metal":     "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal.MI_Film304_Prop_Metal",
    "prop_lampshade": "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_LampShade.MI_Film304_Prop_LampShade",
    "prop_leaf":      "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Leaf.MI_Film304_Prop_Leaf",
    "prop_frame":     "/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Frame.MI_Film304_Prop_Frame",
}

# -------------------------------------------------------------------------
# Full Asset Catalog: All paths use package.asset notation for Houdini Engine
# -------------------------------------------------------------------------
ASSET_CATALOG = {
    # --- EXTERIOR BRUTALIST MONOLITHS ---
    "SM_CITY_TowerCluster": {
        "path": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster.SM_CITY_TowerCluster",
        "category": "skyline",
        "bbox_m": (114.0, 84.6, 108.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CITY_CivicSuperblock": {
        "path": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock.SM_CITY_CivicSuperblock",
        "category": "midground",
        "bbox_m": (120.0, 50.4, 96.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CITY_TightEstate": {
        "path": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TightEstate.SM_CITY_TightEstate",
        "category": "midground",
        "bbox_m": (90.0, 42.0, 90.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CITY_LowSprawl": {
        "path": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_LowSprawl.SM_CITY_LowSprawl",
        "category": "sprawl",
        "bbox_m": (156.0, 28.0, 144.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_KMZ_TowerCluster": {
        "path": "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster.SM_KMZ_TowerCluster",
        "category": "skyline",
        "bbox_m": (114.0, 84.6, 108.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_KMZ_CivicSuperblock": {
        "path": "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_CivicSuperblock.SM_KMZ_CivicSuperblock",
        "category": "midground",
        "bbox_m": (120.0, 50.4, 96.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["asphalt"], 1: MATERIALS["concrete"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_OFFICE_BarbicanScale": {
        "path": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale.SM_OFFICE_BarbicanScale",
        "category": "foreground",
        "bbox_m": (42.0, 32.0, 36.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_OFFICE_SlenderTower": {
        "path": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower.SM_OFFICE_SlenderTower",
        "category": "foreground_accent",
        "bbox_m": (28.0, 72.0, 28.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_OFFICE_CivicSlab": {
        "path": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab.SM_OFFICE_CivicSlab",
        "category": "midground",
        "bbox_m": (84.0, 36.0, 36.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_OFFICE_Bunker": {
        "path": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_Bunker.SM_OFFICE_Bunker",
        "category": "midground",
        "bbox_m": (48.0, 20.0, 42.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_FAC_TowerRibbon": {
        "path": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_TowerRibbon.SM_FAC_TowerRibbon",
        "category": "skyline",
        "bbox_m": (114.0, 85.0, 108.0),
        "domain": "exterior",
        "slots": {
            0: MATERIALS["asphalt"],
            1: MATERIALS["glazing"],
            2: MATERIALS["concrete"]
        },
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_FAC_PunchedEstate": {
        "path": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_PunchedEstate.SM_FAC_PunchedEstate",
        "category": "midground",
        "bbox_m": (105.0, 37.0, 105.0),
        "domain": "exterior",
        "slots": {
            0: MATERIALS["asphalt"],
            1: MATERIALS["glazing"],
            2: MATERIALS["concrete"]
        },
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_FAC_CivicColonnade": {
        "path": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_CivicColonnade.SM_FAC_CivicColonnade",
        "category": "foreground",
        "bbox_m": (126.0, 28.0, 118.0),
        "domain": "exterior",
        "slots": {
            0: MATERIALS["asphalt"],
            1: MATERIALS["glazing"],
            2: MATERIALS["concrete"]
        },
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_ROOF_PlantDeck": {
        "path": "/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_PlantDeck.SM_ROOF_PlantDeck",
        "category": "roof",
        "bbox_m": (28.0, 10.0, 28.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_ROOF_Sawtooth": {
        "path": "/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_Sawtooth.SM_ROOF_Sawtooth",
        "category": "roof",
        "bbox_m": (28.0, 8.0, 28.0),
        "domain": "exterior",
        "slots": {0: MATERIALS["concrete"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },

    # --- INTERIOR OFFICE & CUBICLE SETS ---
    "SM_CUBICLE_Canonical": {
        "path": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical.SM_CUBICLE_Canonical",
        "category": "cubicle_pod",
        "bbox_m": (10.23, 2.19, 6.60),
        "domain": "interior",
        "slots": {0: MATERIALS["polypropylene"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CUBICLE_MazeShift": {
        "path": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift.SM_CUBICLE_MazeShift",
        "category": "cubicle_maze",
        "bbox_m": (17.64, 2.19, 10.60),
        "domain": "interior",
        "slots": {0: MATERIALS["polypropylene"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CUBICLE_OpenPlan": {
        "path": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_OpenPlan.SM_CUBICLE_OpenPlan",
        "category": "cubicle_open",
        "bbox_m": (13.64, 1.22, 6.90),
        "domain": "interior",
        "slots": {0: MATERIALS["polypropylene"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_CUBICLE_Swarm": {
        "path": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Swarm.SM_CUBICLE_Swarm",
        "category": "cubicle_swarm",
        "bbox_m": (24.86, 2.04, 11.40),
        "domain": "interior",
        "slots": {0: MATERIALS["polypropylene"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_OfficeDesk_AC_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016.SM_P_OfficeDesk_AC_FilmStage_20261016",
        "category": "hero_desk",
        "bbox_m": (2.46, 0.76, 1.84),
        "domain": "interior",
        "slots": {0: MATERIALS["desk_staging"], 1: MATERIALS["desk_staging"]},
        "is_multi_slot": True,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "Desk": {
        "path": "/Game/Meshes/Office/Props/Desk.Desk",
        "category": "furniture_desk",
        "bbox_m": (1.68, 0.76, 0.77),
        "domain": "interior",
        "slots": {0: MATERIALS["laminate"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_Chair_KS_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016.SM_P_Chair_KS_FilmStage_20261016",
        "category": "furniture_chair",
        "bbox_m": (0.61, 1.06, 0.58),
        "domain": "interior",
        "slots": {0: MATERIALS["chair_staging"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "P_Chair_KS": {
        "path": "/Game/Meshes/Office/Props/P_Chair_KS.P_Chair_KS",
        "category": "furniture_chair",
        "bbox_m": (0.61, 1.06, 0.58),
        "domain": "interior",
        "slots": {0: MATERIALS["powdercoat"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_DeskDrawers_SG_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016.SM_P_DeskDrawers_SG_FilmStage_20261016",
        "category": "furniture_storage",
        "bbox_m": (1.47, 0.46, 0.26),
        "domain": "interior",
        "slots": {0: MATERIALS["drawers_staging"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "DeskDrawers": {
        "path": "/Game/Meshes/Office/Props/DeskDrawers.DeskDrawers",
        "category": "furniture_storage",
        "bbox_m": (0.78, 0.50, 0.71),
        "domain": "interior",
        "slots": {0: MATERIALS["powdercoat"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_BreakroomTable_AC_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_BreakroomTable_AC_FilmStage_20261016.SM_P_BreakroomTable_AC_FilmStage_20261016",
        "category": "breakroom_table",
        "bbox_m": (2.10, 0.76, 1.01),
        "domain": "interior",
        "slots": {0: MATERIALS["breakroom_table"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },

    # --- ZMJ KITCHEN / BREAKROOM KIT (EXACT 6.0x SCALE DECIMETER TO ARCHITECTURAL) ---
    "SM_O_Counter_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Counter_ZMJ_FilmStage_20261016.SM_O_Counter_ZMJ_FilmStage_20261016",
        "category": "zmj_kitchen",
        "bbox_m": (1.76, 0.94, 0.47),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_counter"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_CounterTop_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CounterTop_ZMJ_FilmStage_20261016.SM_O_CounterTop_ZMJ_FilmStage_20261016",
        "category": "zmj_kitchen",
        "bbox_m": (0.10, 0.34, 0.04),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_countertop"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_EspressoMachine_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016.SM_O_EspressoMachine_ZMJ_FilmStage_20261016",
        "category": "zmj_prop",
        "bbox_m": (0.54, 0.65, 0.47),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_espresso"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_Fridge_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Fridge_ZMJ_FilmStage_20261016.SM_O_Fridge_ZMJ_FilmStage_20261016",
        "category": "zmj_appliance",
        "bbox_m": (0.77, 1.74, 0.88),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_fridge"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_Cabinet_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Cabinet_ZMJ_FilmStage_20261016.SM_O_Cabinet_ZMJ_FilmStage_20261016",
        "category": "zmj_storage",
        "bbox_m": (0.25, 0.26, 0.09),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_cabinet"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016.SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016",
        "category": "zmj_storage",
        "bbox_m": (0.85, 0.33, 0.41),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_shelf"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_CoffeeBag_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeBag_ZMJ_FilmStage_20261016.SM_O_CoffeeBag_ZMJ_FilmStage_20261016",
        "category": "zmj_prop",
        "bbox_m": (0.12, 0.20, 0.11),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_coffeebag"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016.SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016",
        "category": "zmj_prop",
        "bbox_m": (0.14, 0.09, 0.12),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_coffeemug"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_PastryCover_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_PastryCover_ZMJ_FilmStage_20261016.SM_O_PastryCover_ZMJ_FilmStage_20261016",
        "category": "zmj_prop",
        "bbox_m": (0.20, 0.10, 0.20),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_pastrycover"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },
    "SM_O_Pastry_ZMJ_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Pastry_ZMJ_FilmStage_20261016.SM_O_Pastry_ZMJ_FilmStage_20261016",
        "category": "zmj_prop",
        "bbox_m": (0.21, 0.10, 0.20),
        "domain": "interior",
        "slots": {0: MATERIALS["zmj_pastry"]},
        "is_multi_slot": False,
        "default_scale": (6.0, 6.0, 6.0)
    },

    # --- ANCILLARY OFFICE PROPS ---
    "SM_P_VenndingMachine_Osc_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_VenndingMachine_Osc_FilmStage_20261016.SM_P_VenndingMachine_Osc_FilmStage_20261016",
        "category": "furniture_appliance",
        "bbox_m": (1.10, 1.95, 0.90),
        "domain": "interior",
        "slots": {0: MATERIALS["vending_machine"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_S_Watercooler_KS_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Watercooler_KS_FilmStage_20261016.SM_S_Watercooler_KS_FilmStage_20261016",
        "category": "furniture_appliance",
        "bbox_m": (0.45, 1.45, 0.45),
        "domain": "interior",
        "slots": {0: MATERIALS["watercooler"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_Whiteboard_SG_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Whiteboard_SG_FilmStage_20261016.SM_P_Whiteboard_SG_FilmStage_20261016",
        "category": "furniture_prop",
        "bbox_m": (1.80, 1.90, 0.60),
        "domain": "interior",
        "slots": {0: MATERIALS["whiteboard"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_S_Plant_PMB_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016.SM_S_Plant_PMB_FilmStage_20261016",
        "category": "furniture_prop",
        "bbox_m": (0.60, 1.20, 0.60),
        "domain": "interior",
        "slots": {0: MATERIALS["plant"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_S_Cactus_PMB_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Cactus_PMB_FilmStage_20261016.SM_S_Cactus_PMB_FilmStage_20261016",
        "category": "furniture_prop",
        "bbox_m": (0.35, 0.60, 0.35),
        "domain": "interior",
        "slots": {0: MATERIALS["cactus"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_S_Keyboard_KS_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Keyboard_KS_FilmStage_20261016.SM_S_Keyboard_KS_FilmStage_20261016",
        "category": "peripheral",
        "bbox_m": (0.48, 0.04, 0.16),
        "domain": "interior",
        "slots": {0: MATERIALS["keyboard"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_S_Phone_KS_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Phone_KS_FilmStage_20261016.SM_S_Phone_KS_FilmStage_20261016",
        "category": "peripheral",
        "bbox_m": (0.24, 0.12, 0.22),
        "domain": "interior",
        "slots": {0: MATERIALS["phone"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "P_ComputerMonitor_AC": {
        "path": "/Game/Meshes/Office/Props/P_ComputerMonitor_AC.P_ComputerMonitor_AC",
        "category": "peripheral",
        "bbox_m": (0.70, 0.54, 0.14),
        "domain": "interior",
        "slots": {0: MATERIALS["powdercoat"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "P_Lamp_EF": {
        "path": "/Game/Meshes/Office/Props/P_Lamp_EF.P_Lamp_EF",
        "category": "furniture_prop",
        "bbox_m": (0.42, 0.63, 0.42),
        "domain": "interior",
        "slots": {0: MATERIALS["powdercoat"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    },
    "SM_P_Bin01_SY_FilmStage_20261016": {
        "path": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Bin01_SY_FilmStage_20261016.SM_P_Bin01_SY_FilmStage_20261016",
        "category": "furniture_prop",
        "bbox_m": (0.35, 0.45, 0.35),
        "domain": "interior",
        "slots": {0: MATERIALS["powdercoat"]},
        "is_multi_slot": False,
        "default_scale": (1.0, 1.0, 1.0)
    }
}

BRUTALIST_CATALOG = ASSET_CATALOG

@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vec3(self.x * s, self.y * s, self.z * s)
    def length(self) -> float: return math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
    def normalized(self) -> 'Vec3':
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 1e-6 else Vec3(0, 0, 0)
    def dot(self, o) -> float: return self.x*o.x + self.y*o.y + self.z*o.z
    def cross(self, o) -> 'Vec3':
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )

@dataclass
class PlacedElement:
    asset_name: str
    asset_path: str
    category: str
    position_m: Vec3           # Houdini units (meters, Y-up)
    rotation_deg_y: float      # Yaw rotation around Y axis in degrees (strictly orthogonal)
    scale: Vec3
    bbox_m: Tuple[float, float, float]
    material_path: str
    material_slots: Dict[int, str] = field(default_factory=dict)
    is_multi_slot: bool = False
    roof_asset: Optional[str] = None
    note: str = ""


class CameraFrustum:
    """Calculates perspective frustum geometry in Houdini Y-up coordinates."""

    def __init__(self, pos: Vec3, target: Vec3, focal_length_mm: float = 35.0,
                 sensor_w_mm: float = 35.0, aspect_ratio: float = 16.0 / 9.0,
                 near_m: float = 1.0, far_m: float = 500.0):
        self.pos = pos
        self.target = target
        self.focal_length = focal_length_mm
        self.sensor_w = sensor_w_mm
        self.aspect = aspect_ratio
        self.near = near_m
        self.far = far_m

        self.forward = (target - pos).normalized()
        world_up = Vec3(0, 1, 0)
        if abs(self.forward.dot(world_up)) > 0.999:
            world_up = Vec3(0, 0, 1)

        self.right = self.forward.cross(world_up).normalized()
        self.up = self.right.cross(self.forward).normalized()

        self.fov_h = 2.0 * math.atan((sensor_w_mm * 0.5) / focal_length_mm)
        sensor_h_mm = sensor_w_mm / aspect_ratio
        self.fov_v = 2.0 * math.atan((sensor_h_mm * 0.5) / focal_length_mm)

        self.tan_h = math.tan(self.fov_h * 0.5)
        self.tan_v = math.tan(self.fov_v * 0.5)

    def point_at_depth(self, ndc_x: float, ndc_y: float, depth: float) -> Vec3:
        half_w = depth * self.tan_h
        half_h = depth * self.tan_v
        x_cam = ndc_x * half_w
        y_cam = ndc_y * half_h
        return self.pos + (self.forward * depth) + (self.right * x_cam) + (self.up * y_cam)


class UnifiedFilmComposer:
    """Procedurally generates Brutalist, Interior Cubicles, and ZMJ Breakroom layouts."""

    def __init__(self, camera: CameraFrustum, seed: int = 42):
        self.cam = camera
        self.seed = seed
        self.rng = random.Random(seed)
        self.placed: List[PlacedElement] = []

    def _check_overlap(self, p: Vec3, radius: float) -> bool:
        for b in self.placed:
            bx, bz = b.position_m.x, b.position_m.z
            dist = math.sqrt((p.x - bx)**2 + (p.z - bz)**2)
            b_radius = max(b.bbox_m[0], b.bbox_m[2]) * 0.5
            if dist < (radius + b_radius) * 0.85:
                return True
        return False

    def build_exterior_brutalist(self,
                                 framing_curtain_density: float = 1.0,
                                 midground_density: float = 1.0,
                                 skyline_density: float = 1.0,
                                 negative_space_radius_m: float = 25.0,
                                 include_roofs: bool = False,
                                 grid_yaw: float = 0.0) -> List[PlacedElement]:
        """Construct exterior Brutalist massing strictly aligned to the orthogonal street grid.
        
        NO random diagonal rotations. All buildings align to grid_yaw or grid_yaw + 90°.
        """
        self.placed.clear()

        # 1. Foreground Framing Curtains (flanking left and right)
        fg_assets = ["SM_OFFICE_BarbicanScale", "SM_OFFICE_SlenderTower", "SM_FAC_CivicColonnade"]
        for side in (-1.0, 1.0):
            for d in [45.0, 85.0]:
                if self.rng.random() > (0.85 * framing_curtain_density):
                    continue
                ndc_x = side * self.rng.uniform(0.70, 0.95)
                pt = self.cam.point_at_depth(ndc_x, 0.0, d)
                pt.y = 0.0

                aim_proj = self.cam.pos + (self.cam.forward * d)
                dist_to_aim = math.sqrt((pt.x - aim_proj.x)**2 + (pt.z - aim_proj.z)**2)
                if dist_to_aim < negative_space_radius_m:
                    continue

                asset_id = self.rng.choice(fg_assets)
                meta = ASSET_CATALOG[asset_id]
                radius = max(meta["bbox_m"][0], meta["bbox_m"][2]) * 0.5
                if self._check_overlap(pt, radius):
                    continue

                # Orthogonal alignment to grid
                yaw_deg = grid_yaw if side < 0 else (grid_yaw + 180.0)

                self.placed.append(PlacedElement(
                    asset_name=asset_id,
                    asset_path=meta["path"],
                    category="foreground",
                    position_m=pt,
                    rotation_deg_y=yaw_deg,
                    scale=Vec3(*meta["default_scale"]),
                    bbox_m=meta["bbox_m"],
                    material_path=meta["slots"].get(0, MATERIALS["concrete"]),
                    material_slots=dict(meta["slots"]),
                    is_multi_slot=meta.get("is_multi_slot", False),
                    note=f"Foreground framing {('left' if side < 0 else 'right')}"
                ))

        # 2. Midground Civic Massing
        mg_assets = ["SM_FAC_PunchedEstate", "SM_FAC_CivicColonnade", "SM_OFFICE_CivicSlab", "SM_CITY_CivicSuperblock", "SM_OFFICE_Bunker"]
        for d in [140.0, 220.0]:
            count = int(2 * midground_density)
            for _ in range(count):
                ndc_x = self.rng.uniform(-0.80, 0.80)
                if abs(ndc_x) < 0.25:
                    ndc_x = 0.35 if ndc_x >= 0 else -0.35
                pt = self.cam.point_at_depth(ndc_x, 0.0, d)
                pt.y = 0.0

                aim_proj = self.cam.pos + (self.cam.forward * d)
                dist_to_aim = math.sqrt((pt.x - aim_proj.x)**2 + (pt.z - aim_proj.z)**2)
                if dist_to_aim < (negative_space_radius_m * 1.2):
                    continue

                asset_id = self.rng.choice(mg_assets)
                meta = ASSET_CATALOG[asset_id]
                radius = max(meta["bbox_m"][0], meta["bbox_m"][2]) * 0.5
                if self._check_overlap(pt, radius):
                    continue

                # Strict orthogonal alignment: either parallel (grid_yaw) or cross-street (grid_yaw + 90)
                yaw_deg = grid_yaw if self.rng.random() < 0.5 else (grid_yaw + 90.0)

                self.placed.append(PlacedElement(
                    asset_name=asset_id,
                    asset_path=meta["path"],
                    category="midground",
                    position_m=pt,
                    rotation_deg_y=yaw_deg,
                    scale=Vec3(*meta["default_scale"]),
                    bbox_m=meta["bbox_m"],
                    material_path=meta["slots"].get(1, meta["slots"].get(0, MATERIALS["concrete"])),
                    material_slots=dict(meta["slots"]),
                    is_multi_slot=meta.get("is_multi_slot", False),
                    note="Midground civic slab"
                ))

        # 3. Skyline Monoliths (Distant Horizon) - Prioritize window ribbons and punch patterns
        sky_assets = ["SM_FAC_TowerRibbon", "SM_FAC_TowerRibbon", "SM_CITY_TowerCluster", "SM_KMZ_TowerCluster"]
        for d in [350.0, 480.0]:
            count = int(2 * skyline_density)
            for _ in range(count):
                ndc_x = self.rng.uniform(-0.85, 0.85)
                pt = self.cam.point_at_depth(ndc_x, 0.0, d)
                pt.y = 0.0

                asset_id = self.rng.choice(sky_assets)
                meta = ASSET_CATALOG[asset_id]
                radius = max(meta["bbox_m"][0], meta["bbox_m"][2]) * 0.5
                if self._check_overlap(pt, radius):
                    continue

                # Skyline towers face avenue orthogonally
                yaw_deg = grid_yaw if self.rng.random() < 0.6 else (grid_yaw + 180.0)
                scale_y = self.rng.uniform(1.1, 1.35)

                self.placed.append(PlacedElement(
                    asset_name=asset_id,
                    asset_path=meta["path"],
                    category="skyline",
                    position_m=pt,
                    rotation_deg_y=yaw_deg,
                    scale=Vec3(1.0, scale_y, 1.0),
                    bbox_m=meta["bbox_m"],
                    material_path=meta["slots"].get(1, meta["slots"].get(0, MATERIALS["concrete"])),
                    material_slots=dict(meta["slots"]),
                    is_multi_slot=meta.get("is_multi_slot", False),
                    note="Skyline monolith"
                ))

        return self.placed

    # Backward compatibility alias
    def build_composition(self, *args, **kwargs):
        return self.build_exterior_brutalist(*args, **kwargs)

    def build_interior_cubicle_hive(self,
                                    row_count: int = 2,
                                    pods_per_row: int = 2,
                                    x_spacing: float = 5.5,
                                    z_spacing: float = 5.0,
                                    include_desks: bool = True,
                                    include_chairs: bool = True) -> List[PlacedElement]:
        """Construct modular repeating cubicle hives with task desks and chairs with CAD precision."""
        self.placed.clear()
        start_x = -((row_count - 1) * x_spacing) * 0.5
        start_z = -((pods_per_row - 1) * z_spacing) * 0.5

        for r in range(row_count):
            for p in range(pods_per_row):
                px = start_x + (r * x_spacing)
                pz = start_z + (p * z_spacing)
                pos = Vec3(px, 0.0, pz)

                meta = ASSET_CATALOG["SM_CUBICLE_Canonical"]
                self.placed.append(PlacedElement(
                    asset_name="SM_CUBICLE_Canonical",
                    asset_path=meta["path"],
                    category="cubicle_pod",
                    position_m=pos,
                    rotation_deg_y=0.0 if r % 2 == 0 else 180.0,
                    scale=Vec3(1.0, 1.0, 1.0),
                    bbox_m=meta["bbox_m"],
                    material_path=MATERIALS["polypropylene"],
                    material_slots={0: MATERIALS["polypropylene"]},
                    is_multi_slot=False,
                    note="Canonical 6-pod cubicle cluster"
                ))

                if include_desks:
                    for d_idx, d_offset in enumerate([-1.8, 1.8]):
                        d_pos = Vec3(px + d_offset, 0.0, pz - 1.2)
                        d_meta = ASSET_CATALOG["Desk"]
                        self.placed.append(PlacedElement(
                            asset_name="Desk",
                            asset_path=d_meta["path"],
                            category="furniture_desk",
                            position_m=d_pos,
                            rotation_deg_y=90.0 if d_idx == 0 else -90.0,
                            scale=Vec3(1.0, 1.0, 1.0),
                            bbox_m=d_meta["bbox_m"],
                            material_path=MATERIALS["laminate"],
                            material_slots={0: MATERIALS["laminate"]},
                            is_multi_slot=False,
                            note="Task desk"
                        ))

                        if include_chairs:
                            c_pos = Vec3(px + d_offset, 0.0, pz - 0.5)
                            c_meta = ASSET_CATALOG["P_Chair_KS"]
                            self.placed.append(PlacedElement(
                                asset_name="P_Chair_KS",
                                asset_path=c_meta["path"],
                                category="furniture_chair",
                                position_m=c_pos,
                                rotation_deg_y=90.0 if d_idx == 0 else -90.0,
                                scale=Vec3(1.0, 1.0, 1.0),
                                bbox_m=c_meta["bbox_m"],
                                material_path=MATERIALS["powdercoat"],
                                material_slots={0: MATERIALS["powdercoat"]},
                                is_multi_slot=False,
                                note="Task chair"
                            ))

                        # Monitor on Desk (height 0.76m)
                        m_meta = ASSET_CATALOG["P_ComputerMonitor_AC"]
                        self.placed.append(PlacedElement(
                            asset_name="P_ComputerMonitor_AC",
                            asset_path=m_meta["path"],
                            category="peripheral",
                            position_m=Vec3(d_pos.x, 0.76, d_pos.z),
                            rotation_deg_y=90.0 if d_idx == 0 else -90.0,
                            scale=Vec3(1.0, 1.0, 1.0),
                            bbox_m=m_meta["bbox_m"],
                            material_path=MATERIALS["powdercoat"],
                            material_slots={0: MATERIALS["powdercoat"]},
                            is_multi_slot=False,
                            note="Desktop CRT/LCD monitor"
                        ))

                        # Keyboard on Desk
                        k_meta = ASSET_CATALOG["SM_S_Keyboard_KS_FilmStage_20261016"]
                        self.placed.append(PlacedElement(
                            asset_name="SM_S_Keyboard_KS_FilmStage_20261016",
                            asset_path=k_meta["path"],
                            category="peripheral",
                            position_m=Vec3(d_pos.x, 0.765, d_pos.z + (0.25 if d_idx == 0 else -0.25)),
                            rotation_deg_y=90.0 if d_idx == 0 else -90.0,
                            scale=Vec3(1.0, 1.0, 1.0),
                            bbox_m=k_meta["bbox_m"],
                            material_path=MATERIALS["keyboard"],
                            material_slots={0: MATERIALS["keyboard"]},
                            is_multi_slot=False,
                            note="Office keyboard"
                        ))

                        # Desk Lamp on alternating desks
                        if d_idx == 0:
                            lamp_meta = ASSET_CATALOG["P_Lamp_EF"]
                            self.placed.append(PlacedElement(
                                asset_name="P_Lamp_EF",
                                asset_path=lamp_meta["path"],
                                category="furniture_prop",
                                position_m=Vec3(d_pos.x + 0.35, 0.76, d_pos.z - 0.2),
                                rotation_deg_y=45.0,
                                scale=Vec3(1.0, 1.0, 1.0),
                                bbox_m=lamp_meta["bbox_m"],
                                material_path=MATERIALS["powdercoat"],
                                material_slots={0: MATERIALS["powdercoat"]},
                                is_multi_slot=False,
                                note="Gooseneck task lamp"
                            ))

                        # Wastebasket beside desk
                        bin_meta = ASSET_CATALOG["SM_P_Bin01_SY_FilmStage_20261016"]
                        self.placed.append(PlacedElement(
                            asset_name="SM_P_Bin01_SY_FilmStage_20261016",
                            asset_path=bin_meta["path"],
                            category="furniture_prop",
                            position_m=Vec3(d_pos.x + (0.5 if d_idx == 0 else -0.5), 0.0, d_pos.z - 0.4),
                            rotation_deg_y=15.0,
                            scale=Vec3(1.0, 1.0, 1.0),
                            bbox_m=bin_meta["bbox_m"],
                            material_path=MATERIALS["powdercoat"],
                            material_slots={0: MATERIALS["powdercoat"]},
                            is_multi_slot=False,
                            note="Office wastebasket"
                        ))

        return self.placed

    # Desk-top props for the hero workstation: (key, asset path, scale, pivot-to-bottom offset in m,
    # (x_m, z_m) offset from the desk centre, yaw, material key). Scales/offsets were measured from the
    # mesh bounds in UE so every prop reads at real-world size and rests on the desk surface.
    # Houdini (x, y-up, z) maps to UE (x, y, z-up) as (x, z, y); the sitter is on the +z side facing -z.
    _WORKSTATION_PROPS = [
        ("monitor",  "/Game/Meshes/Office/Props/P_ComputerMonitor_AC",                                         0.7467,  0.0014, ( 0.00, -0.32), 90.0, "prop_plastic"),
        ("keyboard", "/Game/Meshes/Office/Props/P_Keyboard_KS",                                                1.1282, -0.0113, ( 0.00,  0.14), 90.0, "prop_plastic"),
        ("mouse",    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Mouse_KMP_FilmStage_20261016",      0.5771,  0.0000, ( 0.36,  0.14), 90.0, "prop_plastic"),
        ("lamp",     "/Game/Meshes/Office/Props/P_Lamp_EF",                                                    0.4446, -0.1689, (-0.44, -0.34), 90.0, "prop_lampshade"),
        ("mug",      "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeMug_ZMJ_FilmStage_20261016",   4.9283, -0.0374, ( 0.40, -0.18),  0.0, "prop_ceramic"),
        ("phone",    "/Game/Meshes/Office/Props/P_Phone_KS",                                                   1.3038, -0.0017, (-0.46,  0.14), 90.0, "prop_plastic"),
        ("pen",      "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Pen_KMP_FilmStage_20261016",        1.0011,  0.0000, ( 0.22,  0.18), 90.0, "prop_metal"),
        ("plant",    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016",      1.8134, -0.2250, ( 0.56, -0.38),  0.0, "prop_leaf"),
        ("frame",    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_PictureFrame_AC_FilmStage_20261016", 0.6286, -0.1100, (-0.20, -0.42), 90.0, "prop_frame"),
    ]

    def build_hero_workstation(self, desk_top_m: float = 0.538) -> List[PlacedElement]:
        """Desk-top dressing for a single hero workstation. Origin = desk centre; y = world up (metres).

        The caller places the HDA actor at the desk centre (UE) and sets the actor's yaw so the +z side
        is where the character sits. `desk_top_m` is the surface height above the floor.
        """
        self.placed.clear()
        for key, path, s, bottom_off, (px, pz), yaw, mat in self._WORKSTATION_PROPS:
            name = path.rsplit("/", 1)[-1]
            self.placed.append(PlacedElement(
                asset_name=name,
                asset_path=f"{path}.{name}",
                category="workstation_prop",
                position_m=Vec3(px, desk_top_m - bottom_off, pz),
                rotation_deg_y=yaw,
                scale=Vec3(s, s, s),
                bbox_m=(0.3, 0.3, 0.3),
                material_path=MATERIALS[mat],
                material_slots={0: MATERIALS[mat]},
                is_multi_slot=False,
                note=f"hero workstation: {key}",
            ))
        return self.placed

    def build_breakroom_kitchen(self, center: Vec3 = Vec3(0, 0, 0.0)) -> List[PlacedElement]:
        """Construct full ZMJ breakroom kit with exact 6.0x decimeter-to-architectural scale multiplier."""
        self.placed.clear()

        # 1. Main Kitchen Counter & CounterTop
        counter_meta = ASSET_CATALOG["SM_O_Counter_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_Counter_ZMJ_FilmStage_20261016",
            asset_path=counter_meta["path"],
            category="zmj_kitchen",
            position_m=Vec3(center.x, 0.0, center.z),
            rotation_deg_y=0.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=counter_meta["bbox_m"],
            material_path=MATERIALS["zmj_counter"],
            material_slots={0: MATERIALS["zmj_counter"]},
            is_multi_slot=False,
            note="Breakroom counter base (6.0x architectural scale)"
        ))

        ct_meta = ASSET_CATALOG["SM_O_CounterTop_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_CounterTop_ZMJ_FilmStage_20261016",
            asset_path=ct_meta["path"],
            category="zmj_kitchen",
            position_m=Vec3(center.x, 0.936, center.z),
            rotation_deg_y=0.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=ct_meta["bbox_m"],
            material_path=MATERIALS["zmj_countertop"],
            material_slots={0: MATERIALS["zmj_countertop"]},
            is_multi_slot=False,
            note="Breakroom polished countertop"
        ))

        # 2. Espresso Machine sitting on Countertop
        esp_meta = ASSET_CATALOG["SM_O_EspressoMachine_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_EspressoMachine_ZMJ_FilmStage_20261016",
            asset_path=esp_meta["path"],
            category="zmj_prop",
            position_m=Vec3(center.x - 0.4, 0.94, center.z),
            rotation_deg_y=0.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=esp_meta["bbox_m"],
            material_path=MATERIALS["zmj_espresso"],
            material_slots={0: MATERIALS["zmj_espresso"]},
            is_multi_slot=False,
            note="Commercial espresso machine"
        ))

        # 3. Fridge
        fridge_meta = ASSET_CATALOG["SM_O_Fridge_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_Fridge_ZMJ_FilmStage_20261016",
            asset_path=fridge_meta["path"],
            category="zmj_appliance",
            position_m=Vec3(center.x + 1.45, 0.0, center.z - 0.1),
            rotation_deg_y=0.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=fridge_meta["bbox_m"],
            material_path=MATERIALS["zmj_fridge"],
            material_slots={0: MATERIALS["zmj_fridge"]},
            is_multi_slot=False,
            note="Commercial office refrigerator"
        ))

        # 4. Pastry Dome & Treat on Countertop
        pc_meta = ASSET_CATALOG["SM_O_PastryCover_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_PastryCover_ZMJ_FilmStage_20261016",
            asset_path=pc_meta["path"],
            category="zmj_prop",
            position_m=Vec3(center.x + 0.35, 0.94, center.z),
            rotation_deg_y=0.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=pc_meta["bbox_m"],
            material_path=MATERIALS["zmj_pastrycover"],
            material_slots={0: MATERIALS["zmj_pastrycover"]},
            is_multi_slot=False,
            note="Glass pastry cover dome"
        ))
        p_meta = ASSET_CATALOG["SM_O_Pastry_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_Pastry_ZMJ_FilmStage_20261016",
            asset_path=p_meta["path"],
            category="zmj_prop",
            position_m=Vec3(center.x + 0.35, 0.945, center.z),
            rotation_deg_y=25.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=p_meta["bbox_m"],
            material_path=MATERIALS["zmj_pastry"],
            material_slots={0: MATERIALS["zmj_pastry"]},
            is_multi_slot=False,
            note="Breakroom pastry treat"
        ))

        # 5. Coffee Bag & Ceramic Mug on Countertop
        cb_meta = ASSET_CATALOG["SM_O_CoffeeBag_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_CoffeeBag_ZMJ_FilmStage_20261016",
            asset_path=cb_meta["path"],
            category="zmj_prop",
            position_m=Vec3(center.x - 0.9, 0.94, center.z),
            rotation_deg_y=-15.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=cb_meta["bbox_m"],
            material_path=MATERIALS["zmj_coffeebag"],
            material_slots={0: MATERIALS["zmj_coffeebag"]},
            is_multi_slot=False,
            note="Artisan coffee beans bag"
        ))
        mug_meta = ASSET_CATALOG["SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016",
            asset_path=mug_meta["path"],
            category="zmj_prop",
            position_m=Vec3(center.x - 0.1, 0.94, center.z - 0.15),
            rotation_deg_y=40.0,
            scale=Vec3(6.0, 6.0, 6.0),
            bbox_m=mug_meta["bbox_m"],
            material_path=MATERIALS["zmj_coffeemug"],
            material_slots={0: MATERIALS["zmj_coffeemug"]},
            is_multi_slot=False,
            note="Large ceramic coffee mug"
        ))

        # 6. Breakroom Dining Table & 4 Chairs
        tbl_meta = ASSET_CATALOG["SM_P_BreakroomTable_AC_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_P_BreakroomTable_AC_FilmStage_20261016",
            asset_path=tbl_meta["path"],
            category="furniture_prop",
            position_m=Vec3(center.x - 0.2, 0.0, center.z - 2.8),
            rotation_deg_y=0.0,
            scale=Vec3(1.0, 1.0, 1.0),
            bbox_m=tbl_meta["bbox_m"],
            material_path=MATERIALS["breakroom_table"],
            material_slots={0: MATERIALS["breakroom_table"]},
            is_multi_slot=False,
            note="Communal breakroom dining table"
        ))
        chair_meta = ASSET_CATALOG["SM_P_Chair_KS_FilmStage_20261016"]
        chair_offsets = [
            (-0.7, 0.0, -2.8, 90.0),
            (0.3, 0.0, -2.8, -90.0),
            (-0.2, 0.0, -3.4, 0.0),
            (-0.2, 0.0, -2.2, 180.0)
        ]
        for c_idx, (cx_off, cy_off, cz_off, c_yaw) in enumerate(chair_offsets):
            self.placed.append(PlacedElement(
                asset_name="SM_P_Chair_KS_FilmStage_20261016",
                asset_path=chair_meta["path"],
                category="furniture_chair",
                position_m=Vec3(center.x + cx_off, cy_off, center.z + cz_off),
                rotation_deg_y=c_yaw,
                scale=Vec3(1.0, 1.0, 1.0),
                bbox_m=chair_meta["bbox_m"],
                material_path=MATERIALS["chair_staging"],
                material_slots={0: MATERIALS["chair_staging"]},
                is_multi_slot=False,
                note=f"Dining chair {c_idx+1}"
            ))

        # 7. Vending Machine
        vend_meta = ASSET_CATALOG["SM_P_VenndingMachine_Osc_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_P_VenndingMachine_Osc_FilmStage_20261016",
            asset_path=vend_meta["path"],
            category="furniture_appliance",
            position_m=Vec3(center.x + 2.8, 0.0, center.z),
            rotation_deg_y=-90.0,
            scale=Vec3(1.0, 1.0, 1.0),
            bbox_m=vend_meta["bbox_m"],
            material_path=MATERIALS["vending_machine"],
            material_slots={0: MATERIALS["vending_machine"]},
            is_multi_slot=False,
            note="Office snack & beverage vending machine"
        ))

        # 8. Watercooler
        wc_meta = ASSET_CATALOG["SM_S_Watercooler_KS_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_S_Watercooler_KS_FilmStage_20261016",
            asset_path=wc_meta["path"],
            category="furniture_appliance",
            position_m=Vec3(center.x - 2.2, 0.0, center.z - 1.2),
            rotation_deg_y=90.0,
            scale=Vec3(1.0, 1.0, 1.0),
            bbox_m=wc_meta["bbox_m"],
            material_path=MATERIALS["watercooler"],
            material_slots={0: MATERIALS["watercooler"]},
            is_multi_slot=False,
            note="Office watercooler with blue jug"
        ))

        # 9. Potted Plant
        plt_meta = ASSET_CATALOG["SM_S_Plant_PMB_FilmStage_20261016"]
        self.placed.append(PlacedElement(
            asset_name="SM_S_Plant_PMB_FilmStage_20261016",
            asset_path=plt_meta["path"],
            category="furniture_prop",
            position_m=Vec3(center.x - 2.2, 0.0, center.z),
            rotation_deg_y=30.0,
            scale=Vec3(1.0, 1.0, 1.0),
            bbox_m=plt_meta["bbox_m"],
            material_path=MATERIALS["plant"],
            material_slots={0: MATERIALS["plant"]},
            is_multi_slot=False,
            note="Potted ficus office plant"
        ))

        return self.placed

BrutalistComposer = UnifiedFilmComposer
