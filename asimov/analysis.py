"""
Code to handle the various kinds of analysis which asimov can handle.

Asimov defintes three types of analysis, depending on the inputs of the analysis.

Simple analyses
  These analyses operate only on a single event,
  and will generally use a very specific set of configuration settings.
  An example of a simple analysis is a bilby or RIFT parameter estimation analysis,
  as these only require access to the data for a single event.
  Before version 0.4 these were called `Productions`.

Event analyses
  These analyses can access the results of all of the simple analyses which have been
  performed on a single event, or a subset of them.
  An example of an event analysis is the production of mixed posterior samples from multiple
  PE analyses.

Project analyses
  These are the most general type of analysis, and have access to the results of all analyses
  on all events, including event and simple analyses.
  This type of analysis is useful for defining a population analysis, for example.

"""
import os
import configparser
from copy import deepcopy
from warnings import warn

from liquid import Liquid

from asimov import config
from asimov.pipelines import known_pipelines
from asimov.utils import update
from asimov.storage import Store


class Analysis:
    """
    The base class for all other types of analysis.

    TODO: Add a check to make sure names cannot conflict
    """

    @property
    def review(self):
        """
        Return the review information attached to the analysis.
        """

    def _process_dependencies(self, needs):
        """
        Process the dependencies list for this production.
        """
        return needs

    @property
    def dependencies(self):
        if "needs" in self.meta:
            dependencies = self._process_dependencies(self.meta["needs"])
        else:
            dependencies = None
        return dependencies

    @property
    def priors(self):
        if "priors" in self.meta:
            priors = self.meta["priors"]
        else:
            priors = None
        return priors

    @property
    def finished(self):
        finished_states = ["uploaded"]
        return self.status in finished_states

    @property
    def status(self):
        return self.status_str.lower()

    @status.setter
    def status(self, value):
        self.status_str = value.lower()
        if self.event.issue_object is not None:
            self.event.issue_object.update_data()

    def results(self, filename=None, handle=False, hash=None):
        store = Store(root=config.get("storage", "results_store"))
        if not filename:
            try:
                items = store.manifest.list_resources(self.subject.name, self.name)
                return items
            except KeyError:
                return None
        elif handle:
            return open(
                store.fetch_file(self.subject.name, self.name, filename, hash), "r"
            )
        else:
            return store.fetch_file(self.subject.name, self.name, filename, hash=hash)

    @property
    def rundir(self):
        """
        Return the run directory for this event.
        """
        if "rundir" in self.meta:
            return self.meta["rundir"]
        elif "working directory" in self.subject.meta:
            value = os.path.join(self.subject.meta["working directory"], self.name)
            self.meta["rundir"] = value
            # TODO: Make sure this is saved back to the ledger
        else:
            return None

    def make_config(self, filename, template_directory=None):
        """
        Make the configuration file for this production.

        Parameters
        ----------
        filename : str
           The location at which the config file should be saved.
        template_directory : str, optional
           The path to the directory containing the pipeline config templates.
           Defaults to the directory specified in the asimov configuration file.
        """

        if "template" in self.meta:
            template = f"{self.meta['template']}.ini"
        else:
            template = f"{self.pipeline}.ini"

        pipeline = known_pipelines[self.pipeline]

        try:
            template_directory = config.get("templating", "directory")
            template_file = os.path.join(f"{template_directory}", template)

        except (configparser.NoOptionError, configparser.NoSectionError):
            if hasattr(pipeline, "config_template"):
                template_file = pipeline.config_template
            else:
                from pkg_resources import resource_filename

                template_file = resource_filename("asimov", f"configs/{template}")

        liq = Liquid(template_file)
        rendered = liq.render(production=self, config=config)

        with open(filename, "w") as output_file:
            output_file.write(rendered)


class SimpleAnalysis(Analysis):
    """
    A single subject, single pipeline analysis.
    """

    def __init__(self, subject, name, pipeline, status=None, comment=None, **kwargs):
        self.event = self.subject = subject
        self.name = name

        if status:
            self.status_str = status.lower()
        else:
            self.status_str = "none"
            self.pipeline = pipeline.lower()
            self.comment = comment
            self.meta = deepcopy(self.subject.meta)
            self.meta = update(self.meta, kwargs)


class SubjectAnalysis(Analysis):
    """
    A single subject analysis which requires results from multiple pipelines.
    """

    pass


class ProjectAnalysis(Analysis):
    """
    A multi-subject analysis.
    """

    def __init__(
        self, subjects, analyses, name, pipeline, status=None, comment=None, **kwargs
    ):
        """ """
        super().__init__()

        self.subjects = subjects
        self.analyses = analyses


class GravitationalWaveTransient(SimpleAnalysis):
    """
    A specific production run.

    Parameters
    ----------
    event : `asimov.event`
        The event this production is running on.
    name : str
        The name of this production.
    status : str
        The status of this production.
    pipeline : str
        This production's pipeline.
    comment : str
        A comment on this production.
    """

    def __init__(self, event, name, status, pipeline, comment=None, **kwargs):
        self.event = event if isinstance(event, Event) else event[0]
        self.subject = self.event
        self.name = name

        pathlib.Path(
            os.path.join(config.get("logging", "directory"), self.event.name, name)
        ).mkdir(parents=True, exist_ok=True)

        self.logger = logger.getChild("analysis").getChild(
            f"{self.event.name}/{self.name}"
        )
        self.logger.setLevel(LOGGER_LEVEL)

        # fh = logging.FileHandler(logfile)
        # formatter = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        # fh.setFormatter(formatter)
        # self.logger.addHandler(fh)

        self.category = config.get("general", "calibration_directory")

        if status:
            self.status_str = status.lower()
        else:
            self.status_str = "none"
        self.comment = comment

        # Start by adding pipeline defaults
        if "pipelines" in self.event.ledger.data:
            if pipeline in self.event.ledger.data["pipelines"]:
                self.meta = deepcopy(self.event.ledger.data["pipelines"][pipeline])
            else:
                self.meta = {}
        else:
            self.meta = {}

        if "postprocessing" in self.event.ledger.data:
            self.meta["postprocessing"] = deepcopy(
                self.event.ledger.data["postprocessing"]
            )

        # Update with the event and project defaults
        if "ledger" in self.event.meta:
            self.event.meta.pop("ledger")
        self.meta = update(self.meta, deepcopy(self.event.meta))
        if "productions" in self.meta:
            self.meta.pop("productions")

        self.meta = update(self.meta, kwargs)

        if "sampler" not in self.meta:
            self.meta["sampler"] = {}
        if "cip jobs" in self.meta:
            # TODO: Should probably raise a deprecation warning
            self.meta["sampler"]["cip jobs"] = self.meta["cip jobs"]

        if "scheduler" not in self.meta:
            self.meta["scheduler"] = {}

        if "likelihood" not in self.meta:
            self.meta["likelihood"] = {}
        if "marginalization" not in self.meta["likelihood"]:
            self.meta["likelihood"]["marginalization"] = {}

        if "data" not in self.meta:
            self.meta["data"] = {}
        if "data files" not in self.meta["data"]:
            self.meta["data"]["data files"] = {}

        if "lmax" in self.meta:
            # TODO: Should probably raise a deprecation warning
            self.meta["sampler"]["lmax"] = self.meta["lmax"]

        self.pipeline = pipeline
        self.pipeline = known_pipelines[pipeline.lower()](self)

        if "review" in self.meta:
            self.review = Review.from_dict(self.meta["review"], production=self)
            self.meta.pop("review")
        else:
            self.review = Review()

        # Check that the upper frequency is included, otherwise calculate it
        if (
            "quality" in self.meta
            and ("maximum frequency" not in self.meta["quality"])
            and ("sample rate" in self.meta["likelihood"])
            and len(self.meta["interferometers"]) > 0
        ) or (
            list(self.meta.get("quality", {}).get("maximum frequency", {}).keys())
            != self.meta.get("interferometers")
            and ("sample rate" in self.meta["likelihood"])
        ):
            if "maximum frequency" not in self.meta["quality"]:
                self.meta["quality"]["maximum frequency"] = {}
            # Account for the PSD roll-off with the 0.875 factor
            for ifo in self.meta["interferometers"]:
                psd_rolloff = self.meta.get("likelihood", {}).get(
                    "roll off factor", 0.875
                )
                if ifo not in self.meta["quality"]["maximum frequency"]:
                    self.meta["quality"]["maximum frequency"][ifo] = int(
                        psd_rolloff * self.meta["likelihood"]["sample rate"] / 2
                    )

        # Add a warning about roll-offs
        if not ("roll off time" in self.meta["likelihood"]):
            self.logger.warning(
                "Using the default roll off settings (0.4-seconds); note that these may result in spectral leakage."
            )

        # Get the data quality recommendations
        if "quality" in self.event.meta:
            self.quality = self.event.meta["quality"]
        else:
            self.quality = {}

        if "quality" in self.meta:
            if "quality" in kwargs:
                self.meta["quality"].update(kwargs["quality"])
            self.quality = self.meta["quality"]

        if ("quality" in self.meta) and ("event time" in self.meta):
            if ("segment start" not in self.meta["quality"]) and (
                "segment length" in self.meta["data"]
            ):
                self.meta["likelihood"]["segment start"] = (
                    self.meta["event time"]
                    - self.meta["data"]["segment length"]
                    + self.meta.get("likelihood", {}).get("post trigger time", 2)
                )
                # self.event.meta['likelihood']['segment start'] = self.meta['data']['segment start']

        # Update waveform data
        if "waveform" not in self.meta:
            self.logger.info("Didn't find waveform information in the metadata")
            self.meta["waveform"] = {}
        if "approximant" in self.meta:
            self.logger.warn(
                "Found deprecated approximant information, "
                "moving to waveform area of ledger"
            )
            approximant = self.meta.pop("approximant")
            self.meta["waveform"]["approximant"] = approximant
        if "reference frequency" in self.meta["likelihood"]:
            self.logger.warning(
                "Found deprecated ref freq information, "
                "moving to waveform area of ledger"
            )
            ref_freq = self.meta["likelihood"].pop("reference frequency")
            self.meta["waveform"]["reference frequency"] = ref_freq

        # Gather the PSDs for the job
        self.psds = self._collect_psds()

        # Gather the appropriate prior data for this production
        if "priors" in self.meta:
            self.priors = self.meta["priors"]
            if (
                "amplitude order" in self.meta["priors"]
                and "pn amplitude order" not in self.meta["waveform"]
            ):
                self.meta["waveform"]["pn amplitude order"] = self.meta["priors"][
                    "amplitude order"
                ]

    def __hash__(self):
        return int(f"{hash(self.name)}{abs(hash(self.event.name))}")

    def __eq__(self, other):
        return (self.name == other.name) & (self.event == other.event)

    def _process_dependencies(self, needs):
        """
        Process the dependencies list for this production.
        """
        return needs

    @property
    def dependencies(self):
        if "needs" in self.meta:
            return self._process_dependencies(self.meta["needs"])
        else:
            return None

    def results(self, filename=None, handle=False, hash=None):
        store = Store(root=config.get("storage", "results_store"))
        if not filename:
            try:
                items = store.manifest.list_resources(self.event.name, self.name)
                return items
            except KeyError:
                return None
        elif handle:
            return open(
                store.fetch_file(self.event.name, self.name, filename, hash), "r"
            )
        else:
            return store.fetch_file(self.event.name, self.name, filename, hash=hash)

    @property
    def rel_psds(self):
        """
        Return the relative path to a PSD for a given event repo.
        """
        rels = {}
        for ifo, psds in self.psds.items():
            psd = self.psds[ifo]
            psd = psd.split("/")
            rels[ifo] = "/".join(psd[-3:])
        return rels

    @property
    def reference_frame(self):
        """
        Calculate the appropriate reference frame.
        """
        ifos = self.meta["interferometers"]
        if len(ifos) == 1:
            return ifos[0]
        else:
            return "".join(ifos[:2])

    def get_meta(self, key):
        """
        Get the value of a metadata attribute, or return None if it doesn't
        exist.
        """
        if key in self.meta:
            return self.meta[key]
        else:
            return None

    def set_meta(self, key, value):
        """
        Set a metadata attribute which doesn't currently exist.
        """
        if key not in self.meta:
            self.meta[key] = value
            self.event.ledger.update_event(self.event)
        else:
            raise ValueError

    @property
    def finished(self):
        finished_states = ["uploaded"]
        return self.status in finished_states

    @property
    def status(self):
        return self.status_str.lower()

    @status.setter
    def status(self, value):
        self.status_str = value.lower()
        self.event.ledger.update_event(self.event)

    @property
    def job_id(self):
        if "job id" in self.meta:
            return self.meta["job id"]
        else:
            return None

    @job_id.setter
    def job_id(self, value):
        self.meta["job id"] = value
        if self.event.issue_object:
            self.event.issue_object.update_data()

    def to_dict(self, event=True):
        """
        Return this production as a dictionary.

        Parameters
        ----------
        event : bool
           If set to True the output is designed to be included nested within an event.
           The event name is not included in the representation, and the production name is provided as a key.
        """
        dictionary = deepcopy(self.meta)
        if not event:
            dictionary["event"] = self.event.name
            dictionary["name"] = self.name

        dictionary["status"] = self.status
        dictionary["pipeline"] = self.pipeline.name.lower()
        dictionary["comment"] = self.comment

        dictionary["review"] = self.review.to_dicts()

        if "data" in self.meta:
            dictionary["data"] = self.meta["data"]
        if "likelihood" in self.meta:
            dictionary["likelihood"] = self.meta["likelihood"]
        if "quality" in self.meta:
            dictionary["quality"] = self.meta["quality"]
        if "priors" in self.meta:
            dictionary["priors"] = self.meta["priors"]
        if "waveform" in self.meta:
            dictionary["waveform"] = self.meta["waveform"]
        dictionary["needs"] = self.dependencies
        dictionary["job id"] = self.job_id

        # Remove duplicates of pipeline defaults
        if self.pipeline.name.lower() in self.event.ledger.data["pipelines"]:
            defaults = deepcopy(
                self.event.ledger.data["pipelines"][self.pipeline.name.lower()]
            )
        else:
            defaults = {}

        if "postprocessing" in self.event.ledger.data:
            defaults["postprocessing"] = deepcopy(
                self.event.ledger.data["postprocessing"]
            )

        if "ledger" in self.event.meta:
            self.event.meta.pop("ledger")

        defaults = update(defaults, deepcopy(self.event.meta))

        dictionary = diff_dict(defaults, dictionary)

        for key, value in self.meta.items():
            if key == "operations":
                continue
        if "repository" in self.meta:
            dictionary["repository"] = self.repository.url
        if "ledger" in dictionary:
            dictionary.pop("ledger")
        if "pipelines" in dictionary:
            dictionary.pop("pipelines")

        if "productions" in dictionary:
            dictionary.pop("productions")

        if not event:
            output = dictionary
        else:
            output = {self.name: dictionary}
        return output

    @property
    def rundir(self):
        """
        Return the run directory for this event.
        """
        if "rundir" in self.meta:
            return os.path.abspath(self.meta["rundir"])
        elif "working directory" in self.event.meta:

            value = os.path.join(self.event.meta["working directory"], self.name)
            self.meta["rundir"] = value
            return os.path.abspath(value)
        else:
            return None

    @rundir.setter
    def rundir(self, value):
        """
        Set the run directory.
        """
        if "rundir" not in self.meta:
            self.meta["rundir"] = value
            if self.event.issue_object is not None:
                self.event.issue_object.update_data()
        else:
            raise ValueError

    def get_psds(self, format="ascii", sample_rate=None):
        """
        Get the PSDs for this production.

        Parameters
        ----------
        format : {ascii, xml}
           The format of the PSD to be returned.
           Defaults to the ascii format.
        sample_rate : int
           The sample rate of the PSD to be returned.
           Defaults to None, in which case the sample rate in the event data is used.

        Returns
        -------
        list
           A list of PSD files for the production.
        """
        if sample_rate is None:
            try:
                if (
                    "likelihood" in self.meta
                    and "sample rate" in self.meta["likelihood"]
                ):
                    sample_rate = self.meta["likelihood"]["sample rate"]
                else:
                    raise DescriptionException(
                        "The sample rate for this event cannot be found.",
                        issue=self.event.issue_object,
                        production=self.name,
                    )
            except Exception as e:
                raise DescriptionException(
                    "The sample rate for this event cannot be found.",
                    issue=self.event.issue_object,
                    production=self.name,
                ) from e

        if (len(self.psds) > 0) and (format == "ascii"):
            return self.psds
        elif format == "xml":
            # TODO: This is a hack, and we need a better way to sort this.
            files = glob.glob(
                f"{self.event.repository.directory}/{self.category}/psds/{sample_rate}/*.xml.gz"
            )
            return files

    def get_timefile(self):
        """
        Find this event's time file.

        Returns
        -------
        str
           The location of the time file.
        """
        try:
            return self.event.repository.find_timefile(self.category)
        except FileNotFoundError:
            new_file = os.path.join("gps.txt")
            with open(new_file, "w") as f:
                f.write(f"{self.event.meta['event time']}")
            self.logger.info(
                f"Created a new time file in {new_file} with time {self.event.meta['event time']}"
            )
            self.event.repository.add_file(
                new_file,
                os.path.join(self.category, new_file),
                "Added a new GPS timefile.",
            )
            return new_file

    def get_coincfile(self):
        """
        Find this event's coinc.xml file.

        Returns
        -------
        str
           The location of the time file.
        """
        try:
            coinc = self.event.repository.find_coincfile(self.category)
            return coinc
        except FileNotFoundError:
            self.logger.info("Could not find a coinc.xml file")
            savepath = os.path.abspath(
                os.path.join(
                    self.event.repository.directory, self.category, "coinc.xml"
                ),
            )
            print(savepath)
            self.event.get_gracedb(
                "coinc.xml",
                savepath,
            )
            coinc = self.event.repository.find_coincfile(self.category)
            return coinc

    def get_configuration(self):
        """
        Get the configuration file contents for this event.
        """
        if "ini" in self.meta:
            ini_loc = self.meta["ini"]
        else:
            # We'll need to search the repository for it.
            try:
                ini_loc = self.event.repository.find_prods(self.name, self.category)[0]
                if not os.path.exists(ini_loc):
                    raise ValueError("Could not open the ini file.")
            except IndexError:
                raise ValueError("Could not open the ini file.")
        try:
            ini = RunConfiguration(ini_loc)
        except ValueError:
            raise ValueError("Could not open the ini file")
        except configparser.MissingSectionHeaderError:
            raise ValueError("This isn't a valid ini file")

        return ini

    @classmethod
    def from_dict(cls, parameters, event, issue=None):
        name, pars = list(parameters.items())[0]
        # Check that pars is a dictionary
        if not isinstance(pars, dict):
            if "event" in parameters:
                parameters.pop("event")

            if "status" not in parameters:
                parameters["status"] = "ready"

            return cls(event=event, **parameters)

        # Check all of the required parameters are included
        if not {"status", "pipeline"} <= pars.keys():
            raise DescriptionException(
                f"Some of the required parameters are missing from {name}", issue, name
            )
        if "comment" not in pars:
            pars["comment"] = None
        if "event" in pars:
            pars.pop(event)

        return cls(event, name, **pars)

    def __repr__(self):
        return f"<Production {self.name} for {self.event} | status: {self.status}>"

    def _collect_psds(self, format="ascii"):
        """
        Collect the required psds for this production.
        """
        psds = {}
        # If the PSDs are specifically provided in the ledger,
        # use those.

        if format == "ascii":
            keyword = "psds"
        elif format == "xml":
            keyword = "xml psds"
        else:
            raise ValueError(f"This PSD format ({format}) is not recognised.")

        if keyword in self.meta:
            # if self.meta["likelihood"]["sample rate"] in self.meta[keyword]:
            psds = self.meta[keyword]  # [self.meta["likelihood"]["sample rate"]]

        # First look through the list of the job's dependencies
        # to see if they're provided by a job there.
        elif self.dependencies:
            productions = {}
            for production in self.event.productions:
                productions[production.name] = production

            for previous_job in self.dependencies:
                try:
                    # Check if the job provides PSDs as an asset and were produced with compatible settings
                    if keyword in productions[previous_job].pipeline.collect_assets():
                        if self._check_compatible(productions[previous_job]):
                            psds = productions[previous_job].pipeline.collect_assets()[
                                keyword
                            ]
                            break
                        else:
                            self.logger.info(
                                f"The PSDs from {previous_job} are not compatible with this job."
                            )
                    else:
                        psds = {}
                except Exception:
                    psds = {}
        # Otherwise return no PSDs
        else:
            psds = {}

        for ifo, psd in psds.items():
            self.logger.debug(f"PSD-{ifo}: {psd}")

        return psds

    def _check_compatible(self, other_production):
        """
        Check that the data settings in two productions are sufficiently compatible
        that one can be used as a dependency of the other.
        """
        compatible = True

        # Check that the sample rate of this analysis is equal or less than that of the preceeding analysis
        # to ensure that PSDs have points at the correct frequencies.
        try:
            compatible = self.meta.get("likelihood", {}).get(
                "sample rate", None
            ) <= other_production.meta.get("likelihood", {}).get("sample rate", None)
        except TypeError:
            # One or more sample rates are missing so these can't be deemed compatible.
            return False
        tests = [
            ("data", "channels"),
            ("data", "frame types"),
            ("data", "segment length"),
        ]
        for test in tests:
            compatible &= self.meta.get(test[0], {}).get(
                test[1], None
            ) == other_production.meta.get(test[0], {}).get(test[1], None)
        return compatible

    def make_config(self, filename, template_directory=None, dryrun=False):
        """
        Make the configuration file for this production.

        Parameters
        ----------
        filename : str
           The location at which the config file should be saved.
        template_directory : str, optional
           The path to the directory containing the pipeline config templates.
           Defaults to the directory specified in the asimov configuration file.
        """

        self.logger.info("Creating config file.")

        self.psds = self._collect_psds()
        self.xml_psds = self._collect_psds(format="xml")

        if "template" in self.meta:
            template = f"{self.meta['template']}.ini"
        else:
            template = f"{self.pipeline.name.lower()}.ini"

        pipeline = self.pipeline
        if hasattr(pipeline, "config_template"):
            template_file = pipeline.config_template
        else:
            try:
                template_directory = config.get("templating", "directory")
                template_file = os.path.join(f"{template_directory}", template)
                if not os.path.exists(template_file):
                    raise Exception
            except Exception:
                from pkg_resources import resource_filename

                template_file = resource_filename("asimov", f"configs/{template}")

        self.logger.info(f"Using {template_file}")

        liq = Liquid(template_file)
        rendered = liq.render(production=self, config=config)

        if not dryrun:
            with open(filename, "w") as output_file:
                output_file.write(rendered)
            self.logger.info(f"Saved as {filename}")
        else:
            print(rendered)

    def build_report(self):
        if self.pipeline:
            self.pipeline.build_report()

    def html(self):
        """
        An HTML representation of this production.
        """
        production = self

        card = ""

        card += f"<div class='asimov-analysis asimov-analysis-{self.status}'>"
        card += f"<h4>{self.name}"

        if self.comment:
            card += (
                f"""  <small class="asimov-comment text-muted">{self.comment}</small>"""
            )
        card += "</h4>"
        if self.status:
            card += f"""<p class="asimov-status">
  <span class="badge badge-pill badge-{status_map[self.status]}">{self.status}</span>
</p>"""

        if self.pipeline:
            card += f"""<p class="asimov-pipeline-name">{self.pipeline.name}</p>"""

        if self.pipeline:
            # self.pipeline.collect_pages()
            card += self.pipeline.html()

        if self.rundir:
            card += f"""<p class="asimov-rundir"><code>{production.rundir}</code></p>"""
        else:
            card += """&nbsp;"""

        if "approximant" in production.meta:
            card += f"""<p class="asimov-attribute">Waveform approximant:
   <span class="asimov-approximant">{production.meta['approximant']}</span>
</p>"""

        card += """&nbsp;"""
        card += """</div>"""

        if len(self.review) > 0:
            for review in self.review:
                card += review.html()

        return card


class Production(SimpleAnalysis):
    pass
