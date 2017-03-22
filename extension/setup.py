from setuptools import setup, Extension

lcs = Extension('lcs', sources=["lcs.c"])
setup(ext_modules=[lcs])
