# Oceanpack

![build](https://github.com/markusritschel/oceanpack/workflows/build/badge.svg)
[![License MIT license](https://img.shields.io/github/license/markusritschel/oceanpack)](./LICENSE)


This repository contains routines for the evaluation of data from the OceanPack™ AUMS (Autonomous Underwater Measuring System) by SubCtech®.


## Installation
Clone this repo via
```bash
git clone https://github.com/markusritschel/oceanpack
```
Then, in the new directory (`cd oceanpack/`) install the package via:
```
pip install .
```
or via
```
pip install -e .
```
if you plan on making changes to the code.

Alternatively, install directly from GitHub via
```
pip install 'git+https://github.com/markusritschel/oceanpack.git'
```

## Testing
Run `make tests` in the source directory to test the code.
This will execute both the unit tests and docstring examples (using `pytest`).

Run `make lint` to check code style consistency.



## Maintainer
- [markusritschel](https://github.com/markusritschel)


## Contact & Issues
For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/oceanpack/issues).


---
&copy; Markus Ritschel 2024
