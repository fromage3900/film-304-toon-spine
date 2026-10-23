# Tools/melusina/find_def_joints.py
import json, re, os

IN = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\def_joints.json"

def decode(name):
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

data = json.load(open(IN, encoding="utf-8"))
defs = []
for j in data["joints"]:
    name = decode(j["name"])
    if name.startswith("DEF_"):
        defs.append({
            "name": name,
            "parent": decode(j["parent"]) if j["parent"] else None,
            "translate": j["translate"],
        })

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"count": len(defs), "joints": defs}, f, indent=2)

print("DEF joints:", len(defs))
chain = [
    "DEF_pelvis", "DEF_spine_01", "DEF_spine_02", "DEF_spine_03", "DEF_neck_02", "DEF_head",
    "DEF_clavicle_l", "DEF_upperarm_l", "DEF_lowerarm_l", "DEF_hand_l",
    "DEF_clavicle_r", "DEF_upperarm_r", "DEF_lowerarm_r", "DEF_hand_r",
    "DEF_thigh_l", "DEF_calf_l", "DEF_foot_l", "DEF_ball_l",
    "DEF_thigh_r", "DEF_calf_r", "DEF_foot_r", "DEF_ball_r",
]
by_name = {d["name"]: d for d in defs}
for c in chain:
    d = by_name.get(c)
    if d:
        print(c, "parent:", d["parent"], "pos:", [round(v, 2) for v in d["translate"]])
    else:
        print(c, "MISSING")
