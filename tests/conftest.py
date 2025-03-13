import pytest

from ckanext.ldap.model.ldap_user import ldap_user_table

try:
    # 2.11 compatibility
    from ckan.model import ensure_engine

    ensure_engine_available = True
except ImportError:
    ensure_engine_available = False


@pytest.fixture
def ensure_db_init():
    """
    Initialises the database for the LDAP plugin. If the tables already exist then
    nothing happens. Must be called after the main CKAN db init.

    :returns: True if the database was modified, False if not
    """
    if ensure_engine_available:
        engine = ensure_engine()
        if not ldap_user_table.exists(engine):
            ldap_user_table.create(engine)
            return True
    else:
        if not ldap_user_table.exists():
            ldap_user_table.create()
            return True
    return False
