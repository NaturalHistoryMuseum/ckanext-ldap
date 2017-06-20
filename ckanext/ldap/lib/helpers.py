#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import pylons


def is_ldap_user():
    """
    Help function for determining if current user is LDAP user
    @return: boolean
    """
    #print "Anja is_ldap_user"
    #print pylons.session
    return 'ckanext-ldap-user' in pylons.session
