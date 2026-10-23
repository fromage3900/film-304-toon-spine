# Prompt for Cline — fix skin poking through Sam's shirt sleeves (headless, new asset only)

Project `G:\film-304-toon-spine` (UE 5.8). Same safety rules as `Docs/CLINE_POSING_PROMPT_20261017.md` (new assets only, no deletes, no map saves, no git, no GUI editor, scripts/logs in `Saved/ClinePosing/`).

## Problem (verified by screenshots `Saved/Screenshots/sleeve1_before.png`, `seat_high34.png`)
On `SK_Sam_Film304_v01` the **skin shell pokes through the right shirt sleeve** (orange blotches on the shoulder top, upper arm and cuff) while he stands in `AS_Sam_ArmsCrossed`. The shirt (`samShirt_mat`, section 11) and skin (`lambert1`, section 0) are separate shells that sit too close, and skinning moves them apart a little. It also shows on the torso (earlier standing screenshots). It is a geometry issue; material tricks do not fix it (enabling `bClothWind_Active` on the shirt instance turns the whole shirt grey, so do not use it).

## Task
1. Source FBX: `Saved/OfflineIntake/20261017/clean_cast/Sam/Sam_CleanFilm_v01.fbx` (and `Sam_CleanFilm_UE_v01.fbx`). Do not modify them. Work on copies in `Saved/ClinePosing/sam_sleeve/`.
2. In headless Blender (4.5 is installed at `C:\Program Files\Blender Foundation\Blender 4.5`), either
   - offset the **shirt** mesh outward along its vertex normals by 0.3–0.5 cm **in the arms and shoulders only** (use a vertex group / mask so the neckline, hem and cuffs stay put), or
   - delete the **skin** faces that lie fully under the shirt (torso and upper arms), keeping neck, forearms, hands, head.
   Prefer the first; fall back to the second. Keep **identical** vertex order, skin weights, bone names, UVs, material slot order and morph targets on everything you did not intentionally change, or the existing animation assets will break.
3. Export a new FBX, import it headlessly to `/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v02` (new name; never overwrite `_v01`) with the same skeleton (reuse `SK_Sam_Film304_v01_Skeleton` via the import skeleton option) so `AS_Sam_ArmsCrossed`, `AS_Sam_HeldPose_v02` and `AS_Sam_Pose_Shrug` still play on it.
4. Material slots: copy the slot-to-instance mapping from `_v01` (`MI_Film304_Sam_*_Toon`); do not edit any instance.
5. Evidence in `Saved/ClinePosing/sam_sleeve_report.json`: vertex counts before/after per section, max shirt offset in cm and where applied, a check that bone names/hierarchy/skin weights are unchanged, that the three pose assets still reference a compatible skeleton, and the asset path. Do **not** assign the new mesh to any actor; I will do that and screenshot it.
