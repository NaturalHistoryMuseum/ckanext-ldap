# Changelog

(This file may not be historically complete, as it is a recent addition to the project).

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
