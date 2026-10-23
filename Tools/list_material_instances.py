import json
import urllib.request

script = """
import unreal

eal = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# Find all MaterialInstances in the project
assets = eal.list_assets("/Game/Materials/Instances", recursive=True, include_folder=False)
results = []
for a in assets:
    results.append(a)

office_mats = eal.list_assets("/Game/Materials", recursive=True, include_folder=False)
filtered_office = [m for m in office_mats if "Office" in m or "Film" in m or "Desk" in m or "Brutalist" in m]

print("ALL_INSTANCES_START")
print(json.dumps({"instances": results, "office_materials": filtered_office}))
print("ALL_INSTANCES_END")
"""

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "editor_query",
        "arguments": {
            "action": "run_python",
            "params": {"command": script}
        }
    }
}
req = urllib.request.Request("http://localhost:9316/mcp", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    txt = res["result"]["content"][0]["text"]
    print(txt)
