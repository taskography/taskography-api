import os
from third_party.pddlgym_planners.pddlgym_planners import _SATISFICING, _OPTIMAL

planners = list(_SATISFICING.keys()) + list(_OPTIMAL.keys())
print('planners: ', planners) # ['FF', 'FF-X', 'FD-lama-first', 'Cerberus-seq-sat', 'Cerberus-seq-agl', 'DecStar-agl-decoupled', 'lapkt-bfws', 'FD-seq-opt-lmcut', 'Delfi', 'DecStar-opt-decoupled']

pddl_domain = 'taskographyv2tiny1'

for planner in planners:
    print('running planner: ', planner)
    os.system('python scripts/benchmark/plan.py --domain-name {} --planner {} --expid {}_{}'.format(pddl_domain, planner, pddl_domain, planner))