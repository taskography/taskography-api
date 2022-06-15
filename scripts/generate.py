import argparse
import random
import numpy as np

from taskography_api.taskography.utils.config import PDDLGymDatasetConfig
from taskography_api.taskography.datasets.pddlgym_dataset import PDDLGymDataset
from taskography_api.taskography.samplers import get_task_sampler


def generate(config):
    """TODO: Create description.
    """
    pddlgym_dataset = PDDLGymDataset(
        seed=config["seed"],
        **config["dataset_kwargs"], 
    )
    pddlgym_dataset.generate(
        domain_name=config.domain_name, 
        sampler_cls=get_task_sampler(config["sampler"]), 
        sampler_kwargs=config["sampler_kwargs"]
    )
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to YAML configuration file")
    args = parser.parse_args()

    # Load config
    config = PDDLGymDatasetConfig.load(args.config)
    config.save()
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    generate(config)
