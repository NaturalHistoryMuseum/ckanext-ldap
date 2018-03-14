# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

from ckan.common import session


def is_ldap_user():
    '''Helper function for determining if current user is LDAP user


    :returns: boolean

    '''

    return u'ckanext-ldap-user' in session
