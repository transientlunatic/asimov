================
Extending Asimov
================

Asimov is designed to be extended via **hooks** — Python classes registered through
`setuptools entry points <https://setuptools.pypa.io/en/latest/userguide/entry_point.html>`_
and discovered automatically at runtime.
Two hook types are supported:

* **applicator** — provides data to a project via ``asimov apply -p <plugin>``
* **postmonitor** — runs at the end of every monitor loop iteration

Both types share the same basic structure: a class with ``__init__(self, ledger)``
and a ``run()`` method, registered under a named entry point group.

---

Applicator Hooks
----------------

An applicator hook lets an external package supply event data to an asimov project
without writing a YAML blueprint by hand.
The `cbcflow <https://git.ligo.org/cbc/cbcflow>`_ integration is one example.

When the user runs:

.. code-block:: console

   $ asimov apply -p my-plugin --event GW150914_095045

Asimov discovers all entry points in the ``asimov.hooks.applicator`` group, finds
the one named ``my-plugin``, instantiates it with the current ledger, and calls
``run(event_name)``.

Writing an applicator hook
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a Python class with:

* ``__init__(self, ledger)`` — receives the current
  :class:`~asimov.ledger.YAMLLedger` instance
* ``run(self, event)`` — receives the event name string passed via ``--event``

.. code-block:: python

   # my_package/applicator.py

   from asimov.event import Event
   from asimov.cli.application import apply_page

   class MyApplicator:
       """Fetch event data from an external source and apply it to the project."""

       def __init__(self, ledger):
           self.ledger = ledger

       def run(self, event):
           """
           Pull data for *event* from an external source and add or update
           it in the project ledger.
           """
           # Example: fetch data from an external service
           data = self._fetch(event)

           # Build a minimal event blueprint and apply it
           blueprint = f"""
   kind: event
   name: {data['name']}
   gps time: {data['gps']}
   repository: {data['repo']}
   """
           import tempfile, os
           with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
               f.write(blueprint)
               tmp = f.name
           try:
               apply_page(tmp, ledger=self.ledger)
           finally:
               os.unlink(tmp)

       def _fetch(self, event_name):
           # Replace with your actual data source
           raise NotImplementedError

Registering the applicator
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add an entry point in your package's ``pyproject.toml``:

.. code-block:: toml

   [project.entry-points."asimov.hooks.applicator"]
   my-plugin = "my_package.applicator:MyApplicator"

After reinstalling your package (``pip install -e .``), the hook is discoverable.
Run it with:

.. code-block:: console

   $ asimov apply -p my-plugin --event GW150914_095045

---

Postmonitor Hooks
-----------------

A postmonitor hook is executed at the end of every monitor loop iteration,
after all analyses have been checked.
It is the right place for reporting, data export, or any action that should happen
once per monitoring cycle across the whole project.

The hook class is instantiated with a *copy* of the ledger (so modifications do not
affect the live ledger) and its ``run()`` method is called with no arguments.

Writing a postmonitor hook
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a Python class with:

* ``__init__(self, ledger)`` — receives a deep copy of the current
  :class:`~asimov.ledger.YAMLLedger`
* ``run(self)`` — performs the reporting or export action

.. code-block:: python

   # my_package/reporter.py

   class StatusReporter:
       """Post each event's analysis statuses to an external dashboard."""

       def __init__(self, ledger):
           self.ledger = ledger

       def run(self):
           """Called once per monitor loop iteration."""
           summary = {}
           for event in self.ledger.get_event():
               summary[event.name] = {
                   prod.name: prod.status
                   for prod in event.productions
               }
           self._post(summary)

       def _post(self, summary):
           import requests
           requests.post(
               "https://my-dashboard.example.com/api/status",
               json=summary,
               timeout=10,
           )

Registering the hook
~~~~~~~~~~~~~~~~~~~~~

Add an entry point in ``pyproject.toml``:

.. code-block:: toml

   [project.entry-points."asimov.hooks.postmonitor"]
   status-reporter = "my_package.reporter:StatusReporter"

After reinstalling, activate the hook for your project by applying a
``kind: configuration`` blueprint:

.. code-block:: yaml

   kind: configuration
   hooks:
     postmonitor:
       status-reporter: {}

.. code-block:: console

   $ asimov apply -f reporter-hook.yaml

From this point on, ``StatusReporter.run()`` is called at the end of every
``asimov monitor`` iteration.

Deactivating the hook
~~~~~~~~~~~~~~~~~~~~~~

Apply an updated configuration blueprint that removes the hook name from
``hooks.postmonitor``, or remove the entry from the ledger manually.

---

Summary
-------

.. list-table::
   :header-rows: 1
   :widths: 25 35 20 20

   * - Hook type
     - Entry point group
     - ``__init__`` args
     - ``run()`` args
   * - Applicator
     - ``asimov.hooks.applicator``
     - ``ledger``
     - ``event`` (name string)
   * - Postmonitor
     - ``asimov.hooks.postmonitor``
     - ``ledger`` (deep copy)
     - *(none)*

See also
--------

* :doc:`pipelines-dev` — How to write a full pipeline plugin
* :ref:`blueprints` — Blueprint YAML format (``kind: configuration`` for activating hooks)
