# Tools/melusina/filter_inventory.py
# Decode FBX-ASCII names and filter the real character meshes/joints.
import json, re, os

IN = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory.json"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory_summary.json"

def decode(name):
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

def main():
    data = json.load(open(IN, encoding="utf-8"))
    joints = data["joints"]
    decoded_joints = []
    for j in joints:
        decoded_joints.append({
            "encoded": j["name"],
            "name": decode(j["name"]),
            "parent": decode(j["parent"]) if j["parent"] else None,
            "translate": j["translate"],
        })
    name_to_pos = {j["name"]: j["translate"] for j in decoded_joints}
    roots = [j["name"] for j in decoded_joints if j["parent"] is None]

    targets = [
        "root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_02", "head",
        "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
        "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
        "thigh_l", "calf_l", "foot_l", "ball_l",
        "thigh_r", "calf_r", "foot_r", "ball_r",
    ]
    target_positions = {t: name_to_pos.get(t) for t in targets}

    meshes = data["meshes"]
    real_meshes = []
    helper_meshes = []
    for m in meshes:
        dec = decode(m["transform"])
        has_skin = m["skinCluster"] is not None
        has_mat = len(m["material_slots"]) > 0
        row = {
            "encoded": m["transform"],
            "name": dec,
            "vertices": m["vertices"],
            "skinCluster": m["skinCluster"],
            "influence_count": m["influence_count"],
            "material_slots": [decode(s) for s in m["material_slots"]],
            "bbox": m["bbox"],
        }
        if has_skin or has_mat:
            real_meshes.append(row)
        else:
            helper_meshes.append(row)

    summary = {
        "joint_count": data["joint_count"],
        "root_joints": roots,
        "target_positions": target_positions,
        "mesh_count_total": data["mesh_count"],
        "mesh_count_real": len(real_meshes),
        "mesh_count_helper": len(helper_meshes),
        "skinned_count": data["skinned_count"],
        "total_vertices": data["total_vertices"],
        "real_meshes": real_meshes,
        "helper_mesh_sample": helper_meshes[:20],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("SUMMARY joints=%d roots=%d real_meshes=%d helper_meshes=%d skinned=%d" % (
        summary["joint_count"], len(roots), len(real_meshes), len(helper_meshes), summary["skinned_count"]))

main()
