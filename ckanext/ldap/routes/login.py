# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import ldap
from ckan.model import User
from ckan.plugins import toolkit
from ckanext.ldap.lib.exceptions import MultipleMatchError, UserConflictError
from ckanext.ldap.lib.search import find_ldap_user
from flask import Blueprint

from . import _helpers

blueprint = Blueprint(name='ldap', import_name=__name__)


@blueprint.before_app_first_request
def initialise():
    ldap.set_option(ldap.OPT_DEBUG_LEVEL, toolkit.config['ckanext.ldap.debug_level'])


@blueprint.route('/ldap_login_handler', methods=['POST'])
def login_handler():
    '''
    Action called when login in via the LDAP login form.
    '''
    params = toolkit.request.values
    came_from = params.get('came_from', None)
    if 'login' in params and 'password' in params:
        login = params['login']
        password = params['password']
        try:
            ldap_user_dict = find_ldap_user(login)
        except MultipleMatchError as e:
            # Multiple users match. Inform the user and try again.
            return _helpers.login_failed(notice=str(e))
        if ldap_user_dict and _helpers.check_ldap_password(ldap_user_dict['cn'], password):
            try:
                user_name = _helpers.get_or_create_ldap_user(ldap_user_dict)
            except UserConflictError as e:
                return _helpers.login_failed(error=str(e))
            return _helpers.login_success(user_name, came_from=came_from)
        elif ldap_user_dict:
            # There is an LDAP user, but the auth is wrong. There could be a
            # CKAN user of the same name if the LDAP user had been created
            # later - in which case we have a conflict we can't solve.
            if toolkit.config['ckanext.ldap.ckan_fallback']:
                exists = _helpers.ckan_user_exists(login)
                if exists['exists'] and not exists['is_ldap']:
                    return _helpers.login_failed(error=toolkit._(
                        'Username conflict. Please contact the site administrator.'))
            return _helpers.login_failed(error=toolkit._('Bad username or password.'))
        elif toolkit.config['ckanext.ldap.ckan_fallback']:
            # No LDAP user match, see if we have a CKAN user match
            try:
                user_dict = _helpers.get_user_dict(login)
                # We need the model to validate the password
                user = User.by_name(user_dict['name'])
            except toolkit.ObjectNotFound:
                user = None
            if user and user.validate_password(password):
                return _helpers.login_success(user.name, came_from=came_from)
            else:
                return _helpers.login_failed(
                    error=toolkit._('Bad username or password.'))
        else:
            return _helpers.login_failed(error=toolkit._('Bad username or password.'))
    return _helpers.login_failed(
        error=toolkit._('Please enter a username and password'))
