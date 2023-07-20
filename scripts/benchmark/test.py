import os
# from ...third_party.pddlgym_planners.pddlgym_planners import _SATISFICING, _OPTIMAL
from third_party.pddlgym_planners.pddlgym_planners import _SATISFICING, _OPTIMAL

# print('_SATISFICING: ',_SATISFICING)
# print('_OPTIMAL: ',_OPTIMAL)
# print('_SATISFICING.keys(): ',list(_SATISFICING.keys()))
# print('_OPTIMAL.keys(): ',list(_OPTIMAL.keys()))

planners = list(_SATISFICING.keys()) + list(_OPTIMAL.keys())
print('planners: ', planners)

pddl_domain = 'taskographyv2tiny1'

for planner in planners:
    print('running planner: ', planner)
    os.system('python scripts/benchmark/plan.py --domain-name {} --planner {} --expid {}'.format(pddl_domain, planner, planner))