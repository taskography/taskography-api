# Planner Interface for [PDDLGym](https://github.com/tomsilver/pddlgym)

**This library is under development by [Tom Silver](http://web.mit.edu/tslvr/www/) and [Rohan Chitnis](https://rohanchitnis.com/). Correspondence: <tslvr@mit.edu> and <ronuchit@mit.edu>.**

This is a lightweight Python interface for using off-the-shelf classical planners like [FastForward](https://fai.cs.uni-saarland.de/hoffmann/ff.html) and [FastDownward](http://www.fast-downward.org/ObtainingAndRunningFastDownward) with [PDDLGym](https://github.com/tomsilver/pddlgym).

**Extensions to this library have been made by [Mohamed Khodeir](https://github.com/Khodeir) and [Christopher Agia](https://agiachris.github.io/) to support a broader range of satisficing and optimal symbolic planners encapsulated in a pip-installable package. Correspondance: <m.khodeir@mail.utoronto.ca> and <cagia@stanford.edu>.**

## System Requirements

This repository has been mostly tested on MacOS Mojave and Catalina with Python 3.6. We would like to make it accessible on more systems; please let us know if you try another and run into any issues.

## Installation

1. If on MacOS, `brew install coreutils`.
2. Install docker.
3. Clone this repository. `git clone https://github.com/agiachris/pddlgym_planners.git && cd pddlgym_planners`.
4. (option a) Create a virtual env, e.g., with conda: `conda env create -f environment.yaml`.
5. (option b) Install [PDDLGym](https://github.com/tomsilver/pddlgym) and `pip install pddlgym_planners/tarski`.
5. Install this repository; `pip install .`.

## Example Usage

**Important Note:** When you invoke a planner for the first time, the respective external package will be installed automatically. This will take up to a few minutes. This step will be skipped the next time you run the same planner.

```python
import pddlgym
from pddlgym_planners.ff import FF  # FastForward
from pddlgym_planners.fd import FD  # FastDownward

# Planning with FastForward
ff_planner = FF()
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", ff_planner(env.domain, state))
print("Statistics:", ff_planner.get_statistics())

# Planning with FastDownward (--alias seq-opt-lmcut)
fd_planner = FD()
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", fd_planner(env.domain, state))
print("Statistics:", fd_planner.get_statistics())

# Planning with FastDownward (--alias lama-first)
lama_first_planner = FD(alias_flag="--alias lama-first")
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", lama_first_planner(env.domain, state))
print("Statistics:", lama_first_planner.get_statistics())
```

## Extended Usage

Upon importing this package in your python script, you'll have easy access to both satisficing and optimal planners through the `pddlgym_planners.PlannerHandler` object; a dictionary hashing a planner name to its corresponding [PDDLPlanner](https://github.com/agiachris/pddlgym_planners/blob/master/pddlgym_planners/pddl_planner.py#L17) object. You may also directly import a planner with `get_planner` should you know its name and alias. All necessary dependencies are auto-installed for planners being used the first time. 


```python 
# pyexample.py script

import pddlgym
import pddlgym_planners

# Instantiate planner handler (dict)
planners = pddlgym_planners.PlannerHandler()
print(planners.keys())      # [optional] check for short-form planner names (keys)

# Planning with Cerberus-agl (satisficing)
cerberus_planner = planners["Cerberus-seq-agl"]
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", cerberus_planner(env.domain, state))
print("Statistics:", cerberus_planner.get_statistics())

# Planning with Delfi (optimal)
delfi_planner = planners["Delfi"]
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", delfi_planner(env.domain, state))
print("Statistics:", delfi_planner.get_statistics())

# Can also directly access planners with get_planner
planner_data = {
    "name": "FD", 
    "kwargs": {"alias_flag": "--alias seq-opt-lmcut"}
}
fd_planner = pddlgym_planners.get_planner(planner_data["name"], **planner_data["kwargs"])
env = pddlgym.make("PDDLEnvBlocks-v0")
state, _ = env.reset()
print("Plan:", fd_planner(env.domain, state))
print("Statistics:", fd_planner.get_statistics())
```

Please refer to [`pddlgym_planners/__init__.py`](https://github.com/agiachris/pddlgym_planners/blob/master/pddlgym_planners/__init__.py) for the names of possible planners to choose from. Additional samples are provided in [`test.py`](https://github.com/agiachris/pddlgym_planners/blob/master/test.py).
