# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in nbp_exchange_rate/__init__.py
from nbp_exchange_rate import __version__ as version

setup(
	name='nbp_exchange_rate',
	version=version,
	description='Replaces standard get_exchange_rate with custom function getting exchange rates from api.nbp.pl',
	author='Levitating Frog',
	author_email='none',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
