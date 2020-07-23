"""LALInference Pipeline specification."""


import os
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException
from ..ini import RunConfiguration


class LALInference(Pipeline):
    """
    The LALInference Pipeline.

    Parameters
    ----------
    production : :class:`asimov.Production`
       The production object.
    category : str, optional
        The category of the job.
        Defaults to "C01_offline".
    """

    STATUS = {"wait", "stuck", "stopped", "running", "finished"}

    def __init__(self, production, category=None):
        super(LALInference, self).__init__(production, category)

        if not production.pipeline.lower() == "lalinference":
            raise PipelineException

    def build_dag(self, psds=None, user=None, clobber_psd=False):
        """
        Construct a DAG file in order to submit a production to the
        condor scheduler using LALInferencePipe.

        Parameters
        ----------
        production : str
           The production name.
        psds : dict, optional
           The PSDs which should be used for this DAG. If no PSDs are
           provided the PSD files specified in the ini file will be used
           instead.
        user : str
           The user accounting tag which should be used to run the job.

        Raises
        ------
        PipelineException
           Raised if the construction of the DAG fails.
        """
        os.chdir(os.path.join(self.production.event.repository.directory,
                              self.category))
        gps_file = self.production.get_timefile()
        ini = self.production.get_configuration()

        if not user:
            if self.production.get_meta("user"):
                user = self.production.get_meta("user")
        else:
            user = ini._get_user()
            self.production.set_meta("user", user)

        ini.update_accounting(user)

        if 'queue' in self.production.meta:
            queue = self.production.meta['queue']
        else:
            queue = 'Priority_PE'

        ini.set_queue(queue)

        if psds:
            ini.update_psds(psds, clobber=clobber_psd)
            ini.run_bayeswave(False)
        else:
            # Need to generate PSDs as part of this job.
            ini.run_bayeswave(True)

        ini.update_webdir(self.production.event.name,
                          self.production.name,
                          rootdir=self.production.event.webdir)
        ini.save()

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(os.path.expanduser("~"),
                                  self.production.event.name,
                                  self.production.name)
            self.production.rundir = rundir

        pipe = subprocess.Popen(["lalinference_pipe",
                                 "-g", f"{gps_file}",
                                 "-r", self.production.rundir,
                                 ini.ini_loc],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()

        if err or "Successfully created DAG file." not in str(out):
            self.production.status = "stuck"
            raise PipelineException(f"DAG file could not be created.\n\n{out}\n\n{err}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)
        else:
            return out
