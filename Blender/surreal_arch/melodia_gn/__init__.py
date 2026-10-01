"""BRUTALIST subset of the Melodia GN builder package, vendored for the 304 film project.

Source: P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/__init__.py

The upstream __init__ imports ~100 builder modules plus the studio stack UI.
This fork registers ONLY the brutalist family and then calls
core._rebuild_derived_data() — the same call the source makes once all builders
have registered, so the TREE_* lookup tables match what is registered here.
"""
from __future__ import annotations

from .core import _rebuild_derived_data

from . import (  # noqa: F401 - each module calls core.register_builder on import
    brutalist_city,
    brutalist_cubicles,
    brutalist_materials,
    brutalist_office,
    brutalist_roofs,
    brutalist_uv,
)

_rebuild_derived_data()
