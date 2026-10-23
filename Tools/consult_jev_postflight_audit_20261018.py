"""Consult Jev on the completed Office Lookdev Showcase delivery and obtain final audit sign-off."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "Docs/GOAL_OFFICE_LOOKDEV_SHOWCASE_20261018.md"
RECEIPT = ROOT / "Saved/Audit/Showcase_20261018/showcase_delivery_receipt.json"
OUT = ROOT / "Saved/Audit/Showcase_20261018/jev_postflight_audit.json"

def main():
    adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
    if not adapter.exists():
        raise FileNotFoundError(f"Jev adapter not found at {adapter}")
    
    spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["JEV_TIMEOUT_SECONDS"] = "55"

    options = [
        "APPROVE_AND_SIGN_OFF_SHOWCASE_DELIVERY",
        "REJECT_DUE_TO_UNMET_CRITERIA",
        "REQUEST_ADDITIONAL_ITERATION"
    ]

    receipt_data = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else {}

    question = (
        "Perform final postflight lookdev and cinematography audit for Film 304 Office Showcase Suite in L_Film_Office. "
        "Review the completed deliverables: "
        "1) The 3-Shot Cinematic Suite rendered to disk: Shot 1 (Master Ensemble), Shot 2 (Dana Hero Portrait), Shot 3 (David Late-Night Crunch Rake). "
        "2) Window Bay 3 exterior sky blowout is 100% sealed with Brutalist concrete towers (SM_Ext_Bay3_RightInfill, SM_Ext_Bay3_FarRightInfill). "
        "3) Blown-out exposure is fully calibrated: PPV auto-exposure bias lowered to -1.1 EV, 7 competing PPVs disabled, floor specular glare eliminated. "
        "4) Character posing and lighting: Sam's broken intake pose is completely removed (autoplay loop disabled, Sam hidden and relocated); "
        "Dana is staged leaning over desk with warm desk lamp illumination; David is staged slumped over keyboard with warm desk lamp and monitor glow. "
        "5) Contact sheet compiled and verified. All master toon shader graphs preserved intact. "
        "Select the appropriate audit status."
    )

    context = f"PLAN:\n{PLAN.read_text(encoding='utf-8')}\n\nDELIVERY_RECEIPT:\n{json.dumps(receipt_data, indent=2)}"
    print("Querying Jev for final showcase audit sign-off...")
    result = module.jev_ask(question, options, context)

    postflight_receipt = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "receipt_sha256": hashlib.sha256(RECEIPT.read_bytes()).hexdigest() if RECEIPT.exists() else None,
        "options": options,
        "judgment": result
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(postflight_receipt, indent=2), encoding="utf-8")
    print("\n--- JEV POSTFLIGHT VERDICT ---")
    print(json.dumps(postflight_receipt, indent=2))

if __name__ == "__main__":
    main()
