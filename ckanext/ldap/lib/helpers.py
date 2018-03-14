
#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import pylons


def is_ldap_user():
    '''Help function for determining if current user is LDAP user


    :returns: boolean

    '''

    return u'ckanext-ldap-user' in pylons.session
