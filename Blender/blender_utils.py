"""Shared probes for the headless Blender entry points.

The identical `set_param` helper used to live once in
`stage_brutalist_review.py` and once in `verify_brutalist_fork.py`. Same
function, two implementations - a fix to one (say, socket-name normalisation)
would silently desync the other, the exact pattern `paris_common.py` was created
to kill for the Paris family. One implementation now; both entry points import
it.

Usage:
    sys.path.insert(0, <this file's directory>)
    from blender_utils import set_param
"""


def set_param(tree, name, value):
    """Set a group-interface INPUT default. Returns True on success.

    Works on the interface item, not the Group Input node socket: on Blender 4+
    the authored default lives on `tree.interface`, and writing the node socket
    reports the type zero back on every read.
    """
    for item in tree.interface.items_tree:
        if (getattr(item, "name", "") == name
                and getattr(item, "in_out", "") == "INPUT"):
            try:
                item.default_value = value
                return True
            except Exception:
                return False
    return False
