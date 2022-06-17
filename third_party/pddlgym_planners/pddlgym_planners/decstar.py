import re
import os
import sys
import subprocess
import numpy as np

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure
from .utils import FilesInCommonTempDirectory


DOCKER_IMAGE = 'khodeir/planutils-taskography:latest'
ALIASES = {
    "agl-decoupled": "--decoupling 'fork(search_type=sat,pruning=cost_frontier(irrelevance=TRANSITIONS),max_leaf_size=10000,build_state_space_size=100)' --heuristic 'hff=ff(cost_type=ONE)' --search 'lazy_greedy(hff,preferred=hff,cost_type=ONE)'",
    "agl-decoupled-fallback": "--decoupling 'portfolio(fallback_on_abstain=true,overwrite_options=true,choose_max_leaves=true,factorings=[fork(search_type=sat,max_leaf_size=10000,build_state_space_size=100),ifork(search_type=sat,max_leaf_size=10000,build_state_space_size=100),incarcs(search_type=sat,max_leaf_size=1000,build_state_space_size=100)])' --heuristic 'hff=ff(cost_type=ONE)' --search 'lazy_greedy(hff,preferred=hff,cost_type=ONE,symmetry=symmetry_state_pruning(lex_prices=false,lex_num_states=false,lex_goal_cost=false))'",
    "opt-decoupled": "--decoupling 'fork(search_type=asda,pruning=cost_frontier(irrelevance=TRANSITIONS),max_leaf_size=10000000)' --search 'astar(lmcut,pruning_heuristic=lmcut(search_type=STAR),pruning=stubborn_sets_decoupled(min_pruning_ratio=0.2,special_case_optimizations=true))'",
    "opt-decoupled-fallback": "--decoupling 'portfolio(fallback_on_abstain=false,overwrite_options=true,choose_max_leaves=true,factorings=[fork(search_type=asda,max_leaf_size=10000000),ifork(max_leaf_size=10000000),incarcs(max_leaf_size=1000000)])' --search 'astar(lmcut,pruning_heuristic=lmcut(search_type=STAR),pruning=stubborn_sets_decoupled(min_pruning_ratio=0.2,special_case_optimizations=true,use_single_var_ifork_optimization=true),symmetry=symmetry_state_pruning(lex_prices=true,lex_num_states=false,lex_goal_cost=false))'", 
}


class DecStar(PDDLPlanner):
    def __init__(self, alias):
        """A wrapper for the DecStar planner.
        Source code: https://bitbucket.org/ipc2018-classical/team2/src/master/
        """
        super().__init__()
        print(f"Instantiating DecStar with --alias {alias}")
        assert alias in ALIASES, f"Expected alias in {ALIASES}"
        self.alias = alias
        self.search_options = ALIASES[alias]
        self.install_decstar()

    def install_decstar(self):
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
        cmd_str = f"docker run --privileged -it -v {probdom_dir}:/problem -w /problem {DOCKER_IMAGE} {timeout_cmd} {timeout} /root/.planutils/bin/decstar /problem/{dom_fname} /problem/{prob_fname} {self.search_options}"
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
            raise PlanningFailure("Plan not found with DecStar! Error: {}".format(
                output))
        if "Plan length: 0 step" in output:
            return []
        
        plan = re.findall(r"(.+) \(\d+?\)", output.lower())
        if not plan:
            raise PlanningFailure("Plan not found with DecStar! Error: {}".format(
                output))
        return plan
    
    def _cleanup(self):
        pass
