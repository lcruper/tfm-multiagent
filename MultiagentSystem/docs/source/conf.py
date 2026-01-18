# Configuration file for the Sphinx documentation builder.

from __future__ import annotations
import sys
from pathlib import Path

# ============================================================
# Path setup
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Project information
# ============================================================

project = "Multiagent Drone and Robot Dog System"
author = "Lidia Cruz Pérez"
copyright = "2026, lidia"

# ============================================================
# General configuration
# ============================================================

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.inheritance_diagram",
]

templates_path = ["_templates"]
exclude_patterns = []

add_module_names = False
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# ============================================================
# Napoleon settings (Google-style docstrings)
# ============================================================

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# ============================================================
# HTML output
# ============================================================

html_theme = "furo"
html_static_path = ["_static"]

# Personalización opcional
html_css_files = ["css/custom.css"]
html_js_files = ["js/custom.js"]

language = "en"

# ============================================================
# Misc
# ============================================================

# Show warnings for broken references
nitpicky = False