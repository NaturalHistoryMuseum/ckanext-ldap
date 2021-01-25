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


@ldap.command(name='setup-org')
def setup_org():
    '''
    Sets up the default organisation which all ldap users will be automatically made members of.
    '''
    # get the organisation all users will be added to
    organization_id = toolkit.config['ckanext.ldap.organization.id']

    # set up context
    user = toolkit.get_action('get_site_user')({
        'ignore_auth': True
    }, {})
    context = {
        'user': user['name']
    }

    try:
        toolkit.get_action('organization_show')(context, {
            'id': organization_id
        })
        click.secho(u"Organisation already exists, doing nothing", fg=u"green")
    except toolkit.ObjectNotFound:
        # see the following commit to understand why this line is here
        # http://github.com/ckan/ckanext-harvest/commit/f315f41c86cbde4a49ef869b6993598f8cb11e2d
        context.pop('__auth_audit', None)
        toolkit.get_action('organization_create')(context, {
            'id': organization_id,
            'name': organization_id
        })
        click.secho(u"New organisation created", fg=u"green")
