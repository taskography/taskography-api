import os

from .task_sampler_base import TaskSamplerBase
from ..utils.loader import loader


class PDDLSceneGraphMapper(TaskSamplerBase):

    def __init__(self, data_path=None, model_name=None, scenegraph=None):
        """Class that maps object names parsed from a PDDL problem file to the 
        corresponding SceneGraphNode object as defined in loader.py. 
        """
        assert (scenegraph is not None or (model_name is not None and data_path is not None))
        if scenegraph is not None:
            super(PDDLSceneGraphMapper, self).__init__(scenegraph)
        else:
            model_type = "verified_graph" if os.path.basename(data_path) == 'tiny' else "automated_graph"
            model_path = os.path.join(data_path, model_type, "3DSceneGraph_" + model_name + ".npz")
            scenegraph = loader(model_path)
            super(PDDLSceneGraphMapper, self).__init__(scenegraph)

        # room name to room ID mapping
        self.room_map = {}
        for room_id, room_name in self.room_names.items():
            self.room_map[room_name] = room_id     

        # receptacle name to receptacle ID mapping
        self.receptacle_map = {}
        for receptacle_id, receptacle_name in self.receptacle_mames.items():
            self.receptacle_map[receptacle_name] = receptacle_id

        # item name to object ID mapping
        self.object_map = {}
        for object_id, item_name in self.object_names.items():
            self.object_map[item_name] = object_id

        # location name to 3d coordinate mapping
        self.location_map = {}
        for e_id, location_name in self.location_names.items():
            if e_id not in ['places', 'unique']:    
                if location_name not in self.location_map:
                    self.location_map[location_name] = self.sg.object[e_id].location
        # locations of center of rooms
        for p_id, location_name in self.location_names['places'].items():
            if location_name not in self.location_map:
                room_id = self.place_to_room_map[p_id]
                self.location_map[location_name] = self.sg.room[room_id].location

    def get_scene_object(self, object_type, name):
        """Return SceneGraphObject of type object_type with the given name.
        """
        assert (object_type in ['item', 'receptacle', 'room'])
        if object_type == 'room':
            return self.get_room(name)            
        elif object_type == 'receptacle':
            return self.get_receptacle(name)
        elif object_type == 'item':
            return self.get_item(name)

    def get_room(self, name):
        """Return Room given the PDDL name of a room.
        """
        assert (name in self.room_map)
        room_id = self.room_map[name]
        return self.sg.room[room_id]
        
    def get_receptacle(self, name):
        """Return SceneObject given the PDDL name of a receptacle.
        """
        assert (name in self.receptacle_map)
        receptacle_id = self.receptacle_map[name]
        return self.sg.object[receptacle_id]

    def get_item(self, name):
        """Return SceneObject given the PDDL name of an item.
        """
        assert (name in self.object_map)
        object_id = self.object_map[name]
        return self.sg.object[object_id]

    def get_3d_location(self, name):
        """Return the x-y-z coordinates of a given PDDL location name.
        """
        assert (name in self.location_map)
        return self.location_map[name]
