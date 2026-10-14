# Dana — toon material lookdev

Three 1280 × 720 Unreal 5.8 stills for the Film 304 group review:

| View | Render |
| --- | --- |
| Day, face and material detail | [PNG](DANA_REFINED_UDS_DAY_DETAIL_v01.png) |
| Day, full figure | [PNG](DANA_REFINED_UDS_DAY_FULLBODY_v01.png) |
| Deep night, full figure | [PNG](DANA_REFINED_UDS_NIGHT_FULLBODY_v01.png) |

These are static material and lighting previews. Dana is in the source T-pose. The imported FBX body has **no skin cluster**, so these images do not demonstrate a working deformation rig or facial animation.

## Material setup

- `/Game/Materials/ToonProfiles/TP_DanaFilm_Clean` controls the clean film Toon response.
- `/Game/Materials/Masters/DanaFilm/` contains the isolated character, face, hair, cornea, stage floor, and hidden import-helper masters. The cornea uses the Toon BSDF through a coverage weight; its instance is `/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Cornea`.
- `/Game/Materials/Instances/DanaFilm/` holds the artist-facing overrides used by the preview maps. The generic imported helper geometry is hidden only in the preview material slot; the source mesh and skin weights are unchanged.
- `/Game/Maps/Lookdev/L_Dana_Toon_UDS_Day` and `L_Dana_Toon_UDS_Night` are the saved comparison stages. Their sequence and Movie Pipeline assets are under `Content/Sequences/DanaLookdev/` and `Content/MoviePipelines/DanaLookdev/`.

The two comparison maps use **Ultra Dynamic Sky**, which must be installed separately by a licensed user at `/Game/UltraDynamicSky`. Vendor content is not included in this commit. The PNGs can be reviewed without UDS.

## FBX handoff

The original imported skeletal mesh remains `/Game/Meshes/Office/Props/C_DanaRenderTest_OSC`. A read-only FBX audit found 37 mesh geometries: 14 intended render meshes (37,822 triangles) and 23 helper or alternate meshes (274,731 triangles). A filtered FBX trial still produced multiple-root and zero-scale-control import errors. A further pruned trial imported only 11,298 triangles of weighted clothing; neither trial replaced the production mesh. The body has zero skin clusters in the source FBX. The next rig step is to bind and export the body from Dana's Maya source, then verify deformation in Unreal.

The asset authoring and capture entry points are `Python/build_dana_refined_uds.py` and `Python/render_dana_in_editor.py`. The read-only FBX tools and guarded Maya exporter are in `Tools/`. The three stills were rendered again with a successful private Unreal render queue; no camera edits were made for this package.
