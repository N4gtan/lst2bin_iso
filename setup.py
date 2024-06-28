# This setup is for compiling the Cython .pyx file into a .so (or .pyd on Windows) module
# Install Cython with pip: pip install cython
# Then run the following command: python setup.py build_ext --inplace
from setuptools import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize("edc_ecc.pyx"))
