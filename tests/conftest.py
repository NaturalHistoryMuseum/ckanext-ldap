import pytest

from ckanext.ldap.model.ldap_user import ldap_user_table


@pytest.fixture
def ensure_db_init():
    '''
    Initialises the LDAP database, must be called after the main CKAN db init.
    '''
    if not ldap_user_table.exists():
        ldap_user_table.create()
