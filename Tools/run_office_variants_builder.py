import json
import urllib.request
from pathlib import Path

script_path = str(Path("g:/film-304-toon-spine/Tools/render_establishing_stills.py").resolve()).replace('\\', '/')
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "editor_query",
        "arguments": {
            "action": "run_python",
            "params": {
                "command": f'exec(open("{script_path}").read())'
            }
        }
    }
}

req = urllib.request.Request(
    "http://localhost:9316/mcp",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print(f"Executing {script_path} via Monolith on port 9316...")
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print(json.dumps(res, indent=2))
