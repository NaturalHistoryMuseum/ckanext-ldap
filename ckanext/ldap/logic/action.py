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

from sqlalchemy import orm, types, Column, Table, ForeignKey

from ckan.lib.helpers import flash_notice, flash_error
from ckan.common import _, request
from ckan.model.user import User
from ckanext.ldap.plugin import config
from ckanext.ldap.model.ldap_user import LdapUser
from ckanext.ldap.controllers.user import _ldap_search
from ckanext.ldap.controllers.user import _ckan_user_exists
from ckanext.ldap.controllers.user import _get_unique_user_name


ValidationError = ckan.logic.ValidationError
NotFound = ckan.logic.NotFound
NotAuthorized = ckan.logic.NotAuthorized

_check_access = ckan.logic.check_access
_get_or_bust = ckan.logic.get_or_bust
_get_action = ckan.logic.get_action

log = logging.getLogger(__name__)

def ldap_check_api_create(context,data_dict):

    try:
        _check_access('user_create', context)
    except NotAuthorized:
        raise ValidationError({ 'Invalid Api Key': 'Not authorized to create a user'})

    return True


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
            raise EnvironmentError({ 'LDAP server': 'is not reachable'})
        except ldap.INVALID_CREDENTIALS:
            log.error('LDAP server credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid')
            raise EnvironmentError({ 'LDAP server': 'credentials (ckanext.ldap.auth.dn and ckanext.ldap.auth.password) invalid'})
    #print "Hello"

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
    #print ldap_user_dict

    if not ldap_user_dict:
        raise ValidationError({ data_dict['name']: 'user not found in ldap'})

    # check if we already have an entry in the ldap table
    #print ldap_user_dict
    entry_exits = LdapUser.by_ldap_id(ldap_user_dict['username'])
    if entry_exits:
        raise ValidationError({ ldap_user_dict['username']: 'Mapping in ckan-ldap table exits already'})

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
        context={'ignore_auth': False},
        data_dict=user_dict
    )
    #print "Hello2"

    # Add the user to it's group if needed - JUST ONE LDAP SPECIFC ORGANIZATION - not for us; Anja 21.6.17
    if 'ckanext.ldap.organization.id' in config:
        plugins.toolkit.get_action('member_create')(
            context={'ignore_auth': False},
            data_dict={
                'id': config['ckanext.ldap.organization.id'],
                'object': user_name,
                'object_type': 'user',
                'capacity': config['ckanext.ldap.organization.role']
            }
        )

    # Check the users email adress and add it to the appropiate organization as Editor
    #print ldap_user_dict['email']
    user_org = _check_mail_org(ldap_user_dict['email'])
    #print user_name
    if user_org:
        plugins.toolkit.get_action('member_create')(
            context={'ignore_auth': False},
            data_dict={
                'id': user_org,
                'object': user_name,
                'object_type': 'user',
                'capacity': 'editor'
            }
        )


    #' TODO': check oben if already an entry for ldap_id!!!!!
    # Add LdapUser entry = Database entry with match ckan_id - ldap_id
    ldap_user = LdapUser(user_id=ckan_user['id'], ldap_id = ldap_user_dict['username'])
    ckan.model.Session.add(ldap_user)
    ckan.model.Session.commit()

    if user_org:
        return "Hooray! User " + user_name + " successfully created in CKAN and added as an Editor to the Organization " + user_org.encode('ascii','ignore')
    else:
        return "Hooray! User " + user_name + " successfully created in CKAN (no Organization was applicable)"

def _check_mail_org(user_email):
    ccca_orgs= [u'aau', u'ages', u'ait', u'alps', u'bayerische-akademie-der-wissenschaften', u'bfw-bundesforschungszentrum-fur-wald', u'boku', u'ccca', u'donau-uni',u'essl', u'gba', u'iiasa', u'iio', u'jr', u'oaw', u'ogm', u'tu-graz', u'tu-wien', u'uba', u'uibk', u'uma', u'uni-salzburg', u'uni-wien', u'vetmeduni', u'uni-graz', u'wifo', u'wp', u'wu', u'zamg', u'zsi']
    ccca_mails = [u'aau.at',u'ages.at',u'ait.ac.at',u'alps-gmbh.com',u'badw.de',u'bfw.gv.at',u'boku.ac.at', u'ccca.ac.at', u'donau-uni.ac.at', u'essl.org',u'geologie.ac.at',u'iiasa.ac.at',u'indoek.at',u'joanneum.at', u'oeaw.ac.at', u'meteorologie.at', u'tugraz.at', u'tuwien.ac.at', u'umweltbundesamt.at',u'uibk.ac.at',u'uma.or.at',u'sbg.ac.at', u'univie.ac.at',u'vetmeduni.ac.at', u'uni-graz.at', u'wifo.ac.at', u'weatherpark.com', u'wu.ac.at',u'zamg.ac.at', u'zsi.at']

    #print len (ccca_orgs)
    #print len(ccca_mails)
    mail_to_check = user_email.split('@')
    if len(mail_to_check)>1:
        mail_to_check = mail_to_check[1]
    else:
        return None
    #print mail_to_check

    if mail_to_check in ccca_mails:
        #print "success"
        org_index = ccca_mails.index(mail_to_check)
        #print ccca_orgs[org_index]
        return ccca_orgs[org_index]
    else:
        # check if subdomain
        if config.get('ckanext.ldap.mail_prefix'):
            prefixes = config['ckanext.ldap.mail_prefix']
            #print prefixes
            dot_i = mail_to_check.find('.')
            if dot_i > 0:
                subdo = mail_to_check[0:dot_i]
                if subdo not in prefixes:
                    return None

                mail_to_check = mail_to_check[dot_i+1:]

                #print mail_to_check
                if mail_to_check in ccca_mails:
                    #print "success"
                    org_index = ccca_mails.index(mail_to_check)
                    #print ccca_orgs[org_index]
                    return ccca_orgs[org_index]

    #print "leider nicht"
    return None

def ldap_mail_org(context, email):
    ccca_orgs= [u'aau', u'ages', u'ait', u'alps',
                u'bayerische-akademie-der-wissenschaften',
                u'bfw-bundesforschungszentrum-fur-wald', u'boku', u'ccca',
                u'donau-uni', u'essl', u'gba', u'iiasa', u'iio', u'jr', u'oaw', u'ogm',
                u'tu-graz', u'tu-wien', u'uba', u'uibk', u'uma', u'uni-salzburg',
                u'uni-wien', u'vetmeduni', u'uni-graz', u'wifo', u'wp', u'wu', u'zamg',
                u'zsi']

    ccca_mails = [u'aau.at',u'ages.at',u'ait.ac.at', u'alps-gmbh.com',
                  u'badw.de',u'bfw.gv.at', u'boku.ac.at', u'ccca.ac.at',
                  u'donau-uni.ac.at', u'essl.org', u'geologie.ac.at',
                  u'iiasa.ac.at', u'indoek.at', u'joanneum.at', u'oeaw.ac.at',
                  u'meteorologie.at', u'tugraz.at', u'tuwien.ac.at',
                  u'umweltbundesamt.at', u'uibk.ac.at', u'uma.or.at',
                  u'sbg.ac.at', u'univie.ac.at', u'vetmeduni.ac.at',
                  u'uni-graz.at', u'wifo.ac.at', u'weatherpark.com',
                  u'wu.ac.at',u'zamg.ac.at', u'zsi.at']

    try:
        emailuser, domain = email.split('@')
        ind = next((i for i, s  in enumerate(ccca_mails) if s in domain),None)
        return ccca_orgs[ind]
    except ValueError:
        raise Exception("Not a valid mail address")

