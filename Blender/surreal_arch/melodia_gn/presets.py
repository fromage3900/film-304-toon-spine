"""BRUTALIST subset of the Melodia builder-preset library.

Source: P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/presets.py
        (upstream lines 4368-4636, copied VERBATIM below).

The upstream file carries presets for every GN builder in the Melodia project
(~4.6k lines). This vendored copy carries only the four brutalist builders so the
304 film repo stays readable:

    GN_BRUTALIST_CityBlock, GN_BRUTALIST_OfficeBlock,
    GN_BRUTALIST_CubicleFarm, GN_BRUTALIST_Roof

Same data shape as upstream (see its module docstring). To refresh, re-extract
those lines from the source file — do not hand-edit here.
"""
from __future__ import annotations

from typing import Any

BUILDERS_PRESETS: dict[str, Any] = {}

BUILDERS_PRESETS["GN_BRUTALIST_OfficeBlock"] = {
    "label": "BRUTALIST Office Block",
    "preset_labels": {
        "BR_OFFICE_CIVIC": "Civic Slab",
        "BR_OFFICE_BARBICAN": "Barbican Scale",
        "BR_OFFICE_BUNKER": "Bunker",
        "BR_OFFICE_SLENDER": "Slender Tower",
    },
    "preset_descriptions": {
        "BR_OFFICE_CIVIC": "The default read: 18x12, six floors, pilotis "
                           "lobby, stair tower, roof plant.",
        "BR_OFFICE_BARBICAN": "Estate scale: 24x14, eight floors, ten bays, "
                              "deep reveals, denser formwork.",
        "BR_OFFICE_BUNKER": "Squat and windowless-heavy: three floors, no "
                            "pilotis, no tower, high parapet, fat bands.",
        "BR_OFFICE_SLENDER": "Ten-storey slab: 10x8 footprint, four bays, "
                             "tight floor height.",
    },
    "presets": {
        "BR_OFFICE_CIVIC": {
            "Block Width": 18.0, "Block Depth": 12.0, "Floors": 6,
            "Floor Height": 3.2, "Bay Count": 8, "Pier Width": 0.5,
            "Band Height": 0.9, "Window Reveal": 0.35, "Pilotis": True,
            "Pilotis Height": 4.2, "Stair Tower": True, "Tower Width": 3.2,
            "Slot Count": 6, "Parapet Height": 0.9, "Roof Plant": True,
            "Plant Height": 2.2, "Formwork": 3,
        },
        "BR_OFFICE_BARBICAN": {
            "Block Width": 24.0, "Block Depth": 14.0, "Floors": 8,
            "Floor Height": 3.4, "Bay Count": 10, "Pier Width": 0.6,
            "Band Height": 1.1, "Window Reveal": 0.55, "Pilotis": True,
            "Pilotis Height": 5.0, "Stair Tower": True, "Tower Width": 4.0,
            "Slot Count": 8, "Parapet Height": 1.2, "Roof Plant": True,
            "Plant Height": 2.6, "Formwork": 5,
        },
        "BR_OFFICE_BUNKER": {
            "Block Width": 14.0, "Block Depth": 10.0, "Floors": 3,
            "Floor Height": 3.6, "Bay Count": 5, "Pier Width": 0.8,
            "Band Height": 1.4, "Window Reveal": 0.9, "Pilotis": False,
            "Pilotis Height": 3.0, "Stair Tower": False, "Tower Width": 3.2,
            "Slot Count": 4, "Parapet Height": 1.6, "Roof Plant": False,
            "Plant Height": 1.4, "Formwork": 4,
        },
        "BR_OFFICE_SLENDER": {
            "Block Width": 10.0, "Block Depth": 8.0, "Floors": 12,
            "Floor Height": 3.0, "Bay Count": 4, "Pier Width": 0.45,
            "Band Height": 0.8, "Window Reveal": 0.3, "Pilotis": True,
            "Pilotis Height": 4.6, "Stair Tower": True, "Tower Width": 2.6,
            "Slot Count": 10, "Parapet Height": 0.7, "Roof Plant": True,
            "Plant Height": 1.8, "Formwork": 2,
        },
    },
}

BUILDERS_PRESETS["GN_BRUTALIST_CubicleFarm"] = {
    "label": "BRUTALIST Cubicle Farm",
    "preset_labels": {
        "BR_CUBICLE_CANON": "Canonical Farm",
        "BR_CUBICLE_MAZE": "Maze Shift",
        "BR_CUBICLE_OPEN": "Open Plan",
        "BR_CUBICLE_SWARM": "Swarm",
    },
    "preset_descriptions": {
        "BR_CUBICLE_CANON": "Three rows of four: partitions, desks, monitors, "
                            "chairs, bins, waffle ceiling.",
        "BR_CUBICLE_MAZE": "Five by five with Drift 0.55 - the grid starts to "
                           "shear without rebuilding.",
        "BR_CUBICLE_OPEN": "Low partitions, no bins, more plants - the "
                           "management-approved read.",
        "BR_CUBICLE_SWARM": "Six by eight at Drift 0.85 - the Escher shear at "
                            "floor-plan scale.",
    },
    "presets": {
        "BR_CUBICLE_CANON": {
            "Rows": 3, "Columns": 4, "Cell Width": 2.4, "Cell Depth": 2.0,
            "Partition Height": 1.65, "Partition Thickness": 0.06,
            "Desk Height": 0.74, "Desk Depth": 0.6, "Monitor": True,
            "Monitor Size": 0.5, "Chair": True, "Overhead Bin": True,
            "Drift": 0.0, "Ceiling Grid": True, "Grid Beams": 8,
            "Ceiling Height": 2.9, "Lights": 8, "Plants": 3,
        },
        "BR_CUBICLE_MAZE": {
            "Rows": 5, "Columns": 5, "Cell Width": 2.4, "Cell Depth": 2.0,
            "Partition Height": 1.65, "Partition Thickness": 0.06,
            "Desk Height": 0.74, "Desk Depth": 0.6, "Monitor": True,
            "Monitor Size": 0.5, "Chair": True, "Overhead Bin": True,
            "Drift": 0.55, "Ceiling Grid": True, "Grid Beams": 10,
            "Ceiling Height": 3.1, "Lights": 10, "Plants": 4,
        },
        "BR_CUBICLE_OPEN": {
            "Rows": 3, "Columns": 5, "Cell Width": 2.6, "Cell Depth": 2.1,
            "Partition Height": 1.10, "Partition Thickness": 0.05,
            "Desk Height": 0.74, "Desk Depth": 0.65, "Monitor": True,
            "Monitor Size": 0.55, "Chair": True, "Overhead Bin": False,
            "Drift": 0.0, "Ceiling Grid": True, "Grid Beams": 8,
            "Ceiling Height": 3.4, "Lights": 8, "Plants": 5,
        },
        "BR_CUBICLE_SWARM": {
            "Rows": 6, "Columns": 8, "Cell Width": 2.0, "Cell Depth": 1.8,
            "Partition Height": 1.5, "Partition Thickness": 0.05,
            "Desk Height": 0.72, "Desk Depth": 0.55, "Monitor": True,
            "Monitor Size": 0.45, "Chair": True, "Overhead Bin": True,
            "Drift": 0.85, "Ceiling Grid": True, "Grid Beams": 14,
            "Ceiling Height": 3.0, "Lights": 14, "Plants": 6,
        },
    },
}


# BRUTALIST city family (2026-09-25): the 2D exterior massing layer.  Same dial
# philosophy as the other two brutalist builders - the system IS the parameter set.
# Presets double as the contact-sheet shot list, so every one is a frame a team can
# look at rather than an abstract number set.

BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"] = {
    "label": "BRUTALIST City Block",
    "preset_labels": {
        "BR_CITY_TIGHT": "Tight Estate",
        "BR_CITY_TOWERS": "Tower Cluster",
        "BR_CITY_SPRAWL": "Low Sprawl",
        "BR_CITY_CIVIC": "Civic Superblock",
    },
    "preset_descriptions": {
        "BR_CITY_TIGHT": "4x4 lots at 12m with 6m streets: the Barbican read, "
                         "18-42m of stacked slab.",
        "BR_CITY_TOWERS": "3x3 generous lots, 45-90m. Aerial view territory - "
                          "the skyline shot.",
        "BR_CITY_SPRAWL": "5x5 wide lots, deep setback, 8-16m. Post-war "
                          "low-rise estate plate.",
        "BR_CITY_CIVIC": "2x2 oversized lots, 14m carriageways, 16-28m. "
                         "Institutional superblock with a plaza-scale void.",
    },
    "presets": {
        "BR_CITY_TIGHT": {
            "Blocks X": 4, "Blocks Y": 4, "Lot Width": 12.0, "Lot Depth": 12.0,
            "Street Width": 6.0, "Setback": 1.0, "Height Min": 18.0,
            "Height Max": 42.0, "Seed": 7, "Ground": True, "Roads": True,
            "Sidewalks": True, "Parapet": True, "Piers": True,
        },
        "BR_CITY_TOWERS": {
            "Blocks X": 3, "Blocks Y": 3, "Lot Width": 18.0, "Lot Depth": 16.0,
            "Street Width": 10.0, "Setback": 2.0, "Height Min": 45.0,
            "Height Max": 90.0, "Seed": 23, "Ground": True, "Roads": True,
            "Sidewalks": True, "Parapet": True, "Piers": True,
        },
        "BR_CITY_SPRAWL": {
            "Blocks X": 5, "Blocks Y": 5, "Lot Width": 20.0, "Lot Depth": 18.0,
            "Street Width": 7.0, "Setback": 4.0, "Height Min": 8.0,
            "Height Max": 16.0, "Seed": 3, "Ground": True, "Roads": True,
            "Sidewalks": True, "Parapet": True, "Piers": True,
        },
        "BR_CITY_CIVIC": {
            "Blocks X": 2, "Blocks Y": 2, "Lot Width": 28.0, "Lot Depth": 24.0,
            "Street Width": 14.0, "Setback": 3.0, "Height Min": 16.0,
            "Height Max": 28.0, "Seed": 11, "Ground": True, "Roads": True,
            "Sidewalks": True, "Parapet": True, "Piers": False,
        },
    },
}

# BRUTALIST roof family (2026-09-25) - GN_BRUTALIST_Roof, added with the builder.
# Same philosophy as the rest of the family: the system IS the parameter set, and
# each preset is a frame a team can look at rather than an abstract number set.
# Roof Style values are the builder's own enum: 0 Flat/Parapet, 1 Low Pitch,
# 2 Sawtooth, 3 Barrel Vault, 4 Pyramid/Hip, 5 Plant Deck.
BUILDERS_PRESETS["GN_BRUTALIST_Roof"] = {
    "label": "BRUTALIST Roof",
    "preset_labels": {
        "BR_ROOF_FLAT": "Flat Parapet",
        "BR_ROOF_PITCH": "Low Pitch",
        "BR_ROOF_SAWTOOTH": "Sawtooth",
        "BR_ROOF_BARREL": "Barrel Vault",
        "BR_ROOF_HIP": "Pyramid Hip",
        "BR_ROOF_PLANT": "Plant Deck",
    },
    "preset_descriptions": {
        "BR_ROOF_FLAT": "Parapet rim over a deck. The default brutalist "
                        "roofline; reads at skyline distance.",
        "BR_ROOF_PITCH": "Shallow two-sided pitch, eaves dropping outward.",
        "BR_ROOF_SAWTOOTH": "North-lit sheds - the post-war industrial plate.",
        "BR_ROOF_BARREL": "Faceted concrete barrel for vaulted halls.",
        "BR_ROOF_HIP": "Four-way hip over a civic block.",
        "BR_ROOF_PLANT": "Lift overrun and plant housing; makes a flat roof "
                         "read as inhabited rather than unfinished.",
    },
    "presets": {
        "BR_ROOF_FLAT": {
            "Building Width": 18.0, "Building Depth": 12.0, "Roof Style": 0,
            "Roof Pitch": 0.28, "Eave Overhang": 0.6, "Roof Thickness": 0.32,
            "Gutters": True, "Gutter Width": 0.28,
            "Roof Plant": False, "Plant Height": 1.6, "Plant Units": 4,
        },
        "BR_ROOF_PITCH": {
            "Building Width": 22.0, "Building Depth": 14.0, "Roof Style": 1,
            "Roof Pitch": 0.22, "Eave Overhang": 0.9, "Roof Thickness": 0.35,
            "Gutters": True, "Gutter Width": 0.3,
            "Roof Plant": False, "Plant Height": 1.6, "Plant Units": 4,
        },
        "BR_ROOF_SAWTOOTH": {
            "Building Width": 26.0, "Building Depth": 18.0, "Roof Style": 2,
            "Roof Pitch": 0.34, "Eave Overhang": 0.4, "Roof Thickness": 0.3,
            "Sawtooth Teeth": 5, "Sawtooth Width": 3.4,
            "Gutters": False, "Gutter Width": 0.28,
            "Roof Plant": False, "Plant Height": 1.6, "Plant Units": 4,
        },
        "BR_ROOF_BARREL": {
            "Building Width": 20.0, "Building Depth": 16.0, "Roof Style": 3,
            "Roof Pitch": 0.42, "Eave Overhang": 0.5, "Roof Thickness": 0.4,
            "Gutters": False, "Gutter Width": 0.28,
            "Roof Plant": False, "Plant Height": 1.6, "Plant Units": 4,
        },
        "BR_ROOF_HIP": {
            "Building Width": 24.0, "Building Depth": 20.0, "Roof Style": 4,
            "Roof Pitch": 0.3, "Eave Overhang": 1.0, "Roof Thickness": 0.36,
            "Gutters": True, "Gutter Width": 0.32,
            "Roof Plant": False, "Plant Height": 1.6, "Plant Units": 4,
        },
        "BR_ROOF_PLANT": {
            "Building Width": 18.0, "Building Depth": 12.0, "Roof Style": 5,
            "Roof Pitch": 0.28, "Eave Overhang": 0.6, "Roof Thickness": 0.32,
            "Gutters": True, "Gutter Width": 0.28,
            "Roof Plant": True, "Plant Height": 2.2, "Plant Units": 6,
        },
    },
}

# City facade variations (2026-09-25). Facade Style is the builder's enum:
# 0 Blank, 1 Ribbon, 2 Punched, 3 Colonnade. Default stays 0, so every
# pre-existing city preset is untouched - these are ADDITIONAL named looks.
# NOTE: the registry dict is BUILDERS_PRESETS, not _BUILDERS_PRESETS; the
# leading-underscore name is a NameError, not a private alias.
BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"]["presets"]["BR_CITY_TOWERS_GLASS"] = {
    "Blocks X": 3, "Blocks Y": 3, "Lot Width": 18.0, "Lot Depth": 16.0,
    "Street Width": 10.0, "Setback": 2.0, "Height Min": 45.0,
    "Height Max": 90.0, "Seed": 23, "Ground": True, "Roads": True,
    "Sidewalks": True, "Parapet": True, "Piers": True,
    "Facade Style": 1, "Window Floors": 18, "Window Bay": 2.4,
    "Window Band Height": 1.6, "Window Reveal": 0.3, "Fin Depth": 0.5,
    "Fin Count": 6,
}
BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"]["presets"]["BR_CITY_PUNCHED"] = {
    "Blocks X": 4, "Blocks Y": 4, "Lot Width": 14.0, "Lot Depth": 14.0,
    "Street Width": 7.0, "Setback": 1.5, "Height Min": 18.0,
    "Height Max": 36.0, "Seed": 5, "Ground": True, "Roads": True,
    "Sidewalks": True, "Parapet": True, "Piers": True,
    "Facade Style": 2, "Window Floors": 9, "Window Bay": 2.0,
    "Window Band Height": 1.3, "Window Reveal": 0.35, "Fin Depth": 0.5,
    "Fin Count": 6,
}
BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"]["presets"]["BR_CITY_COLONNADE"] = {
    "Blocks X": 2, "Blocks Y": 2, "Lot Width": 28.0, "Lot Depth": 24.0,
    "Street Width": 14.0, "Setback": 3.0, "Height Min": 16.0,
    "Height Max": 28.0, "Seed": 11, "Ground": True, "Roads": True,
    "Sidewalks": True, "Parapet": True, "Piers": True,
    "Facade Style": 3, "Window Floors": 6, "Window Bay": 2.6,
    "Window Band Height": 1.5, "Window Reveal": 0.4, "Fin Depth": 0.9,
    "Fin Count": 10,
}
BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"]["preset_labels"].update({
    "BR_CITY_TOWERS_GLASS": "Tower Cluster (Ribbon glazing)",
    "BR_CITY_PUNCHED": "Punched Estate",
    "BR_CITY_COLONNADE": "Civic Colonnade",
})
BUILDERS_PRESETS["GN_BRUTALIST_CityBlock"]["preset_descriptions"].update({
    "BR_CITY_TOWERS_GLASS": "The skyline shot with ribbon glazing - the "
                            "difference between a tower and a grey box.",
    "BR_CITY_PUNCHED": "Punched openings on a bay grid, post-war housing read.",
    "BR_CITY_COLONNADE": "Deep vertical fins on a civic superblock.",
})
