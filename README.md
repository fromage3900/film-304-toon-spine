# Humber 304 UE Toon Shading Pipeline

Standalone Unreal Engine 5.8 toon-shading spine for indie 3D animation film projects.

## Hello friends ~

This is the base UE project for our film toon/look-development pipeline. It includes the reusable shader spine, Toon Profiles, material instances, Python builders, and a lookdev scene.

**You do not need Git experience to use the project.** Clone/download the repository, install Git LFS if you are cloning with Git, then open `MelodiaToonFilm.uproject` in Unreal Engine 5.8.

## Quick start

1. Install **Unreal Engine 5.8**.
2. If using Git, install Git LFS and run `git lfs install` once on your computer.
3. Clone this repository, then run `git lfs pull`.
4. Open `MelodiaToonFilm.uproject`.
5. Open the included lookdev content and create material instances from `M_Master_Toon_Universal`.
6. Before contributing changes, run `python Python/verify_repo.py` from the repository root.

> Do not copy this entire repository into another project's `Content/` directory. Unreal assets are package-path aware. Use Unreal's migration workflow when moving assets into another project.

## Structure

```
Content/
  Materials/
    Masters/          # M_Master_Toon_Universal
    Functions/        # reusable material functions
    ToonProfiles/     # TP_* art-direction assets
Python/
  extract_dependencies.py
  build_master.py
  verify_repo.py
Config/
  DefaultEngine.ini
Docs/
  TOON_SPINE.md
  FILM_PIPELINE.md
```

## Engine requirements

- Unreal Engine 5.8
- Substrate enabled
- Movie Render Pipeline
- Python Editor Script Plugin

The public release is intended to be self-contained. If the dependency verifier reports a plugin reference, treat that as a release blocker rather than installing a private project dependency.

## Contributing

See `CONTRIBUTING.md`. Keep generated folders out of Git, use LFS for binary assets, never raw-copy `.uasset`/`.umap` files between package paths, and run the repository verifier before pushing.

## License

No open-source license has been selected yet. Until the repository owner adds one, do not assume permission to redistribute or relicense the project outside the intended class collaboration.

## Research

See `Docs/FILM_PIPELINE.md` for the film workflow and `Docs/TOON_SPINE.md` for the shader architecture.
