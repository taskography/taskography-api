# taskography-api
A simple API for sampling symbolic planning tasks in large-scale 3D scene graphs.

![Taskography-API System Diagram](figures/taskography-api-system.png)

---


## Overview
This repository corresponds to Taskography-API as described in *Taskography: Evaluating robot task planning over large 3D scene graphs*, presented at CoRL2021: [project page](https://taskography.github.io/), [paper link](https://www.chrisagia.com/papers/Taskography-CoRL-2021.pdf). 
We provide support for the following:

- **Hierarchical-Symbolic Graph Construction.** 
The raw [Gibson](https://3dscenegraph.stanford.edu/database.html) scene graph data is [loaded](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/utils/loader.py#L8) from its `.npz` file format encoding before [heuristically](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/task_sampler_base.py) determining the scene's inter- and intra-layer connectivity structure.
- **Task Sampling.** [Problem samplers](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/samplers/domains) for auto-generating [PDDLGym](https://github.com/tomsilver/pddlgym) domains of increasing complexity: `Rearrangement(k)`, `Courier(n,k)`, `Lifted Rearrangement(k)`, `Lifted Courier(n,k)`, as described in our paper. Task samplers are modifiable to the degree literal goal conjuctions (k) and stow capacity (n).
- **Trajectory Sampling.** Scripts for generating state-action trajectory datasets atop PDDLGym environments with your choice of [PDDL planner](https://github.com/agiachris/pddlgym_planners); for purposes of training neurosymbolic learning-to-plan algorithms.
- **Environment Wrappers.** 
Gym [environment wrappers](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/envs) enabling symbolic interaction with 3D scene graphs - in support of training online decision making algorithms and reinforcement learning methods. 

We refer to the [Instructions](#instructions) section for details on the basic and extended usage of our framework.


## Setup

### System Requirements
This repository has been primarily tested on Ubuntu 16.04, 18.04 and macOS Monterey with Python 3.6. 

### Installation 
One of our package dependencies requires Docker - please follow [these steps](https://docs.docker.com/engine/install/) to install it. 
We also recommend creating a virtual environment, e.g. with [venv](https://docs.python.org/3/library/venv.html) or [anaconda3](https://anaconda.org/) before proceeding with the following installation steps. 

```bash
# if on macOS
brew install coreutils

git clone https://github.com/taskography/taskography-api.git --recurse-submodules
cd ./taskography_api && pip install .
pip install -r requirements.txt
```

### Data Download
Please follow the [download instructions](https://github.com/StanfordVL/3DSceneGraph) for the [Gibson 3D Scene Graph database](https://docs.google.com/forms/d/e/1FAIpQLScnlTFPUYtBqlN8rgj_1J3zJm44bIhmIx8gDhOqiJyTwja8vw/viewform?usp=sf_link). 
The testing of our repository is limited to the *tiny* (388 Mb) and *medium* (389.5 Mb) data splits.


## Instructions
Taskography-API is designed to enable fast prototyping of 3D scene graph symbolic planning domains.
We partition the functionality into three main categories: [samplers](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/samplers), [datasets](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/datasets) and [envs](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/envs), which we describe in detail below. 

### Task Samplers
Task samplers allow the user to generate an arbitrary number of [PDDL](https://planning.wiki/ref/pddl/domain) planning problems to any one 3D scene graph instance. 
The [example samplers](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/samplers/domains) are written on a per-domain basis; i.e., each [sampler](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/__init__.py) has a corresponding hand-defined PDDL [domain file](https://github.com/taskography/taskography-api/tree/main/domains) that specifies the object types, predicate relations, the action set, and the symbolic transition model of the desired task category. 

| Task Category                  | Task Sampler  | PDDL Domain File   |
| ------------------------------ | ------------- | ------------------ |
| `Rearrangement(k)`             | [TaskSamplerV2](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/taskographyv2.py) | [taskographyv2.pddl](https://github.com/taskography/taskography-api/blob/main/domains/taskographyv2.pddl) |
| `Courier(n,k)`                 | [TaskSamplerV3](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/taskographyv3.py)| [taskographyv3.pddl](https://github.com/taskography/taskography-api/blob/main/domains/taskographyv3.pddl) |
| `Lifted Rearrangement(k)`      | [TaskSamplerV4](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/taskographyv4.py) | [taskographyv4.pddl](https://github.com/taskography/taskography-api/blob/main/domains/taskographyv4.pddl) |
| `Lifted Courier(n,k)`          | [TaskSamplerV5](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/taskographyv5.py) | [taskographyv5.pddl](https://github.com/taskography/taskography-api/blob/main/domains/taskographyv5.pddl) |

All task samplers must subclass [ProblemSamplerBase](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/problem_sampler_base.py): an abstract base class defining several must-implement methods that interface heavily with PDDLGym's [domain parser](https://github.com/tomsilver/pddlgym/blob/master/pddlgym/parser.py#L433) to create object-oriented references to scene graph entities and relations before the [problem parser](https://github.com/tomsilver/pddlgym/blob/master/pddlgym/parser.py#L622) writes them out as PDDL problem files. 
Furthermore, [ProblemSamplerBase](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/problem_sampler_base.py) itself inherets from [TaskSamplerBase](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/task_sampler_base.py), which is responsible for constructing the hierarchical, spatial, and symbolic relationships between nodes in the [loaded](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/utils/loader.py) 3D scene graph.


#### Custom Samplers
We encourage developers to follow the below procedure should they require custom samplers for new task categories:
1. Manually write an associated PDDL domain file and include it in the [domains](https://github.com/taskography/taskography-api/tree/main/domains) directory;
2. If the domain file follows the `domains/taskographyv<i>.pddl` format, optionally provide a [domain name alias](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/utils/constants.py#L2) to be used when auto-generating PDDLGym domains and problem files - described in the next section;
3. Write a sampler in `taskography_api/taskography/samplers/domains` subclassing `ProblemSamplerBase` and made accessible by adding it to the [`../domains/__init__.py`](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/domains/__init__.py) and [`../samplers/__init__.py`](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/__init__.py) modules;


### Dataset Generation
Particularly useful downstream use-cases of our task samplers is to generate PDDLGym domains and expert demonstrations atop from classical planners. 

#### PDDLGym Domains
The [PDDLGymDataset](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/datasets/pddlgym_dataset.py) class gives users the ability to auto-generate PDDLGym environments constituting train and test problems across an entire data split of 3D scene graphs, e.g., Gibson *tiny* or *medium*.
The guiding parameters for this process should be specified in a `.yaml` configuration file - we provide [examples](https://github.com/taskography/taskography-api/tree/main/configs/generate/problems) for each of our task categories.
With this complete, creating a novel PDDLGym environment is as simple running:

```bash
python scripts/generate_domain.py --config <path/to/problem_config.yaml>
```

Note: our instructions installs PDDLGym at `third_party/pddlgym` as an editable package to allow for incorporating new environments without rebuilding. 
When called, `PDDLGymDataset` dynamically modifies the [`pddlgym/pddlgym/__init__.py`](https://github.com/tomsilver/pddlgym/blob/master/pddlgym/__init__.py) so that the generated environment is registered upon next import.
If you did not follow our installation instructions, you may need to modify the configuration's `problem_dir` parameter to reflect your PDDLGym package location.

Aside: if parameter `save_samplers` is set true, the task samplers will be saved in pickle file format to the default location of `datasets/samplers/<domain_type>/<sampler_name>`, so as to circumvent the 3D scene graph pre-processing when generating future environments.

#### Trajectory Datasets
We additionally offer a [TrajectoryGymDataset](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/datasets/trajectory_dataset.py) class that loads a newly generated PDDLGym environment, iterates through all train (and optionally test) problems, and saves the state-action trajectories of problems solved by a specified classical planner. 
Please refer to our fork of [pddlgym_planners](https://github.com/agiachris/pddlgym_planners/blob/073c7c65072c72d6239194c919f87b3be7d1b765/pddlgym_planners/__init__.py) for a comprehensive list of supported planners, which are installed the first time they queried. 

The trajectories are by default saved to `datasets/trajectories/<domain_name>` in pickle file format. 
We provide an example of [configuration file](https://github.com/taskography/taskography-api/blob/main/configs/generate/trajectories.yaml) to complement the following launch command:

```bash
python scripts/generate_trajectories.py --config <path/to/trajectory_config.yaml>
```


### Taskography Gym Environments 
The support the training of futuristic learning-to-plan algorithms, we provide a [Taskography gym](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/envs/taskography.py) class that can be utilized as per the familiar gym API. 
Instiating this environment requires specifying the task category and Gibson split, along with a few other parameters - please see our [example](https://github.com/taskography/taskography-api/blob/main/configs/env.yaml).

```bash
python scripts/validate/taskography_env.py --config <path/to/env_config.yaml>
```

A scene graph and task are sampled at uniform random with each `env.reset()` call. 
For efficiency, there's the option to pre-compute `episodes_per_scene` tasks per sampled 3D scene graph, i.e., episodes are conducted in a new scene every `episodes_per_scene` tasks.


## Citation
Taskography-API has an MIT [License](https://github.com/taskography/taskography-api/blob/main/LICENSE). If you find this package helpful, please consider citing our work:

```
@inproceedings{agia2022taskography,
  title={Taskography: Evaluating robot task planning over large 3D scene graphs},
  author={Agia, Christopher and Jatavallabhula, Krishna Murthy and Khodeir, Mohamed and Miksik, Ondrej and Vineet, Vibhav and Mukadam, Mustafa and Paull, Liam and Shkurti, Florian},
  booktitle={Conference on Robot Learning},
  pages={46--58},
  year={2022},
  organization={PMLR}
}
```


## References
We would like to credit the developers of several very useful packages.

- "PDDLGym: Gym Environments from PDDL Problems," Tom Silver, Rohan Chitnis, [link](https://github.com/tomsilver/pddlgym) to repository.
- "PDDLGym Planners: Lightweight Python interface for using off-the-shelf classical planners," Tom Silver, Rohan Chitnis, [link](https://github.com/ronuchit/pddlgym_planners) to repository.