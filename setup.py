# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from enerdata import __version__

with open('requirements.txt', 'r') as f:
    requirements = f.readlines()

PACKAGES_DATA = {'enerdata': ['profiles/data/*.csv', 'profiles/data/*.xlsx']}

setup(
    name='enerdata',
    version=__version__,
    description='A set of energy models',
    provides=['enerdata'],
    packages=find_packages(),
    package_data=PACKAGES_DATA,
    install_requires=requirements,
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    url='http://code.gisce.net',
)
