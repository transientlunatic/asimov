.. _python-api-tutorial:

Using the Python API
====================

This tutorial shows how to create and manage an asimov project entirely from Python,
using the testing pipelines that ship with asimov.
No HTCondor cluster is required to follow most of the steps.

By the end you will know how to:

* Create a project and add events from Python
* Apply blueprints programmatically
* Inspect analysis status from Python

Prerequisites
-------------

Install asimov with no optional extras:

.. code-block:: console

   $ pip install asimov

All examples below can be run in a plain Python script or a Jupyter notebook.

Step 1 — Create a project
--------------------------

.. code-block:: python

   from asimov.project import Project

   project = Project(
       name="API Tutorial",
       location="/tmp/api-tutorial"
   )
   print(project)
   # <Project 'API Tutorial' at /tmp/api-tutorial>

This creates the same directory structure as ``asimov init``:

.. code-block:: text

   /tmp/api-tutorial/
   ├── .asimov/
   │   ├── asimov.conf
   │   └── ledger.yml
   ├── working/
   ├── checkouts/
   ├── results/
   └── logs/

.. note::
   If the directory already contains a project, ``Project()`` raises ``RuntimeError``.
   Load existing projects with :meth:`~asimov.project.Project.load` instead.

Step 2 — Add events
--------------------

All mutating operations must happen inside a ``with project:`` block.
The block saves the ledger atomically when it exits without error:

.. code-block:: python

   with project:
       gw150914 = project.add_subject(name="GW150914_095045")
       gw151012 = project.add_subject(name="GW151012_095443")

   # Verify they were added
   for event in project.get_event():
       print(event.name)
   # GW150914_095045
   # GW151012_095443

Step 3 — Apply blueprints
--------------------------

The cleanest way to attach analyses is to write blueprint files and apply them with
``asimov apply``.
Here we write a blueprint for the testing pipeline, which requires no real software
and completes immediately:

.. code-block:: python

   import os
   import subprocess

   blueprint = """\
   kind: analysis
   name: test-run
   pipeline: simpletestpipeline
   comment: Quick test without a cluster.
   """

   blueprint_file = "/tmp/api-tutorial/test-analysis.yaml"
   with open(blueprint_file, "w") as f:
       f.write(blueprint)

   for event_name in ["GW150914_095045", "GW151012_095443"]:
       subprocess.run(
           ["asimov", "apply", "-f", blueprint_file, "--event", event_name],
           check=True,
           cwd="/tmp/api-tutorial",
       )

Step 4 — Inspect the project
------------------------------

Load the project back (or keep the existing object) and inspect events and their
analyses:

.. code-block:: python

   project = Project.load("/tmp/api-tutorial")

   for event in project.get_event():
       print(f"\n{event.name}")
       for prod in event.productions:
           print(f"  {prod.name:20s}  pipeline={prod.pipeline}  status={prod.status}")

Typical output::

   GW150914_095045
     test-run              pipeline=simpletestpipeline  status=ready

   GW151012_095443
     test-run              pipeline=simpletestpipeline  status=ready

Step 5 — Run the monitor
-------------------------

The monitor loop checks analysis status, submits ready analyses, and collects
finished results.

From the project directory you can run the monitor once from the CLI:

.. code-block:: console

   $ cd /tmp/api-tutorial
   $ asimov monitor

Or from Python using :func:`~asimov.monitor_api.run_monitor`:

.. code-block:: python

   import os
   os.chdir("/tmp/api-tutorial")

   from asimov.monitor_api import run_monitor
   results = run_monitor(verbose=True)

.. note::
   ``run_monitor()`` requires access to an HTCondor scheduler for real pipelines.
   The testing pipelines (:class:`~asimov.pipelines.testing.SimpleTestPipeline` etc.)
   simulate submission without a cluster, but the monitor infrastructure still
   attempts to contact Condor to track running jobs.
   For fully offline testing, use the :class:`~asimov.testing.AsimovTestCase`
   base class (see :doc:`/test-interface`).

Step 6 — Building on this
--------------------------

Once you have the basics working, you can use the full blueprint vocabulary to set
up real analyses:

.. code-block:: python

   bilby_blueprint = """\
   kind: analysis
   name: pe-bilby
   pipeline: bilby
   comment: IMRPhenomXPHM parameter estimation.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   likelihood:
     marginalization:
       distance: true
   needs:
     - pipeline: bayeswave
   """

   with open("/tmp/api-tutorial/bilby.yaml", "w") as f:
       f.write(bilby_blueprint)

   subprocess.run(
       ["asimov", "apply", "-f", "/tmp/api-tutorial/bilby.yaml",
        "--event", "GW150914_095045"],
       check=True,
       cwd="/tmp/api-tutorial",
   )

See :doc:`/pipelines/bilby` for a full reference of bilby blueprint settings.

Complete Script
---------------

The full sequence above, in a single script:

.. code-block:: python

   import os
   import subprocess
   from asimov.project import Project

   PROJECT_DIR = "/tmp/api-tutorial-complete"
   EVENTS = ["GW150914_095045", "GW151012_095443", "GW151226_033853"]

   # --- 1. Create project ---
   project = Project(name="API Tutorial Complete", location=PROJECT_DIR)

   # --- 2. Add events ---
   with project:
       for name in EVENTS:
           project.add_subject(name=name)

   # --- 3. Apply blueprint ---
   blueprint = """\
   kind: analysis
   name: test-run
   pipeline: simpletestpipeline
   comment: Testing pipeline — no cluster required.
   """
   bp_file = os.path.join(PROJECT_DIR, "test.yaml")
   with open(bp_file, "w") as f:
       f.write(blueprint)

   for name in EVENTS:
       subprocess.run(
           ["asimov", "apply", "-f", bp_file, "--event", name],
           check=True, cwd=PROJECT_DIR,
       )

   # --- 4. Inspect ---
   project = Project.load(PROJECT_DIR)
   for event in project.get_event():
       for prod in event.productions:
           print(f"{event.name}  {prod.name}  [{prod.status}]")

See also
--------

* :doc:`/python-api` — Python API reference
* :ref:`blueprints` — Full blueprint YAML format
* :doc:`/pipelines/bilby` — Bilby pipeline settings
* :doc:`/monitor-api` — ``run_monitor()`` API reference
