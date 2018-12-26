#!/usr/bin/env python3

"""
Python setuptools install script.

Usage:
$ python setup.py install               # install globally
$ python setup.py install --user        # install for user
$ python setup.py test                  # run test suite
$ python setup.py develop               # install symlink for development
$ python setup.py develop --uninstall   # uninstall for development
"""

from setuptools import setup
from album_rsync._version import __version__

with open('README.md') as f:
    readme = f.read()    # pylint: disable=invalid-name

setup(
    name='album-rsync',
    version=__version__,
    description='A python script to manage synchronising a local directory of photos with a remote service based on an rsync interaction pattern',
    long_description=readme,
    author='Paul Heasley',
    author_email='paul@phdesign.com.au',
    url='http://www.phdesign.com.au/album-rsync',
    download_url=f'https://github.com/phdesign/album-rsync/archive/v{__version__}.tar.gz',
    packages=['album_rsync'],
    license='MIT',
    keywords=['flickr', 'sync', 'rsync', 'photo', 'media', 'google', 'photos'],
    install_requires=[
        'flickr_api',
        'rx',
        'backoff'
    ],
    dependency_links=[
        'git+git://github.com/alexis-mignon/python-flickr-api@65effbe#egg=flickr_api'
    ],
    setup_requires=['pytest-runner', 'pytest-pylint'],
    tests_require=['pytest', 'pylint'],
    zip_safe=True,
    entry_points={
        'console_scripts': ['album-rsync=album_rsync:main'],
    },
    include_package_data=True
)
