# general constants
DOMAIN_ALIAS = {
    "taskographyv1": "flat_rearrangement",
    "taskographyv2": "rearrangement",
    "taskographyv3": "courier",
    "taskographyv4": "lifted_rearrangement",
    "taskographyv5": "lifted_courier",
}


DOMAIN_BAGSLOTS = {
    "flat_rearrangement": False,
    "rearrangement": False,
    "courier": True,
    "lifted_rearrangement": False,
    "lifted_courier": True
}


OFFICIAL_SPLITS = {
    "tiny": "tiny/verified_graph",
    "medium": "medium/automated_graph"
}


SPLIT_SCENES = {
    "tiny": 35,
    "tiny/verified_graph": 35,
    "medium": 105,
    "medium/automated_graph": 105
}


# scene entities
ROOMS = {
    'bathroom',
    'bedroom',
    'childs_room',
    'closet',
    'corridor',
    'dining_room',
    'empty_room',
    'exercise_room',
    'garage',
    'home_office',
    'kitchen',
    'living_room',
    'lobby',
    'pantry_room',
    'playroom',
    'staircase',
    'storage_room',
    'television_room',
    'utility_room'
}


OBJECTS = {
    'apple',
    'backpack',
    'banana',
    'baseball bat',
    'baseball glove',
    'book',
    'bottle',
    'bowl',
    'cake',
    'cell phone',
    'clock',
    'cup',
    'frisbee',
    'handbag',
    'keyboard',
    'kite',
    'knife',
    'laptop',
    'mouse',
    'orange',
    'potted plant',
    'remote',
    'spoon',
    'sports ball',
    'suitcase',
    'teddy bear',
    'tie',
    'toothbrush',
    'umbrella',
    'vase',
    'wine glass',
    'bicycle',
    'motorcycle',
    'surfboard',
    'tv'
}

SMALL_OBJECTS = {
    'apple',
    'banana',
    'baseball glove',
    'book',
    'bottle',
    'bowl',
    'cell phone',
    'cup',
    'knife',
    'mouse',
    'orange',
    'remote',
    'spoon',
    'tie',
    'toothbrush',
    'wine glass'
}

MEDIUM_OBJECTS = {
    'cake',
    'clock',
    'frisbee',
    'laptop',
    'teddy bear',
    'vase'
}

LARGE_OBJECTS = {
    'backpack',
    'baseball bat',
    'handbag',
    'keyboard',
    'kite',
    'potted plant',
    'sports ball',
    'suitcase',
    'umbrella',
    'bicycle',
    'motorcycle',
    'surfboard',
    'tv'
}

assert(len(SMALL_OBJECTS.union(MEDIUM_OBJECTS.union(LARGE_OBJECTS))) == len(OBJECTS))


# objects that can be placed in HEATING receptacle type
HEATABLE_OBJECTS = {
    'apple',
    'banana',
    'bottle',
    'bowl',
    'cake',
    'cup',
    'orange'
}

# objects that can be placed in COOLING receptacle type
COOLABLE_OBJECTS = {
    'apple',
    'banana',
    'bottle',
    'bowl',
    'cake',
    'cup',
    'orange',
    'wine glass'
}

# objects that can be placed in CLEANING receptacle type
CLEANABLE_OBJECTS = {
    'apple',
    'banana',
    'bottle',
    'bowl',
    'cup',
    'frisbee',
    'knife',
    'orange',
    'spoon',
    'sports ball',
    'toothbrush',
    'vase',
    'wine glass'
}

# receptacle objects can store one or more non-receptacle object
RECEPTACLE_OBJECTS = {
    'backpack',
    'baseball glove',
    'bottle',
    'bowl',
    'handbag',
    'suitcase',
    'vase',
    'wine glass'
}

# non-receptacle objects cannot store other objects
NON_RECEPTACLE_OBJECTS = OBJECTS - RECEPTACLE_OBJECTS


RECEPTACLES = {
    'bed',
    'bench',
    'boat',
    'chair',
    'couch',
    'dining table',
    'microwave',
    'oven',
    'refrigerator',
    'sink',
    'toaster',
    'toilet'
}

# receptacle types (for generating receptacle receptacle_type facts)
OPENING_RECEPTACLES = {
    'microwave',
    'oven',
    'refrigerator'
}

HEATING_RECEPTACLES = {
    'microwave',
    'oven',
    'toaster'
}

COOLING_RECEPTACLES = {
    'refrigerator'
}

CLEANING_RECEPTACLES = {
    'sink'
}

# TODO: leave out toggle for now, macro-actions assume toggle on the receptacles
# TOGGLEABLE_RECEPTACLES = {
#     'microwave',
#     'oven',
#     'sink',
#     'toaster',
#     'toilet'
# }


MATERIALS = {
    'ceramic',
    'fabric',
    'foliage',
    'food',
    'glass',
    'leather',
    'metal',
    'mirror',
    'other',
    'oven',
    'paper',
    'plastic',
    'polished stone',
    'stone',
    'wood'
}

TEXTURES = {
    'visual': {
        'blotchy',
        'chequered',
        'crosshatched',
        'dotted',
        'grid',
        'interlaced',
        'lined',
        'marbled',
        'paisley',
        'polka-dotted',
        'smeared',
        'stained',
        'striped',
        'swirly',
        'zigzagged'
    },
    'tactile': {
        'braided',
        'bumpy',
        'crystalline',
        'fibrous',
        'frilly',
        'gauzy',
        'grooved',
        'knitted',
        'matted',
        'meshed',
        'perforated',
        'pleated',
        'potholed',
        'scaly',
        'spiralled',
        'stratified',
        'studded',
        'veined',
        'waffled',
        'woven',
        'wrinkled',
    }
}


# PDDLGym Taskography benchmark domain names
BENCHMARK_DOMAINS = [
    ## Full Domains
    # Rearrangment(k)
    "taskographyv2tiny1",
    "taskographyv2medium1",
    "taskographyv2tiny2",
    "taskographyv2medium2",
    "taskographyv2tiny5",
    "taskographyv2medium5",
    "taskographyv2tiny10",
    "taskographyv2medium10",
    # Courier(n, k)
    "taskographyv3tiny5bagslots5",
    "taskographyv3medium5bagslots5",
    "taskographyv3tiny10bagslots3",
    "taskographyv3medium10bagslots3",
    "taskographyv3tiny10bagslots5",
    "taskographyv3medium10bagslots5",
    "taskographyv3tiny10bagslots7",
    "taskographyv3medium10bagslots7",
    "taskographyv3tiny10bagslots10",
    "taskographyv3medium10bagslots10",
    # Lifted Rearrangement(k)
    "taskographyv4tiny5",
    "taskographyv4medium5",
    # Lifted Courier(n, k)
    "taskographyv5tiny5bagslots5",
    "taskographyv5medium5bagslots5",
    
    ## Scrubbed Domains
    # Rearrangement(k)
    "taskographyv2tiny1scrub",
    "taskographyv2medium1scrub",
    "taskographyv2tiny2scrub",
    "taskographyv2medium2scrub",
    "taskographyv2tiny10scrub",
    "taskographyv2medium10scrub",
    # Courier(n, k)
    "taskographyv3tiny10bagslots10scrub",
    "taskographyv3medium10bagslots10scrub",
    "taskographyv3tiny10bagslots3scrub",
    "taskographyv3medium10bagslots3scrub",
    "taskographyv3tiny10bagslots5scrub",
    "taskographyv3medium10bagslots5scrub",
    "taskographyv3tiny10bagslots7scrub",
    "taskographyv3medium10bagslots7scrub",
    # Lifted Rearrangement(k)
    "taskographyv4tiny5scrub",
    "taskographyv4medium5scrub",
    # Lifted Courier(n, k)
    "taskographyv5tiny5bagslots5scrub",
    "taskographyv5medium5bagslots5scrub"
]
