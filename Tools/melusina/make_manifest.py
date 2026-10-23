# Tools/melusina/make_manifest.py
import json, hashlib, os, datetime

ROOT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1"
OUT = os.path.join(ROOT, "MANIFEST.json")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    entries = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            entries.append({
                "path": rel,
                "size_bytes": os.path.getsize(path),
                "sha256": sha256(path),
            })
    entries.sort(key=lambda e: e["path"])
    manifest = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "root": ROOT,
        "file_count": len(entries),
        "files": entries,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("MANIFEST WRITTEN", len(entries), "files")

main()
