#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import ckan.logic, ckan.logic.auth
from ckan.common import _
from ckan.logic.auth.create import user_create as ckan_user_create
from ckanext.ldap.controllers.user import _find_ldap_user


@ckan.logic.auth_allow_anonymous_access
def user_create(context, data_dict=None):
    '''

    :param context: 
    :param data_dict:  (Default value = None)

    '''
    if data_dict and u'name' in data_dict:
        ldap_user_dict = _find_ldap_user(data_dict[u'name'])
        if ldap_user_dict:
            return {u'success': False, u'msg': _(u'An LDAP user by that name already exists')}

    return ckan_user_create(context, data_dict)
