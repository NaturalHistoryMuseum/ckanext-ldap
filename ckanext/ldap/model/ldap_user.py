#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK

import datetime

import ckan.model.meta as meta
import ckan.model.user as user
import ckan.model.domain_object as domain_object
import ckan.model.types as _types

from sqlalchemy import orm, types, Column, Table, ForeignKey

__all__ = [u'LdapUser']

ldap_user_table = Table(u'ldap_user', meta.metadata,
                     Column(u'id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                     Column(u'user_id', types.UnicodeText, ForeignKey(u'user.id'), unique=True, nullable=False),
                     Column(u'ldap_id', types.UnicodeText, index=True, unique=True, nullable=False),
                     Column(u'created', types.DateTime, default=datetime.datetime.now)
                     )

def setup():
    '''Model setup; ensure our table exists'''
    if not ldap_user_table.exists() and user.user_table.exists():
        ldap_user_table.create()

class LdapUser(domain_object.DomainObject):
    '''Represents an entry mapping a ldap id to a CKAN user'''
    @classmethod
    def by_ldap_id(cls, ldap_id, autoflush=True):
        '''Return the LdapUser object mapping the given ldap id

        :param ldap_id: ldap id, as returned by the LDAP server
        :param autoflush:  (Default value = True)
        :returns: LdapUser object or None

        '''
        obj = meta.Session.query(cls).autoflush(autoflush)\
              .filter_by(ldap_id=ldap_id).first()
        return obj

    @classmethod
    def by_user_id(cls, user_id, autoflush=True):
        '''Return the LdapUser object mapping the given user id

        :param user_id: CKAN user id (actual id, not name)
        :param autoflush:  (Default value = True)
        :returns: LdapUser object or None

        '''
        obj = meta.Session.query(cls).autoflush(autoflush)\
              .filter_by(user_id=user_id).first()
        return obj

meta.mapper(LdapUser, ldap_user_table,
       properties={
            u'user': orm.relation(user.User,
                backref=orm.backref(u'ldap_user',
                cascade=u'all, delete, delete-orphan'
                ))
            },
       )
