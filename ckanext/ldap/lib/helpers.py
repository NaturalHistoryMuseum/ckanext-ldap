# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK
import six
from ckan.common import session
from ckan.plugins import toolkit

if six.PY3:
    from urllib.parse import urlparse, parse_qs
else:
    from urlparse import urlparse, parse_qs


def is_ldap_user():
    '''
    Helper function for determining if current user is LDAP user.

    :returns: boolean
    '''
    return u'ckanext-ldap-user' in session


def get_login_action():
    '''
    Returns ldap login handler. Preserves parameter `came_from` as stored in context object's
    login_handler.
    '''
    if hasattr(toolkit.c, u'login_handler'):
        came_from = parse_qs(urlparse(toolkit.c.login_handler).query).get(u'came_from')
    else:
        came_from = None
    if came_from:
        action = toolkit.url_for(u'ldap.login_handler', came_from=str(came_from[0]))
    else:
        action = toolkit.url_for(u'ldap.login_handler')
    return action


def decode_str(s, encoding=u'utf-8'):
    try:
        # this try throws NameError if this is python3
        if isinstance(s, basestring) and isinstance(s, str):
            return unicode(s, encoding)
    except NameError:
        if isinstance(s, bytes):
            return s.decode(encoding)
    return s
