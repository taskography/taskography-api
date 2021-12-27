from .domains import *


_SAMPLERS = {
    "taskographyv1": TaskSamplerV1,
    "taskographyv2": TaskSamplerV2,
    "taskographyv3": TaskSamplerV3,
    "taskographyv4": TaskSamplerV4,
    "taskographyv5": TaskSamplerV5,
    "flat_rearrangement": TaskSamplerV1,
    "rearrangement": TaskSamplerV2,
    "courier": TaskSamplerV3,
    "lifted_rearrangement": TaskSamplerV4,
    "lifted_courier": TaskSamplerV5
}


def get_task_sampler(sampler, sampler_kwargs=None):
    if sampler not in _SAMPLERS:
        raise KeyError("Specified domain {} does not exist.".format(sampler))

    if sampler_kwargs is None:
        return _SAMPLERS[sampler]
    else:
        return _SAMPLERS[sampler](**sampler_kwargs)
