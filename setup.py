import sys
from setuptools import setup, find_packages

INSTALL_REQUIRES = ['pytz', 'workalendar']

if sys.version_info < (2, 7):
    INSTALL_REQUIRES += ['backport_collections']

setup(
    name='enerdata',
    version='0.10.0',
    packages=find_packages(),
    url='http://code.gisce.net',
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    install_requires=INSTALL_REQUIRES,
    description=''
)
