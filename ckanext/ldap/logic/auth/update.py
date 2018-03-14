#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import ckan.logic, ckan.logic.auth
from ckan.common import _
from ckan.logic.auth.update import user_update as ckan_user_update
from ckanext.ldap.plugin import config
from ckanext.ldap.model.ldap_user import LdapUser
from ckanext.ldap.controllers.user import _find_ldap_user

@ckan.logic.auth_allow_anonymous_access
def user_update(context, data_dict):
    '''Ensure LDAP users cannot be edited, and name clash with ldap users

    :param context: 
    :param data_dict: 

    '''
    user_obj = None
    try:
        user_obj = ckan.logic.auth.get_user_object(context, data_dict)
    except ckan.logic.NotFound:
        pass
    # Prevent edition of LDAP users (if so configured)
    if config[u'ckanext.ldap.prevent_edits'] and user_obj and LdapUser.by_user_id(user_obj.id):
        return {u'success': False, u'msg': _(u'Cannot edit LDAP users')}
    # Prevent name clashes!
    if u'name' in data_dict and user_obj and user_obj.name != data_dict[u'name']:
        ldap_user_dict = _find_ldap_user(data_dict[u'name'])
        if ldap_user_dict:
            if len(user_obj.ldap_user) == 0 or user_obj.ldap_user[0].ldap_id != ldap_user_dict[u'ldap_id']:
                return {u'success': False, u'msg': _(u'An LDAP user by that name already exists')}

    return ckan_user_update(context, data_dict)
