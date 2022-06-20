import argparse
import yaml
import gym
import random

from taskography_api.taskography import envs


def load_from_class(config):
    env = vars(envs)[config["env"]](**config["env_kwargs"])
    env.reset()
    return env


def load_from_registry(config):
    env = gym.make("{}Env-v0".format(config["env"]), **config["env_kwargs"])
    env.reset()
    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to environment config")
    args = parser.parse_args()

    with open(args.config, "r") as fh:
        config = yaml.safe_load(fh)
    random.seed(config["seed"])

    load_from_class(config)
    load_from_registry(config)
