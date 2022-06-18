from email.policy import default
import os
import os.path as osp
import random
from collections import defaultdict

from pddlgym.parser import PDDLDomainParser
from taskography_api.taskography.utils.utils import \
    (register_pddlgym_domain, write_domain_file, domain_name_to_config)
from taskography_api.taskography.utils.constants import (OFFICIAL_SPLITS, SPLIT_SCENES)


class PDDLGymDataset:

    def __init__(self,
                 data_dir,
                 split,
                 problem_dir,
                 train_scenes,
                 samples_per_train_scene,
                 samples_per_test_scene,
                 save_samplers=False,
                 sampler_dir=None,
                 seed=0,
                 ):
        """Generate PDDLGym-interfaced symbolic robot planning datasets fully automatically.

        args:
            data_dir: path to root directory of 3D scene graph data
            split: dataset split (i.e., tiny or medium scene graphs)
            problem_dir: path to save sampled problem files; pddlgym/pddlgym/pddl
            train_scenes: number of scenes to use for training problems
            samples_per_train_scene: unique samples per train scene
            samples_per_test_scene: unique samples for the remaining test scenes
            save_samplers: whether or not to save the scene-specific problem samplers (default: False)
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
                 domain_name,
                 sampler_cls, 
                 sampler_kwargs,
                 ):
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
