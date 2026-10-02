# Contributing

This repository is a small Unreal Engine 5.8 film/lookdev spine. Keep changes reproducible for classmates.

## Before pushing

- Open the project with Unreal Engine 5.8.
- Run `python Python/verify_repo.py` from the repository root.
- Do not commit `Binaries/`, `DerivedDataCache/`, `Intermediate/`, or `Saved/`.
- Git LFS must own Unreal/media binaries covered by `.gitattributes`.
- Never copy `.uasset` or `.umap` files between package paths with Explorer, `cp`, or `Copy-Item`. Use Unreal's asset migration/rename tools.
- Do not add private Melodia/game plugins as dependencies of the classroom spine.
- Keep feature work on a branch and make commits describe one bounded change.

## Maps and external actors

The current repository ignores World Partition external-actor/object plumbing. Do not introduce a production World Partition/OFPA map unless the repository policy is changed deliberately so its external actors are versioned and verified.

## Python

Scripts that import `unreal` run inside Unreal and cannot be executed by ordinary GitHub-hosted Python. CI therefore checks portable repository contracts and Python syntax without pretending to execute editor-only APIs.

## Licensing

No open-source license has been selected yet. Do not add or change licensing terms as part of an unrelated contribution.
