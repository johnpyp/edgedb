.. _ref_cli_edgedb_instance_upgrade:


=======================
edgedb instance upgrade
=======================

Upgrades an EdgeDB instance or installation.

.. cli:synopsis::

    edgedb instance upgrade [<options>] [<name>]


Description
===========

This command is used to upgrade EdgeDB instances individually or in
bulk.

.. note::

    The ``edgedb instance upgrade`` command is not intended for use with
    self-hosted instances.


Options
=======

:cli:synopsis:`<name>`
    The EdgeDB instance name to upgrade.

:cli:synopsis:`--force`
    Forces the upgrade process even if there is no new version.

:cli:synopsis:`--to-latest`
    Upgrades a specified instance to the latest major version.

:cli:synopsis:`--to-nightly`
    Upgrades a specified instance to a latest nightly version.

:cli:synopsis:`--local-minor`
    Upgrades all local instances to the latest minor versions.

:cli:synopsis:`--to-version=<version>`
    Upgrades to a specified major version.

:cli:synopsis:`-v, --verbose`
    Verbose output.
