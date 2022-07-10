import os
import argparse

from taskography_api.taskography.utils.loader import loader


def load_scene_graphs(args):
    """Iterate through and load all scene graphs in Gibson's tiny/verified and
    medium/automated_graph splits. No assertions should be triggered.
    """
    data_path = os.path.expandvars(args.data_path)
    filedirs = [
        os.path.join(data_path, "tiny/verified_graph"),
        os.path.join(data_path, "medium/automated_graph"),
    ]
    filepaths = [
        os.path.join(fd, filename) for fd in filedirs for filename in os.listdir(fd)
    ]
    for fp in filepaths:
        try:
            print(f"Loading 3D scene graph: {fp}")
            _ = loader(fp)
        except:
            raise RuntimeError("Failed to load 3D scene graph {}".format(fp))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-path", "-d", type=str, required=True, help="Path to 3DSG dataset root"
    )
    args = parser.parse_args()

    load_scene_graphs(args)
