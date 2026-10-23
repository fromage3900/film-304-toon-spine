# Film 304 evening execution plan — 17 October 2026

Owner brief: every film character staged and posed, proper materials and textures,
targeted headless Maya/Houdini/KineFX repairs when demonstrated necessary, and a
film-owned Universal Toon Master with expanded halftone/dither and private Melodia
features surgically removed. First deliverable is a posed cast lineup.

## Responsibility and bounds

Brennan owns cameras, composition, lighting decisions, Sequencer shot framing and
render submission. Codex owns bounded cast repairs, material bindings, pose assets,
shader source/builders and verification. One editor writer at a time. Codex does not
move cameras, change exposure/lights, switch maps, save the composition map, or
start renders while Brennan is composing. Imports and shader compiles use announced
short mutation windows; read-only checks and offline DCC work can proceed alongside
composition. If a render is running, postpone imports/compiles until it completes.

Workspace: G:/film-304-toon-spine, root HumberToonShader.uproject. Do not mutate the
nested project, BS_GodFile, source Maya rigs, source textures or shared upstream
functions. Preserve existing dirty work. No Git staging, commits, cleanup, deployment,
engine rebuild, renderer replacement, new router or general pipeline redesign.

## Ordered work packages and acceptance gates

1. **Baseline and cast lock.** Reconcile specs/cast/cast_rigs.v1.json, the source
   intake and live imported skeletal meshes. Initial known cast: Dana, David, Sam,
   Spider. Record any additional source characters explicitly; never infer completion
   from an old four-character list. Capture actual mesh paths, height/bounds, skeleton,
   section/material names, morphs, UV/texture conventions, current actors and overrides.
   Identify the two Universal assets by full path. Record current shader compile
   status, functions, texture dependencies and instance overrides before edits.
   Gate: every cast member has an explicit readiness row and every blocker has evidence.

2. **Texture and section correctness, one character at a time.** Validate actual skin
   dimensions and tile bindings; clean-named individual 2048-square tiles prevent
   accidental UDIM strip aggregation. Match VT sampler type, sRGB and normal conventions
   to usage. Verify shoes/clothing atlases, iris/sclera/cornea/lashes/teeth/mouth splits.
   Dana v09 is a candidate derived import, not an overwrite of v08. Read independent
   DCC receipts before import; validate new UE sections/morphs and assign every slot.
   Apply the same measured per-face export repair to David/Sam only if needed. Spider
   gets its own measured slot/UV treatment. Source-only diffuse rigs do not magically
   acquire authored normal maps: derived maps stay labelled and are optional polish.
   Gate per character: no null/default/unmatched slots, correct parents and textures
   survive save/readback, and owner-composed close view confirms eyes and skin.

3. **Posed lineup.** Reuse validated skeleton/pose infrastructure. Author one held,
   asymmetric neutral/characterful pose per cast member; ground feet, check silhouette,
   wrists, shoulders, knee direction, eye aim, clipping and the spider's contact legs.
   Use provisional human heights from existing specs, then report measured world bounds;
   do not copy Dana's scale blindly. Create separately named pose assets and expose
   assignments/marks for Brennan's arrangement. Stage only agreed cast actors during a
   short writer window. No auto-layout of Brennan's composition.
   Gate: every locked cast member is present, visibly posed rather than T-posed, grounded,
   textured, readable in the owner's lineup frame. Save only explicitly owned assets;
   Brennan saves the composed map.

4. **Universal surgical trim.** Preserve the exact working source and instance overrides.
   Start from the migrated Universal graph, never substitute the small film master.
   Maintain an explicit KEEP/DROP/REPLACE inventory and output connections. Keep film
   texture/UDIM support, toon ramp/palette, useful rim/sheen, normal/roughness/ORM controls,
   required transparency and print effects. Remove private character/gameplay, elemental,
   celestial/Madoka/Itto/MeshBlend and project-specific MPC/function dependencies from the
   film deliverable through explicit neutral rewires before node deletion. Expand the
   deny list from measured dependencies. No aggressive orphan sweep. Do not delete shared
   functions or original assets. Store changes in a reproducible film-owned builder.
   Gate: compiled output and sample texture paths remain connected; matched-instance
   comparison preserves the base look; recursive delivery closure has no private assets.

5. **Film print controls and clamps.** Add halftone dot size/frequency, coverage,
   rotation, shadow gating, contrast and tint; ordered Bayer and stable noise dither
   modes with strength, scale and seed. Default to deterministic patterns, effects off,
   preserving the baseline look. Use footprint/derivative filtering and distance fade
   where needed; validate moving-camera behavior rather than promising no shimmer.
   Clamp coverage/strength/roughness/metallic to 0..1 in the graph, bound nonzero scales
   and denominator widths, clamp band counts to a supported discrete range, and document
   practical print ranges after observed render tests. Editor slider ranges alone are
   insufficient. Keep exposure/HDR color controls separate from normalized masks.
   Gate: off/default equivalence, endpoints and out-of-range inputs stay finite; sample
   halftone and dither frames read at delivery resolution; short owner-approved motion
   comparison checks temporal stability at the project's actual sampling settings.

6. **Closeout and class delivery.** Re-read saved assignments and pose assets; owner saves
   then reopens the lineup when ready. Build a fresh allowlisted class archive from the
   verified film dependency closure, excluding original Melodia assets/functions/source,
   caches, old archives and unrelated third-party content. Inspect filenames and recursive
   references, hash contents and test archive integrity. Keep license-required dependencies
   explicit. Do not distribute the existing untrimmed Universal shader zip as the new
   class delivery. Record restart/fresh-open results separately from source/editor proof.
   Gate: complete cast matrix, viewed owner-composed lineup and character details, shader
   comparison evidence, clean private-dependency scan, reproducible builders and verified
   delivery archive. Unobserved results remain open, never passed by implication.

## Jev decision boundary

Review the above as a closed choice: CAST_FIRST_THEN_SHADER (steps 1–6 in order),
SHADER_FIRST_THEN_CAST (1,4,5,2,3,6), or HOLD_FOR_MISSING_PREREQUISITES.
Criteria: fastest useful contribution while Brennan composes, single-writer safety,
preservation of working Universal shading, reversible source protection, honest proof
and private dependency exclusion. Save actual Jev source/model/choice/confidence/reason
with the input plan hash. Jev chooses strategy; existing tools execute and verify.

## Stop rule

Complete only when all six acceptance gates pass. Stop expansion at this boundary:
no new shots, environment rebuild, hair/groom redesign, full animation library or game
integration. A failure blocks only its dependent work; progress independent packages.
Current state is recorded in SESSION_HANDOFF_20261017_CAST_WIRING.md and evidence under
Saved/Audit/EveningExecution_20261017, not additional competing status documents.
