import pytest

from ckanext.ldap.lib.utils import init_tables


@pytest.fixture
def ensure_db_init():
    '''
    Initialises the LDAP database, must be called after the main CKAN db init.
    '''
    init_tables()
