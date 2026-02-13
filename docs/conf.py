project = 'Oceanpack'
author = 'Markus Ritschel'

# Minimal Sphinx config to allow building with myst-parser
extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinxcontrib.bibtex',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', '_autoapi']

master_doc = 'index'

# HTML
html_theme = 'furo'

# MyST settings
myst_enable_extensions = [
    'amsmath',
    'attrs_inline',
    'colon_fence',
    'deflist',
    'dollarmath',
    'fieldlist',
    'html_admonition',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Bibliography
bibtex_bibfiles = ['references.bib']
bibtex_reference_style = 'author_year'

