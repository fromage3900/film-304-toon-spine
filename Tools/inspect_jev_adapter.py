import importlib.util
from pathlib import Path

adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("Module attributes:")
for k in dir(module):
    if not k.startswith("__"):
        print(f"  {k}: {getattr(module, k)}")
