import os.path as osp


REQUIRED_BASE_KEYS = [
    "domain_type",
    "split",
    "bagslots",
    "complexity",
    "train_scenes",
    "samples_per_train_scene",
    "samples_per_test_scene",
    "seed"
]


_KEY_MAP = {
    "domain_type": "",
    "split": "split",
    "bagslots": "n",
    "complexity": "k",
    "train_scenes": "trsc",
    "samples_per_train_scene": "trsa",
    "samples_per_test_scene": "tesa",
    "seed": "seed"
}


_KEY_MAP_INV = {v: k for k, v in _KEY_MAP.items()}


def room_to_str_name(room_inst):
    return f"room{int(room_inst.id)}_{room_inst.scene_category.replace(' ', '_')}"


def place_to_str_name(place_id, inst, is_object=False, is_room=False):
    assert (not (is_object and is_room))
    if is_room:
        return f"place{int(place_id)}_door_room{int(inst.id)}_{inst.scene_category.replace(' ', '_')}"
    elif is_object:
        return f"place{int(place_id)}_item{int(inst.id)}_{inst.class_.replace(' ', '_')}"
    return f"place{int(place_id)}_receptacle{int(inst.id)}_{inst.class_.replace(' ', '_')}"


def receptacle_to_str_name(rec_inst):
    return f"receptacle{int(rec_inst.id)}_{rec_inst.class_.replace(' ', '_')}"


def object_to_str_name(obj_inst, size):
    return f"item{int(obj_inst.id)}_{obj_inst.class_.replace(' ', '_')}_{size}"


def location_to_str_name(room_data, place_id):
    (cx, cy), room_id, floor_num = room_data
    cx = f"neg{-cx}" if cx < 0 else f"pos{cx}"
    cy = f"neg{-cy}" if cy < 0 else f"pos{cy}"
    return f"location_X{cx}_Y{cy}_place{place_id}_room{int(room_id)}_floor{floor_num}"


def write_domain_file(pddlgym_domain, domain_filepath, domain_name=None):
    """Write out PDDL domain file while scanning for and removing the 
    untyped equality (= ?v0 ?v1) written by PDDLGymDomainParser.

    args:
        pddlgym_domain: PDDLGymDomainParser object
        domain_filepath: path to write PDDL domain file
        domain_name: relabel the domain with this name (default: None)
    """
    if domain_name is not None: pddlgym_domain.domain_name = domain_name
    pddlgym_domain.write(domain_filepath)
    
    with open(domain_filepath, "rt") as fh:
        lines = fh.readlines()
        lines = [l for l in lines if l.strip("\n").strip() != "(= ?v0 ?v1)"]
    with open(domain_filepath, "wt") as fh:    
        fh.writelines(lines)


def register_pddlgym_domain(problem_dir, domain_name):
    """Add new domain to the list of environments to be registered by PDDLGym.
    
    args:
        problem_dir: path to pddlgym/pddlgym/pddl directory
        domain_name: name of the domain
    """
    register_filepath = osp.realpath(osp.join(osp.dirname(problem_dir), "__init__.py"))
    with open(register_filepath, "rt") as fh:
        lines = fh.readlines()
    
    idx = -1
    for i, line in enumerate(lines):
        if line.strip("\n").strip() == "]:":
            idx = i
            break
    assert idx != -1, "Could not find appropriate location to insert domain declaration"
    decl_str = '\t\t(\n'
    decl_str += f'\t\t\t"{domain_name}",\n'
    decl_str += '\t\t\t{\n'
    decl_str += '\t\t\t\t"operators_as_actions": True,\n'
    decl_str += '\t\t\t\t"dynamic_action_space": True\n'
    decl_str += '\t\t\t}\n'
    decl_str += '\t\t)\n'
    lines.insert(idx, decl_str)
    
    # extend list
    prev = lines[idx-1].strip("\n")
    assert prev[-1] in [",", ")"]
    if prev[-1] != ",":
        prev += ","
    prev += "\n"
    lines[idx-1] = prev
    
    with open(register_filepath, "wt") as fh:
        fh.writelines(lines)


def config_to_domain_name(**kwargs):
    """A convention for naming domains and obtaining their respective PDDLGym registry
    from a set of input keyword arguments.
    """
    # Ensure base keys provided
    for k in REQUIRED_BASE_KEYS:
        assert k in kwargs, f"Missing keyword argument {k} required to name the domain."
    
    # Construct name
    domain_name = kwargs["domain_type"]
    for k in REQUIRED_BASE_KEYS[1:]:
        k, v = _KEY_MAP[k], kwargs[k]
        if k == "n" and v == None: v = 0
        domain_name += f"_{k}_{v}"
    
    return domain_name.lower()


def domain_to_pddlgym_name(domain_name, test=False):
    """Domain name as registered by PDDLGym.
    """
    pddlgym_name = domain_name.capitalize()
    if test: pddlgym_name += "Test"
    return f"PDDLEnv{pddlgym_name}-v0"


def domain_name_to_config(domain_name):
    """Base config from the provided domain name.
    """
    params = domain_name.lower().split("_")
    split_idx = params.index("split")
    
    # Domain type and split
    config = dict()
    config["domain_type"] = "_".join([p for p in params[:split_idx]])
    config["split"] = params[split_idx + 1]
    
    # Remaining keys
    prev_key = None
    for p in params[split_idx + 2:]:
        if p in _KEY_MAP_INV: prev_key = _KEY_MAP_INV[p]
        else: config[prev_key] = int(p)

    assert all(k in config for k in REQUIRED_BASE_KEYS)
    return config


def scene_graph_name(scene_graph_filepath):
    return scene_graph_filepath.split('.')[0].split('_')[-1].lower()


def sampler_name(scene_graph_filepath, complexity, bagslots=None):
    sampler_name = scene_graph_name(scene_graph_filepath)
    bagslots = 0 if bagslots is None else bagslots
    sampler_name += f"_n{bagslots}_k{complexity}"
    return sampler_name
