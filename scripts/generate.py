import os
import yaml
import random
import numpy as np
import argparse

from taskography_api.taskography.samplers import get_task_sampler
from taskography_api.taskography.datasets.pddlgym_dataset import PDDLGymDataset
from taskography_api.taskography.datasets.trajectory_dataset import TrajectoryDataset


def generate(config):
    """TODO: Create description.
    """
    pddlgym_dataset = PDDLGymDataset(**config["dataset_kwargs"], seed=config["seed"])
    pddlgym_dataset.generate(get_task_sampler(config["sampler"]), config["sampler_kwargs"])
    
    # create TrajectoryDataset
    # create gym environment for each problem
    # solve with specified planner
    # pickle states and actions into a dataset
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to YAML configuration file")
    args = parser.parse_args()

    with open(args.config, "r") as fh:
        config = yaml.safe_load(fh)

    random.seed(config["seed"])
    np.random.seed(config["seed"])
    generate(config)
