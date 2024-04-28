# type:ignore # noqa: PGH003, INP001
"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

-- Project information -----------------------------------------------------
https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
"""

import os
import sys

from sphinx_pyproject import SphinxConfig

sys.path.insert(0, os.path.abspath("../src"))  # noqa: PTH100
config = SphinxConfig("../pyproject.toml", globalns=globals())


# def setup(app) -> None:
#     """Set up the Sphinx application.

#     Args:
#     ----
#         app: The Sphinx application object.

#     Returns:
#     -------
#         None

#     """
#     app.add_css_file("source/custom.css")
