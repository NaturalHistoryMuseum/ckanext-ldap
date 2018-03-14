#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

from setuptools import setup, find_packages

version = u'0.1'

setup(
	name=u'ckanext-ldap',
	version=version,
	description=u'CKAN plugin to provide LDAP authentication',
    url=u'https://github.com/NaturalHistoryMuseum/ckanext-ldap',
	packages=find_packages(),
	namespace_packages=[u'ckanext', u'ckanext.ldap'],
	entry_points=u'''
        [ckan.plugins]
            ldap = ckanext.ldap.plugin:LdapPlugin
        [paste.paster_command]
            ldap=ckanext.ldap.commands.ldap:LDAPCommand
	''',
    include_package_data=True,
)
