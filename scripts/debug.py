
from taskography_api.utils.loader import loader
from taskography_api.utils.utils import scenegraph_mst

fp = "/Users/christopheragia/Projects/data/tiny/verified_graph/3DSceneGraph_Allensville.npz"
building = loader(fp)
scenegraph_mst(building)
