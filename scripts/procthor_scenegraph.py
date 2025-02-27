import json

class SceneGraphNode(object):
    def __init__(self):
        self.id = None

    def set_attribute(self, attr, value):
        if attr not in self.__dict__.keys():
            raise ValueError(f"Unknown attribute: {attr}")
        self.__dict__[attr] = value

    def get_attribute(self, attr):
        if attr not in self.__dict__.keys():
            raise ValueError(f"Unknown attribute: {attr}")
        return self.__dict__[attr]

    def print_attributes(self):
        print(f"--- {self.__class__.__name__} ID: {self.get_attribute('id')} ---")
        for key in self.__dict__.keys():
            print(f"Key: {key} | Value: {self.get_attribute(key)}")


class Door(SceneGraphNode):
    def __init__(self, data=None):
        super().__init__()
        self.asset_id = None
        self.asset_position = None
        self.hole_polygon = None
        self.openable = None
        self.openness = None
        self.rooms = None
        self.walls = None
        if data is not None:
            self.set_attribute('asset_id', data['assetId'])
            self.set_attribute('asset_position', data['assetPosition'])
            self.set_attribute('hole_polygon', data['holePolygon'])
            self.set_attribute('id', data['id'])
            self.set_attribute('openable', data['openable'])
            self.set_attribute('openness', data['openness'])
            self.set_attribute('rooms', [data['room0'], data['room1']])
            self.set_attribute('walls', [data['wall0'], data['wall1']])


class ObjectChild(SceneGraphNode):
    def __init__(self, data=None):
        super().__init__()
        self.asset_id = None
        self.kinematic = None
        self.position = None
        self.rotation = None
        if data is not None:
            self.set_attribute('asset_id', data['assetId'])
            self.set_attribute('id', data['id'])
            self.set_attribute('kinematic', data['kinematic'])
            self.set_attribute('position', data['position'])
            self.set_attribute('rotation', data['rotation'])


class Object(SceneGraphNode):
    def __init__(self, data=None):
        super().__init__()
        self.asset_id = None
        self.children = None
        self.kinematic = None
        self.material = None
        self.position = None
        self.rotation = None
        if data is not None:
            self.set_attribute('asset_id', data['assetId'])
            # self.set_attribute('children', [ObjectChild(child) for child in data['children']])
            self.set_attribute('id', data['id'])
            self.set_attribute('kinematic', data['kinematic'])
            self.set_attribute('material', data['material'])
            self.set_attribute('position', data['position'])
            self.set_attribute('rotation', data['rotation'])
            if 'children' in data:
                self.set_attribute('children', [ObjectChild(child) for child in data['children']])
            else:
                self.set_attribute('children', [])

class Room(SceneGraphNode):
    def __init__(self, data=None):
        super().__init__()
        self.ceilings = None
        self.children = None
        self.floor_material = None
        self.floor_polygon = None
        self.room_type = None
        if data is not None:
            self.set_attribute('ceilings', data['ceilings'])
            self.set_attribute('children', data['children'])
            self.set_attribute('floor_material', data['floorMaterial'])
            self.set_attribute('floor_polygon', data['floorPolygon'])
            self.set_attribute('id', data['id'])
            self.set_attribute('room_type', data['roomType'])


class Wall(SceneGraphNode):
    def __init__(self, data=None):
        super().__init__()
        self.color = None
        self.material = None
        self.polygon = None
        self.room_id = None
        if data is not None:
            self.set_attribute('id', data['id'])
            self.set_attribute('material', data['material'])
            self.set_attribute('polygon', data['polygon'])
            self.set_attribute('room_id', data['roomId'])
            if 'color' in data:
                self.set_attribute('color', data['color'])


class House(SceneGraphNode):
    def __init__(self, json_data=None):
        super().__init__()
        self.doors = None
        self.objects = None
        self.rooms = None
        self.walls = None
        self.windows = None
        self.metadata = None
        self.procedural_parameters = None
        if json_data is not None:
            self.set_attribute('doors', [Door(door) for door in json_data.get('doors', [])])
            self.set_attribute('objects', [Object(obj) for obj in json_data.get('objects', [])])
            self.set_attribute('rooms', [Room(room) for room in json_data.get('rooms', [])])
            self.set_attribute('walls', [Wall(wall) for wall in json_data.get('walls', [])])
            self.set_attribute('windows', json_data.get('windows', []))
            self.set_attribute('metadata', json_data.get('metadata', {}))
            self.set_attribute('procedural_parameters', json_data.get('proceduralParameters', {}))


if __name__ == "__main__":
    procthor_json_path = 'procthor_houses/procthor-10k_train_0.json'
    with open(procthor_json_path, 'r') as f:
        procthor_json = json.load(f)
    house = House(procthor_json)
    house.print_attributes()
