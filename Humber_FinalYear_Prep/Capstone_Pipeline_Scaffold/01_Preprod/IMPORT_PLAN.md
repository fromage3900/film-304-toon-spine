# Office Spider — Asset Import Plan

**Date:** 2026-10-06
**Source:** `C:/Users/froma/Downloads/OneDrive_2026-10-06 (1)/3rd Year Film/`
**Target:** `/g/film-304-toon-spine/`

## 1. Storyboards (DONE)

All 17 approved pages staged in `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/`

- `SB_OfficeSpider_Page01.png` through `SB_OfficeSpider_Page17.png`
- `SB_OfficeSpider_notes.md`

## 2. 3D Models (FBX) — Office Props

**Source:** `3D Models/FBX Files/`

### Office Desk Set
| File | Target Path | Notes |
|------|-------------|-------|
| `P_OfficeDesk_AC.fbx` | `Content/Meshes/Office/Props/` | Main desk |
| `P_ComputerMonitor_AC.fbx` | `Content/Meshes/Office/Props/` | Monitor |
| `P_ComputerTower_AC.fbx` | `Content/Meshes/Office/Props/` | Tower |
| `P_Keyboard_KS.fbx` | `Content/Meshes/Office/Props/` | Keyboard |
| `P_Laptop_KS.fbx` | `Content/Meshes/Office/Props/` | Laptop |
| `P_Chair_KS.fbx` | `Content/Meshes/Office/Props/` | Office chair |
| `P_Lamp_EF.fbx` | `Content/Meshes/Office/Props/` | Desk lamp |
| `P_Phone_KS.fbx` | `Content/Meshes/Office/Props/` | Phone |
| `P_File_EF.fbx` | `Content/Meshes/Office/Props/` | Papers |
| `P_StickyNotes_PMB.fbx` | `Content/Meshes/Office/Props/` | Sticky notes |
| `P_ThumbTack_PMB.fbx` | `Content/Meshes/Office/Props/` | Thumbtacks |
| `P_Book_PMB.fbx` | `Content/Meshes/Office/Props/` | Book |
| `P_BookShelf_PMB.fbx` | `Content/Meshes/Office/Props/` | Bookshelf |
| `P_Shelf_PMB.fbx` | `Content/Meshes/Office/Props/` | Shelf |
| `P_Box_EF.fbx` | `Content/Meshes/Office/Props/` | Box |
| `P_Cushion_EF.fbx` | `Content/Meshes/Office/Props/` | Cushion |
| `P_Cushion_Long_EF.fbx` | `Content/Meshes/Office/Props/` | Long cushion |
| `P_SecurityCam_KS.fbx` | `Content/Meshes/Office/Props/` | Security camera |
| `P_Watercooler_KS.fbx` | `Content/Meshes/Office/Props/` | Watercooler |
| `mop_box_wands_paperTowels.fbx` | `Content/Meshes/Office/Props/` | Cleaning supplies |

### Break Room Set
| File | Target Path | Notes |
|------|-------------|-------|
| `P_BreakroomTable_AC.fbx` | `Content/Meshes/BreakRoom/Props/` | Break room table |
| `SukhbirGhuldu_Kettle.fbx` | `Content/Meshes/BreakRoom/Props/` | Kettle |
| `SukhbirGhuldu_WhiteBoards.fbx` | `Content/Meshes/BreakRoom/Props/` | Whiteboards |
| `SukhbirGhuldu_Filing_Cabinets.fbx` | `Content/Meshes/BreakRoom/Props/` | Filing cabinets |
| `SukhbirGhuldu_DeskDrawers.fbx` | `Content/Meshes/BreakRoom/Props/` | Desk drawers |
| `SukhbirGhuldu_Calendars.fbx` | `Content/Meshes/BreakRoom/Props/` | Calendars |
| `SukhbirGhuldu_Scissors.fbx` | `Content/Meshes/BreakRoom/Props/` | Scissors |
| `vennding_machine.fbx` | `Content/Meshes/BreakRoom/Props/` | Vending machine |

### Environment
| File | Target Path | Notes |
|------|-------------|-------|
| `Benko_Pearl_OfficeAssets_02.max` | `Content/Meshes/Office/Environment/` | Max file — needs conversion |
| `BreakRoom_ZMJ.max` | `Content/Meshes/BreakRoom/Environment/` | Max file — needs conversion |

## 3. Character Rigs (Maya .mb)

**Source:** `Rigs/Temp/`

| File | Character | Target Path | Notes |
|------|-----------|-------------|-------|
| `Dana_Rig_v1.5.mb` | Dana | `Content/Meshes/Characters/Dana/` | Maya rig — convert to FBX |
| `David_Rig_v1.51.mb` | David | `Content/Meshes/Characters/David/` | Maya rig — convert to FBX |

**Conversion path:** Maya .mb → Blender → FBX → UE 5.8

## 4. Concept Art

**Source:** `Concept Art/`

| File | Target Path |
|------|-------------|
| `OfficeThumbnails01.jpg` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `OfficeThumbnails02 - Couches.jpg` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `OfficeThumbnails03 - Computer Stuff.jpg` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `OfficeThumbnails04 - Kitchen Stuff.jpg` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `SpiderStory_Concepts_PMB_01.png` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `SpiderStory_Concepts_PMB_02.png` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `SpiderStory_Concepts_PMB_03.png` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |

## 5. Documentation

**Source:** `Documentation/`

| File | Target Path |
|------|-------------|
| `Office Spider Rough Draft.pdf` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Story/` |
| `Spider Movement References.docx` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/` |
| `Tasks-3rd Year Film.xlsx` | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Story/` |

## 6. Import Order

1. **Concept art** — reference only, no conversion needed
2. **FBX props** — direct import into UE, apply toon materials
3. **Maya rigs** — Blender conversion → FBX → UE
4. **Max files** — need 3ds Max or Blender conversion (may be skip-able if FBX versions exist)
5. **Storyboards** — already staged

## 7. Toon Material Mapping

All imported assets need to be re-materialized with the existing toon pipeline:

- **Office props** → `MI_Toon_Office_*` materials
- **Break room props** → `MI_Toon_Office_*` materials
- **Characters** → `MI_Toon_Character` + `M_Master_Toon_Character`
- **Environment** → `MI_Toon_Environment` + existing brutalist materials

## 8. Missing Assets

Still needed:
- **Spider mesh** — the star! Not in the folder. Need to build in Blender or find elsewhere.
- **Coffee maker** — not in the folder (kettle is there, but storyboard shows coffee maker)
- **Microwave** — not in the folder
- **Fridge** — not in the folder
- **Mugs/cups** — not in the folder
- **Cat photo** — small prop, can be made quickly
- **Donut** — small prop for the "Donut Day" payoff
