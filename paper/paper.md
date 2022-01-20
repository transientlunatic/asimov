---
title: "Asimov: A framework for coordinating parameter estimation workflows"
tags:
    - astronomy
    - gravitational waves
    - Python
authors:
    - name: "Daniel Williams"
      orcid: 0000-0003-3772-198X
      affiliation: 1
    - name: "John Veitch"
      orcid: 0000-0002-6508-0713
      affiliation: 1
    - name: "Maria Luisa Chiofalo"
      orcid: 0000-0002-6992-5963
      affilitation: 4
    - name: "Patricia Schmidt"
      orcid: 0000-0003-1542-1791
      affiliation: 6
    - name: "Richard P. Udall"
      orcid: 0000-0001-6877-3278
      affiliation: 5
    - name: "Avi Vajpeji"
      orcid: 0000-0002-4146-1132
      affiliation: "2, 3"
    - name: "Charlie Hoy"
      orcid: 0000-0002-8843-6719
      affiliation: 7
affiliations:
    - name: "School of Physics and Astronomy, University of Glasgow, Glasgow, G12 8QQ, United Kingdom"
      index: 1
    - name: "School of Physics and Astronomy, Monash University, Clayton VIC 3800, Australia"
      index: 2
    - name: "OzGrav: The ARC Centre of Excellence for Gravitational Wave Discovery, Clayton VIC 3800, Australia"
      index: 3
    - name: "Department of Physics 'Enrico Fermi', University of Pisa, and INFN, Largo Bruno Pontecorvo 3 I-56126 Pisa, Italy"
      index: 4
    - name: "LIGO Laboratory, California Institute of Technology"
      index: 5
    - name: "School of Physics and Astronomy and Institute for Gravitational Wave Astronomy, University of Birmingham, Edgbaston, Birmingham, B15 9TT, United Kingdom"
      index: 6
    - name: "Cardiff University, Cardiff CF24 3AA, UK"
	  index: 7
date: 17 December 2021
bibliography: paper.bib

---

# Summary

Since the first detection in 2015 of gravitational waves from compact binary coalescence [@GW150914], improvements to the Advanced LIGO and Advanced Virgo detectors have expanded our view into the universe for these signals. 
Searches of the of the latest observing run (O3) have increased the number of detected signals to 90, at a rate of approximately 1 per week [@GWTC2.1;@GWTC3]. 
Future observing runs are expected to increase this even further[@Abbott:2020qfu]. 
Bayesian analysis of the signals can reveal the properties of the coalescing black holes and neutron stars by comparing predicted waveforms to the observed data [@TheLIGOScientific:2016wfe].
The proliferating number of detected signals, the increasing number of methods that have been deployed [@lalinference; @Ashton:2018jfp; @Lange:2018pyp], and the variety of waveform models [@Ossokine:2020kjp; @Khan:2019kot; @Pratten:2020ceb] create an ever-expanding number of analyses that can be considered.

# Statement of Need

While these developments are positive, they also bring considerable challenges.
The first of these lies with the high rate at which gravitational waves can now be detected; thanks to the improved sensitivity of the detectors they observe a much larger volume of space, and the increasing size of the detector network has also increased the total time during which observations occur. 
The second comes from developments in the analysis techniques and related software. 
Development of these techniques has accelerated in a short period of time, and the landscape of analysis software has become diverse. 
It is desirable to be able to use these techniques with ease, but thanks to the highly distributed development process which has produced them, they often have highly heterogeneous interfaces.

We developed asimov as a solution to both of these problems, as it is capable both of organising and tracking a large number of on-going analyses, but also of performing setup and post-processing of several different analysis pipelines, providing a single uniform interface. 
The software has been designed to be easily extensible, making integration with new pipelines straight-forward.

In addition, ensuring that the large number of analyses are completed successfully, and their results collated efficiently proved a formidable challenge when relying on "by-hand" approaches.
The LIGO Scientific Collaboration operate a number of high-throughput computing facilities (the LIGO Data Grid [LDG]) which are themselves controlled by the ``htcondor`` scheduling system.
``asimov`` monitors the progress of jobs within the ``htcondor`` ecosystem, resubmits jobs to the cluster which fail due to transient problems, such as file I/O errors in computing nodes, and detects the completion of analysis jobs.
Upon completion of a job the results are post-processed using the ``PESummary`` python package [@pesummary], and humans can be alerted by a message posted by ``asimov`` to a Mattermost or Slack channel.
Interaction with `htcondor` will also allow jobs to be submitted to the Open Science Grid in the future. 

Prior to the development of `asimov` analyses of gravitational wave data had been configured and run manually, or had relied on collections of shell scripts.
`Asimov` therefore constitutes an new approach, designed to be both more maintainable, and to improve the reproduciblity of results generated by analysis pipelines.

# Implementation

In order to produce a uniform interface to all of its supported pipelines, `asimov` implements a YAML-formatted configuration file, which is referred to as its "production ledger". 
This file is used to specify the details of each event to be analysed, details about the data sources, and details of each pipeline which should be applied to the specified data. 
This allows identical settings to be used with multiple different pipelines, with a minimum of configuration, reducing the possibility of transcription errors between setups.
In the current implementation of `Asimov` the production ledger is stored using an issue tracker on a custom ``Gitlab`` instance, with each issue representing a different event.
This approach is, however, neither flexible nor scalable, and future development will use an alternative means of storing the ledger.

`Asimov` simplifies the process of gathering and collating the various settings and data-products required to configure an analysis.
These include data quality information: data from gravitational wave detectors can be affected by non-stationary noise or "glitches" which must be either be removed before analysis, or the analysis must be configured to mitigate their effect on final results.
These data are provided to `Asimov` in YAML format from the appropriate team, and used to make appropriate selections in the analysis.

The analysis of gravitational wave data is generally performed within a Bayesian framework, which requires prior probability distributions being chosen before the analysis.
Ideally these distributions would be chosen such that a very broad range of parameter values is explored and sampled, however this is computationally impractical, and to improve the speed and efficiency of the analysis a rough guess of the parameters is required.
This is normally determined by "preliminary" analyses, rougher, rapid analyses performed, which are themselves informed by the detection process which identified the event in the raw detector data.
These prior data are analysed by the ``PEConfigurator`` tool to determine appropriate prior ranges, and settings for the waveform approximant to be used in the analysis.

The calibration of the detectors; the correspondance between the strain on the detector and the intensity of light at the interferometer's exit port, can change over the course of an observing run.
The uncertainty in this quantity is marginalised by many of the analyses, which requires data files to be collected and provided to the analyses.

Once the correct data, settings, and calibration information has been identified and collected it is possible to configure analyses.
`Asimov` allows analyses to be described as a dependency tree, allowing the output data products from one analysis to be used as an input for another.
This is often useful for coordinating the determination of the PSD of the analysed data.

Each pipeline is configured with a mixture of configuration files and command-line arguments. 
`Asimov` produces the appropriately-formatted configuration file for each pipeline using a template and substitutions from the production ledger. 
The appropriate command line program is then run for the given pipeline, in order to produce an execution environment and submission data for the `htcondor` scheduling system.
This is then submitted to the LDG, and the job id is collected and stored by `asimov`.

It is then possible to automatically monitor the progress of jobs on the LDG, produce a webpage summarising the status of all on-going analyses, and detect the completion of jobs and initialise post-processing.

# Acknowledgements

This work was supported by STFC grants ST/V001736/1 and ST/V005634/1.  P.S. acknowledges support from STFC grant ST/V005677/1.
We are grateful for the support of our colleagues in the LIGO-Virgo Compact Binary Coalescence Parameter Estimation working group, including, but not limited to Christopher Berry for his suggestions and 

# References
