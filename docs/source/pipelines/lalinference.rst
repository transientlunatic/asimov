.. _lalinference-pipelines:

LALInference pipeline
=====================

Asimov provides support for the `LALInference <https://lscsoft.docs.ligo.org/lalsuite/lalinference/>`_ pipeline.
While LALInference has been largely superseded by bilby and RIFT for new analyses, the interface
remains useful for cross-checks and for replicating older results.

Review status
-------------

.. warning::
   The LALInference integration has been deprecated and must not be used for new collaboration
   parameter estimation analyses.

Quick start
-----------

A LALInference blueprint requires specifying the inference engine (``lalinferencenest`` for
nested sampling, or ``lalinferencemcmc`` for MCMC):

.. code-block:: yaml

   kind: analysis
   name: pe-lalinference
   pipeline: lalinference
   comment: LALInference nested sampling.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   engine: lalinferencenest
   nparallel: 8

Apply it to an event with:

.. code-block:: console

   $ asimov apply -f lalinference.yaml --event GW150914_095045

Examples
--------

Nested sampling
~~~~~~~~~~~~~~~

.. code-block:: yaml

   kind: analysis
   name: lalinference-nest
   pipeline: lalinference
   comment: LALInference with nested sampling.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   engine: lalinferencenest
   nparallel: 25
   needs:
     - pipeline: bayeswave

Markov Chain Monte Carlo
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   kind: analysis
   name: lalinference-mcmc
   pipeline: lalinference
   comment: LALInference with MCMC.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   engine: lalinferencemcmc
   nparallel: 25
   needs:
     - pipeline: bayeswave

Blueprint settings reference
-----------------------------

See :ref:`blueprints` for the full precedence rules and :ref:`template-reference` for how
these settings map to variables inside the configuration template.

Top-level analysis settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``engine``
     - str
     - The LALInference inference engine. Either ``"lalinferencenest"`` (nested sampling) or ``"lalinferencemcmc"`` (MCMC). **Required.**
   * - ``nparallel``
     - int
     - Number of parallel chains or threads. **Required.**

``waveform`` settings
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``waveform:approximant``
     - str
     - Waveform approximant (e.g. ``IMRPhenomXPHM``). **Required.**
   * - ``waveform:reference frequency``
     - float
     - Reference frequency in Hz. **Required.**
   * - ``waveform:pn amplitude order``
     - int
     - Post-Newtonian amplitude order. Defaults to ``0``.

``likelihood`` settings
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``likelihood:sample rate``
     - int
     - Sample rate in Hz. **Required.**
   * - ``likelihood:start frequency``
     - float
     - Waveform generation start frequency.

``scheduler`` settings
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``scheduler:accounting group``
     - str
     - HTCondor accounting group. Required on most clusters.
   * - ``scheduler:environment``
     - str
     - Path to the LALSuite software installation. Falls back to the global ``[pipelines] environment`` setting.

Analysis states
---------------

LALInference analyses pass through the standard asimov states.
See :ref:`states` for the full state machine description.

See also
--------

* :ref:`template-reference` — Full Liquid template variable reference
* :ref:`blueprints` — Blueprint YAML format and settings hierarchy
* :doc:`bilby` — The recommended replacement for LALInference
