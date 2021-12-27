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
    
    domain_name = ''.join(map(str.capitalize, DOMAIN_ALIAS[domain_name].split('_')))
    domain_name += split.capitalize()
    if domain_version in ["v3", "v5"]:
        assert (bagslots is not None)
        domain_name += f"N{bagslots}"
    domain_name += f"K{complexity}"
    domain_name += f"TrSc{train_scenes}TrSa{samples_per_train_scene}TeSa{samples_per_test_scene}"
    domain_name += f"Seed{seed}"
    return domain_name


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
