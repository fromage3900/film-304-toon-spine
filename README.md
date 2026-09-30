# Melodia Toon Film

Standalone UE 5.8 toon shading spine for indie 3D animation film projects.

## What this is

A clean extraction of the Melodia universal toon material system, stripped of game-specific
dependencies (MeshBlend plugin, water sim, Nikki character effects) and ready for
film/cinematic production in Unreal Engine 5.8's Substrate Toon pipeline.

## Structure

```
Content/
  Materials/
    Masters/          # M_Master_Toon_Universal (the spine)
    Functions/        # Only the MFs the master actually calls
    ToonProfiles/     # TP_* assets for art-direction
Python/
  extract_dependencies.py   # Traces MF dependency graph from the master
  build_master.py           # Rebuilds the master from scratch
Config/
  DefaultEngine.ini
Docs/
  TOON_SPINE.md             # Architecture + dependency map
  FILM_PIPELINE.md          # Indie film workflow with UE 5.8 toon
```

## Quick start

1. Clone into a UE 5.8 project's Content/ folder, or use as a standalone content pack
2. Run `Python/extract_dependencies.py` in the UE editor to verify the dependency graph
3. Open M_Master_Toon_Universal and create material instances

## Engine requirements

- Unreal Engine 5.8+ (Substrate Toon BSDF is experimental in 5.8)
- No external plugins required (MeshBlend dependency stripped)

## Research

See `Docs/FILM_PIPELINE.md` for the indie 3D animation film workflow using UE 5.8's
Substrate Toon pipeline.
