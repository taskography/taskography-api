import random

from pddlgym.structs import LiteralConjunction
from ..problem_sampler_base import ProblemSamplerBase
from .taskographyv1 import TaskSamplerV1


class TaskSamplerV2(TaskSamplerV1):

    def __init__(self, domain_filepath, scene_graph_filepath, complexity=1, bagslots=None):
        """PDDL problem sampler for the Rearrangement(k) task. 
        Corresponding domain specification: domains/taskographyv2.pddl.
        """
        assert bagslots is None, "Rearrangement(k) domains does not use bagslots."
        super().__init__(domain_filepath, scene_graph_filepath, complexity=complexity, bagslots=bagslots)
        self._sorted_room_ids = sorted(list(self.room_names.keys()))

    def create_entities(self):
        super().create_entities()

        # Item / Entity Types
        room_type = self.domain.types['room']
        place_type = self.domain.types['place']

        # Rooms
        for room_id, room_name in self.room_names.items():
            room = room_type(room_name)
            self.entities.add(room)
            self.entities_map[room_name] = room

        # Places
        for place_id, place_name in self.place_names.items():
            place = place_type(place_name)
            self.entities.add(place)
            self.entities_map[place_name] = place
    
    def create_predicates(self):
        super().create_predicates()

        # PDDL Entity / Object Map
        emap = self.entities_map

        # Predicate Types
        place_in_room = self.domain.predicates['placeinroom']
        room_place = self.domain.predicates['roomplace']
        location_in_place = self.domain.predicates['locationinplace']
        place_location = self.domain.predicates['placelocation']
        rooms_connected = self.domain.predicates['roomsconnected']
        
        # placeInRoom, roomPlace, placeLocation, locationInPlace, roomsConnected
        for room_id in self.room_to_place_map:
            room_name = self.room_names[room_id]
            place_id = self.room_to_place_map[room_id]['root']
            place_name = self.place_names[place_id]
            location_name = self.location_names['places'][place_id]
            self.predicates.add(place_location(emap[location_name], emap[place_name]))
            self.predicates.add(location_in_place(emap[location_name], emap[place_name]))
            self.predicates.add(room_place(emap[place_name], emap[room_name]))
            self.predicates.add(place_in_room(emap[place_name], emap[room_name]))
            for place_id in self.room_to_place_map[room_id]['places']:
                place_name = self.place_names[place_id]
                self.predicates.add(place_in_room(emap[place_name], emap[room_name]))
            for connected_room_id in self.sg.room[room_id].connected_rooms:
                connected_room_name = self.room_names[connected_room_id]
                self.predicates.add(rooms_connected(emap[room_name], emap[connected_room_name]))

        # locationInPlace, placeLocation
        for place_id in self.place_to_entity_map:
            place_name = self.place_names[place_id]
            location_name = self.location_names['places'][place_id]
            self.predicates.add(place_location(emap[location_name], emap[place_name]))
            self.predicates.add(location_in_place(emap[location_name], emap[place_name]))
            for e_id in self.place_to_entity_map[place_id]['objects']:
                location_name = self.location_names[e_id]
                self.predicates.add(location_in_place(emap[location_name], emap[place_name]))   

    def sample_task_repr(self):
        valid = False
        while not valid:
            i_ids = random.sample(self._sorted_item_ids, k=self.complexity)
            r_ids = random.sample(self._sorted_receptacle_ids, k=self.complexity)
            valid_goal = all([i_id not in self.receptacle_to_object_map[r_id] \
                for i_id, r_id in zip(i_ids, r_ids)])
            valid = valid or valid_goal
        ir_ids = sorted(list(zip(i_ids, r_ids)))

        a_rid = random.sample(self._sorted_room_ids, k=1)[0]
        a_pid = self.room_to_place_map[a_rid]["root"]
        task_repr = {
            "a_rid": a_rid,
            "a_pid": a_pid,
            "i_ids": [id[0] for id in ir_ids],
            "r_ids": [id[1] for id in ir_ids]
        }
        return task_repr
        
    def sample(self, k=1, repeat=False):
        emap = self.entities_map

        # Predicate Types
        in_room = self.domain.predicates['inroom']
        in_place = self.domain.predicates['inplace']
        at_location = self.domain.predicates['atlocation']
        in_receptacle = self.domain.predicates['inreceptacle']

        tasks = []
        for task in ProblemSamplerBase.sample(self, k=k, repeat=repeat):
            predicates = self.predicates.copy()
            
            # init | agent: inRoom, inPlace, atLocation
            predicates.add(in_room(emap["robot"], emap[self.room_names[task["a_rid"]]]))
            predicates.add(in_place(emap["robot"], emap[self.place_names[task["a_pid"]]]))
            predicates.add(at_location(emap["robot"], emap[self.location_names["places"][task["a_pid"]]]))
            
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
        return super().valid()
