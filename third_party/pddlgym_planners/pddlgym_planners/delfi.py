import re
import os
import sys
import subprocess
import numpy as np

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure
from .utils import FilesInCommonTempDirectory


DOCKER_IMAGE = 'khodeir/planutils-taskography:latest'


class Delfi(PDDLPlanner):

    def __init__(self):
        """A wrapper for the Delfi planner.
        Source code: https://bitbucket.org/ipc2018-classical/team23/src/ipc-2018-seq-opt/
        """

        super().__init__()
        print("Instantiating Delfi")
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
        cmd_str = f"docker run --privileged -it -v {probdom_dir}:/problem -w /problem {DOCKER_IMAGE} {timeout_cmd} {timeout} /root/.planutils/bin/delfi /problem/{dom_fname} /problem/{prob_fname} /problem/delfi.plan --image-from-lifted-task"
        return cmd_str

    def _output_to_plan(self, output):
        # Technically this is number of evaluated states which is always
        # 1+number of expanded states, but we report evaluated for consistency
        # with FF.
        num_node_expansions = re.findall(r"evaluated (\d+) state", output.lower())
        plan_length = re.findall(r"plan length: (\d+) step", output.lower())
        plan_cost = re.findall(r"plan cost: (\d+)", output.lower())
        search_time = re.findall(r"search time: (\d+\.\d+)", output.lower())[-1:]
        total_time = re.findall(r"total time: (\d+\.\d+)", output.lower())
        if "num_node_expansions" not in self._statistics:
            self._statistics["num_node_expansions"] = 0
        if len(num_node_expansions) == 1:
            assert int(num_node_expansions[0]) == float(num_node_expansions[0])
            # self._statistics["num_node_expansions"] += int(
            #     num_node_expansions[0])
            self._statistics["num_node_expansions"] = int(num_node_expansions[0])
        if len(search_time) == 1:
            try:
                search_time_float = float(search_time[0])
                self._statistics["search_time"] = search_time_float
            except:
                raise PlanningFailure("Error on output's search time format: {}".format(search_time[0]))
        if len(total_time) == 1:
            try:
                total_time_float = float(total_time[0])
                self._statistics["total_time"] = total_time_float
            except:
                raise PlanningFailure("Error on output's total time format: {}".format(total_time[0]))
        if len(plan_length) == 1:
            try:
                plan_length_int = int(plan_length[0])
                self._statistics["plan_length"] = plan_length_int
            except:
                raise PlanningFailure("Error on output's plan length format: {}".format(plan_length[0]))
        if len(plan_cost) == 1:
            try:
                plan_cost_int = int(plan_cost[0])
                self._statistics["plan_cost"] = plan_cost_int
            except:
                raise PlanningFailure("Error on output's plan cost format: {}".format(plan_cost[0]))
        if "Solution found" not in output:
            raise PlanningFailure("Plan not found with Delfi! Error: {}".format(
                output))
        if "Plan length: 0 step" in output:
            return []
        try:
            plan_fpath = os.path.join(self.tmpdir.dirname, 'delfi.plan')
            with open(plan_fpath, 'r') as f:
                plan_output = f.read()
            self.tmpdir.cleanup()
            plan = re.findall(r"^\(([^)]+)\)", plan_output, re.M)
            assert plan
            return plan
        except:
            raise PlanningFailure("Plan not found with Delfi! Error: {}".format(
                output))
    
    def _cleanup(self):
        pass
