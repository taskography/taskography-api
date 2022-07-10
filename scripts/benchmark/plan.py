import os
import json
import random
import pprint
import numpy as np
import argparse
from tqdm import tqdm

import pddlgym
from pddlgym_planners import PlannerHandler
from pddlgym_planners.pddl_planner import PDDLPlanner
from pddlgym_planners.planner import PlanningFailure, PlanningTimeout
from taskography_api.taskography.utils.utils import save_json


_STATS = ["num_node_expansions", "plan_length", "search_time", "total_time"]


def generate_dataset_statistics(args, planner: PDDLPlanner, split: str) -> None:
    """Run PDDLPlanner on specified PDDLGym environment and save statistics.
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

    run_stats = []
    timeouts = 0
    failures = 0
    for i in tqdm(range(m)):
        env.fix_problem_index(i)
        state, _ = env.reset()
        problem_fname = env.problems[i].problem_fname
        try:
            plan = planner.plan_to_action_from_pddl(
                env.domain, state, domain_fname, problem_fname, timeout=args.timeout
            )
            run_stats.append(planner.get_statistics().copy())
        except PlanningTimeout:
            timeouts += 1
        except PlanningFailure:
            failures += 1

    # Log statistics
    statsfile = os.path.join(args.save_dir, f"{args.expid}_{split}.py")
    json_string = json.dumps(run_stats, indent=4, sort_keys=True)
    json_string = "STATS = " + json_string + "\n"
    timeout_string = f"num_timeouts = {timeouts}\n"
    failure_string = f"num_failures = {failures}\n"
    num_problems_string = f"num_problems = {m}\n"
    with open(statsfile, "w") as f:
        f.write(json_string)
        f.write(timeout_string)
        f.write(failure_string)
        f.write(num_problems_string)

    # Compute statistics
    planner_stats = {}
    for stat in _STATS:
        if stat not in planner_stats:
            planner_stats[stat] = np.zeros(len(run_stats))
        for i, run in enumerate(run_stats):
            planner_stats[stat][i] = run[stat]
    for stat in _STATS:
        stat_mean = float(planner_stats[stat].mean().item())
        stat_std = float(planner_stats[stat].std().item())
        planner_stats[stat] = stat_mean
        planner_stats[stat + "_std"] = stat_std
    planner_stats["success_rate"] = float(len(run_stats) / m)
    planner_stats["timeout_rate"] = float(timeouts / m)
    planner_stats["failure_rate"] = float(failures / m)

    # Save statistics
    pprinter = pprint.PrettyPrinter()
    pprinter.pprint(planner_stats)
    save_json(
        os.path.join(args.save_dir, args.expid + f"_{split}" + ".json"), planner_stats
    )


def planning_demo(args, planner: PDDLPlanner) -> None:
    """Run PDDLPlanner on a randomly sampled task.
    """
    # Instantiate PDDLGym environment
    env = pddlgym.make("PDDLEnv{}-v0".format(args.domain_name.capitalize()))
    i = random.choice(list(range(len(env.problems))))
    env.fix_problem_index(i)
    state, _ = env.reset()
    domain_fname = env.domain.domain_fname
    problem_fname = env.problems[i].problem_fname

    # Planning demo
    print(f"Attempting {args.domain_name} problem {i}")
    try:
        plan = planner.plan_to_action_from_pddl(
            env.domain, state, domain_fname, problem_fname, timeout=args.timeout
        )
        for j, action in enumerate(plan):
            print(f"Action {j}: {action}")
        print("Statistics")
        pprinter = pprint.PrettyPrinter()
        pprinter.pprint(planner.get_statistics())
    except PlanningTimeout as timeout:
        print(timeout)
    except PlanningFailure as failure:
        print(failure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-dir",
        type=str,
        default="exp",
        help="Directory to log all experiment results",
    )
    parser.add_argument(
        "--expid",
        type=str,
        default="debug",
        help="Unique ID for experiment (dir within log-dir in which to write logfiles to)",
    )
    parser.add_argument(
        "--planner", type=str, required=True, help="Planner to benchmark"
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        required=True,
        help="Name of domain registered in PDDLGym",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout constraint for the planners",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of problems for debugging",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Demo a planner on a single problem, no statistics are tracked",
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Run only on test splits, skipping train splits",
    )
    args = parser.parse_args()

    args.save_dir = os.path.join(args.log_dir, args.expid)
    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)

    planner = PlannerHandler()[(args.planner)]
    if args.demo:
        planning_demo(args, planner)
    else:
        if not args.skip_train:
            generate_dataset_statistics(args, planner, "train")
        generate_dataset_statistics(args, planner, "test")
