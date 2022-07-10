import setuptools
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = [
    "gym==0.21.0",
    "flatten_dict",
    "imageio",
    "ipdb",
    "matplotlib",
    "multipledispatch",
    "networkx",
    "numpy",
    "Pillow",
    "psutil",
    "pyrddl",
    "pytest",
    "PyYAML",
    "recommonmark",
    "scikit_image",
    "scipy",
    "setuptools",
    "scikit-image",
    "tqdm"
    f"pddlgym_planners @ file://localhost/{Path(__file__).parent}/third_party/pddlgym_planners",
]

setuptools.setup(
    name="taskography_api",
    version="0.0.1",
    author="Christopher Agia, Krishna Murthy Jatavallabhula, Mohamed Khodeir",
    author_email="cagia@cs.stanford.edu",
    description="A simple API generating symbolic planning tasks in 3D scene graphs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/taskography/taskography-api.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=install_requires,
)
