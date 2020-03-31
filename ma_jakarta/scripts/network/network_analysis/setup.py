from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("node_dif_cython.pyx")
)
