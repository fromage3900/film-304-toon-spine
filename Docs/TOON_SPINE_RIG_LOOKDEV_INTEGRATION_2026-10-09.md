# FILM-304 — Rig/FBX to UE5.8 Toon Spine Lookdev Convergence
**Plan date:** 2026-10-09 | **Owner:** Brennan | **Repo:** `fromage3900/film-304-toon-spine` | **Target:** prove the currently staged updated film rig and FBX animation in one lookdev prototype

## Mission
Audit local G: stage against the current film `main`, identify the *updated rig actually present* (not an assumed GitHub copy), validate FBX animation against its intended UE Skeleton (`SK_*`), then connect it to **existing** toon materials and deliver judged character + animation lookdev frames. **Do not start a new shader architecture.**

**Recommended frontier:** GPT-6 Codex (or existing Codex agent) as UE5.8/Python import/build integration owner; Claude Sonnet 5.5 can review visual artifacts once there is a usable capture. **Recon:** DeepSeek V4.1 Flash for G:/P4/Git + rig manifests and headless Blender report.

## Current GitHub baseline (2026-10-08; local may be ahead)
- `Docs/HANDOFF_2026-10-08_NEXT_PHASE.md`: builder-generated film material core landed; verified spine build PASS, 15-master/12-function fresh-load compile checks and `Tools/verify_all.ps1` 9/9. These are baseline results, **not** live checks of today's imported rig.
- Existing staging: `Python/build_shot_stage.py`, `specs/office_spider/stage_shots.v1.json`, `L_Toon_Shot_Office`, `Python/render_prototypes.py` request override. Reuse rather than generate a competing capture tool.
- `Docs/TOON_SPINE.md`, `Docs/MATERIAL_WIRING_PLAN.md`, `Docs/CONTENT_CONVENTIONS.md` and `Docs/GROUP_STAGING_GUIDE.md` govern assets. Preserve separate `M_Outline_InvertedHull` path and source-driven builders.
- Known prior issue: on one laptop a texture could load as 32×32 default vs 256×256 in-process; workstation Shader Model 6/Substrate render support and two pre-existing staging-slot naming failures were open. **Do not confuse these with the new rig's defects**. First verify machine and scope.
- GitHub search does **not** prove the updated rig/FBX is present in tracked `main`; local G: owner evidence must decide.

## Stage T0 — Flash convergence sweep (read-only)
1. `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git worktree list`, `git lfs ls-files`; check P4 opens if used, and identify the exact G: project root. Inventory unsaved/ignored FBXs, source `.blend`, rig/animation assets and their dependencies by mtime/hash. No pull/revert/checkout of dirty files.
2. Diff local staged material builder scripts/config and `.uasset` references against GitHub `main`. Classify: ALREADY CANON / UNCOMMITTED OWNER / OTHER AGENT / STALE / UNKNOWN. Do not sweep unrelated assets.
3. Make a **headless Blender 5.2 audit on a copy** of the intended source rig/FBX: armature names, deform bone hierarchy, action names/ranges/FPS, transforms, root/root-motion, bind pose, object and action scales, forward/up axis, vertex weights and animation channel coverage. Capture errors and a neutral + posed viewport preview if reproducible.
4. Produce `Saved/Audit/film_rig_toon_20261009/recon.json`, minimal diff/manifest and 3 prioritized execution candidates. Name intended UE SK and AnimBP from **observed local objects**, not guessed names.

## Stage T1 — FBX → Skeleton truth table
- Compare FBX bone hierarchy, bind pose, root, rotation order, unit conversion, frame rate and action sampling to target `SK_*`. Check whether current import uses the *correct intended skeleton* and whether the deformation is an import-axis / reference-pose / animation curve problem.
- Prefer existing rig/SK/IK pipeline; create a new skeleton ONLY with explicit owner decision and a proven incompatibility. Avoid deleting/replacing shared film group skeletons or touching Melusina game's `SK_Melusina_Skeleton`.
- Select **one** representative animated clip and one neutral pose for a full UE import → Sequencer/AnimBP playback comparison; fix observed bind pose, bone mapping, transform, scale, root motion or frame sampling one at a time. Track import settings and original FBX hash.
- `UnrealEditor-Cmd.exe` probes are allowed when no competing editor owns the same assets; final deformation proof requires UI render/Sequencer playback, not successful importer return alone.

## Stage T2 — first judged lookdev prototypes
- Use `M_Master_Toon_Character` or existing correct character/face/hair master instances and Toon Profiles, preserving their builder-generated dependency graph. Do **not** copy a new master into film.
- Set up 3 compact representative tests: **neutral rig/material lineup**, **one animated acting pose**, **one film shot with existing key/fill/rim + inverted-hull outline**. Show front/three-quarter profile and a silhouette/texture closeup if it reveals defects.
- Render on known-compatible SM6 workstation if laptop cannot render Substrate; label each capture with host/GPU, renderer, resolution, frame, SK, FBX/action hash, material instance, Toon Profile, and source camera.
- Check banding/normal transitions, outline weight, skin/cloth/hair separation, specular behavior, UV distortion, animation silhouette, and material shimmer over time. Don't let compositing or untracked lookdev overlays fake material quality.

## Stage T3 — validation / canonical landing
- Run `Tools/verify_all.ps1`, relevant spine/fresh-load compile and targeted film import/animation checks. Record **new** PASS/FAIL; distinguish pre-existing laptop texture and owner staging-slot failures rather than asserting a global green.
- Deliver immutable evidence: `Saved/Audit/film_rig_toon_20261009/` import settings, one JSON bone/action report, 3 labeled stills, short playback, script/version hashes, and a minimal proposed diff.
- **Acceptance:** intended skeleton reused; selected clip plays without bad bone twist/root scale/contact pops; 3 judged toon renders show correct material/profile/outline; no duplicate master or redundant SK; no pre-existing film assets overwritten; checks explicitly reported.
- **Fallback for today:** if actual rig remains unavailable or incompatible, deliver standalone rig root-cause table + a material prototype on an already-valid existing mesh. Do not claim animation integration.
- Commit only lane-owned additions after owner's review via isolated branch/PR following film group guide. Never silently push binaries from G: or mix unrelated school members' files.

## Cost / concurrency contract (all lanes)

1. **Flash read-only reconnaissance, then frontier intervention.** Use DeepSeek V4.1 Flash (`deepseek-flash`) or an already-paid low-cost model. Bound reconnaissance to 1 repo search + 1 local filesystem inventory + 1 targeted report; max ~15 tool invocations; no binary mutation, UE editor launch, shader rebuilding, file deletion, P4 submit, or commits. Cap output to 1-2 pages and machine-readable candidate files. Do not dump whole logs or old plans into the frontier model's context.
2. Hand the expensive agent: (a) current head SHA + branch/worktree, (b) `git status --short` and P4 opens when relevant, (c) exact absolute paths *as locally observed*, (d) authoritative references / conflicts, (e) prioritized defects with evidence and confidence, (f) exact next runnable commands and rollback path. Mark **UNKNOWN** rather than inventing data.
3. Only one writer per `.blend` or UE `.uasset` / level at a time. Work on a new generation or isolated worktree / `refs/agents/<lane>`; never overwrite an open scene, force-push, merge another agent's branch, bulk-delete assets, or submit unrelated P4 changelists.
4. Run bounded **inventory → one fix → test → evidence → next fix**. Two unsuccessful attempts on the same issue trigger a documented blocker and owner review, not a token-expensive loop. Restrict frontier context to the current lane's evidence packet and relevant files.
5. CI/headless checks establish structure only; *visual* success requires inspected images / video and *UE* gameplay success requires actual editor/PIE playback where specified. Never report success from a manifest alone.
6. `G:` is local storage, not accessible through this GitHub-only plan authoring session. The local reconnaissance agent must resolve G: against its own running machine and report `unavailable` if not mounted. Never confuse a GitHub snapshot with current disk or P4 state.

## Frontier handoff prompt
> Execute ONLY the film rig/FBX to toon-spine lane described here. Use the Flash-generated G: inventory and Blender 5.2 skeleton/action report first. Treat the existing 2026-10-08 material builder spine and render harness as canon. Prove one imported FBX animation on the intended UE Skeleton, then deliver neutral / acting / in-shot Substrate Toon lookdev captures with exact hashes, material names, before/after evidence and fresh-load checks. No speculative new masters, SK duplication, unrelated film asset overwrites or unapproved P4 submit.

## Cross-project boundary
This is the `film-304-toon-spine` group repository. The separate `MelodiaMelusinaV2` runtime animation cleanup and Shorewake school animatic are not part of this write lane.
