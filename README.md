# oceanpack
![build](https://github.com/markusritschel/oceanpack/workflows/build/badge.svg)
[![GitHub license](https://img.shields.io/github/license/markusritschel/oceanpack)](https://github.com/markusritschel/oceanpack/blob/master/LICENSE)
[![codecov](https://codecov.io/gh/markusritschel/oceanpack/branch/master/graph/badge.svg)](https://codecov.io/gh/markusritschel/oceanpack)

**Note:** This is not an official package. The company SubCtech is not involved in the development of the routines provided here. 

This repository contains routines for the evaluation of data from the OceanPack&trade; AUMS (Autonomous Underwater Measuring System) by _SubCtech&reg;_.
The routines were written during my job as research assistant at the Max-Planck-Institute for Meteorology in Hamburg, working in the group of Dr. Peter Landschützer.

The `oceanpack` module containes routines to read-in log files of the OceanPack as well as various helper functions to help with the data processing,
e.g. 
* converting coordinates from the Analyzer's format into decimal digits
* converting xCO2 to pCO2
* applying temperature corrections
* computing the fugacity fCO2
* etc.

In the subdirectory `notebooks` one can also find a [Jupyter Notebook](https://github.com/markusritschel/oceanpack/blob/master/oceanpack/notebooks/examples.ipynb) showing the usage of the various functions based on a short dataset. 

Contact
-------
Feel free to contact me via git@markusritschel.de.
For problems or feature requests please open an [issue](https://github.com/markusritschel/oceanpack/issues).
Of course, you are also welcome to contribute and start a pull-request :-)
