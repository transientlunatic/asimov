.. _ledger:

The Asimov Ledger
=================

The ledger is asimov's internal database.
It records the full configuration and current status of every event and analysis in your project.
You will not normally need to interact with it directly — asimov creates and updates it automatically as you apply blueprints and run the monitor.

.. note::

   **The ledger is not a configuration file.**
   Do not edit ``asimov/ledger.yml`` by hand.
   Instead use ``asimov apply -f <blueprint.yaml>`` to make changes.
   Direct edits bypass validation and can leave the project in an inconsistent state.

This page is a reference for the structure and meaning of ledger settings.
It is primarily useful when:

* Writing a new pipeline and needing to understand what data is available in ``production.meta``
* Debugging an unexpected analysis configuration

Settings hierarchy
------------------

Settings in the ledger are applied in order of increasing priority:

1. **Global defaults** — applied via a ``kind: configuration`` blueprint
2. **Pipeline defaults** — under the ``pipelines: <name>`` key of a ``kind: configuration`` blueprint
3. **Event settings** — in a ``kind: event`` blueprint
4. **Analysis settings** — in a ``kind: analysis`` blueprint

An analysis-level setting always wins over a project-level setting.
See :ref:`blueprints` for the full precedence example and settings reference.

Detector information
--------------------

The ``interferometers`` key lists the detectors used in an analysis.
It takes a list of standard detector abbreviations:

.. code-block:: yaml

   interferometers:
     - H1
     - L1
     - V1

Data settings
-------------

Data settings live under the ``data`` key.

.. code-block:: yaml

   data:
     calibration:
       H1: /home/cal/H1-calibration.dat
       L1: /home/cal/L1-calibration.dat
     channels:
       H1: H1:DCS-CALIB_STRAIN_C02
       L1: L1:DCS-CALIB_STRAIN_C02
     frame types:
       H1: H1_HOFT_C02
       L1: L1_HOFT_C02
     segments:
       H1: H1:DMT-ANALYSIS_READY:1
       L1: L1:DMT-ANALYSIS_READY:1
     segment length: 4

``calibration``
  Location of calibration spline files, keyed by detector.
  Can be an absolute path or a path relative to the event repository.

``channels``
  Data channel names, keyed by detector.

``frame types``
  Frame type names used for data access, keyed by detector.

``segments``
  Segment flag definitions, keyed by detector.

``segment length``
  Length of the analysis segment in seconds.

``data files``
  Pre-downloaded frame files, keyed by detector.
  Use when frame data is not available from CVMFS or GraceDB.

  .. code-block:: yaml

     data:
       data files:
         H1: ./H1-file.gwf
         L1: ./L1-file.gwf

Data quality settings
---------------------

Data quality settings live under the ``quality`` key.

.. code-block:: yaml

   quality:
     minimum frequency:
       H1: 20
       L1: 20
     maximum frequency:
       H1: 2048
       L1: 2048

Likelihood settings
-------------------

Likelihood settings live under the ``likelihood`` key.
These control how the likelihood function is constructed.
For more detail on all likelihood settings see :ref:`blueprints`.

.. code-block:: yaml

   likelihood:
     psd length: 4
     reference frequency: 20
     sample rate: 2048
     segment start: 1126259462.391
     start frequency: 13.333333333333334
     window length: 4

Prior settings
--------------

Prior settings live under the ``priors`` key.
See :doc:`priors` for a full reference.

.. code-block:: yaml

   priors:
     chirp mass:
       type: UniformInComponentsChirpMass
       minimum: 10
       maximum: 100
     mass ratio:
       type: UniformInComponentsMassRatio
       minimum: 0.1
       maximum: 1.0
     luminosity distance:
       type: PowerLaw
       minimum: 10
       maximum: 3000
       alpha: 2

Postprocessing settings
-----------------------

Postprocessing settings live under the ``postprocessing`` key.

.. code-block:: yaml

   postprocessing:
     pesummary:
       accounting group: ligo.dev.o4.cbc.pe.lalinference
       cosmology: Planck15_lal
       evolve spins: forward
       multiprocess: 4
       redshift: exact
       regenerate posteriors:
         - redshift
         - mass_1_source
         - mass_2_source
         - chirp_mass_source
         - total_mass_source
         - final_mass_source
         - final_mass_source_non_evolved
         - radiated_energy
       skymap samples: 2000
