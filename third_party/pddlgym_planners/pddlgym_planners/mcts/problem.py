from copy import deepcopy
import numpy as np

from tarski.grounding import LPGroundingStrategy
from tarski.grounding.errors import ReachabilityLPUnsolvable
from tarski.grounding.ops import approximate_symbol_fluency
from tarski.syntax.transform.action_grounding import ground_schema,  ground_schema_into_plain_operator_from_grounding
from tarski.search.operations import is_applicable, progress
from tarski.evaluators.simple import evaluate
from tarski.model import wrap_tuple
from tarski.io import PDDLReader
from tarski.fstrips.manipulation.simplify import Simplify
from tarski.syntax import CompoundFormula, Connective, Atom


TESTING = False


class PddlProblem:
    __action_bindings = None
    __operators_by_fluent = None
    def __init__(self, domain_file, problem_file, reward_subgoals=True, action_costs=True, oversample_relevant_actions=True):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(domain_file)
        self.problem = reader.parse_instance(problem_file)
        simp = Simplify(self.problem)
        self.problem = simp.simplify(True, True)
        self.lang = self.problem.language
        self.init = self.problem.init
        self.set_goal(self.problem.goal)
        self.ground_action_sampler = self.ground_action_sampler_with_replacement()
        self.reward_subgoals = reward_subgoals
        self.action_costs = action_costs
        self.oversample_relevant_actions = oversample_relevant_actions
        print(f"Analyzed {len(self.operators_by_fluent)} actions")

    def step(self, state, action):
        new_state = self.next_state(state, action)
        is_done = self.is_goal(new_state)
        reward = 0
        if is_done:
            reward += 100
        elif self.reward_subgoals:
            reward += 100 * (self.prop_subgoals_completed(new_state) - self.prop_subgoals_completed(state))
        if self.action_costs:
            reward -= self.action_cost(action)
        return new_state, reward, is_done

    def action_cost(self, action):
        return 1

    def prop_subgoals_completed(self, state):
        reward = 0
        goal = self.problem.goal
        if isinstance(goal, CompoundFormula) and goal.connective is Connective.And:
            for f in goal.subformulas:
                if evaluate(f, state):
                    reward += 1 / len(goal.subformulas)
        return reward

    def is_goal(self, state):
        return evaluate(self.problem.goal, state)

    def next_state(self, state, action):
        return progress(state, action)

    def set_goal(self, goal, num_hops=1):
        self.problem.goal = goal
        if isinstance(goal, Atom):
            self.goal_terms = set([x.signature for x in goal.subterms])
        elif isinstance(goal, CompoundFormula):
            self.goal_terms = set([x.signature for y in goal.subformulas for x in y.subterms])
        else:
            raise NotImplementedError

        _, statics = approximate_symbol_fluency(self.problem)

        # add all the terms that appear in a predicate with a goal term
        for i in range(num_hops):
            extended_terms = set()
            for predicate in statics:
                for args in self.problem.init.predicate_extensions[predicate.signature]:
                    if any(a.expr.signature in self.goal_terms for a in args):
                        for a in args:
                            extended_terms.add(a.expr.signature)
            self.goal_terms = self.goal_terms.union(extended_terms)

    def sample_random_action(self, state):
        actions = list(self.action_generator(state))
        if self.oversample_relevant_actions:
            p = np.ones(len(actions))
            goal_terms = self.goal_terms
            for i in range(len(actions)):
                action = actions[i]
                overlap = goal_terms.intersection(set([o.signature for a in action.effects for o in a.atom.subterms]))
                p[i] += len(overlap)
            p = p / p.sum()
            i = np.random.choice(len(actions), p=p)
        else:
            i = np.random.choice(len(actions))

        return actions[i]

    def action_generator(self, state):
        all_ops = set()
        for action_name in self.operators_by_fluent:
            candidates = self.__all_ops.get(action_name, set())
            for fluent in self.operators_by_fluent[action_name]:
                fluent_candidates = set()
                sig = fluent.signature
                if sig in state.predicate_extensions:
                    for condition in self.operators_by_fluent[action_name][fluent]:
                        if (condition[0] is Connective.Not and condition[1:] not in state.predicate_extensions[sig]) \
                            or (condition[0] is not Connective.Not and condition in state.predicate_extensions[sig]):
                            fluent_candidates = fluent_candidates.union(self.operators_by_fluent[action_name][fluent][condition])
                else:
                    # e.g. the fluent is `holds ?o` and there is no held object in the state
                    # print('not in state', fluent, len(self.operators_by_fluent[action_name][fluent]))
                    for condition in self.operators_by_fluent[action_name][fluent]:
                        if condition[0] is Connective.Not:
                            fluent_candidates = fluent_candidates.union(self.operators_by_fluent[action_name][fluent][condition])
                candidates = fluent_candidates.intersection(candidates)
                if len(candidates) == 0:
                    break

            all_ops = all_ops.union(candidates)

        for op in all_ops:
            if TESTING:
                assert is_applicable(state, op), f"Expected {op} to be applicable - Something is going wrong."
            yield op

    @property
    def action_bindings(self):
        if self.__action_bindings is None:
            grounder = LPGroundingStrategy(self.problem)
            self.__action_bindings = {a:list(bindings) for a,bindings in grounder.ground_actions().items()}
        return self.__action_bindings

    @property
    def operators_by_fluent(self):
        if self.__operators_by_fluent is None:
            self.__all_ops = {}
            self.__operators_by_fluent = {}

            p = self.problem
            fluents, _ = approximate_symbol_fluency(p)

            for name, bindings in self.action_bindings.items():
                action = p.get_action(name)
                by_fluent = self.__operators_by_fluent.setdefault(name, {})
                for binding in bindings:
                    op = ground_schema_into_plain_operator_from_grounding(action, binding)
                    self.__all_ops.setdefault(name, set()).add(op)

                    for precond in op.precondition.subformulas:

                        if isinstance(precond, Atom) and precond.predicate in fluents:
                            by_fluent.setdefault(precond.predicate, {}).setdefault(wrap_tuple(precond.subterms), []).append(op)
                        elif isinstance(precond, CompoundFormula) and precond.connective is Connective.Not and len(precond.subformulas) == 1 and isinstance(precond.subformulas[0], Atom):
                            negated_precond = precond.subformulas[0]
                            by_fluent.setdefault(negated_precond.predicate, {}).setdefault( (Connective.Not, ) + wrap_tuple(negated_precond.subterms), []).append(op)
                        elif isinstance(precond, Atom) and not precond.predicate in fluents:
                            pass
                        else:
                            raise NotImplementedError(precond)

        return self.__operators_by_fluent
