#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

test_requirements=[
    'pytest'
]

setup(
    name='couchdb-schematics',
    license='BSD',
    version='0.1.0-beta',
    description='',
    author=u'',
    author_email='',
    url='http://github.com/ryanolson/couchdb-schematics',
    packages=['couchdb_schematics'],
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
    tests_require=test_requirements,
    install_requires=[
        'setuptools>=0.8',
        'schematics>=0.9.1-alpha',
        'CouchDB'
    ] + test_requirements,
    dependency_links = [
        'https://github.com/ryanolson/schematics/tarball/master#egg=schematics-0.9.1-alpha'
    ]
)
