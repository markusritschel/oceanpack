=========
oceanpack
=========


This is the documentation of the `oceanpack <https://github.com/markusritschel/oceanpack>`_ package.

.. note::
    This is **not** an official package. The company SubCtech is not involved in the development of the routines provided here.


The ``oceanpack`` package containes routines to read-in log files of the OceanPack as well as various helper functions to help with the data processing, e.g.

* converting coordinates from the Analyzer's format into decimal digits
* converting xCO2 to pCO2
* applying temperature corrections
* computing the fugacity fCO2
* etc.


Installation
============
You can install this package on your machine via pip by executing

::

    $ pip install git+https://github.com/markusritschel/oceanpack.git#egg=oceanpack

in your terminal.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   License <license>
   Authors <authors>
   Changelog <changelog>
   examples.ipynb
   Module Reference <api/modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _toctree: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _references: http://www.sphinx-doc.org/en/stable/markup/inline.html
.. _Python domain syntax: http://sphinx-doc.org/domains.html#the-python-domain
.. _Sphinx: http://www.sphinx-doc.org/
.. _Python: http://docs.python.org/
.. _Numpy: http://docs.scipy.org/doc/numpy
.. _SciPy: http://docs.scipy.org/doc/scipy/reference/
.. _matplotlib: https://matplotlib.org/contents.html#
.. _Pandas: http://pandas.pydata.org/pandas-docs/stable
.. _Scikit-Learn: http://scikit-learn.org/stable
.. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _NumPy style: https://numpydoc.readthedocs.io/en/latest/format.html
.. _classical style: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists
