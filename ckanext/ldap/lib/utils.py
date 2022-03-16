from ckanext.ldap.model.ldap_user import ldap_user_table


def init_tables() -> bool:
    '''
    Initialises the database for the LDAP plugin. If the tables already exist then nothing happens.

    :return: True if the database was modified, False if not
    '''
    if not ldap_user_table.exists():
        ldap_user_table.create()
        return True
    return False
