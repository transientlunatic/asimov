Managing projects
=================

Olivaw is the commandline interface for asimov which is designed to make working with your project easier.

Creating projects
-----------------

You can use olivaw to produce a new project, and set up the required directory structure automatically.

The easiest way to do this is by running

.. code-block:: console

		$ olivaw init "Test project"

Which will convert the current directory into an asimov project directory, including producing the ledger file, and creating directories for results storage.

It is possible to customise the project in a number of ways, including specifying alternative locations for the various subdirectories (though you should do this with care).


Cloning projects
----------------

If you need to extend another analysis it might make sense to be able to get access to the settings which were used for its various events and analyses.

To do this asimov allows you to *clone* an existing project by running

.. code-block:: console

		$ olivaw clone path/to/project

This will give you a local copy of everything from that project, including results.

Command documentation
---------------------

.. click:: asimov.olivaw:olivaw
   :prog: olivaw
   :commands: init
   :nested: full
