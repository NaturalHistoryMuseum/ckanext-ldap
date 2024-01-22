# Changelog

## v3.3.0 (2024-01-22)

### Feature

- add "ignore referrals" config option

### Chores/Misc

- add build section to read the docs config
- add regex for version line in citation file
- add citation.cff to list of files with version
- add contributing guidelines
- add code of conduct
- add citation file
- update support.md links

## v3.2.11 (2023-09-25)

### Docs

- update docker test service name in readme

### Style

- fix some minor formatting irregularities

### Tests

- sort out the CKAN 2.10 tests
- add a test for login_success
- add test for login_failed helper

### Build System(s)

- adds ckantest:next as a test target option

### CI System(s)

- add tests on next to ci
- update docker test service name in github action workflow
- fix tests, postgresql wasn't working

## v3.2.10 (2023-07-17)

### Docs

- update logos

## v3.2.9 (2023-04-11)

### Build System(s)

- fix postgres not loading when running tests in docker

### Chores/Misc

- add action to sync branches when commits are pushed to main

## v3.2.8 (2023-02-20)

### Docs

- fix api docs generation script

### Chores/Misc

- small fixes to align with other extensions

## v3.2.7 (2023-02-13)

### Fix

- add 'about' key to schema

### Style

- add whitespace in schema

## v3.2.6 (2023-01-31)

### Docs

- **readme**: change logo url from blob to raw

## v3.2.5 (2023-01-31)

### Docs

- **readme**: direct link to logo in readme
- **readme**: fix github actions badge

## v3.2.4 (2023-01-25)

### Fix

- move templates into theme directory

### Style

- fix some auto style issues

### Build System(s)

- **docker**: use 'latest' tag for test docker image

## v3.2.3 (2022-12-12)

### Style

- change quotes in setup.py to single quotes

### Build System(s)

- include top-level data files in theme folder
- add package data

## v3.2.2 (2022-12-08)

### Build System(s)

- update python-ldap minor version

## v3.2.1 (2022-12-01)

### Docs

- **readme**: fix table borders
- **readme**: format test section
- **readme**: update installation steps
- **readme**: update ckan patch version in header badge

## v3.2.0 (2022-11-28)

### Fix

- exclude helpers from pre-commit test
- unpin ckantools version

### Docs

- fix markdown-include references
- add section delimiters
- fix a few bits of the README
- add logo

### Build System(s)

- set changelog generation to incremental
- pin ckantools minor version
- exclude docs from setuptools

### CI System(s)

- add cz_nhm as a dependency
- **commitizen**: fix message template
- add pypi release action

### Chores/Misc

- remove manifest.in
- clear old changelog
- use cz_nhm commitizen config
- improve commitizen message template
- move cz config into separate file
- add --pytest-test-first arg to precommit

## v3.1.4 (2022-11-07)

### Fix

- move docs requirements into separate file

## v3.1.3 (2022-11-07)

### Fix

- add the module name for coverage generation
- use ckantest docker v0.2

### Docs

- add badge
- add mkdocs config

### Build System(s)

- add a bash script to run tests
- try coveralls again with GITHUB_TOKEN
- use coverallsapp action
- use ubuntu-latest
- add docker dependencies for libldap2 and libsasl2

### Chores/Misc

- update various package files

## v3.1.2 (2022-08-08)

## v3.1.1 (2022-04-25)

## v3.1.0 (2022-03-21)

## v3.0.1 (2022-03-14)

## v3.0.0 (2021-03-09)

## v2.1.0 (2021-01-25)

## v2.0.0-alpha (2019-07-23)

## v1.0.2 (2018-05-17)

## v1.0.1 (2018-01-29)

## v1.0.0 (2018-01-04)

## v0.0.1 (2017-04-11)
