import os
import tqdm
import argparse

import pddlgym
from taskography_api.taskography.utils.utils import save_json
from taskography_api.taskography.utils.domain_utils import (
    compute_ground_problem_size,
    get_sastask_from_pddl,
    estimate_branches,
    count_operators,
)


def generate_dataset_statistics(args, split: str) -> None:
    """Generate PDDLGym environment statistics.
    """
    # Instantiate PDDLGym environment
    registered_name = args.domain_name.capitalize()
    if split == "test":
        registered_name += "Test"
    env = pddlgym.make("PDDLEnv{}-v0".format(registered_name))
    domain_fname = env.domain.domain_fname
    m = len(env.problems)
    if args.limit is not None:
        m = min(args.limit, len(env.problems))

    run_stats = {}
    for i in tqdm(range(m)):
        stats = {}
        problem_fname = env.problems[i].problem_fname

        sas_task, pddl_task = get_sastask_from_pddl(domain_fname, problem_fname)
        stats.update(compute_ground_problem_size(domain_fname, problem_fname))
        stats.update(estimate_branches(sas_task, pddl_task))
        stats.update(count_operators(sas_task))
        run_stats[problem_fname] = stats

    save_json(
        os.path.join(args.exp_dir, args.exp_name + f"_{split}" + ".json"), run_stats
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp-dir",
        type=str,
        default="./exp",
        help="Directory to store experimental results",
    )
    parser.add_argument(
        "--exp-name",
        type=str,
        required=True,
        help="Subdirectory to write aggregated planner statistics",
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        required=True,
        help="Name of domain registered in PDDLGym",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of problems for debugging",
    )
    args = parser.parse_args()

    if not os.path.exists(args.exp_dir):
        os.makedirs(args.exp_dir)

    generate_dataset_statistics(args, "train")
    generate_dataset_statistics(args, "test")
