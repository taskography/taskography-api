# taskography-api
A simple, multi-functional API for sampling symbolic planning tasks in large-scale 3D scene graphs.

![Taskography-API System Diagram](figures/taskography-api-system.png)

---

## General
This repository corresponds to Taskography-API as described in *Taskography: Evaluating robot task planning over large 3D scene graphs*, presented at CoRL2021 ([project page](https://taskography.github.io/), [paper link](https://www.chrisagia.com/papers/Taskography-CoRL-2021.pdf)). 


The code supports the following operations pertinent to task planning in 3D scene graphs:

- **Symbolic-Hierarchical Graph Construction.** 
The raw scene graph data is [loaded](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/utils/loader.py#L8) from its `.npz` file format encoding. We [heuristically determine](https://github.com/taskography/taskography-api/blob/main/taskography_api/taskography/samplers/task_sampler_base.py) the inter-layer support and intra-layer connectity structure of the scene before sampling tasks atop.
- **PDDL Task Sampling.** We offer [PDDL task samplers](https://github.com/taskography/taskography-api/tree/main/taskography_api/taskography/samplers/domains) for planning domains of increasing complexity as introduced in our paper: `Rearrangement(k)`, `Courier(n,k)`, `Lifted Rearrangement(k)`, `Lifted Courier(n,k)`. Each indvidual task sampler is modifiable to the degree literal goal conjuctions (k), and for Courier domains, stow capacity (n).


## Setup
Add setup steps.

### Requirements
This is the easy part.

## Instructions 

### Usage
Add simple usage examples.

### Tips
Add tips for extended usage.


## References
Add references to third_party dependencies. 

[1] Add
[2] Add

