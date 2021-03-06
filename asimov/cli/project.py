"""
Project management tools.
"""

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

import os
import yaml

import click

from asimov import config
from asimov import storage
from asimov import ledger
from asimov import gitlab

from asimov.cli import connect_gitlab

@click.command()
@click.argument("name")
@click.option("--root", default=os.getcwd(),
              help="Location to create the project, default is the current directory.")
@click.option("--working", default="working",
              help="The location to store working directories, default is a directory called 'working' inside the current directory.")
@click.option("--checkouts", default="checkouts",
              help="The location to store cloned git repositories.")
@click.option("--results", default="results",
              help="The location where the results store should be created.")
def init(name, root, working="working", checkouts="checkouts", results="results"):
    """
    Roll-out a new project.
    """
    import venv
    import pathlib

    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    os.chdir(root)

    config.set("project", "name", name)
    config.set("project", "root", root)

    project_name = name

    # Make the virtual environment
    builder = venv.EnvBuilder(system_site_packages=False,
                              clear=False,
                              symlinks=False,
                              upgrade=False,
                              with_pip=True,
                              prompt=f"Asimov {project_name}")

    builder.create("environment")

    config.set("general", "environment", "environment")

    # Make the working directory
    pathlib.Path(working).mkdir(parents=True, exist_ok=True)
    config.set("general", "rundir_default", working)

    # Make the git directory
    pathlib.Path(checkouts).mkdir(parents=True, exist_ok=True)
    config.set("general", "git_default", checkouts)

    # Make the results store
    storage.Store.create(root=results, name=f"{project_name} storage")
    config.set("storage", "results_store", results)

    # Make the ledger
    ledger.Ledger.create()
    config.set("ledger", "engine", "yamlfile")
    config.set("ledger", "location", "ledger.yml")

    with open("asimov.conf", "w") as config_file:
        config.write(config_file)


@click.command()
@click.argument("location")
def clone(location):
    import venv
    import pathlib
    import shutil

    working = "working"
    results = "results"
    
    remote_config = os.path.join(location, "asimov.conf")
    config = configparser.ConfigParser()
    config.read([remote_config])
    click.echo(f'Cloning {config.get("project", "name")}')
    root = os.path.join(os.getcwd(), config.get("project", "name").lower().replace(" ", "-"))
    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    os.chdir(root)
    config.set("project", "root", root)
    # Make the virtual environment
    #builder = venv.EnvBuilder(system_site_packages=False,
    #                          clear=False,
    #                          symlinks=False,
    #                          upgrade=False,
    #                          with_pip=True,
    #                          prompt=f"Asimov {project_name}")

    #builder.create("environment")

    #config.set("general", "environment", "environment")

    # Make the working directory
    #shutil.copytree(os.path.join(config.get("general", "rundir_default"), working)
    #config.set("general", "rundir_default", working)

    # Make the git directory
    #pathlib.Path(checkouts).mkdir(parents=True, exist_ok=True)
    #config.set("general", "git_default", checkouts)

    # Copy the results store
    #shutil.copyfile(os.path.join(location, config.get("storage", "results_store")), results)
    shutil.copytree(os.path.join(location, config.get("storage", "results_store")), results)
    config.set("storage", "results_store", results)

    # Make the ledger
    if config.get("ledger", "engine") == "yamlfile":
        shutil.copyfile(os.path.join(location, config.get("ledger", "location")), "ledger.yml")
    elif config.get("ledger", "engine") == "gitlab":
        _, repository = connect_gitlab(config)

        events = gitlab.find_events(repository,
                                update=False,
                                subset=[None],
                                label=config.get("gitlab", "event_label"),
                                repo=False)

        total = []
        for event in events:
            total.append(yaml.safe_load(event.event_object.to_yaml()))
        with open("ledger.yml", "w") as f:
            f.write(yaml.dump(total))

    config.set("ledger", "engine", "yamlfile")
    config.set("ledger", "location", "ledger.yml")

    with open("asimov.conf", "w") as config_file:
        config.write(config_file)
