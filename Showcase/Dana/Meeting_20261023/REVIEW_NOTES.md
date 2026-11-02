# Dana toon look review — 23 Oct 2026

## Meeting read

The dark-eyed frame is a rejected material probe, not an eye replacement. Render 09 keeps the amber iris and pale sclera visible; render 10 loses that contrast. The eye, sclera, iris, cornea, and eye-interior slot references read back unchanged between the captures. The exact cross-material cause is still unisolated, so do not present render 10 as a look target.

The skin is still too pale in both frames. The earlier warm `BaseTint` attempts did not reach the visible albedo: Dana’s active Universal Toon instance has Layer A enabled, and that layer wins the color blend ahead of `BaseTint`.

## Verified source and safety

- Dana’s skin chain remains the existing `MI_Dana_Skin_FaceVerified_v02` → `MI_Film304_Toon` → Universal v06. The shared master and production map were not changed.
- Two additive child candidates are saved with `bLayerA_Active=false`, a restrained golden-brown `BaseTint`, and matching Banded/Smooth switches. Parent and parameter readbacks passed; the pair has **not** been visually rendered or approved.
- Existing `L_Film_Office` capture evidence reports no dirty map packages after the last successful capture. No production map save was issued; the later close-up process ended on its GPU allocation failure.
- Face SDFs are directional UV studies, not a connected Universal face-shadow input. Universal v06 exposes `PatternSDFMap` for pattern work; do not claim face-shadow SDF integration yet.

## Review artifacts

- Eye contrast: `Renders/DanaEyeContrast_09vs10_v01.png`
- Eye-readable but pale: `Renders/DanaPortrait_09_Universal_Banded_WarmBrown_v01.png`
- Dark-eyed reject: `Renders/DanaPortrait_10_Universal_Banded_DeepWarmBrown_v01.png`
- Normal and roughness options: `Maps/Dana_Hython_MapStudies_Contact_v01.png`
- Face SDF direction and feather preview: `Maps/DanaFaceSDF_TonePreview_v01.png`
- Render, material, and slot readbacks: `Saved/Audit/DanaMeeting/capture_report.json`
- Warm child material readbacks: `Saved/Audit/DanaMeeting/warm_brown_universal_child_readback.json`

## Next bounded pass

1. Render the prepared Banded child first at 1920×1080 with the recorded pose and camera. Inspect actual face color and both eyes before making a Smooth twin capture.
2. If eyes darken again, isolate the skin material slot against the same eye materials and inspect the mesh section/material mapping; do not compensate with an eye recolor until that cause is identified.
3. For face SDF, keep the left/right mask and tone preview as evidence, then add a face-specific SDF path only through an approved additive shader experiment. Keep this separate from the existing periodic pattern input.
4. Compare Arcane striation, Riso dot emboss, and Gouache fiber as subtle normal/roughness studies after the base complexion and eyes read correctly.

The 2560/4K close-up attempts exhausted D3D12 video memory while allocating large shadow maps. A later 1080p launch did not produce a completion record and was stopped before the active C: editor was affected. The latest capture report remains partial; the new warm-brown pair is prepared, not render-proven.

