#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging
import re
import uuid

import ldap
import ldap.filter
from ckan.common import session
from ckan.model import Session
from ckan.plugins import toolkit

from ckanext.ldap.lib.exceptions import UserConflictError
from ckanext.ldap.model.ldap_user import LdapUser

log = logging.getLogger(__name__)


def login_failed(notice=None, error=None):
    '''
    Handle login failures. Redirect to /user/login and flash an optional message.

    :param notice: Optional notice for the user (Default value = None)
    :param error: Optional error message for the user (Default value = None)
    '''
    if notice:
        toolkit.h.flash_notice(notice)
    if error:
        toolkit.h.flash_error(error)
    return toolkit.redirect_to('user.login')


def login_success(user_name, came_from):
    '''
    Handle login success. Saves the user in the session and redirects to user/logged_in.

    :param user_name: The user name
    '''
    session['ckanext-ldap-user'] = user_name
    session.save()
    return toolkit.redirect_to('user.logged_in', came_from=came_from)


def get_user_dict(user_id):
    '''
    Calls the action API to get the detail for a user given their id.

    @param user_id: The user id
    '''
    context = {
        'ignore_auth': True
    }
    data_dict = {
        'id': user_id
    }
    return toolkit.get_action('user_show')(context, data_dict)


def ckan_user_exists(user_name):
    '''
    Check if a CKAN user name exists, and if that user is an LDAP user.

    :param user_name: User name to check
    :return: Dictionary defining 'exists' and 'ldap'.
    '''
    try:
        user = get_user_dict(user_name)
    except toolkit.ObjectNotFound:
        return {
            'exists': False,
            'is_ldap': False
        }

    ldap_user = LdapUser.by_user_id(user['id'])
    if ldap_user:
        return {
            'exists': True,
            'is_ldap': True
        }
    else:
        return {
            'exists': True,
            'is_ldap': False
        }


def get_unique_user_name(base_name):
    '''
    Create a unique, valid, non existent user name from the given base name.

    :param base_name: Base name
    :return: A valid user name not currently in use based on base_name
    '''
    base_name = re.sub('[^-a-z0-9_]', '_', base_name.lower())
    base_name = base_name[0:100]
    if len(base_name) < 2:
        base_name = (base_name + '__')[0:2]
    count = 0
    user_name = base_name
    while (ckan_user_exists(user_name))['exists']:
        count += 1
        user_name = '{base}{count}'.format(base=base_name[0:100 - len(str(count))],
                                           count=str(count))
    return user_name


def get_or_create_ldap_user(ldap_user_dict):
    '''
    Get or create a CKAN user from the data returned by the LDAP server.

    :param ldap_user_dict: Dictionary as returned by _find_ldap_user
    :return: The CKAN username of an existing user
    '''
    # Look for existing user, and if found return it.
    ldap_user = LdapUser.by_ldap_id(ldap_user_dict['username'])
    if ldap_user:
        # TODO: Update the user detail.
        return ldap_user.user.name
    user_dict = {}
    update = False
    # Check whether we have a name conflict (based on the ldap name, without mapping
    # it to allowed chars)
    exists = ckan_user_exists(ldap_user_dict['username'])
    if exists['exists'] and not exists['is_ldap']:
        # If ckanext.ldap.migrate is set, update exsting user_dict.
        if not toolkit.config['ckanext.ldap.migrate']:
            raise UserConflictError(toolkit._(
                'There is a username conflict. Please inform the site administrator.'))
        else:
            user_dict = get_user_dict(ldap_user_dict['username'])
            update = True

    # If a user with the same ckan name already exists but is an LDAP user, this means
    # (given that we didn't find it above) that the conflict arises from having mangled
    # another user's LDAP name. There will not however be a conflict based on what is
    # entered in the user prompt - so we can go ahead. The current user's id will just
    # be mangled to something different.

    # Now get a unique user name (if not "migrating"), and create the CKAN user and
    # the LdapUser entry.
    user_name = user_dict['name'] if update else get_unique_user_name(
        ldap_user_dict['username'])
    user_dict.update({
        'name': user_name,
        'email': ldap_user_dict['email'],
        'password': str(uuid.uuid4())
    })
    if 'fullname' in ldap_user_dict:
        user_dict['fullname'] = ldap_user_dict['fullname']
    if 'about' in ldap_user_dict:
        user_dict['about'] = ldap_user_dict['about']
    if update:
        ckan_user = toolkit.get_action('user_update')(
            context={
                'ignore_auth': True
            },
            data_dict=user_dict
        )
    else:
        ckan_user = toolkit.get_action('user_create')(
            context={
                'ignore_auth': True
            },
            data_dict=user_dict
        )
    ldap_user = LdapUser(user_id=ckan_user['id'], ldap_id=ldap_user_dict['username'])
    Session.add(ldap_user)
    Session.commit()
    # Add the user to it's group if needed
    if 'ckanext.ldap.organization.id' in toolkit.config:
        toolkit.get_action('member_create')(
            context={
                'ignore_auth': True
            },
            data_dict={
                'id': toolkit.config['ckanext.ldap.organization.id'],
                'object': user_name,
                'object_type': 'user',
                'capacity': toolkit.config['ckanext.ldap.organization.role']
            }
        )
    return user_name


def check_ldap_password(cn, password):
    '''
    Checks that the given cn/password credentials work on the given CN.

    :param cn: Common name to log on
    :param password: Password for cn
    :return: True on success, False on failure
    '''
    cnx = ldap.initialize(toolkit.config['ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=toolkit.config['ckanext.ldap.trace_level'])
    try:
        cnx.bind_s(cn, password)
    except ldap.SERVER_DOWN:
        log.error('LDAP server is not reachable')
        return False
    except ldap.INVALID_CREDENTIALS:
        log.debug('Invalid LDAP credentials')
        return False
    # Fail on empty password
    if password == '':
        log.debug('Invalid LDAP credentials')
        return False
    cnx.unbind_s()
    return True
