.. eql:section-intro-page:: cli

.. _ref_cli_overview:

===
CLI
===

:edb-alt-title: The EdgeDB CLI

The ``edgedb`` command-line interface (CLI) lets you install EdgeDB,
spin up local or cloud instances, open the REPL or EdgeDB UI, execute queries,
manage auth roles, introspect schema, create migrations, and more.

You can install it with one shell command.

.. _ref_cli_edgedb_install:

.. rubric:: Installation

On Linux or MacOS, run the following in your terminal and follow the
on-screen instructions:

.. code-block:: bash

    $ curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh

For Windows, the installation script is:

.. code-block:: powershell

    PS> iwr https://ps1.edgedb.com -useb | iex

* The `script <https://sh.edgedb.com>`_, inspired by 
  `rustup <https://rustup.rs/>`_, will detect the OS and download the
  appropriate build of the EdgeDB CLI tool, ``edgedb``.
* The ``edgedb`` command is a single executable (it's `open source!
  <https://github.com/edgedb/edgedb-cli/>`_)
* Once installed, the ``edgedb`` command can be used to install,
  uninstall, upgrade, and interact with EdgeDB server instances.
* You can uninstall EdgeDB server or remove the ``edgedb`` command at
  any time.


.. rubric:: Connection options

All commands respect a common set of
:ref:`connection options <ref_cli_edgedb_connopts>`, which let you specify
a target instance. This instance can be local to your machine, hosted
remotely, or on EdgeDB Cloud.


.. _ref_cli_edgedb_nightly:

.. rubric:: Nightly version

To install the nightly version of the CLI (not to be confused with the nightly
version of EdgeDB itself!) use this command:

.. code-block:: bash

    $ curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | \
      sh -s -- --nightly


.. _ref_cli_edgedb_uninstall:

.. rubric:: Uninstallation

Command-line tools contain just one binary, so to remove it on Linux or
macOS run:

.. code-block:: bash

   $ rm "$(which edgedb)"

To remove all configuration files, run ``edgedb info`` to list the directories
where EdgeDB stores data, then use ``rf -rf <dir>`` to delete those
directories.

If the command-line tool was installed by the user (recommended) then it
will also remove the binary.

On Windows, the binary can be found inside ``AppData\Roaming`\edgedb\bin``
under your username. For example, for a user named ``lee`` on a standard
Windows PC it will be located at ``C:\Users\lee\AppData\Roaming\edgedb\bin``
and can be removed from there.

Before deleting the tool, you may also want to use the ``edgedb`` command
to remove any existing :ref:`instances <ref_cli_edgedb_instance_destroy>`
and :ref:`server <ref_cli_edgedb_server_uninstall>` packages.

.. code-block:: bash

   $ edgedb instance destroy <instance_name>

To list instances and server versions use the following commands
respectively:

.. code-block:: bash

   $ edgedb instance status
   $ edgedb server list-versions --installed-only


.. _ref_cli_edgedb_config:

.. rubric:: Configure CLI and REPL

You can customize the behavior of the ``edgedb`` CLI and REPL with a
``cli.toml`` global configuration file. The location of ``cli.toml``
differs between operating systems, and can be found with the
:ref:`ref_cli_edgedb_info` command which will display its location in
the ``Config`` row of its output.

The ``cli.toml`` file contains the following parameters, all of which
are optional. An example ``cli.toml`` with all parameters:

.. code-block::

    [shell]
    expand-strings = true
    history-size = 10000
    implicit-properties = false
    input-mode = "emacs"
    limit = 100
    idle-transaction-timeout = "1m1s"
    output-format = "default"
    display-typenames = true
    print-stats = "off"
    verbose-errors = false

* ``expand-strings``: ``true`` to show line breaks in quoted strings with
  ``\n``, ``false`` to display on a single line with ``\n`` shown.
* ``history-size``: Maximum number of queries to keep in the
  ``edgedb.history``file. History can be accessed via the ``\history`` or 
  ``\s`` command.
* ``implicit-properties``: Includes type name inside each query when set
  to ``true``.
* ``input-mode``: One of ``vi``, ``emacs``
* ``limit``: Maximum number of query results to display (default 100). Set to
  0 to disable.
* ``idle-transaction-timeout``: Use a single unbroken string, e.g. ``1m20s``.
* ``output-format``: One of ``default``, ``json``, ``json-pretty``,
  ``json-lines``, ``tab-separated``.
* ``display-typenames``: Setting to ``false`` will display ``Object`` for all
  objects instead of their type names.
* ``print-stats``: Displays time taken after each query. Options: ``off``,
  ``query``, ``detailed``
* ``verbose-errors``: Prints all errors with maximum verbosity when set to
  ``true``, including backtraces.

:ref:`Notes on network usage <ref_cli_edgedb_network>`


.. toctree::
    :maxdepth: 3
    :hidden:

    edgedb_connopts
    network
    edgedb
    edgedb_analyze
    edgedb_configure
    edgedb_cli_upgrade
    edgedb_cloud/index
    edgedb_database/index
    edgedb_describe/index
    edgedb_dump
    edgedb_info
    edgedb_instance/index
    edgedb_list
    edgedb_migrate
    edgedb_migration/index
    edgedb_project/index
    edgedb_query
    edgedb_restore
    edgedb_server/index
    edgedb_ui
    edgedb_watch
