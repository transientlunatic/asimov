"""
Trigger handling code.
"""

import glob
import os
import pathlib
from copy import deepcopy
import configparser
import subprocess

import networkx as nx
import yaml
from ligo.gracedb.rest import GraceDb, HTTPError
from liquid import Liquid

from asimov import config, logger, LOGGER_LEVEL
from asimov.analysis import Production
from asimov.pipelines import known_pipelines
from asimov.storage import Store
from asimov.utils import update, diff_dict

from .git import EventRepo
from .ini import RunConfiguration
from .review import Review

status_map = {
    "cancelled": "light",
    "finished": "success",
    "uploaded": "success",
    "processing": "primary",
    "running": "primary",
    "stuck": "warning",
    "restart": "secondary",
    "ready": "secondary",
    "wait": "light",
    "stop": "danger",
    "manual": "light",
    "stopped": "light",
}


class DescriptionException(Exception):
    """Exception for event description problems."""

    def __init__(self, message, issue=None, production=None):
        super(DescriptionException, self).__init__(message)
        self.message = message
        self.issue = issue
        self.production = production

    def __repr__(self):
        text = f"""
An error was detected with the YAML markup in this issue.
Please fix the error and then remove the `yaml-error` label from this issue.
<p>
  <details>
     <summary>Click for details of the error</summary>
     <p><b>Production</b>: {self.production}</p>
     <p>{self.message}</p>
  </details>
</p>

- [ ] Resolved
"""
        return text

    def submit_comment(self):
        """
        Submit this exception as a comment on the gitlab
        issue for the event.
        """
        if self.issue:
            self.issue.add_label("yaml-error", state=False)
            self.issue.add_note(self.__repr__())
        else:
            print(self.__repr__())


class Event:
    """
    A specific gravitational wave event or trigger.
    """

    def __init__(self, name, repository=None, update=False, **kwargs):
        """
        Parameters
        ----------
        update : bool
           Flag to determine if the event repo should be updated
           when it is loaded. Defaults to False.
        """
        self.name = name

        self.logger = logger.getChild("event").getChild(f"{self.name}")
        self.logger.setLevel(LOGGER_LEVEL)

        # pathlib.Path(os.path.join(config.get("logging", "directory"), name)).mkdir(
        #    parents=True, exist_ok=True
        # )
        # logfile = os.path.join(config.get("logging", "directory"), name, "asimov.log")

        # fh = logging.FileHandler(logfile)
        # formatter = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        # fh.setFormatter(formatter)
        # self.logger.addHandler(fh)

        if "working_directory" in kwargs:
            self.work_dir = kwargs["working_directory"]
        else:
            self.work_dir = os.path.join(
                config.get("general", "rundir_default"), self.name
            )
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)

        if "ledger" in kwargs:
            if kwargs["ledger"]:
                self.ledger = kwargs["ledger"]
        else:
            self.ledger = None

        if repository:
            if "git@" in repository or "https://" in repository:
                self.repository = EventRepo.from_url(
                    repository, self.name, directory=None, update=update
                )
            else:
                self.repository = EventRepo(repository)
        elif not repository:
            # If the repository isn't set you'll need to make one
            location = config.get("general", "git_default")
            location = os.path.join(location, self.name)
            self.repository = EventRepo.create(location)

        else:
            self.repository = repository

        if "psds" in kwargs:
            self.psds = kwargs["psds"]
        else:
            self.psds = {}

        self.meta = kwargs

        self.issue_object = None
        if "issue" in kwargs:
            if kwargs["issue"]:
                self.issue_object = kwargs.pop("issue")
                self.from_notes()
        else:
            self.issue_object = None

        self.productions = []
        self.graph = nx.DiGraph()

        if "productions" in kwargs:
            for production in kwargs["productions"]:
                try:
                    self.add_production(
                        Production.from_dict(
                            production, event=self, issue=self.issue_object
                        )
                    )
                except DescriptionException as error:
                    error.submit_comment()

        self.productions = []
        self.graph = nx.DiGraph()

        if "productions" in kwargs:
            for production in kwargs["productions"]:
                try:
                    self.add_production(
                        Production.from_dict(
                            production, event=self, issue=self.issue_object
                        )
                    )
                except DescriptionException as error:
                    error.submit_comment()

        self._check_required()

        if (
            ("interferometers" in self.meta)
            and ("calibration" in self.meta)
            and ("data" in self.meta)
        ):
            try:
                self._check_calibration()
            except DescriptionException:
                pass

    def __eq__(self, other):
        if isinstance(other, Event):
            if other.name == self.name:
                return True
            else:
                return False
        else:
            return False

    def update_data(self):
        if self.ledger:
            self.ledger.update_event(self)
        pass

    def _check_required(self):
        """
        Find all of the required metadata is provided.
        """
        return True

    def _check_calibration(self):
        """
        Find the calibration envelope locations.
        """

        if "calibration" not in self.meta["data"]:
            self.logger.warning("There are no calibration envelopes for this event.")

        elif ("calibration" in self.meta["data"]) and (
            set(self.meta["interferometers"]).issubset(
                set(self.meta["data"]["calibration"].keys())
            )
        ):
            pass

        else:
            self.logger.warning(
                f"""Some of the calibration envelopes are missing from this event. """
                f"""{set(self.meta['interferometers']) - set(self.meta['data']['calibration'].keys())} are absent."""
            )

    def _check_psds(self):
        """
        Find the psd locations.
        """
        if ("calibration" in self.meta) and (
            set(self.meta["interferometers"]) == set(self.psds.keys())
        ):
            pass
        else:
            raise DescriptionException(
                "Some of the required psds are missing from this issue. "
                f"{set(self.meta['interferometers']) - set(self.meta['calibration'].keys())}"
            )

    @property
    def webdir(self):
        """
        Get the web directory for this event.
        """
        if "webdir" in self.meta:
            return self.meta["webdir"]
        else:
            return None

    def add_production(self, production):
        """
        Add an additional production to this event.
        """

        if production.name in [production_o.name for production_o in self.productions]:
            raise ValueError(
                f"A production with this name already exists for {self.name}. New productions must have unique names."
            )

        self.productions.append(production)
        self.graph.add_node(production)

        if production.dependencies:
            dependencies = production.dependencies
            dependencies = [
                production
                for production in self.productions
                if production.name in dependencies
            ]
            for dependency in dependencies:
                self.graph.add_edge(dependency, production)

    def __repr__(self):
        return f"<Event {self.name}>"

    @classmethod
    def from_dict(cls, data, issue=None, update=False, ledger=None):
        """
        Convert a dictionary representation of the event object to an Event object.
        """
        event = cls(**data, issue=issue, update=update, ledger=ledger)
        if ledger:
            ledger.add_event(event)
        return event

    @classmethod
    def from_yaml(cls, data, issue=None, update=False, repo=True, ledger=None):
        """
        Parse YAML to generate this event.

        Parameters
        ----------
        data : str
           YAML-formatted event specification.
        issue : int
           The gitlab issue which stores this event.
        update : bool
           Flag to determine if the repository is updated when loaded.
           Defaults to False.
        ledger : `asimov.ledger.Ledger`
           An asimov ledger which the event should be included in.

        Returns
        -------
        Event
           An event.
        """
        data = yaml.safe_load(data)
        if "kind" in data:
            data.pop("kind")
        if (
            not {
                "name",
            }
            <= data.keys()
        ):
            raise DescriptionException(
                "Some of the required parameters are missing from this issue."
            )

        try:
            calibration = data["data"]["calibration"]
        except KeyError:
            calibration = {}

        if "productions" in data:
            if isinstance(data["productions"], type(None)):
                data["productions"] = []
        else:
            data["productions"] = []

        if "interferometers" in data and "event time" in data:

            if calibration.keys() != data["interferometers"]:
                # We need to fetch the calibration data
                from asimov.utils import find_calibrations

                try:
                    data["data"]["calibration"] = find_calibrations(data["event time"])
                except ValueError:
                    logger.warning(
                        f"Could not find calibration files for {data['name']}"
                    )

        if "working directory" not in data:
            data["working directory"] = os.path.join(
                config.get("general", "rundir_default"), data["name"]
            )

        if not repo and "repository" in data:
            data.pop("repository")
        event = cls.from_dict(data, issue=issue, update=update, ledger=ledger)

        if issue:
            event.issue_object = issue
            event.from_notes()

        return event

    @classmethod
    def from_issue(cls, issue, update=False, repo=True):
        """
        Parse an issue description to generate this event.


        Parameters
        ----------
        update : bool
           Flag to determine if the repository is updated when loaded.
           Defaults to False.
        """

        text = issue.text.split("---")

        event = cls.from_yaml(text[1], issue, update=update, repo=repo)
        event.text = text
        # event.from_notes()

        return event

    def from_notes(self):
        """
        Update the event data from information in the issue comments.

        Uses nested dictionary update code from
        https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth#3233356
        """

        notes_data = self.issue_object.parse_notes()
        for note in notes_data:
            update(self.meta, note)

    def get_gracedb(self, gfile, destination):
        """
        Get a file from Gracedb, and store it in the event repository.

        Parameters
        ----------
        gfile : str
           The name of the gracedb file, e.g. `coinc.xml`.
        destination : str
           The location in the repository for this file.
        """

        if "gid" in self.meta:
            gid = self.meta["gid"]
        else:
            raise ValueError("No GID is included in this event's metadata.")

        try:
            client = GraceDb(service_url=config.get("gracedb", "url"))
            file_obj = client.files(gid, gfile)

            with open("download.file", "w") as dest_file:
                dest_file.write(file_obj.read().decode())

            if "xml" in gfile:
                # Convert to the new xml format
                command = ["ligolw_no_ilwdchar", "download.file"]
                pipe = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                out, err = pipe.communicate()

            self.repository.add_file(
                "download.file",
                destination,
                commit_message=f"Downloaded {gfile} from GraceDB",
            )
            self.logger.info(f"Fetched {gfile} from GraceDB")
        except HTTPError as e:
            self.logger.error(
                f"Unable to connect to GraceDB when attempting to download {gfile}. {e}"
            )
            raise HTTPError(e)

    def to_dict(self, productions=True):
        data = {}
        data["name"] = self.name

        if self.repository.url:
            data["repository"] = self.repository.url
        else:
            data["repository"] = self.repository.directory

        for key, value in self.meta.items():
            data[key] = value
        # try:
        #    data['repository'] = self.repository.url
        # except AttributeError:
        #    pass
        if productions:
            data["productions"] = []
            for production in self.productions:
                # Remove duplicate data
                prod_dict = production.to_dict()[production.name]
                dupes = []
                prod_names = []
                for key, value in prod_dict.items():
                    if production.name in prod_names:
                        continue
                    if key in data:
                        if data[key] == value:
                            dupes.append(key)
                for dupe in dupes:
                    prod_dict.pop(dupe)
                prod_names.append(production.name)
                data["productions"].append({production.name: prod_dict})
        data["working directory"] = self.work_dir
        if "issue" in data:
            data.pop("issue")
        if "ledger" in data:
            data.pop("ledger")
        if "pipelines" in data:
            data.pop("pipelines")
        return data

    def to_yaml(self):
        """Serialise this object as yaml"""
        data = self.to_dict()

        return yaml.dump(data, default_flow_style=False)

    def to_issue(self):
        self.text[1] = "\n" + self.to_yaml()
        return "---".join(self.text)

    def draw_dag(self):
        """
        Draw the dependency graph for this event.
        """
        return nx.draw(self.graph, labelled=True)

    def get_all_latest(self):
        """
        Get all of the jobs which are not blocked by an unfinished job
        further back in their history.

        Returns
        -------
        set
            A set of independent jobs which are not finished execution.
        """
        unfinished = self.graph.subgraph(
            [
                production
                for production in self.productions
                if production.finished is False
            ]
        )
        ends = [
            x
            for x in unfinished.reverse().nodes()
            if unfinished.reverse().out_degree(x) == 0
        ]
        return set(ends)  # only want to return one version of each production!

    def build_report(self):
        for production in self.productions:
            production.build_report()

    def html(self):
        card = f"""
        <div class="card event-data" id="card-{self.name}">
        <div class="card-body">
        <h3 class="card-title">{self.name}</h3>
        """

        card += "<h4>Analyses</h4>"
        card += """<div class="list-group">"""

        for production in self.productions:
            card += production.html()

        card += """</div>"""

        # card += """
        # </div></div>
        # """

        return card
