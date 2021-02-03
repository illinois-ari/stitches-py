from glob import glob
import importlib
import logging
import os
import sys
import subprocess
import typing as t

from setuptools import find_packages, setup
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

logger = logging.getLogger(__name__)

##############################
#   Setup
##############################

# Find pacakges in project
pkgs = find_packages(exclude=['tests'])

r_map: t.Dict[t.Type, t.Set] = dict() # Resource Map
r_types = dict()

for p in pkgs:
    pass

entry_points = dict()
entry_points['console_scripts'] = ['stitches-py = stitches_py.cli:cli_group']


args =  dict(
    name='stitches-py',
    version='0.0.0',
    packages=pkgs,
    ext_modules=list(),
    cmdclass=dict(),
    zip_safe=True,
    entry_points=entry_points,
    setup_requires=[
        'pydantic',
        'typing_inspect'
    ],
    install_requires=[],
    tests_require=[]
)


setup(**args)