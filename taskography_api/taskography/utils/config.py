import os
import os.path as osp
import yaml
import pprint
import copy
import flatten_dict

from .constants import DOMAIN_ALIAS, DOMAIN_BAGSLOTS
from .utils import REQUIRED_BASE_KEYS, config_to_domain_name, domain_to_pddlgym_name


class Config(object):
    def __init__(self):
        self.parsed = False
        self.config = dict()

    def update(self, d):
        self.config.update(d)

    def save(self, path):
        if os.path.isdir(path):
            path = os.path.join(path, "config.yaml")
        with open(path, "w") as f:
            yaml.dump(self.config, f)

    @classmethod
    def load(cls, path):
        if os.path.isdir(path):
            path = os.path.join(path, "config.yaml")
        with open(path, "r") as f:
            data = yaml.load(f, Loader=yaml.Loader)
        config = cls()
        config.update(data)
        return config

    @staticmethod
    def _flatten_helper(flattened_config, value, prefix, separator="."):
        if isinstance(value, dict) and all([isinstance(k, str) for k in value.keys()]):
            # We have another nested configuration dictionary
            for k in value.keys():
                Config._flatten_helper(
                    flattened_config,
                    value[k],
                    prefix + separator + k,
                    separator=separator,
                )
        else:
            # We do not have a config file, just return the regular value.
            flattened_config[
                prefix[1:]
            ] = value  # Note that we remove the first prefix because it has a leading '.'

    def flatten(self, separator="."):
        """Returns a flattened version of the config where '.' separates nested values"""
        flattened_config = {}
        Config._flatten_helper(flattened_config, self.config, "", separator=separator)
        return flattened_config

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __contains__(self, key):
        return self.config.__contains__(key)

    def __str__(self):
        return pprint.pformat(self.config, indent=4)

    def copy(self):
        config = type(self)()
        config.config = copy.deepcopy(self.config)
        return config


class PDDLGymDatasetConfig(Config):
    def __init__(self):
        super().__init__()
        # Sampler Args
        self.config["sampler"] = None
        self.config["sampler_kwargs"] = {}

        # Dataset Args
        self.config["dataset"] = None
        self.config["dataset_kwargs"] = {}

        # Seed
        self.config["seed"] = None

    @classmethod
    def load(cls, path):
        config = super().load(path)
        # Absolute paths
        config.expand_vars(config.config)
        return config

    def save(self, dir="datasets/configs"):
        if not osp.exists(dir):
            os.makedirs(dir)
        super().save(osp.join(dir, self.domain_name + ".yaml"))

    @property
    def domain_name_kwargs(self):
        """Required kwargs for generating domain name string."""
        flat_config = flatten_dict.flatten(self.config, reducer=lambda *x: x[-1])

        # Domain type
        domain_type = osp.splitext(osp.basename(flat_config["domain_filepath"]))[0]
        if "taskography" in domain_type:
            domain_type = DOMAIN_ALIAS[domain_type]

        # Check bagslots None for Rearrangement domains
        bagslots = flat_config["bagslots"]
        assert (DOMAIN_BAGSLOTS[domain_type] and bagslots is not None) or (
            not DOMAIN_BAGSLOTS[domain_type] and bagslots is None
        ), "Incorrectly specified bagslots."

        # Remaining keys
        kwargs = {
            "domain_type": domain_type,
            "bagslots": 0 if bagslots is None else bagslots,
        }
        for k in REQUIRED_BASE_KEYS:
            if k in ["domain_type", "bagslots"]:
                continue
            kwargs[k] = flat_config[k]

        return kwargs

    @property
    def domain_name(self):
        return config_to_domain_name(**self.domain_name_kwargs)

    @property
    def pddlgym_name(self):
        return domain_to_pddlgym_name(self.domain_name)

    @staticmethod
    def expand_vars(config):
        """Recurse config dictionary and expand all environment variables."""
        if isinstance(config, dict) and all([isinstance(k, str) for k in config.keys()]):
            for key, value in config.items():
                if isinstance(value, dict):
                    PDDLGymDatasetConfig.expand_vars(value)
                elif isinstance(value, str):
                    print("Checking value:", value)
                    if any(["$" in v for v in value.split("/")]):
                        print("Modifying it with expand_vars")
                        config[key] = osp.expandvars(value)
            return
        raise ValueError("Config must be a dictionary with string keys")
