#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging

from ckanext.ldap import routes
from ckanext.ldap.lib.helpers import get_login_action, is_ldap_user
from ckanext.ldap.logic.auth.create import user_create
from ckanext.ldap.logic.auth.update import user_update
from ckanext.ldap.model.ldap_user import setup as model_setup

from ckan.common import session
from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit

log = logging.getLogger(__name__)


class ConfigError(Exception):
    ''' '''
    pass


class LdapPlugin(SingletonPlugin):
    '''"LdapPlugin

    This plugin provides Ldap authentication by implementing the IAuthenticator
    interface.


    '''
    implements(interfaces.IAuthenticator)
    implements(interfaces.IConfigurable)
    implements(interfaces.IConfigurer)
    implements(interfaces.IBlueprint, inherit=True)
    implements(interfaces.IAuthFunctions)
    implements(interfaces.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        '''Implement IConfiguer.update_config

        Add our custom template to the list of templates so we can override the login form.

        :param config:

        '''
        toolkit.add_template_directory(config, u'templates')

    ## IBlueprint
    def get_blueprint(self):
        return routes.blueprints

    def get_auth_functions(self):
        '''Implements IAuthFunctions.get_auth_functions'''
        return {
            u'user_update': user_update,
            u'user_create': user_create
            }

    def configure(self, config):
        '''Implementation of IConfigurable.configure

        :param config:

        '''
        # Setup our models
        model_setup()
        # Our own config schema, defines required items, default values and
        # transform functions
        schema = {
            u'ckanext.ldap.uri': {
                u'required': True
                },
            u'ckanext.ldap.base_dn': {
                u'required': True
                },
            u'ckanext.ldap.search.filter': {
                u'required': True
                },
            u'ckanext.ldap.username': {
                u'required': True
                },
            u'ckanext.ldap.email': {
                u'required': True
                },
            u'ckanext.ldap.auth.dn': {},
            u'ckanext.ldap.auth.password': {
                u'required_if': u'ckanext.ldap.auth.dn'
                },
            u'ckanext.ldap.auth.method': {
                u'default': u'SIMPLE',
                u'validate': _allowed_auth_methods
                },
            u'ckanext.ldap.auth.mechanism': {
                u'default': u'DIGEST-MD5',
                u'validate': _allowed_auth_mechanisms
                },
            u'ckanext.ldap.search.alt': {},
            u'ckanext.ldap.search.alt_msg': {
                u'required_if': u'ckanext.ldap.search.alt'
                },
            u'ckanext.ldap.fullname': {},
            u'ckanext.ldap.organization.id': {},
            u'ckanext.ldap.organization.role': {
                u'default': u'member',
                u'validate': _allowed_roles
                },
            u'ckanext.ldap.ckan_fallback': {
                u'default': False,
                u'parse': toolkit.asbool
                },
            u'ckanext.ldap.prevent_edits': {
                u'default': False,
                u'parse': toolkit.asbool
                },
            u'ckanext.ldap.migrate': {
                u'default': False,
                u'parse': toolkit.asbool
                },
            u'ckanext.ldap.debug_level': {
                u'default': 0,
                u'parse': toolkit.asint
                },
            u'ckanext.ldap.trace_level': {
                u'default': 0,
                u'parse': toolkit.asint
                },
            }
        errors = []
        for key, options in schema.items():
            config_value = config.get(key, None)

            if config_value:
                if u'parse' in options:
                    config_value = (options[u'parse'])(config_value)
                try:
                    if u'validate' in options:
                        (options[u'validate'])(config_value)
                    toolkit.config[key] = config_value
                except ConfigError as e:
                    errors.append(str(e))
            elif options.get(u'required', False):
                errors.append(u'Configuration parameter {0} is required'.format(key))
            elif u'required_if' in options and options[u'required_if'] in toolkit.config:
                errors.append(u'Configuration parameter {0} is required '
                              u'when {1} is present'.format(key, options[u'required_if']))
            elif u'default' in options:
                toolkit.config[key] = options[u'default']

            # make sure the config options are all unicode for LDAP
            if isinstance(toolkit.config.get(key, None), str):
                toolkit.config[key] = unicode(toolkit.config.get(key))
        if len(errors):
            raise ConfigError(u'\n'.join(errors))

    def login(self):
        '''Implementation of IAuthenticator.login

        We don't need to do anything here as we override the form & implement our own controller
        action


        '''
        pass

    def identify(self):
        '''Implementiation of IAuthenticator.identify

        Identify which user (if any) is logged in via this plugin


        '''
        # FIXME: This breaks if the current user changes their own user name.
        user = session.get(u'ckanext-ldap-user')
        if user:
            toolkit.c.user = user
        else:
            # add the 'user' attribute to the context to avoid issue #4247
            toolkit.c.user = None

    def logout(self):
        '''Implementation of IAuthenticator.logout'''
        self._delete_session_items()

    def abort(self, status_code, detail, headers, comment):
        '''Implementation of IAuthenticator.abort

        :param status_code:
        :param detail:
        :param headers:
        :param comment:

        '''
        return status_code, detail, headers, comment

    def _delete_session_items(self):
        '''Delete user details stored in the session by this plugin'''
        if u'ckanext-ldap-user' in session:
            del session[u'ckanext-ldap-user']
            session.save()

    def get_helpers(self):
        ''' '''
        return {
            u'is_ldap_user': is_ldap_user,
            u'get_login_action': get_login_action
            }


def _allowed_roles(v):
    '''

    :param v:

    '''
    if v not in [u'member', u'editor', u'admin']:
        raise ConfigError(u'role must be one of "member", "editor" or "admin"')


def _allowed_auth_methods(v):
    '''

    :param v:

    '''
    if v.upper() not in [u'SIMPLE', u'SASL']:
        raise ConfigError(u'Only SIMPLE and SASL authentication methods are supported')


def _allowed_auth_mechanisms(v):
    '''

    :param v:

    '''
    if v.upper() not in [
        u'DIGEST-MD5', ]:  # Only DIGEST-MD5 is supported when the auth method is SASL
        raise ConfigError(u'Only DIGEST-MD5 is supported as an authentication mechanism')
