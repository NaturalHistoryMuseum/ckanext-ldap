#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK


import logging

from ckan.plugins import toolkit

log = logging.getLogger()


class LDAPCommand(toolkit.CkanCommand):
    '''
    Paster function to set up the default organisation
    
    Paster function can be included to provision scripts - otherwise, get an error after
    provisioning new CKAN instance
    
    Commands:
    
        paster ldap setup-org -c /etc/ckan/default/development.ini

    '''
    summary = __doc__.split(u'\n')[0]
    usage = __doc__

    def command(self):
        if not self.args or self.args[0] in [u'--help', u'-h', u'help']:
            print self.__doc__
            return

        self._load_config()

        cmd = self.args[0]
        if cmd == u'setup-org':
            self.setup_org()
        else:
            print u'Command %s not recognized' % cmd

    def setup_org(self):
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
        except toolkit.ObjectNotFound:
            # see the following commit to understand why this line is here
            # http://github.com/ckan/ckanext-harvest/commit/f315f41c86cbde4a49ef869b6993598f8cb11e2d
            self.context.pop(u'__auth_audit', None)
            toolkit.get_action(u'organization_create')(context, {
                u'id': organization_id,
                u'name': organization_id
            })
