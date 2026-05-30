## Introduction

Welcome to the documentation of [oceanpack](https://github.com/markusritschel/oceanpack)!

This package is a collection of routines that help with the quality control and processing of data collected with the OceanPack ferrybox system of SubCtech.

```{admonition} Disclaimer
:class: warning

This is **not** an official package. The company SubCtech is not involved in the development of the routines provided here.
```

```{admonition} About the system
:class: seealso

The OceanPack system by SubCtech is a modular and customizable solution designed for real-time monitoring and analysis of various oceanographic parameters.

The system can be tailored to meet specific research or operational needs by integrating different sensors and modules.
It provides continuous real-time data on a variety of parameters such as temperature, salinity, CO2, etc.
Data are usually stored on an SD card but can also be streamed to a computer.
```

The package provides routines for conversion of xCO2 to pCO2, for applying temperature corrections, computing the fugacity, etc.

A full description of the functions and the underlying algorithms can be found in the Module Reference.

## Getting Started

### Installation

After cloning the repository, you can install the package in your environment.
The recommended way to install is via [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
```

This installs all dependencies and makes the project's source code (located in `src`) available for import.
Then activate the virtual environment:

```bash
source .venv/bin/activate
```

Alternatively, add directly from GitHub to an existing project:

```bash
uv add git+https://github.com/markusritschel/oceanpack.git
```


### Usage

The package can be imported and used as follows:

```python
import oceanpack
```

In addition, you will have access to a [command line interface (CLI)](cli.md) that you can run from the terminal:

```bash
oceanpack --help
```

### Test code

You can run
```bash
just test
```
to run the tests.


## Contact

For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/oceanpack/issues).


```{toctree}
:hidden:
:caption: About

workflow
cli
```

```{toctree}
:hidden:

:caption: Main navigation
example
```


```{toctree}
:hidden:
:caption: Project information

api/index
bibliography
README <readme>
LICENSE <license>
CHANGELOG <changelog>
```
