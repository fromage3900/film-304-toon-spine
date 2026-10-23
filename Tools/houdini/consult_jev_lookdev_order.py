"""Consult Jev on the optimal execution order for cinematic Houdini lookdev and geometry bakes."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "Docs/HOUDINI_PIPELINE_RESEARCH_AND_PLAN_20261017.md"
OUT = ROOT / "Saved/Audit/HoudiniBrutalist/jev_lookdev_execution_review.json"

def main():
    adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
    if not adapter.exists():
        print(f"Error: Jev adapter not found at {adapter}")
        return 1
        
    spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "120"
    
    plan_text = PLAN.read_text(encoding="utf-8")
    
    question = (
        "We are executing cinematic lookdev and procedural Houdini Engine bakes for Film 304 in L_Film_Office. "
        "The current active stage has 5 upright Brutalist skyline towers with window slots visible out the office window, "
        "and CineCam_Hero_WindowEstablishing (28mm) framing Dana and David. "
        "To make these renders look straight out of a high-end film (Mielgo / Deakins chiaroscuro), we are implementing: "
        "1) Film noir light-slicing window louvers / venetian blinds on the window bays to project dramatic shadow stripes on the characters; "
        "2) Rooftop crowns, plant decks, HVAC, and radio spires with aviation lights to detail the skyline silhouette; "
        "3) Living window lighting variation (warm 3200K vs cool 6500K fluorescent interior glow) in MI_Film304_BrutalistGlazing; "
        "4) Catenary industrial powerlines draped across building alleys. "
        "Select the safest, most visually impactful sequential execution order to implement in the active Unreal level."
    )
    
    options = [
        "BLINDS_SHADOWS_FIRST__THEN_ROOFS_SPIRES__THEN_WINDOW_LIGHTING__THEN_CATENARY_CABLES",
        "ROOFS_SPIRES_FIRST__THEN_BLINDS_SHADOWS__THEN_WINDOW_LIGHTING__THEN_CATENARY_CABLES",
        "WINDOW_LIGHTING_FIRST__THEN_ROOFS_SPIRES__THEN_BLINDS_SHADOWS__THEN_CATENARY_CABLES"
    ]
    
    print("Querying Jev for architectural execution order...")
    result = module.jev_ask(question, options, plan_text)
    
    receipt = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "question": question,
        "options": options,
        "judgment": result
    }
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("\n--- JEV VERDICT ---")
    print(json.dumps(receipt, indent=2))
    return 0 if result.get("status") == "ok" else 1

if __name__ == "__main__":
    raise SystemExit(main())
