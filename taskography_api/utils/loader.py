import numpy as np

# SceneGraphNode, Building, Room, SceneObject, Camera
from .scenegraph import *
from .utils import scenegraph_mst


def loader(path):
    """Load a 3D scene graph.
    args:
        path: path to an iGibson scene graph pickle file.
    """
    data = np.load(path, allow_pickle=True)["output"].item()
    building = Building()

    # Set building attributes
    for key in data["building"].keys():
        if key in [
            "object_inst_segmentation",
            "room_inst_segmentation",
            "object_voxel_occupancy",
            "room_voxel_occupancy",
        ]:
            continue
        building.set_attribute(key, data["building"][key])
    res = building.voxel_resolution
    voxel_centers = np.reshape(building.voxel_centers, (res[0], res[1], res[2], 3))
    building.set_attribute("voxel_centers", voxel_centers)

    # Set room attributes
    unique_rooms = np.unique(data["building"]["room_inst_segmentation"])
    for room_id in unique_rooms:
        if room_id == 0:
            continue
        building.room[room_id] = Room()
        room_faces = np.where(data["building"]["room_inst_segmentation"] == room_id)[0]
        building.room[room_id].set_attribute("inst_segmentation", room_faces)
        room_voxels = np.where(data["building"]["room_voxel_occupancy"] == room_id)[0]
        building.room[room_id].set_attribute("voxel_occupancy", room_voxels)
        for key in data["room"][room_id].keys():
            building.room[room_id].set_attribute(key, data["room"][room_id][key])
    
    # Set object attributes
    unique_objects = np.unique(data["building"]["object_inst_segmentation"])
    for object_id in unique_objects:
        if object_id == 0:
            continue
        building.object[object_id] = SceneObject()
        object_faces = np.where(data["building"]["object_inst_segmentation"] == object_id)[0]
        building.object[object_id].set_attribute("inst_segmentation", object_faces)
        object_voxels = np.where(data["building"]["object_voxel_occupancy"] == object_id)[0]
        building.object[object_id].set_attribute("voxel_occupancy", object_voxels)
        for key in data["object"][object_id].keys():
            building.object[object_id].set_attribute(key, data["object"][object_id][key])
    
    # Set camera attributes
    for cam_id in data["camera"].keys():
        if cam_id == 0:
            continue
        building.camera[cam_id] = Camera()
        for key in data["camera"][cam_id].keys():
            building.camera[cam_id].set_attribute(key, data["camera"][cam_id][key])

    scenegraph_mst(building)
    return building
