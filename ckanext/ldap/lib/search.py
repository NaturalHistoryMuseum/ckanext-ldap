# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging

import ldap
from ckan.plugins import toolkit
from ckanext.ldap.lib import helpers
from ckanext.ldap.lib.exceptions import MultipleMatchError

log = logging.getLogger('ckanext.ldap')


def find_ldap_user(login):
    '''
    Find the LDAP user identified by 'login' in the configured ldap database.

    :param login: The login to find in the LDAP database
    :returns: None if no user is found, a dictionary defining 'cn', 'username', 'fullname' and
              'email' otherwise.
    '''
    cnx = ldap.initialize(toolkit.config['ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=toolkit.config['ckanext.ldap.trace_level'])
    cnx.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
    if toolkit.config.get('ckanext.ldap.auth.dn'):
        try:
            if toolkit.config['ckanext.ldap.auth.method'] == 'SIMPLE':
                cnx.bind_s(toolkit.config['ckanext.ldap.auth.dn'],
                           toolkit.config['ckanext.ldap.auth.password'])
            elif toolkit.config['ckanext.ldap.auth.method'] == 'SASL':
                if toolkit.config['ckanext.ldap.auth.mechanism'] == 'DIGEST-MD5':
                    auth_tokens = ldap.sasl.digest_md5(toolkit.config['ckanext.ldap.auth.dn'],
                                                       toolkit.config['ckanext.ldap.auth.password'])
                    cnx.sasl_interactive_bind_s('', auth_tokens)
                else:
                    log.error(f'SASL mechanism not supported: '
                              f'{toolkit.config["ckanext.ldap.auth.mechanism"]}')
                    return None
            else:
                log.error(f'LDAP authentication method is not supported: '
                          f'{toolkit.config["ckanext.ldap.auth.method"]}')
                return None
        except ldap.SERVER_DOWN:
            log.error('LDAP server is not reachable')
            return None
        except ldap.INVALID_CREDENTIALS:
            log.error('LDAP server credentials (ckanext.ldap.auth.dn and '
                      'ckanext.ldap.auth.password) invalid')
            return None
        except ldap.LDAPError as e:
            log.error(f'Fatal LDAP Error: {e}')
            return None

    filter_str = toolkit.config['ckanext.ldap.search.filter'].format(
        login=ldap.filter.escape_filter_chars(login))
    attributes = [toolkit.config['ckanext.ldap.username']]
    if 'ckanext.ldap.fullname' in toolkit.config:
        attributes.append(toolkit.config['ckanext.ldap.fullname'])
    if 'ckanext.ldap.email' in toolkit.config:
        attributes.append(toolkit.config['ckanext.ldap.email'])
    try:
        ret = ldap_search(cnx, filter_str, attributes, non_unique='log')
        if ret is None and 'ckanext.ldap.search.alt' in toolkit.config:
            filter_str = toolkit.config['ckanext.ldap.search.alt'].format(
                login=ldap.filter.escape_filter_chars(login))
            ret = ldap_search(cnx, filter_str, attributes, non_unique='raise')
    finally:
        cnx.unbind()
    return ret


def ldap_search(cnx, filter_str, attributes, non_unique='raise'):
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
                       silently ignore the error. (Default value = 'raise')
    :returns: A dictionary defining 'cn', self.ldap_username and any other attributes
              that were defined in attributes; or None if no user was found.

    '''
    try:
        res = cnx.search_s(toolkit.config['ckanext.ldap.base_dn'], ldap.SCOPE_SUBTREE,
                           filterstr=filter_str, attrlist=attributes)
    except ldap.SERVER_DOWN:
        log.error('LDAP server is not reachable')
        return None
    except ldap.OPERATIONS_ERROR as e:
        log.error(f'LDAP query failed. Maybe you need auth credentials for performing searches? '
                  f'Error returned by the server: {e}')
        return None
    except (ldap.NO_SUCH_OBJECT, ldap.REFERRAL) as e:
        log.error(
            'LDAP distinguished name (ckanext.ldap.base_dn) is malformed or does not exist.')
        return None
    except ldap.FILTER_ERROR:
        log.error('LDAP filter (ckanext.ldap.search) is malformed')
        return None
    if len(res) > 1:
        if non_unique == 'log':
            log.error(
                'LDAP search.filter search returned more than one entry, ignoring. Fix the '
                'search to return only 1 or 0 results.')
        elif non_unique == 'raise':
            raise MultipleMatchError(toolkit.config['ckanext.ldap.search.alt_msg'])
        return None
    elif len(res) == 1:
        cn = res[0][0]
        attr = res[0][1]
        ret = {
            'cn': cn,
        }

        # Check required fields
        for i in ['username', 'email']:
            cname = 'ckanext.ldap.' + i
            if toolkit.config[cname] not in attr or not attr[toolkit.config[cname]]:
                log.error('LDAP search did not return a {}.'.format(i))
                return None
        # Set return dict
        for i in ['username', 'fullname', 'email', 'about']:
            cname = f'ckanext.ldap.{i}'
            if cname in toolkit.config and toolkit.config[cname] in attr:
                v = attr[toolkit.config[cname]]
                if v:
                    ret[i] = helpers.decode_str(v[0])
        return ret
    else:
        return None
