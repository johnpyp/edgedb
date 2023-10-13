.. _ref_cli_edgedb_instance_status:


======================
edgedb instance status
======================

Shows instance information.

.. cli:synopsis::

     edgedb instance status [<options>] [<name>]


Description
===========

``edgedb instance status`` is a terminal command for displaying the
information about EdgeDB instances.


Options
=======

:cli:synopsis:`<name>`
    Shows only the status of the specific EdgeDB instance (running or not,
    and on which ``pid``).

:cli:synopsis:`--json`
    Formats output as JSON.

:cli:synopsis:`--extended`
    Outputs more debug info about each instance.

:cli:synopsis:`--service`
    Shows current systems service information.
