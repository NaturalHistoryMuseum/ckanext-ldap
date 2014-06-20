ckanext-ldap
============

Overview
--------

This plugin provides LDAP authentication for CKAN. Features include:

- Imports username, full name, email and description;
- Can match against several LDAP fields (eg. username or full name);
- Allows to have LDAP only authentication, or combine LDAP and basic CKAN authentication;
- Can add LDAP users to a given organization automatically;
- Works with Active Directory.

Requirements
------------

This plugin uses the pythton-ldap module. This available to install via pip:

```sh
  pip install python-ldap
```

Unless you install this from a binary, then building this will require ldap2, sasl2 and ssl development packages to
be installed on your system. Under Debian and derivatives these can be installed by doing:

```sh
apt-get install libldap2-dev libsasl2-dev libssl-dev
```

Configuration
-------------

Configuration of an LDAP client is always tricky. Unfortunately this really varies from system to system - we cannot 
provide general advice, you need to check with the LDAP server administrator.

The plugin provides the following **required** configuration items:

- `ldap.uri`: The URI of the LDAP server, of the form _ldap://example.com_. You can use the URI to specify TLS 
              (use 'ldaps' protocol), and the port number (suffix ':port');
- `ldap.base_dn`: The base dn in which to perform the search. Example: 'ou=USERS,dc=example,dc=com';
- `ldap.search.filter`: This is the search string that is sent to the LDAP server, in which '{login}' is replaced by the
                 user name provided by the user. Example: 'sAMAccountName={login}'. The search performed here **must** 
                 return exactly 0 or 1 entry. See `ldap.search.alt` to provide search on alternate fields;
- `ldap.username`: The LDAP attribute that will be used as the CKAN username. This **must** be unique;
- `ldap.email`: The LDAP attribute to map to the user's email address. This **must** be unique.

In addition the plugin provides the following optional configuration items:

- `ldap.ckan_fallback`: If defined and true this will attempt to log in against the CKAN user database when no LDAP user 
                        exists;
- `ldap.prevent_edits`: If defined and true, this will prevent LDAP users from editing their profile. Note that there
                        is no problem in allowing users to change their details - even their user name can be changed.
                        But you may prefer to keep things centralized in your LDAP server. **Important**: while this
                        prevents the operation from happening, it won't actually remove the 'edit settings' button
                        from the dashboard. You need to do this in your own template;
- `ldap.auth.dn`: If your LDAP server requires authentication (eg. Active Directory), this should be the DN to use;
- `ldap.auth.password`: If your LDAP server requires authentication, add the password here;
- `ldap.fullname`: The LDAP attribute to map to the user's full name;
- `ldap.about`: The LDAP attribute to map to the user's description;
- `ldap.organization.id`: If this is set, users that log in using LDAP will automatically get added to the given
                          organization. **Warning**: Changing this parameter will only affect users that have not yet
                          logged on. It will not modify the organization of users who have already logged on;
- `ldap.organization.role`: The role given to users added in the given organization ('admin', 'editor' or 'member').
                            **Warning**: Changing this parameter will only affect users that have not yet logged on.
                            It will not modify the role of users who have already logged on;
- `ldap.search.alt`: An alternative search string for the LDAP filter. If this is present and the search using
                     `ldap.search.filter` returns exactly 0 results, then a search using this filter will be performed.
                     If this search returns exactly one result, then it will be accepted. You can use this for example
                     in Active Directory to match against both username and fullname by setting `ldap.search.filter` to 
                     'sAMAccountName={login}' and `ldap.search.alt` to 'name={login}'
                     
                     The approach of using two separate filter strings (rather than one with an or statement) 
                     ensures that priority will always be given to the unique id match. `ldap.search.alt` however can 
                     be used to match against more than one field. For example you could match against either the full name or
                     the email address by setting `ldap.search.alt` to '(|(name={login})(mail={login}))'.
- `ldap.search.alt_msg`: A message that is output to the user when the search on `ldap.search.filter` returns 0 results,
                         and the search on `ldap.search.alt` returns more than one result. Example: 'Please use your short
                         account name instead'.