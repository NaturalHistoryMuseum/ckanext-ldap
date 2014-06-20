import ckan.logic, ckan.logic.auth
from ckan.common import _
from ckan.logic.auth.create import user_create as ckan_user_create
from ckanext.ldap.controllers.user import _find_ldap_user


@ckan.logic.auth_allow_anonymous_access
def user_create(context, data_dict=None):
    if data_dict and 'name' in data_dict:
        ldap_user_dict = _find_ldap_user(data_dict['name'])
        if ldap_user_dict:
            return {'success': False, 'msg': _('An LDAP user by that name already exists')}

    return ckan_user_create(context, data_dict)