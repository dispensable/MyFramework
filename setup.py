# -*- coding:utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

from myframework import __version__

setup(
    name='myframework',
    version=__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['myframework=myframework.main:run']
        },
    install_requires=['docopt>=0.6.2', 'inotify>=0.2.8', 'Mako>=1.0.6', 'schema>=0.6.5'],

    # metadata for upload to PyPI
    author="dispensable",
    author_email="sunsetmask@gmail.com",
    description="A simple but functional Python micro web framework.",
    license="",
    keywords="http web framework",
    url="https://dispensable.github.io/MyFramework",
)
