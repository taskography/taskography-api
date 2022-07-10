from .taskography import Taskography

import gym

gym.register(
    id="TaskographyEnv-v0",
    entry_point="taskography_api.taskography.envs.taskography:Taskography",
)
