import numpy as np
from collections import defaultdict

from .loader import loader


def index_building(building):
    """Index rooms and floors in the building.
    """
    room_ids = dict()           # dict(key=room_idx, value=room_id)
    room_loc = dict()           # dict(key=room_idx, value=room_location)
    room_floor = dict()         # dict(key=room_idx, value=floor_idx)
    floor_idx = dict()          # dict(key=floor_id, value=floor_idx)
    floor_ids = dict()          # dict(key=floor_idx, value=floor_id)

    count = 0
    for idx, id in enumerate(building.room):
        room_ids[idx] = id
        room_loc[idx] = building.room[id].location
        f_id = building.room[id].floor_number
        if f_id not in floor_idx:
            floor_idx[f_id] = count
            floor_ids[count] = f_id
            count += 1
        room_floor[id] = floor_idx[f_id]

    floor_rooms = defaultdict(set)
    for r_id, f_id in room_floor.items():
        floor_rooms[f_id].add(r_id)
    
    return room_ids, room_loc, room_floor, floor_rooms


def compute_room_adj(room_loc):
    num_rooms = len(room_loc)
    adj_rooms = np.zeros((num_rooms, num_rooms), dtype=np.float)
    
    loc_tensor = np.array(list(room_loc.values())).shape()



def scenegraph_mst(building):
    """Apply Kruskal's algorithm to find the minimum spanning tree of room connectivities.
    Edge weights are determined by the distance between rooms' centroids. Heuristics are 
    used to determine floor adjacency such that only a single connection exists between floors.
    args:
        building: a loaded <Building(SceneGraphNode)> object.
    """
    room_ids, room_loc, room_floor, floor_rooms = index_building(building)

    # sanity check on scene graph pickle data
    if building.num_rooms is None:
        building.num_rooms = len(building.room)
    assert(len(building.room) == building.num_rooms)
    num_floors_with_rooms = len(floor_rooms)


#     # compute room-room distances
#     adj_rooms = np.zeros((building.num_rooms, building.num_rooms))
#     for i in range(building.num_rooms):
#         for j in range(i+1, building.num_rooms):
#             dist = np.linalg.norm(location[i] - location[j], 2)
#             adj_rooms[i, j] = dist
#             adj_rooms[j, i] = dist

#     # compute minimum spanning tree for all rooms
#     room_graph = Graph(building.num_rooms)

#     # find average-minimum distances of rooms between floors
#     if num_floors_with_rooms > 1:
#         adj_floors = np.zeros((num_floors_with_rooms, num_floors_with_rooms))
#         adj_floors_count = np.ones((num_floors_with_rooms, num_floors_with_rooms))
        
#         for room_id_a, floor_id_a in floor.items():
#             for floor_id_b in floor_to_room_map:
#                 if floor_id_a == floor_id_b:
#                     continue
                
#                 # compute minimum room-room distance between different floors
#                 room_id_bs = np.array(list(floor_to_room_map[floor_id_b]), dtype=int)
#                 room_id_as = np.ones_like(room_id_bs, dtype=int) * room_id_a
#                 min_dist = adj_rooms[room_id_as, room_id_bs].min()
                
#                 # compute running average
#                 n = adj_floors_count[floor_id_a, floor_id_b]
#                 adj_floors[floor_id_a, floor_id_b] += (1/n) * (min_dist - adj_floors[floor_id_a, floor_id_b])
#                 adj_floors_count[floor_id_a, floor_id_b] += 1

#         # compute minimum spanning floor tree
#         floor_graph = Graph(num_floors_with_rooms)
#         for floor_id_a in range(num_floors_with_rooms):
#             for floor_id_b in range(floor_id_a, num_floors_with_rooms):
#                 floor_graph.addEdge(floor_id_a, floor_id_b, adj_floors[floor_id_a, floor_id_b])
#         floor_mst = floor_graph.KruskalMST()

#         # add minimum edge across floors
#         for floor_id_a, floor_id_b, w in floor_mst:
#             room_id_as = np.array(list(floor_to_room_map[floor_id_a]), dtype=int)
#             room_id_bs = np.array(list(floor_to_room_map[floor_id_b]), dtype=int)
#             ones_b = np.ones_like(room_id_bs, dtype=int)

#             distances = np.zeros(len(room_id_as) * len(room_id_bs))
#             room_coords = np.empty((2, len(room_id_as) * len(room_id_bs)), dtype=int)
#             i = 0
#             for room_a in room_id_as:
#                 room_idx_as = ones_b.copy() * room_a
#                 distances[i:i+len(ones_b)] = adj_rooms[room_idx_as, room_id_bs]
#                 room_coords[:, i:i+len(ones_b)] = np.stack((room_idx_as, room_id_bs))
#                 i += len(ones_b)

#             min_edge = np.min(distances)
#             min_room_a, min_room_b = room_coords[:, np.argmin(distances)]
#             room_graph.addEdge(min_room_a, min_room_b, min_edge)
    
#     for floor_id in floor_to_room_map:
#         room_ids = np.array(list(floor_to_room_map[floor_id]), dtype=int)
#         for i, room_i in enumerate(room_ids):
#             for j, room_j in enumerate(room_ids, i+1):
#                 room_graph.addEdge(room_i, room_j, adj_rooms[room_i, room_j])
    
#     # compute room MST
#     room_mst = room_graph.KruskalMST()
#     building.MST = room_mst
#     connected_rooms = set()
#     for i, j, w in room_mst:
#         connected_rooms.add(room_map[i])
#         connected_rooms.add(room_map[j])
#         building.room[room_map[i]].connected_rooms.add(room_map[j])
#         building.room[room_map[j]].connected_rooms.add(room_map[i])
    
#     assert(len(connected_rooms) == building.num_rooms)
#     assert(len(building.MST) == building.num_rooms - 1)


# class Graph:
 
#     def __init__(self, vertices):
#         self.V = vertices  
#         self.graph = [] 
 
#     def addEdge(self, u, v, w):
#         self.graph.append([u, v, w])

#     def find(self, parent, i):
#         if parent[i] == i:
#             return i
#         return self.find(parent, parent[i])

#     def union(self, parent, rank, x, y):
#         xroot = self.find(parent, x)
#         yroot = self.find(parent, y)
 
#         if rank[xroot] < rank[yroot]:
#             parent[xroot] = yroot
#         elif rank[xroot] > rank[yroot]:
#             parent[yroot] = xroot
#         else:
#             parent[yroot] = xroot
#             rank[xroot] += 1

#     def KruskalMST(self):
#         result = []  
#         i = 0
#         e = 0

#         self.graph = sorted(self.graph, key=lambda item: item[2])
#         parent = []
#         rank = []
 
#         # Create V subsets with single elements
#         for node in range(self.V):
#             parent.append(node)
#             rank.append(0)
 
#         # Number of edges to be taken is equal to V-1
#         while e < self.V - 1:
#             u, v, w = self.graph[i]
#             i = i + 1
#             x = self.find(parent, u)
#             y = self.find(parent, v)
 
#             if x != y:
#                 e = e + 1
#                 result.append([u, v, w])
#                 self.union(parent, rank, x, y)
 
#         minimumCost = 0
#         for u, v, weight in result:
#             minimumCost += weight

#         return result