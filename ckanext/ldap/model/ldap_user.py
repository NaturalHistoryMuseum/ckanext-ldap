#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import datetime

from ckan import model
from sqlalchemy import Column, ForeignKey, Table, orm, types

ldap_user_table = Table('ldap_user', model.meta.metadata,
                        Column('id', types.UnicodeText, primary_key=True,
                               default=model.types.make_uuid),
                        Column('user_id', types.UnicodeText, ForeignKey('user.id'),
                               unique=True, nullable=False),
                        Column('ldap_id', types.UnicodeText, index=True, unique=True,
                               nullable=False),
                        Column('created', types.DateTime, default=datetime.datetime.now)
                        )


def setup():
    '''Model setup; ensure our table exists'''
    if not ldap_user_table.exists() and model.user.user_table.exists():
        ldap_user_table.create()


class LdapUser(model.domain_object.DomainObject):
    '''Represents an entry mapping a ldap id to a CKAN user'''

    @classmethod
    def by_ldap_id(cls, ldap_id, autoflush=True):
        '''Return the LdapUser object mapping the given ldap id

        :param ldap_id: ldap id, as returned by the LDAP server
        :param autoflush:  (Default value = True)
        :returns: LdapUser object or None

        '''
        obj = model.meta.Session.query(cls).autoflush(autoflush) \
            .filter_by(ldap_id=ldap_id).first()
        return obj

    @classmethod
    def by_user_id(cls, user_id, autoflush=True):
        '''Return the LdapUser object mapping the given user id

        :param user_id: CKAN user id (actual id, not name)
        :param autoflush:  (Default value = True)
        :returns: LdapUser object or None

        '''
        obj = model.meta.Session.query(cls).autoflush(autoflush) \
            .filter_by(user_id=user_id).first()
        return obj


model.meta.mapper(LdapUser, ldap_user_table, properties={
    'user': orm.relation(model.user.User,
                         backref=orm.backref('ldap_user', cascade='all, delete, delete-orphan'))
}, )
