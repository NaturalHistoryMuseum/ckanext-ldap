import click

from ckan.plugins import toolkit


def get_commands():
    return [ldap]


@click.group()
def ldap():
    '''
    The LDAP CLI.
    '''
    pass


@ldap.command(name=u'setup-org')
def setup_org():
    '''
    Sets up the default organisation which all ldap users will be automatically made members of.
    '''
    # get the organisation all users will be added to
    organization_id = toolkit.config[u'ckanext.ldap.organization.id']

    # set up context
    user = toolkit.get_action(u'get_site_user')({
        u'ignore_auth': True
    }, {})
    context = {
        u'user': user[u'name']
    }

    try:
        toolkit.get_action(u'organization_show')(context, {
            u'id': organization_id
        })
        click.secho(u"Organisation already exists, doing nothing", fg=u"green")
    except toolkit.ObjectNotFound:
        # see the following commit to understand why this line is here
        # http://github.com/ckan/ckanext-harvest/commit/f315f41c86cbde4a49ef869b6993598f8cb11e2d
        context.pop(u'__auth_audit', None)
        toolkit.get_action(u'organization_create')(context, {
            u'id': organization_id,
            u'name': organization_id
        })
        click.secho(u"New organisation created", fg=u"green")
