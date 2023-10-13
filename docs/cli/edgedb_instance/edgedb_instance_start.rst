.. _ref_cli_edgedb_instance_start:


=====================
edgedb instance start
=====================

Starts an EdgeDB instance, changing status from ``inactive`` to ``running``.

.. cli:synopsis::

     edgedb instance start [--foreground] <name>


Description
===========

``edgedb instance start`` is a terminal command for starting a new
EdgeDB instance.

.. note::

    The ``edgedb instance start`` command is not intended for use with
    self-hosted instances.


Options
=======

:cli:synopsis:`<name>`
    The EdgeDB instance name.

:cli:synopsis:`--foreground`
    Starts the instance in the foreground rather than using systemd to
    manage the process (note: you might need to stop the non-foreground
    instance first).
