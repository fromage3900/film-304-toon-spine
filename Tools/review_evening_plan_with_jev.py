"""Review the bounded film plan through the existing Jev adapter; no editor writes."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'Docs/EVENING_EXECUTION_PLAN_20261017.md'
OUT = ROOT / 'Saved/Audit/EveningExecution_20261017/jev_plan_review.json'

def main():
    adapter = Path.home() / '.claude/mcp_servers/jev_mcp.py'
    spec = importlib.util.spec_from_file_location('existing_jev_adapter', adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ['JEV_TIMEOUT_SECONDS'] = '55'
    plan = PLAN.read_text(encoding='utf-8')
    options = ['CAST_FIRST_THEN_SHADER', 'SHADER_FIRST_THEN_CAST',
               'HOLD_FOR_MISSING_PREREQUISITES']
    result = module.jev_ask(
        'Select the safest effective execution order for this bounded film plan. '
        'Cast inventory and actual shader graph checks are execution gates, not '
        'claims that repairs already passed. Owner composes renders concurrently.',
        options, plan)
    receipt = {'time_utc': datetime.now(timezone.utc).isoformat(),
               'plan': str(PLAN), 'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
               'options': options, 'judgment': result}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    return 0 if result.get('status') == 'ok' else 1

if __name__ == '__main__':
    raise SystemExit(main())
