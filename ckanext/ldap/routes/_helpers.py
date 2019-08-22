#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging
import uuid

import ldap
import ldap.filter
import re
from ckanext.ldap.lib.exceptions import UserConflictError
from ckanext.ldap.model.ldap_user import LdapUser
from ckanext.ldap.plugin import config

from ckan.common import session
from ckan.model import Session
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


def login_failed(notice=None, error=None):
    '''Handle login failures

    Redirect to /user/login and flash an optional message

    :param notice: Optional notice for the user (Default value = None)
    :param error: Optional error message for the user (Default value = None)

    '''
    if notice:
        toolkit.h.flash_notice(notice)
    if error:
        toolkit.h.flash_error(error)
    toolkit.redirect_to(u'user.login')


def login_success(user_name, came_from):
    '''Handle login success

    Saves the user in the session and redirects to user/logged_in

    :param user_name: The user name
    '''
    session[u'ckanext-ldap-user'] = user_name
    session.save()
    toolkit.redirect_to(u'user.logged_in', came_from=came_from)


def get_user_dict(user_id):
    """Calls the action API to get the detail for a user given their id

    @param user_id: The user id
    """
    context = {
        u'ignore_auth': True
        }
    data_dict = {
        u'id': user_id
        }
    return toolkit.get_action(u'user_show')(context, data_dict)


def ckan_user_exists(user_name):
    '''Check if a CKAN user name exists, and if that user is an LDAP user.

    :param user_name: User name to check
    :returns: Dictionary defining 'exists' and 'ldap'.

    '''
    try:
        user = get_user_dict(user_name)
    except toolkit.ObjectNotFound:
        return {
            u'exists': False,
            u'is_ldap': False
            }

    ldap_user = LdapUser.by_user_id(user[u'id'])
    if ldap_user:
        return {
            u'exists': True,
            u'is_ldap': True
            }
    else:
        return {
            u'exists': True,
            u'is_ldap': False
            }


def get_unique_user_name(base_name):
    '''Create a unique, valid, non existent user name from the given base name

    :param base_name: Base name
    :returns: A valid user name not currently in use based on base_name

    '''
    base_name = re.sub(u'[^-a-z0-9_]', u'_', base_name.lower())
    base_name = base_name[0:100]
    if len(base_name) < 2:
        base_name = (base_name + u'__')[0:2]
    count = 0
    user_name = base_name
    while (ckan_user_exists(user_name))[u'exists']:
        count += 1
        user_name = u'{base}{count}'.format(base=base_name[0:100 - len(str(count))],
                                            count=str(count))
    return user_name


def get_or_create_ldap_user(ldap_user_dict):
    '''Get or create a CKAN user from the data returned by the LDAP server

    :param ldap_user_dict: Dictionary as returned by _find_ldap_user
    :returns: The CKAN username of an existing user

    '''
    # Look for existing user, and if found return it.
    ldap_user = LdapUser.by_ldap_id(ldap_user_dict[u'username'])
    if ldap_user:
        # TODO: Update the user detail.
        return ldap_user.user.name
    user_dict = {}
    update = False
    # Check whether we have a name conflict (based on the ldap name, without mapping
    # it to allowed chars)
    exists = ckan_user_exists(ldap_user_dict[u'username'])
    if exists[u'exists'] and not exists[u'is_ldap']:
        # If ckanext.ldap.migrate is set, update exsting user_dict.
        if not config[u'ckanext.ldap.migrate']:
            raise UserConflictError(toolkit._(
                u'There is a username conflict. Please inform the site administrator.'))
        else:
            user_dict = get_user_dict(ldap_user_dict[u'username'])
            update = True

    # If a user with the same ckan name already exists but is an LDAP user, this means
    # (given that we didn't find it above) that the conflict arises from having mangled
    # another user's LDAP name. There will not however be a conflict based on what is
    # entered in the user prompt - so we can go ahead. The current user's id will just
    # be mangled to something different.

    # Now get a unique user name (if not "migrating"), and create the CKAN user and
    # the LdapUser entry.
    user_name = user_dict[u'name'] if update else get_unique_user_name(
        ldap_user_dict[u'username'])
    user_dict.update({
        u'name': user_name,
        u'email': ldap_user_dict[u'email'],
        u'password': str(uuid.uuid4())
        })
    if u'fullname' in ldap_user_dict:
        user_dict[u'fullname'] = ldap_user_dict[u'fullname']
    if u'about' in ldap_user_dict:
        user_dict[u'about'] = ldap_user_dict[u'about']
    if update:
        ckan_user = toolkit.get_action(u'user_update')(
            context={
                u'ignore_auth': True
                },
            data_dict=user_dict
            )
    else:
        ckan_user = toolkit.get_action(u'user_create')(
            context={
                u'ignore_auth': True
                },
            data_dict=user_dict
            )
    ldap_user = LdapUser(user_id=ckan_user[u'id'], ldap_id=ldap_user_dict[u'username'])
    Session.add(ldap_user)
    Session.commit()
    # Add the user to it's group if needed
    if u'ckanext.ldap.organization.id' in config:
        toolkit.get_action(u'member_create')(
            context={
                u'ignore_auth': True
                },
            data_dict={
                u'id': config[u'ckanext.ldap.organization.id'],
                u'object': user_name,
                u'object_type': u'user',
                u'capacity': config[u'ckanext.ldap.organization.role']
                }
            )
    return user_name


def check_ldap_password(cn, password):
    '''Checks that the given cn/password credentials work on the given CN.

    :param cn: Common name to log on
    :param password: Password for cn
    :returns: True on success, False on failure

    '''
    cnx = ldap.initialize(config[u'ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=config[u'ckanext.ldap.trace_level'])
    try:
        cnx.bind_s(cn, password)
    except ldap.SERVER_DOWN:
        log.error(u'LDAP server is not reachable')
        return False
    except ldap.INVALID_CREDENTIALS:
        log.debug(u'Invalid LDAP credentials')
        return False
    # Fail on empty password
    if password == u'':
        log.debug(u'Invalid LDAP credentials')
        return False
    cnx.unbind_s()
    return True
