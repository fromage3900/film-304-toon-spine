"""Consult Jev on the Office Lookdev Showcase execution plan and audit."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "Docs/GOAL_OFFICE_LOOKDEV_SHOWCASE_20261018.md"
OUT = ROOT / "Saved/Audit/Showcase_20261018/jev_showcase_audit.json"

def main():
    adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
    if not adapter.exists():
        raise FileNotFoundError(f"Jev adapter not found at {adapter}")
    
    spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "55"

    options = [
        "EXECUTE_WINDOW_BACKDROP_THEN_POSES_THEN_CAMERAS_THEN_RENDERS",
        "RENDER_CURRENT_SCENE_BEFORE_BACKDROP_AND_POSE_POLISH",
        "HOLD_FOR_ADDITIONAL_OWNER_INPUT"
    ]

    question = (
        "Evaluate the execution plan for the Film 304 Office Lookdev & Cinematic Showcase Suite in L_Film_Office. "
        "The creative owner requests a polished 3-shot lookdev showcase (Master OTS, Dana Portrait, Low-Angle Desk Rake) "
        "to highlight toon lookdev, physical DOF, and composition. Current scene diagnostics revealed: "
        "1) Window Bay 3 has an exterior sky gap causing a pure white blowout; "
        "2) Venetian blinds are pulled up at ceiling height; "
        "3) Dana is in a basic standing pose while David has an animated sleep pose with snore clouds; "
        "4) Cameras need physical DOF (f/2.5 - f/3.2) and exact framing. "
        "All work is strictly scoped to the active L_Film_Office map with shared toon master shaders frozen. "
        "Select the recommended execution path."
    )

    context = PLAN.read_text(encoding="utf-8")
    print("Querying Jev for lookdev showcase execution order...")
    result = module.jev_ask(question, options, context)

    receipt = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "options": options,
        "judgment": result
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("\n--- JEV VERDICT ---")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    main()
