import os
import pickle
from collections import defaultdict

import pddlgym
from pddlgym_planners import PlannerHandler
from pddlgym_planners.planner import PlanningTimeout, PlanningFailure
from taskography_api.taskography.utils.utils import domain_to_pddlgym_name


class TrajectoryGymDataset:
    def __init__(
        self, env: str, planner: str, trajectory_dir: str = None, test: bool = True
    ) -> None:
        """A class for generating expert demonstrations from symbolic task
        planners on 3D scene graph PDDLGym environments.

        args:
            env: PDDLGym environment name
            planner: task planner name
            trajectory_dir: path to save trajectory data
            test: save test split solution (default: True)
        """
        self.env = env
        self.planner = PlannerHandler()[planner]
        self.trajectory_dir = trajectory_dir
        self.test = test

    def generate_from_env(self) -> None:
        """Generate state-action trajectories atop PDDLGym environment."""
        assert self.env is not None, "PDDLGym environment name not provided"
        domain_name = self.env.strip("PDDLEnv").split("-")[0].lower()

        # Output trajectory directory
        if self.trajectory_dir is None:
            self.trajectory_dir = "datasets/trajectories"
        if self.trajectory_dir.split("/")[-1] == "trajectories":
            self.trajectory_dir = os.path.join(self.trajectory_dir, domain_name)
        if not os.path.exists(self.trajectory_dir):
            os.makedirs(self.trajectory_dir)

        metadata = defaultdict(list)
        solved, failed, timeout = 0, 0, 0
        modes = ["train"] if not self.test else ["train", "test"]
        for mode in modes:
            # Make environment
            env_name = domain_to_pddlgym_name(domain_name, test=mode == "test")
            env = pddlgym.make(env_name)

            # Attempt to solve problems
            for i in range(len(env.problems)):
                env.fix_problem_index(i)
                state, _ = env.reset()
                count = solved + failed + timeout

                try:
                    plan = self.planner.plan_to_action_from_pddl(
                        domain=env.domain,
                        state=state,
                        dom_file=env.domain.domain_fname,
                        prob_file=env.problems[i].problem_fname,
                    )
                    solved += 1
                    saved = True

                    # Collect states and actions
                    states = []
                    curr_state = state
                    for action in plan:
                        states.append(curr_state)
                        curr_state, _, _, _ = env.step(action)
                    assert len(states) == len(plan), "Number of states and actions are unequal"

                    # Save trajectory
                    with open(os.path.join(self.trajectory_dir, f"problem{count}.pkl"), "wb") as fh:
                        pickle.dump((states, plan), fh)

                except PlanningTimeout:
                    timeout += 1
                    saved = False

                except PlanningFailure:
                    failed += 1
                    saved = False

                metadata[mode].append((f"problem{count}", saved))

        # Save metadata
        with open(os.path.join(self.trajectory_dir, "metadata.pkl"), "wb") as fh:
            pickle.dump(metadata, fh)
