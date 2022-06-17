import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

setuptools.setup(
    name='pddlgym_planners',
    version='0.0.1',    
    author='Tom Silver, Rohan Chitnis, Mohamed Khodeir, Christopher Agia',
    author_email='cagia@stanford.edu',
    description='Symbolic planning support in Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/agiachris/pddlgym_planners',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
