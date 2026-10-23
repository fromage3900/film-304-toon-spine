import sys
import json
import urllib.request
from pathlib import Path

def run_ue_script(script_path):
    p = Path(script_path).resolve()
    code = f'exec(open("{p.as_posix()}").read())'
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "editor_query",
            "arguments": {
                "action": "run_python",
                "params": {"command": code}
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
                    try:
                        text_data = json.loads(item["text"])
                        if "output" in text_data and text_data["output"]:
                            for entry in text_data["output"]:
                                print(entry.get("output", ""))
                        else:
                            print("Result:", text_data.get("result"))
                            if "error" in text_data:
                                print("Error:", text_data.get("error"))
                    except:
                        print(item["text"])
        else:
            print(res)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_ue_script(sys.argv[1])
    else:
        print("Usage: python run_ue_script.py <path_to_script.py>")
