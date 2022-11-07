# Changelog

(This file may not be historically complete, as it is a recent addition to the project).

## v3.1.4 (2022-11-07)

### Fix

- move docs requirements into separate file

## v3.1.3 (2022-11-07)

### Fix

- add the module name for coverage generation
- use ckantest docker v0.2

## v3.1.2 (2022-08-08)

## v3.1.1 (2022-04-25)

## v3.1.0 (2022-03-21)

## v3.0.1 (2022-03-14)

## [3.0.0] - 2021-01-25

- Drop python2 support, add complete python3.6-3.8 support
- Switch docker based tests to run on python3
- Remove python2 specific code (_u_ string prefixes primarily), embrace some python3 code (use of
  fstrings)
- Remove dependency on six

## [2.1.0] - 2021-01-25

- Updated to work with CKAN 2.9.1.
- Switched to docker based testing.
- Add dependency on six

## [2.0.0-alpha] - 2019-07-23

- Updated to work with CKAN 2.9.0a, e.g.:
    - uses toolkit wherever possible
    - references to Pylons removed
- Standardised README, CHANGELOG, setup.py and .github files to match other Museum extensions
