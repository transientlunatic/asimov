.. _priors:

Prior Distributions
===================

Asimov provides a uniform way to specify prior distributions in blueprints.
Priors are validated when a blueprint is applied and are automatically translated
to the format expected by each pipeline.

Specifying Priors in a Blueprint
---------------------------------

Add a ``priors:`` section to any blueprint.
Each key is the **parameter name** (using the same space-separated convention as
other blueprint keys) and the value is a mapping of prior settings:

.. code-block:: yaml

   kind: event
   name: GW150914_095045
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

Apply the blueprint with:

.. code-block:: console

   $ asimov apply -f event.yaml

Prior settings reference
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Type
     - Description
   * - ``minimum``
     - float
     - Lower bound of the prior. Used for ``Uniform``, ``PowerLaw``, and most other distributions.
   * - ``maximum``
     - float
     - Upper bound of the prior. Required for all bounded distributions.
   * - ``type``
     - str
     - Distribution class name. Passed to the pipeline's prior interface verbatim (e.g. ``Uniform``, ``PowerLaw``, ``Gaussian``, ``UniformInComponentsChirpMass``). Optional — pipelines fall back to a default if omitted.
   * - ``boundary``
     - str
     - Boundary condition. One of ``"periodic"``, ``"reflective"``, or omitted. Primarily used by bilby.
   * - ``alpha``
     - float
     - Power-law index. Used only when ``type: PowerLaw``.
   * - ``mu``
     - float
     - Mean of a Gaussian prior.
   * - ``sigma``
     - float
     - Standard deviation of a Gaussian prior.

Setting the default prior set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The special ``default:`` key tells the pipeline which built-in prior set to use as a
base, with your per-parameter entries merged on top:

.. code-block:: yaml

   priors:
     default: BBHPriorDict
     luminosity distance:
       type: PowerLaw
       minimum: 10
       maximum: 3000
       alpha: 2

The ``default`` value is pipeline-specific. For bilby the common choices are
``BBHPriorDict`` (binary black holes), ``BNSPriorDict`` (binary neutron stars), and
``NSBHPriorDict`` (neutron-star–black-hole systems).

Settings Inheritance
---------------------

Priors follow the same inheritance hierarchy as all other settings:

1. **Global** — ``kind: configuration`` blueprint, applied project-wide
2. **Event** — ``kind: event`` blueprint, applies to every analysis on that event
3. **Analysis** — ``kind: analysis`` blueprint, applies only to that specific run

A more specific level overrides individual parameters from the level above;
parameters not mentioned at the inner level are inherited.

For example, if the event blueprint sets a distance prior and the analysis blueprint
sets a chirp-mass prior, the analysis will use both:

.. code-block:: yaml

   # event.yaml — sets distance prior for all analyses on this event
   kind: event
   name: GW150914_095045
   priors:
     luminosity distance:
       type: PowerLaw
       minimum: 10
       maximum: 3000
       alpha: 2
   ---
   # bilby.yaml — overrides chirp mass for this specific analysis
   kind: analysis
   name: pe-bilby
   pipeline: bilby
   waveform:
     approximant: IMRPhenomXPHM
     reference frequency: 20
   priors:
     chirp mass:
       type: UniformInComponentsChirpMass
       minimum: 21
       maximum: 45

What your priors produce
-------------------------

When asimov builds a pipeline configuration file, it translates your blueprint
priors into the format that pipeline expects.
You do not need to manage these files yourself.

For **bilby**, the blueprint priors become a ``prior-dict`` entry in the bilby
``.ini`` file.
For example, the blueprint::

   priors:
     default: BBHPriorDict
     chirp mass:
       type: UniformInComponentsChirpMass
       minimum: 21
       maximum: 45
     luminosity distance:
       type: PowerLaw
       minimum: 10
       maximum: 3000
       alpha: 2

produces a bilby configuration section like:

.. code-block:: text

   default-prior = BBHPriorDict
   prior-dict = {chirp_mass = UniformInComponentsChirpMass(minimum=21, maximum=45, name='chirp_mass'),
    luminosity_distance = PowerLaw(minimum=10, maximum=3000, alpha=2, name='luminosity_distance', unit='Mpc')}

For **LALInference**, priors become ``[minimum, maximum]`` pairs in the
``[priors]`` section of the LALInference ini file.

For **RIFT**, prior bounds are passed directly as command-line arguments to the
ILE and CIP stages.

For Pipeline Developers
------------------------

To add prior support to a new pipeline, subclass :class:`~asimov.priors.PriorInterface`
and implement the ``convert()`` method.
See :doc:`/pipelines-dev` for the full developer guide.
