import re
import os
import sys
import subprocess
import numpy as np

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure
from .utils import FilesInCommonTempDirectory


DOCKER_IMAGE = 'khodeir/planutils-taskography:latest'
ALIASES = [
    "seq-agl-cerberus2018", # dag from coloring
    "seq-sat-cerberus2018",
    "seq-agl-cerberus-gl-2018", # dag greedy level
    "seq-sat-cerberus-gl-2018",
]


class Cerberus(PDDLPlanner):

    def __init__(self, alias=ALIASES[0]):
        """A wrapper for the Cerberus planner.
        GitHub repository: https://github.com/ctpelok77/fd-red-black-postipc2018
        """
        super().__init__()
        print(f"Instantiating Cerberus with --alias {alias}")
        assert alias in ALIASES, f"Expected alias in {ALIASES}"
        self.alias = alias
        self.install_cerberus()

    def install_cerberus(self):
        subprocess.check_call(f'docker pull {DOCKER_IMAGE}', shell=True, stdout=subprocess.DEVNULL)

    def plan_from_pddl(self, dom_file, prob_file, horizon=np.inf, timeout=10, remove_files=False):
        with FilesInCommonTempDirectory(dom_file, prob_file) as (dom_file, prob_file):
            return super().plan_from_pddl(dom_file, prob_file, horizon=horizon, timeout=timeout, remove_files=remove_files)

    def _get_cmd_str(self, dom_file, prob_file, timeout):
        timeout_cmd = "gtimeout" if sys.platform == "darwin" else "timeout"
        probdom_dir = os.path.dirname(dom_file)
        dom_fname = os.path.basename(dom_file)
        prob_fname = os.path.basename(prob_file)
        assert probdom_dir == os.path.dirname(prob_file), "Files must be in the same directory"
        cmd_str = f"docker run --privileged -it -v {probdom_dir}:/problem -w /problem {DOCKER_IMAGE} {timeout_cmd} {timeout} /root/.planutils/bin/cerberus --alias {self.alias} /problem/{dom_fname} /problem/{prob_fname}"
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
            raise PlanningFailure("Plan not found with Cerberus! Error: {}".format(
                output))
        if "Plan length: 0 step" in output:
            return []
        
        plan = re.findall(r"(.+) \(\d+?\)", output.lower())
        if not plan:
            raise PlanningFailure("Plan not found with Cerberus! Error: {}".format(
                output))
        return plan
    
    def _cleanup(self):
        pass
