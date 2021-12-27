import os
import argparse

from taskography_api.taskography.utils.loader import loader


parser = argparse.ArgumentParser()
parser.add_argument("--data-path", "-d", type=str, required=True, help="Path to 3DSG dataset root")
args = parser.parse_args()

# no assertions should be triggered when loading 3D scene graphs
filedirs = [os.path.join(args.data_path, "tiny/verified_graph"), os.path.join(args.data_path, "medium/automated_graph")]
filepaths = [os.path.join(fd, filename) for fd in filedirs for filename in os.listdir(fd)]
for fp in filepaths:
    try:
        print(f"Loading 3D scene graph: {fp}")
        _ = loader(fp)
    except:
        raise RuntimeError("Failed to load 3D scene graph {}".format(fp))
