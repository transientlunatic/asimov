.. _bilby-pipelines:

Bilby pipeline
==============

The bilby interface allows asimov to configure, submit, and monitor analyses using `bilby <https://lscsoft.docs.ligo.org/bilby/>`_ and ``bilby_pipe``.
Bilby is a Bayesian inference library designed for gravitational-wave parameter estimation.

Review status
-------------

.. note::
   The bilby integration is fully reviewed and is suitable for use in all collaboration analyses.

Quick start
-----------

The minimal blueprint for a bilby analysis is:

.. code-block:: yaml

   kind: analysis
   name: pe-bilby
   pipeline: bilby
   comment: Parameter estimation with bilby.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20

Apply it to an event with:

.. code-block:: console

   $ asimov apply -f bilby-analysis.yaml --event GW150914_095045

Examples
--------

Standard parameter estimation (O3 default)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This was the default bilby setup used in the GWTC-2.1 and GWTC-3 catalog analyses:

.. code-block:: yaml

   kind: analysis
   name: bilby-imrphenomxphm
   pipeline: bilby
   comment: IMRPhenomXPHM parameter estimation.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   likelihood:
     marginalization:
       distance: true
       phase: false
       time: false
   needs:
     - pipeline: bayeswave

With ROQ likelihood
~~~~~~~~~~~~~~~~~~~~

ROQ bases can dramatically reduce the cost of the likelihood evaluation for short, low-mass signals:

.. code-block:: yaml

   kind: analysis
   name: bilby-roq
   pipeline: bilby
   comment: Parameter estimation using a ROQ likelihood.
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   likelihood:
     type: ROQGravitationalWaveTransient
     roq:
       folder: /path/to/roq/basis
       scale: 1.0
   needs:
     - pipeline: bayeswave

Comparing waveform approximants with a strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a :ref:`strategy <blueprints>` to run multiple waveform approximants from a single blueprint:

.. code-block:: yaml

   kind: analysis
   name: bilby-{waveform.approximant}
   pipeline: bilby
   comment: Systematic waveform comparison.
   needs:
     - pipeline: bayeswave
   strategy:
     waveform.approximant:
       - IMRPhenomXPHM
       - SEOBNRv5PHM
       - IMRPhenomXO4a

Blueprint settings reference
-----------------------------

The settings below can be specified in a bilby blueprint at any level of the hierarchy
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
     - Waveform approximant (e.g. ``IMRPhenomXPHM``). **Required.**
   * - ``waveform:reference frequency``
     - float
     - Reference frequency in Hz at which spins are defined. **Required.**
   * - ``waveform:generator``
     - str
     - Waveform generator class. Defaults to ``bilby.gw.waveform_generator.LALCBCWaveformGenerator``.
   * - ``waveform:pn spin order``
     - int
     - Post-Newtonian spin order. Defaults to ``-1`` (automatic).
   * - ``waveform:pn tidal order``
     - int
     - Post-Newtonian tidal order. Defaults to ``-1`` (automatic).
   * - ``waveform:pn phase order``
     - int
     - Post-Newtonian phase order. Defaults to ``-1`` (automatic).
   * - ``waveform:pn amplitude order``
     - int
     - Post-Newtonian amplitude order. Defaults to ``0``.
   * - ``waveform:mode array``
     - list
     - Spherical harmonic modes to include (e.g. ``[[2,2],[3,3]]``). Defaults to all modes.
   * - ``waveform:conversion function``
     - str
     - Parameter conversion function name. Defaults to ``None``.
   * - ``waveform:generation function``
     - str
     - Waveform generation function name. Defaults to ``None``.
   * - ``waveform:file``
     - str
     - Path to a numerical relativity waveform file. Defaults to ``None``.
   * - ``waveform:arguments``
     - dict
     - Extra keyword arguments for the waveform generator. Defaults to ``None``.
   * - ``waveform:enforce signal duration``
     - bool
     - Enforce that the signal duration fits within the analysis segment. Defaults to ``False``.

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
     - PSD estimation segment length in seconds. Defaults to ``sample rate``.
   * - ``likelihood:post trigger time``
     - float
     - Seconds of data to analyse after the trigger. Defaults to ``2.0``.
   * - ``likelihood:roll off time``
     - float
     - Window roll-off time in seconds. Defaults to ``0.4``.
   * - ``likelihood:start frequency``
     - float
     - Frequency at which waveform generation begins. Not the same as the minimum analysis frequency set in ``quality:minimum frequency``.
   * - ``likelihood:coherence test``
     - bool
     - Run a coherence test. Defaults to ``False``.
   * - ``likelihood:type``
     - str
     - Likelihood class. Defaults to ``GravitationalWaveTransient``. Use ``ROQGravitationalWaveTransient`` for ROQ analyses.
   * - ``likelihood:time reference``
     - str
     - Timing reference. Defaults to ``"geocent"``.
   * - ``likelihood:reference frame``
     - str
     - Sky reference frame. Defaults to ``"sky"``.
   * - ``likelihood:frequency domain source model``
     - str
     - Frequency-domain source model. Defaults to ``"lal_binary_black_hole"``.
   * - ``likelihood:time domain source model``
     - str
     - Time-domain source model. Optional.
   * - ``likelihood:kwargs``
     - dict
     - Extra keyword arguments for the likelihood constructor.

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
     - Distance marginalisation. Defaults to ``True``.
   * - ``likelihood:marginalization:distance lookup``
     - str
     - Path to a pre-computed distance lookup table. Computed at runtime if not set.
   * - ``likelihood:marginalization:phase``
     - bool
     - Phase marginalisation. Defaults to ``False``.
   * - ``likelihood:marginalization:time``
     - bool
     - Time marginalisation. Defaults to ``False``.
   * - ``likelihood:marginalization:calibration``
     - bool
     - Calibration marginalisation. Defaults to ``False``.

Calibration settings
"""""""""""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``likelihood:calibration:sample``
     - bool
     - Sample over calibration uncertainty in the likelihood.
   * - ``likelihood:calibration:correction type``
     - str
     - Calibration correction type.

ROQ settings
"""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``likelihood:roq:folder``
     - str
     - Directory containing the ROQ basis.
   * - ``likelihood:roq:weights``
     - str
     - Pre-computed ROQ weight file.
   * - ``likelihood:roq:weight format``
     - str
     - Format of the ROQ weight file.
   * - ``likelihood:roq:scale``
     - float
     - ROQ scale factor. Defaults to ``1``.
   * - ``likelihood:roq:linear matrix``
     - str
     - Linear ROQ basis matrix file.
   * - ``likelihood:roq:quadratic matrix``
     - str
     - Quadratic ROQ basis matrix file.

Relative binning settings
""""""""""""""""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``likelihood:relative binning:fiducial parameters``
     - dict
     - Fiducial parameter values for relative binning.
   * - ``likelihood:relative binning:update fiducial parameters``
     - bool
     - Update fiducial parameters during the run. Defaults to ``False``.
   * - ``likelihood:relative binning:epsilon``
     - float
     - Relative binning accuracy parameter. Defaults to ``0.025``.

``sampler`` settings
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Type
     - Description
   * - ``sampler:sampler``
     - str
     - Sampler name. Defaults to ``"dynesty"``. Other options include ``"nessai"`` and ``"emcee"``.
   * - ``sampler:seed``
     - int
     - Random seed. Defaults to ``1``.
   * - ``sampler:parallel jobs``
     - int
     - Number of parallel sampling jobs. Defaults to ``2``.
   * - ``sampler:sampler kwargs``
     - dict
     - Sampler-specific keyword arguments. The default for dynesty is ``{'nlive': 1000, 'naccept': 60, 'check_point_plot': True, 'check_point_delta_t': 1800, 'print_method': 'interval-60', 'sample': 'acceptance-walk'}``.

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
     - float
     - Memory to request in GB. Defaults to ``4.0``.
   * - ``scheduler:request generation memory``
     - str
     - Memory for data generation jobs. Defaults to ``None`` (same as main job).
   * - ``scheduler:request cpus``
     - int
     - CPUs to request. Defaults to ``1``.
   * - ``scheduler:request disk``
     - int
     - Disk space to request in GB. Defaults to ``1``.
   * - ``scheduler:type``
     - str
     - Scheduler type. Defaults to ``"condor"``.
   * - ``scheduler:osg``
     - bool
     - Submit to the Open Science Grid. Defaults to ``False``.
   * - ``scheduler:desired sites``
     - str
     - Comma-separated OSG sites to target. Optional.
   * - ``scheduler:transfer files``
     - bool
     - Transfer files to worker nodes. Defaults to ``True``.
   * - ``scheduler:container``
     - str
     - Container image to use. Optional.
   * - ``scheduler:conda env``
     - str
     - Conda environment to activate on worker nodes. Optional.
   * - ``scheduler:periodic restart time``
     - int
     - HTCondor periodic restart time in seconds. Defaults to ``28800`` (8 hours).
   * - ``scheduler:generation pool``
     - str
     - HTCondor pool for data generation. Defaults to ``"local-pool"``.
   * - ``scheduler:environment variables``
     - dict
     - Extra environment variables to set for the job.
   * - ``scheduler:scitoken issuer``
     - str
     - SciToken issuer URL for authentication. Optional.

See also
--------

* :ref:`template-reference` — Full Liquid template variable reference
* :ref:`blueprints` — Blueprint YAML format and settings hierarchy
* :doc:`bayeswave` — BayesWave pipeline, commonly used to generate on-source PSDs for bilby
