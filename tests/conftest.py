import pytest

from ckanext.ldap.model.ldap_user import ldap_user_table

try:
    # 2.11 compatibility
    from ckan.model import ensure_engine
except ImportError:

    def ensure_engine():
        return None


@pytest.fixture
def ensure_db_init():
    """
    Initialises the database for the LDAP plugin.

    If the tables already exist then nothing happens. Must be called after the main CKAN
    db init.
    """
    engine = ensure_engine()
    ldap_user_table.create(engine, checkfirst=True)
