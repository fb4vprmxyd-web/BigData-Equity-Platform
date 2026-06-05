"""Sphinx configuration for CW2 Value-Sentiment Investment Strategy documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Value-Sentiment Investment Strategy"
copyright = "2026, Team 09 — UCL IFT"
author = "Team 09"
release = "2.8.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "*.pdf"]

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

todo_include_todos = True
