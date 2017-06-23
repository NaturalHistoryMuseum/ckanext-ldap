import ckan.logic, ckan.logic.auth
from ckan.common import _
from ckan.logic.auth.create import user_create as ckan_user_create
from ckanext.ldap.controllers.user import _find_ldap_user


@ckan.logic.auth_allow_anonymous_access
def user_create(context, data_dict=None):
    #print "******User create********"
    #print data_dict
    if data_dict and 'name' in data_dict:
        # Modification Anja, 23.6.17
        # We should not walk into this path
        # as automatic user creation by first login of the user does not have data_dict
        # thus we enter this path only - as it looks so far - if there was an authentication problem
        # with the API KEY for the api function
        # Hence we simply return at this point

        #return {'success': False, 'msg': _('Some problem ... please verify according to error type ... :-)')}

        # :-) Unfortunately we end up here when someone registers ... therefore we have to live with the error message (see above)
        # at least so far
        
        ldap_user_dict = _find_ldap_user(data_dict['name'].encode('utf-8'))
        if ldap_user_dict:
            return {'success': False, 'msg': _('An LDAP user by that name already exists')}

    return ckan_user_create(context, data_dict)
