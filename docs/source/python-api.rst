.. _python-api:

Python API
==========

In addition to the command-line interface, asimov provides a Python API that allows you to
create and manage projects programmatically. This is particularly useful for:

* Setting up a project from a script or Jupyter notebook
* Adding events and applying blueprints without leaving Python
* Inspecting analysis status programmatically
* Integrating asimov into larger automated workflows

The primary interface for configuring analyses remains **blueprints** applied via
:ref:`asimov apply <blueprints>`. The Python API handles project creation, event management,
and status inspection; it does not replace blueprints.

Creating a New Project
----------------------

Use the ``Project`` class to create a new asimov project from Python.
This produces the same directory structure and configuration files as ``asimov init``:

.. code-block:: python

    from asimov.project import Project

    project = Project(
        name="GWTC-3 Reanalysis",
        location="/data/projects/gwtc3"
    )

If the target directory already contains a project, ``Project()`` raises a ``RuntimeError``.
Use :meth:`~asimov.project.Project.load` instead (see below).

Loading an Existing Project
----------------------------

Load a project that was created with ``asimov init`` or a previous ``Project()`` call:

.. code-block:: python

    from asimov.project import Project

    project = Project.load("/data/projects/gwtc3")

Working with the Context Manager
---------------------------------

All mutating operations (adding subjects, applying blueprints via the API) must be performed
inside a ``with project:`` block. The context manager changes into the project directory and
saves the ledger atomically when the block exits without error:

.. code-block:: python

    from asimov.project import Project

    project = Project.load("/data/projects/gwtc3")

    with project:
        subject = project.add_subject(name="GW150914_095045")
        # Further changes happen here; the ledger is written on exit

If an exception is raised inside the block, the ledger is **not** saved, so the project
state is left unchanged.

Adding Subjects (Events)
------------------------

Call :meth:`~asimov.project.Project.add_subject` inside a context block:

.. code-block:: python

    with project:
        gw150914 = project.add_subject(name="GW150914_095045")
        gw151012 = project.add_subject(name="GW151012_095443")
        gw151226 = project.add_subject(name="GW151226_033853")

Applying Blueprints Programmatically
--------------------------------------

After adding subjects, use ``asimov apply`` to attach analyses.
The CLI is the most straightforward way:

.. code-block:: console

    $ asimov apply -f bilby-analysis.yaml --event GW150914_095045

You can also shell out from Python if you want to keep everything in one script:

.. code-block:: python

    import subprocess

    subprocess.run(
        ["asimov", "apply", "-f", "bilby-analysis.yaml",
         "--event", "GW150914_095045"],
        check=True,
        cwd="/data/projects/gwtc3"
    )

See :ref:`blueprints` for the blueprint YAML format and :doc:`pipelines/bilby`,
:doc:`pipelines/rift`, :doc:`pipelines/bayeswave` for pipeline-specific settings.

Inspecting Events and Analyses
--------------------------------

Use :meth:`~asimov.project.Project.get_event` to read back subjects and their analyses:

.. code-block:: python

    project = Project.load("/data/projects/gwtc3")

    # All events
    for event in project.get_event():
        print(f"Event: {event.name}")
        for production in event.productions:
            print(f"  {production.name}  ({production.pipeline})  [{production.status}]")

    # A single event by name
    gw150914 = project.get_event("GW150914_095045")
    print(gw150914.productions)

Running the Monitor
--------------------

To run the monitor loop from Python (equivalent to ``asimov monitor``), use
:func:`~asimov.monitor_api.run_monitor`:

.. code-block:: python

    from asimov.monitor_api import run_monitor

    run_monitor()

Call this after changing into the project directory, or use it inside an
``asimov start`` / ``asimov stop`` managed loop. See :doc:`monitor-api` for details.

Complete Example
----------------

The following script creates a project, adds three O1 events, applies a bilby
blueprint to each, and then inspects the result:

.. code-block:: python

    import subprocess
    from asimov.project import Project

    EVENTS = ["GW150914_095045", "GW151012_095443", "GW151226_033853"]
    PROJECT_DIR = "/data/projects/o1-reanalysis"

    # --- Create the project ---
    project = Project(name="O1 Reanalysis", location=PROJECT_DIR)

    with project:
        for name in EVENTS:
            project.add_subject(name=name)

    # --- Apply a blueprint to each event ---
    blueprint = """
    kind: analysis
    name: pe-bilby
    pipeline: bilby
    comment: IMRPhenomXPHM parameter estimation.
    waveform:
      approximant: IMRPhenomXPHM
      reference frequency: 20
    needs:
      - pipeline: bayeswave
    """

    with open("bilby.yaml", "w") as f:
        f.write(blueprint)

    for name in EVENTS:
        subprocess.run(
            ["asimov", "apply", "-f", "bilby.yaml", "--event", name],
            check=True,
            cwd=PROJECT_DIR,
        )

    # --- Inspect ---
    project = Project.load(PROJECT_DIR)
    for event in project.get_event():
        for prod in event.productions:
            print(f"{event.name}  {prod.name}  [{prod.status}]")

API Reference
-------------

Project Class
~~~~~~~~~~~~~

.. autoclass:: asimov.project.Project
   :members:
   :undoc-members:
   :show-inheritance:
