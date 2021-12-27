import numpy as np
import heapq

from taskography_api.taskography.utils.scenegraph import Building
from taskography_api.taskography.utils.constants import *
from ..utils.constants import *
from ..utils.utils import *


class TaskSamplerBase(object):

    def __init__(self, scene_graph):
        """TaskSamplerBase parses a 3D scene graph symbolically and spatially to 
        determine the hierarchical support relations between objects, receptacles, places, 
        rooms, and their locations. This information is useful when describing the initial
        state of a planning problem, as well as to sampling feasible goals.
        
        args:
            scene_graph: a 3D scene graph Building object
        """
        # parsed scene graph
        assert isinstance(scene_graph, Building)
        self.sg = scene_graph

        # scene capabilities
        self.valid_scene = True
        self.can_heat = False
        self.can_cool = False
        self.can_clean = False
        self.valid_lifted = True
        self.num_lifted_pairs = 0
        self.lifted_class_relations = set()
        self.lifted_class_matrix = None

        # rooms
        self.num_rooms = 0
        self.room_names = dict()
        self.room_to_place_map = dict()
        self.place_to_room_map = dict()
        # places
        self.num_places = 0
        self.place_names = dict()
        self.place_to_entity_map = dict()
        self.entity_to_place_map = dict()
        # receptacles
        self.num_receptacles = 0
        self.receptacles = dict()
        self.receptacle_names = dict()
        self.receptacle_to_object_map = dict()
        # objects
        self.num_objects = 0
        self.objects = dict()
        self.object_sizes = dict()
        self.object_names = dict()
        self.supported_objects = set()
        self.unsupported_objects = set()
        # locations
        self.locations = dict()
        self.location_names = dict()
        
        # categorize scene entities and get names
        self.get_scene_entities()
        # get hierarchical support relations: object-receptacle, object-room, receptacle-room
        self.get_support_relations()
        # 2d grid coordinates, room ids, and floor numbers for objects, receptacles and places
        self.get_locations()
        # build 2d matrix of lifted (class-specific) object-receptacle problem difficulty scores
        self.build_lifted_class_matrix()

    def get_scene_entities(self):
        """Categorize object and receptacle IDs by their class.
        """
        self.receptacles['all'] = set()
        self.receptacles['opening_type'] = set()
        self.receptacles['heating_type'] = set()
        self.receptacles['cooling_type'] = set()
        self.receptacles['cleaning_type'] = set()
        self.receptacles['class_count'] = dict()
        self.receptacles['class_index'] = dict()
        self.receptacles['class_index_inv'] = dict()
        self.objects['all'] = set()
        self.objects['heatable_type'] = set()
        self.objects['coolable_type'] = set()
        self.objects['cleanable_type'] = set()
        self.objects['class_count'] = dict()
        self.objects['class_index'] = dict()
        self.objects['class_index_inv'] = dict()

        for e_id in self.sg.object:
            scene_entity = self.sg.object[e_id]

            # consider only objects and receptacles with a parent room
            parent_room_id = scene_entity.parent_room
            if parent_room_id is not None:

                if parent_room_id not in self.room_names:
                    parent_room = self.sg.room[parent_room_id]
                    self.room_names[parent_room_id] = room_to_str_name(parent_room)
                    self.room_to_place_map[parent_room_id] = dict()
                    self.room_to_place_map[parent_room_id]['root'] = self.num_places
                    self.room_to_place_map[parent_room_id]['places'] = set()
                    self.place_to_room_map[self.num_places] = parent_room_id
                    self.place_names[self.num_places] = place_to_str_name(self.num_places, parent_room, is_room=True)
                    self.num_places += 1

                if scene_entity.class_ in RECEPTACLES:
                    self.receptacles['all'].add(e_id)
                    receptacle_class = scene_entity.class_.replace(' ', '')
                    self.receptacles['class_count'][receptacle_class] = self.receptacles['class_count'].get(receptacle_class, 0) + 1
                    self.receptacle_names[e_id] = receptacle_to_str_name(scene_entity)
                    self.receptacle_to_object_map[e_id] = set()
                    if scene_entity.class_ in OPENING_RECEPTACLES: self.receptacles['opening_type'].add(e_id)
                    if scene_entity.class_ in HEATING_RECEPTACLES: self.receptacles['heating_type'].add(e_id)
                    if scene_entity.class_ in COOLING_RECEPTACLES: self.receptacles['cooling_type'].add(e_id)
                    if scene_entity.class_ in CLEANING_RECEPTACLES: self.receptacles['cleaning_type'].add(e_id)
                
                elif scene_entity.class_ in OBJECTS:
                    self.objects['all'].add(e_id)
                    object_class = scene_entity.class_.replace(' ', '')
                    self.objects['class_count'][object_class] = self.objects['class_count'].get(object_class, 0) + 1
                    if scene_entity.class_ in HEATABLE_OBJECTS: self.objects['heatable_type'].add(e_id)
                    if scene_entity.class_ in COOLABLE_OBJECTS: self.objects['coolable_type'].add(e_id)
                    if scene_entity.class_ in CLEANABLE_OBJECTS: self.objects['cleanable_type'].add(scene_entity)
                    if scene_entity.class_ in SMALL_OBJECTS: self.object_sizes[e_id] = 'smallitem'
                    elif scene_entity.class_ in MEDIUM_OBJECTS: self.object_sizes[e_id] = 'mediumitem'
                    elif scene_entity.class_ in LARGE_OBJECTS: self.object_sizes[e_id] = 'largeitem'
                    self.object_names[e_id] = object_to_str_name(scene_entity, self.object_sizes[e_id])

        self.num_objects = len(self.objects['all'])
        self.num_receptacles = len(self.receptacles['all'])
        self.num_rooms = len(self.room_names)
        if self.num_objects == 0 or self.num_receptacles == 0 or self.num_rooms == 0: self.valid_scene = False
        if len(self.objects['heatable_type']) > 0 and len(self.receptacles['heating_type']) > 0: self.can_heat = True
        if len(self.objects['coolable_type']) > 0 and len(self.receptacles['cooling_type']) > 0: self.can_cool = True
        if len(self.objects['cleanable_type']) > 0 and len(self.receptacles['cleaning_type']) > 0: self.can_clean = True
        
        # sort object / receptacle semantic class by their frequency
        sorted_object_class = sorted(list(self.objects['class_count'].items()), key=lambda x: x[1])
        for idx, (class_, _) in enumerate(sorted_object_class):
            self.objects['class_index'][class_] = idx
            self.objects['class_index_inv'][idx] = class_
        sorted_receptacle_class = sorted(list(self.receptacles['class_count'].items()), key=lambda x: x[1])
        for idx, (class_, _) in enumerate(sorted_receptacle_class):
            self.receptacles['class_index'][class_] = idx
            self.receptacles['class_index_inv'][idx] = class_

        # categorize empty rooms
        for room_id in self.sg.room:
            if room_id not in self.room_names:
                room = self.sg.room[room_id]
                self.room_names[room_id] = room_to_str_name(room)
                self.room_to_place_map[room_id] = dict()
                self.room_to_place_map[room_id]['root'] = self.num_places
                self.room_to_place_map[room_id]['places'] = set()
                self.place_to_room_map[self.num_places] = room_id
                self.place_names[self.num_places] = place_to_str_name(self.num_places, room, is_room=True)
                self.num_places += 1

    def get_support_relations(self, dist_threshold=2):
        """Determine object-receptacle support relations based on the dist_threshold proximity
        metric. Standalone objects (unsupported by a receptacle) map to -1. 
        """       
        object_distances = dict()
        for o_id in self.objects['all']:    
            obj_inst = self.sg.object[o_id]
            obj_room = obj_inst.parent_room

            for r_id in self.receptacles['all']:
                rec_inst = self.sg.object[r_id]
                rec_room = rec_inst.parent_room
        
                if obj_room != rec_room: 
                    continue

                # proximity threshold
                dist = np.linalg.norm(obj_inst.location - rec_inst.location, 2)
                if dist < dist_threshold:
                    if o_id not in self.supported_objects:
                        self.supported_objects.add(o_id)    
                        object_distances[o_id] = list()
                    heapq.heappush(object_distances[o_id], (dist, r_id))
        
        # assign object to closest receptacle
        for o_id in object_distances:
            _, r_id = object_distances[o_id][0]
            self.receptacle_to_object_map[r_id].add(o_id)
            self.lifted_class_relations.add((self.sg.object[o_id].class_.replace(' ', ''), self.sg.object[r_id].class_.replace(' ', '')))
        self.unsupported_objects = self.objects['all'] - self.supported_objects

        # define place-entity and room-place mappings
        self.entity_to_place_map['objects'] = dict()
        self.entity_to_place_map['receptacles'] = dict()
        for o_id in self.unsupported_objects:
            obj_inst = self.sg.object[o_id]
            self.place_names[self.num_places] = place_to_str_name(self.num_places, obj_inst, is_object=True)
            self.place_to_entity_map[self.num_places] = {'root': o_id, 'objects': set()}
            self.entity_to_place_map['objects'][o_id] = self.num_places
            self.room_to_place_map[obj_inst.parent_room]['places'].add(self.num_places)
            self.place_to_room_map[self.num_places] = obj_inst.parent_room
            self.num_places += 1

        for r_id in self.receptacles['all']:
            rec_inst = self.sg.object[r_id]
            self.place_names[self.num_places] = place_to_str_name(self.num_places, rec_inst)
            self.place_to_entity_map[self.num_places] = {'root': r_id, 'objects': set()}
            self.entity_to_place_map['receptacles'][r_id] = self.num_places
            for o_id in self.receptacle_to_object_map[r_id]:
                self.place_to_entity_map[self.num_places]['objects'].add(o_id)
                self.entity_to_place_map['objects'][o_id] = self.num_places
            self.room_to_place_map[rec_inst.parent_room]['places'].add(self.num_places)
            self.place_to_room_map[self.num_places] = rec_inst.parent_room
            self.num_places += 1

    def get_locations(self):
        """Compute locations of all objects, receptacles, and places (self.room_to_place_map[room_id]['root']).
        """
        self.locations['objects'] = dict()
        self.locations['receptacles'] = dict()
        self.locations['places'] = dict()
        self.location_names['places'] = dict()
        self.location_names['unique'] = set()
        voxel_res = self.sg.voxel_size
        
        # object locations
        for o_id in self.objects['all']:
            obj_coord = np.floor(self.sg.object[o_id].location / voxel_res).astype(int)[:2]
            room_id = self.sg.object[o_id].parent_room
            floor_num = self.sg.room[room_id].floor_number
            room_data = (obj_coord, room_id, floor_num)
            location_name = location_to_str_name(room_data, self.entity_to_place_map['objects'][o_id])
            self.location_names[o_id] = location_name
            self.location_names['unique'].add(location_name)
            self.locations['objects'][o_id] = room_data

        # receptacle locations
        for r_id in self.receptacles['all']:
            rec_coord = np.floor(self.sg.object[r_id].location / voxel_res).astype(int)[:2]
            room_id = self.sg.object[r_id].parent_room
            floor_num = self.sg.room[room_id].floor_number
            room_data = (rec_coord, room_id, floor_num)
            location_name = location_to_str_name(room_data, self.entity_to_place_map['receptacles'][r_id])
            self.location_names[r_id] = location_name
            self.location_names['unique'].add(location_name)
            self.locations['receptacles'][r_id] = room_data

        # place locations (room doors)
        for room_id in self.room_to_place_map:
            room_coord = np.floor(self.sg.room[room_id].location / voxel_res).astype(int)[:2]
            floor_num = self.sg.room[room_id].floor_number
            room_data = (room_coord, room_id, floor_num)
            place_id = self.room_to_place_map[room_id]['root']
            location_name = location_to_str_name(room_data, place_id)
            self.location_names['places'][place_id] = location_name
            self.location_names['unique'].add(location_name)
            self.locations['places'][place_id] = room_data

        # place locations (remaining places)
        for place_id in self.place_to_entity_map:
            e_id = self.place_to_entity_map[place_id]['root']
            self.location_names['places'][place_id] = self.location_names[e_id]
            e_type = 'receptacles' if e_id not in self.unsupported_objects else 'objects'
            self.locations['places'][place_id] = self.locations[e_type][e_id]

    def build_lifted_class_matrix(self):
        """Build a matrix scoring the combined object-receptacle lifted problem difficulty.
        """
        self.lifted_class_matrix = np.zeros((len(self.objects['class_count']), len(self.receptacles['class_count'])))
        if len(self.lifted_class_matrix) == 0:
            self.valid_lifted = False
            return 

        for o_class, o_count in self.objects['class_count'].items():
            for r_class, r_count in self.receptacles['class_count'].items():
                if (o_class, r_class) in self.lifted_class_relations:
                    continue
                o_idx = self.objects['class_index'][o_class]
                r_idx = self.receptacles['class_index'][r_class]
                self.lifted_class_matrix[o_idx, r_idx] = o_count + r_count - 2

        if np.max(self.lifted_class_matrix) == 0: self.valid_lifted = False
        self.num_lifted_pairs = np.sum((self.lifted_class_matrix > 0).astype(int))
