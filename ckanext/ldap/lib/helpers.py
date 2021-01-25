# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK
from ckan.common import session
from ckan.plugins import toolkit

from urllib.parse import urlparse, parse_qs


def is_ldap_user():
    '''
    Helper function for determining if current user is LDAP user.

    :returns: boolean
    '''
    return 'ckanext-ldap-user' in session


def get_login_action():
    '''
    Returns ldap login handler. Preserves parameter `came_from` as stored in context object's
    login_handler.
    '''
    if hasattr(toolkit.c, 'login_handler'):
        came_from = parse_qs(urlparse(toolkit.c.login_handler).query).get('came_from')
    else:
        came_from = None
    if came_from:
        action = toolkit.url_for('ldap.login_handler', came_from=str(came_from[0]))
    else:
        action = toolkit.url_for('ldap.login_handler')
    return action


def decode_str(s, encoding='utf-8'):
    if isinstance(s, bytes):
        return s.decode(encoding)
    return s
