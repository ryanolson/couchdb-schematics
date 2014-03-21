# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~~~~~

    :author: Ryan Olson
    :copyright: (c) 2013 Ryan Olson
    :license: Apache v2, see LICENSE for more details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from setuptools import setup

test_requirements=[
    'pytest'
]

setup(
    name='couchdb-schematics',
    license='BSD',
    version='1.1.0',
    author='Ryan Olson',
    author_email='rmolson@gmail.com',
    description='',
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
        'CouchDB',
        'schematics',
    ] + test_requirements,
    dependency_links = [
    ]
)
