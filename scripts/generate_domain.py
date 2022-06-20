import argparse
import yaml
import random
import numpy as np

import taskography_api.taskography.datasets as datasets
import taskography_api.taskography.utils as utils
from taskography_api.taskography.samplers import get_task_sampler


def generate_domain(config):
    """Generate a PDDLGym environment as per the task sampler and dataset 
    configuration parameters.
    """
    dataset = vars(datasets)[config["dataset"]](
        seed=config["seed"],
        **config["dataset_kwargs"], 
    )
    domain_filepath, problem_filepaths = dataset.generate(
        domain_name=config.domain_name,
        sampler_cls=get_task_sampler(config["sampler"]), 
        sampler_kwargs=config["sampler_kwargs"]
    )
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to YAML configuration file")
    args = parser.parse_args()
    
    with open(args.config, "r") as fh:
        config = yaml.safe_load(fh)
    config = vars(utils)[config["dataset"] + "Config"].load(args.config)
    config.save()
    
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    generate_domain(config)
