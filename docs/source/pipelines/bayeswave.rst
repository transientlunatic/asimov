.. _bayeswave-pipelines:

BayesWave pipeline
==================

The BayesWave interface allows asimov to configure, submit, and monitor analyses using
`BayesWave <https://git.ligo.org/lscsoft/bayeswave>`_.
BayesWave is most commonly used as the first analysis of an event to produce on-source
PSD estimates, which are then passed to subsequent parameter estimation analyses.

Review status
-------------

.. note::
   The BayesWave integration is fully reviewed and is suitable for use in all collaboration analyses.

Quick start
-----------

The minimal blueprint for a BayesWave PSD estimation run is:

.. code-block:: yaml

   kind: analysis
   name: generate-psds
   pipeline: bayeswave
   comment: On-source PSD estimation.

Apply it to an event with:

.. code-block:: console

   $ asimov apply -f bayeswave.yaml --event GW150914_095045

BayesWave does not require waveform settings, as it models the data as a sum of sine-Gaussian
wavelets rather than using a compact binary waveform model.

Passing PSDs to downstream analyses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BayesWave exports its PSD estimates as an asset.
A downstream bilby or RIFT analysis can declare a dependency on BayesWave and
asimov will automatically pass the PSD file paths through to that analysis:

.. code-block:: yaml

   kind: analysis
   name: generate-psds
   pipeline: bayeswave
   comment: On-source PSD estimation.
   ---
   kind: analysis
   name: pe-bilby
   pipeline: bilby
   comment: Parameter estimation using BayesWave PSDs.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   needs:
     - generate-psds

Examples
--------

On-source PSD generation (O3 default)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This was the default BayesWave setup used in the GWTC-2.1 and GWTC-3 catalog analyses:

.. code-block:: yaml

   kind: analysis
   name: generate-psds
   pipeline: bayeswave
   comment: On-source PSD estimation.
   likelihood:
     sample rate: 4096
     segment length: 4
     iterations: 100000
     chains: 8
     threads: 4
   scheduler:
     accounting group: ligo.dev.o4.cbc.pe.bilby
     request memory: 8192 MB
     request post memory: 16384 MB

Blueprint settings reference
-----------------------------

The settings below can be specified in a BayesWave blueprint at any level of the hierarchy
(global, pipeline-defaults, event, or analysis-specific).
See :ref:`blueprints` for the full precedence rules and :ref:`template-reference` for how
these settings map to variables inside the configuration template.

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
   * - ``likelihood:psd length``
     - float
     - PSD estimation segment length in seconds. Defaults to ``segment length``.
   * - ``likelihood:window length``
     - float
     - Analysis window length in seconds. Defaults to ``segment length``.
   * - ``likelihood:segment start``
     - float
     - GPS start time of the analysis segment. If not set, derived from the event time and segment length so that the event time falls two seconds before the end of the segment.
   * - ``likelihood:roll off time``
     - float
     - Window roll-off time in seconds. Defaults to ``1.0``.
   * - ``likelihood:iterations``
     - int
     - Number of MCMC iterations. Defaults to ``100000``.
   * - ``likelihood:chains``
     - int
     - Number of MCMC chains. Defaults to ``8``.
   * - ``likelihood:threads``
     - int
     - Number of threads per chain. Defaults to ``4``.

``data`` settings (BayesWave-specific)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``data:cache files``
     - dict
     - Maps each IFO to a cache file path. When provided, BayesWave reads data from these files rather than using datafind.

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
   * - ``scheduler:request memory``
     - str
     - Memory to request for the main BayesWave jobs. Defaults to ``"8192 MB"``.
   * - ``scheduler:request post memory``
     - str
     - Memory to request for BayesWavePost jobs. Defaults to ``"16384 MB"``.
   * - ``scheduler:request disk``
     - str
     - Disk space to request for BayesWave jobs. Defaults to ``"64 MB"``.
   * - ``scheduler:request post disk``
     - str
     - Disk space to request for BayesWavePost jobs. Defaults to ``"64 MB"``.
   * - ``scheduler:environment``
     - str
     - Path to the BayesWave software installation. Falls back to the global ``[pipelines] environment`` setting.

See also
--------

* :ref:`template-reference` — Full Liquid template variable reference
* :ref:`blueprints` — Blueprint YAML format and settings hierarchy
* :doc:`bilby` — Bilby pipeline, which commonly depends on BayesWave PSDs
* :doc:`rift` — RIFT pipeline, which commonly depends on BayesWave PSDs
