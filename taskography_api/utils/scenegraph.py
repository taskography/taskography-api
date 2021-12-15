class SceneGraphNode(object):

    def __init__(self):
        pass

    def set_attribute(self, attr, value):
        if attr not in self.__dict__.keys():
            raise ValueError(f"Unknown attribute: {attr}")
        self.__dict__[attr] = value
    
    def get_attribute(self, attr):
        if attr not in self.__dict__.keys():
            raise ValueError(f"Unknown attribute: {attr}")
        return self.__dict__[attr]


class Building(SceneGraphNode):

    def __init__(self):
        # 2D floor area (sq. meters)
        self.floor_area = None
        # Functionality of the building
        self.function = None
        # Gibson split (tiny, medium, large)
        self.gibson_split = None
        # Unique building id
        self.id = None
        # Name of the Gibson model
        self.name = None
        # Number of panoramic cameras in the model
        self.num_cameras = None
        # Number of floors in the building
        self.num_floors = None
        # Number of objects in the building
        self.num_objects = None
        # Number of rooms in the building
        self.num_rooms = None
        # Building reference point
        self.reference_point = None
        # 3D size of building
        self.size = None
        # 3D volume of building (in cubic meters, computed from the 3D convex hull)
        self.volume = None
        # Size of each voxel
        self.voxel_size = None
        # 3D coordinates of voxel centers (N x 3)
        self.voxel_centers = None
        # Number of voxels per axis (k x l x m)
        self.voxel_resolution = None

        # Instantiate other layers in the graph
        self.room = {}
        self.camera = {}
        self.object = {}

    def print_attributes(self):
        print(f'--- Building ID: {self.id} ---')
        for key in self.__dict__.keys():
            if key not in ['room', 'camera', 'object', 'voxel_centers']:
                print(f"Key: {key} | Value: {self.get_attribute(key)}")


class Room(SceneGraphNode):

    def __init__(self):
        # 2D floor area (in square meters)
        self.floor_area = None
        # Index of the floor that contains this room
        self.floor_number = None
        # Unique space id per building
        self.id = None
        # 3D coordinates of room center
        self.location = None
        # Building face indices that correspond to this room
        self.inst_segmentation = None
        # Functionality of the room
        self.scene_category = None
        # 3D size of the room
        self.size = None
        # Building's voxel indices tha correspond to this space
        self.voxel_occupancy = None
        # 3D volume of the room (in cubic meters, computed from the 3D convex hull)
        self.volume = None
        # Parent building that contains this room
        self.parent_building = None
        # Connected Rooms
        self.connected_rooms = set()

    def print_attributes(self):
        print(f'--- Room ID: {self.id} ---')
        for key in self.__dict__.keys():
            print(f"Key: {key} | Value: {self.get_attribute(key)}")


class SceneObject(SceneGraphNode):

    def __init__(self):
        # List of possible actions
        self.action_affordance = None
        # 2D floor area (in square meters)
        self.floor_area = None
        # Total surface coverage (in square meters)
        self.surface_coverage = None
        # Object label
        self.class_ = None
        # Unique object id per building
        self.id = None
        # 3D coordinates of object center
        self.location = None
        # List of main object materials
        self.material = None
        # 3D object size
        self.size = None
        # Building face indices that correspond to this object
        self.inst_segmentation = None
        # Main tactile texture (may be None)
        self.tactile_texture = None
        # Main visible texture (may be None)
        self.visual_texture = None
        # 3D volume of object (in cubic meters, computed from the 3D convex hull)
        self.volume = None
        # Building voxel indices corresponding to this object
        self.voxel_occupancy = None
        # Parent room that contains this object
        self.parent_room = None

    def print_attributes(self):
        print(f'--- Object ID: {self.id} ---')
        for key in self.__dict__.keys():
            print(f"Key: {key} | Value: {self.get_attribute(key)}")


class Camera(SceneGraphNode):

    def __init__(self):
        # Name of the camera
        self.name = None
        # Unique camera id
        self.id = None
        # Camera field of view
        self.FOV = None
        # 3D location of camera in the model
        self.location = None
        # 3D orientation of camera (quaternion)
        self.rotation = None
        # Camera modality (e.g., RGB, grayscale, depth, etc.)
        self.modality = None
        # Camera resolution
        self.resolution = None
        # Parent room that contains this camera
        self.parent_room = None
