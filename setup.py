#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

from setuptools import find_packages, setup

__version__ = u'2.0.0-alpha'

with open(u'README.md', u'r') as f:
    __long_description__ = f.read()

setup(
    name=u'ckanext-ldap',
    version=__version__,
    description=u'A CKAN extension that provides LDAP authentication.',
    long_description=__long_description__,
    classifiers=[
        u'Development Status :: 3 - Alpha',
        u'Framework :: Flask',
        u'Programming Language :: Python :: 2.7'
    ],
    keywords=u'CKAN data ldap',
    author=u'Natural History Museum',
    author_email=u'data@nhm.ac.uk',
    url=u'https://github.com/NaturalHistoryMuseum/ckanext-ldap',
    license=u'GNU GPLv3',
    packages=find_packages(exclude=[u'tests']),
    namespace_packages=[u'ckanext', u'ckanext.ldap'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'python-ldap==3.0.0',
        ],
    entry_points= \
        u'''
        [ckan.plugins]
            ldap=ckanext.ldap.plugin:LdapPlugin

        [paste.paster_command]
            ldap=ckanext.ldap.commands.ldap:LDAPCommand
        ''',
    )
