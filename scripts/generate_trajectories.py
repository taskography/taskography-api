import argparse
import yaml

import taskography_api.taskography.datasets as datasets


def generate_trajectories(config):
    """Generate task plan demonstrations from planners on an existing PDDLGym
    environment or randomly sampled (unsaved) tasks. Demonstrations are stored as
    (list(states), list(actions)) tuples. 
    """
    dataset = vars(datasets)[config["dataset"]](**config["dataset_kwargs"])
    dataset.generate_from_env()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to YAML configuration file")
    args = parser.parse_args()
    
    # Load config
    with open(args.config, "r") as fh:
        config = yaml.safe_load(fh)    

    generate_trajectories(config)
