# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-ldap
# Created by the Natural History Museum in London, UK


class MultipleMatchError(Exception):
    pass


class UserConflictError(Exception):
    pass
