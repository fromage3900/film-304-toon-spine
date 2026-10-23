"""Consult Jev on the optimal execution order for VFX, Cubicle Labyrinth, and Composed Scenes."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "Docs/HOUDINI_PIPELINE_RESEARCH_AND_PLAN_20261017.md"
OUT = ROOT / "Saved/Audit/HoudiniBrutalist/jev_vfx_composition_review.json"

def main():
    adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
    if not adapter.exists():
        print(f"Error: Jev adapter not found at {adapter}")
        return 1
        
    spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "120"
    
    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else "Film 304 VFX & Set Dressing Execution Plan"
    
    question = (
        "We are staging advanced VFX, set dressing, and composed cinematic cameras in L_Film_Office for Film 304. "
        "The components to be integrated are: "
        "1) Atmospheric VFX: Enable Volumetric Fog on ExponentialHeightFog, configure forward Mie scattering (0.65) and sunbeam volumetric scattering intensity, spawn Niagara floating dust motes catching the louvered light beams, and dial Imperfecter film grain/lens dirt/chromatic fringe; "
        "2) Bureaucratic Cubicle Labyrinth: Stage an extensive cubicle pod hive using SM_CUBICLE_Swarm / SM_CUBICLE_Canonical dressed with desks, task chairs, CRT monitors, lamps, and troffer downlights, then create CineCam_Hero_CubicleEstablishing (24mm, high-angle overhead diagonal looking down into the maze); "
        "3) Breakroom Sanctuary Vignette: Compose the full ZMJ breakroom kit (espresso bar, pastry dome, fridge, dining table, chairs, watercooler, trash/recycle bins, under-cabinet task light) and frame CineCam_Hero_BreakroomEstablishing (35mm); "
        "4) Corridor Watercooler Vignette: Watercooler, potted plant, whiteboard, clock with CineCam_Hero_CorridorWatercooler (50mm). "
        "Select the recommended sequential execution order for staging and validation in Unreal Engine."
    )
    
    options = [
        "VFX_ATMOSPHERE_FIRST__THEN_CUBICLE_LABYRINTH__THEN_BREAKROOM_SANCTUARY__THEN_CORRIDOR_VIGNETTE",
        "CUBICLE_LABYRINTH_FIRST__THEN_BREAKROOM_SANCTUARY__THEN_VFX_ATMOSPHERE__THEN_CORRIDOR_VIGNETTE",
        "BREAKROOM_SANCTUARY_FIRST__THEN_CUBICLE_LABYRINTH__THEN_CORRIDOR_VIGNETTE__THEN_VFX_ATMOSPHERE"
    ]
    
    print("Querying Jev for VFX, Cubicle, and Scene composition order...")
    result = module.jev_ask(question, options, plan_text)
    
    receipt = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest() if PLAN.exists() else "none",
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
