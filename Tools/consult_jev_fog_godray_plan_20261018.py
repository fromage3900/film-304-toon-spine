"""Consult Jev on the best path to cinematic render quality + godrays in Film 304.

Context is assembled from the real audit findings so the closed candidate set is
grounded in measured project state, not opinion.
"""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved/Audit/Film304_Closeout_20261018/jev_fog_godray_review.json"
ADAPTER = Path.home() / ".claude/mcp_servers/jev_mcp.py"

QUESTION = (
    "Film 304 is a UE5.8 stylized/toon cinematic. We need the best plan for cinematic "
    "render quality and readable godrays. Measured current state:\n"
    "(1) FOG VALUES DRIFT: five scripts write fog_density with five different values "
    "(0.0016 establishing, 0.0018 morning, 0.002 houdini lookdev, 0.003 master showcase, "
    "0.006 city night). fog_max_opacity is written as both 0.92 and 0.65. "
    "fog_height_falloff is 0.12 and 0.08. Re-running any script silently clobbers the "
    "approved look, and nothing detects the conflict.\n"
    "(2) APPROVED-VALUE CLOBBER: volumetric_fog_extinction_scale is hard-coded to 1.2 in two "
    "setup scripts, but our render review tested 4.0 against a prior 2.5 and said keep the "
    "reviewed value only after visual proof. Re-running either script reverts a reviewed value.\n"
    "(3) FRAGILE LOOKUP: four scripts resolve the fog actor with first-match isinstance() with "
    "no assert and no label check. The project was previously bitten by duplicate fog.\n"
    "(4) STATIC vs SEQUENCER CONFLICT: one script writes FogDensity as static editor values, "
    "another writes the same property as a sequencer track default. Winner depends on whether "
    "a shot renders under MRQ.\n"
    "(5) PER-SHOT FOOTGUN: r.VolumetricFog.TemporalReprojection=0 is applied only as an MRQ "
    "console override in one delivery script. It cut loop seam drift 82 percent (wrap MAE "
    "1.8899 to 0.3451). Any new sequence that forgets the override inherits full fog drift.\n"
    "(6) TOON CONFLICT: our own pipeline docs state post-process cel shading and the outline "
    "pass fight fog, bloom and translucency, yet we run forward Mie volumetric scattering at "
    "g=0.65 globally. The audit doc hand-waves this as 'toon tolerates fog if materials are "
    "authored for it' with no rendered proof.\n"
    "(7) GODRAYS: three Film_WindowShaft spotlights (140 candela, 4300K, 1500 atten radius, "
    "11/18 cone, volumetric scattering 6.0, volumetric shadow on) plus a directional SunBeam "
    "at intensity 5.5 with volumetric scattering 3. The lighting audit flags two competing "
    "4-5 intensity directionals in the same toon frame as a likely wash-out.\n"
    "We will not accept a configuration as approved without a rendered side-by-side proof."
    "Choose the single best sequencing approach for reaching cinematic quality and godrays."
)

OPTIONS = [
    "A__LOCK_FOG_SINGLE_SOURCE_OF_TRUTH_FIRST__THEN_FOG_DRIFT_REPORT__THEN_TEMPORAL_REPROJECTION_GLOBAL_DEFAULT__THEN_GODRAY_EXTERIOR_INTERIOR_SPLIT_WITH_RENDERED_A_B",
    "B__GODRAY_LIGHTING_RIG_AND_OUTLINE_CONFLICT_FIRST__THEN_FOG_SOURCE_OF_TRUTH__THEN_A_B_RENDER_PROOF",
    "C__PER_SHOT_LIGHTING_VARIANTS_AND_RENDER_PROOF_FIRST__THEN_FOG_SOURCE_OF_TRUTH_AND_DRIFT_GUARDS__THEN_TEMPORAL_DEFAULT",
    "D__DISABLE_VOLUMETRIC_MIE_FOG_ON_INTERIOR_TOON_SHOTS__KEEP_DISTANCE_ONLY__THEN_FIX_SOURCE_OF_TRUTH__THEN_GODRAY_REBUILD",
]


def main():
    if not ADAPTER.exists():
        print(f"Error: Jev adapter not found at {ADAPTER}")
        return 1

    spec = importlib.util.spec_from_file_location("existing_jev_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "120"

    context = "\n".join(
        [
            (ROOT / "Docs/FILM_PIPELINE.md").read_text(encoding="utf-8"),
            (ROOT / "Docs/SCENE_LIGHTING_AUDIT_20261018.md").read_text(encoding="utf-8"),
            (ROOT / "Docs/HOUDINI_ENGINE_VFX_AND_COMPOSED_STAGING_20261017.md").read_text(encoding="utf-8"),
        ]
    )

    print("Querying Jev for fog + godray sequencing...")
    result = module.jev_ask(QUESTION, OPTIONS, context)

    receipts = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "question": QUESTION,
        "options": OPTIONS,
        "context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
        "judgment": result,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print("--- JEV VERDICT ---")
    print(json.dumps(receipts, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())