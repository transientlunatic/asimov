.. _rift-pipelines:

RIFT pipeline
=============

The RIFT interface allows asimov to configure, submit, and monitor analyses using the
`RIFT <https://github.com/oshaughn/research-projects-RIT>`_ (Rapid Iterative Fitting and Exploration) pipeline.
RIFT uses a two-stage iterative approach: the ILE stage evaluates the likelihood on a grid, and the CIP stage fits a posterior from those evaluations.

Review status
-------------

.. warning::
   The RIFT integration has not been fully reviewed.
   It must not be used for collaboration parameter estimation analyses without additional review.

Quick start
-----------

The minimal blueprint for a RIFT analysis is:

.. code-block:: yaml

   kind: analysis
   name: pe-rift
   pipeline: rift
   comment: Parameter estimation with RIFT.
   waveform:
     approximant: SEOBNRv4PHM
     reference frequency: 20

Apply it to an event with:

.. code-block:: console

   $ asimov apply -f rift-analysis.yaml --event GW150914_095045

Examples
--------

Standard parameter estimation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   kind: analysis
   name: rift-seobnrv4phm
   pipeline: rift
   comment: SEOBNRv4PHM parameter estimation.
   waveform:
     approximant: SEOBNRv4PHM
     reference frequency: 20
     maximum mode: 4
   likelihood:
     marginalization:
       distance: true
       maximum distance: 10000
   needs:
     - pipeline: bayeswave

With physical assumptions (binary neutron star)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RIFT supports making explicit physical assumptions to speed up the analysis:

.. code-block:: yaml

   kind: analysis
   name: rift-bns
   pipeline: rift
   comment: BNS analysis assuming matter effects.
   waveform:
     approximant: IMRPhenomPv2_NRTidalv2
     reference frequency: 20
   likelihood:
     assume:
       - matter
       - nonprecessing

With manual bootstrapping
~~~~~~~~~~~~~~~~~~~~~~~~~~

A pre-generated initial grid can be provided to bootstrap the run.
The grid file must be placed in the event repository with the name ``<analysis-name>_bootstrap.xml.gz``:

.. code-block:: yaml

   kind: analysis
   name: rift-bootstrap
   pipeline: rift
   comment: RIFT with a manual bootstrap grid.
   waveform:
     approximant: SEOBNRv4PHM
     reference frequency: 20
   bootstrap: manual
   needs:
     - name-of-grid-generating-analysis

Blueprint settings reference
-----------------------------

The settings below can be specified in a RIFT blueprint at any level of the hierarchy
(global, pipeline-defaults, event, or analysis-specific).
See :ref:`blueprints` for the full precedence rules and :ref:`template-reference` for how
these settings map to variables inside the configuration template.

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
     - Waveform approximant (e.g. ``SEOBNRv4PHM``). **Required.**
   * - ``waveform:reference frequency``
     - float
     - Reference frequency in Hz at which spins are defined. **Required.**
   * - ``waveform:maximum mode``
     - int
     - Maximum spherical harmonic mode order. Defaults to ``2``. If ``likelihood:start frequency`` is not set, it is derived as ``(2 / maximum mode) * minimum frequency``.
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
     - Start frequency for waveform generation. If not set, derived from ``waveform:maximum mode`` and ``quality:minimum frequency``.

Marginalisation settings
"""""""""""""""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``likelihood:marginalization:distance``
     - bool
     - Enable distance marginalisation. Defaults to ``False``.
   * - ``likelihood:marginalization:distance lookup``
     - str
     - Path to a pre-computed distance lookup table.
   * - ``likelihood:marginalization:maximum distance``
     - float
     - Maximum distance in Mpc for distance marginalisation. Defaults to ``10000``.

Physical assumption settings
"""""""""""""""""""""""""""""

The ``likelihood:assume`` list forces specific physical assumptions to speed up or constrain the analysis.
Each item in the list activates one assumption:

.. code-block:: yaml

   likelihood:
     assume:
       - no spin
       - matter

.. list-table::
   :header-rows: 1

   * - Value
     - Description
   * - ``no spin``
     - Assume both components are non-spinning.
   * - ``precessing``
     - Assume spin-induced precession is possible.
   * - ``nonprecessing``
     - Assume spin is aligned; no precession.
   * - ``matter``
     - Assume both components may have matter effects (e.g. neutron stars).
   * - ``matter secondary``
     - Assume only the secondary component has matter effects (e.g. NSBH system).
   * - ``eccentric``
     - Assume the orbit may be eccentric.
   * - ``high q``
     - Assume a high mass-ratio system.
   * - ``well-placed``
     - Assume the event is well-placed for the detector network.
   * - ``lowlatency tradeoffs``
     - Apply low-latency performance trade-offs.

``sampler`` settings
~~~~~~~~~~~~~~~~~~~~

RIFT uses two stages of sampling — ILE (Iterative Likelihood Evaluation) and CIP
(Constructing Inference Posteriors) — each with their own settings.

CIP settings
"""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``sampler:cip:fitting method``
     - str
     - Fitting method in the CIP stage. ``"rf"`` (random forest) or ``"gp"`` (Gaussian process). Defaults to ``"rf"``.
   * - ``sampler:cip:sampling method``
     - str
     - Sampling method in CIP. Options: ``"default"``, ``"GMM"``, ``"adaptive_cartesian_gpu"``. Defaults to ``"default"``.
   * - ``sampler:cip:explode jobs``
     - int
     - Number of parallel CIP jobs. More jobs reduce wall-clock time. Defaults to ``3``.
   * - ``sampler:cip:explode jobs auto``
     - bool
     - Automatically determine the number of CIP jobs. Defaults to ``True``.
   * - ``sampler:use aligned phase coordinates``
     - bool
     - Use aligned-phase coordinates internally. Defaults to ``True``.
   * - ``sampler:correlate parameters default``
     - bool
     - Use default parameter correlations. Defaults to ``True``.
   * - ``sampler:use rescaled transverse spin coordinates``
     - bool
     - Use rescaled transverse spin coordinates. Defaults to ``True``.
   * - ``sampler:force iterations``
     - int
     - Force a fixed number of RIFT iterations. Optional.

ILE settings
"""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``sampler:ile:n eff``
     - int
     - Target number of effective samples per ILE iteration. Defaults to ``100``.
   * - ``sampler:ile:runtime max minutes``
     - int
     - Maximum runtime per ILE job in minutes. Defaults to ``700``.
   * - ``sampler:ile:jobs per worker``
     - int
     - Number of likelihood evaluations per ILE worker. Defaults to ``20``.
   * - ``sampler:ile sampling method``
     - str
     - Sampling method for ILE. Defaults to ``"adaptive_cartesian_gpu"``.
   * - ``sampler:manual grid``
     - str
     - Path to a pre-generated initial grid file. Optional; used with ``bootstrap: manual``.

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
     - Memory to request per job. Defaults to ``"4.0"`` GB.
   * - ``scheduler:osg``
     - bool
     - Submit to the Open Science Grid. Defaults to ``False``.

Bootstrapping
-------------

RIFT supports bootstrapping a new analysis from the grid of a previous one.
Set ``bootstrap: manual`` in the blueprint and place the grid file in the event repository
as ``<analysis-name>_bootstrap.xml.gz``.

Use a ``needs`` dependency to ensure the bootstrapping analysis completes first:

.. code-block:: yaml

   kind: analysis
   name: rift-refined
   pipeline: rift
   comment: Refined RIFT run bootstrapped from a coarse run.
   waveform:
     approximant: SEOBNRv4PHM
     reference frequency: 20
   bootstrap: manual
   needs:
     - rift-coarse

See also
--------

* :ref:`template-reference` — Full Liquid template variable reference
* :ref:`blueprints` — Blueprint YAML format and settings hierarchy
* :doc:`bayeswave` — BayesWave pipeline, commonly used to generate on-source PSDs for RIFT
