
import logging
import pylons
from ckan.lib.cli import CkanCommand
from ckanext.datastore.db import _get_engine
from ckan.plugins import toolkit
from ckan import logic

log = logging.getLogger()

class LDAPCommand(CkanCommand):
    """

    Paster function to set up the default organisation

    Paster function can be included to provision scripts - otherwise, get an error after provisioning new CKAN instance

    Commands:

        paster ldap setup-org -c /etc/ckan/default/development.ini

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__


    def command(self):

        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.__doc__
            return

        self._load_config()

        # Set up context
        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        self.context = {'user': user['name']}

        cmd = self.args[0]

        if cmd == 'setup-org':
            self.setup_org()
        else:
            print 'Command %s not recognized' % cmd

    def setup_org(self):

        # Get the organisation all users will be added to
        organization_id = pylons.config['ckanext.ldap.organization.id']

        try:
            toolkit.get_action('organization_show')(self.context, {'id': organization_id})
        except logic.NotFound:
            toolkit.get_action('organization_create')(self.context, {'id': organization_id, 'name': organization_id})
