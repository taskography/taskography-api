import os
import re
import sys
import tempfile

from .pddl_planner import PDDLPlanner
from .planner import PlanningFailure


URL = "git@github.mit.edu:ronuchit/correa-lifted-planner-icaps-2020.git"


class Lifted(PDDLPlanner):
    """A wrapper for Correa et al. lifted planner, https://ai.dmi.unibas.ch/papers/correa-et-al-icaps2020.pdf.
    Github repository: git@github.mit.edu:ronuchit/correa-lifted-planner-icaps-2020.git
    """
    def __init__(self):
        super().__init__()
        dirname = os.path.dirname(os.path.realpath(__file__))
        self._exec = os.path.join(
            dirname, "correa-lifted-planner-icaps-2020/powerlifted.py")
        if not os.path.exists(self._exec):
            self._install_lifted()

    def _get_cmd_str(self, dom_file, prob_file, timeout):
        translator_file = tempfile.NamedTemporaryFile(delete=False).name
        timeout_cmd = "gtimeout" if sys.platform == "darwin" else "timeout"
        cmd_str = "{} {} {} -d {} -i {} -s gbfs -e goalcount -g full_reducer --translator-output-file {}".format(timeout_cmd, timeout, self._exec, dom_file, prob_file, translator_file)
        return cmd_str

    def _output_to_plan(self, output):
        num_node_expansions = re.findall(r"generated (\d+) state", output.lower())
        if "num_node_expansions" not in self._statistics:
            self._statistics["num_node_expansions"] = 0
        if len(num_node_expansions) == 1:
            assert int(num_node_expansions[0]) == float(num_node_expansions[0])
            self._statistics["num_node_expansions"] += int(num_node_expansions[0])
        if "Solution found." not in output:
            raise PlanningFailure("Plan not found with FD! Error: {}".format(
                output))
        found_plan = re.findall(r"solution \d+?: \((.+)\)", output.lower())
        found_plan = [step.strip() for step in found_plan]
        if not found_plan:
            raise PlanningFailure("Plan not found with lifted planner! Error: {}".format(output))
        return found_plan

    def _install_lifted(self):
        loc = os.path.dirname(self._exec)
        # Install and compile lifted planner.
        os.system("git clone {} {}".format(URL, loc))
        os.system("cd {} && ./build.py && cd -".format(loc))
        assert os.path.exists(self._exec)
        assert os.path.exists(os.path.join(loc, "builds", "release"))
