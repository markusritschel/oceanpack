=========
oceanpack
=========

The `oceanpack <https://github.com/markusritschel/oceanpack>`_ package is a collection of routines that help with the quality control and processing of data collected with the OceanPack ferrybox system of SubCtech.

.. note::
    This is **not** an official package. The company SubCtech is not involved in the development of the routines provided here.

The OceanPack system measures underway :math:`CO_2` alongside water temperature, salinity and other parameters.
Data are usually stored on an SD card but can also be streamed to a computer.
The routines in this package contain routines for conversion of xCO2 to pCO2, for applying temperature corrections, computing the fugacity, etc.


A full description of the functions and the underlying algorithms can be found in the Module Reference.

.. TODO: Add a more extensive description here. Maybe include photos/images of the OceanPack etc. Mention any pecularities.


Contribution
============
The entire code is publicly available on `Github <https://github.com/markusritschel/oceanpack>`_.
If you feel like contributing, issues and pull requests are welcome :-)



.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Content

   installation
   examples.ipynb
   License <license>
   Changelog <changelog>


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: API
   
   Module Reference <api/modules>
   genindex
   py-modindex


------------

References
==========
    .. bibliography::



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
