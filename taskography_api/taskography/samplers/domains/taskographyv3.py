from .taskographyv2 import TaskSamplerV2


class TaskSamplerV3(TaskSamplerV2):
    def __init__(self, domain_filepath, scene_graph_filepath, complexity=1, bagslots=3):
        """PDDL problem sampler for the Courier(n, k) task. 
        Corresponding domain specification: domains/taskographyv3.pddl.
        """
        assert bagslots is not None, "Courier(n, k) domains use bagslots."
        super().__init__(
            domain_filepath,
            scene_graph_filepath,
            complexity=complexity,
            bagslots=bagslots,
        )

    def create_entities(self):
        super().create_entities()

        # Item / Entity Types
        bagslot_type = self.domain.types["bagslot"]

        # Bagslots
        for bagslot_id in range(self.bagslots):
            bagslot_name = f"bagslot{bagslot_id + 1}"
            bagslot = bagslot_type(bagslot_name)
            self.entities.add(bagslot)
            self.entities_map[bagslot_name] = bagslot

    def create_predicates(self):
        super().create_predicates()

        # PDDL Entity / Object Map
        emap = self.entities_map

        # smallItem, mediumItem, largeItem
        for o_id in self.objects["all"]:
            str_obj_name = self.object_names[o_id]
            self.predicates.add(
                self.domain.predicates[self.object_sizes[o_id]](emap[str_obj_name])
            )

    def sample_task_repr(self):
        return super().sample_task_repr()

    def sample(self, k=1, repeat=False):
        return super().sample(k=k, repeat=repeat)

    def valid(self):
        return super().valid()
