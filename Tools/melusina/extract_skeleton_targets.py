# Tools/melusina/extract_skeleton_targets.py
import json, re, os

IN = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\skeleton_targets.json"

def decode(name):
    if name is None:
        return None
    name = name.split("|")[-1]
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

def main():
    data = json.load(open(IN, encoding="utf-8"))
    by_name = {}
    for j in data["joints"]:
        name = decode(j["name"])
        by_name[name] = j["translate"]

    spine = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_02", "head"]
    arms = []
    for side in ("l", "r"):
        arms += ["clavicle_%s" % side, "upperarm_%s" % side, "lowerarm_%s" % side, "hand_%s" % side]
    legs = []
    for side in ("l", "r"):
        legs += ["thigh_%s" % side, "calf_%s" % side, "foot_%s" % side, "ball_%s" % side]
    fingers = []
    for side in ("l", "r"):
        for finger in ("thumb", "index", "middle", "ring", "pinky"):
            for seg in ("01", "02", "03"):
                fingers.append("%s_%s_%s" % (finger, seg, side))

    targets = {}
    missing = []
    for name in spine + arms + legs + fingers:
        pos = by_name.get(name)
        if pos is None:
            missing.append(name)
        targets[name] = pos

    result = {
        "units": "cm",
        "up_axis": "y",
        "targets": targets,
        "missing": missing,
        "found_count": len([v for v in targets.values() if v is not None]),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("targets found=%d missing=%d" % (result["found_count"], len(missing)))
    if missing:
        print("missing:", missing)

main()
