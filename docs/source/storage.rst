.. _storage:

=================
Storage Interface
=================

In order to ensure the veracity of results files, asimov implements an interface
for storing results files from pipelines.

Results are stored in directories called **Stores**.
When files are checked in and out they are verified by comparing their MD5 hash to
the hash recorded when the file was originally stored.
Additional safety can be guaranteed by asserting that the file matches an externally
provided hash.

The storage interface was developed to replace the need for ``git`` to store large
results files, while guaranteeing that file content has not been edited or corrupted
after production.
Files stored in a Store are write-once-read-only; once a file is stored it is never
edited.
This follows the overall asimov philosophy: if changes must be made, create a new
analysis rather than overwriting existing results.

When to Use the Store vs. the Event Git Repository
----------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Use the **Store**
     - Use the **event git repository**
   * - Large results files (posterior samples, PSD files, summary pages)
     - Configuration files, blueprints, small input data
   * - Files that must be read-only after they are created
     - Files that are iterated on during development
   * - Content-addressed access by UUID (integrity-checked retrieval)
     - Version-controlled access by git history
   * - Pipeline output artefacts
     - Pipeline input templates, scripts

---

Python API
----------

The Python API lives in ``asimov.storage``.
The two main classes are:

* :class:`~asimov.storage.Store` — file-system operations and file management
* :class:`~asimov.storage.Manifest` — low-level manifest file handling
  (you do not normally need to use this directly)

Creating a store
~~~~~~~~~~~~~~~~

.. code-block:: python

   from asimov.storage import Store

   store = Store.create("/data/results/my_store", "My Store")

``Store.create`` creates the directory and a ``.manifest`` subdirectory that tracks
all files in the store.

Storing a file
~~~~~~~~~~~~~~

Use :meth:`~asimov.storage.Store.add_file` to check a file into the store.
Files are organised in a three-level hierarchy: ``event / production / filename``.

.. code-block:: python

   from asimov.storage import Store

   store = Store("/data/results/my_store")

   record = store.add_file("GW150914_095045", "pe-bilby", "posterior_samples.hdf5")
   print(record)
   # {'uuid': 'f9f167be-e8e3-449a-a0c6-8bf7f91e7b7a', 'hash': 'd41d8cd9...'}

The returned dictionary contains the UUID and MD5 hash.
Store these in the analysis ledger or a database if you need to retrieve the file
later by UUID.

A file named ``shared`` can be used for resources shared between multiple analyses:

.. code-block:: python

   store.add_file("GW150914_095045", "shared", "calibration.hdf5")

Retrieving a file
~~~~~~~~~~~~~~~~~

Use :meth:`~asimov.storage.Store.fetch_file` to retrieve a file.
The method looks up the UUID, copies the file to the current directory, and checks
its MD5 hash against the manifest:

.. code-block:: python

   store = Store("/data/results/my_store")

   store.fetch_file("GW150914_095045", "pe-bilby", "posterior_samples.hdf5")

Optionally pass an expected hash to perform an additional integrity check:

.. code-block:: python

   store.fetch_file(
       "GW150914_095045", "pe-bilby", "posterior_samples.hdf5",
       hash="d41d8cd98f00b204e9800998ecf8427e"
   )

If any hash check fails, :exc:`~asimov.storage.HashError` is raised and the file
is not returned.

---

The ``locutus`` CLI
--------------------

``locutus`` is a command-line interface to the storage API.
It is installed alongside ``asimov``.

All ``locutus`` commands must be run from inside the Store directory (the one
containing the ``.manifest`` subdirectory), or from a directory that has a Store
configured in the asimov project settings.

.. code-block:: console

   $ locutus --help
   Usage: locutus [OPTIONS] COMMAND [ARGS]...

   Commands:
     init   Initialise a new Store
     store  Store a file in the Store.
     fetch  Fetch a file from an event production.
     list   List files stored for an event production.
     info   Check the information about this Store.

``locutus init``
~~~~~~~~~~~~~~~~~

Initialise a new Store in the current directory:

.. code-block:: console

   $ locutus init --name "GWTC-3 Results"

Options:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - ``--name TEXT``
     - Human-readable name for the store.

``locutus store``
~~~~~~~~~~~~~~~~~

Add a file to the store:

.. code-block:: console

   $ locutus store GW150914_095045 pe-bilby posterior_samples.hdf5

Arguments: ``EVENT  PRODUCTION  FILENAME``

``locutus fetch``
~~~~~~~~~~~~~~~~~

Retrieve a file from the store into the current directory:

.. code-block:: console

   $ locutus fetch GW150914_095045 pe-bilby posterior_samples.hdf5

Optionally verify against a known hash:

.. code-block:: console

   $ locutus fetch GW150914_095045 pe-bilby posterior_samples.hdf5 \
       --hash d41d8cd98f00b204e9800998ecf8427e

Arguments: ``EVENT  PRODUCTION  FILENAME``

Options:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - ``--hash TEXT``
     - Optional expected MD5 hash. Raises an error if the retrieved file does not match.

``locutus list``
~~~~~~~~~~~~~~~~

List all files stored for a given event and production:

.. code-block:: console

   $ locutus list GW150914_095045 pe-bilby

Arguments: ``EVENT  PRODUCTION``

``locutus info``
~~~~~~~~~~~~~~~~

Print information about the current Store:

.. code-block:: console

   $ locutus info

---

Manifest files
--------------

A manifest file (``.manifest/manifest.yml`` inside the store root) records every
file that has been checked in.
The format is a YAML hierarchy:

.. code-block:: yaml

   name: My Store
   events:
     GW150914_095045:
       pe-bilby:
         posterior_samples.hdf5:
           hash: d41d8cd98f00b204e9800998ecf8427e
           uuid: f9f167be-e8e3-449a-a0c6-8bf7f91e7b7a

The :class:`~asimov.storage.Manifest` Python class provides helpers for reading and
writing manifests, but under normal usage you do not need to interact with it directly.
