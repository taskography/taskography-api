import numpy as np
import networkx as nx
from collections import defaultdict


def index_building(building):
    """Index rooms and floors in the building.
    """
    room_ids = dict()                   # dict(key=room_idx, value=room_id)
    room_loc = dict()                   # dict(key=room_idx, value=room_location)
    room_floor = dict()                 # dict(key=room_idx, value=floor_idx)
    floor_idx = dict()                  # dict(key=floor_id, value=floor_idx)
    floor_ids = dict()                  # dict(key=floor_idx, value=floor_id)
    floor_rooms = defaultdict(set)      # dict(key=floor_idx, value=set(room_idx))

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


def scenegraph_mst(building):
    """Apply Kruskal's algorithm to find the minimum spanning tree of room connectivities.
    Edge weights are determined by the distance between rooms' centroids. Heuristics are 
    used to determine floor adjacency such that only a single connection exists between floors.
    args:
        building: a loaded <Building(SceneGraphNode)> object.
    """
    room_ids, room_loc, floor_rooms = index_building(building)

    # sanity check on scene graph pickle data
    if building.num_rooms is None:
        building.num_rooms = len(building.room)
    assert(len(building.room) == building.num_rooms)
    num_floors_with_rooms = len(floor_rooms)

    # room-room distance matrix
    room_loc_np = np.array(list(room_loc.values()))                 # n x 3 
    room_loc_np_exp = np.expand_dims(room_loc_np.copy(), axis=2)    # n x 3 x 1
    room_dist_mat = np.linalg.norm((room_loc_np_exp.transpose(1, 0, 2) - room_loc_np_exp.transpose(1, 2, 0)), axis=0)

    # compute minumal spanning tree of rooms
    room_graph = nx.Graph()
    if num_floors_with_rooms > 1:

        # compute minimal spanning tree of floors
        floor_graph = nx.Graph()
        floor_adj_data = dict()
        for floor_a, floor_a_rooms in floor_rooms.items():
            for floor_b, floor_b_rooms in floor_rooms.items():
                if floor_a == floor_b or (floor_a, floor_b) in floor_adj_data or (floor_b, floor_a) in floor_adj_data:
                    continue
                floor_a_rooms = list(floor_a_rooms)
                floor_b_rooms = list(floor_b_rooms)

                # floor-floor heuristic: mean of min connection between rooms in both floors 
                n, m = len(floor_a_rooms), len(floor_b_rooms)
                floor_a_rooms_repeat = np.repeat(np.array(floor_a_rooms, dtype=np.int), m)
                floor_b_rooms_tile = np.tile(np.array(floor_b_rooms, dtype=np.int), n)
                room_a_to_b_dist = room_dist_mat[floor_a_rooms_repeat, floor_b_rooms_tile].reshape(n, m)
                floor_dist_heuristic = np.amin(room_a_to_b_dist, axis=0).mean()
                floor_graph.add_edge(floor_a, floor_b, weight=floor_dist_heuristic)
                
                # store minimum connection between floors
                room_a_tidx, room_b_tidx = np.unravel_index(np.argmin(room_a_to_b_dist), shape=room_a_to_b_dist.shape)
                data = {
                    "min_rooms": [floor_a_rooms[room_a_tidx], floor_b_rooms[room_b_tidx]], 
                    "min_dist": np.amin(room_a_to_b_dist)
                }
                floor_adj_data[(floor_a, floor_b)] = data
                floor_adj_data[(floor_b, floor_a)] = data

        floor_mst = nx.minimum_spanning_tree(floor_graph)
        assert (floor_mst.order() == num_floors_with_rooms)

        # add edge between closest rooms connecting floors
        for floor_a, floor_b in floor_mst.edges():
            data = floor_adj_data[(floor_a, floor_b)]
            room_graph.add_edge(*data["min_rooms"], weight=data["min_dist"])

    # connect all rooms in each floor
    for _, rooms in floor_rooms.items():
        room_idx_repeat = np.repeat(np.array(list(rooms), dtype=np.int), len(rooms))
        room_idx_tile = np.tile(np.array(list(rooms), dtype=np.int), len(rooms))
        room_dist = room_dist_mat[room_idx_repeat, room_idx_tile]
        room_graph.add_weighted_edges_from(list(zip(room_idx_repeat, room_idx_tile, room_dist)))

    # add room adjacency list to scene graph
    room_mst = nx.minimum_spanning_tree(room_graph)
    assert(nx.number_connected_components(room_mst) == 1), "Minimum spanning tree is not complete"
    assert (building.num_rooms == room_mst.order()), "Missing rooms in computed minimum spanning tree"
    assert (building.num_rooms-1 == room_mst.size()), "Missing edges in the computed minimum spanning tree"
    for room_a_idx, room_b_idx in room_mst.edges():
        building.room[room_ids[room_a_idx]].connected_rooms.add(room_ids[room_b_idx])
        building.room[room_ids[room_b_idx]].connected_rooms.add(room_ids[room_a_idx])
