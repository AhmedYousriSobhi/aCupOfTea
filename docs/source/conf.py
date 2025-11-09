# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Imports
import os
import sys

# Add project root to sys.path so we can reference top-level folders
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'aCupOfTea'
copyright = '2025, Ahmed Yousri Sobhi'
author = 'Ahmed Yousri Sobhi'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_nb', # Enable markdown parsing
    ]

nb_execution_mode = "off"   # or "auto", "cache", etc.

templates_path = ['_templates']
exclude_patterns = []

# Let Sphinx find Markdown files
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
