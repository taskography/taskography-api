import numpy as np


UnvisitedUCB = 1e100 # TODO: revisit
class Node:

    parent = None
    value_sum = 0.
    times_visited = 0

    def __init__(self, parent, action):
        self.parent = parent
        self.action = action
        self.children = set()
        self.problem = parent.problem

        self.state, self.immediate_reward, self.is_done = self.problem.step(parent.state, action)
        self.action_generator = self.problem.action_generator(self.state)

    def is_leaf(self):
        return len(self.children) == 0

    def is_root(self):
        return self.parent is None

    def get_mean_value(self):
        return self.value_sum / self.times_visited if self.times_visited != 0 else 0

    def ucb_score(self, scale=10):
        if self.times_visited == 0:
            return UnvisitedUCB

        U = np.sqrt(2*np.log(self.parent.times_visited) / self.times_visited)
        return self.get_mean_value() + scale*U

    def best_child(self, by='ucb', return_score=False):
        children = list(self.children)
        if by == 'ucb':
            scores = [c.ucb_score() for c in children]
        elif by == 'value':
            scores = [c.get_mean_value() for c in children]
        else:
            raise ValueError

        best_child_index = np.argmax(scores)
        best_child_score = scores[best_child_index]
        best_child = children[best_child_index]
        if return_score:
            return best_child, best_child_score
        return best_child

    def select_leaf(self):
        if self.is_leaf():
            return self
        best_child = self.best_child('ucb')
        return best_child.select_leaf()

    def expand(self, previously_visited_set):
        if self.is_done:
            return self
        for action in self.action_generator:
            child = Node(self, action)
            child_hash = hash(child.state)
            if previously_visited_set is None or (not child_hash in previously_visited_set):
                previously_visited_set.add(child_hash)
                self.children.add(child)


        return self.select_leaf()

    def rollout(self, horizon):
        is_done = self.is_done
        if is_done:
            return 0
        state = self.state
        total_reward = 0
        for i in range(horizon):
          if is_done:
            break
          action = self.problem.sample_random_action(state)
          state, reward, is_done = self.problem.step(state, action)
          total_reward += reward
        return total_reward

    def propagate(self, child_value):
        # compute node value
        value = self.immediate_reward + child_value

        # update value_sum and times_visited
        self.value_sum += value
        self.times_visited += 1

        # propagate upwards
        if not self.is_root():
            self.parent.propagate(value)


class Root(Node):
    def __init__(self, problem, state):
        self.action = None
        self.parent = None
        self.children = set()
        self.immediate_reward = 0
        self.problem = problem
        self.state = state
        self.is_done = problem.is_goal(self.state)
        self.action_generator = problem.action_generator(self.state)


def plan_mcts(root, n_iters=10, horizon=20, use_visited_set=True):
    """
    builds tree with monte-carlo tree search for n_iters iterations
    :param root: tree node to plan from
    :param n_iters: how many select-expand-simulate-propagate loops to make
    """
    if use_visited_set:
        root.previously_visited_set = set()
    else:
        root.previously_visited_set = None

    for _ in range(n_iters):
        node = root.select_leaf()
        child = node.expand(root.previously_visited_set)
        mcreward = child.rollout(horizon)
        child.propagate(mcreward)
        if child.is_done:
            print('Found goal')
            return child


