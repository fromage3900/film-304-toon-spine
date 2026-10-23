import json
import urllib.request

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "editor_query",
        "arguments": {
            "action": "run_python",
            "params": {
                "command": 'exec(open("G:/film-304-toon-spine/Tools/check_current_map.py").read())'
            }
        }
    }
}

req = urllib.request.Request(
    "http://localhost:9316/mcp",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print(json.dumps(res, indent=2))
