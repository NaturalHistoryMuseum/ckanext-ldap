import re
import uuid
import logging
import sys
import ldap, ldap.filter
import ckan.plugins as p
import ckan.model
import pylons

from ckan.lib.helpers import flash_notice, flash_error
from ckan.common import _, request
from ckan.model.user import User
from ckanext.ldap.plugin import config
from ckanext.ldap.model.ldap_user import LdapUser

log = logging.getLogger(__name__)


class MultipleMatchError(Exception):
    pass
class UserConflictError(Exception):
    pass


class UserController(p.toolkit.BaseController):

    def __init__(self):
        ldap.set_option(ldap.OPT_DEBUG_LEVEL, config['ckanext.ldap.debug_level'])

    def login_handler(self):
        """Action called when login in via the LDAP login form"""
        params = request.POST
        if 'login' in params and 'password' in params:
            login = params['login']
            password = params['password']
            try:
                ldap_user_dict = _find_ldap_user(login)
            except MultipleMatchError as e:
                # Multiple users match. Inform the user and try again.
                return self._login_failed(notice=str(e))
            if ldap_user_dict and _check_ldap_password(ldap_user_dict['cn'], password):
                try:
                    user_name = _get_or_create_ldap_user(ldap_user_dict)
                except UserConflictError as e:
                    return self._login_failed(error=str(e))
                return self._login_success(user_name)
            elif ldap_user_dict:
                # There is an LDAP user, but the auth is wrong. There could be a CKAN user of the
                # same name if the LDAP user had been created later - in which case we have a
                # conflict we can't solve.
                if config['ckanext.ldap.ckan_fallback']:
                    exists = _ckan_user_exists(login)
                    if exists['exists'] and not exists['is_ldap']:
                        return self._login_failed(error=_('Username conflict. Please contact the site administrator.'))
                return self._login_failed(error=_('Bad username or password.'))
            elif config['ckanext.ldap.ckan_fallback']:
                # No LDAP user match, see if we have a CKAN user match
                try:
                    user_dict = p.toolkit.get_action('user_show')(data_dict = {'id': login})
                    # We need the model to validate the password
                    user = User.by_name(user_dict['name'])
                except p.toolkit.ObjectNotFound:
                    user = None
                if user and user.validate_password(password):
                    return self._login_success(user.name)
                else:
                    return self._login_failed(error=_('Bad username or password.'))
            else:
                return self._login_failed(error=_('Bad username or password.'))
        return self._login_failed(error=_('Please enter a username and password'))

    def _login_failed(self, notice=None, error=None):
        """Handle login failures

        Redirect to /user/login and flash an optional message

        @param notice: Optional notice for the user
        @param error: Optional error message for the user
        """
        if notice:
            flash_notice(notice)
        if error:
            flash_error(error)
        p.toolkit.redirect_to(controller='user', action='login')

    def _login_success(self, user_name):
        """Handle login success

        Saves the user in the session and redirects to user/logged_in

        @param user_name: The user name
        """
        pylons.session['ckanext-ldap-user'] = user_name
        pylons.session.save()
        p.toolkit.redirect_to(controller='user', action='dashboard', id=user_name)


def _ckan_user_exists(user_name):
    """Check if a CKAN user name exists, and if that user is an LDAP user.

    @param user_name: User name to check
    @return: Dictionary defining 'exists' and 'ldap'.
    """
    try:
        user = p.toolkit.get_action('user_show')(data_dict = {'id': user_name})
    except p.toolkit.ObjectNotFound:
        return {'exists': False, 'is_ldap': False}

    ldap_user = LdapUser.by_user_id(user['id'])
    if ldap_user:
        return {'exists': True, 'is_ldap': True}
    else:
        return {'exists': True, 'is_ldap': False}


def _get_unique_user_name(base_name):
    """Create a unique, valid, non existent user name from the given base name

    @param base_name: Base name
    @return: A valid user name not currently in use based on base_name
    """
    base_name = re.sub('[^-a-z0-9_]', '_', base_name.lower())
    base_name = base_name[0:100]
    if len(base_name) < 2:
        base_name = (base_name + "__")[0:2]
    count = 0
    user_name = base_name
    while (_ckan_user_exists(user_name))['exists']:
        count += 1
        user_name = "{base}{count}".format(base=base_name[0:100-len(str(count))], count=str(count))
    return user_name


def _get_or_create_ldap_user(ldap_user_dict):
    """Get or create a CKAN user from the data returned by the LDAP server

    @param ldap_user_dict: Dictionary as returned by _find_ldap_user
    @return: The CKAN username of an existing user
    """
    # Look for existing user, and if found return it.
    ldap_user = LdapUser.by_ldap_id(ldap_user_dict['username'])
    if ldap_user:
        # TODO: Update the user detail.
        return ldap_user.user.name
    user_dict = {}
    update=False
    # Check whether we have a name conflict (based on the ldap name, without mapping it to allowed chars)
    exists = _ckan_user_exists(ldap_user_dict['username'])
    if exists['exists'] and not exists['is_ldap']:
        # If ckanext.ldap.migrate is set, update exsting user_dict.
        if not config['ckanext.ldap.migrate']:
             raise UserConflictError(_('There is a username conflict. Please inform the site administrator.'))
        else:
            user_dict = p.toolkit.get_action('user_show')(data_dict = {'id': ldap_user_dict['username']})
            update=True
        
    # If a user with the same ckan name already exists but is an LDAP user, this means (given that we didn't
    # find it above) that the conflict arises from having mangled another user's LDAP name. There will not
    # however be a conflict based on what is entered in the user prompt - so we can go ahead. The current
    # user's id will just be mangled to something different.

    # Now get a unique user name (if not "migrating"), and create the CKAN user and the LdapUser entry.
    user_name = user_dict['name'] if update else _get_unique_user_name(ldap_user_dict['username'])
    user_dict.update({
        'name': user_name,
        'email': ldap_user_dict['email'],
        'password': str(uuid.uuid4())
    })
    if 'fullname' in ldap_user_dict:
        user_dict['fullname'] = ldap_user_dict['fullname']
    if 'about' in ldap_user_dict:
        user_dict['about'] = ldap_user_dict['about']
    if update:
        ckan_user = p.toolkit.get_action('user_update')(
            context={'ignore_auth': True},
            data_dict=user_dict
        )
    else:
        ckan_user = p.toolkit.get_action('user_create')(
            context={'ignore_auth': True},
            data_dict=user_dict
        )
    ldap_user = LdapUser(user_id=ckan_user['id'], ldap_id = ldap_user_dict['username'])
    ckan.model.Session.add(ldap_user)
    ckan.model.Session.commit()
    # Add the user to it's group if needed
    if 'ckanext.ldap.organization.id' in config:
        p.toolkit.get_action('member_create')(
            context={'ignore_auth': True},
            data_dict={
                'id': config['ckanext.ldap.organization.id'],
                'object': user_name,
                'object_type': 'user',
                'capacity': config['ckanext.ldap.organization.role']
            }
        )
    return user_name


def _find_ldap_user(login):
    """Find the LDAP user identified by 'login' in the configured ldap database

    @param login: The login to find in the LDAP database
    @return: None if no user is found, a dictionary defining 'cn', 'username', 'fullname' and 'email otherwise.
    """
    cnx = ldap.initialize(config['ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=config['ckanext.ldap.trace_level'])
    if config.get('ckanext.ldap.auth.dn'):
        try:
            if config['ckanext.ldap.auth.method'] == 'SIMPLE':
                cnx.bind_s(config['ckanext.ldap.auth.dn'], config['ckanext.ldap.auth.password'])
            elif config['ckanext.ldap.auth.method'] == 'SASL':
                if config['ckanext.ldap.auth.mechanism'] == 'DIGEST-MD5':
                    auth_tokens = ldap.sasl.digest_md5(config['ckanext.ldap.auth.dn'], config['ckanext.ldap.auth.password'])
                    cnx.sasl_interactive_bind_s("", auth_tokens)
                else:
                    log.error("SASL mechanism not supported: {0}".format(config['ckanext.ldap.auth.mechanism']))
                    return None
            else:
                log.error("LDAP authentication method is not supported: {0}".format(config['ckanext.ldap.auth.method']))
                return None
        except ldap.SERVER_DOWN:
            log.error('LDAP server is not reachable')
            return None
        except ldap.INVALID_CREDENTIALS:
            log.error('LDAP server credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid')
            return None
        except ldap.LDAPError, e:
            log.error("Fatal LDAP Error: {0}".format(e))
            return None

    filter_str = config['ckanext.ldap.search.filter'].format(login=ldap.filter.escape_filter_chars(login))
    attributes = [config['ckanext.ldap.username']]
    if 'ckanext.ldap.fullname' in config:
        attributes.append(config['ckanext.ldap.fullname'])
    if 'ckanext.ldap.email' in config:
        attributes.append(config['ckanext.ldap.email'])
    try:
        ret = _ldap_search(cnx, filter_str, attributes, non_unique='log')
        if ret is None and 'ckanext.ldap.search.alt' in config:
            filter_str = config['ckanext.ldap.search.alt'].format(login=ldap.filter.escape_filter_chars(login))
            ret = _ldap_search(cnx, filter_str, attributes, non_unique='raise')
    finally:
        cnx.unbind()
    return ret


def _ldap_search(cnx, filter_str, attributes, non_unique='raise'):
    """Helper function to perform the actual LDAP search

    @param cnx: The LDAP connection object
    @param filter_str: The LDAP filter string
    @param attributes: The LDAP attributes to fetch. This *must* include self.ldap_username
    @param non_unique: What to do when there is more than one result. Can be either 'log' (log an error
                       and return None - used to indicate that this is a configuration problem that needs
                       to be address by the site admin, not by the current user) or 'raise' (raise an
                       exception with a message that will be displayed to the current user - such
                       as 'please use your unique id instead'). Other values will silently ignore the error.
    @return: A dictionary defining 'cn', self.ldap_username and any other attributes that were defined
             in attributes; or None if no user was found.
    """
    try:
        res = cnx.search_s(config['ckanext.ldap.base_dn'], ldap.SCOPE_SUBTREE, filterstr=filter_str, attrlist=attributes)
    except ldap.SERVER_DOWN:
        log.error('LDAP server is not reachable')
        return None
    except ldap.OPERATIONS_ERROR as e:
        log.error('LDAP query failed. Maybe you need auth credentials for performing searches? Error returned by the server: ' + e.info)
        return None
    except (ldap.NO_SUCH_OBJECT, ldap.REFERRAL) as e:
        log.error('LDAP distinguished name (ckanext.ldap.base_dn) is malformed or does not exist.')
        return None
    except ldap.FILTER_ERROR:
        log.error('LDAP filter (ckanext.ldap.search) is malformed')
        return None
    if len(res) > 1:
        if non_unique == 'log':
            log.error('LDAP search.filter search returned more than one entry, ignoring. Fix the search to return only 1 or 0 results.')
        elif non_unique == 'raise':
            raise MultipleMatchError(config['ckanext.ldap.search.alt_msg'])
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
            if config[cname] not in attr or not attr[config[cname]]:
                log.error('LDAP search did not return a {}.'.format(i))
                return None
        # Set return dict
        for i in ['username', 'fullname', 'email', 'about']:
            cname = 'ckanext.ldap.' + i
            if cname in config and config[cname] in attr:
                v = attr[config[cname]]
                if v:
                    ret[i] = _decode_str(v[0])
        return ret
    else:
        return None


def _check_ldap_password(cn, password):
    """Checks that the given cn/password credentials work on the given CN.

    @param cn: Common name to log on
    @param password: Password for cn
    @return: True on success, False on failure
    """
    cnx = ldap.initialize(config['ckanext.ldap.uri'], bytes_mode=False,
                          trace_level=config['ckanext.ldap.trace_level'])
    try:
        cnx.bind_s(cn, password)
    except ldap.SERVER_DOWN:
        log.error('LDAP server is not reachable')
        return False
    except ldap.INVALID_CREDENTIALS:
        log.debug('Invalid LDAP credentials')
        return False
    # Fail on empty password
    if password == '':
        log.debug('Invalid LDAP credentials')
        return False
    cnx.unbind_s()
    return True


def _decode_str(s, encoding='utf-8'):
    try:
        # this try throws NameError if this is python3
        if isinstance(s, basestring) and isinstance(s, str):
            return unicode(s, encoding)
    except NameError:
        if isinstance (s, bytes):
            return s.decode(encoding)
    return s
