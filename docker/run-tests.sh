#!/bin/bash

pytest --cov=ckanext.ldap --ckan-ini=test.ini tests

while getopts 'c' OPTION; do
  case "$OPTION" in
    c) coveralls;;
    ?) exit 1;;
  esac
done
