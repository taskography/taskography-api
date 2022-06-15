import random

from pddlgym.structs import LiteralConjunction
from ..problem_sampler_base import ProblemSamplerBase


class TaskSamplerV1(ProblemSamplerBase):

    def __init__(self, domain_filepath, scene_graph_filepath, complexity=1, bagslots=None):
        """PDDL problem sampler for the non-hierarchical Rearrangement(k) task. 
        Corresponding domain specification: domains/taskographyv1.pddl.
        """
        super().__init__(domain_filepath, scene_graph_filepath, complexity=complexity, bagslots=bagslots)
        assert bagslots is None, "Flat Rearrangement(k) domains does not use bagslots."
        self._sorted_item_ids = sorted(list(self.objects["all"]))
        self._sorted_receptacle_ids = sorted(list(self.receptacles["all"]))
        self._sorted_location_ids = sorted(list(set(self.location_names.keys()) - {'unique', 'places'}))

    def create_entities(self):
        # Item / Entity Types
        agent_type = self.domain.types['agent']
        receptacle_type = self.domain.types['receptacle']
        item_type = self.domain.types['item']
        location_type = self.domain.types['location']

        # Agent
        agent = agent_type("robot")
        self.entities.add(agent)
        self.entities_map["robot"] = agent

        # Receptacles
        for r_id, receptacle_name in self.receptacle_names.items():
            receptacle = receptacle_type(receptacle_name)
            self.entities.add(receptacle)
            self.entities_map[receptacle_name] = receptacle

        # Items
        for o_id, object_name in self.object_names.items():
            object = item_type(object_name)
            self.entities.add(object)
            self.entities_map[object_name] = object

        # Locations (objects, receptacles and places)
        for location_name in self.location_names['unique']:
            location = location_type(location_name)
            self.entities.add(location)
            self.entities_map[location_name] = location
    
    def create_predicates(self):
        # PDDL Entity / Object Map
        emap = self.entities_map

        # Predicate Types
        receptacle_at_location = self.domain.predicates['receptacleatlocation']
        item_at_location = self.domain.predicates['itematlocation']
        in_receptacle = self.domain.predicates['inreceptacle']
        in_any_receptacle = self.domain.predicates['inanyreceptacle']
        receptacle_opening_type = self.domain.predicates['receptacleopeningtype']

        # receptacleAtLocation 
        for r_id in self.receptacles['all']:
            str_rec_name = self.receptacle_names[r_id]
            str_rec_loc_name = self.location_names[r_id]
            self.predicates.add(receptacle_at_location(emap[str_rec_name], emap[str_rec_loc_name]))

        # itemAtLocation
        for o_id in self.objects['all']:
            str_obj_name = self.object_names[o_id]
            str_obj_loc_name = self.location_names[o_id]            
            self.predicates.add(item_at_location(emap[str_obj_name], emap[str_obj_loc_name]))

        # inReceptacle, inAnyReceptacle, and receptacleOpeningType
        for r_id in self.receptacle_to_object_map:
            str_rec_name = self.receptacle_names[r_id]
            for o_id in self.receptacle_to_object_map[r_id]:
                str_obj_name = self.object_names[o_id]
                self.predicates.add(in_receptacle(emap[str_obj_name], emap[str_rec_name]))
                self.predicates.add(in_any_receptacle(emap[str_obj_name]))
            if r_id in self.receptacles['opening_type']:
                self.predicates.add(receptacle_opening_type(emap[str_rec_name]))

    def sample_task_repr(self):
        valid = False
        while not valid:
            i_ids = random.sample(self._sorted_item_ids, k=self.complexity)
            r_ids = random.sample(self._sorted_receptacle_ids, k=self.complexity)
            valid_goal = all([i_id not in self.receptacle_to_object_map[r_id] \
                for i_id, r_id in zip(i_ids, r_ids)])
            valid = valid or valid_goal
        ir_ids = sorted(list(zip(i_ids, r_ids)))

        task_repr = {
            "a_lid": random.sample(self._sorted_location_ids, k=1)[0],
            "i_ids": [id[0] for id in ir_ids],
            "r_ids": [id[1] for id in ir_ids]
        }
        return task_repr

    def sample(self, k=1, repeat=False):
        emap = self.entities_map

        # Predicate Types
        at_location = self.domain.predicates['atlocation']
        in_receptacle = self.domain.predicates['inreceptacle']

        tasks = []
        for task in ProblemSamplerBase.sample(self, k=k, repeat=repeat):
            predicates = self.predicates.copy()

            # init | agent: atLocation
            predicates.add(at_location(emap["robot"], emap[self.location_names[task["a_lid"]]]))
            
            # goal | pick object, place receptacle: inReceptacle
            goals = []
            for i_id, r_id in zip(task["i_ids"], task["r_ids"]):
                goals.append(in_receptacle(
                    emap[self.object_names[i_id]], 
                    emap[self.receptacle_names[r_id]]
                ))
            goals = LiteralConjunction(goals)

            task = {
                "objects": self.entities.copy(),
                "initial_state": predicates,
                "goal": goals
            }
            tasks.append(task)

        return tasks

    def valid(self):
        return super().valid() and self.num_objects >= self.complexity
