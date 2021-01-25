import pytest
from ckan.plugins import toolkit

from ckanext.ldap.lib.helpers import is_ldap_user, get_login_action, decode_str
from mock import MagicMock, patch


def test_is_ldap_user():
    mock_session = {'ckanext-ldap-user': MagicMock()}
    with patch('ckanext.ldap.lib.helpers.session', mock_session):
        assert is_ldap_user()

        del mock_session['ckanext-ldap-user']
        assert not is_ldap_user()


@pytest.mark.ckan_config('ckan.plugins', 'ldap')
@pytest.mark.ckan_config('ckanext.ldap.uri', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.base_dn', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.search.filter', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.username', 'n/a')
@pytest.mark.ckan_config('ckanext.ldap.email', 'n/a')
@pytest.mark.usefixtures('with_plugins', 'with_request_context')
@pytest.mark.filterwarnings('ignore::sqlalchemy.exc.SADeprecationWarning')
class TestGetLoginAction:

    def test_with_came_from(self):
        toolkit.c.login_handler = '/somewhere?came_from=beans'
        action = get_login_action()
        assert action == '/ldap_login_handler?came_from=beans'

    def test_without_came_from(self):
        toolkit.c.login_handler = '/somewhere?lemons=xyz'
        action = get_login_action()
        assert action == '/ldap_login_handler'


def test_decode_str():
    assert decode_str(b'beans') == 'beans'
    assert decode_str(b'\xf0\x9f\x92\xa9') == '💩'
    assert decode_str('beans') == 'beans'
