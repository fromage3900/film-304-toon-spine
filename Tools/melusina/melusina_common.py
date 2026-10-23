# Tools/melusina/melusina_common.py
import json, hashlib, os, re, math

def decode_name(name):
    if name is None:
        return None
    name = name.split("|")[-1]
    return re.sub(r"FBXASC(\d{3})", lambda m: chr(int(m.group(1))), name)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def vec_sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

def vec_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]

def vec_scale(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]

def vec_len(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])

def vec_norm(a):
    l = vec_len(a)
    if l < 1e-9:
        return [0.0, 0.0, 0.0]
    return [a[0] / l, a[1] / l, a[2] / l]

def vec_cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]

def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
