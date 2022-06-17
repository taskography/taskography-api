import os
import sys
import tempfile
import shutil
import numpy as np

from .mcts.problem import PddlProblem
from .mcts.algorithm import Root, plan_mcts
from .mcts.helpers import branching_factor


class FilesInCommonTempDirectory:

    def __init__(self, *file_paths):
        """Temporary directory for storing related temporary files.
        Typically used to store ADL and corresponding STRIPS translations.
        """
        self.file_paths = file_paths
        self.create_temp_dir()
    
    def cleanup(self):
        if self.tmpdir is not None:
            self.tmpdir.cleanup()
    
    def create_temp_dir(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dirname = self.tmpdir.name
        new_fpaths = []
        for fpath in self.file_paths:
            new_fpath = os.path.join(self.dirname, os.path.basename(fpath))
            shutil.copyfile(fpath, new_fpath)
            new_fpaths.append(new_fpath)
        self.new_fpaths = new_fpaths
    
    def __enter__(self):
        return self.new_fpaths
    
    def __exit__(self, type, value, traceback):
        self.cleanup()


def compute_ground_problem_size(domfile, probfile):
    from adl2strips import ADL2Strips
    with ADL2Strips(domfile, probfile) as (domfile, _):
        with open(domfile, 'r') as f:
            grounded_dom = f.read()
        sections = grounded_dom.split('(:')
        predicates = 0
        actions = 0
        for section in grounded_dom.split('(:'):
            if section.startswith('predicates'):
                predicates = len(section.split('\n')) - 1
            elif section.startswith('action'):
                actions += 1
    return dict(num_actions=actions, num_facts=predicates)


def estimate_branching_factor(domain_file, problem_file):
    problem = PddlProblem(domain_file, problem_file, reward_subgoals=False, action_costs=False, oversample_relevant_actions=False)
    root = Root(problem, problem.init)
    plan_mcts(root, n_iters=1000, horizon=0)
    return branching_factor(root, agg=np.mean)


def get_sastask_from_pddl(domain, task):
    # Hacky workaround to importing FD translation methods
    sys.path.append("pddlgym_planners/FD/src/translate/")
    import normalize
    import pddl_parser
    import translate
    pddl_task = pddl_parser.open(
        domain_filename=domain, task_filename=task)
    sas_task = translate.pddl_to_sas(pddl_task, max_num_actions=float("inf"), pg_generator=None)
    # Bring path back to normal
    sys.path.pop(-1)
    return sas_task, pddl_task


def count_branches_v2(sas_task, pddl_task):
    '''This is very domain specific. It basically counts the actions the agent can take at all locations.
    It ignores how the action space changes if the agent does anything other than move.'''
    indexes = dict(atlocation=None, inroom=None, inplace=None)
    for var_index, value_names in enumerate(sas_task.variables.value_names):
        for name in indexes:
            if any(f" {name}" in v for v in value_names):
                assert indexes[name] is None, f"Unexpected: More than one sas variable for pddl {name}"
                indexes[name] = var_index

    location_name_to_place_name = {
        v.args[0]: v.args[1] for v in pddl_task.init if v.predicate == 'locationinplace'
    }
    place_name_to_room_name = {
        v.args[0]: v.args[1] for v in pddl_task.init if v.predicate == 'placeinroom'
    }

    location_name_to_index = {}
    for location_index, atlocation_value in enumerate(sas_task.variables.value_names[indexes['atlocation']]):
        location_name = atlocation_value.split(', ')[-1].strip(')')
        location_name_to_index[location_name] = location_index
    place_name_to_index = {}
    for place_index, inplace_value in enumerate(sas_task.variables.value_names[indexes['inplace']]):
        place_name = inplace_value.split(', ')[-1].strip(')')
        place_name_to_index[place_name] = place_index
    room_name_to_index = {}
    for room_index, inroom_value in enumerate(sas_task.variables.value_names[indexes['inroom']]):
        room_name = inroom_value.split(', ')[-1].strip(')')
        room_name_to_index[room_name] = room_index

    location_index_to_place_index = {location_name_to_index[location_name]: place_name_to_index[place_name] for location_name, place_name in location_name_to_place_name.items()}
    place_index_to_room_index = {place_name_to_index[place_name]: room_name_to_index[room_name] for place_name, room_name in place_name_to_room_name.items()}

    def sample_state():
        for location_idx in location_index_to_place_index:
            place_idx = location_index_to_place_index[location_idx]
            room_idx = place_index_to_room_index[place_idx]
            
            state = sas_task.init.values.copy()
            state[indexes['atlocation']] = location_idx
            state[indexes['inplace']] = place_idx
            state[indexes['inroom']] = room_idx
            yield state


    num_branches = [] # will have the same length as the number of locations in the problem
    for state in sample_state():
        num_applicable = 0
        for operator in sas_task.operators:
            applicable = True
            for (var, assignment) in operator.get_applicability_conditions():
                if state[var] != assignment:
                    applicable = False
                    break
            if applicable:
                num_applicable += 1
        num_branches.append(num_applicable)

    return dict(
        mean_branching_factor=float(np.mean(num_branches)),
        max_branching_factor=int(np.max(num_branches)),
        min_branching_factor=int(np.min(num_branches))
    )


def estimate_branches_v3(sas_task, pddl_task, num_rollouts=10, horizon=100):
    ### Data structure to keep operators grouped by atlocation
    index = None
    for var_index, value_names in enumerate(sas_task.variables.value_names):
        name = 'atlocation'
        if any(f" {name}" in v for v in value_names):
            assert index is None, f"Unexpected: More than one sas variable for pddl {name}"
            index = var_index
    operators_by_location = {}
    for operator in sas_task.operators:
        for var, assignment in operator.get_applicability_conditions():
            if var == index:
                operators_by_location.setdefault(assignment, []).append(operator)
                break
        else:
            operators_by_location.setdefault('None', []).append(operator)
    ### Monte carlo sim
    rollout_stats = []
    for i in range(num_rollouts):
        num_actions_possible = []
        state = sas_task.init.values.copy()
        for s in range(horizon):
            all_applicable = []
            for operator in operators_by_location.get(state[index], []) + operators_by_location.get('None', []):
                applicable = True
                for (var, assignment) in operator.get_applicability_conditions():
                    if state[var] != assignment:
                        applicable = False
                        break
                if applicable:
                    all_applicable.append(operator)

            rollout_stats.append(len(all_applicable))
            operator = np.random.choice(all_applicable)
            for (var, _, eff, _) in operator.pre_post:
                state[var] = eff

    return dict(
        mean_branching_factor=float(np.mean(rollout_stats)),
        max_branching_factor=int(np.max(rollout_stats)),
        min_branching_factor=int(np.min(rollout_stats))
    )


def count_operators(sas_task):
    return dict(num_sas_operators=len(sas_task.operators), num_sas_variables=len(sas_task.variables.value_names))
