import os
import os.path as osp
import random
from collections import defaultdict
from __future__ import annotations

from pddlgym.parser import PDDLDomainParser
from taskography_api.taskography.samplers.problem_sampler_base import ProblemSamplerBase
from taskography_api.taskography.utils.utils import (register_pddlgym_domain, write_domain_file, domain_name_to_config)
from taskography_api.taskography.utils.constants import (OFFICIAL_SPLITS, SPLIT_SCENES)


class PDDLGymDataset:

    def __init__(self,
                 data_dir: str,
                 split: str,
                 problem_dir: str,
                 train_scenes: int,
                 samples_per_train_scene: int,
                 samples_per_test_scene: int,
                 save_samplers: bool=False,
                 sampler_dir: str=None,
                 seed: int=0,
                 ) -> None:
        """A class for generating PDDLGym 3D scene graph symbolic planning datasets.

        args:
            data_dir: path to root directory of 3D scene graph data
            split: dataset split
            problem_dir: path to save sampled problem files
            train_scenes: number of scenes to use for training problems        
            samples_per_train_scene: unique samples per train scene
            samples_per_test_scene: unique samples for the remaining test scenes
            save_samplers: save the scene-specific problem samplers (default: False)
            sampler_dir: path to save the scene-specific problem samplers (default: None)
            seed: pseudo-random generator seed (default: 0)
        """
        assert osp.isdir(data_dir), "Dataset directory does not exist."
        assert split in OFFICIAL_SPLITS, "Please specify a valid data split."
        assert train_scenes <= SPLIT_SCENES[split], "Number of training scenes exceeds dataset split size."
        
        # Passed parameters
        self.data_dir = data_dir
        self.split = split
        self.problem_dir = problem_dir
        self.save_samplers = save_samplers
        self.sampler_dir = sampler_dir
        self.train_scenes = train_scenes
        self.samples_per_train_scene = samples_per_train_scene
        self.samples_per_test_scene = samples_per_test_scene
        self.seed = seed
        
        # Domain
        self.domain_filepath = None
        self.problem_filepaths = defaultdict(list)

    def generate(self, 
                 domain_name: str,
                 sampler_cls: ProblemSamplerBase, 
                 sampler_kwargs: dict
                 ) -> tuple[str, list[str]]:
        """Generate 3D scene graph symbolic planning domain. Dynamically modify PDDLGym scripts
        to register the environment.

        args:
            domain_name: unique name of the environment
            sampler_cls: task sampler subclassing ProblemSamplerBase
            sampler_kwargs: task sampler kwargs
        
        returns:
            domain_filepath: path to written PDDL domain file
            problem_filepaths: paths to written PDDL problem files
        """
        # Convert domain name
        self.domain_filepath = osp.join(self.problem_dir, domain_name + ".pddl")
        assert not osp.exists(self.domain_filepath), f"Dataset {domain_name} already exists"
        if self.sampler_dir is None:
            self.sampler_dir = osp.join("datasets/samplers", domain_name_to_config(domain_name)["domain_type"])

        # Write PDDL domain file
        pddlgym_domain = PDDLDomainParser(sampler_kwargs["domain_filepath"], expect_action_preds=False, operators_as_actions=False)        
        write_domain_file(pddlgym_domain, self.domain_filepath, domain_name)
        register_pddlgym_domain(self.problem_dir, domain_name)
        sampler_kwargs["domain_filepath"] = self.domain_filepath
        
        # Scene graph models
        split = OFFICIAL_SPLITS[self.split]
        scene_graph_filepaths = [osp.join(self.data_dir, split, m) for m in os.listdir(osp.join(self.data_dir, split))]
        random.shuffle(scene_graph_filepaths)

        # Generate dataset
        mode = "train"
        samples_per_scene = self.samples_per_train_scene
        problem_dir = osp.join(self.problem_dir, domain_name)
        os.mkdir(problem_dir)
        for i, scene_graph_filepath in enumerate(scene_graph_filepaths):
            
            # Instantiate sampler
            try:
                sampler = sampler_cls.load_from_name(
                    scene_graph_filepath,
                    sampler_kwargs["complexity"], 
                    sampler_kwargs["bagslots"],
                    dir=self.sampler_dir
                )                
            except:
                sampler_kwargs["scene_graph_filepath"] = scene_graph_filepath
                sampler = sampler_cls(**sampler_kwargs)

            # Sample tasks
            if sampler.valid():
                if self.save_samplers: sampler.save(dir=self.sampler_dir)

                print(f"Sampling {samples_per_scene} tasks in {sampler._model_name}")
                tasks = sampler.sample(k=samples_per_scene)
                for task in tasks:
                    problem_filepath = sampler.write(**task, problem_dir=problem_dir)   
                    self.problem_filepaths[mode].append(problem_filepath)             

                if i == self.train_scenes:
                    mode = "test"
                    samples_per_scene = self.samples_per_test_scene
                    problem_dir = problem_dir + '_test'
                    os.mkdir(problem_dir)

        return self.domain_filepath, self.problem_filepaths
