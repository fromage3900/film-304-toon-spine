# Office Spider — Asset Compatibility & Import Status

**Date:** 2026-10-06
**Project:** 3rd Year Film — Office Spider
**Engine:** Unreal Engine 5.8 (Substrate Toon Pipeline)

## Summary

Asset inventory from `OneDrive_2026-10-06 (1)/3rd Year Film/` with import status and UE 5.8 compatibility notes.

## 1. Storyboards — STAGED ✅

**Location:** `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/`

| File | Artist | Status |
|------|--------|--------|
| `SB_OfficeSpider_Page01.png` – `Page12.png` | Jeffrey Dawn | Staged |
| `SB_OfficeSpider_Page13.png` – `Page17.png` | Joujou Yeh | Staged |
| `SB_OfficeSpider_notes.md` | — | Staged |

**Total:** 17 approved pages

## 2. 3D Models (FBX) — STAGED ✅

**Location:** `Content/Meshes/Office/Props/` and `Content/Meshes/BreakRoom/Props/`

### Office Props (20 files)

| File | UE Import | Toon Material | Notes |
|------|-----------|---------------|-------|
| `P_OfficeDesk_AC.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Main desk |
| `P_ComputerMonitor_AC.fbx` | ✅ Direct | `MI_Toon_Office_Screen` | Monitor |
| `P_ComputerTower_AC.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Tower |
| `P_Keyboard_KS.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Keyboard |
| `P_Laptop_KS.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Laptop |
| `P_Chair_KS.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Office chair |
| `P_Lamp_EF.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Desk lamp |
| `P_Phone_KS.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Phone |
| `P_File_EF.fbx` | ✅ Direct | `MI_Toon_Office_Paper` | Papers |
| `P_StickyNotes_PMB.fbx` | ✅ Direct | `MI_Toon_Office_Paper` | Sticky notes |
| `P_ThumbTack_PMB.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Thumbtacks |
| `P_Book_PMB.fbx` | ✅ Direct | `MI_Toon_Office_Paper` | Book |
| `P_BookShelf_PMB.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Bookshelf |
| `P_Shelf_PMB.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Shelf |
| `P_Box_EF.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Box |
| `P_Cushion_EF.fbx` | ✅ Direct | `MI_Toon_Office_Fabric` | Cushion |
| `P_Cushion_Long_EF.fbx` | ✅ Direct | `MI_Toon_Office_Fabric` | Long cushion |
| `P_SecurityCam_KS.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Security camera |
| `P_Watercooler_KS.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Watercooler |
| `mop_box_wands_paperTowels.fbx` | ✅ Direct | `MI_Toon_Office_Polypropylene` | Cleaning supplies |

### Break Room Props (8 files)

| File | UE Import | Toon Material | Notes |
|------|-----------|---------------|-------|
| `P_BreakroomTable_AC.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Break room table |
| `SukhbirGhuldu_Kettle.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Kettle |
| `SukhbirGhuldu_WhiteBoards.fbx` | ✅ Direct | `MI_Toon_Office_Whiteboard` | Whiteboards |
| `SukhbirGhuldu_Filing_Cabinets.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Filing cabinets |
| `SukhbirGhuldu_DeskDrawers.fbx` | ✅ Direct | `MI_Toon_Office_Laminate` | Desk drawers |
| `SukhbirGhuldu_Calendars.fbx` | ✅ Direct | `MI_Toon_Office_Paper` | Calendars |
| `SukhbirGhuldu_Scissors.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Scissors |
| `vennding_machine.fbx` | ✅ Direct | `MI_Toon_Office_PowderCoat` | Vending machine |

## 3. Character Rigs (Maya .mb) — STAGED, NOT CONVERTED ⚠️

**Location:** `Content/Meshes/Characters/Dana/` and `Content/Meshes/Characters/David/`

| File | Format | UE Import | Status |
|------|--------|-----------|--------|
| `Dana_Rig_v1.5.mb` | Maya binary | ❌ Cannot import directly | Needs conversion |
| `David_Rig_v1.51.mb` | Maya binary | ❌ Cannot import directly | Needs conversion |

### Compatibility Issues

1. **Maya .mb is binary** — UE 5.8 cannot import Maya binary files directly
2. **Custom rig controls** — FK/IK, finger curves, breathing deformer will NOT transfer to UE
3. **Skeleton naming** — Maya skeleton naming won't match UE's Humanoid or MetaHuman skeleton
4. **Retargeting required** — even after FBX conversion, bones need remapping to UE skeleton

### Conversion Path

```
Maya .mb → Maya FBX export → UE 5.8 import → Retarget to UE skeleton
```

**Requirements:**
- Maya 2025 (installed at `C:/Program Files/Autodesk/Maya2025/`)
- FBX export from Maya
- UE retargeting setup

### Rig Features (from ReadMe)

**Dana v1.5:**
- FK/IK spine, finger controls, eyelid creases
- Breathing deformer, blink fix, teeth controllers
- Partial + Full body geometry options
- Hairstyle options

**David v1.51:**
- Same feature set as Dana
- Fixed hair issue
- Body Mechanics mode

**Author:** Gabriel Salas (Gumroad)
**License:** Educational, non-commercial use only

## 4. Max Files — NOT STAGED ⚠️

**Source:** `3D Models/Max Files/`

| File | Format | UE Import | Notes |
|------|--------|-----------|-------|
| `Benko_Pearl_OfficeAssets_02.max` | 3ds Max | ❌ Cannot import directly | Needs conversion |
| `BreakRoom_ZMJ.max` | 3ds Max | ❌ Cannot import directly | Needs conversion |

**Note:** These may be skip-able if the FBX versions above cover the same assets.

## 5. Concept Art — STAGED ✅

**Location:** `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/References/`

| File | Notes |
|------|-------|
| `OfficeThumbnails01.jpg` | Office layout thumbnails |
| `OfficeThumbnails02 - Couches.jpg` | Couch options |
| `OfficeThumbnails03 - Computer Stuff.jpg` | Computer props |
| `OfficeThumbnails04 - Kitchen Stuff.jpg` | Kitchen props |
| `SpiderStory_Concepts_PMB_01.png` | Spider story concept 1 |
| `SpiderStory_Concepts_PMB_02.png` | Spider story concept 2 |
| `SpiderStory_Concepts_PMB_03.png` | Spider story concept 3 |

## 6. Documentation — STAGED ✅

**Location:** `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Story/`

| File | Notes |
|------|-------|
| `Office Spider Rough Draft.pdf` | Script/rough draft |
| `Tasks-3rd Year Film.xlsx` | Task tracking |
| `Spider Movement References.docx` | Spider animation reference |

## 7. Missing Assets

Still needed for full Office Spider production:

| Asset | Priority | Notes |
|-------|----------|-------|
| Spider mesh | 🔴 Critical | The star! Not in the folder |
| Coffee maker | 🟡 Medium | Storyboard shows one; kettle is available |
| Microwave | 🟡 Medium | Break room prop |
| Fridge | 🟡 Medium | Break room prop |
| Mugs/cups | 🟢 Low | Small props |
| Cat photo | 🟢 Low | Small prop for desk |
| Donut | 🟢 Low | "Donut Day" payoff prop |

## 8. Next Steps

1. **Import FBX props into UE** — drag and drop into Content Browser
2. **Apply toon materials** — assign `MI_Toon_Office_*` materials to each prop
3. **Convert Maya rigs** — use Maya 2025 to export FBX, then retarget in UE
4. **Build missing props** — spider, coffee maker, microwave, fridge in Blender
5. **Set up Sequencer** — create master sequence with shots from storyboard

## 9. Toon Material Mapping

All imported assets should use the existing toon pipeline:

- **Office props** → `MI_Toon_Office_*` materials (already in repo)
- **Break room props** → `MI_Toon_Office_*` materials
- **Characters** → `MI_Toon_Character` + `M_Master_Toon_Character`
- **Environment** → `MI_Toon_Environment` + existing brutalist materials

## 10. Git Status

**Staged files:**
- 17 storyboard pages
- 20 office props (FBX)
- 8 break room props (FBX)
- 2 character rigs (Maya .mb)
- 7 concept art images
- 3 documentation files
- 1 import plan
- 1 compatibility doc (this file)

**Total:** ~181 files staged and ready for commit
