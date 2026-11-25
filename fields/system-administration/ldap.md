<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/system-administration/">System Administration</a></nav>

# System Administration - LDAP

<!-- related-block -->
<div class="reading-time">1 min read · Updated 23 Nov 2026</div>


## Reference
- Youtube playlist: []()

## Motivation

## Installation - OpenLdap
1. In Fedora/CentOS, we install openldap and 
    ```bash
    yum install -y openldap openldap-servers
    ```
    - Openldap-servers is being installed along with *slapd* daemon, it support multiple of implementations that help in users authentication process.
2. Start the *slapd* daemon service:
    ```bash
    systemctl start slapd

    systemctl enable slapd
    ``` 
3. It uses port 389/tcp, so add this port to the firewall:
    ```bash
    firewall-cmd --permanent --add-port=389/tcp

    firewall-cmd reload
    ```
4. Set the configuration for the LDAP directory, which is a tree of data Entry "DIT" (Directory Information Tree). 
    - Entry is a collection of *Attribute*, where each attribute has name/value pair.
    - Each collection of attributes are defined under *ObjectClass*.
        ```txt
        Tree -> Collection of Entries
        Entry -> ObjectClass -> Attribute -> Name/Value
        Each Entry has a unique Identifier called *DN* (Distinguished Name)
        ```
    - To edit the configuration file:
        ```bash
        ls /etc/openldap/slapd.d/cn\=config
        ```