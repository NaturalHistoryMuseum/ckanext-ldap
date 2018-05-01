#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
Amended: hvw / 2018
"""

import pylons
from ckan.plugins.toolkit import c

try:
    # In case we are running Python3
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


def is_ldap_user():
    """
    Help function for determining if current user is LDAP user
    @return: boolean
    """

    return 'ckanext-ldap-user' in pylons.session


def get_login_action():
    ''' Returns ldap login handler. Preserves parameter `came_from`
    as stored in context object's login_handler.

    '''
    lh = c.login_handler
    camefrom = parse_qs(urlparse(lh).query).get('came_from')
    if camefrom:
        action = "/ldap_login_handler?came_from=" + camefrom[0]
    else:
        action = "/ldap_login_handler"
    return action 
