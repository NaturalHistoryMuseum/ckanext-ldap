import pylons
import ckan.plugins as p

config = {}

from ckanext.ldap.logic.auth.update import user_update
from ckanext.ldap.logic.auth.create import user_create
from ckanext.ldap.model.ldap_user import setup as model_setup
from ckanext.ldap.lib.helpers import is_ldap_user


class ConfigError(Exception):
    pass

class LdapPlugin(p.SingletonPlugin):
    """"LdapPlugin

    This plugin provides Ldap authentication by implementing the IAuthenticator
    interface.
    """
    p.implements(p.IAuthenticator)
    p.implements(p.IConfigurable)
    p.implements(p.IConfigurer)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IAuthFunctions)
    p.implements(p.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        """Implement IConfiguer.update_config

        Add our custom template to the list of templates so we can override the login form.
        """
        p.toolkit.add_template_directory(config, 'templates')

    def before_map(self, map):
        """Implements Iroutes.before_map

        Add our custom login form handler"""
        map.connect('/ldap_login_handler',
                    controller='ckanext.ldap.controllers.user:UserController',
                    action='login_handler')
        return map

    def get_auth_functions(self):
        """Implements IAuthFunctions.get_auth_functions"""
        return {
            'user_update': user_update,
            'user_create': user_create
        }

    def configure(self, main_config):
        """Implementation of IConfigurable.configure"""
        # Setup our models
        model_setup()
        # Our own config schema, defines required items, default values and transform functions
        schema = {
            'ldap.uri': {'required': True},
            'ldap.base_dn': {'required': True},
            'ldap.search.filter': {'required': True},
            'ldap.username': {'required': True},
            'ldap.email': {'required': True},
            'ldap.auth.dn': {},
            'ldap.auth.password': {'required_if': 'ldap.auth.dn'},
            'ldap.search.alt': {},
            'ldap.search.alt_msg': {'required_if': 'ldap.search.alt'},
            'ldap.fullname': {},
            'ldap.organization.id': {},
            'ldap.organization.role': {'default': 'member', 'validate': _allowed_roles},
            'ldap.ckan_fallback': {'default': False, 'parse': p.toolkit.asbool},
            'ldap.prevent_edits': {'default': False, 'parse': p.toolkit.asbool}
        }
        errors = []
        for i in schema:
            if i in main_config:
                v = main_config[i]
                if 'parse' in schema[i]:
                    v = (schema[i]['parse'])(v)
                try:
                    if 'validate' in schema[i]:
                        (schema[i]['validate'])(v)
                    config[i] = v
                except ConfigError as e:
                    errors.append(str(e))
            elif schema[i].get('required', False):
                errors.append('Configuration parameter {} is required'.format(i))
            elif schema[i].get('required_if', False) and schema[i]['required_if'] in config:
                errors.append('Configuration parameter {} is required when {} is presnt'.format(i,
                    schema[i]['required_if']))
            elif 'default' in schema[i]:
                config[i] = schema[i]['default']
        if len(errors):
            raise ConfigError("\n".join(errors))

    def login(self):
        """Implementation of IAuthenticator.login

        We don't need to do anything here as we override the form & implement our own controller action
        """
        pass

    def identify(self):
        """ Implementiation of IAuthenticator.identify

        Identify which user (if any) is logged in via this plugin
        """
        # FIXME: This breaks if the current user changes their own user name.
        user = pylons.session.get('ckanext-ldap-user')
        if user:
            p.toolkit.c.user = user

    def logout(self):
        """Implementation of IAuthenticator.logout"""
        self._delete_session_items()

    def abort(self, status_code, detail, headers, comment):
        """Implementation of IAuthenticator.abort"""
        return status_code, detail, headers, comment

    def _delete_session_items(self):
        """Delete user details stored in the session by this plugin"""
        if 'ckanext-ldap-user' in pylons.session:
            del pylons.session['ckanext-ldap-user']
            pylons.session.save()

    def get_helpers(self):
        return {
            'is_ldap_user': is_ldap_user
        }


def _allowed_roles(v):
    """Raise an exception if the value is not an allowed role"""
    if v not in ['member', 'editor', 'admin']:
        raise ConfigError('role must be one of "member", "editor" or "admin"')
