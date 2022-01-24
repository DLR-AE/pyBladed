"""
Helper for installing and testing the package.
"""

from distutils.core import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyBladed",
    version="0.1",
    author="Oliver Hach",
    author_email="oliver.hach@dlr.de",
    description="Wrapper to run Bladed simulations and read (binary) results",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DLR-AE/pyBladed",
    packages=['pyBladed', 'pyBladed.model', 'pyBladed.results'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: MS Windows",
    ],
    python_requires='>=3.7',
    install_requires=['numpy>=1.12', 'pytest', 'pythonnet'],
)
