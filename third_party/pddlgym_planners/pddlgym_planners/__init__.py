import inspect
from pprint import PrettyPrinter
pprinter = PrettyPrinter(indent=4)

from .pddl_planner import PDDLPlanner
from .ff import FF
from .ffx import FFX
from .fd import FD
from .cerberus import Cerberus
from .decstar import DecStar
from .delfi import Delfi
from .lapkt import LAPKTBFWS
from .satplan import SATPlan
# from lifted import Lifted # not yet open-sourced


_PLANNERS = {}
for k, v in list(globals().items()):
    if inspect.isclass(v) and issubclass(v, PDDLPlanner) and not v == PDDLPlanner:
        _PLANNERS[k] = v
print("Call get_planner(name, **kwargs) with supported planners below and known kwargs")
pprinter.pprint(_PLANNERS)


def get_planner(name, **kwargs):
    """Initialize and return the specified planner with kwargs.
    args:
        name: <str> planner name
        kwargs: <dict> arguments to the planner constructor
    returns:
        planner: <PDDLPlanner> planner
    """
    try:
        planner = _PLANNERS[name]
    except:
        raise ValueError("[get_planner] Planner with name {} is not supported".format(name))
    
    try: 
        planner = planner(**kwargs)
    except:
        print(
            "[get_planner] Ensure that **kwargs corresponds to the {} constructor \
                argument spec:".format(name)
        )
        print(inspect.getfullargspec(planner.__init__))

    return planner


_SATISFICING = {
    "FF": {
        "planner": FF,
        "planner_kwargs": {}
    },
    "FF-X": {
        "planner": FFX,
        "planner_kwargs": {}
    },
    "FD-lama-first": {
        "planner": FD,
        "planner_kwargs": {"alias_flag": "--alias lama-first"}
    },
    "Cerberus-seq-sat": {
        "planner": Cerberus,
        "planner_kwargs": {"alias": "seq-sat-cerberus2018"}
    },
    "Cerberus-seq-agl": {
        "planner": Cerberus,
        "planner_kwargs": {"alias": "seq-agl-cerberus2018"}
    },
    "DecStar-agl-decoupled": {
        "planner": DecStar,
        "planner_kwargs": {"alias": "agl-decoupled-fallback"}
    },
    "lapkt-bfws": {
        "planner": LAPKTBFWS,
        "planner_kwargs": {}
    },
    # "lifted": {
    #     "planner": Lifted,
    #     "planner_kwargs": {}
    # }
}

_OPTIMAL = {
    "FD-seq-opt-lmcut": {
        "planner": FD,
        "planner_kwargs": {"alias_flag": "--alias seq-opt-lmcut"}
    },
    # "SatPlan": {
    #     "planner": SATPlan,
    #     "planner_kwargs": {}
    # },
    "Delfi": {
        "planner": Delfi,
        "planner_kwargs": {}
    },
    "DecStar-opt-decoupled": {
        "planner": DecStar,
        "planner_kwargs": {"alias": "opt-decoupled-fallback"}
    }
}

class PlannerHandler(dict):

    def __init__(self):        
        """Simplifies access to supported planners.
        """
        for k, v in _SATISFICING.items():
            data = v.copy()
            data["planner_type"] = "satisficing"
            super().__setitem__(k, data)

        for k, v in _OPTIMAL.items():
            data = v.copy()
            data["planner_type"] = "optimal"
            super().__setitem__(k, data)

    def __getitem__(self, k):
        """Get planner by name.
        """
        try:
            print("[PlannerHandler] Fetching planner {}".format(k))
            v = super().__getitem__(k)
        except:
            raise KeyError("[PlannerHandler] Planner {} is not supported".format(k))
        return v["planner"](**v["planner_kwargs"])

    def get_planners_of_type(self, type):
        """Return a list of planners of the specified type.
        args:
            type: <str> Planner type: "satisficing" or "optimal"
        returns:
            planners: <list<tuple<str, PDDLPlanner>> List of PDDLPlanners and their str names

        """
        assert type in ["satisficing", "optimal"]
        planners = [(k, self.__getitem__(k)) for k, v in self.items() if v["planner_type"] == type]
        return planners
