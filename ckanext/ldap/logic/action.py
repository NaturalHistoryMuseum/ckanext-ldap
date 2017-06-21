# encoding: utf-8

import ckan.logic
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.logic import side_effect_free

import os
import logging
import re
import uuid


import ldap, ldap.filter
import ckan.model as model
import pylons

from ckan.lib.helpers import flash_notice, flash_error
from ckan.common import _, request
from ckan.model.user import User
from ckanext.ldap.plugin import config
from ckanext.ldap.model.ldap_user import LdapUser

from sqlalchemy import orm, types, Column, Table, ForeignKey


ValidationError = ckan.logic.ValidationError
NotFound = ckan.logic.NotFound
_check_access = ckan.logic.check_access
_get_or_bust = ckan.logic.get_or_bust
_get_action = ckan.logic.get_action

log = logging.getLogger(__name__)

def add_ckan_user(context,data_dict):

    # Lookup Ldap
    if  config.get('ckanext.ldap.uri'):
        cnx = ldap.initialize(config['ckanext.ldap.uri'])
    else:
        raise ValidationError({ 'ckan.ldap.uri': 'not speciifed in development/production.ini'})

    try:
       check_name = data_dict['name']
    except:
       raise ValidationError({ 'name': 'missing; use -d option'})

    if check_name == None or check_name == "":
       raise ValidationError({ 'name': ' is missing; use -d option'})

    if config.get('ckanext.ldap.auth.dn'):
        try:
            cnx.bind_s(config['ckanext.ldap.auth.dn'], config['ckanext.ldap.auth.password'])
        except ldap.SERVER_DOWN:
            log.error('LDAP server is not reachable')
            raise ValidationError({ 'LDAP server': 'is not reachable'})
            return None
        except ldap.INVALID_CREDENTIALS:
            log.error('LDAP server credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid')
            raise ValidationError({ 'LDAP server': 'credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid'})
            return None
    print "Hello"

    filter_str = config['ckanext.ldap.search.filter'].format(login=ldap.filter.escape_filter_chars(data_dict['name']))
    attributes = [config['ckanext.ldap.username']]
    if 'ckanext.ldap.fullname' in config:
        attributes.append(config['ckanext.ldap.fullname'])
    if 'ckanext.ldap.email' in config:
        attributes.append(config['ckanext.ldap.email'])
    try:
        ret = _ldap_search(cnx, filter_str, attributes, non_unique='log')
        if ret is None and 'ckanext.ldap.search.alt' in config:
            filter_str = config['ckanext.ldap.search.alt'].format(login=ldap.filter.escape_filter_chars(data_dict['name']))
            ret = _ldap_search(cnx, filter_str, attributes, non_unique='raise')
    finally:
        cnx.unbind()

    ldap_user_dict = ret
    print ldap_user_dict

    if not ldap_user_dict:
        raise ValidationError({ data_dict['name']: 'user not found in ldap'})
        return None
    # Now get a unique user name, and create the CKAN user
    user_name = _get_unique_user_name(data_dict['name'])

    if 'email' in ldap_user_dict:
        user_mail = ldap_user_dict['email']
    else:
        user_mail = ""
    user_dict = {
        'name': user_name,
        'email': user_mail,
        'password': str(uuid.uuid4())
    }
    if 'fullname' in ldap_user_dict:
        user_dict['fullname'] = ldap_user_dict['fullname']
    if 'about' in ldap_user_dict:
        user_dict['about'] = ldap_user_dict['about']
    ckan_user = plugins.toolkit.get_action('user_create')(
        context={'ignore_auth': True},
        data_dict=user_dict
    )
    print "Hello2"

    # Add the user to it's group if needed - JUST ONE LDAP SPECIFC ORGANIZATION - not for us; Anja 21.6.17
    if 'ckanext.ldap.organization.id' in config:
        plugins.toolkit.get_action('member_create')(
            context={'ignore_auth': True},
            data_dict={
                'id': config['ckanext.ldap.organization.id'],
                'object': user_name,
                'object_type': 'user',
                'capacity': config['ckanext.ldap.organization.role']
            }
        )

    # Check the users email adress and add it to the appropiate organization as Editor
    print ldap_user_dict['email']
    user_org = _check_mail_org(ldap_user_dict['email'])
    print user_name
    if user_org:
        plugins.toolkit.get_action('member_create')(
            context={'ignore_auth': True},
            data_dict={
                'id': user_org,
                'object': user_name,
                'object_type': 'user',
                'capacity': 'editor'
            }
        )

    # Add LdapUser entry = Database entry with match ckan_id - ldap_id
    ldap_user = LdapUser(user_id=ckan_user['id'], ldap_id = ldap_user_dict['username'])
    ckan.model.Session.add(ldap_user)
    ckan.model.Session.commit()

    if user_org:
        return "Hooray! User " + user_name + " successfully created in CKAN and added as an Editor to the Organization " + user_org.encode('ascii','ignore')
    else:
        return "Hooray! User " + user_name + " successfully created in CKAN (no Organization was applicable)"

def _check_mail_org(user_email):
    ccca_orgs= [u'aau', u'ages', u'ait', u'alps', u'bayerische-akademie-der-wissenschaften', u'bfw-bundesforschungszentrum-fur-wald', u'boku', u'ccca', u'essl', u'gba', u'iiasa', u'iio', u'jr', u'oaw', u'ogm', u'tu-graz', u'tu-wien', u'uba', u'uibk', u'uma', u'uni-salzburg', u'uni-wien', u'vetmeduni', u'wegener-center', u'wifo', u'wp', u'wu', u'zamg', u'zsi',u'usertest-organization']
    ccca_mails = [u'aau.at',u'ages.at',u'ait.ac.at',u'alps-gmbh.com',u'badw.de',u'bfw.gv.at',u'boku.ac.at', u'ccca.ac.at', u'essl.org',u'geologie.ac.at',u'iiasa.ac.at',u'indoek.at',u'joanneum.at', u'oeaw.ac.at', u'meteorologie.at', u'tugraz.at', u'tuwien.ac.at', u'umweltbundesamt.at',u'uibk.ac.at',u'uma.or.at',u'sbg.ac.at', u'univie.ac.at',u'vetmeduni.ac.at', u'uni-graz.at', u'wifo.ac.at', u'weatherpark.com', u'wu.ac.at',u'zamg.ac.at', u'zsi.at',u'none.at']

    print len (ccca_orgs)
    print len(ccca_mails)
    mail_to_check = user_email.split('@')
    if len(mail_to_check)>1:
        mail_to_check = mail_to_check[1]
    else:
        return None
    print mail_to_check

    if mail_to_check in ccca_mails:
        print "success"
        org_index = ccca_mails.index(mail_to_check)
        print ccca_orgs[org_index]
        return ccca_orgs[org_index]
    else:
        # check if subdomain
        if config.get('ckanext.ldap.mail_prefix'):
            prefixes = config['ckanext.ldap.mail_prefix']
            print prefixes
            dot_i = mail_to_check.find('.')
            if dot_i > 0:
                subdo = mail_to_check[0:dot_i]
                mail_to_check = mail_to_check[dot_i+1:]
                print subdo
                print mail_to_check
                if mail_to_check in ccca_mails:
                    print "success"
                    org_index = ccca_mails.index(mail_to_check)
                    print ccca_orgs[org_index]
                    return ccca_orgs[org_index]

    print "leider nicht"
    return None

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
                    ret[i] = v[0].decode('utf-8')
        return ret
    else:
        return None

def _ckan_user_exists(user_name):
    """Check if a CKAN user name exists, and if that user is an LDAP user.

    @param user_name: User name to check
    @return: Dictionary defining 'exists' and 'ldap'.
    """

    print "**************** Anja ckan_user_exists"
    print user_name
    try:
        user = plugins.toolkit.get_action('user_show')(data_dict = {'id': user_name})
    except plugins.toolkit.ObjectNotFound:
        return {'exists': False, 'is_ldap': False}

    print user
    ldap_user = LdapUser.by_user_id(user['id'])
    print ldap_user

    if ldap_user:
        return {'exists': True, 'is_ldap': True}
    else:
        return {'exists': True, 'is_ldap': False}


def _get_unique_user_name(base_name):
    """Create a unique, valid, non existent user name from the given base name

    @param base_name: Base name
    @return: A valid user name not currently in use based on base_name
    """
    print base_name
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
