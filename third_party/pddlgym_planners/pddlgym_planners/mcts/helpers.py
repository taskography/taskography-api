def branching_factor(node, agg=max, d=0):
    if node.is_leaf():
        return None
    r = [len(node.children)]
    for c in node.children:
        b = branching_factor(c, agg=agg, d=d+1)
        if b is not None:
            r.extend(b)
    if d > 0:
        return r
    else:
        return agg(r)


def tree_size(node):
    return 1 + sum([tree_size(c) for c in node.children])


def tree_depth(node, agg=max):
    if node.is_leaf():
        return 1
    return 1 + agg([tree_depth(c, agg=agg) for c in node.children])


def get_goal_dfs(node):
    if node.is_done:
        return node
    if node.is_leaf():
        return None
    for c in node.children:
        goal = get_goal_dfs(c)
        if goal is not None:
            return goal
    return None

def get_path(leaf):
    node = leaf
    path = []
    while not node.is_root():
        path = [node.action] + path
        node = node.parent
    return path
