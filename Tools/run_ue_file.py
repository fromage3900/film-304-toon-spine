"""Run a Python file inside the live Unreal Editor via the Monolith bridge on 9316.

    python Tools/run_ue_file.py Python/audit_fog_drift.py

Fallback for Tools/mcp_exec.ps1, which talks to the Claireon MCP on 62468. When the
editor restarts, Claireon can be down while Monolith's editor_query on 9316 stays up,
so keep both paths available.

Mirrors the `exec(open(...).read())` pattern already used by
Tools/run_inspect_monolith.py.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINTS = (
    ("monolith", "http://127.0.0.1:9316/mcp"),
    ("claireon", "http://127.0.0.1:62468/mcp"),
)


def _post(endpoint, script_path, extra_args):
    # Forward any extra CLI args into the executed script's sys.argv, so a single
    # editor-resident script can be run in several modes without one file per mode.
    preamble = ""
    if extra_args:
        import json as _json

        preamble = f"import sys as _sys; _sys.argv = [{_json.dumps(script_path)}"
        preamble += "".join(f", {_json.dumps(a)}" for a in extra_args)
        preamble += "]\n"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "editor_query",
            "arguments": {
                "action": "run_python",
                "params": {
                    "command": preamble + f'exec(open(r"{script_path}").read())'
                },
            },
        },
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if len(sys.argv) < 2:
        print("Usage: python Tools/run_ue_file.py <script.py> [more.py ...]")
        return 2

    failures = []
    targets = sys.argv[1:]
    # Treat trailing non-path arguments as args for the script, not scripts to run.
    scripts = [t for t in targets if Path(t).suffix == ".py" or Path(t).is_file()]
    extra = [t for t in targets if t not in scripts]

    if not scripts:
        print("Usage: python Tools/run_ue_file.py <script.py> [script args...]")
        return 2

    for target in scripts:
        script_path = str(Path(target).resolve())
        if not Path(script_path).is_file():
            print(f"MISSING: {script_path}")
            failures.append(target)
            continue

        for name, endpoint in ENDPOINTS:
            try:
                result = _post(endpoint, script_path, extra)
            except (urllib.error.URLError, OSError) as exc:
                print(f"[{name}] {target}: unavailable ({exc.__class__.__name__})")
                continue

            print(f"[{name}] {target}")
            if isinstance(result, dict):
                content = (result.get("result") or {}).get("content") or []
                for item in content:
                    if item.get("type") == "text":
                        print(item.get("text"))
                if result.get("error"):
                    print("MCP_ERROR:", json.dumps(result["error"])[:2000])
                    failures.append(target)
            else:
                print(json.dumps(result, indent=2)[:4000])
            break
        else:
            failures.append(target)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())