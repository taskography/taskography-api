"""General interface for a planner in stochastic domains.
The key difference is that it returns a policy rather than a plan.
"""

import abc
import numpy as np


class StochasticPlanner:
    """An abstract stochastic planner for PDDLGym.
    """
    def __init__(self):
        self._statistics = {}

    @abc.abstractmethod
    def __call__(self, domain, horizon=np.inf, timeout=10):
        """Takes in a PDDLGym domain. Returns a policy mapping PDDLGym states
        to actions. Note that the state already contains the goal, accessible
        via `state.goal`. The domain for an env is given by `env.domain`.
        """
        raise NotImplementedError("Override me!")

    def reset_statistics(self):
        """Reset the internal statistics dictionary.
        """
        self._statistics = {}

    def get_statistics(self):
        """Get the internal statistics dictionary.
        """
        return self._statistics
