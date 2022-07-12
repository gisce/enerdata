# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from enerdata import __version__

with open('requirements.txt', 'r') as f:
    requirements = f.readlines()

setup(
    name='enerdata',
    version=__version__,
    description='A set of energy models',
    provides=['enerdata'],
    packages=find_packages(),
    install_requires=requirements,
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    url='http://code.gisce.net',
)
