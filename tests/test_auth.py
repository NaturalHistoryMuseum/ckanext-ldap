import pytest

from ckan.logic import check_access, NotAuthorized
from ckan.plugins import toolkit
from ckan.tests import factories
from mock import patch, MagicMock


@pytest.mark.ckan_config('ckan.plugins', 'ldap')
@pytest.mark.ckan_config('ckanext.ldap.uri', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.base_dn', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.search.filter', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.username', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.email', 'n/a')
@pytest.mark.usefixtures('clean_db', 'ensure_db_init', 'with_plugins', 'with_request_context')
@pytest.mark.filterwarnings('ignore::sqlalchemy.exc.SADeprecationWarning')
class TestAuthPasswordReset:

    def test_default_is_allow(self):
        assert 'ckanext.ldap.allow_password_reset' not in toolkit.config
        user = factories.User()
        assert check_access('user_reset', {'user': user['name']})

    @pytest.mark.ckan_config('ckanext.ldap.allow_password_reset', 'true')
    def test_allow_when_true(self):
        user = factories.User()
        assert check_access('user_reset', {'user': user['name']})

    @pytest.mark.ckan_config('ckanext.ldap.allow_password_reset', 'false')
    def test_disallow_when_false(self):
        user = factories.User()
        mock_ldap_user = MagicMock(by_user_id=MagicMock(return_value=MagicMock()))
        with patch('ckanext.ldap.logic.auth.LdapUser', mock_ldap_user):
            with pytest.raises(NotAuthorized, match='Cannot reset password for LDAP user'):
                check_access('user_reset', {'user': user['name']})
