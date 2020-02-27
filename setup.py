import sys
from setuptools import setup, find_packages

PACKAGES_DATA = {'enerdata': ['profiles/data/*.xlsx']}

INSTALL_REQUIRES = ['pytz', 'workalendar<8.0.0']

if sys.version_info < (2, 7):
    INSTALL_REQUIRES += ['backport_collections']

setup(
    name='enerdata',
    version='0.21.0',
    packages=find_packages(),
    url='http://code.gisce.net',
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    install_requires=INSTALL_REQUIRES,
    package_data=PACKAGES_DATA,
    description='A set of energy models'
)
