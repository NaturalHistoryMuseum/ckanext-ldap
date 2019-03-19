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
from ckanext.ldap.model.ldap_user import LdapUser
from ckanext.ldap.plugin import config

from ckan.common import session
from ckan.model import Session, User
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


class MultipleMatchError(Exception):
    ''' '''
    pass


class UserConflictError(Exception):
    ''' '''
    pass


class UserController(toolkit.BaseController):
    ''' '''

    def __init__(self):
        ldap.set_option(ldap.OPT_DEBUG_LEVEL, config[u'ckanext.ldap.debug_level'])

    def login_handler(self):
        '''Action called when login in via the LDAP login form'''
        came_from = toolkit.request.params.get(u'came_from', '')
        params = toolkit.request.POST
        if u'login' in params and u'password' in params:
            login = params[u'login']
            password = params[u'password']
            try:
                ldap_user_dict = _find_ldap_user(login)
            except MultipleMatchError as e:
                # Multiple users match. Inform the user and try again.
                return self._login_failed(notice=str(e))
            if ldap_user_dict and _check_ldap_password(ldap_user_dict[u'cn'], password):
                try:
                    user_name = _get_or_create_ldap_user(ldap_user_dict)
                except UserConflictError as e:
                    return self._login_failed(error=str(e))
                return self._login_success(user_name, came_from=came_from)
            elif ldap_user_dict:
                # There is an LDAP user, but the auth is wrong. There could be a
                # CKAN user of the same name if the LDAP user had been created
                # later - in which case we have a conflict we can't solve.
                if config[u'ckanext.ldap.ckan_fallback']:
                    exists = _ckan_user_exists(login)
                    if exists[u'exists'] and not exists[u'is_ldap']:
                        return self._login_failed(error=toolkit._(
                            u'Username conflict. Please contact the site administrator.'))
                return self._login_failed(error=toolkit._(u'Bad username or password.'))
            elif config[u'ckanext.ldap.ckan_fallback']:
                # No LDAP user match, see if we have a CKAN user match
                try:
                    user_dict = _get_user_dict(login)
                    # We need the model to validate the password
                    user = User.by_name(user_dict[u'name'])
                except toolkit.ObjectNotFound:
                    user = None
                if user and user.validate_password(password):
                    return self._login_success(user.name, came_from=came_from)
                else:
                    return self._login_failed(
                        error=toolkit._(u'Bad username or password.'))
            else:
                return self._login_failed(error=toolkit._(u'Bad username or password.'))
        return self._login_failed(
            error=toolkit._(u'Please enter a username and password'))

    def _login_failed(self, notice=None, error=None):
        '''Handle login failures
        
        Redirect to /user/login and flash an optional message

        :param notice: Optional notice for the user (Default value = None)
        :param error: Optional error message for the user (Default value = None)

        '''
        if notice:
            toolkit.h.flash_notice(notice)
        if error:
            toolkit.h.flash_error(error)
        toolkit.redirect_to(controller=u'user', action=u'login')

    def _login_success(self, user_name, came_from):
        '''Handle login success
        
        Saves the user in the session and redirects to user/logged_in

        :param user_name: The user name
        '''
        session[u'ckanext-ldap-user'] = user_name
        session.save()
        toolkit.redirect_to(u'user.logged_in', came_from=came_from)


def _get_user_dict(user_id):
    """Calls the action API to get the detail for a user given their id

    @param user_id: The user id
    """
    context = {u'ignore_auth': True}
    data_dict = {u'id': user_id}
    return toolkit.get_action(u'user_show')(context, data_dict)


def _ckan_user_exists(user_name):
    '''Check if a CKAN user name exists, and if that user is an LDAP user.

    :param user_name: User name to check
    :returns: Dictionary defining 'exists' and 'ldap'.

    '''
    try:
        user = _get_user_dict(user_name)
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


def _get_unique_user_name(base_name):
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
    while (_ckan_user_exists(user_name))[u'exists']:
        count += 1
        user_name = u'{base}{count}'.format(base=base_name[0:100 - len(str(count))],
                                            count=str(count))
    return user_name


def _get_or_create_ldap_user(ldap_user_dict):
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
    exists = _ckan_user_exists(ldap_user_dict[u'username'])
    if exists[u'exists'] and not exists[u'is_ldap']:
        # If ckanext.ldap.migrate is set, update exsting user_dict.
        if not config[u'ckanext.ldap.migrate']:
            raise UserConflictError(toolkit._(
                u'There is a username conflict. Please inform the site administrator.'))
        else:
            user_dict = _get_user_dict(ldap_user_dict[u'username'])
            update=True

    # If a user with the same ckan name already exists but is an LDAP user, this means
    # (given that we didn't find it above) that the conflict arises from having mangled
    # another user's LDAP name. There will not however be a conflict based on what is
    # entered in the user prompt - so we can go ahead. The current user's id will just
    # be mangled to something different.

    # Now get a unique user name (if not "migrating"), and create the CKAN user and
    # the LdapUser entry.
    user_name = user_dict[u'name'] if update else _get_unique_user_name(
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


def _find_ldap_user(login):
    '''Find the LDAP user identified by 'login' in the configured ldap database

    :param login: The login to find in the LDAP database
    :returns: None if no user is found, a dictionary defining 'cn', 'username',
              'fullname' and 'email otherwise.

    '''
    cnx = ldap.initialize(config[u'ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=config[u'ckanext.ldap.trace_level'])
    if config.get(u'ckanext.ldap.auth.dn'):
        try:
            if config[u'ckanext.ldap.auth.method'] == u'SIMPLE':
                cnx.bind_s(config[u'ckanext.ldap.auth.dn'],
                           config[u'ckanext.ldap.auth.password'])
            elif config[u'ckanext.ldap.auth.method'] == u'SASL':
                if config[u'ckanext.ldap.auth.mechanism'] == u'DIGEST-MD5':
                    auth_tokens = ldap.sasl.digest_md5(config[u'ckanext.ldap.auth.dn'],
                                                       config[
                                                           u'ckanext.ldap.auth.password'])
                    cnx.sasl_interactive_bind_s(u'', auth_tokens)
                else:
                    log.error(u'SASL mechanism not supported: {0}'.format(
                        config[u'ckanext.ldap.auth.mechanism']))
                    return None
            else:
                log.error(u'LDAP authentication method is not supported: {0}'.format(
                    config[u'ckanext.ldap.auth.method']))
                return None
        except ldap.SERVER_DOWN:
            log.error(u'LDAP server is not reachable')
            return None
        except ldap.INVALID_CREDENTIALS:
            log.error(
                u'LDAP server credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid')
            return None
        except ldap.LDAPError, e:
            log.error(u'Fatal LDAP Error: {0}'.format(e))
            return None

    filter_str = config[u'ckanext.ldap.search.filter'].format(
        login=ldap.filter.escape_filter_chars(login))
    attributes = [config[u'ckanext.ldap.username']]
    if u'ckanext.ldap.fullname' in config:
        attributes.append(config[u'ckanext.ldap.fullname'])
    if u'ckanext.ldap.email' in config:
        attributes.append(config[u'ckanext.ldap.email'])
    try:
        ret = _ldap_search(cnx, filter_str, attributes, non_unique=u'log')
        if ret is None and u'ckanext.ldap.search.alt' in config:
            filter_str = config[u'ckanext.ldap.search.alt'].format(
                login=ldap.filter.escape_filter_chars(login))
            ret = _ldap_search(cnx, filter_str, attributes, non_unique=u'raise')
    finally:
        cnx.unbind()
    return ret


def _ldap_search(cnx, filter_str, attributes, non_unique=u'raise'):
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
        res = cnx.search_s(config[u'ckanext.ldap.base_dn'], ldap.SCOPE_SUBTREE,
                           filterstr=filter_str, attrlist=attributes)
    except ldap.SERVER_DOWN:
        log.error(u'LDAP server is not reachable')
        return None
    except ldap.OPERATIONS_ERROR as e:
        log.error(
            u'LDAP query failed. Maybe you need auth credentials for performing searches? Error returned by the server: ' + e.info)
        return None
    except (ldap.NO_SUCH_OBJECT, ldap.REFERRAL) as e:
        log.error(
            u'LDAP distinguished name (ckanext.ldap.base_dn) is malformed or does not exist.')
        return None
    except ldap.FILTER_ERROR:
        log.error(u'LDAP filter (ckanext.ldap.search) is malformed')
        return None
    if len(res) > 1 and config[u'ckanext.ldap.use_first'] == False:
        if non_unique == u'log':
            log.error(
                u'LDAP search.filter search returned more than one entry, ignoring. Fix the search to return only 1 or 0 results.')
        elif non_unique == u'raise':
            raise MultipleMatchError(config[u'ckanext.ldap.search.alt_msg'])
        return None
    elif len(res) == 1 or (len(res) >0 and config[u'ckanext.ldap.use_first'] == True):
        cn = res[0][0]
        attr = res[0][1]
        ret = {
            u'cn': cn,
            }

        # Check required fields
        for i in [u'username', u'email']:
            cname = u'ckanext.ldap.' + i
            if config[cname] not in attr or not attr[config[cname]]:
                log.error(u'LDAP search did not return a {}.'.format(i))
                return None
        # Set return dict
        for i in [u'username', u'fullname', u'email', u'about']:
            cname = u'ckanext.ldap.' + i
            if cname in config and config[cname] in attr:
                v = attr[config[cname]]
                if v:
                    ret[i] = _decode_str(v[0])
        return ret
    else:
        return None


def _check_ldap_password(cn, password):
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


def _decode_str(s, encoding=u'utf-8'):
    '''

    :param s: 
    :param encoding:  (Default value = u'utf-8')

    '''
    try:
        # this try throws NameError if this is python3
        if isinstance(s, basestring) and isinstance(s, str):
            return unicode(s, encoding)
    except NameError:
        if isinstance(s, bytes):
            return s.decode(encoding)
    return s
