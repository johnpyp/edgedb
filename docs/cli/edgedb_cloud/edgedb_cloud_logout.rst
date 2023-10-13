.. _ref_cli_edgedb_cloud_logout:


===================
edgedb cloud logout
===================

.. note::

    This CLI command requires CLI version 3.0 or later.

Logs out, forgetting the stored access token.

.. cli:synopsis::

    edgedb cloud logout [<options>]

Options
=======

:cli:synopsis:`--all-profiles`
    Logs out from all Cloud profiles
:cli:synopsis:`--force`
    Forces log out from all profiles, even if linked to a project
:cli:synopsis:`--non-interactive`
    Do not ask questions, assume user wants to log out of all profiles not
    linked to a project
