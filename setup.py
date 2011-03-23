#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import codecs

if os.path.exists('README.rst'):
    long_description = codecs.open('README.rst', 'r', 'utf-8').read()
else:
    long_description = 'See http://github.com/AIFDR/riab'


setup(
    name='riab',
    version=0.1,
    description='Risk In a Box',
    author='Ted Dunstone, Ole Nielsen, Ariel Nunez, David Winslow',
    author_email='',
    url='http://riskinabox.org',
    platforms=['any'],
    license='GPL',
    packages=packages,
    data_files=data_files,
    zip_safe=False,
    install_requires=[
        'riab_geonode', 
        'riab_server',
        'sphinx',
        ],

    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: System :: Distributed Computing',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    long_description=long_description,
)
