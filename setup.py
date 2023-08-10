from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

setup(
    name='hexachromix',
    version='0.1',
    packages=find_packages(),
    ext_modules=cythonize([
        Extension('hexachromix', ['hexachromix.pyx']),
    ]),
)
