import shutil
from pathlib import Path

src = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Content\IMPERFECTER_-_Post_Process_Toolkit_v1.3.1___40_5.6__5.7_\IMPERFECTER_-_Post_Process_Toolkit_v1.3.1___40_5.6__5.7_\IMPERFECTER - Post Process Toolkit v1.3.1 (5.6-5.7)\Imperfecter\Content")
dst = Path(r"G:\film-304-toon-spine\Content\Textures\PostProcess\Imperfecter")

dst.mkdir(parents=True, exist_ok=True)

copied = []
for item in src.rglob("*"):
    if item.is_file():
        rel = item.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append(str(rel))

print(f"Copied {len(copied)} files to {dst}:")
for c in copied:
    print(f"  + {c}")
