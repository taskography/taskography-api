from typing import Tuple, List, Dict, Set, Type

import os
import random
import tempfile
import shutil
import gym

from pddlgym.core import PDDLEnv
from pddlgym.structs import Literal
from ..samplers import get_task_sampler
from ..samplers.problem_sampler_base import ProblemSamplerBase
from ..utils.constants import OFFICIAL_SPLITS


class Taskography(gym.Env):
    def __init__(
        self,
        sampler: str,
        sampler_kwargs: Dict,
        data_dir: str,
        split: str,
        episodes_per_scene: int = 10,
    ) -> None:
        """The Taskography gym environment class.

        args:
            sampler: task sampler name
            sampler_kwargs: task sampler kwargs
            data_dir: path to root directory of 3D scene graph data
            split: Gibson dataset split
            episodes_per_scene: number of episodes before sampling new scene (default: 10)
        """
        self._sampler = sampler
        self._sampler_kwargs = sampler_kwargs
        self._data_dir = os.path.expandvars(data_dir)
        self._split = split
        self._episodes_per_scene = episodes_per_scene

        # Problem sampling attributes
        self._domain_filepath = sampler_kwargs["domain_filepath"]
        self._problem_dir = tempfile.mkdtemp()
        self._episode_count = 0
        self._problem_samplers = self._load_samplers()
        self._env = None

    @property
    def observation_space(self):
        return self._env.observation_space

    @property
    def action_space(self):
        return self._env.action_space

    def _load_samplers(self) -> List[Type[ProblemSamplerBase]]:
        """Instantiate a task sampler for each scene graph.

        returns:
            problem_samplers: list of task samplers subclassing ProblemSamplerBase
        """
        sampler_cls = get_task_sampler(self._sampler)
        sampler_kwargs = self._sampler_kwargs.copy()

        # Scene graph models
        split = OFFICIAL_SPLITS[self._split]
        scene_graph_filepaths = [
            os.path.join(self._data_dir, split, m)
            for m in os.listdir(os.path.join(self._data_dir, split))
        ]

        problem_samplers = []
        for scene_graph_filepath in scene_graph_filepaths:
            sampler_kwargs["scene_graph_filepath"] = scene_graph_filepath
            problem_samplers.append(sampler_cls(**sampler_kwargs))

        return problem_samplers

    def reset(self) -> Set[Literal]:
        """Sample scene graph and task at uniform random.

        returns:
            state: set of state literals
        """
        if self._episode_count % self._episodes_per_scene == 0:
            self._episode_count = 0
            shutil.rmtree(self._problem_dir)
            self._problem_dir = tempfile.mkdtemp()

            # Sample scene at uniform random
            scene_idx = random.randint(0, len(self._problem_samplers) - 1)
            sampler = self._problem_samplers[scene_idx]

            # Sampler tasks at random
            for task in sampler.sample(k=self._episodes_per_scene, repeat=True):
                sampler.write(**task, problem_dir=self._problem_dir)

            self._env = PDDLEnv(
                domain_file=self._domain_filepath,
                problem_dir=self._problem_dir,
                operators_as_actions=True,
                dynamic_action_space=True,
            )

        assert isinstance(self._env, PDDLEnv)
        self._env.fix_problem_index(self._episode_count)
        state, _ = self._env.reset()

        self._episode_count += 1
        return state

    def step(self, action: Literal) -> Tuple[Set[Literal], float, bool, Dict]:
        """Take symbolic environment step.

        args:
            action: current action as literal

        returns:
            state: set of state literals
            reward: 1 if the goal is reached, 0 otherwise
            done: True if the goal is reached
            debug_info: dictionary of debug information
        """
        state, reward, done, debug_info = self._env.step(action)
        return state, reward, done, debug_info

    def render(self):
        raise NotImplementedError("Symbolic renderer is not implemented.")
