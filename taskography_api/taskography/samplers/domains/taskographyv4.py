import random
import numpy as np

from pddlgym.structs import LiteralConjunction
from ..problem_sampler_base import ProblemSamplerBase
from .taskographyv2 import TaskSamplerV2
from taskography_api.taskography.utils.constants import OBJECTS, RECEPTACLES


class TaskSamplerV4(TaskSamplerV2):
    def __init__(
        self, domain_filepath, scene_graph_filepath, complexity=1, bagslots=None
    ):
        """PDDL problem sampler for the Lifted Rearrangement(k) task. 
        Corresponding domain specification: domains/taskographyv4.pddl.
        """
        super().__init__(
            domain_filepath,
            scene_graph_filepath,
            complexity=complexity,
            bagslots=bagslots,
        )
        assert (
            bagslots is None
        ), "Lifted Rearrangement(k) domains does not use bagslots."
        lifted_class_array = self.lifted_class_matrix.copy().reshape(-1)
        mask = lifted_class_array > 0
        self._lifted_class_indices = np.arange(len(lifted_class_array))[mask]
        self._lifted_class_weights = (
            lifted_class_array[mask] / lifted_class_array[mask].sum()
        )

    def create_entities(self):
        super().create_entities()

        # Item / Entity Types
        rclass_type = self.domain.types["rclass"]
        iclass_type = self.domain.types["iclass"]

        # Receptacle Classes
        for r_class in RECEPTACLES:
            r_class = r_class.replace(" ", "")
            rclass = rclass_type(r_class)
            self.entities.add(rclass)
            self.entities_map[r_class] = rclass

        # Item Classes
        for i_class in OBJECTS:
            i_class = i_class.replace(" ", "")
            iclass = iclass_type(i_class)
            self.entities.add(iclass)
            self.entities_map[i_class] = iclass

    def create_predicates(self):
        super().create_predicates()

        # PDDL Entity / Object Map
        emap = self.entities_map

        # Predicate Types
        receptacle_class = self.domain.predicates["receptacleclass"]
        item_class = self.domain.predicates["itemclass"]
        class_relation = self.domain.predicates["classrelation"]

        # receptacleClass
        for r_id in self.receptacles["all"]:
            str_rec_name = self.receptacle_names[r_id]
            str_rec_class = self.sg.object[r_id].class_.replace(" ", "")
            self.predicates.add(
                receptacle_class(emap[str_rec_name], emap[str_rec_class])
            )

        # itemClass
        for o_id in self.objects["all"]:
            str_obj_name = self.object_names[o_id]
            str_obj_class = self.sg.object[o_id].class_.replace(" ", "")
            self.predicates.add(item_class(emap[str_obj_name], emap[str_obj_class]))

        # classRelation
        for (str_obj_class, str_rec_class) in self.lifted_class_relations:
            self.predicates.add(
                class_relation(emap[str_obj_class], emap[str_rec_class])
            )

    def sample_task_repr(self):
        class_relations = np.random.choice(
            self._lifted_class_indices,
            size=self.complexity,
            replace=False,
            p=self._lifted_class_weights,
        )
        i_ids, r_ids = np.unravel_index(
            class_relations, shape=self.lifted_class_matrix.shape
        )
        class_relation_ids = sorted(list(zip(i_ids.tolist(), r_ids.tolist())))

        a_rid = random.sample(self._sorted_room_ids, k=1)[0]
        a_pid = self.room_to_place_map[a_rid]["root"]
        task_repr = {
            "a_rid": a_rid,
            "a_pid": a_pid,
            "i_ids": [id[0] for id in class_relation_ids],
            "r_ids": [id[1] for id in class_relation_ids],
        }
        return task_repr

    def sample(self, k=1, repeat=False):
        emap = self.entities_map

        # Predicate Types
        in_room = self.domain.predicates["inroom"]
        in_place = self.domain.predicates["inplace"]
        at_location = self.domain.predicates["atlocation"]
        class_relation = self.domain.predicates["classrelation"]

        tasks = []
        for task in ProblemSamplerBase.sample(self, k=k, repeat=repeat):
            predicates = self.predicates.copy()

            # init | agent: inRoom, inPlace, atLocation
            predicates.add(in_room(emap["robot"], emap[self.room_names[task["a_rid"]]]))
            predicates.add(
                in_place(emap["robot"], emap[self.place_names[task["a_pid"]]])
            )
            predicates.add(
                at_location(
                    emap["robot"], emap[self.location_names["places"][task["a_pid"]]]
                )
            )

            # goal | pick object, place receptacle: inReceptacle
            goals = []
            for i_id, r_id in zip(task["i_ids"], task["r_ids"]):
                goals.append(
                    class_relation(
                        emap[self.objects["class_index_inv"][i_id]],
                        emap[self.receptacles["class_index_inv"][r_id]],
                    )
                )
            goals = LiteralConjunction(goals)

            task = {
                "objects": self.entities.copy(),
                "initial_state": predicates,
                "goal": goals,
            }
            tasks.append(task)

        return tasks

    def valid(self):
        return (
            ProblemSamplerBase.valid(self)
            and self.valid_lifted
            and self.num_lifted_pairs >= self.complexity
        )
