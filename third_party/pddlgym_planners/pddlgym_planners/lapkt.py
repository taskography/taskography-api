import re
import os
import sys
import subprocess
import numpy as np

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure
from .utils import FilesInCommonTempDirectory


DOCKER_IMAGE = 'khodeir/bfws:latest'


class LAPKTBFWS(PDDLPlanner):

    def __init__(self):
        """A wrapped for the LAPKT-BFWS planner.
        GitHub repository: https://github.com/nirlipo/BFWS-public
        """
        super().__init__()
        print("Instantiating LAPKT-BFWS")
        self.install_delfi()

    def install_delfi(self):
        subprocess.check_call(f'docker pull {DOCKER_IMAGE}', shell=True, stdout=subprocess.DEVNULL)

    def plan_from_pddl(self, dom_file, prob_file, horizon=np.inf, timeout=10, remove_files=False):
        self.tmpdir = FilesInCommonTempDirectory(dom_file, prob_file)
        (dom_file, prob_file) = self.tmpdir.new_fpaths
        return super().plan_from_pddl(dom_file, prob_file, horizon=horizon, timeout=timeout, remove_files=remove_files)


    def _get_cmd_str(self, dom_file, prob_file, timeout):
        timeout_cmd = "gtimeout" if sys.platform == "darwin" else "timeout"
        probdom_dir = os.path.dirname(dom_file)
        dom_fname = os.path.basename(dom_file)
        prob_fname = os.path.basename(prob_file)
        assert probdom_dir == os.path.dirname(prob_file), "Files must be in the same directory"
        cmd_str = f"docker run --privileged -it -v {probdom_dir}:/problem -w /problem {DOCKER_IMAGE} {timeout_cmd} {timeout} bfws --domain /problem/{dom_fname} --problem /problem/{prob_fname} --output /problem/bfws.plan --BFWS-f5 1"
        return cmd_str

    def _output_to_plan(self, output):
        try:
            self._statistics["num_node_expansions"] = int(re.search('nodes expanded during search: (\d+)', output.lower()).group(1))
            self._statistics["total_time"] = self._statistics["search_time"] = float(re.search('total time: ([0-9.]+)', output.lower()).group(1))
            self._statistics["plan_cost"] = float(re.search('plan found with cost: ([0-9.]+)', output.lower()).group(1))
        except:
            raise PlanningFailure("Failure parsing output of bfws")

        try:
            plan_fpath = os.path.join(self.tmpdir.dirname, 'bfws.plan')
            with open(plan_fpath, 'r') as f:
                plan_output = f.read()
            self.tmpdir.cleanup()
            plan = re.findall(r"^\(([^)]+)\)", plan_output.lower(), re.M)
            assert plan
            self._statistics["plan_length"] = len(plan)
            return plan
        except:
            raise PlanningFailure("Plan not found with BFWS! Error: {}".format(output))

    def _cleanup(self):
        pass
