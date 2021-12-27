import os
import time
import random
import numpy as np

from pddlgym.parser import (PDDLDomainParser, PDDLProblemParser)
from pddlgym.structs import LiteralConjunction
from ..task_sampler_base import TaskSamplerBase
from taskography_api.taskography.utils.constants import (OBJECTS, RECEPTACLES)


class TaskSamplerV4(TaskSamplerBase):

    def __init__(self, domain, scenegraph, task_length=1):
        """PDDL problem sampler for the Lifted Rearrangement(k) task. Corresponding domain specification: domains/taskographyv4.pddl.
        """
        super(TaskSamplerV4, self).__init__(scenegraph)

        # PDDLGym domain
        assert(os.path.basename(domain) == "taskographyv4.pddl")
        self.domain = PDDLDomainParser(domain, expect_action_preds=False, operators_as_actions=True)
        self.task_length = task_length

        # PDDL entities and name-to-entity mapping
        self.pddl_entity_set = set()
        self.pddl_entity_map = dict()
        self.generate_pddl_entities()

        # PDDL predicates
        self.pddl_predicate_set = set()
        self.generate_pddl_predicates()

        # history of sampled tasks
        self.sampled_tasks = set()

    def reset_history(self):
        self.sampled_tasks = set()

    def generate_pddl_entities(self):
        """Generate a dictionary of PDDL entities as per the domains/taskographyv4.pddl domain. The dictionary maps 
        entity names to their corresponding PDDLGym object.
        """
        # Item / Entity Types
        agent_type = self.domain.types['agent']
        room_type = self.domain.types['room']
        place_type = self.domain.types['place']
        receptacle_type = self.domain.types['receptacle']
        rclass_type = self.domain.types['rclass']
        item_type = self.domain.types['item']
        iclass_type = self.domain.types['iclass']
        location_type = self.domain.types['location']

        # Agent
        agent = agent_type("robot")
        self.pddl_entity_set.add(agent)
        self.pddl_entity_map["robot"] = agent

        # Rooms
        for room_id, room_name in self.room_names.items():
            room = room_type(room_name)
            self.pddl_entity_set.add(room)
            self.pddl_entity_map[room_name] = room

        # Places
        for place_id, place_name in self.place_names.items():
            place = place_type(place_name)
            self.pddl_entity_set.add(place)
            self.pddl_entity_map[place_name] = place

        # Receptacles
        for r_id, receptacle_name in self.receptacle_names.items():
            receptacle = receptacle_type(receptacle_name)
            self.pddl_entity_set.add(receptacle)
            self.pddl_entity_map[receptacle_name] = receptacle
        
        # Receptacle Classes
        for r_class in RECEPTACLES:
            r_class = r_class.replace(' ', '')
            rclass = rclass_type(r_class)
            self.pddl_entity_set.add(rclass)
            self.pddl_entity_map[r_class] = rclass

        # Items
        for o_id, object_name in self.object_names.items():
            object = item_type(object_name)
            self.pddl_entity_set.add(object)
            self.pddl_entity_map[object_name] = object

        # Item Classes
        for i_class in OBJECTS:
            i_class = i_class.replace(' ', '')
            iclass = iclass_type(i_class)
            self.pddl_entity_set.add(iclass)
            self.pddl_entity_map[i_class] = iclass

        # Locations (objects, receptacles and places)
        for location_name in self.location_names['unique']:
            location = location_type(location_name)
            self.pddl_entity_set.add(location)
            self.pddl_entity_map[location_name] = location                    

    def generate_pddl_predicates(self):
        """Generate set of task agnostic predicates.
        """
        # PDDL Entity / Object Map
        emap = self.pddl_entity_map

        # Predicate Types
        place_in_room = self.domain.predicates['placeinroom']
        room_place = self.domain.predicates['roomplace']
        location_in_place = self.domain.predicates['locationinplace']
        place_location = self.domain.predicates['placelocation']
        rooms_connected = self.domain.predicates['roomsconnected']
        receptacle_at_location = self.domain.predicates['receptacleatlocation']
        item_at_location = self.domain.predicates['itematlocation']
        in_receptacle = self.domain.predicates['inreceptacle']
        in_any_receptacle = self.domain.predicates['inanyreceptacle']
        receptacle_opening_type = self.domain.predicates['receptacleopeningtype']
        receptacle_class = self.domain.predicates['receptacleclass']
        item_class = self.domain.predicates['itemclass']
        class_relation = self.domain.predicates['classrelation']

        # placeInRoom, roomPlace, placeLocation, locationInPlace, roomsConnected
        for room_id in self.room_to_place_map:
            room_name = self.room_names[room_id]
            place_id = self.room_to_place_map[room_id]['root']
            place_name = self.place_names[place_id]
            location_name = self.location_names['places'][place_id]
            self.pddl_predicate_set.add(place_location(emap[location_name], emap[place_name]))
            self.pddl_predicate_set.add(location_in_place(emap[location_name], emap[place_name]))
            self.pddl_predicate_set.add(room_place(emap[place_name], emap[room_name]))
            self.pddl_predicate_set.add(place_in_room(emap[place_name], emap[room_name]))
            for place_id in self.room_to_place_map[room_id]['places']:
                place_name = self.place_names[place_id]
                self.pddl_predicate_set.add(place_in_room(emap[place_name], emap[room_name]))
            for connected_room_id in self.sg.room[room_id].connected_rooms:
                connected_room_name = self.room_names[connected_room_id]
                self.pddl_predicate_set.add(rooms_connected(emap[room_name], emap[connected_room_name]))

        # locationInPlace, placeLocation
        for place_id in self.place_to_entity_map:
            place_name = self.place_names[place_id]
            location_name = self.location_names['places'][place_id]
            self.pddl_predicate_set.add(place_location(emap[location_name], emap[place_name]))
            self.pddl_predicate_set.add(location_in_place(emap[location_name], emap[place_name]))
            for e_id in self.place_to_entity_map[place_id]['objects']:
                location_name = self.location_names[e_id]
                self.pddl_predicate_set.add(location_in_place(emap[location_name], emap[place_name]))

        # receptacleAtLocation, receptacleClass
        for r_id in self.receptacles['all']:
            str_rec_name = self.receptacle_names[r_id]
            str_rec_loc_name = self.location_names[r_id]
            str_rec_class = self.sg.object[r_id].class_.replace(' ', '')
            self.pddl_predicate_set.add(receptacle_at_location(emap[str_rec_name], emap[str_rec_loc_name]))
            self.pddl_predicate_set.add(receptacle_class(emap[str_rec_name], emap[str_rec_class]))

        # itemAtLocation, itemClass
        for o_id in self.objects['all']:
            str_obj_name = self.object_names[o_id]
            str_obj_loc_name = self.location_names[o_id]            
            str_obj_class = self.sg.object[o_id].class_.replace(' ', '')
            self.pddl_predicate_set.add(item_at_location(emap[str_obj_name], emap[str_obj_loc_name]))
            self.pddl_predicate_set.add(item_class(emap[str_obj_name], emap[str_obj_class]))

        # inReceptacle, inAnyReceptacle, and receptacleOpeningType
        for r_id in self.receptacle_to_object_map:
            str_rec_name = self.receptacle_names[r_id]
            for o_id in self.receptacle_to_object_map[r_id]:
                str_obj_name = self.object_names[o_id]
                self.pddl_predicate_set.add(in_receptacle(emap[str_obj_name], emap[str_rec_name]))
                self.pddl_predicate_set.add(in_any_receptacle(emap[str_obj_name]))
            if r_id in self.receptacles['opening_type']:
                self.pddl_predicate_set.add(receptacle_opening_type(emap[str_rec_name]))

        # classRelation
        for (str_obj_class, str_rec_class) in self.lifted_class_relations:
            self.pddl_predicate_set.add(class_relation(emap[str_obj_class], emap[str_rec_class]))

    def sample_pick_and_place(self, avoid_repeats=True, task_length=1):
        """Sample a pick and place task. Task length refers to the number of pick and place sub-tasks
        in the rearrangement problem. If no verifiable task is sampled in 5 seconds, None is returned.
        """       
        task = dict()
        valid = False
        start_time = time.time()

        # agent start room
        room_names_list = list(self.room_names.keys())
        agent_room_id = random.choice(room_names_list)
        agent_room = self.room_names[agent_room_id]
        place_id = self.room_to_place_map[agent_room_id]['root']
        agent_place = self.place_names[place_id]
        agent_location = self.location_names['places'][place_id]
        task['agent_room'] = agent_room
        task['agent_place'] = agent_place
        task['agent_location'] = agent_location

        # sample valid item / receptacle class relations
        lifted_class_array = self.lifted_class_matrix.copy().reshape(-1)
        indices = np.arange(len(lifted_class_array))
        mask = lifted_class_array > 0
        lifted_class_array = lifted_class_array[mask]
        weights = lifted_class_array / lifted_class_array.sum()
        indices = indices[mask]
        while not valid:
            # sample indices
            samples = np.random.choice(indices, task_length, replace=False, p=weights)
            o_indices, r_indices = np.unravel_index(samples, shape=self.lifted_class_matrix.shape)
            # translate indices to class categories
            object_classes = list()
            receptacle_classes = list()
            for o_idx, r_idx in zip(o_indices, r_indices):
                object_classes.append(self.objects['class_index_inv'][o_idx])
                receptacle_classes.append(self.receptacles['class_index_inv'][r_idx])
            
            task['object_classes'] = object_classes
            task['receptacle_classes'] = receptacle_classes
            valid = self.verify_task(task, avoid_repeats=avoid_repeats)
            if time.time() - start_time > 5 and not valid:
                return None
        
        return task

    def verify_task(self, task, avoid_repeats=True):
        """Verify if a sampled pick and place task has not been observed.
        """
        # sorted task parameters
        task_params = sorted(zip(task['object_classes'], task['receptacle_classes']), key=lambda x: x[0])
        task_str = "{}".format(task_params)
        valid = task_str not in self.sampled_tasks
        self.sampled_tasks.add(task_str)
        return valid if avoid_repeats else True

    def generate_pddl_problem(self, problem_filepath, problem_name, task_length=None, domain_name=None):
        """Append predicates for a sampled problem, and generate a goal.
        """
        if task_length is None:
            task_length = self.task_length
        task = self.sample_pick_and_place(task_length=task_length)

        if domain_name is None:
            domain_name = self.domain.domain_name

        if task is not None:
            emap = self.pddl_entity_map
            pddl_predicates = self.pddl_predicate_set.copy()

            # Predicate Types
            in_room = self.domain.predicates['inroom']
            in_place = self.domain.predicates['inplace']
            at_location = self.domain.predicates['atlocation']
            class_relation = self.domain.predicates['classrelation']

            # init | agent: inRoom, inPlace, atLocation
            pddl_predicates.add(in_room(emap['robot'], emap[task['agent_room']]))
            pddl_predicates.add(in_place(emap['robot'], emap[task['agent_place']]))
            pddl_predicates.add(at_location(emap['robot'], emap[task['agent_location']]))

            # goal | pick object, place receptacle: classRelation
            goals = []
            for str_obj_class, str_rec_class in zip(task['object_classes'], task['receptacle_classes']):
                goals.append(class_relation(emap[str_obj_class], emap[str_rec_class]))      
            goals = goals[:task_length]          
            pddl_goal = LiteralConjunction(goals)

            PDDLProblemParser.create_pddl_file(
                problem_filepath,
                objects=self.pddl_entity_set,
                initial_state=pddl_predicates,
                problem_name=problem_name,
                domain_name=domain_name,
                goal=pddl_goal,
                fast_downward_order=True
            )
            return True

        return False
