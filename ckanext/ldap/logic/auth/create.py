#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

from ckan.plugins import toolkit
from ckanext.ldap.lib.search import find_ldap_user


@toolkit.chained_auth_function
@toolkit.auth_allow_anonymous_access
def user_create(next_auth, context, data_dict=None):
    '''
    :param next_auth: the next auth function in the chain
    :param context:
    :param data_dict:  (Default value = None)
    '''
    if data_dict and u'name' in data_dict:
        ldap_user_dict = find_ldap_user(data_dict[u'name'])
        if ldap_user_dict:
            return {
                u'success': False,
                u'msg': toolkit._(u'An LDAP user by that name already exists')
            }

    return next_auth(context, data_dict)
