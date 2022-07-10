from typing import Tuple, Dict, DefaultDict

import numpy as np
import networkx as nx
from collections import defaultdict

from .scenegraph import *


def loader(path: str) -> Building:
    """Load a 3D scene graph.

    args:
        path: path to an iGibson scene graph pickle file.
    
    returns:
        building: 3D scene graph building
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
        object_faces = np.where(
            data["building"]["object_inst_segmentation"] == object_id
        )[0]
        building.object[object_id].set_attribute("inst_segmentation", object_faces)
        object_voxels = np.where(
            data["building"]["object_voxel_occupancy"] == object_id
        )[0]
        building.object[object_id].set_attribute("voxel_occupancy", object_voxels)
        for key in data["object"][object_id].keys():
            building.object[object_id].set_attribute(
                key, data["object"][object_id][key]
            )

    # Set camera attributes
    for cam_id in data["camera"].keys():
        if cam_id == 0:
            continue
        building.camera[cam_id] = Camera()
        for key in data["camera"][cam_id].keys():
            building.camera[cam_id].set_attribute(key, data["camera"][cam_id][key])

    scenegraph_mst(building)
    return building


def scenegraph_mst(building: Building) -> None:
    """Apply Kruskal's algorithm to find the minimum spanning tree of room connectivities.
    Edge weights are determined by the distance between rooms' centroids. Heuristics are 
    used to determine floor adjacency such that only a single connection exists between floors.
    
    args:
        building: a loaded 3D scene graph building       
    """
    room_ids, room_loc, floor_rooms = index_building(building)

    # sanity check on scene graph pickle data
    if building.num_rooms is None:
        building.num_rooms = len(building.room)
    assert len(building.room) == building.num_rooms
    num_floors_with_rooms = len(floor_rooms)

    # room-room distance matrix
    room_loc_np = np.array(list(room_loc.values()))  # n x 3
    room_loc_np_exp = np.expand_dims(room_loc_np.copy(), axis=2)  # n x 3 x 1
    room_dist_mat = np.linalg.norm(
        (room_loc_np_exp.transpose(1, 0, 2) - room_loc_np_exp.transpose(1, 2, 0)),
        axis=0,
    )

    # compute minumal spanning tree of rooms
    room_graph = nx.Graph()
    if num_floors_with_rooms > 1:

        # compute minimal spanning tree of floors
        floor_graph = nx.Graph()
        floor_adj_data = dict()
        for floor_a, floor_a_rooms in floor_rooms.items():
            for floor_b, floor_b_rooms in floor_rooms.items():
                if (
                    floor_a == floor_b
                    or (floor_a, floor_b) in floor_adj_data
                    or (floor_b, floor_a) in floor_adj_data
                ):
                    continue
                floor_a_rooms = list(floor_a_rooms)
                floor_b_rooms = list(floor_b_rooms)

                # floor-floor heuristic: mean of min connection between rooms in both floors
                n, m = len(floor_a_rooms), len(floor_b_rooms)
                floor_a_rooms_repeat = np.repeat(
                    np.array(floor_a_rooms, dtype=np.int), m
                )
                floor_b_rooms_tile = np.tile(np.array(floor_b_rooms, dtype=np.int), n)
                room_a_to_b_dist = room_dist_mat[
                    floor_a_rooms_repeat, floor_b_rooms_tile
                ].reshape(n, m)
                floor_dist_heuristic = np.amin(room_a_to_b_dist, axis=0).mean()
                floor_graph.add_edge(floor_a, floor_b, weight=floor_dist_heuristic)

                # store minimum connection between floors
                room_a_tidx, room_b_tidx = np.unravel_index(
                    np.argmin(room_a_to_b_dist), shape=room_a_to_b_dist.shape
                )
                data = {
                    "min_rooms": [
                        floor_a_rooms[room_a_tidx],
                        floor_b_rooms[room_b_tidx],
                    ],
                    "min_dist": np.amin(room_a_to_b_dist),
                }
                floor_adj_data[(floor_a, floor_b)] = data
                floor_adj_data[(floor_b, floor_a)] = data

        floor_mst = nx.minimum_spanning_tree(floor_graph)
        assert floor_mst.order() == num_floors_with_rooms

        # add edge between closest rooms connecting floors
        for floor_a, floor_b in floor_mst.edges():
            data = floor_adj_data[(floor_a, floor_b)]
            room_graph.add_edge(*data["min_rooms"], weight=data["min_dist"])

    # connect all rooms in each floor
    for _, rooms in floor_rooms.items():
        room_idx_repeat = np.repeat(np.array(list(rooms), dtype=np.int), len(rooms))
        room_idx_tile = np.tile(np.array(list(rooms), dtype=np.int), len(rooms))
        room_dist = room_dist_mat[room_idx_repeat, room_idx_tile]
        room_graph.add_weighted_edges_from(
            list(zip(room_idx_repeat, room_idx_tile, room_dist))
        )

    # add room adjacency list to scene graph
    room_mst = nx.minimum_spanning_tree(room_graph)
    assert (
        nx.number_connected_components(room_mst) == 1
    ), "Minimum spanning tree is not complete"
    assert (
        building.num_rooms == room_mst.order()
    ), "Missing rooms in computed minimum spanning tree"
    assert (
        building.num_rooms - 1 == room_mst.size()
    ), "Missing edges in the computed minimum spanning tree"
    for room_a_idx, room_b_idx in room_mst.edges():
        building.room[room_ids[room_a_idx]].connected_rooms.add(room_ids[room_b_idx])
        building.room[room_ids[room_b_idx]].connected_rooms.add(room_ids[room_a_idx])


def index_building(building: Building) -> Tuple[Dict, Dict, DefaultDict]:
    """Index rooms and floors in the building.
    """
    room_ids = dict()  # dict(key=room_idx, value=room_id)
    room_loc = dict()  # dict(key=room_idx, value=room_location)
    room_floor = dict()  # dict(key=room_idx, value=floor_idx)
    floor_idx = dict()  # dict(key=floor_id, value=floor_idx)
    floor_ids = dict()  # dict(key=floor_idx, value=floor_id)
    floor_rooms = defaultdict(set)  # dict(key=floor_idx, value=set(room_idx))

    count = 0
    for idx, id in enumerate(building.room):
        room_ids[idx] = id
        room_loc[idx] = building.room[id].location
        f_id = building.room[id].floor_number
        if f_id not in floor_idx:
            floor_idx[f_id] = count
            floor_ids[count] = f_id
            count += 1
        room_floor[idx] = floor_idx[f_id]

    for r_idx, f_idx in room_floor.items():
        floor_rooms[f_idx].add(r_idx)

    return room_ids, room_loc, floor_rooms
