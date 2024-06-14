# Oceanpack

![build](https://github.com/markusritschel/oceanpack/actions/workflows/main.yml/badge.svg)
[![License MIT license](https://img.shields.io/github/license/markusritschel/oceanpack)](./LICENSE)

**Disclaimer:** This is not an official package. The company SubCtech is not involved in the development of the routines provided here.

This repository contains routines for the evaluation of data from the OceanPack&trade; AUMS (Autonomous Underwater Measuring System) by _SubCtech&reg;_.

The `oceanpack` module contains routines to read-in log files of the OceanPack as well as various helper functions to help with the data processing,
e.g.

- converting coordinates from the Analyzer's format into decimal digits
- converting xCO2 to pCO2
- applying temperature corrections
- computing the fugacity fCO2
- etc.

## Installation

Clone this repo via

```bash
git clone https://github.com/markusritschel/oceanpack
```

Then, in the new directory (`cd oceanpack/`) install the package via:

```bash
pip install .
```

or via

```bash
pip install -e .
```

if you plan to make changes to the code.

Alternatively, install directly from GitHub via

```bash
pip install 'git+https://github.com/markusritschel/oceanpack.git'
```

## Examples

In the subdirectory `notebooks` one can also find a [Jupyter Notebook](https://github.com/markusritschel/oceanpack/blob/master/notebooks/examples.ipynb) showing the usage of the various functions based on a short dataset. 

## Testing

Run `make tests` in the source directory to test the code.
This will execute both the unit tests and docstring examples (using `pytest`).

Run `make lint` to check code style consistency.

## Contact & Issues

For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/oceanpack/issues).

---
&copy; Markus Ritschel 2024
