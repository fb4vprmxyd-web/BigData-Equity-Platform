"""Sphinx configuration for the Code Documentation appendix."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "CW2 — Code Documentation"
copyright = "2026, Team 09 — UCL IFT"
author = "Team 09"
release = "2.8.0"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Number figures and tables for cross-references
numfig = True
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
    "code-block": "Listing %s",
}

# Lightweight theme that prints cleanly (no sidebar, no JS-heavy chrome)
html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = False
html_show_copyright = False
html_show_sphinx = False

html_theme_options = {
    "fixed_sidebar": False,
    "show_relbars": False,
    "show_powered_by": False,
    "page_width": "920px",
    "sidebar_width": "0",
    "body_max_width": "auto",
    "nosidebar": True,
}
html_sidebars = {"**": []}
