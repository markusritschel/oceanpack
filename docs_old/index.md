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

The routines in this package contain routines for conversion of xCO2 to pCO2, for applying temperature corrections, computing the fugacity, etc.

A full description of the functions and the underlying algorithms can be found in the Module Reference.

## Getting Started

### Installation

#### Install via pip

The easiest way to install the package is via pip directly from this repository:

```bash
$ pip install git+https://github.com/markusritschel/oceanpack.git
```

#### Clone repo and install locally

Alternatively, clone the repo and use the *Make* targets provided.
First, run

```bash
make conda-env
# or alternatively
make install-requirements
```

to install the required packages either via `conda` or `pip`, followed by

```bash
make src-available
```

to make the project's routines (located in `src`) available for import.
This will also give you access to a command line interface (CLI) that can be used for some basic tasks.

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
make tests
```

to run the tests via `pytest`.

## Contact

For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/oceanpack/issues).
