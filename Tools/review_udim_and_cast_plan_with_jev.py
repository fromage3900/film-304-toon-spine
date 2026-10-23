"""Consult Jev on the UDIM failure recovery plan and architectural next steps."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "Docs/AUDIT_AND_RECOVERY_PLAN_CAST_UDIM_20261017.md"
OUT = ROOT / "Saved/Audit/EveningExecution_20261017/jev_udim_plan_review.json"

def main():
    adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
    spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "120"
    plan = PLAN.read_text(encoding="utf-8")
    
    question = (
        "After graph injection of 3-tile UDIM logic into M_Master_Toon_Universal caused "
        "regressions on Dana's tuned hair and flattened toon cel banding across cast instances, "
        "emergency mitigations restored the live stage (re-bound MI_Dana_Hair on M_Master_Toon_Hair, "
        "re-established RampStrength=0.85, and cleared all dream parameters to 0). "
        "Select the next best architectural path for the Film 304 pipeline."
    )
    
    options = [
        "SPECIALIZED_HAIR_FACE_PLUS_ENCAPSULATED_UDIM_MF",
        "MONOLITHIC_UNIVERSAL_MASTER_CONVERGENCE",
        "DCC_PREBAKED_SINGLE_ATLAS_PIPELINE"
    ]
    
    print("Querying Jev...")
    result = module.jev_ask(question, options, plan)
    
    receipt = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "options": options,
        "judgment": result
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if result.get("status") == "ok" else 1

if __name__ == "__main__":
    raise SystemExit(main())
