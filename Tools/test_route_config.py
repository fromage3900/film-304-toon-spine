import importlib.util
from pathlib import Path
import os

adapter = Path.home() / ".claude/mcp_servers/jev_mcp.py"
spec = importlib.util.spec_from_file_location("existing_jev_adapter", adapter)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("route_config:", module.route_config())
print("get_nous_key:", bool(module.get_nous_key()))
