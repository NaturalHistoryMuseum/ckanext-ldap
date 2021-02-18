# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging

import ldap
from ckanext.ldap.lib import helpers
from ckanext.ldap.lib.exceptions import MultipleMatchError

from ckan.plugins import toolkit

log = logging.getLogger(u'ckanext.ldap')


def find_ldap_user(login):
    '''Find the LDAP user identified by 'login' in the configured ldap database

    :param login: The login to find in the LDAP database
    :returns: None if no user is found, a dictionary defining 'cn', 'username',
              'fullname' and 'email otherwise.

    '''
    cnx = ldap.initialize(toolkit.config[u'ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=toolkit.config[u'ckanext.ldap.trace_level'])
    cnx.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
    if toolkit.config.get(u'ckanext.ldap.auth.dn'):
        try:
            if toolkit.config[u'ckanext.ldap.auth.method'] == u'SIMPLE':
                cnx.bind_s(toolkit.config[u'ckanext.ldap.auth.dn'],
                           toolkit.config[u'ckanext.ldap.auth.password'])
            elif toolkit.config[u'ckanext.ldap.auth.method'] == u'SASL':
                if toolkit.config[u'ckanext.ldap.auth.mechanism'] == u'DIGEST-MD5':
                    auth_tokens = ldap.sasl.digest_md5(toolkit.config[u'ckanext.ldap.auth.dn'],
                                                       toolkit.config[
                                                           u'ckanext.ldap.auth.password'])
                    cnx.sasl_interactive_bind_s(u'', auth_tokens)
                else:
                    log.error(u'SASL mechanism not supported: {0}'.format(
                        toolkit.config[u'ckanext.ldap.auth.mechanism']))
                    return None
            else:
                log.error(u'LDAP authentication method is not supported: {0}'.format(
                    toolkit.config[u'ckanext.ldap.auth.method']))
                return None
        except ldap.SERVER_DOWN:
            log.error(u'LDAP server is not reachable')
            return None
        except ldap.INVALID_CREDENTIALS:
            log.error(
                u'LDAP server credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) '
                u'invalid')
            return None
        except ldap.LDAPError as e:
            log.error(u'Fatal LDAP Error: {0}'.format(e))
            return None

    filter_str = toolkit.config[u'ckanext.ldap.search.filter'].format(
        login=ldap.filter.escape_filter_chars(login))
    attributes = [toolkit.config[u'ckanext.ldap.username']]
    if u'ckanext.ldap.fullname' in toolkit.config:
        attributes.append(toolkit.config[u'ckanext.ldap.fullname'])
    if u'ckanext.ldap.email' in toolkit.config:
        attributes.append(toolkit.config[u'ckanext.ldap.email'])
    try:
        ret = ldap_search(cnx, filter_str, attributes, non_unique=u'log')
        if ret is None and u'ckanext.ldap.search.alt' in toolkit.config:
            filter_str = toolkit.config[u'ckanext.ldap.search.alt'].format(
                login=ldap.filter.escape_filter_chars(login))
            ret = ldap_search(cnx, filter_str, attributes, non_unique=u'raise')
    finally:
        cnx.unbind()
    return ret


def ldap_search(cnx, filter_str, attributes, non_unique=u'raise'):
    '''Helper function to perform the actual LDAP search

    :param cnx: The LDAP connection object
    :param filter_str: The LDAP filter string
    :param attributes: The LDAP attributes to fetch. This *must* include self.ldap_username
    :param non_unique: What to do when there is more than one result. Can be either
                       'log' (log an error and return None - used to indicate that this
                       is a configuration problem that needs to be address by the site
                       admin, not by the current user) or 'raise' (raise an exception
                       with a message that will be displayed to the current user - such
                       as 'please use your unique id instead'). Other values will
                       silently ignore the error. (Default value = u'raise')
    :returns: A dictionary defining 'cn', self.ldap_username and any other attributes
              that were defined in attributes; or None if no user was found.

    '''
    try:
        res = cnx.search_s(toolkit.config[u'ckanext.ldap.base_dn'], ldap.SCOPE_SUBTREE,
                           filterstr=filter_str, attrlist=attributes)
    except ldap.SERVER_DOWN:
        log.error(u'LDAP server is not reachable')
        return None
    except ldap.OPERATIONS_ERROR as e:
        log.error(
            u'LDAP query failed. Maybe you need auth credentials for performing searches? Error '
            u'returned by the server: ' + str(e))
        return None
    except (ldap.NO_SUCH_OBJECT, ldap.REFERRAL) as e:
        log.error(
            u'LDAP distinguished name (ckanext.ldap.base_dn) is malformed or does not exist.')
        return None
    except ldap.FILTER_ERROR:
        log.error(u'LDAP filter (ckanext.ldap.search) is malformed')
        return None
    if len(res) > 1:
        if non_unique == u'log':
            log.error(
                u'LDAP search.filter search returned more than one entry, ignoring. Fix the '
                u'search to return only 1 or 0 results.')
        elif non_unique == u'raise':
            raise MultipleMatchError(toolkit.config[u'ckanext.ldap.search.alt_msg'])
        return None
    elif len(res) == 1:
        cn = res[0][0]
        attr = res[0][1]
        ret = {
            u'cn': cn,
            }

        # Check required fields
        for i in [u'username', u'email']:
            cname = u'ckanext.ldap.' + i
            if toolkit.config[cname] not in attr or not attr[toolkit.config[cname]]:
                log.error(u'LDAP search did not return a {}.'.format(i))
                return None
        # Set return dict
        for i in [u'username', u'fullname', u'email', u'about']:
            cname = u'ckanext.ldap.' + i
            if cname in toolkit.config and toolkit.config[cname] in attr:
                v = attr[toolkit.config[cname]]
                if v:
                    ret[i] = helpers.decode_str(v[0])
        return ret
    else:
        return None
