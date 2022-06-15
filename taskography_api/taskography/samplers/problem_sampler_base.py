import os
import json
import pickle
from abc import (ABC, abstractmethod)

from .task_sampler_base import TaskSamplerBase
from taskography_api.taskography.utils.loader import loader
from taskography_api.taskography.utils.utils import scene_graph_name, sampler_name
from pddlgym.parser import (PDDLDomainParser, PDDLProblemParser)


class ProblemSamplerBase(ABC, TaskSamplerBase):

    # Number of problem files written.
    _num_written = 0
    
    @abstractmethod
    def __init__(self, 
                 domain_filepath, 
                 scene_graph_filepath, 
                 complexity=1,
                 bagslots=None
                 ):
        """An abstract class for sampling planning tasks in large 3D scene graphs.

        args:
            domain_filepath: path to PDDL domain file
            scene_graph_filepath: path to 3D scene file
            complexity: level of difficulty for the sampled task (default: 1)
            bagslots: number of bagslots the agent is equipped with for Courier tasks (default: None)
        """
        assert os.path.exists(domain_filepath)
        assert os.path.exists(scene_graph_filepath)

        TaskSamplerBase.__init__(self, loader(scene_graph_filepath))
        self.domain = PDDLDomainParser(domain_filepath, expect_action_preds=False, operators_as_actions=False)
        self.complexity = complexity
        self.bagslots = bagslots
        
        # Populate in abstract methods
        self.tasks = set()
        self.entities = set()
        self.entities_map = dict()
        self.predicates = set()
        self.create_entities()
        self.create_predicates()

        # Labelling attributes
        self._model_name = scene_graph_name(scene_graph_filepath)
        self._problem_prefix = self._model_name + self.domain.domain_name
        self._sampler_name = sampler_name(scene_graph_filepath, self.complexity, self.bagslots)

    @abstractmethod
    def create_entities(self):
        """Create set of task-agnostic PDDL entities, and a mapping from their entity
        string names to their corresponding PDDLGym objects.
        """
        pass
    
    @abstractmethod
    def create_predicates(self):
        """Create a set of task-agnostic PDDL predicates, and a mapping from their predicate
        string names to their corresponding PDDLGym objects.
        """
        pass

    @abstractmethod
    def sample_task_repr(self):
        """Randomly sample a single task and cast it into a low-memory representation. E.g., 
        task_repr = {
            "a_rid": room_*,                        # agent starting room ID      
            "a_pid": place_*,                       # agent starting place ID     
            "a_lid": location_*,                    # agent starting location ID
            "i_ids": [i_1, i_2, ..., i_complexity], # goal item IDs       
            "r_ids": [r_1, r_2, ..., r_complexity]  # goal receptacle IDS 
        }
        Note: 
            - "a_rid" and "a_pid" keys may be ommited for the taskographyv1.pddl domain
            - For lifted planning problems, "i_ids" and "r_ids" reflect item and receptacle class names.
        
        returns:
            task_repr: low-memory dictionary representation of a task
        """
        pass

    @abstractmethod
    def sample(self, k=1, repeat=False):
        """Sample a list of k possible tasks in the domain. Hash low-memory representations
        of tasks into self.tasks to ensure novel tasks are sampled when repeat=False.
        
        args:
            k: batch size of tasks (default: 1)
            repeat: whether or not the sampled task can be repeated (default: False)
        returns:
            tasks: list of sampled task dictionaries
        """
        task_reprs = []
        while len(task_reprs) < k:
            task_repr = self.sample_task_repr()
            task_repr_str = json.dumps(task_repr, sort_keys=True)
            if repeat or task_repr_str not in self.tasks: task_reprs.append(task_repr)
            if not repeat and task_repr_str not in self.tasks: self.tasks.add(task_repr_str)
        return task_reprs

    @abstractmethod
    def valid(self):
        """Checks ensuring the scene graph is valid for the task configuration.
        """
        # All objects / receptacles must have a designated parent room
        return self.valid_scene

    # def reset(self, complexity=1, bagslots=None):
    #     """Reset state of the sampler and optionally alter the complexity of the tasks, 
    #     perhaps to be used in a curriculum train scheme.
    #     """
    #     self.tasks = set()
    #     self.complexity = complexity
    #     self.bagslots = bagslots

    def write(self, 
              objects,
              initial_state,
              goal,
              problem_filepath=None,
              problem_name=None,
              problem_dir='',
              domain_name=None,
              fast_downward_order=True
              ):
        """Write PDDL problem file to disk.

        args:
            objects: full set of objects in the planning problem
            initial_state: full set of predicates grounded over objects, i.e., facts
            goal: partial set of goal predicates grounded over objects, i.e., literals
            problem_filepath: path where the PDDL problem file will be written (default: None)
            problem_name: name of the planning problem (default: None)
            problem_dir: optional root directory to save the problem file (default: '')
            domain_name: name of the planning domain (default: None)
            fast_downward_order: whether or not the file should be written in FD-order (default: True)
        returns:
            problem_filepath: full path to the written problem file
        """
        assert problem_dir != '' and problem_filepath is None
        problem_filepath = os.path.join(problem_dir, f"problem{ProblemSamplerBase._num_written}.pddl") \
            if problem_filepath is None else problem_filepath
        problem_name = f"{self._problem_prefix}Problem{ProblemSamplerBase._num_written}" \
            if problem_name is None else problem_name
        domain_name = self.domain.domain_name \
            if domain_name is None else domain_name
        
        assert not os.path.exists(problem_filepath)
        PDDLProblemParser.create_pddl_file(
            objects=objects,
            initial_state=initial_state,
            goal=goal,
            file_or_filepath=problem_filepath,
            problem_name=problem_name,
            domain_name=domain_name,
            fast_downward_order=fast_downward_order
        )
        ProblemSamplerBase._num_written += 1  
        return os.path.realpath(problem_filepath)

    def save(self, dir="datasets/samplers"):
        """Save an instance of the sampler as a pickle file.
        """
        if not os.path.exists(dir): os.makedirs(dir)
        filename = os.path.join(dir, self._sampler_name + ".pkl")
        assert not os.path.exists(filename), f"Sampler already exists at {filename}"
        with open(filename, "wb") as fh:
            pickle.dump(self, fh)
        
    @classmethod
    def load(cls, filepath):
        """Load a saved pickle instance of the sampler.
        """
        with open(filepath, "rb") as fh:
            return pickle.load(fh)

    @classmethod
    def load_from_name(cls, scene_graph_filepath, complexity, bagslots=None, dir="datasets/samplers"):
        """Load a saved pickle instance of the sampler.
        """
        _sampler_name = sampler_name(scene_graph_filepath, complexity, bagslots) + ".pkl"
        with open(os.path.join(dir, _sampler_name), "rb") as fh:
            sampler = pickle.load(fh)
        return sampler
