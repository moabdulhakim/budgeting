# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
import django
sys.path.insert(0, os.path.abspath('../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

# -- Project information -----------------------------------------------------
project = 'Spendo'
copyright = '2026, F-S-Sh-M'
author = 'F-S-Sh-M'
release = '.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      
    'sphinx.ext.viewcode',    
    'sphinx.ext.napoleon',     
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']


html_theme_options = {
    "repository_url": "https://github.com/moabdulhakim/budgeting", 
    "use_repository_button": True,
    "use_download_button": True,
    "header_links_before_dropdown": 4,
    "show_navbar_depth": 2,
    "toc_title": "On this page", 
}




