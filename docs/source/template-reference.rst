.. _template-reference:

===================================
Pipeline Configuration Template Reference
===================================

Asimov generates configuration files for analysis pipelines by rendering **Liquid templates**.
Each pipeline ships with a default template (stored in ``asimov/configs/``), but you can override this by pointing to your own template in the asimov configuration file.

This page is a complete reference for all variables available inside a pipeline configuration template.

.. contents:: Contents
   :local:
   :depth: 2


How templates work
==================

When you run ``asimov manage build``, asimov:

1. Reads all settings for the analysis from the ledger (merging global defaults, pipeline defaults, event settings, and analysis-specific settings — see :ref:`blueprints` for the precedence order).
2. Passes the merged settings to the Liquid template engine.
3. Writes the rendered output to the event repository as the pipeline's configuration file.

Template files use the `Liquid templating language <https://shopify.github.io/liquid/>`_.
The most common Liquid constructs used in asimov templates are:

.. code-block:: liquid

   {# Output a value #}
   {{ variable }}

   {# Assign a shorthand alias #}
   {%- assign ifos = production.meta['interferometers'] -%}

   {# Conditional #}
   {% if data contains "calibration" %}
   calibration-model=CubicSpline
   {% endif %}

   {# Loop over a list #}
   {% for ifo in ifos %}{{ ifo }},{% endfor %}

   {# Default value if the key is absent or nil #}
   {{ likelihood['post trigger time'] | default: 2.0 }}

   {# Round a number #}
   {{ likelihood['sample rate'] | round }}

The ``{%-`` and ``-%}`` variants strip surrounding whitespace, which is useful for keeping the generated config file tidy.


Overriding the default template
================================

To use a custom template for a pipeline, set the ``directory`` key in the ``[templating]`` section of your asimov configuration, then place a file named ``<pipeline>.ini`` there:

.. code-block:: ini

   [templating]
   directory = config-templates

Asimov will look for ``config-templates/bilby.ini``, ``config-templates/bayeswave.ini``, etc.
Any pipeline for which no custom template is found falls back to the bundled default.


Top-level template variables
==============================

Two objects are always available at the top level of every template.

``production``
   The analysis object.
   Contains all merged settings and provides helper methods.
   See `The production object`_ below for full details.

``config``
   The parsed asimov configuration (from ``asimov.conf``).
   Provides access to project-wide settings that are not stored in the ledger.
   See `The config object`_ below.


The ``production`` object
==========================

Attributes
----------

``production.name``
   The name of this analysis, as specified in the blueprint (e.g. ``"Prod0"``).

``production.meta``
   A dictionary containing the fully merged settings for this analysis.
   Settings are merged in priority order: global defaults → pipeline defaults → event settings → analysis-specific settings.
   All keys use spaces rather than underscores (e.g. ``"segment length"`` not ``"segment_length"``).

   Most templates begin by assigning shorthand aliases for the nested sub-dictionaries:

   .. code-block:: liquid

      {%- assign data      = production.meta['data'] -%}
      {%- assign quality   = production.meta['quality'] -%}
      {%- assign likelihood = production.meta['likelihood'] -%}
      {%- assign waveform  = production.meta['waveform'] -%}
      {%- assign sampler   = production.meta['sampler'] -%}
      {%- assign scheduler = production.meta['scheduler'] -%}
      {%- assign ifos      = production.meta['interferometers'] -%}

``production.rundir``
   The absolute path to the working directory for this analysis.
   Used to set output directories in configuration files.

   .. code-block:: liquid

      outdir={{ production.rundir }}

``production.event``
   The parent event/subject object.

   ``production.event.name``
      The event name (e.g. ``"GW150914_095045"``).

   ``production.event.repository.directory``
      The absolute path to the event's git repository on disk.
      Useful for constructing paths to calibration envelopes or other files committed there.

      .. code-block:: liquid

         {%- assign repo_dir = production.event.repository.directory -%}
         H1-spcal-envelope={{ repo_dir }}/{{ data['calibration']['H1'] }}

``production.psds``
   A dictionary mapping interferometer names to PSD file paths.
   These are the PSDs that have been passed forward from a completed upstream analysis (e.g. BayesWave).

   .. code-block:: liquid

      psd-dict={ {% for ifo in ifos %}{{ifo}}:{{production.psds[ifo]}},{% endfor %} }

``production.xml_psds``
   Like ``production.psds`` but in XML format.
   Used by RIFT (which requires PSDs in LALInference XML format).

``production._previous_assets()``
   Returns a dictionary of all assets declared by upstream dependency analyses.
   Useful when you need to conditionally use PSDs or other files that may or may not be present:

   .. code-block:: liquid

      {%- if production._previous_assets() contains "psds" %}
      psd-dict={ {% for ifo in ifos %}{{ifo}}:{{production._previous_assets()['psds'][ifo]}},{% endfor %} }
      {%- endif %}

``production.quality``
   A shorthand alias for ``production.meta['quality']``.

``production.pipeline``
   The pipeline instance.
   Provides pipeline-specific helper methods — see `Pipeline helper methods`_ below.


Pipeline helper methods
-----------------------

``production.pipeline.get_prior_interface()``
   Returns a prior interface object for this pipeline.
   This object translates the generic prior settings from the ledger into the format expected by the specific pipeline.

   .. code-block:: liquid

      {%- assign prior_interface = production.pipeline.get_prior_interface() -%}
      default-prior={{ prior_interface.get_default_prior() }}
      prior-dict={{ prior_interface.to_prior_dict_string() }}

``production.pipeline.get_sampler_kwargs()``
   Returns a formatted string of sampler keyword arguments suitable for passing directly to bilby.

   .. code-block:: liquid

      sampler-kwargs={{ production.pipeline.get_sampler_kwargs() }}

``production.pipeline.get_additional_files()``
   Returns a list of extra files that should be transferred to worker nodes when running on OSG or similar distributed systems.

   .. code-block:: liquid

      {%- assign additional_files = production.pipeline.get_additional_files() %}
      {%- if additional_files.size > 0 %}
      additional-transfer-paths={% for file in additional_files %}{{ file }} {% endfor %}
      {%- endif %}


``production.meta`` sub-keys
=============================

The settings below are all accessed through ``production.meta``.
They can be set in blueprints at any level of the hierarchy (global, pipeline, event, or analysis).

Event-level keys
----------------

``production.meta['event time']``
   The GPS trigger time of the event.

   .. code-block:: liquid

      trigger-time={{ production.meta['event time'] }}

``production.meta['interferometers']``
   A list of interferometer abbreviations to include in the analysis (e.g. ``['H1', 'L1', 'V1']``).
   Templates typically iterate over this list to generate per-IFO configuration:

   .. code-block:: liquid

      detectors={{ production.meta['interferometers'] }}
      {% for ifo in ifos %}{{ ifo }}-psd={{ production.psds[ifo] }}{% endfor %}

``production.meta['cosmology']``
   The name of the cosmological model to use.
   Defaults to ``"Planck15"``.

``production.meta['engine']``
   The inference engine name (used by LALInference and RIFT).
   Examples: ``"lalinferencenest"``, ``"lalinferencemcmc"``.


``data`` keys
-------------

These are accessed as ``production.meta['data']``, or via the alias ``data`` if assigned at the template top.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Type
     - Description
   * - ``data['channels']``
     - dict
     - Maps each IFO to its data channel name (e.g. ``H1: H1:DCS-CALIB_STRAIN_C02``).
   * - ``data['frame types']``
     - dict
     - Maps each IFO to its frame type (e.g. ``H1: H1_HOFT_C02``).
   * - ``data['data files']``
     - dict
     - Maps each IFO to a local frame file path. When non-empty, used instead of data discovery.
   * - ``data['cache files']``
     - dict
     - Maps each IFO to a cache file path (used by BayesWave).
   * - ``data['calibration']``
     - dict
     - Maps each IFO to its calibration envelope file path (relative to the event repository, or absolute).
   * - ``data['segment length']``
     - float
     - Duration of the data segment in seconds.
   * - ``data['format']``
     - str
     - Data format. Defaults to ``"gwf"``.
   * - ``data['datafind url']``
     - str
     - URL of the datafind service. Defaults to ``"https://datafind.igwn.org"``.
   * - ``data['datafind url type']``
     - str
     - Protocol for datafind. Defaults to ``"osdf"``.


``quality`` keys
----------------

These are accessed as ``production.meta['quality']`` or via the alias ``quality``.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Type
     - Description
   * - ``quality['minimum frequency']``
     - dict
     - Maps each IFO to its minimum analysis frequency in Hz.
   * - ``quality['maximum frequency']``
     - dict
     - Maps each IFO to its maximum analysis frequency in Hz.
   * - ``quality['lowest minimum frequency']``
     - float
     - The single lowest minimum frequency across all IFOs. Used by BayesWave.
   * - ``quality['state vector']``
     - dict
     - Maps each IFO to its state vector channel name. Optional; used by LALInference.
   * - ``quality['sample rate']``
     - int
     - Sample rate in Hz. Used by LALInference (bilby uses ``likelihood['sample rate']``).


``likelihood`` keys
-------------------

These are accessed as ``production.meta['likelihood']`` or via the alias ``likelihood``.

General settings
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``likelihood['sample rate']``
     - int
     - Sample rate in Hz for likelihood evaluation.
   * - ``likelihood['psd length']``
     - float
     - Duration (seconds) of data used to estimate the PSD. Defaults to ``sample rate``.
   * - ``likelihood['post trigger time']``
     - float
     - Seconds of data analysed after the trigger time. Defaults to ``2.0``.
   * - ``likelihood['roll off time']``
     - float
     - Window roll-off time in seconds. Defaults to ``0.4`` (bilby) or ``1.0`` (BayesWave).
   * - ``likelihood['start frequency']``
     - float
     - Start frequency for waveform generation. Not the same as the minimum analysis frequency.
   * - ``likelihood['coherence test']``
     - bool
     - Whether to run a coherence test. Defaults to ``False``.
   * - ``likelihood['type']``
     - str
     - The likelihood class name. Defaults to ``"GravitationalWaveTransient"`` (bilby).
   * - ``likelihood['time reference']``
     - str
     - The detector used as timing reference. Defaults to ``"geocent"``.
   * - ``likelihood['reference frame']``
     - str
     - Sky reference frame. Defaults to ``"sky"``.
   * - ``likelihood['frequency domain source model']``
     - str
     - Frequency-domain source model function. Defaults to ``"lal_binary_black_hole"``.
   * - ``likelihood['time domain source model']``
     - str
     - Time-domain source model function. Optional.
   * - ``likelihood['kwargs']``
     - dict
     - Extra keyword arguments passed directly to the likelihood constructor.
   * - ``likelihood['window length']``
     - float
     - Window length in seconds (BayesWave only).
   * - ``likelihood['segment start']``
     - float
     - GPS start time of the analysis segment (BayesWave only).
   * - ``likelihood['iterations']``
     - int
     - Number of MCMC iterations (BayesWave only). Defaults to ``100000``.
   * - ``likelihood['chains']``
     - int
     - Number of MCMC chains (BayesWave only). Defaults to ``8``.
   * - ``likelihood['threads']``
     - int
     - Number of threads per chain (BayesWave only). Defaults to ``4``.

Marginalisation settings
~~~~~~~~~~~~~~~~~~~~~~~~~

These are nested under ``likelihood['marginalization']``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``likelihood['marginalization']['distance']``
     - bool
     - Enable distance marginalisation. Defaults to ``True`` (bilby), ``False`` (RIFT).
   * - ``likelihood['marginalization']['distance lookup']``
     - str
     - Path to a pre-computed distance marginalisation lookup table.
   * - ``likelihood['marginalization']['phase']``
     - bool
     - Enable phase marginalisation. Defaults to ``False``.
   * - ``likelihood['marginalization']['time']``
     - bool
     - Enable time marginalisation. Defaults to ``False``.
   * - ``likelihood['marginalization']['calibration']``
     - bool
     - Enable calibration marginalisation. Defaults to ``False``.
   * - ``likelihood['marginalization']['maximum distance']``
     - float
     - Maximum distance in Mpc for distance marginalisation (RIFT only). Defaults to ``10000``.

Calibration settings
~~~~~~~~~~~~~~~~~~~~~

These are nested under ``likelihood['calibration']``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``likelihood['calibration']['sample']``
     - bool
     - Whether to sample over calibration uncertainty in the likelihood.
   * - ``likelihood['calibration']['correction type']``
     - str
     - Calibration correction type (bilby only).

ROQ settings
~~~~~~~~~~~~~

These are nested under ``likelihood['roq']``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``likelihood['roq']['folder']``
     - str
     - Path to the directory containing the ROQ basis.
   * - ``likelihood['roq']['weights']``
     - str
     - Path to pre-computed ROQ weight file.
   * - ``likelihood['roq']['weight format']``
     - str
     - Format of the ROQ weight file.
   * - ``likelihood['roq']['scale']``
     - float
     - ROQ scale factor. Defaults to ``1``.
   * - ``likelihood['roq']['linear matrix']``
     - str
     - Path to the linear ROQ basis matrix.
   * - ``likelihood['roq']['quadratic matrix']``
     - str
     - Path to the quadratic ROQ basis matrix.

Relative binning settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

These are nested under ``likelihood['relative binning']``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``likelihood['relative binning']['fiducial parameters']``
     - dict
     - Fiducial parameter values for relative binning. Optional.
   * - ``likelihood['relative binning']['update fiducial parameters']``
     - bool
     - Whether to update fiducial parameters during the run. Defaults to ``False``.
   * - ``likelihood['relative binning']['epsilon']``
     - float
     - Relative binning accuracy parameter. Defaults to ``0.025``.

RIFT assume settings
~~~~~~~~~~~~~~~~~~~~~

These are nested under ``likelihood['assume']`` as a list and are specific to RIFT.
Each item in the list activates a specific physical assumption for the run.

.. list-table::
   :header-rows: 1

   * - Value
     - Description
   * - ``no spin``
     - Assume both components have zero spin.
   * - ``precessing``
     - Assume spin-induced precession is possible.
   * - ``nonprecessing``
     - Assume spin is aligned; no precession.
   * - ``matter``
     - Assume both components may have matter effects (e.g. neutron stars).
   * - ``matter secondary``
     - Assume only the secondary component has matter effects.
   * - ``eccentric``
     - Assume the orbit may be eccentric.
   * - ``high q``
     - Assume a high mass-ratio system.
   * - ``well-placed``
     - Assume the event is well-placed for the detector network.
   * - ``lowlatency tradeoffs``
     - Apply low-latency performance trade-offs.


``waveform`` keys
-----------------

These are accessed as ``production.meta['waveform']`` or via the alias ``waveform``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``waveform['approximant']``
     - str
     - Waveform approximant name (e.g. ``"IMRPhenomXPHM"``). Required.
   * - ``waveform['reference frequency']``
     - float
     - Reference frequency in Hz at which spins and other quantities are defined. Required.
   * - ``waveform['generator']``
     - str
     - Waveform generator class. Defaults to ``"bilby.gw.waveform_generator.LALCBCWaveformGenerator"`` (bilby).
   * - ``waveform['pn spin order']``
     - int
     - Post-Newtonian spin order. Defaults to ``-1`` (automatic).
   * - ``waveform['pn tidal order']``
     - int
     - Post-Newtonian tidal order. Defaults to ``-1`` (automatic).
   * - ``waveform['pn phase order']``
     - int
     - Post-Newtonian phase order. Defaults to ``-1`` (automatic).
   * - ``waveform['pn amplitude order']``
     - int
     - Post-Newtonian amplitude order. Defaults to ``0``.
   * - ``waveform['file']``
     - str
     - Path to a numerical relativity waveform file. Defaults to ``None``.
   * - ``waveform['arguments']``
     - dict
     - Extra keyword arguments passed to the waveform generator. Defaults to ``None``.
   * - ``waveform['mode array']``
     - list
     - List of spherical harmonic modes to include (e.g. ``[[2,2],[3,3]]``). Defaults to ``None`` (all modes).
   * - ``waveform['conversion function']``
     - str
     - Name of a function used to convert waveform parameters. Defaults to ``None``.
   * - ``waveform['generation function']``
     - str
     - Name of a waveform generation function. Defaults to ``None``.
   * - ``waveform['enforce signal duration']``
     - bool
     - Whether to enforce that the signal fits within the analysis segment. Defaults to ``False``.
   * - ``waveform['maximum mode']``
     - int
     - Maximum spherical harmonic mode order (RIFT only). Defaults to ``2``.


``sampler`` keys
----------------

These are accessed as ``production.meta['sampler']`` or via the alias ``sampler``.

General sampler settings (bilby)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``sampler['sampler']``
     - str
     - Name of the sampler to use. Defaults to ``"dynesty"``. Other options: ``"nessai"``, ``"emcee"``.
   * - ``sampler['seed']``
     - int
     - Random seed for reproducibility. Defaults to ``1``.
   * - ``sampler['parallel jobs']``
     - int
     - Number of parallel sampling runs. Defaults to ``2``.
   * - ``sampler['sampler kwargs']``
     - dict
     - Sampler-specific keyword arguments as a dictionary.

RIFT CIP settings
~~~~~~~~~~~~~~~~~~

These are nested under ``sampler['cip']`` and are specific to the RIFT pipeline.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``sampler['cip']['fitting method']``
     - str
     - Fitting method used in the CIP stage. ``"rf"`` (random forest) or ``"gp"`` (Gaussian process). Defaults to ``"rf"``.
   * - ``sampler['cip']['sampling method']``
     - str
     - Sampling method in CIP. Options: ``"default"``, ``"GMM"``, ``"adaptive_cartesian_gpu"``. Defaults to ``"default"``.
   * - ``sampler['cip']['explode jobs']``
     - int
     - Number of CIP jobs to run in parallel. Defaults to ``3``.
   * - ``sampler['cip']['explode jobs auto']``
     - bool
     - Automatically determine the number of explode jobs. Defaults to ``True``.

RIFT ILE settings
~~~~~~~~~~~~~~~~~~

These are nested under ``sampler['ile']`` and are specific to the RIFT pipeline.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``sampler['ile']['n eff']``
     - int
     - Target number of effective samples per ILE iteration. Defaults to ``100``.
   * - ``sampler['ile']['runtime max minutes']``
     - int
     - Maximum runtime per ILE job in minutes. Defaults to ``700``.
   * - ``sampler['ile']['jobs per worker']``
     - int
     - Likelihood evaluations per ILE worker. Defaults to ``20``.
   * - ``sampler['ile sampling method']``
     - str
     - Sampling method for ILE. Defaults to ``"adaptive_cartesian_gpu"``.
   * - ``sampler['manual grid']``
     - str
     - Path to a pre-generated initial grid file. Optional.
   * - ``sampler['force iterations']``
     - int
     - Force a fixed number of RIFT iterations. Optional.
   * - ``sampler['use aligned phase coordinates']``
     - bool
     - Use aligned-phase coordinates internally. Defaults to ``True``.
   * - ``sampler['correlate parameters default']``
     - bool
     - Use default parameter correlations. Defaults to ``True``.
   * - ``sampler['use rescaled transverse spin coordinates']``
     - bool
     - Use rescaled transverse spin coordinates. Defaults to ``True``.


``scheduler`` keys
------------------

These are accessed as ``production.meta['scheduler']`` or via the alias ``scheduler``.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Key
     - Type
     - Description
   * - ``scheduler['accounting group']``
     - str
     - HTCondor accounting group (e.g. ``"ligo.dev.o4.cbc.pe.bilby"``). Required for most clusters.
   * - ``scheduler['request memory']``
     - str or float
     - Memory to request per job (e.g. ``"4.0"`` GB or ``"8192 MB"``).
   * - ``scheduler['request generation memory']``
     - str
     - Memory for data generation jobs (bilby). Defaults to ``None`` (same as main job).
   * - ``scheduler['request post memory']``
     - str
     - Memory for BayesWave post-processing jobs. Defaults to ``"16384 MB"``.
   * - ``scheduler['request disk']``
     - str
     - Disk space to request per job.
   * - ``scheduler['request post disk']``
     - str
     - Disk space for BayesWave post-processing jobs.
   * - ``scheduler['request cpus']``
     - int
     - Number of CPUs to request. Defaults to ``1``.
   * - ``scheduler['type']``
     - str
     - Scheduler type. Defaults to ``"condor"``.
   * - ``scheduler['osg']``
     - bool
     - Submit to the Open Science Grid. Defaults to ``False``.
   * - ``scheduler['transfer files']``
     - bool
     - Whether to transfer files to worker nodes. Defaults to ``True``.
   * - ``scheduler['desired sites']``
     - str
     - Comma-separated list of desired OSG sites. Defaults to ``None``.
   * - ``scheduler['container']``
     - str
     - Container image to use for the job. Defaults to ``None``.
   * - ``scheduler['conda env']``
     - str
     - Name of the conda environment to activate. Defaults to ``None``.
   * - ``scheduler['environment']``
     - str
     - Path to the pipeline software installation (used by BayesWave and LALInference).
   * - ``scheduler['environment variables']``
     - dict
     - Extra environment variables to set for the job.
   * - ``scheduler['periodic restart time']``
     - int
     - HTCondor periodic restart time in seconds. Defaults to ``28800`` (8 hours).
   * - ``scheduler['generation pool']``
     - str
     - HTCondor pool for data generation jobs (bilby). Defaults to ``"local-pool"``.
   * - ``scheduler['analysis executable']``
     - str
     - Override the default analysis executable path. Optional.
   * - ``scheduler['scitoken issuer']``
     - str
     - SciToken issuer URL for authentication. Optional.
   * - ``scheduler['queue']``
     - str
     - HTCondor queue name. Optional.


The ``config`` object
======================

The ``config`` object exposes the parsed asimov configuration file (``asimov.conf``).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Key
     - Description
   * - ``config['general']['webroot']``
     - Root directory for web-accessible output pages.
   * - ``config['general']['osg']``
     - Whether OSG submission is enabled project-wide.
   * - ``config['condor']['user']``
     - HTCondor accounting username.
   * - ``config['pipelines']['environment']``
     - Path to the pipeline software environment (e.g. a conda prefix or LALSuite install).

Example usage:

.. code-block:: liquid

   webdir={{ config['general']['webroot'] }}/{{ production.event.name }}/{{ production.name }}
   accounting_group_user={{ config['condor']['user'] }}


Common Liquid patterns
======================

Per-IFO configuration
----------------------

Many settings are defined per-interferometer as a dictionary.
The standard way to render them is to loop over ``ifos``:

.. code-block:: liquid

   {%- assign ifos = production.meta['interferometers'] -%}

   channel-dict={ {% for ifo in ifos %}{{data['channels'][ifo]}},{% endfor %} }
   psd-dict={ {% for ifo in ifos %}{{ifo}}:{{production.psds[ifo]}},{% endfor %} }
   minimum-frequency={ {% for ifo in ifos %}{{ifo}}:{{quality['minimum frequency'][ifo]}},{% endfor %} }

Conditional sections
---------------------

Use ``if`` blocks to include configuration sections only when the relevant settings are present:

.. code-block:: liquid

   {%- if data contains "calibration" %}
   {%- if data['calibration'] contains ifos[0] %}
   calibration-model=CubicSpline
   spline-calibration-envelope-dict={ {% for ifo in ifos %}{{ifo}}:{{data['calibration'][ifo]}},{% endfor %} }
   {%- endif %}
   {%- endif %}

   {%- if likelihood contains "roq" %}
   roq-folder={{ likelihood['roq']['folder'] }}
   {%- endif %}

Using defaults
--------------

The ``| default:`` filter provides a fallback for missing or nil values:

.. code-block:: liquid

   post-trigger-duration={{ likelihood['post trigger time'] | default: 2.0 }}
   sampler={{ sampler['sampler'] | default: "dynesty" }}
   cosmology={{ production.meta['cosmology'] | default: "Planck15" }}

Handling the event repository
------------------------------

Not all analyses have a git repository (e.g. test pipelines or analyses using only public data).
It is good practice to guard against a missing repository:

.. code-block:: liquid

   {%- if production.event.repository -%}
   {%- assign repo_dir = production.event.repository.directory -%}
   {%- else -%}
   {%- assign repo_dir = "." -%}
   {%- endif -%}


See also
========

* :ref:`pipeline-dev` — Writing a new pipeline interface
* :ref:`blueprints` — Blueprint YAML reference and settings hierarchy
* :doc:`pipelines/bilby` — Bilby-specific settings
* :doc:`pipelines/rift` — RIFT-specific settings
* :doc:`pipelines/bayeswave` — BayesWave-specific settings
* :doc:`pipelines/lalinference` — LALInference-specific settings
