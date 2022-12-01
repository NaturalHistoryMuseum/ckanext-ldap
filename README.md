<!--header-start-->
<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-ldap

[![Tests](https://img.shields.io/github/workflow/status/NaturalHistoryMuseum/ckanext-ldap/Tests?style=flat-square)](https://github.com/NaturalHistoryMuseum/ckanext-ldap/actions/workflows/main.yml)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-ldap/main?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-ldap)
[![CKAN](https://img.shields.io/badge/ckan-2.9.7-orange.svg?style=flat-square)](https://github.com/ckan/ckan)
[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg?style=flat-square)](https://www.python.org/)
[![Docs](https://img.shields.io/readthedocs/ckanext-ldap?style=flat-square)](https://ckanext-ldap.readthedocs.io)

_A CKAN extension that provides LDAP authentication._

<!--header-end-->

# Overview

<!--overview-start-->
This plugin provides LDAP authentication for CKAN.

Features include:
- Imports username, full name, email and description;
- Can match against several LDAP fields (eg. username or full name);
- Allows to have LDAP only authentication, or combine LDAP and basic CKAN authentication;
- Can add LDAP users to a given organization automatically;
- Works with Active Directory.

<!--overview-end-->

# Installation

<!--installation-start-->
Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

## Installing from PyPI

```shell
pip install ckanext-ldap
```

## Installing from source

1. Clone the repository into the `src` folder:
   ```shell
   cd $INSTALL_FOLDER/src
   git clone https://github.com/NaturalHistoryMuseum/ckanext-ldap.git
   ```

2. Activate the virtual env:
   ```shell
   . $INSTALL_FOLDER/bin/activate
   ```

3. Install via pip:
   ```shell
   pip install $INSTALL_FOLDER/src/ckanext-ldap
   ```

### Installing in editable mode

Installing from a `pyproject.toml` in editable mode (i.e. `pip install -e`) requires `setuptools>=64`; however, CKAN 2.9 requires `setuptools==44.1.0`. See [our CKAN fork](https://github.com/NaturalHistoryMuseum/ckan) for a version of v2.9 that uses an updated setuptools if this functionality is something you need.

## Post-install setup

1. Add 'ldap' to the list of plugins in your `$CONFIG_FILE`:
   ```ini
   ckan.plugins = ... ldap
   ```

<!--installation-end-->

# Configuration

<!--configuration-start-->
These are the options that can be specified in your .ini config file.

## LDAP configuration **[REQUIRED]**

| Name                         | Description                                                                                                                                                                                                                         | Options    |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| `ckanext.ldap.uri`           | The URI of the LDAP server, of the form _ldap://example.com_. You can use the URI to specify TLS (use 'ldaps' protocol), and the port number (suffix ':port').                                                                      | True/False |
| `ckanext.ldap.base_dn`       | The base dn in which to perform the search. Example: 'ou=USERS,dc=example,dc=com'.                                                                                                                                                  |            |
| `ckanext.ldap.search.filter` | This is the search string that is sent to the LDAP server, in which '{login}' is replaced by the user name provided by the user. Example: 'sAMAccountName={login}'. The search performed here **must** return exactly 0 or 1 entry. |            |
| `ckanext.ldap.username`      | The LDAP attribute that will be used as the CKAN username. This **must** be unique.                                                                                                                                                 |            |
| `ckanext.ldap.email`         | The LDAP attribute to map to the user's email address. This **must** be unique.                                                                                                                                                     |            |

## Other options

| Name                                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Options                         | Default  |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|----------|
| `ckanext.ldap.ckan_fallback`        | If true this will attempt to log in against the CKAN user database when no LDAP user exists.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | True/False                      | False    |
| `ckanext.ldap.prevent_edits`        | If true, this will prevent LDAP users from editing their profile. Note that there is no problem in allowing users to change their details - even their user name can be changed. But you may prefer to keep things centralized in your LDAP server. **Important**: while this prevents the operation from happening, it won't actually remove the 'edit settings' button from the dashboard. You need to do this in your own template.                                                                                                                                                                                                                                                                                                                                                                                                                                  | True/False                      | False    |
| `ckanext.ldap.auth.dn`              | DN to use if LDAP server requires authentication.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                 |          |
| `ckanext.ldap.auth.password`        | Password to use if LDAP server requires authentication.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |                                 |          |
| `ckanext.ldap.auth.method`          | Authentication method                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | SIMPLE, SASL                    |          |
| `ckanext.ldap.auth.mechanism`       | SASL mechanism to use, if auth.method is set to SASL.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |                                 |          |
| `ckanext.ldap.fullname`             | The LDAP attribute to map to the user's full name.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |                                 |          |
| `ckanext.ldap.about`                | The LDAP attribute to map to the user's description.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |                                 |          |
| `ckanext.ldap.organization.id`      | If this is set, users that log in using LDAP will automatically get added to the given organization. **Warning**: Changing this parameter will only affect users that have not yet logged on. It will not modify the organization of users who have already logged on. **Warning**: The organization to which to add LDAP users must already exist; the first user logging in will not automatically create it and instead you will see a "500 Server Error" returned.                                                                                                                                                                                                                                                                                                                                                                                                  |                                 |          |
| `ckanext.ldap.organization.role`    | The role given to users added in the given organization ('admin', 'editor' or 'member'). **Warning**: Changing this parameter will only affect users that have not yet logged on. It will not modify the role of users who have already logged on. This is only used if `ckanext.ldap.organization.id` is set. There is currently no functionality for mapping LDAP groups to CKAN roles, so this just assigns the same role to _every_ new LDAP user.                                                                                                                                                                                                                                                                                                                                                                                                                  | member, editor, admin           | 'member' |
| `ckanext.ldap.search.alt`           | An alternative search string for the LDAP filter. If this is present and the search using `ckanext.ldap.search.filter` returns exactly 0 results, then a search using this filter will be performed. If this search returns exactly one result, then it will be accepted. You can use this for example in Active Directory to match against both username and fullname by setting `ckanext.ldap.search.filter` to  'sAMAccountName={login}' and `ckanext.ldap.search.alt` to 'name={login}'. The approach of using two separate filter strings (rather than one with an or statement) ensures that priority will always be given to the unique id match. `ckanext.ldap.search.alt` however can  be used to match against more than one field. For example you could match against either the full name or the email address by setting `ckanext.ldap.search.alt` to '(\ | (name={login})(mail={login}))'. |          |
| `ckanext.ldap.search.alt_msg`       | A message that is output to the user when the search on `ckanext.ldap.search.filter` returns 0 results, and the search on `ckanext.ldap.search.alt` returns more than one result. Example: 'Please use your short account name instead'.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |                                 |          |
| `ckanext.ldap.migrate`              | If true this will change an existing CKAN user with the same username to an LDAP user. Otherwise, an exception `UserConflictError`is raised if LDAP-login with an already existing local CKAN username is attempted. This option provides a migration path from local CKAN authentication to LDAP authentication: Rename all users to their LDAP usernames and instruct them to login with their LDAP credentials. Migration then happens transparently.                                                                                                                                                                                                                                                                                                                                                                                                                | True/False                      | False    |
| `ckanext.ldap.debug_level`          | [python-ldap debug level](https://www.python-ldap.org/en/python-ldap-3.0.0b1/reference/ldap.html?highlight=debug_level#ldap.OPT_DEBUG_LEVEL). **Security warning**: it is strongly recommended to keep this parameter set to 0 (zero) on production systems, otherwise [plaintext passwords will be logged by `python-ldap`](https://github.com/python-ldap/python-ldap/issues/384)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 0-9                             | 0        |
| `ckanext.ldap.trace_level`          | [python-ldap trace level](https://www.python-ldap.org/en/python-ldap-3.0.0b1/reference/ldap.html?highlight=trace_level#ldap.initialize). **Security warning**: it is strongly recommended to keep this parameter set to 0 (zero) on production systems, otherwise [plaintext passwords will be logged by `python-ldap`](https://github.com/python-ldap/python-ldap/issues/384)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | 0-9                             | 0        |
| `ckanext.ldap.allow_password_reset` | If true, allows LDAP users to reset their passwords, if false, disallows this functionality. Note that if this is true, the password that is reset is the CKAN user password, not the LDAP one. If set to false, the request to reset will be denied only if the user is an LDAP user, if not they will be allowed to reset regardless of the value of this option.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | True/False                      | true     |

<!--configuration-end-->

# Usage

<!--usage-start-->
## Example Test Configuration
To test that the extension is working correctly without having to set up an LDAP service yourself, you can try this config snippet:

```ini
ckanext.ldap.uri = ldap://ldap.forumsys.com:389
ckanext.ldap.base_dn = dc=example,dc=com
ckanext.ldap.search.filter = cn=*{login}*
ckanext.ldap.username = cn
ckanext.ldap.auth.dn = cn=read-only-admin,dc=example,dc=com
ckanext.ldap.email = mail
ckanext.ldap.auth.password = password
ckanext.ldap.auth.method = SIMPLE
```

See [here](https://www.forumsys.com/tutorials/integration-how-to/ldap/online-ldap-test-server/) for more information.
Then just login with `tesla` or `gauss` for example with `password` as the password.

## Commands

### `ldap`

1. `setup-org`: create the organisation specified in `ckanext.ldap.organization.id`.
    ```bash
    ckan -c $CONFIG_FILE ldap setup-org
    ```

2. `initdb`: ensure the tables needed by this extension exist.
    ```bash
    ckan -c $CONFIG_FILE ldap initdb
    ```

## Templates

This extension overrides `templates/user/login.html` and sets the form action to the LDAP login handler.

To use it elsewhere:

```html+jinja
{% set ldap_action = h.get_login_action() %}
{% snippet "user/snippets/login_form.html", action=ldap_action, error_summary=error_summary %}
```

The helper function `h.is_ldap_user()` is also provided for templates.

<!--usage-end-->

# Testing

<!--testing-start-->
There is a Docker compose configuration available in this repository to make it easier to run tests. The ckan image uses the Dockerfile in the `docker/` folder.

To run the tests against ckan 2.9.x on Python3:

1. Build the required images:
   ```shell
   docker-compose build
   ```

2. Then run the tests.
   The root of the repository is mounted into the ckan container as a volume by the Docker compose
   configuration, so you should only need to rebuild the ckan image if you change the extension's
   dependencies.
   ```shell
   docker-compose run ckan
   ```

<!--testing-end-->
