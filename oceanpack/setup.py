# TODO: follow https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html
from setuptools import find_packages, setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


TEST_REQUIRES = ["pytest"]

INSTALL_REQUIRES = ['numpy',
                    'pandas']

AUTHOR = "Markus Ritschel"
AUTHOR_EMAIL = "kontakt@markusritschel.de"


setup(name='oceanpack',
      version='0.1',
      description='Routines for working with the log files of the subCtech OceanPack',
      long_description=long_description,
      url='http://github.com/markusritschel/oceanpack',
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      install_requires=INSTALL_REQUIRES,
      tests_require=TEST_REQUIRES,
      # py_modules=["cdo"],
      # python_requires=['>=3.6']
      )
