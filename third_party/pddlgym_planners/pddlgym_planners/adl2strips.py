import os
import shlex 
import subprocess

from .utils import FilesInCommonTempDirectory


class ADL2Strips:

    def __init__(self, domain_filename, problem_filename, timeout=10):
        """A simple translation class from ADL to Strips DSLs, based on the below repository.
        GitHub Repository: https://github.com/pucrs-automated-planning/adl2strips.git
        """
        self.domain_filename = domain_filename
        self.problem_filename = problem_filename
        self.timeout = timeout
        
        self.submodule_path = os.path.dirname(os.path.realpath(__file__))
        self.exec_path = os.path.join(self.submodule_path, "ff")
        if not os.path.exists(self.exec_path):
            self.install_adl2strips()
        self.tmpdir = None

    def install_adl2strips(self):
        os.system("cd {} && make && cd -".format(self.submodule_path))
        assert os.path.exists(self.exec_path)

    def __enter__(self):
        """Open ADL domain, problem files as STRIPS.
        """
        self.tmpdir = FilesInCommonTempDirectory(self.domain_filename, self.problem_filename)
        domain_fpath, problem_fpath = self.tmpdir.file_paths
        tmpdirname = self.tmpdir.dirname
        domain_fname, problem_fname = os.path.basename(domain_fpath), os.path.basename(problem_fpath)

        cmd_str = f'{self.exec_path} -p {tmpdirname} -o /{domain_fname} -f /{problem_fname}'
        output = subprocess.check_output(shlex.split(cmd_str), timeout=self.timeout, cwd=tmpdirname, stderr=subprocess.STDOUT)
        translated_domfile_path = os.path.join(tmpdirname, 'domain.pddl')
        translated_probfile_path = os.path.join(tmpdirname, 'facts.pddl')

        return translated_domfile_path, translated_probfile_path

    def __exit__(self, type, value, traceback):
        """Clean up temporary directory and files within.
        """
        if self.tmpdir is not None:
            self.tmpdir.cleanup()
