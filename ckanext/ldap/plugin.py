import logging
import pylons
import ckan.plugins as p

config = {}

from ckanext.ldap.logic.auth.update import user_update
from ckanext.ldap.logic.auth.create import user_create
from ckanext.ldap.model.ldap_user import setup as model_setup
from ckanext.ldap.lib.helpers import is_ldap_user


log = logging.getLogger(__name__)


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
            'ckanext.ldap.uri': {'required': True},
            'ckanext.ldap.base_dn': {'required': True},
            'ckanext.ldap.search.filter': {'required': True},
            'ckanext.ldap.username': {'required': True},
            'ckanext.ldap.email': {'required': True},
            'ckanext.ldap.auth.dn': {},
            'ckanext.ldap.auth.password': {'required_if': 'ckanext.ldap.auth.dn'},
            'ckanext.ldap.auth.method': {'default': 'SIMPLE', 'validate': _allowed_auth_methods},
            'ckanext.ldap.auth.mechanism': {'default': 'DIGEST-MD5', 'validate': _allowed_auth_mechanisms},
            'ckanext.ldap.search.alt': {},
            'ckanext.ldap.search.alt_msg': {'required_if': 'ckanext.ldap.search.alt'},
            'ckanext.ldap.fullname': {},
            'ckanext.ldap.organization.id': {},
            'ckanext.ldap.organization.role': {'default': 'member', 'validate': _allowed_roles},
            'ckanext.ldap.ckan_fallback': {'default': False, 'parse': p.toolkit.asbool},
            'ckanext.ldap.prevent_edits': {'default': False, 'parse': p.toolkit.asbool},
            'ckanext.ldap.migrate': {'default': False, 'parse': p.toolkit.asbool},
            'ckanext.ldap.debug_level': {'default': 0, 'parse': p.toolkit.asint},
            'ckanext.ldap.trace_level': {'default': 0, 'parse': p.toolkit.asint},
        }
        errors = []
        for i in schema:
            v = None
            if i in main_config:
                v = main_config[i]
            elif i.replace('ckanext.', '') in main_config:
                log.warning('LDAP configuration options should be prefixed with \'ckanext.\'. ' +
                            'Please update {0} to {1}'.format(i.replace('ckanext.', ''), i))
                # Support ldap.* options for backwards compatibility
                main_config[i] = main_config[i.replace('ckanext.', '')]
                v = main_config[i]

            if v:
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
        # make sure all the strings in the config are unicode formatted
        for key, value in config.iteritems():
            if isinstance(value, str):
                config[key] = unicode(value, encoding='utf-8')

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

def _allowed_auth_methods(v):
    """Raise an exception if the value is not an allowed authentication method"""
    if v.upper() not in ['SIMPLE', 'SASL']:
        raise ConfigError('Only SIMPLE and SASL authentication methods are supported')

def _allowed_auth_mechanisms(v):
    """Raise an exception if the value is not an allowed authentication mechanism"""
    if v.upper() not in ['DIGEST-MD5',]:  # Only DIGEST-MD5 is supported when the auth method is SASL
        raise ConfigError('Only DIGEST-MD5 is supported as an authentication mechanism')
