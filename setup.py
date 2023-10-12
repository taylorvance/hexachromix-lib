from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

setup(
    name='hexachromix',
    version='0.2.4',
    description='Hexachromix',
    author='Taylor Vance',
    author_email='mirrors.cities0w@icloud.com',
    packages=find_packages(),
    install_requires=[
        'cython<4.0.0',
        'multimcts==0.6.4',
        'fastapi',
        'uvicorn',
        'psutil',
    ],
    entry_points={
        'console_scripts': ['hexachromix-cli=hexachromix.cli:main'],
    },
    ext_modules=cythonize([
        Extension('hexachromix.core', ['hexachromix/core.pyx']),
    ]),
)
