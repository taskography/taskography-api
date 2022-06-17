import re
import os
import sys
import subprocess
import numpy as np

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure
from .adl2strips import ADL2Strips


SATPLAN_REPO = "https://github.com/Khodeir/SatPlan.git"
MEMORY = 10_000_000_000 # 10G


class SATPlan(PDDLPlanner):

    def __init__(self):
        """A wrapper for SatPlan, https://www.cs.rochester.edu/u/kautz/satplan/.
        GitHub repository: https://github.com/Khodeir/SatPlan.git
        """
        super().__init__()
        self._top_dir = os.path.dirname(os.path.realpath(__file__))
        self._satplan_path = os.path.join(self._top_dir, "SatPlan")
        self._exec = os.path.join(self._satplan_path, "bin/satplan")
        print("Instantiating SATPlan")
        if not os.path.exists(self._exec):
            self._install_satplan()

    def _get_cmd_str(self, dom_file, prob_file, timeout):
        timeout_cmd = "gtimeout" if sys.platform == "darwin" else "timeout"
        cmd_str = f"{timeout_cmd} {timeout} {self._exec} -globalmemory {MEMORY} -domain {dom_file} -problem {prob_file} -solution sol.sat.pddl"
        return cmd_str

    def plan_from_pddl(self, dom_file, prob_file, horizon=np.inf, timeout=10, remove_files=False):
        with ADL2Strips(dom_file, prob_file) as (grounded_dom_file, grounded_prob_file):
            return super().plan_from_pddl(grounded_dom_file, grounded_prob_file, horizon=horizon, timeout=timeout, remove_files=remove_files)

    def _output_to_plan(self, output):
        if '***SAT!***' in output:
            with open('sol.sat.pddl', 'r') as f:
                plan_str = f.read()
            os.remove('sol.sat.pddl')
            action_regex = r'^.*\(.+\).*$'
            leading_trailing_parens_regex = r'(^[^(]+\(|\).*$)'
            plan_steps = plan_str.lower().split('\n')
            plan_steps = [re.sub(leading_trailing_parens_regex, '', step).replace('-', ' ')[:-1] for step in plan_steps if re.match(action_regex, step)]
            self._statistics["plan_length"] = len(plan_steps)
            self._statistics["num_node_expansions"] = np.nan
            self._statistics["search_time"] = self._statistics["total_time"] = float(re.search('([0-9.]+) seconds total planner time', output).group(1))
            return plan_steps
        else:
            raise PlanningFailure(f"Plan not found with SatPlan! Error: {output}")

    def _install_satplan(self):
        subprocess.check_output(f'cd {self._satplan_path} && mkdir bin && make && cd -', shell=True)
        subprocess.check_output(f'cd {self._satplan_path} && make install && cd -', shell=True, env=dict(HOME=self._satplan_path))
        assert os.path.exists(self._exec)
