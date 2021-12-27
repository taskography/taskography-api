import os
import os.path as osp

from .constants import DOMAIN_ALIAS


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


def convert_domain_name(
        domain_name, 
        split, 
        complexity, 
        bagslots,
        train_scenes,
        samples_per_train_scene, 
        samples_per_test_scene,
        seed
    ):

    domain_version = domain_name.replace("taskography", "")
    assert (domain_version in ["v1", "v2", "v4"] and bagslots is None \
        or domain_version in ["v3", "v5"] and bagslots is not None)
    
    # domain config
    domain_name = DOMAIN_ALIAS[domain_name]
    domain_name += f"_{split}"
    # sampler config
    if domain_version in ["v3", "v5"]:
        assert (bagslots is not None)
        domain_name += f"_n{bagslots}"
    domain_name += f"_k{complexity}"
    # dataset config
    domain_name += f"_trsc{train_scenes}"
    domain_name += f"_trsa{samples_per_train_scene}"
    domain_name += f"_tesa{samples_per_test_scene}"
    domain_name += f"_seed{seed}"

    names = {
        "domain_name": domain_name,
        "gym_name": domain_name.capitalize(),
        "gym_name_test": domain_name.capitalize() + "Test"
    }
    return names


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
    assert idx != -1, "Could not find appropriate location to insert domain declaration"
    decl_str = '\t\t(\n'
    decl_str += f'\t\t\t"{domain_name}",\n'
    decl_str += '\t\t\t{{\n'
    decl_str += '\t\t\t\t"operators_as_actions": False,\n'
    decl_str += '\t\t\t\t"dynamic_action_space": True\n'
    decl_str += '\t\t\t}}\n'
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
