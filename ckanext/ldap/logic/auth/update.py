#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

from ckan.logic import auth
from ckan.plugins import toolkit
from ckanext.ldap.lib.search import find_ldap_user
from ckanext.ldap.model.ldap_user import LdapUser


@toolkit.chained_auth_function
@toolkit.auth_allow_anonymous_access
def user_update(next_auth, context, data_dict):
    '''
    Ensure LDAP users cannot be edited, and name clash with ldap users.

    :param next_auth: the next auth function in the chain
    :param context:
    :param data_dict:
    '''
    user_obj = None
    try:
        user_obj = auth.get_user_object(context, data_dict)
    except toolkit.ObjectNotFound:
        pass
    # Prevent edition of LDAP users (if so configured)
    if toolkit.config['ckanext.ldap.prevent_edits'] and user_obj and LdapUser.by_user_id(
        user_obj.id):
        return {
            'success': False,
            'msg': toolkit._('Cannot edit LDAP users')
        }
    # Prevent name clashes!
    if 'name' in data_dict and user_obj and user_obj.name != data_dict['name']:
        ldap_user_dict = find_ldap_user(data_dict['name'])
        if ldap_user_dict:
            if (len(user_obj.ldap_user) == 0 or
                    user_obj.ldap_user[0].ldap_id != ldap_user_dict['ldap_id']):
                return {
                    'success': False,
                    'msg': toolkit._('An LDAP user by that name already exists')
                }

    return next_auth(context, data_dict)
