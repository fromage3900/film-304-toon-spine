# Tools/melusina/find_roots.py
import json, re

IN = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"

def decode(name):
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

data = json.load(open(IN, encoding="utf-8"))
joint_names = {decode(j["name"]) for j in data["joints"]}
roots = []
for j in data["joints"]:
    parent = decode(j["parent"]) if j["parent"] else None
    if parent is None or parent not in joint_names:
        roots.append({"name": decode(j["name"]), "parent": parent, "translate": j["translate"]})

print("joint_count", data["joint_count"])
print("hierarchy_roots", len(roots))
for r in roots:
    print(r["name"], "| parent:", r["parent"], "| pos:", [round(v, 2) for v in r["translate"]])
