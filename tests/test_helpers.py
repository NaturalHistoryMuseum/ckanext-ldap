from ckanext.ldap.lib.helpers import is_ldap_user
from mock import MagicMock, patch


def test_is_ldap_user():
    mock_session = {'ckanext-ldap-user': MagicMock()}
    with patch('ckanext.ldap.lib.helpers.session', mock_session):
        assert is_ldap_user()

        del mock_session['ckanext-ldap-user']
        assert not is_ldap_user()
