#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import logging

from ckan.common import session
from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit
from ckanext.ldap import routes, cli
from ckanext.ldap.lib.helpers import get_login_action, is_ldap_user
from ckanext.ldap.logic.auth import user_create, user_update, user_reset
from ckanext.ldap.model.ldap_user import setup as model_setup

log = logging.getLogger(__name__)


class ConfigError(Exception):
    ''' '''
    pass


class LdapPlugin(SingletonPlugin):
    '''
    LdapPlugin

    This plugin provides Ldap authentication by implementing the IAuthenticator
    interface.
    '''
    implements(interfaces.IAuthenticator)
    implements(interfaces.IConfigurable)
    implements(interfaces.IConfigurer)
    implements(interfaces.IBlueprint, inherit=True)
    implements(interfaces.IAuthFunctions)
    implements(interfaces.ITemplateHelpers, inherit=True)
    implements(interfaces.IClick)

    ## IClick
    def get_commands(self):
        return cli.get_commands()

    def update_config(self, config):
        '''Implement IConfiguer.update_config

        Add our custom template to the list of templates so we can override the login form.

        :param config:

        '''
        toolkit.add_template_directory(config, 'templates')

    ## IBlueprint
    def get_blueprint(self):
        return routes.blueprints

    def get_auth_functions(self):
        '''Implements IAuthFunctions.get_auth_functions'''
        return {
            'user_update': user_update,
            'user_create': user_create,
            'user_reset': user_reset,
        }

    def configure(self, config):
        '''
        Implementation of IConfigurable.configure

        :param config:
        '''
        # Setup our models
        model_setup()
        # Our own config schema, defines required items, default values and
        # transform functions
        schema = {
            'ckanext.ldap.uri': {
                'required': True
            },
            'ckanext.ldap.base_dn': {
                'required': True
            },
            'ckanext.ldap.search.filter': {
                'required': True
            },
            'ckanext.ldap.username': {
                'required': True
            },
            'ckanext.ldap.email': {
                'required': True
            },
            'ckanext.ldap.auth.dn': {},
            'ckanext.ldap.auth.password': {
                'required_if': 'ckanext.ldap.auth.dn'
            },
            'ckanext.ldap.auth.method': {
                'default': 'SIMPLE',
                'validate': _allowed_auth_methods
            },
            'ckanext.ldap.auth.mechanism': {
                'default': 'DIGEST-MD5',
                'validate': _allowed_auth_mechanisms
            },
            'ckanext.ldap.search.alt': {},
            'ckanext.ldap.search.alt_msg': {
                'required_if': 'ckanext.ldap.search.alt'
            },
            'ckanext.ldap.fullname': {},
            'ckanext.ldap.organization.id': {},
            'ckanext.ldap.organization.role': {
                'default': 'member',
                'validate': _allowed_roles
            },
            'ckanext.ldap.ckan_fallback': {
                'default': False,
                'parse': toolkit.asbool
            },
            'ckanext.ldap.prevent_edits': {
                'default': False,
                'parse': toolkit.asbool
            },
            'ckanext.ldap.migrate': {
                'default': False,
                'parse': toolkit.asbool
            },
            'ckanext.ldap.debug_level': {
                'default': 0,
                'parse': toolkit.asint
            },
            'ckanext.ldap.trace_level': {
                'default': 0,
                'parse': toolkit.asint
            },
        }
        errors = []
        for key, options in schema.items():
            config_value = config.get(key, None)

            if config_value:
                if 'parse' in options:
                    config_value = (options['parse'])(config_value)
                try:
                    if 'validate' in options:
                        (options['validate'])(config_value)
                    toolkit.config[key] = config_value
                except ConfigError as e:
                    errors.append(str(e))
            elif options.get('required', False):
                errors.append('Configuration parameter {0} is required'.format(key))
            elif 'required_if' in options and options['required_if'] in toolkit.config:
                errors.append('Configuration parameter {0} is required '
                              'when {1} is present'.format(key, options['required_if']))
            elif 'default' in options:
                toolkit.config[key] = options['default']

        if len(errors):
            raise ConfigError('\n'.join(errors))

    # IAuthenticator
    def login(self):
        '''
        We don't need to do anything here as we override the form & implement our own controller
        action.
        '''
        pass

    # IAuthenticator
    def identify(self):
        '''
        Identify which user (if any) is logged in via this plugin
        '''
        # FIXME: This breaks if the current user changes their own user name.
        user = session.get('ckanext-ldap-user')
        if user:
            toolkit.c.user = user
        else:
            # add the 'user' attribute to the context to avoid issue #4247
            toolkit.c.user = None

    # IAuthenticator
    def logout(self):
        self._delete_session_items()

    # IAuthenticator
    def abort(self, status_code, detail, headers, comment):
        return status_code, detail, headers, comment

    def _delete_session_items(self):
        '''
        Delete user details stored in the session by this plugin.
        '''
        if 'ckanext-ldap-user' in session:
            del session['ckanext-ldap-user']
            session.save()

    def get_helpers(self):
        return {
            'is_ldap_user': is_ldap_user,
            'get_login_action': get_login_action
        }


def _allowed_roles(v):
    if v not in ['member', 'editor', 'admin']:
        raise ConfigError('role must be one of "member", "editor" or "admin"')


def _allowed_auth_methods(v):
    if v.upper() not in ['SIMPLE', 'SASL']:
        raise ConfigError('Only SIMPLE and SASL authentication methods are supported')


def _allowed_auth_mechanisms(v):
    # Only DIGEST-MD5 is supported when the auth method is SASL
    if v.upper() != 'DIGEST-MD5':
        raise ConfigError('Only DIGEST-MD5 is supported as an authentication mechanism')
