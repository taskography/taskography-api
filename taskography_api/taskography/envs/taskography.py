import os
import random
import tempfile
import shutil
import gym
from pddlgym.core import PDDLEnv

from ..samplers import get_task_sampler
from ..utils.constants import OFFICIAL_SPLITS


class Taskography(gym.Env):

    def __init__(self,
                 sampler,
                 sampler_kwargs,
                 data_dir,
                 split,
                 episodes_per_scene=10,
                 ):
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

    def _load_samplers(self):
        """Load up a task sampler for each scene_graph_filepath.
        """
        sampler_cls = get_task_sampler(self._sampler)
        sampler_kwargs = self._sampler_kwargs.copy()
        
        # Scene graph models
        split = OFFICIAL_SPLITS[self._split]
        scene_graph_filepaths = [os.path.join(self._data_dir, split, m) \
            for m in os.listdir(os.path.join(self._data_dir, split))]

        problem_samplers = []
        for scene_graph_filepath in scene_graph_filepaths:
            # Instantiate sampler
            sampler_kwargs["scene_graph_filepath"] = scene_graph_filepath
            problem_samplers.append(sampler_cls(**sampler_kwargs))

        return problem_samplers

    def reset(self):
        """Sample scene graph taks at random.
        """
        if self._episode_count % self._episodes_per_scene == 0:
            self._episode_count = 0
            shutil.rmtree(self._problem_dir)
            self._problem_dir = tempfile.mkdtemp()

            # Sample scene at uniform random
            scene_idx = random.randint(0, len(self._problem_samplers)-1)
            sampler = self._problem_samplers[scene_idx]

            # Sampler tasks at random
            for task in sampler.sample(k=self._episodes_per_scene, repeat=True):
                sampler.write(**task, problem_dir=self._problem_dir)

            self._env = PDDLEnv(
                domain_file=self._domain_filepath,
                problem_dir=self._problem_dir,
                operators_as_actions=True,
                dynamic_action_space=True
            )
            
        assert isinstance(self._env, PDDLEnv)
        self._env.fix_problem_index(self._episode_count)
        state, _ = self._env.reset()
        
        self._episode_count += 1
        return state

    def step(self, action):
        """Take symbolic environment step.
        """
        return self._env.step(action)

    def render(self):
        raise NotImplementedError("Symbolic renderer is not implemented.")
