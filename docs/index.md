![](_static/logo.png)

## Introduction

Welcome to the documentation of Oceanpack!

This repository contains routines for the evaluation of data from the OceanPack™ AUMS (Autonomous Underwater Measuring System) by SubCtech®.

```{tip}
- Give a short introduction on what the package is about.
- Limit yourself to just a few sentences.
- You may also give some instructions on how to navigate through the documentation.
```

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

### Usage

The package can be imported and used as follows:

```python
import oceanpack
```

### Test code

You can run

```bash
make tests
```

to run the tests via `pytest`.


## Contact

For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/oceanpack/issues).
