from typing import Dict, Tuple, Union

import sys
import numpy as np

from pddlgym_planners.adl2strips import ADL2Strips


def compute_ground_problem_size(domain_filepath: str, problem_filepath: str) -> Dict[str, int]:
    """Compute number of ground action and predicates in a PDDL domain."""
    with ADL2Strips(domain_filepath, problem_filepath) as (dfp, _):
        with open(dfp, "r") as f:
            grounded_dom = f.read()

        sections = grounded_dom.split("(:")
        predicates = 0
        actions = 0
        for section in grounded_dom.split("(:"):
            if section.startswith("predicates"):
                predicates = len(section.split("\n")) - 1
            elif section.startswith("action"):
                actions += 1

    return dict(num_actions=actions, num_facts=predicates)


def get_sastask_from_pddl(domain_filepath: str, problem_filepath: str) -> Tuple:
    """Return SAS task from PDDL."""
    # Temporarily add translate to path
    sys.path.append("third_party/pddlgym_planners/FD/src/translate/")
    import normalize
    import pddl_parser
    import translate

    pddl_task = pddl_parser.open(domain_filename=domain_filepath, task_filename=problem_filepath)
    sas_task = translate.pddl_to_sas(pddl_task, max_num_actions=float("inf"), pg_generator=None)
    sys.path.pop(-1)
    return sas_task, pddl_task


def estimate_branches(
    sas_task, pddl_task, num_rollouts: int = 10, horizon: int = 100
) -> Dict[str, Union[int, float]]:
    """Estimate the mean, minimum and maximum branch factor of the PDDL domain
    with Monte-Carlo rollouts.
    """
    # Data structure to keep operators grouped by at location
    index = None
    for var_index, value_names in enumerate(sas_task.variables.value_names):
        name = "atlocation"
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
            operators_by_location.setdefault("None", []).append(operator)

    # Monte carlo simulation
    rollout_stats = []
    for i in range(num_rollouts):
        state = sas_task.init.values.copy()
        for s in range(horizon):
            all_applicable = []
            for operator in operators_by_location.get(state[index], []) + operators_by_location.get(
                "None", []
            ):
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
        min_branching_factor=int(np.min(rollout_stats)),
    )


def count_operators(sas_task) -> Dict[str, int]:
    """Return the number of SAS operators and variables."""
    return dict(
        num_sas_operators=len(sas_task.operators),
        num_sas_variables=len(sas_task.variables.value_names),
    )
