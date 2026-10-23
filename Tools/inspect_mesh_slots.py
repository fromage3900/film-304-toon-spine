import json
import urllib.request

script = """
import unreal

def inspect_assets():
    mesh_paths = [
        # Brutalist
        "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
        "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock",
        "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TightEstate",
        "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_LowSprawl",
        "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster",
        "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_CivicSuperblock",
        "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale",
        "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
        "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab",
        "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_Bunker",
        "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical",
        "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift",
        "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_OpenPlan",
        "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Swarm",
        "/Game/Meshes/Office/Props/Desk",
        "/Game/Meshes/Office/Props/DeskDrawers",
        "/Game/Meshes/Office/Props/P_Chair_KS",
        "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016"
    ]
    results = {}
    for p in mesh_paths:
        sm = unreal.EditorAssetLibrary.find_asset_data(p).get_asset()
        if sm and isinstance(sm, unreal.StaticMesh):
            slots = []
            for i in range(sm.get_num_sections(0) if hasattr(sm, 'get_num_sections') else len(sm.static_materials)):
                mat = sm.get_material(i)
                slot_name = sm.static_materials[i].material_slot_name if i < len(sm.static_materials) else f"slot_{i}"
                slots.append({
                    "slot_index": i,
                    "slot_name": str(slot_name),
                    "default_material": mat.get_path_name() if mat else None
                })
            results[p] = {"num_materials": len(sm.static_materials), "slots": slots}
        else:
            results[p] = "NOT_FOUND"

    print("MESH_SLOTS_JSON_START")
    print(json.dumps(results))
    print("MESH_SLOTS_JSON_END")

inspect_assets()
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
