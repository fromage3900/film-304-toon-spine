import urllib.request
import json
import sys

def run_ue(code_str):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "editor_query",
            "arguments": {
                "action": "run_python",
                "params": {"command": code_str}
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
        if "result" in res and "content" in res["result"]:
            for item in res["result"]["content"]:
                if item.get("type") == "text":
                    print(item.get("text"))
        else:
            print(res)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_ue(sys.argv[1])
    else:
        print("Usage: python run_ue.py '<python code>'")
